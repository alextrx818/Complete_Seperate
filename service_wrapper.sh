#!/bin/bash
# line 1-2: Robust service wrapper for Football Match Tracking System
# Ensures proper environment setup and provides detailed diagnostics

# line 4-6: Set strict error handling and ensure proper execution
set -e
cd "$(dirname "$0")"

# line 8-11: Create logs directory and setup logging
mkdir -p logs
LOGFILE="logs/service_wrapper.log"
echo "===============================================" >> $LOGFILE
echo "$(date) Starting service wrapper (PID: $$)" >> $LOGFILE

# line 14-19: Kill any potentially stuck processes (more than 5 minutes old)
echo "Checking for stuck processes..." >> $LOGFILE
ps aux | grep orchestrate_complete.py | grep -v grep >> $LOGFILE || true
for pid in $(ps aux | grep "[o]rchestrate_complete.py" | awk '{if ($10 ~ /[0-9]+:[0-9][0-9]/ && $10 !~ /^0:/) print $2}'); do
    echo "Killing stuck process $pid (running too long)" >> $LOGFILE
    kill -9 $pid 2>/dev/null || true
done

# line 22-24: Remove any stale lock files
echo "Removing any stale locks..." >> $LOGFILE
rm -f /var/run/sports_bot.lock 2>/dev/null || true

# line 26-30: Check and record system resources
echo "System resources before execution:" >> $LOGFILE
echo "Memory: $(free -m | grep Mem | awk '{print $3 "MB used, " $4 "MB free"}')" >> $LOGFILE
echo "Disk: $(df -h . | tail -1 | awk '{print $5 " used, " $4 " free"}')" >> $LOGFILE
echo "Load: $(cat /proc/loadavg)" >> $LOGFILE

# line 32-37: Ensure the virtual environment is properly activated
echo "Activating virtual environment..." >> $LOGFILE
export VIRTUAL_ENV=$(pwd)/sports_venv
export PATH="$VIRTUAL_ENV/bin:$PATH"
echo "Python: $(which python)" >> $LOGFILE
echo "Environment: VIRTUAL_ENV=$VIRTUAL_ENV" >> $LOGFILE
echo "PATH=$PATH" >> $LOGFILE

# line 39-42: Set explicit timeouts and connection parameters
export API_TIMEOUT=30
export HTTP_TIMEOUT=30
export PYTHONUNBUFFERED=1
export LOG_STRICT=0

# line 44-46: Run the pipeline with explicit timeout
echo "$(date) Executing pipeline with 10 minute timeout..." >> $LOGFILE
timeout 600 python orchestrate_complete.py >> $LOGFILE 2>&1
EXIT_CODE=$?

# line 49-57: Report completion and status
echo "$(date) Pipeline exited with code: $EXIT_CODE" >> $LOGFILE
if [ $EXIT_CODE -eq 124 ]; then
    echo "ERROR: Pipeline TIMED OUT after 10 minutes!" >> $LOGFILE
elif [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: Pipeline failed with exit code $EXIT_CODE" >> $LOGFILE
else
    echo "SUCCESS: Pipeline completed successfully" >> $LOGFILE
fi

# line 59-60: Final resource check
echo "Final memory: $(free -m | grep Mem | awk '{print $3 "MB used"}')" >> $LOGFILE
exit $EXIT_CODE
