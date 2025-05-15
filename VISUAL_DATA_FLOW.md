# Visual Data Flow - Sports Bot

```
┌─────────────────────┐
│ orchestrate_complete│◄────────────────┐
└──────────┬──────────┘                 │
           │                            │
           ▼                            │
┌─────────────────────┐                 │
│pure_json_fetch_cache│                 │
└──────────┬──────────┘                 │
           │                            │
           ▼                            │
┌─────────────────────┐                 │
│    merge_logic      │                 │
└─────┬───────────────┘                 │
      │                                 │
      ├─────────────┬───────────────────┘
      │             │
      ▼             ▼
┌──────────┐  ┌─────────────┐
│ Alerts   │  │summary_json_│
│ System   │  │ generator   │
└──────┬───┘  └──────┬──────┘
       │             │
       ▼             ▼
┌──────────┐  ┌─────────────┐
│OU3 Alert │  │combined_match│
│Detection │  │  summary    │
└──────────┘  └─────────────┘
```

## Process Flow

1. **Orchestration** (`orchestrate_complete.py`):
   - Controls overall pipeline execution
   - Manages memory monitoring and logger validation
   - Loops through API calls periodically

2. **Data Acquisition** (`pure_json_fetch_cache.py`):
   - Fetches live match data from API
   - Implements caching to reduce API calls
   - Outputs to full_match_cache.json

3. **Data Processing** (`merge_logic.py`):
   - Enriches match data with details, odds, etc.
   - Merges various data sources
   - Outputs to merge_logic.json

4. **Branch 1: Alert Processing**
   - `Alerts/alerter_main.py` - Alert orchestration 
   - `Alerts/OU3.py` - Detects matches with high Over/Under lines
   - Outputs to alert-specific log files

5. **Branch 2: Summary Generation**
   - `summary_json_generator.py` - Creates structured JSON summaries
   - `combined_match_summary.py` - Formats for human readability
   - Outputs to complete_summary.logger

## Memory Management

Memory monitoring wraps around the entire process:
- `memory_monitor.py` - Tracks RSS usage across cycles
- `logger_monitor.py` - Prevents logger/handler proliferation
- `log_config.py` - Centralizes logging configuration
