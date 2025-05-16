#!/usr/bin/env python3
"""
Diagnostic script to check logging configuration issues:
1. How headers are emitted and if timestamps are added
2. What formatter the summary logger is using
3. If SingleLineFormatter is being used for multi-line messages
"""
import logging
import sys
import os
from pathlib import Path

# Add the current directory to the path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Force reload of modules
if 'log_config' in sys.modules:
    del sys.modules['log_config']
if 'combined_match_summary' in sys.modules:
    del sys.modules['combined_match_summary']

# Import our modules
from log_config import get_logger, SUMMARY_LOGGER, LOGGING_CONFIG
from combined_match_summary import write_combined_match_summary, get_combined_summary_logger

print("\n===== LOGGING DIAGNOSTICS =====\n")

# 1. Check summary logger formatters
print("1. SUMMARY LOGGER FORMATTERS:")
logger = get_logger(SUMMARY_LOGGER)
if logger:
    print(f"  Summary logger has {len(logger.handlers)} handlers")
    for i, h in enumerate(logger.handlers):
        fmt_string = getattr(h.formatter, '_fmt', "Unknown")
        print(f"  [DIAG] Handler {i} ({type(h).__name__}): formatter = {fmt_string}")
        if hasattr(h.formatter, '__class__') and hasattr(h.formatter.__class__, '__name__'):
            print(f"  [DIAG] Formatter class: {h.formatter.__class__.__name__}")
        if hasattr(h, 'baseFilename'):
            print(f"  [DIAG] File: {h.baseFilename}")
        if fmt_string and '%(asctime)s' in fmt_string:
            print(f"  [WARNING] This handler adds timestamps to every log message!")
else:
    print("  Summary logger not found")

# 2. Check for SingleLineFormatter in config
print("\n2. CHECKING FOR SINGLELINEFORMATTER:")
formatters_config = LOGGING_CONFIG.get("formatters", {})
for name, fmt_config in formatters_config.items():
    factory = fmt_config.get("()", None)
    print(f"  Formatter '{name}': factory = {factory}")
    if factory == "log_config.SingleLineFormatter":
        print(f"  [GOOD] Found SingleLineFormatter for '{name}'")
    else:
        print(f"  Format string: {fmt_config.get('format', 'Not specified')}")

# 3. Check how match headers are emitted
print("\n3. EXAMINING COMBINED_MATCH_SUMMARY.PY:")
import inspect
from combined_match_summary import write_combined_match_summary

# Get the source code for the function
source_lines = inspect.getsource(write_combined_match_summary)
print("  Relevant lines from write_combined_match_summary:")
for line in source_lines.splitlines():
    if "logger.info" in line or "match_line" in line or "ts_line" in line:
        print(f"  {line.strip()}")

# 4. Test a simple multi-line log message
print("\n4. TESTING MULTI-LINE LOG MESSAGE:")
test_logger = get_combined_summary_logger()
multi_line_msg = """This is a test message
with multiple lines
to see if each line gets a timestamp prefix."""

print("  Logging multi-line message to summary logger...")
test_logger.info(multi_line_msg)
print("  Check logs/combined_match_summary.logger to see if each line got a timestamp")

print("\n===== DIAGNOSTICS COMPLETE =====\n")

# 5. Suggest fixes
print("SUGGESTED FIXES:")
print("1. If handlers have '%(asctime)s' in formatter, update LOGGING_CONFIG formatters")
print("2. If missing SingleLineFormatter, add this class to log_config.py:")
print("""
class SingleLineFormatter(logging.Formatter):
    \"\"\"Special formatter that doesn't add timestamps to continuation lines.\"\"\"
    def format(self, record):
        message = super().format(record)
        # Only first line gets timestamp prefix, continuation lines are raw
        if '\\n' in message:
            first_line, rest = message.split('\\n', 1)
            return first_line + '\\n' + rest
        return message
""")
print("3. Update LOGGING_CONFIG formatters to use:")
print("""
"summary_formatter": {
    "()": "log_config.SingleLineFormatter",
    "format": "%(message)s"  # No timestamp prefix at all
}
""")

# Check exact log writing technique
print("\n5. EXACT LOG LINE EMISSION:")
print("""If you're doing multiple logger.info() calls, each gets its own timestamp.
Instead, build the entire message as a single string:

full_message = f\"\"\"
{match_line}
{ts_line}

Competition: {competition} ({country})
...
\"\"\"
logger.info(full_message)  # Single call with complete message
""")
