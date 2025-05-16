# Sports Bot Logging System Rules

## ABSOLUTE GLOBAL RULES

This document establishes the **absolute global rules** for ALL loggers in the sports bot project. **No exceptions** are permitted to these rules. All developers must follow these conventions to ensure consistent logging behavior and formatting across the entire codebase.

## 1. Newest-First Log Entries (PrependFileHandler)

All log files in the sports bot project display entries in reverse chronological order, with the newest entries at the top of the file. This is implemented using a custom `PrependFileHandler` that prepends new log entries to the beginning of log files.

### Implementation

The `PrependFileHandler` class in `log_config.py` overrides the `emit` method to prepend log messages rather than append them:

```python
class PrependFileHandler(TimedRotatingFileHandler):
    """Custom file handler that prepends new log entries at the beginning of the file."""
    
    def emit(self, record):
        """Override the emit method to prepend rather than append."""
        msg = self.format(record) + '\n'
        path = self.baseFilename
        try:
            with open(path, 'r+', encoding=self.encoding) as f:
                existing = f.read()
                f.seek(0)
                f.write(msg + existing)
        except FileNotFoundError:
            with open(path, 'w', encoding=self.encoding) as f:
                f.write(msg)
```

All file handlers in the `LOGGING_CONFIG` dictionary use this handler:

```python
"handler_name": {
    "class": "log_config.PrependFileHandler",
    "level": "INFO",
    "formatter": "standard",
    "filename": str(LOGS_DIR / "path" / "to" / "logfile.log"),
    "when": "midnight",
    "backupCount": 30,
    "encoding": "utf8",
},
```

## 2. Persistent Match Counter

Match summaries use a persistent counter that increments with each new match, regardless of match data source. This counter is stored in `match_id.txt` and provides a globally sequential match ID.

### Implementation

The counter is implemented in `write_combined_match_summary()` function in `combined_match_summary.py`:

```python
# Read current ID (default to 0 if file is empty or doesn't exist)
try:
    with open(match_id_file, 'r') as f:
        content = f.read().strip()
        current_id = int(content) if content else 0
except (FileNotFoundError, ValueError):
    current_id = 0

# Increment the counter
current_id += 1

# Write updated ID back to file
with open(match_id_file, 'w') as f:
    f.write(str(current_id))
```

The current match ID is displayed in the match header:

```
================#MATCH 123 of 456===============
```

## 3. Match Summary Formatting

Match summaries follow a specific format with a centered header and timestamp:

```
================#MATCH 123 of 456===============
          05/15/2025 06:33:53 PM EDT          

Competition: Premier League (England)
Match: Arsenal FC vs Manchester United
...
```

### Implementation

The match summary formatter uses a simple formatter without timestamps to avoid redundancy:

```python
formatter = logging.Formatter('%(message)s')
```

The header is centered with dynamically calculated padding:

```python
# Compute target width for perfect centering
base = max(len(match_str), len(ts_str))
width = base + 20  # Add padding

# Ensure width - len(ts_str) is even for perfect centering
if (width - len(ts_str)) % 2 != 0:
    width += 1
    
# Center both lines
match_line = match_str.center(width, '=')
ts_line = ts_str.center(width, ' ')
```

## 4. Eastern Time Zone for All Timestamps

All log timestamps use Eastern Time (America/New_York) and a consistent MM/DD/YYYY HH:MM:SS AM/PM format with timezone indicator.

### Implementation

The timezone is set globally:

```python
os.environ['TZ'] = 'America/New_York'
time.tzset()  # Apply the timezone setting to the process
```

A converter function is bound to the Formatter class:

```python
def ny_time_converter(timestamp):
    """Return a time.struct_time in local (NY) timezone"""
    return time.localtime(timestamp)

logging.Formatter.converter = staticmethod(ny_time_converter)
```

## 5. Viewing Logs

To view logs in the natural order (oldest first), use the `tac` command:

```bash
tac logs/combined_match_summary.logger | less
```

To show only the first N entries in reverse order:

```bash
tac logs/combined_match_summary.logger | head -n <lines>
```

## 6. Log Rotation

All logs are configured for automatic daily rotation with 30 days of retention:

```python
"when": "midnight",
"backupCount": 30,
```

## 7. Using create_custom_logger for All New Loggers

ALL new loggers in the project MUST be created using the `create_custom_logger` function from `log_config.py`. This function automatically enforces all global logging rules:

```python
from log_config import create_custom_logger

# For standard logs (with timestamp prefixes)
logger = create_custom_logger(
    name="my_component",  # Required
    log_file="/path/to/logs/my_component.log",  # Optional, set to None for console-only
    timestamp_prefix=True,  # Default=True: include timestamp prefix
    level=logging.INFO  # Default logging level
)

# For logs with embedded timestamps (like match summaries)
logger = create_custom_logger(
    name="match_summary",
    log_file="/path/to/logs/match_summary.log",
    timestamp_prefix=False,  # No timestamp prefix, for logs with their own timestamps
    level=logging.INFO
)
```

This function ensures:

