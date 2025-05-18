#!/usr/bin/env python3
"""
Diagnostic script to analyze the logging behavior in the sports_bot project.
This is a temporary file that can be deleted after diagnostics are complete.
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

print("\n===== LOGGING DIAGNOSTIC REPORT =====")

# 1. Test the combined summary logger configuration
summary_logger = get_combined_summary_logger()

# Detailed handler inspection
print("[DIAG] summary logger handlers:", summary_logger.handlers)
print(f"\nTest 1: Summary Logger Configuration")
print(f"Handler count: {len(summary_logger.handlers)}")

for i, handler in enumerate(summary_logger.handlers):
    handler_type = type(handler).__name__
    print(f"  Handler {i+1}: {handler_type}")
    # Get the actual handler instance for deeper inspection
    print(f"    Handler instance: {handler}")
    print(f"    Is closed: {getattr(handler, 'closed', 'N/A')}")
    print(f"    Formatter: {type(handler.formatter).__name__}")
    
    if hasattr(handler, 'baseFilename'):
        print(f"    File: {handler.baseFilename}")
        
    if hasattr(handler, 'formatter'):
        fmt_string = getattr(handler.formatter, '_fmt', None)
        date_fmt = getattr(handler.formatter, 'datefmt', None)
        print(f"    Format string: {fmt_string}")
        print(f"    Date format: {date_fmt}")
        
        # Check the converter
        if hasattr(handler.formatter, 'converter'):
            converter_name = handler.formatter.converter.__name__ if hasattr(handler.formatter.converter, '__name__') else str(handler.formatter.converter)
            print(f"    Converter: {converter_name}")

# 2. Test multi-line message behavior
print(f"\nTest 2: Multi-line Message Behavior")
print("Logging a multi-line message to see how it appears in the log:")
print('logger.info("LINE1\\nLINE2")')
summary_logger.info("LINE1\nLINE2")
print("Check the log file to see how that was formatted.")

# More specific multi-line tests
print("\nAdditional multi-line tests:")
summary_logger.info("FIRST LINE\nSECOND LINE")

# Test with a blank line
print("\nTesting with a blank line:")
summary_logger.info("\nContent after blank line")

# Test with multiple blank lines
print("\nTesting with multiple blank lines:")
summary_logger.info("\n\nContent after two blank lines")

# 3. Inspect a sample summary string
header = f"{'=' * 20} MATCH 999/999 {'=' * 20}"
current_time = get_eastern_time().strftime("%m/%d/%Y %I:%M:%S %p %Z")
sample_summary = f"{header}\nTime: {current_time}\n\nCompetition: Test Competition\nMatch: Team A vs Team B"

print(f"\nTest 3: Sample Summary String Analysis")
print(f"repr(summary) = {repr(sample_summary)}")
print(f"summary starts with newline: {sample_summary.startswith('\\n')}")
print(f"newlines before header text: {sample_summary[:20].count('\\n')}")

# 4. Test split vs single call
print(f"\nTest 4: Split vs Single Call")
print("a) Logging the header separately:")
summary_logger.info(header)
print("b) Logging the time separately:")
summary_logger.info(f"Time: {current_time}")
print("c) Now logging them together in one call:")
summary_logger.info(f"{header}\nTime: {current_time}")

print("\n===== DIAGNOSTIC COMPLETE =====")
print("You can now check the logs for the results and delete this file.")
