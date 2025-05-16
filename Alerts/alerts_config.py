# alerts_config.py – Centralized alert parameters

"""
Configuration file for alert satellites.

This module provides a centralized place to configure parameters for all alert scanners.
When adding a new alert satellite, add its configuration parameters here.

The ALERT_PARAMS dictionary is imported by orchestrate_complete.py and passed to 
AlerterMain during initialization.
"""

# Example:
ALERT_PARAMS = {
    "OverUnderAlert": {"threshold": 3.0},
    # Add other alerts here as you create them:
    # "MyNewAlert": {"paramA": "foo", "paramB": 42},
}
