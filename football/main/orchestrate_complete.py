#!/usr/bin/env python3
"""
orchestrate_complete.py - Main orchestration script for the sports betting data pipeline

IMPORTANT NOTE: This script should normally be executed through the run_pipeline.sh wrapper,
which provides:
- Process locking (via flock) to prevent multiple instances running simultaneously
- Head-insertion logging to orchestrator.log (newest entries at the top)
- Virtual environment activation at ./sports_venv/

To run properly:
    $ ./run_pipeline.sh

Not recommended to run directly:
    $ python3 orchestrate_complete.py

VIRTUAL ENVIRONMENT REQUIREMENTS:
The script depends on a virtual environment located at ./sports_venv/ with the following
key dependencies:
- requests: For sending Telegram notifications
- pytz: For timezone handling (America/New_York)
- aiohttp: For asynchronous HTTP requests
- propcache: For data caching

Installation (if needed):
    $ cd football/main
    $ python -m venv sports_venv
    $ ./sports_venv/bin/pip install requests pytz aiohttp propcache

The run_pipeline.sh wrapper automatically activates this environment.
"""

"""
=================================================================================
COMPLETE SPORTS BOT PROJECT STRUCTURE AND DATA FLOW
=================================================================================

Project Architecture
-------------------
The sports bot in this folder is a modular football match data processing pipeline
with two parallel output branches working on the same underlying data.

Main Components & Data Flow
-------------------------
1. orchestrate_complete.py: Core orchestration engine that controls the workflow
2. run_pipeline.sh: Shell wrapper script that executes the orchestration engine
3. pure_json_fetch_cache.py: Fetches & caches API data → outputs to full_match_cache.json
4. merge_logic.py: Combines and enriches match data → outputs to merge_logic.json

Complete Execution Pipeline
-------------------------
STEP 1: JSON fetch via pure_json_fetch_cache.py
   ↓
STEP 2: Prepare data for merge (unpack from cache)
   ↓
STEP 3: Run merge logic via merge_logic.py (creates enriched match data)
   ↓
STEP 4: Save output files (merge_logic.json, complete_cache_output.json)
   ↓
STEP 4.25: Generate summary JSON via summary_json_generator.py (creates summary_data.json)
   ↓
   ├────────────────────┐
   ↓                    ↓
STEP 4.5: Alert scan   STEP 5: Print summaries
   ↓                    ↓
AlerterMain system     combined_match_summary.py
   ↓                    ↓
OU3.py detection       complete_summary.logger
   ↓
OU3.logger

Key Fork in Processing Pipeline
----------------------------
After data is fetched, merged and saved, the pipeline splits into two parallel branches:

Branch 1: Alert System (STEP 4.5)
- Purpose: Monitor matches for high Over/Under betting lines (≥3.0)
- Key Files: 
  - Alerts/alerter_main.py: Alert orchestration system
  - Alerts/OU3.py: Over/Under line detection module
  - Alerts/*.logger: Alert log files
- Output: Alerts logged and potentially sent as notifications

Branch 2: Summary Generation (STEP 5)
- Purpose: Generate human-readable formatted match summaries
- Key Files:
  - combined_match_summary.py: Formats match data for human readability
  - complete_summary.logger: Stores formatted match summaries
- Output: Comprehensive match summaries with formatted sections

Data Files & Outputs
------------------
- full_match_cache.json - Raw API data from fetch operation
- merge_logic.json - Enriched match data after processing
- summary_data.json - Structured JSON with summary fields
- complete_summary.logger - Human-readable match summaries

Log Files:
- orchestrator.log - Main orchestration process log
- summary_json.logger - Log of summary JSON generation
- OU3.logger - Log of Over/Under alerts

This architecture provides clear separation of concerns, making the system
modular and maintainable while allowing both alert and summary generation
to work independently on the same underlying data.
"""

import asyncio
import json
import logging
import os
import sys
import time
import subprocess
import gc
import psutil
from datetime import datetime
import pytz
from pathlib import Path

# Import memory monitoring tool
sys.path.append(str(Path(__file__).parent))
import memory_monitor
import logger_monitor

# Import centralized logging configuration
from log_config import get_logger, validate_logger_count, cleanup_handlers

# Cache the timezone object at module scope
TZ = pytz.timezone("America/New_York")

# Import fetch and merge modules
sys.path.append(Path(__file__).parent.as_posix())
import pure_json_fetch_cache
from merge_logic import merge_all_matches
from combined_match_summary import get_status_description

# Import summary JSON generator
from summary_json_generator import write_summary_json

# Import the new alert system
from Alerts.alerter_main import AlerterMain
from Alerts.OU3 import OverUnderAlert

