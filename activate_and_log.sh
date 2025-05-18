#!/bin/bash
# line 1-2: Environment activation and logging script for football_bot service
# Ensures clean activation and proper journal integration

# line 4-6: Activate the virtual environment
cd "$(dirname "$0")"
source sports_venv/bin/activate

# line 8-12: Log environment information to journal with proper tagging
logger -t football_bot "ACTIVATION: Starting service with environment details"
logger -t football_bot "VIRTUAL_ENV=$VIRTUAL_ENV"
logger -t football_bot "PYTHON=$(which python)"
logger -t football_bot "PYTHON_VERSION=$(python --version 2>&1)"
logger -t football_bot "PATH=$PATH"

# line 14-16: Report success and exit with proper code
logger -t football_bot "ACTIVATION: Environment setup complete"
exit 0
