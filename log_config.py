#!/usr/bin/env python3
"""
log_config.py - Centralized logging configuration for the sports bot

This module provides a single, centralized configuration for all loggers
in the sports bot, ensuring consistent handler management and preventing
logger/handler proliferation.
"""

import os
import logging
import logging.config
from pathlib import Path
import sys

# Base directories
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"

# Ensure log directories exist
for log_dir in [
    LOGS_DIR,
    LOGS_DIR / "fetch",
    LOGS_DIR / "summary",
    LOGS_DIR / "alerts",
    LOGS_DIR / "memory",
    LOGS_DIR / "monitor",
]:
    log_dir.mkdir(exist_ok=True, parents=True)

# Logger names
ORCHESTRATOR_LOGGER = "orchestrator"
FETCH_CACHE_LOGGER = "pure_json_fetch"
FETCH_DATA_LOGGER = "fetch_data"
MERGE_LOGIC_LOGGER = "merge_logic"
SUMMARY_JSON_LOGGER = "summary_json"
MEMORY_MONITOR_LOGGER = "memory_monitor"
LOGGER_MONITOR_LOGGER = "logger_monitor"
SUMMARY_LOGGER = "summary"
OU3_LOGGER = "OU3"

# Central logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(message)s",
            "datefmt": "%m/%d/%Y %I:%M:%S %p %Z",
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "orchestrator_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": str(LOGS_DIR / "orchestrator.log"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf8",
        },
        "fetch_cache_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "pure_json_fetch.log"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf8",
        },
        "fetch_data_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "fetch" / "fetch_data.log"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf8",
        },
        "merge_logic_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "fetch" / "merge_logic.log"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf8",
        },
        "summary_json_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": str(LOGS_DIR / "summary" / "summary_json.logger"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf8",
        },
        "memory_monitor_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "memory" / "memory_monitor.log"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf8",
        },
        "logger_monitor_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "monitor" / "logger_monitor.log"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf8",
        },
    },
    "loggers": {
        ORCHESTRATOR_LOGGER: {
            "level": "INFO",
            "handlers": ["console", "orchestrator_file"],
            "propagate": False,
        },
        FETCH_CACHE_LOGGER: {
            "level": "DEBUG",
            "handlers": ["fetch_cache_file"],
            "propagate": False,
        },
        FETCH_DATA_LOGGER: {
            "level": "INFO",
            "handlers": ["fetch_data_file"],
            "propagate": False,
        },
        MERGE_LOGIC_LOGGER: {
            "level": "DEBUG",
            "handlers": ["merge_logic_file"],
            "propagate": False,
        },
        SUMMARY_JSON_LOGGER: {
            "level": "INFO",
            "handlers": ["summary_json_file"],
            "propagate": False,
        },
        MEMORY_MONITOR_LOGGER: {
            "level": "INFO",
            "handlers": ["memory_monitor_file", "console"],
            "propagate": False,
        },
        LOGGER_MONITOR_LOGGER: {
            "level": "INFO",
            "handlers": ["logger_monitor_file", "console"],
            "propagate": False,
        },
        SUMMARY_LOGGER: {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        OU3_LOGGER: {
            "level": "INFO",
            "handlers": [],  # Handlers will be added by the alert system
            "propagate": False,
        },
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console"],
    },
}

# Dictionary to track alert loggers that have been configured
_configured_alert_loggers = set()

def configure_logging():
    """
    Configure all loggers using dictConfig.
    This should be called once at application startup.
    """
    logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(name):
    """
    Get a properly configured logger by name.
    If the logger has already been configured in dictConfig, returns it.
    """
    return logging.getLogger(name)

