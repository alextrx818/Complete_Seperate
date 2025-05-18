#!/bin/bash
# line 1-2: Robust service wrapper for Football Match Tracking System
# Ensures proper environment setup and provides detailed diagnostics

# line 4-6: Set strict error handling and ensure proper execution
set -e
cd "$(dirname "$0")"

# line 8-11: Create logs directory and setup logging with absolute paths
mkdir -p /root/Complete_Seperate/logs
LOGFILE="/root/Complete_Seperate/logs/service_wrapper.log"
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

# line 32-40: Log the already activated virtual environment with both file and journal logging
echo "Using pre-activated virtual environment..." >> $LOGFILE
echo "Python: $(which python)" >> $LOGFILE
echo "Environment: VIRTUAL_ENV=$VIRTUAL_ENV" >> $LOGFILE
echo "PATH=$PATH" >> $LOGFILE

# line 37-38: Ensure logs directory exists with absolute paths
mkdir -p /root/Complete_Seperate/logs
LOG_TIMING="/root/Complete_Seperate/logs/logging_timing.log"
LOG_PERF="/root/Complete_Seperate/logs/performance_timings.log"

# lines 41-45: Optimized consolidated logging pattern with reduced frequency
# Only log environment info once at service start if not already logged today
ENV_LOG_FILE="/root/Complete_Seperate/logs/env_logged_$(date +%Y%m%d).flag"
start=$(date +%s%N)
if [[ ! -f "$ENV_LOG_FILE" ]]; then
  {
    echo "Environment: VIRTUAL_ENV=$VIRTUAL_ENV, PYTHON=$(which python)"
    echo "PATH=$PATH"
    echo "SERVICE_START: Environment logged at $(date)"
  } | systemd-cat -t football_bot
  touch "$ENV_LOG_FILE"
fi

# lines 47-48: Cycle-specific logging (minimal overhead)
{ echo "CYCLE: Starting new pipeline cycle at $(date)" | systemd-cat -t football_bot; }
end=$(date +%s%N)
echo "CONSOLIDATED_LOG_TIME=$((end-start))" >> $LOG_TIMING

# line 39-42: Set explicit timeouts and connection parameters
export API_TIMEOUT=30
export HTTP_TIMEOUT=30
export PYTHONUNBUFFERED=1
export LOG_STRICT=0

# lines 60-70: Run the pipeline with explicit timeout and performance measurement points
echo "$(date) Executing pipeline with 10 minute timeout..." >> $LOGFILE

# line 63-64: Performance measurement - fetch start
echo "FETCH_START=$(date +%s%N)" | systemd-cat -t football_bot

# line 66: Use asynchronous logging for non-critical status updates
{ echo "STATUS: Pipeline started" | systemd-cat -t football_bot & }

timeout 600 python orchestrate_complete.py >> $LOGFILE 2>&1
EXIT_CODE=$?

# line 72: Performance measurement - fetch end
echo "FETCH_END=$(date +%s%N)" | systemd-cat -t football_bot
fetch_end=$(date +%s%N)
echo "TOTAL_RUNTIME_NS=$((fetch_end-start))" >> $LOG_PERF

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
