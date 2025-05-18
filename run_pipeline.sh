#!/bin/bash
# This is the ONLY supported way to start the sports bot pipeline.
# It activates the external virtual environment and runs the orchestrator.

# Fail on any error
set -e

# Change to script directory (use absolute path for cron compatibility)
cd "$(dirname "$0")"

# Ensure logs directory exists with absolute path
mkdir -p /root/Complete_Seperate/logs

# Log start timestamp and PID
echo "$(date) STARTING pipeline (PID $$)" >> /root/Complete_Seperate/logs/cron.log

# Log initial resource usage
echo "RSS: $(ps -o rss= -p $$)kB, FDs: $(ls /proc/$$/fd | wc -l)" >> /root/Complete_Seperate/logs/cron.log

# Print Python info for debugging
echo "$(date) Using Python: $(which python)" >> /root/Complete_Seperate/logs/cron.log
echo "PATH: $PATH" >> /root/Complete_Seperate/logs/cron.log

# Activate virtual environment
source ./sports_venv/bin/activate

# Use flock to prevent overlapping runs
(
    # Try to acquire lock, exit if already locked
    flock -n 9 || { echo "$(date) Pipeline already running, skipping this run" >> /root/Complete_Seperate/logs/cron.log; exit 0; }
    
    # Run the orchestrator
    python orchestrate_complete.py
    EXIT_CODE=$?
    
    # Log exit code
    echo "$(date) EXIT code $EXIT_CODE" >> /root/Complete_Seperate/logs/cron.log
    
    # Log final resource usage
    echo "Final RSS: $(ps -o rss= -p $$)kB, FDs: $(ls /proc/$$/fd | wc -l)" >> /root/Complete_Seperate/logs/cron.log
    
    # Alert on non-zero exit code
    if [ $EXIT_CODE -ne 0 ]; then
        echo "WARNING: Pipeline failed with exit code $EXIT_CODE" >> /root/Complete_Seperate/logs/cron.log
    fi
    
    exit $EXIT_CODE
) 9>/var/run/sports_bot.lock
