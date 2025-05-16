# Alerts Subsystem: Comprehensive Guide

This document captures every step we've taken to build a flexible, scalable alerting branch in the sports bot, and shows exactly how to add new alert "satellites" in the future. If you ever need to reconstruct the system from scratch, just follow these steps in order.

## 1. Architectural Overview

### Orchestrator Pipeline

- **Fetch & Cache → Merge & Enrich → Print Human Summaries → Generate JSON → Run Alerts**
- Alerts run on the in-memory JSON immediately after it's written, using the same ordered match list that was printed.

### Alert Branch

- **AlerterMain**: central coordinator—no detection logic, only discovery, deduplication, formatting, logging, and notification.
- **BaseAlert (abstract)**: defines a safe interface every detector must follow.
- **Satellite Alerts** (e.g. OverUnderAlert): simply implement check(match) and declare defaults; everything else is wired up for them.

### Auto-Discovery & Configuration

- All subclasses of Alert in Alerts/ are discovered at runtime—no manual imports.
- Parameters (thresholds, etc.) come from a single source of truth: Alerts/alerts_config.py, merged with any DEFAULT_PARAMS defined in the class.

### Logging & State

- Each alert gets its own log file (<AlertName>.logger) and a dedup store (<AlertName>.seen.json).
- File handlers and seen-ID loading are encapsulated in a private _initialize_alert() helper.

## 2. Foundational Steps (What We Did First)

### Create BaseAlert (Alerts/base_alert.py)

- Defined abstract Alert class with:
  - **__init__(name, debug=False)**
    - Configures a logger for this alert.
    - Optionally adds a debug-level file handler.
  - **check(match)** (abstract)
  - **safe_check(match)** wrapper to catch exceptions and log them without crashing the pipeline.
- Added a top-of-file "NOTE FOR AI BOT" comment to guide future alert creation.

### Refactor Existing Satellites

- Updated OU3.py to subclass Alert.
- Removed its own handler setup—now uses self.logger.
- Stubbed in DEFAULT_PARAMS = {"threshold": 3.0}.

### Auto-Discovery (Alerts/alerter_main.py)

- Added discover_alerts() class method:
  - Scans Alerts/ folder for Python files.
  - Dynamically imports each module.
  - Finds classes inheriting from Alert.
  - Merges DEFAULT_PARAMS with the central ALERT_PARAMS.
  - Instantiates each alert.
- Updated __init__ to call discovery, then _initialize_alert() for each instance.
- Moved all per-alert logger/seen-ID setup into _initialize_alert().

### Central Config (Alerts/alerts_config.py)

- Created a simple ALERT_PARAMS dictionary—maps class names to parameter dicts.
- Orchestrator loads this file and passes it into AlerterMain.

### Orchestrator Hook (orchestrate_complete.py)

- Replaced hard-coded alert instantiation with call to run_alerters().
- Added "NOTE FOR AI BOT" markers so any developer knows:
  - This is the single alerts entry point.
  - Alert parameters are sourced from alerts_config.py.

## 3. Adding a New Alert Scanner

When you need to introduce a new alert (e.g. HighScoringAlert), follow these steps:

### Create File

- Path: Alerts/HighScoringAlert.py

### Subclass BaseAlert

```python
from .base_alert import Alert

class HighScoringAlert(Alert):
    DEFAULT_PARAMS = {"goal_threshold": 3}

    def __init__(self, goal_threshold=None):
        super().__init__(name="HighScoring", debug=False)
        self.goal_threshold = goal_threshold or self.DEFAULT_PARAMS["goal_threshold"]

    def check(self, match):
        # Your detection logic here...
        # Return None or a dict payload if triggered
```

### Add Configuration (optional override)

- Open Alerts/alerts_config.py
- Add:
  ```python
  ALERT_PARAMS["HighScoringAlert"] = {"goal_threshold": 4}
  ```

### Run Pipeline

- On next execution, AlerterMain.discover_alerts() will automatically pick up HighScoringAlert.
- It will log discovery, instantiate with merged params, initialize its log file and seen-IDs, and run its safe_check() on every match.

## 4. How Alerts Are Processed

### Pipeline calls

```python
summary_json = write_summary_json(merged_data)
await run_alerters(summary_json, match_ids)
```

### run_alerters

- Instantiates AlerterMain(auto_discover=True, alert_params=ALERT_PARAMS).
- Logs how many alerts were discovered.
- Loops through each match in summary_json['matches']:
  - For each alert in alerter.alerts, calls alert.safe_check(match).
  - If payload returned and match_id not in its seen list:
    - Logs the trigger, formats with alerter.format_alert(), sends notifications, writes to <AlertName>.logger, and marks it as seen.

### Deduplication

- Once an alert fires on a match, that match_id is added to <AlertName>.seen.json.
- The same alert will not fire again for that match—unless you manually clear the file.

## 5. OverUnderAlert Implementation

In Alerts/OU3.py, your check(match) should:

### Filter by live play

```python
status = int(match.get("status_id", 0))
if status not in {2, 3, 4}:  # first half, half-time, second half
    return None
```

### Extract O/U map

```python
ou_map = match.get("odds", {}).get("over_under", {})
if not ou_map:
    return None
```

### Pick latest entry

```python
latest = max(ou_map.values(), key=lambda e: e.get("timestamp", 0))
line = float(latest.get("line", 0))
```

### Threshold check

```python
if line <= self.threshold:
    return None
```

### Return payload

```python
return {
  "type": self.name,
  "line": line,
  "over": float(latest.get("over", 0)),
  "under": float(latest.get("under", 0)),
  "threshold": self.threshold,
  "timestamp": latest["timestamp"],
  "detail": f"Over/Under Line: {line:.2f}"
}
```

## 6. Recovery & Rebuild Instructions

If the machine reboots or the project is wiped, do the following in order:

1. Clone repo → cd football/main
2. Ensure log_config.py has the timezone converter and PrependFileHandler adjustments.
3. Ensure Alerts/base_alert.py and alerter_main.py exist with the auto-discovery and _initialize_alert logic.
4. Ensure Alerts/alerts_config.py defines ALERT_PARAMS.
5. Ensure OU3.py (and any other satellites) subclass Alert and define DEFAULT_PARAMS + check().
6. Restart pipeline via run_pipeline.sh.
   - You should see console summaries, then logs in logs/, then alerts firing based on your new scanner.
7. Verify
   - Check combined_match_summary.logger for summary output.
   - Check summary_json.logger for JSON prepends.
   - Check Alerts/*.logger for any alert triggers.
   - Check Alerts/*.seen.json to confirm dedup IDs.

With this document, you have a step-by-step record of how we built the alert fork, established the foundation, and how to keep adding new detectors seamlessly. Happy alerting!
