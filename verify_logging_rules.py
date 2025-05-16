#!/usr/bin/env python3
"""
This script validates that all logging system rules are correctly implemented:
1. Newest-first log entries
2. Persistent match counter
3. Match summary formatting
4. Eastern Time Zone for all timestamps
"""
import sys
import os
import time
from pathlib import Path

# Force reload of the logging configuration
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if 'log_config' in sys.modules:
    del sys.modules['log_config']

# Now import the logging modules
import log_config
from combined_match_summary import write_combined_match_summary

# Test loggers
orchestrator = log_config.get_logger(log_config.ORCHESTRATOR_LOGGER)
merge_logic = log_config.get_logger(log_config.MERGE_LOGIC_LOGGER)
memory_monitor = log_config.get_logger(log_config.MEMORY_MONITOR_LOGGER)

print("===== LOGGING RULES VERIFICATION =====")

# 1. Test various loggers to verify newest-first entries
print("\n1. Testing various loggers with newest-first entries:")
orchestrator.info("ORCHESTRATOR TEST 1: This should appear at the top of the log")
time.sleep(1)  # Small delay to ensure timestamps differ
orchestrator.info("ORCHESTRATOR TEST 2: This should appear above TEST 1")
time.sleep(1)

merge_logic.info("MERGE_LOGIC TEST 1: This should appear at the top of the merge log")
time.sleep(1)
merge_logic.info("MERGE_LOGIC TEST 2: This should appear above TEST 1")
time.sleep(1)

memory_monitor.info("MEMORY_MONITOR TEST 1: This should appear at the top of the memory monitor log")
time.sleep(1)
memory_monitor.info("MEMORY_MONITOR TEST 2: This should appear above TEST 1")

# 2. Check the match counter file status
print("\n2. Checking match counter file:")
match_id_file = Path(__file__).parent / "match_id.txt"
if match_id_file.exists():
    with open(match_id_file, 'r') as f:
        current_id = f.read().strip()
    print(f"  Current match ID: {current_id}")
else:
    print("  match_id.txt not found")

# 3. Test match summary formatting
print("\n3. Testing match summary formatting:")
# Sample match data
sample_match = {
    "competition": "Premier League",
    "country": "England",
    "home_team": "Liverpool FC",
    "away_team": "Chelsea FC",
    "status_id": 3,
    "score": [None, None, [2, 1], [1, 0]],
    "odds": {},
    "environment": {
        "weather": "Rainy",
        "temperature": 62,
        "humidity": 75,
        "wind": "Light Breeze, 8 mph"
    }
}

# Write two match summaries to test increment and newest-first
print("  Writing first match summary...")
write_combined_match_summary(sample_match)
time.sleep(1)
print("  Writing second match summary...")
write_combined_match_summary(sample_match)

# 4. Verify the logs have newest-first entries
print("\n4. Verification steps:")
print("  a. Check orchestrator.log - newest entries should be at the top")
print("  b. Check logs/combined_match_summary.logger - newest match should be at the top")
print("  c. Verify match_id.txt has incremented properly")

print("\nTo check log entries, run:")
print("  head -n 20 logs/orchestrator.log")
print("  head -n 20 logs/combined_match_summary.logger")

# 5. Show the current match ID
with open(match_id_file, 'r') as f:
    final_id = f.read().strip()
print(f"\nFinal match ID: {final_id}")

print("\n===== VERIFICATION COMPLETE =====")
