# Alert Subsystem README

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Data Flow](#architecture--data-flow)
3. [Key Components](#key-components)
   - [BaseAlert (base_alert.py)](#1-basealert-base_alertpy)
   - [Alert Configuration (alerts_config.py)](#2-alert-configuration-alerts_configpy)
   - [AlerterMain (alerter_main.py)](#3-alertermain-alerter_mainpy)
   - [Orchestrator Integration (orchestrate_complete.py)](#4-orchestrator-integration-orchestrate_completepy)
   - [Satellite Scanner (e.g., OU3.py)](#5-satellite-scanner-eg-ou3py)
4. [Creating a New Alert Satellite](#creating-a-new-alert-satellite)
5. [Testing & Validation](#testing--validation)
6. [Next Steps & Completion Criteria](#next-steps--completion-criteria)

## Overview

**IMPORTANT: Refer to this README whenever exploring, modifying, or extending the alert system.**

The Alert Subsystem is a modular, plugin-based framework designed to scan enriched match data for user-defined conditions ("alerts"). It sits downstream of the core sports-data pipeline and upstream of user notifications/logging. New alert "satellites" can be dropped into the system without modifying core orchestration logic.

### Goals

- **Separation of Concerns**: Detection logic (satellites) vs orchestration & notification (AlerterMain).
- **Auto‑Discovery**: New alert classes are auto‑loaded from the Alerts/ folder.
- **Safe Execution**: Satellite failures do not crash the pipeline via safe_check().
- **Global Consistency**: Unified timezone, status‑ordering, and logging conventions.
- **Easy Extension**: Developers can add new alerts by subclassing a single base class.

## Architecture & Data Flow

```
merge_all_matches  
      ↓             (sorted by DESIRED_STATUS_ORDER)  
write_combined_match_summary  → human-readable console & file  
      ↓  (unchanged list)  
write_summary_json (produces in-memory dict + prepend‑log)  
      ↓  
run_alerters(summary_json)  → invokes AlerterMain  
      ↓  (auto-discovered Alert instances)  
For each match in summary_json['matches']:
    alert.safe_check(match)  → detection logic
        ↳ None: no alert
        ↳ payload:  dedupe → format_alert() → send_notification() + per-alert log
```

1. **Data Enrichment**: Raw API data → merge_logic → enriched match dicts
2. **Summary Generation**: Formatted human logs, then JSON summaries
3. **Alerter Invocation**: run_alerters hands JSON to AlerterMain
4. **Detection**: BaseAlert.safe_check() calls each satellite's check()
5. **Deduplication**: Each alert writes/reads <AlertName>.seen.json to avoid repeats
6. **Notification & Logging**: Matches that trigger are formatted and sent/logged

## Key Components

### 1. BaseAlert (Alerts/base_alert.py)

Abstract Class requiring:

- **__init__(self, name: str, debug: bool=False)** — registers a per-alert logger, optional debug file handler.
- **check(self, match: Dict) -> Optional[Union[str, Dict]]** — must be implemented by satellites.
- **safe_check(self, match)** — wraps check() in try/catch, logs exceptions, and returns None on error.

**Usage Note for AI Bot**: At top of file, a comment instructs: "Drop new .py in Alerts/, subclass Alert, implement check(match)."

### 2. Alert Configuration (Alerts/alerts_config.py)

Holds a centralized ALERT_PARAMS mapping:

```python
ALERT_PARAMS = {
    "OverUnderAlert": {"threshold": 3.0},
    # "MyNewAlert": { ... }
}
```

Enables changing parameters without code edits.

### 3. AlerterMain (Alerts/alerter_main.py)

- **Auto‑Discovery**: discover_alerts() scans all .py files (except __init__, main, base) for subclasses of Alert.
- **Initialization**: After discovery, _initialize_alert(alert) sets up file-base → per-alert logger → loads .seen.json.
- **Execution**: No longer uses legacy run(); instead, run_alerters() from the orchestrator drives alerts.
- **Formatting**: Uses format_alert(match, payload, alert.name) to produce consistent multi-line messages.

### 4. Orchestrator Integration (orchestrate_complete.py)

- **Singleton Entry**: run_alerters(summary_json, match_ids) is the single alert hook, after write_summary_json.
- **Configuration Loading**: Imports ALERT_PARAMS from Alerts/alerts_config.py instead of in‑lining.
- **Command Note for AI Bot**: Inline comments mark this as the only alert invocation point.

### 5. Satellite Scanner (e.g., Alerts/OU3.py)

- **Inheritance**: class OverUnderAlert(Alert) with DEFAULT_PARAMS = {"threshold":3.0}.
- **Detection (check)**:
  - Converts match['status_id'] → int, skips if not in {2,3,4}.
  - Reads ou_map = match.get('odds', {}).get('over_under', {}).
  - Finds the entry with the highest timestamp.
  - Checks if line > self.threshold.
  - Returns a payload dict containing type, line, over, under, threshold, timestamp, detail or None.
- **Safe Execution**: All exceptions are caught by base_alert.safe_check().

## Creating a New Alert Satellite

### File Placement
- Alerts/MyNewAlert.py

### Subclass BaseAlert

```python
from .base_alert import Alert

class MyNewAlert(Alert):
    DEFAULT_PARAMS = {"paramA": 42}  # optional defaults

    def __init__(self, paramA=None, debug=False):
        super().__init__(name="MyNewAlert", debug=debug)
        self.paramA = paramA or self.DEFAULT_PARAMS["paramA"]

    def check(self, match):
        # Your detection logic, e.g.:
        if match.get('score', {}).get('home',0) > self.paramA:
            return {"type": self.name, "value": match['score']['home']}
        return None
```

### Configuration
- Add to Alerts/alerts_config.py:

```python
ALERT_PARAMS["MyNewAlert"] = {"paramA": 10}
```

### Auto‑Discovery
- No further imports needed—simply restart the pipeline.

### Test
- Write unit tests under tests/test_mynewalert.py using safe_check.

## Testing & Validation

### Unit Tests (e.g. test_ou3.py)
- Live match above/below threshold
- Non‑live status returns None
- Missing over_under returns None

### Integration
- Run the full pipeline (run_pipeline.sh) and confirm:
  - Alerts fire exactly once per match.
  - .seen.json files populate correctly.
  - Alert logs (Alerts/OU3.logger) contain formatted messages.
  - Telegram messages (if enabled) deliver correctly.

## Next Steps & Completion Criteria

### Finalize OU3 Scanner
- Polish payload (over + under), ensure self.name consistency.

### Complete Unit Tests
- Achieve 100% coverage for all alert logic branches.

### Deprecate Legacy Entry
- Remove or deprecate AlerterMain.run().

### Add CI/CD Checks
- Linting, test runs on PR.

### Document Alerts
- Maintain a registry of available alerts and their parameters.

### When Is This Done?
- All alerts auto-discover, configure, and run without code changes (just adding new files).
- No unhandled exceptions in alert check paths.
- Clear, consistent logs and notifications.
- README and in‑code comments guide new developers end‑to‑end.

## Rebuild Guide

If the alert system needs to be rebuilt from scratch, follow these steps:

1. Create `base_alert.py` with the abstract Alert class implementing `safe_check()`
2. Create `alerts_config.py` with the ALERT_PARAMS dictionary
3. Implement `alerter_main.py` with `discover_alerts()` and `_initialize_alert()` 
4. Modify `orchestrate_complete.py` to import alerts_config and call `run_alerters()`
5. Implement satellite alerts (e.g., OU3.py) by subclassing Alert
6. Add unit tests for each alert satellite

Following this guide, you should be able to reconstruct the entire alert system with the same architecture and functionality.
