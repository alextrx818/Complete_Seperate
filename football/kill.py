#!/usr/bin/env python3
"""
kill.py - A safe kill switch for the sports bot system

This script identifies and gracefully terminates all running sports bot processes.
It provides detailed feedback on which processes were found and terminated.

Usage:
    python3 kill.py          # Run with default options
    python3 kill.py --force  # Force kill processes that don't terminate gracefully

Author: Sports Bot Team
Date: 2025-05-15
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("kill_switch")

# Target processes to look for (lowercase for case-insensitive matching)
TARGET_PROCESSES = [
    "live.py",
    "orchestrate_complete.py",
    "run_pipeline.sh",
    "pure_json_fetch_cache.py",
    "merge_logic.py",
    "alerter_main.py",
    "combined_match_summary.py"
]

def get_process_list():
    """Get a list of all running processes matching our target keywords."""
    try:
        # Run ps command to get process details
        result = subprocess.run(
            ["ps", "-eo", "pid,ppid,cmd"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        process_list = []
        for line in result.stdout.splitlines()[1:]:  # Skip header line
            parts = line.strip().split(None, 2)
            if len(parts) >= 3:
                pid = parts[0]
                ppid = parts[1]
                cmd = parts[2].lower()  # Case-insensitive matching
                
                # Check if this process matches any of our targets
                for target in TARGET_PROCESSES:
                    if target.lower() in cmd:
                        process_list.append({
                            "pid": int(pid),
                            "ppid": int(ppid),
                            "cmd": parts[2],
                            "matched_target": target
                        })
                        break
        
        return process_list
    
    except subprocess.SubprocessError as e:
        logger.error(f"Error getting process list: {e}")
        return []

def kill_process(pid, force=False, wait_time=3):
    """Kill a process by PID with optional force flag."""
    try:
        process_info = subprocess.run(
            ["ps", "-p", str(pid), "-o", "cmd="],
            capture_output=True,
            text=True
        )
        
        process_name = process_info.stdout.strip()
        if not process_name:
            logger.warning(f"Process {pid} not found, may have already terminated")
            return True
        
        if force:
            # SIGKILL - forceful termination
            logger.info(f"Force killing process {pid}: {process_name}")
            os.kill(pid, signal.SIGKILL)
            return True
        else:
            # SIGTERM - graceful termination
            logger.info(f"Sending termination signal to process {pid}: {process_name}")
            os.kill(pid, signal.SIGTERM)
            
            # Wait for the process to terminate
            start_time = time.time()
            while time.time() - start_time < wait_time:
                try:
                    # Check if process still exists
                    os.kill(pid, 0)
                    # Small sleep to avoid CPU spinning
                    time.sleep(0.1)
                except OSError:
                    # Process is gone
                    logger.info(f"Process {pid} terminated gracefully")
                    return True
            
            logger.warning(f"Process {pid} did not terminate after {wait_time}s")
            return False
    
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Kill switch for sports bot processes")
    parser.add_argument("--force", action="store_true", help="Force kill processes (SIGKILL)")
    parser.add_argument("--wait", type=int, default=3, help="Seconds to wait for graceful termination")
    parser.add_argument("--dry-run", action="store_true", help="List processes without killing them")
    args = parser.parse_args()
    
    # Banner
    print("\n" + "="*60)
    print(" SPORTS BOT KILL SWITCH ".center(60, "="))
    print("="*60 + "\n")
    
    # Get all matching processes
    processes = get_process_list()
    
    if not processes:
        logger.info("No running sports bot processes found")
        return
    
    # Group processes by type for better reporting
    process_groups = {}
    for proc in processes:
        target = proc["matched_target"]
        if target not in process_groups:
            process_groups[target] = []
        process_groups[target].append(proc)
    
    # Print process summary
    logger.info(f"Found {len(processes)} sports bot processes running:")
    for target, procs in process_groups.items():
        logger.info(f"- {target}: {len(procs)} {'process' if len(procs) == 1 else 'processes'}")
        for proc in procs:
            logger.info(f"  - PID {proc['pid']}: {proc['cmd'][:60]}")
    
    if args.dry_run:
        logger.info("Dry run - no processes will be killed")
        return
    
    # First pass: attempt graceful termination
    stubborn_processes = []
    for proc in processes:
        success = kill_process(proc["pid"], force=args.force, wait_time=args.wait)
        if not success:
            stubborn_processes.append(proc)
    
    # Second pass: force kill any remaining processes
    if stubborn_processes and not args.force:
        logger.warning(f"{len(stubborn_processes)} processes didn't terminate gracefully")
        response = input("Force kill these processes? [y/N] ").lower()
        
        if response == 'y':
            for proc in stubborn_processes:
                kill_process(proc["pid"], force=True)
    
    # Final verification
    remaining = get_process_list()
    if remaining:
        logger.warning(f"{len(remaining)} sports bot processes still running")
        for proc in remaining:
            logger.warning(f"- PID {proc['pid']}: {proc['cmd'][:60]}")
    else:
        logger.info("All sports bot processes successfully terminated")

if __name__ == "__main__":
    main()
