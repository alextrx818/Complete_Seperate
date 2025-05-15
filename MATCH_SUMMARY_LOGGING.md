# Sports Bot Logging: Multi-Timestamp Diagnosis & Fix

This README captures the full history of the multi-timestamp issue in the match summary logs, the diagnostics performed, and the step-by-step implementation of the solution.

## 1. Background & Symptom

**Issue**: In `combined_match_summary.py`, a single `logger.info(summary)` call produced multiple timestamp prefixes (3+) on consecutive lines, making logs cluttered and confusing.

**Observed Behavior**:
```
05/15/2025 05:46:30 PM EDT INFO 
05/15/2025 05:46:30 PM EDT INFO ==================== MATCH 17/17 ====================
05/15/2025 05:46:30 PM EDT INFO Time: 05/15/2025 05:46:30 PM EDT
```

## 2. Step-by-Step Diagnostics

### Handler Inspection

Ran after obtaining the summary logger:
```python
print("[DIAG] summary.handlers =", [type(h).__name__ for h in logger.handlers])
```

**Result**: Exactly two handlers (`StreamHandler`, `FileHandler`). Both used timestamped formatters.

### Raw Summary Content

Inserted before logging:
```python
print("[DIAG] repr(summary) =", repr(summary))
```

**Result**: Summary did not start with `\n`, but it contained multiple internal `\n` separators.

### Per-Line Prefix Test

Ran:
```python
logger.info("TEST1\nTEST2\nTEST3")
```

**Result**: Python 3.12 logging prefixed the first line with a timestamp, but the other lines appeared without timestamps. However, in the log file, the visual appearance was as if each line had its own timestamp.

### Formatter Verification

Dumped each handler's formatter configuration:
```python
for h in logger.handlers:
    print("    →", h, "fmt=", getattr(h.formatter, '_fmt', None))
```

**Result**: Both handlers used `'%(asctime)s...'` format strings.

## 3. Root Cause

The issue was not multiple timestamps being added, but rather how Python's logging system handles multi-line messages:

1. Python's logging system adds a timestamp prefix to the first line of a log message
2. Each newline character creates a visual break in the log file
3. When a multi-line string is logged, it creates the appearance of multiple timestamped entries

A single `logger.info(summary)` call on a multi-line string therefore produced what looked like multiple timestamps in the log output.

## 4. Solutions Implemented

We implemented two complementary solutions:

### A. Centered Header & Timestamp Format

Instead of a multi-line log entry, we now emit separate log calls with centered formatting:

```python
# Create compact match label
match_str = f"#MATCH {match_num} of {total_matches}"

# Compute target width for perfect centering
base = max(len(match_str), len(ts_str))
width = base + 20  # Add padding

# Ensure width - len(ts_str) is even for perfect centering
if (width - len(ts_str)) % 2 != 0:
    width += 1
    
# Center both lines
match_line = match_str.center(width, '=')
ts_line = ts_str.center(width, ' ')

# Log as separate entries
logger.info(match_line)
logger.info(ts_line)
logger.info(f"\nCompetition: {competition}...")
```

### B. Simple Formatter Without Timestamps

We modified the formatter in `get_combined_summary_logger()` to use a simple formatter that doesn't add timestamps:

```python
# Use a simple formatter without timestamps for the match summary logger
formatter = logging.Formatter('%(message)s')
```

This ensures that even if we use multiple `logger.info()` calls, the log file won't show redundant timestamps.

## 5. Results

The combined match summary log now has a clean, readable format:

```
================#MATCH 5 of 20================
          05/15/2025 06:31:13 PM EDT          

Competition: Premier League (England)
Match: Arsenal FC vs Manchester United
Score: 2 - 1 (HT: 1 - 0)
Status: Half-time break (Status ID: 3)

--- MATCH BETTING ODDS ---
│ ML:     │ Home: -118 │ Draw: +250 │ Away:  +333 │ (@1X2')
│ Spread: │ Home: +200 │ Hcap: 1.95 │ Away:  +195 │ (@AH')
│ O/U:    │ Over: +250 │ Line: 1.85 │ Under: +205 │ (@O/U')

--- MATCH ENVIRONMENT ---
Weather: Unknown (Partly Cloudy)
Temperature: 68
Humidity: 65%
Wind: Moderate Breeze, 13 mph

------------------------------------------------------------
```

## 6. Pre-Run Requirements

Before executing `combined_match_summary.py`, ensure the merge logic output file exists:

**Expected file**: `merge_logic.json` in the same directory as the summary script:
```
/root/CascadeProjects/sports_bot/football/main/merge_logic.json
```

**Generation**: Run the merge logic pipeline (typically `orchestrate_complete.py`) or the designated pipeline script to produce `merge_logic.json`:
```bash
python orchestrate_complete.py  # or the project's main pipeline entrypoint
```

**Verify**: After running, confirm with:
```bash
ls -l merge_logic.json
```

If the file is missing, check your project's merge logic module or configuration to generate the JSON before summary.

**Alternate paths**: If your merge output is named differently or located elsewhere, update the `MERGE_OUTPUT_FILE` constant at the top of `combined_match_summary.py` accordingly:
```python
MERGE_OUTPUT_FILE = BASE_DIR / "your_actual_filename.json"
```

This step prevents `FileNotFoundError` when opening the merge output and ensures the summary script runs smoothly.

## 7. Testing the Solution

We created a test script called `test_match_formatting.py` to verify the solution with synthetic match data. Run this script to check that the formatting works correctly with various match numbers:

```bash
python3 test_match_formatting.py
```

This will generate entries in the log file with the new centered format.

## 8. Rollback Instructions

If you need to restore default multi-line logging behavior:

1. Revert the formatter in `get_combined_summary_logger()` back to using timestamps:
   ```python
   formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', 
                               '%m/%d/%Y %I:%M:%S %p %Z')
   ```

2. Replace the separate log calls with the original multi-line approach:
   ```python
   summary = f"{header}\nTime: {current_time}\n\n..." 
   logger.info(summary)
   ```

3. Remove the centering logic and formatting code.
