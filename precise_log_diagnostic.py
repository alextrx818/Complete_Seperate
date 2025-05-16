#!/usr/bin/env python3
"""
Precise diagnostic script to analyze the specific logging behaviors
"""
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the project's logging configuration and functions
from log_config import get_logger
from combined_match_summary import get_combined_summary_logger, get_eastern_time

print("\n===== PRECISE LOGGING DIAGNOSTIC =====")

# 1. Get the summary logger and check handlers
summary_logger = get_combined_summary_logger()

# Handler & formatter check
print("\n[TEST 1] Handler & Formatter Check:")
print("[DIAG] summary.handlers =", [type(h).__name__ for h in summary_logger.handlers])
for h in summary_logger.handlers:
    print("    →", h, "fmt=", getattr(h.formatter, '_fmt', None))

# 2. Per-line prefix test
print("\n[TEST 2] Per-Line Prefix Test:")
print("logger.info(\"TEST1\\nTEST2\\nTEST3\")")
summary_logger.info("TEST1\nTEST2\nTEST3")

# 3. Create a sample summary similar to what's in the code
header = f"{'=' * 20} MATCH 999/999 {'=' * 20}"
current_time = get_eastern_time().strftime("%m/%d/%Y %I:%M:%S %p %Z")
    
# Simulate what happens in write_combined_match_summary
summary = f"{header}\nTime: {current_time}\n\nCompetition: Test Competition\nMatch: Team A vs Team B"

# Raw summary contents check
print("\n[TEST 3] Raw Summary Check:")
print("[DIAG] repr(summary) =", repr(summary))
print("[DIAG] summary starts with newline:", summary.startswith('\n'))
print("[DIAG] newlines before header:", summary[:len(header)].count('\n'))
print("[DIAG] total newlines in summary:", summary.count('\n'))

# Log the test summary
print("\n[TEST 4] Logging Sample Summary:")
print("About to log summary...")
summary_logger.info(summary)
print("Summary logged - check output above and in log file")

# 5. Experiment with different formats
print("\n[TEST 5] Different Format Experiment:")

# No newlines
summary_logger.info(f"NO-NEWLINES HEADER - {current_time} - Test match")

# With exactly one newline after header
one_nl = f"ONE-NEWLINE HEADER\nTime: {current_time} - Test match"
print("Logging with one newline:")
print("[DIAG] repr(one_nl) =", repr(one_nl))
summary_logger.info(one_nl)

# With blank line after header
with_blank = f"WITH-BLANK HEADER\n\nTime: {current_time} - Test match"
print("Logging with blank line:")
print("[DIAG] repr(with_blank) =", repr(with_blank))
summary_logger.info(with_blank)

# Read the log file to display exactly what was written
print("\n===== LOG FILE CONTENTS =====")
try:
    log_path = Path("logs/combined_match_summary.logger")
    if log_path.exists():
        with open(log_path, "r") as f:
            tail_lines = f.readlines()[-20:]  # Get last 20 lines
            for i, line in enumerate(tail_lines):
                print(f"Line {i+1}: {repr(line)}")
except Exception as e:
    print(f"Error reading log file: {e}")

print("\n===== DIAGNOSTIC COMPLETE =====")