def configure_alert_logger(alert_name):
    """
    Configure a logger for a specific alert.
    Only configures the logger if it hasn't been configured before.
    """
    if alert_name in _configured_alert_loggers:
        return logging.getLogger(alert_name)
    
    # Create alert log directory if it doesn't exist
    alert_log_dir = LOGS_DIR / "alerts"
    alert_log_dir.mkdir(exist_ok=True, parents=True)
    
    # Set up logger configuration
    log_file = str(alert_log_dir / f"{alert_name}.log")
    handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        backupCount=30,
        encoding="utf8"
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    
    # Get logger and configure
    logger = logging.getLogger(alert_name)
    
    # Properly clean up any existing handlers
    for h in list(logger.handlers):
        logger.removeHandler(h)
        h.close()
    
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    # Mark this alert logger as configured
    _configured_alert_loggers.add(alert_name)
    
    return logger

def cleanup_handlers():
    """
    Properly clean up all handlers to release file descriptors.
    Call this at application shutdown.
    """
    # Get all loggers
    loggers = [logging.getLogger()] + list(logging._handlerList)
    
    # Clean up handlers
    for logger in loggers:
        if isinstance(logger, logging.Logger):
            handlers = list(logger.handlers)
            for handler in handlers:
                try:
                    handler.close()
                    logger.removeHandler(handler)
                except:
                    pass
        elif isinstance(logger, logging.Handler):
            try:
                logger.close()
            except:
                pass

def validate_logger_count():
    """
    Validate that logger count and handler count hasn't grown beyond expected.
    Raises an exception if counts exceed thresholds.
    """
    # Fixed set of expected loggers plus a margin for alerts and standard lib loggers
    EXPECTED_LOGGER_COUNT = 40  # Base loggers plus room for alerts and stdlib loggers
    EXPECTED_HANDLERS_PER_LOGGER = 2  # Most loggers have console + file
    
    # Standard library/framework loggers that are expected and can be ignored
    STANDARD_LOGGERS = [
        'asyncio', 'concurrent', 'concurrent.futures',
        'aiohttp', 'aiohttp.access', 'aiohttp.client', 'aiohttp.internal',
        'aiohttp.server', 'aiohttp.web', 'aiohttp.websocket',
        'dotenv', 'dotenv.main', 'urllib3', 'requests', 'chardet',
        'PIL', 'parso', 'jedi'
    ]
    
    # Get actual counts
    logger_count = len(logging.Logger.manager.loggerDict)
    
    # Check for unexpected logger growth
    unexpected_loggers = []
    for name in logging.Logger.manager.loggerDict:
        # Skip loggers that are expected
        if name in LOGGING_CONFIG["loggers"] or name in _configured_alert_loggers:
            continue
            
        # Skip standard library loggers
        if any(name == std_logger or name.startswith(f"{std_logger}.") for std_logger in STANDARD_LOGGERS):
            continue
            
        # This is an unexpected logger
        unexpected_loggers.append(name)
    
    # If we have unexpected loggers OR we've significantly exceeded our threshold
    if unexpected_loggers or logger_count > EXPECTED_LOGGER_COUNT + 10:
        error_msg = f"Logger count: {logger_count}, Threshold: {EXPECTED_LOGGER_COUNT}"
        if unexpected_loggers:
            error_msg += f". Unexpected loggers: {unexpected_loggers}"
        
        # Only fail if we have truly unexpected loggers (not just standard lib ones)
        if unexpected_loggers:
            print(error_msg, file=sys.stderr)
            return False
        
        # Just log a warning if we have no unexpected loggers but count is high
        print(f"WARNING: High logger count but all are expected: {error_msg}", file=sys.stderr)
    
    # Check handler count for each logger
    for name, logger in logging.Logger.manager.loggerDict.items():
        if hasattr(logger, 'handlers'):
            handler_count = len(logger.handlers)
            # Allow 4 handlers maximum - some loggers might legitimately have console + file + others
            if handler_count > 4:
                error_msg = f"Handler count for logger '{name}' exceeded threshold: {handler_count} > 4"
                print(error_msg, file=sys.stderr)
                return False
            # Just log a warning for handlers exceeding our preferred count of 2
            elif handler_count > EXPECTED_HANDLERS_PER_LOGGER:
                print(f"WARNING: Logger '{name}' has {handler_count} handlers (preferred max: {EXPECTED_HANDLERS_PER_LOGGER})", file=sys.stderr)
    
    return True

# Configure logging when this module is imported
configure_logging()
