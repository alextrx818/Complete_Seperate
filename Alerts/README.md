# Alerts Subsystem

This document describes the design, configuration, and extension points for the Alert Branch of the sports‑bot project. It is intended for developers integrating new alert scanners (satellites) or maintaining the central alert orchestration (AlerterMain).

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture & Data Flow](#2-architecture--data-flow)
3. [BaseAlert: Core Interface](#3-basealert-core-interface)
4. [Implementing a Satellite Scanner](#4-implementing-a-satellite-scanner)
5. [Auto‑Discovery & Registration](#5-autodiscovery--registration)
6. [Pipeline Integration](#6-pipeline-integration)
7. [Configuration & Parameters](#7-configuration--parameters)
8. [Logging, Formatting & State](#8-logging-formatting--state)
9. [Error Handling](#9-error-handling)
10. [Extending the System](#10-extending-the-system)
11. [Troubleshooting & FAQs](#11-troubleshooting--faqs)

## 1. Overview

The Alert Branch runs in parallel with the main fetch/merge/summary pipeline. Its responsibilities are strictly:

- **Detection**: each satellite scanner examines one match's data and signals when its specific criteria are met.
- **Orchestration**: AlerterMain manages scanner discovery, deduplication, formatting, logging, and notifications (e.g., Telegram).

No scanning logic lives in the main orchestrator; all domain‑specific criteria are contained in satellite classes under `Alerts/`.

## 2. Architecture & Data Flow

**Core Pipeline** (`orchestrate_complete.py`):
1. Fetch → Merge → Write Combined Summaries → Generate Summary JSON
2. Calls `run_alerters(summary_json, match_ids)` immediately after JSON generation.

**AlerterMain** (`Alerts/alerter_main.py`):
1. Discovers all BaseAlert subclasses.
2. Iterates over `summary_json['matches']`, invoking each scanner via `safe_check(match)`.
3. On positive payloads, applies dedup logic, formats the alert, logs it, and sends notifications.

**Satellite Scanners** (`Alerts/*.py`, e.g. `OU3.py`):
1. Inherit from BaseAlert.
2. Implement only a `check(match)` method that returns a structured payload or None.

## 3. BaseAlert: Core Interface

**Location**: `Alerts/base_alert.py`

**Responsibilities**:
- **Interface**: defines `check(match)` signature.
- **Error Safety**: wraps calls in `safe_check()` to catch exceptions and log errors without crashing.
- **Logging**: each scanner gets its own named logger from the base class.

**Key Methods**:
```
Alert(name)
    └── constructor: set human‑readable name and logger.
check(match)
    └── abstract: called by satellites for detection logic.
safe_check(match)
    └── wrapper: try/catch around check(), logs on error, returns None on exception.
```

## 4. Implementing a Satellite Scanner

To add a new alert scanner:

1. Create a new file under `Alerts/`, e.g. `my_event_alert.py`.
2. Define a class that extends `Alert`:
   - Call `super().__init__(name="MyAlertName")` in `__init__`.
   - Implement `check(self, match) -> None | dict`:
     - Inspect fields in the match dict (status_id, score, odds, env, etc.).
     - Return a descriptive dict payload when criteria are met, else None.
3. Drop the file into `Alerts/`—no changes to other code required.

**Example Implementation**:

```python
# Alerts/goal_alert.py
from typing import Dict, Optional, Any
from .base_alert import Alert

class GoalAlert(Alert):
    """Alert when a match reaches a certain number of goals."""
    
    def __init__(self, min_goals: int = 3):
        super().__init__(name="GoalAlert")
        self.min_goals = min_goals
        
    def check(self, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if total goals meets or exceeds threshold."""
        match_id = match.get("match_id", "unknown")
        
        # Extract score information
        score = match.get("score", [])
        if not isinstance(score, list) or len(score) < 4:
            self.logger.debug(f"Match {match_id}: Invalid score format")
            return None
            
        # Extract home and away scores
        home_score = score[2][0] if isinstance(score[2], list) else 0
        away_score = score[3][0] if isinstance(score[3], list) else 0
        
        total_goals = home_score + away_score
        
        # Check if total goals meets threshold
        if total_goals >= self.min_goals:
            self.logger.info(f"Match {match_id}: Total goals {total_goals} meets threshold {self.min_goals}")
            return {
                "type": "GOAL",
                "total_goals": total_goals,
                "threshold": self.min_goals,
                "detail": f"Total Goals: {total_goals} (Threshold: {self.min_goals})"
            }
            
        return None
```

## 5. Auto‑Discovery & Registration

AlerterMain automatically discovers scanners:

1. Scans the `Alerts/` directory (excluding `__init__.py`, `alerter_main.py`, `base_alert.py`).
2. Imports each module dynamically.
3. Finds all classes that subclass `Alert`.
4. Instantiates them, using parameters from an optional `alert_params` map.

This mechanism frees you from maintaining a manual list: new scanners are live by file presence.

## 6. Pipeline Integration

**Entry Point**: `run_alerters(summary_json, match_ids)` in the orchestrator.

Inside it:
1. Instantiate `AlerterMain(auto_discover=True, alert_params=...)`.
2. Log how many matches and alerts will run.
3. Loop over `summary_json['matches']`, retrieving `match_id` for dedup.
4. Invoke each scanner via `notice = alert.safe_check(match)`.
5. If notice and not already seen:
   - Add to seen‑IDs.
   - Format, log, and notify.

No scanner or format code resides in the orchestrator—everything routes through AlerterMain.

## 7. Configuration & Parameters

Default thresholds and other per‑alert settings live in the orchestrator's `alert_params` dict.

**Example**:
```python
alert_params = {
    "OverUnderAlert": {"threshold": 3.5},
    "GoalAlert": {"min_goals": 2}
}
```

Pass `alert_params` to AlerterMain to customize each scanner's constructor args.

## 8. Logging, Formatting & State

**Per‑Alert Logs**: each scanner has a dedicated `.logger` file under `Alerts/` via `configure_alert_logger()`.

**Seen‑IDs Persistence**: for each alert, a `<AlertName>.seen.json` file stores match IDs already notified, preventing duplicates across runs.

**Formatting**: AlerterMain's `format_alert(match, payload, alert_type)` produces a consistent, pretty-printed multi‑line message matching the combined-summary style.

## 9. Error Handling

**Isolation**: any exception in a scanner's `check()` is caught by `safe_check()`, logged with stack trace, and treated as "no alert."

**Discovery Failures**: modules or classes that fail to import/instantiate during discovery are logged but do not halt the pipeline.

**Notification Errors**: failures sending to Telegram (or other channels) are logged but do not crash the service.

## 10. Extending the System

To add or modify alerts:

1. Drop a new Python file in `Alerts/` implementing the `Alert` interface.
2. Define your criteria in `check(match)`, returning None or a payload dict.
3. (Optional) Add constructor parameters to `alert_params` in the orchestrator if needed.
4. Run the pipeline—your new alert will be auto-registered and active immediately.

No changes to the main orchestrator or existing alert code are required.

## 11. Troubleshooting & FAQs

- **My alert isn't running**: ensure your class inherits `Alert`, file name ends with `.py`, and you didn't exclude it in discovery patterns.
- **Parameters not applied**: verify `alert_params` uses the exact class name key.
- **Duplicate notifications**: check that your payload includes no changing fields (e.g. timestamps) so dedup IDs match.
- **Formatting looks off**: confirm `format_match_summary()` outputs the expected lines and `format_alert()` inserts payload details in the right place.

Now you have a fully‑global, plugin‑style alert framework: the main pipeline just hands off data, AlerterMain orchestrates, and satellite classes implement detection. Drop in new scanners freely, and maintain only the `alert_params` map for customization.

Happy alerting! 🎉