1. **Newest-first log entries** using PrependFileHandler
2. **Eastern Time** formatting for all timestamps
3. **Proper handling of multi-line messages** using SingleLineFormatter
4. **Configurable timestamp prefixes** for special loggers that include their own timestamps

## 8. Log Maintenance

To clean up log handlers and properly release file descriptors, call:

```python
from log_config import cleanup_handlers
cleanup_handlers()
```

This should be done at application shutdown.



Global Logging Configuration & Diagnostics README

This README provides a complete, step‑by‑step guide to implement and verify two global logging rules across the sports bot project:

Consistent Eastern‑Time timestamps (one prefix per log invocation)

Newest‑first file logs (prepend mode)

It also covers diagnostics, append‑based match summaries, and rollback procedures.

1. Prerequisites

Python ≥ 3.12

pytz installed (optional)

Project uses centralized logging.config.dictConfig in log_config.py

All modules import log_config (and call configure_logging()) before creating any loggers

2. Global Eastern‑Time Timestamping

2.1 Set Process Timezone

In log_config.py, at the very top, add:

import os, time, logging
# Force process into Eastern Time (New York)
os.environ['TZ'] = 'America/New_York'
time.tzset()

2.2 Define & Bind Converter

Immediately after, define and bind a converter:

# Convert Unix timestamp to local Eastern time
def ny_time_converter(timestamp):
    return time.localtime(timestamp)
# Bind globally to Formatter
logging.Formatter.converter = staticmethod(ny_time_converter)

2.3 (Optional) Single‑Line Formatter

To prevent per‑line prefixes on multi‑line messages, subclass Formatter:

import logging
class SingleLineFormatter(logging.Formatter):
    def format(self, record):
        text = super().format(record)
        lines = text.splitlines(keepends=True)
        return lines[0] + ''.join(lines[1:]) if len(lines) > 1 else text

In your LOGGING_CONFIG['formatters'], use:

"standard": {
  "()": "log_config.SingleLineFormatter",
  "format": "%(asctime)s [%(levelname)s] %(message)s",
  "datefmt": "%m/%d/%Y %I:%M:%S %p %Z"
},
"detailed": {
  "()": "log_config.SingleLineFormatter",
  "format": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
  "datefmt": "%m/%d/%Y %I:%M:%S %p %Z"
}

3. Global Newest‑First File Logs

3.1 Define PrependFileHandler

Also in log_config.py, add:

from logging.handlers import TimedRotatingFileHandler
class PrependFileHandler(TimedRotatingFileHandler):
    def emit(self, record):
        msg = self.format(record) + '\n'
        path = self.baseFilename
        try:
            with open(path, 'r+', encoding=self.encoding) as f:
                old = f.read()
                f.seek(0)
                f.write(msg + old)
        except FileNotFoundError:
            with open(path, 'w', encoding=self.encoding) as f:
                f.write(msg)

3.2 Update LOGGING_CONFIG['handlers']

For each file‑based handler entry (e.g. "orchestrator_file", "fetch_data_file", etc.), change:

"class": "logging.handlers.TimedRotatingFileHandler"

to:

"class": "log_config.PrependFileHandler"

Keep all other parameters unchanged (level, formatter, filename, when, backupCount, encoding).

4. Append‑Based Match Summaries

4.1 Persistent Match Counter

Create a file match_id.txt next to combined_match_summary.py.

At summary start, read its integer (default 0), increment, overwrite, store in current_id.

Use header: #MATCH {current_id}.

4.2 Append Summaries

Use standard append-mode logs (logger.info(full_summary) or with open(log, 'a')).

Do not store large in-memory lists.

4.3 Reverse‑Order Viewing

Shell: tac combined_match_summary.log | head -n <N>

Python:

for line in reversed(open('combined_match_summary.log').readlines()):
    print(line, end='')

5. Diagnostics & Verification

Run these in your environment to confirm correct behavior:

Handler & Formatter Check

import logging
logger = logging.getLogger('summary')
print([type(h).__name__ for h in logger.handlers])
print([h.formatter._fmt for h in logger.handlers])

• Expect: ['StreamHandler','PrependFileHandler'] and ['%(asctime)s…','%(message)s'].

Per‑Line Prefix Test

logger.info("LINE1\nLINE2")

• Console shows one timestamp; second line unprefixed (if using SingleLineFormatter).

Multi‑Line Single Call
Build header & timestamp in one string:

header = f"{match_line}\n{ts_line}"
logger.info(header)

• You should see exactly one prefix on the first line.

Newest‑First Log File

tac path/to/any.log | head -n 5

• Verify newest entries appear at the top.

Timestamp Format
Check sample line: MM/DD/YYYY HH:MM:SS AM/PM EDT.

6. Rollback Procedures

Timestamps: Remove converter binding or restore logging.Formatter.converter to default; comment out os.environ['TZ'] and tzset().

SingleLineFormatter: Remove "()" keys; revert to base Formatter.

PrependFileHandler: Change handler classes back to TimedRotatingFileHandler.

Summaries: Restore original multi-line or prepend logic if needed.