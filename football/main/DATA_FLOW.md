# Sports Bot Data Flow

This document outlines the data flow through the Sports Bot system, from API data fetching to formatted output.

## High-Level Data Flow

```
orchestrate_complete.py → pure_json_fetch_cache.py → merge_logic.py → combined_match_summary.py → complete_summary.logger
```

## Detailed Flow

1. **orchestrate_complete.py**: Main controller script
   - Initiates the entire data processing workflow
   - Coordinates the fetching, merging, and formatting steps
   - Determines which matches to process

2. **pure_json_fetch_cache.py**: API data fetching and caching
   - Handles API requests with efficient caching
   - Creates/reads cache files (*.json)
   - Minimizes redundant API calls

3. **merge_logic.py**: Data integration and enrichment
   - Combines data from different API endpoints:
     - Live match data
     - Match details
     - Betting odds
     - Team information
     - Competition data
   - Creates comprehensive match objects
   - Outputs to merge_logic.json as an intermediate reference file

4. **combined_match_summary.py**: Data formatting and presentation
   - Takes the merged match objects
   - Applies formatting logic for all sections:
     - Match details
     - Betting odds
     - Environment data (weather, temperature, etc.)
   - Contains specialized functions like `summarize_environment()`
   - Handles translation of codes to human-readable values

5. **complete_summary.logger**: Final output
   - Contains the formatted, human-readable match summaries
   - Maintains a log of all processed matches
   - Displays sections like:
     ```
     --- MATCH ENVIRONMENT ---
     Weather: Sunny
     Temperature: 78.8°F
     Humidity: 44%
     Wind: Gentle Breeze, 11.9 mph
     ```

## JSON Data Structure - Environment Example

```json
"environment": {
  "weather": 1,            // Numeric weather code (1=Sunny, etc.)
  "temperature": "19°C",   // Temperature with unit
  "wind": "1.8m/s",        // Wind speed in meters/second
  "humidity": "94%",       // Humidity percentage
  "pressure": "762mmHg"    // Pressure (not displayed)
}
```

## Weather Code Mapping

```
1: Sunny
2: Partly Cloudy
3: Cloudy
4: Overcast
5: Foggy
6: Light Rain
7: Rain
8: Heavy Rain
9: Snow
10: Thunder
```