# Define the exact status_id sequence you care about:
DESIRED_STATUS_ORDER = ["2","3","4","5","6","8","13"]

# Constants
BASE_DIR = Path(__file__).parent
FULL_CACHE_FILE = BASE_DIR / "full_match_cache.json"
OUTPUT_FILE = BASE_DIR / "complete_cache_output.json"
MERGE_OUTPUT_FILE = BASE_DIR / "merge_logic.json"
SUMMARY_SCRIPT = BASE_DIR / "combined_match_summary.py"

# Get pre-configured logger from centralized configuration
logger = get_logger("orchestrator")

# Setup a dedicated logger for match summaries - only for console output now
def setup_summary_logger():
    sum_log = get_logger("summary")
    sum_log.setLevel(logging.INFO)
    # Prevent propagation to root logger
    sum_log.propagate = False
    
    return sum_log

summary_logger = setup_summary_logger()

def get_eastern_time():
    # Use the cached timezone object for better performance
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")

# Prepending logic moved to wrapper script

def unpack_full_cache(full_cache: dict):
    live = {"results": []}
    details = {}
    odds = {}
    team_cache = {}
    comp_cache = {}
    country_map = {}

    for m in full_cache.get("matches", []):
        mid = m.get("match_id")
        basic = m.get("basic_info", {})
        live["results"].append(basic)
        details[mid] = m.get("details", {})
        odds[mid] = m.get("odds", {})

        # teams
        for role in ("home_team", "away_team"):
            t = m.get("enriched", {}).get(role, {})
            tid = t.get("id")
            if tid:
                team_cache[tid] = t

        # competition
        comp = m.get("enriched", {}).get("competition", {})
        cid = comp.get("id")
        if cid:
            comp_cache[cid] = comp

        # country
        country_id = comp.get("country_id")
        country_name = m.get("metadata", {}).get("country_name")
        if country_id and country_name:
            country_map[country_id] = country_name

    return live, details, odds, team_cache, comp_cache, country_map

async def run_complete_pipeline():
    """Run the complete pipeline consisting of all steps."""
    
    # Log cache sizes and memory stats
    memory_monitor.log_cache_sizes()
    
    # Check file descriptor count
    memory_monitor.check_file_descriptor_count()
    
    logger.info("STEP 1: JSON fetch")
    match_ids = await pure_json_fetch_cache.main()
    
    logger.info("STEP 2: Merge and enrichment")
    full_cache = json.loads(FULL_CACHE_FILE.read_text())
    live_data, details_by_id, odds_by_id, team_cache, comp_cache, country_map = unpack_full_cache(full_cache)
    merged_data = merge_all_matches(
        live_data, details_by_id, odds_by_id,
        team_cache, comp_cache, country_map
    )
    merged_data = [{"created_at": get_eastern_time(), **m} for m in merged_data]
    
    # Sort strictly by our status_id order; any others fall to the end
    merged_data = sorted(
        merged_data,
        key=lambda m: (
            DESIRED_STATUS_ORDER.index(m.get("status_id")) 
              if m.get("status_id") in DESIRED_STATUS_ORDER 
              else len(DESIRED_STATUS_ORDER)
        )
    )
    
    logger.info(f"Merged {len(merged_data)} records")
    
    logger.info("STEP 3: Generate summary JSON")
    summary_json = write_summary_json(merged_data)
    
    logger.info("STEP 4: Run alerters")
    await run_alerters(summary_json, match_ids)
    
    logger.info("Pipeline complete")
    
    # Dump garbage collection stats
    memory_monitor.dump_gc_stats()

async def run_alerters(summary_json, match_ids):
    # Create alert instances
    alerts = [
        OverUnderAlert(threshold=3.0),  # O/U ≥ 3.00
    ]
    
    # Create AlerterMain instance
    alerter = AlerterMain(alerts=alerts)
    
    # Process all matches with AlerterMain
    # This follows the architecture where alerter_main.py handles orchestration,
    # deduplication, formatting and notification
    logger.info(f"Processing {len(summary_json['matches'])} matches through AlerterMain")
    
    # Let the AlerterMain system process the matches
    for match in summary_json['matches']:
        # Ensure we have a match_id in the expected format
        match_id = match.get("match_id") or match.get("id")
        if not match_id:
            continue
            
        # Check each registered alert
        for alert in alerter.alerts:
            # Check if this alert is triggered
            notice = alert.check(match)
            
            # Only proceed if alert triggers and not already seen
            file_base_id = alerter.alert_file_bases[id(alert)]
            if notice and match_id not in alerter.seen_ids[file_base_id]:
                # Process this match - this will handle formatting, logging and notifications
                logger.info(f"Alert {file_base_id} triggered for match {match_id}")
                
                # Mark as seen for deduplication
                alerter.seen_ids[file_base_id].add(match_id)
                alerter._save_seen(file_base_id)

