# Sports Bot Project

## Overview
This repository contains the Sports Bot system for processing football (soccer) match data. The system features a modular architecture with components for data acquisition, processing, formatting, and alerting.

## Core Components

### Orchestration System
- `football/main/orchestrate_complete.py` - Main pipeline controller
- `football/main/log_config.py` - Centralized logging configuration
- `football/main/memory_monitor.py` - Memory usage tracking
- `football/main/logger_monitor.py` - Logger growth monitoring

### Data Pipeline
- `football/main/pure_json_fetch_cache.py` - API data fetching with caching
- `football/main/merge_logic.py` - Data merging and enrichment
- `football/main/summary_json_generator.py` - JSON summary generation
- `football/main/combined_match_summary.py` - Human-readable match formatting

### Alert System
- `football/main/Alerts/alerter_main.py` - Alert orchestration
- `football/main/Alerts/OU3.py` - Over/Under betting line detection
- `football/main/Alerts/format_utils.py` - Consistent alert formatting

## Key Features
- Centralized logging system to prevent memory leaks
- Memory monitoring capabilities
- Modular design with clear separation of concerns
- Alert system for match monitoring based on betting lines

## Directory Structure
- `football/main/logs/` - Log files organized by component
- `football/main/Alerts/logs/` - Alert-specific log files
- `football/main/Alerts/seen/` - Deduplication storage for alerts
- `football/main/cache/` - API response caching

## Flow Documentation
See `football/main/DATA_FLOW.md` for detailed information about the data pipeline flow.
