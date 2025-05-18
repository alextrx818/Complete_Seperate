#!/bin/bash
# Script to debug environment variables in systemd context
# line 1-2: Setup comment

# line 4-5: Create timestamped log file
LOG_FILE=/root/Complete_Seperate/logs/env_debug.log
echo "=== ENVIRONMENT DEBUG $(date) ===" >> $LOG_FILE

# line 8-11: Log environment information
echo "USER: $(whoami)" >> $LOG_FILE
echo "PWD: $(pwd)" >> $LOG_FILE
echo "PATH: $PATH" >> $LOG_FILE
env | sort >> $LOG_FILE

# line 14-17: Test API connectivity
echo "=== TESTING API CONNECTIVITY ===" >> $LOG_FILE
curl -s -o /dev/null -w "%{http_code}" https://api.thesports.com/v1/football/match/detail_live >> $LOG_FILE
echo "" >> $LOG_FILE

# line 20-22: Log Python information
echo "=== PYTHON INFO ===" >> $LOG_FILE
which python >> $LOG_FILE
python --version >> $LOG_FILE

# line 25-27: Check virtual environment
echo "=== VIRTUAL ENV ===" >> $LOG_FILE
echo "VIRTUAL_ENV: $VIRTUAL_ENV" >> $LOG_FILE
ls -la /root/Complete_Seperate/sports_venv/bin >> $LOG_FILE