def print_instructions():
    """Print instructions for scheduling the pipeline using cron"""
    logger.info("""
=== SCHEDULING INSTRUCTIONS ===

To run this pipeline every 30 seconds using cron:

1. Create a shell script wrapper (run_pipeline.sh):
   #!/bin/bash
   cd /root/CascadeProjects/sports_bot/football/main
   python orchestrate_complete.py

2. Make it executable: chmod +x run_pipeline.sh

3. Add to crontab (every minute, it will handle its own rate limiting):
   * * * * * /root/CascadeProjects/sports_bot/football/main/run_pipeline.sh

Alternatively, use a simple while loop in a shell script:
   while true; do
     python orchestrate_complete.py
     sleep 30
   done
""")

if __name__ == "__main__":
    # Initialize process and memory monitoring
    proc = psutil.Process(os.getpid())
    start_mem = proc.memory_info().rss / (1024*1024)
    logger.info(f"Starting memory: {start_mem:.1f} MB")
    
    # Check for open file descriptors
    try:
        fd_count = len(os.listdir(f"/proc/{proc.pid}/fd"))
        logger.info(f"Initial FD count: {fd_count}")
    except Exception as e:
        logger.warning(f"Could not check file descriptors: {e}")
    
    # Validate initial logger and handler counts
    logger.info("Validating initial logger and handler counts...")
    if not validate_logger_count():
        logger.error("Logger validation failed! Exiting to prevent memory leaks.")
        sys.exit(1)
    
    logger.info(f"Initial logger count: {len(logging.Logger.manager.loggerDict)}")
    logger.info("Initial logger validation passed.")
    
    try:
        # Run the pipeline
        cycle_count = 0
        max_cycles = 10  # Run for 10 cycles to gather meaningful data
        
        while cycle_count < max_cycles:
            logger.info(f"\n===== RUNNING CYCLE {cycle_count} =====")
            
            # Start memory monitoring for this cycle
            memory_monitor.start_cycle_monitoring()
            
            # Run the pipeline
            asyncio.run(run_complete_pipeline())
            
            # End memory monitoring for this cycle
            memory_monitor.end_cycle_monitoring()
            
            cycle_count += 1
            
            # Print current memory usage after each cycle
            curr_mem = proc.memory_info().rss / (1024*1024)
            delta_mem = curr_mem - start_mem
            logger.info(f"Current memory: {curr_mem:.1f} MB ({delta_mem:+.1f} MB from start)")
            
            # Validate logger and handler counts after each cycle
            logger.info("Validating logger and handler counts after cycle...")
            if not validate_logger_count():
                logger.error("Logger validation failed after cycle! Exiting to prevent memory leaks.")
                sys.exit(1)
                
            logger.info(f"Current logger count: {len(logging.Logger.manager.loggerDict)}")
            
            # Count top types of objects
            counts = {}
            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                if obj_type not in counts:
                    counts[obj_type] = 0
                counts[obj_type] += 1
            
            # Log top 10 most common object types
            top_types = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
            logger.info(f"Top 10 object types: {top_types}")
            
            # Sleep between cycles
            logger.info("Sleeping for 3 seconds between cycles...")
            time.sleep(3)
        
        logger.info("\n===== ALL CYCLES COMPLETE =====")
        logger.info("Memory monitoring complete. Check logs/memory/memory_monitor.log for detailed results.")
        
        # Log final logger count
        logger.info(f"Final logger count: {len(logging.Logger.manager.loggerDict)}")
    
    except Exception as e:
        logger.exception(f"Error during pipeline execution: {e}")
    
    finally:
        # Always perform cleanup of all handlers
        logger.info("Cleaning up all handlers to release file descriptors...")
        cleanup_handlers()
        logger.info("Handler cleanup complete.")
        
        # Count top types of objects
        counts = {}
        for obj in gc.get_objects():
            t = type(obj).__name__
            counts[t] = counts.get(t, 0) + 1
        for t, cnt in sorted(counts.items(), key=lambda x: -x[1])[:5]:
            logger.info(f"  {t}: {cnt}")
    
    # Log final logger count
    logger.info(f"Final logger count: {len(logging.Logger.manager.loggerDict)}")
    
    # Perform cleanup of all handlers
    logger.info("Cleaning up all handlers to release file descriptors...")
    cleanup_handlers()
    logger.info("Handler cleanup complete.")
