#!/usr/bin/env python3
"""
summary_json_generator.py - Generates JSON summaries of matches with the same fields displayed in the combined match summary

This module creates a JSON representation of all the fields that appear in the combined match summary format,
making it easier to:
1. Reference exact field paths for alert criteria
2. Debug which fields are available for scanning
3. Ensure consistent data representation between display and scanning

The generated JSON is saved to summary_data.json and logged to summary_json.logger
"""

import json
import os
import logging
import pytz
from datetime import datetime
from pathlib import Path
from log_config import get_logger

# Use the same timezone as the main orchestrator
TZ = pytz.timezone("America/New_York")

# Path constants
BASE_DIR = Path(__file__).parent
SUMMARY_JSON_FILE = BASE_DIR / "summary_data.json"
SUMMARY_JSON_LOG = BASE_DIR / "logs/summary/summary_json.logger"

def setup_summary_json_logger():
    """Get the pre-configured summary_json logger"""
    return get_logger("summary_json")

def get_eastern_time():
    """Get current time in Eastern timezone with consistent format"""
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")

def extract_summary_fields(match):
    """
    Extract and structure the fields that would appear in the combined match summary
    This function mirrors the logic in combined_match_summary.py but returns structured data
    instead of formatted text
    """
    # Extract score information from the match structure
    home_live = home_ht = away_live = away_ht = 0
    sd = match.get("score", [])
    if isinstance(sd, list) and len(sd) > 3:
        hs, as_ = sd[2], sd[3]
        if isinstance(hs, list) and len(hs) > 1:
            home_live, home_ht = hs[0], hs[1]
        if isinstance(as_, list) and len(as_) > 1:
            away_live, away_ht = as_[0], as_[1]
        
    # For cases where score is in home_scores/away_scores
    home_scores = match.get("home_scores", [])
    away_scores = match.get("away_scores", [])
    if home_scores and len(home_scores) > 0 and home_live == 0:
        home_live = sum(home_scores)
    if away_scores and len(away_scores) > 0 and away_live == 0:
        away_live = sum(away_scores)
            
    summary_data = {
        "match_id": match.get("match_id") or match.get("id"),
        "status": {
            "id": match.get("status_id"),
            "description": match.get("status") or "",
            "match_time": match.get("match_time") or 0,
        },
        "teams": {
            "home": {
                "name": match.get("home_team", "Unknown"),
                "score": {
                    "current": home_live,
                    "halftime": home_ht,
                    "detailed": home_scores
                },
                "position": match.get("home_position"),
                "country": match.get("home_country"),
                "logo_url": match.get("home_logo")
            },
            "away": {
                "name": match.get("away_team", "Unknown"),
                "score": {
                    "current": away_live,
                    "halftime": away_ht,
                    "detailed": away_scores
                },
                "position": match.get("away_position"),
                "country": match.get("away_country"),
                "logo_url": match.get("away_logo")
            }
        },
        "competition": {
            "name": match.get("competition", "Unknown"),
            "id": match.get("competition_id"),
            "country": match.get("country"),
            "logo_url": match.get("competition_logo")
        },
        "round": match.get("round", {}),
        "venue": match.get("venue_id"),
        "referee": match.get("referee_id"),
        "neutral": match.get("neutral") == 1,
        "coverage": match.get("coverage", {}),
        "start_time": match.get("scheduled"),
        "odds": extract_odds(match),
        "environment": extract_environment(match),
        "events": extract_events(match),
    }
    
    return summary_data

def extract_odds(match):
    """Extract odds information from the match"""
    odds_data = {
        "full_time_result": {
            "home": None,
            "draw": None,
            "away": None,
            "timestamp": None,
            "match_time": None
        },
        "both_teams_to_score": {
            "yes": None,
            "no": None
        },
        "over_under": {},
        "spread": {},
        "raw": {}
    }
    
    # Extract raw odds data from the merge_logic format
    raw_odds = match.get("odds", {})
    if raw_odds:
        # Store raw odds data
        odds_data["raw"] = raw_odds
        
        # Extract moneyline odds (eu format)
        eu_odds = raw_odds.get("eu", [])
        if eu_odds:
            # Sort by time and pick best entry
            eu_odds.sort(key=lambda x: x[1] if len(x) > 1 else 0)
            best_eu = eu_odds[0] if eu_odds else None
            
            if best_eu and len(best_eu) >= 5:
                odds_data["full_time_result"] = {
                    "home": best_eu[2],
                    "draw": best_eu[3],
                    "away": best_eu[4],
                    "timestamp": best_eu[0] if len(best_eu) > 0 else None,
                    "match_time": best_eu[1] if len(best_eu) > 1 else None
                }
        
        # Extract spread odds (asia format)
        asia_odds = raw_odds.get("asia", [])
        if asia_odds:
            # Sort by time and pick best entry
            asia_odds.sort(key=lambda x: x[1] if len(x) > 1 else 0)
            best_asia = asia_odds[0] if asia_odds else None
            
            if best_asia and len(best_asia) >= 5:
                handicap = best_asia[3] if len(best_asia) > 3 else 0
                odds_data["spread"] = {
                    "handicap": handicap,
                    "home": best_asia[2] if len(best_asia) > 2 else None,
                    "away": best_asia[4] if len(best_asia) > 4 else None,
                    "timestamp": best_asia[0] if len(best_asia) > 0 else None,
                    "match_time": best_asia[1] if len(best_asia) > 1 else None
                }
        
        # Extract over/under odds (bs format)
        bs_odds = raw_odds.get("bs", [])
        if bs_odds:
            # Sort by time and pick best entry
            bs_odds.sort(key=lambda x: x[1] if len(x) > 1 else 0)
            best_bs = bs_odds[0] if bs_odds else None
            
            if best_bs and len(best_bs) >= 5:
                line = best_bs[3] if len(best_bs) > 3 else 0
                line_str = str(line)
                odds_data["over_under"][line_str] = {
                    "line": line,
                    "over": best_bs[2] if len(best_bs) > 2 else None,
                    "under": best_bs[4] if len(best_bs) > 4 else None,
                    "timestamp": best_bs[0] if len(best_bs) > 0 else None,
                    "match_time": best_bs[1] if len(best_bs) > 1 else None
                }
                
                # Store the primary over/under line for easy access
                odds_data["primary_over_under"] = {
                    "line": line,
                    "over": best_bs[2] if len(best_bs) > 2 else None,
                    "under": best_bs[4] if len(best_bs) > 4 else None
                }
    
    # Process betting markets if available (for markets not in the raw odds)
    if "betting" in match and "markets" in match["betting"]:
        markets = match["betting"]["markets"]
        
        # Both teams to score (often not in the raw odds)
        for market in markets:
            if market.get("name") == "Both Teams to Score":
                for selection in market.get("selections", []):
                    name = selection.get("name", "").lower()
                    odds = selection.get("odds")
                    if name == "yes":
                        odds_data["both_teams_to_score"]["yes"] = odds
                    elif name == "no":
                        odds_data["both_teams_to_score"]["no"] = odds
    
    return odds_data

def extract_environment(match):
    """Extract environment data from the match"""
    env_data = {
        "weather": None,
        "weather_description": None,
        "temperature": None,
        "temperature_value": None,
        "temperature_unit": None,
        "wind": None,
        "wind_value": None,
        "wind_unit": None,
        "wind_description": None,
        "humidity": None,
        "humidity_value": None,
        "pressure": None,
        "pressure_value": None,
        "pressure_unit": None,
        "raw": None
    }
    
    if "environment" in match:
        env = match["environment"]
        # Store the raw environment data
        env_data["raw"] = env
        
        # Weather code and description
        if "weather" in env:
            weather_code = env["weather"]
            # Convert to int if it's a string
            if isinstance(weather_code, str) and weather_code.isdigit():
                weather_code = int(weather_code)
            env_data["weather"] = weather_code
            
            # Map weather code to description
            weather_map = {
                1: "Sunny",
                2: "Partly Cloudy",
                3: "Cloudy",
                4: "Overcast",
                5: "Foggy",
                6: "Light Rain",
                7: "Rain",
                8: "Heavy Rain",
                9: "Snow",
                10: "Thunder"
            }
            env_data["weather_description"] = weather_map.get(weather_code, "Unknown")
        
        # Temperature parsing
        temp = env.get("temperature")
        env_data["temperature"] = temp
        if temp:
            # Try to extract numeric value and unit
            import re
            temp_match = re.match(r'([\d.-]+)\s*([^\d]*)', str(temp))
            if temp_match:
                value, unit = temp_match.groups()
                try:
                    env_data["temperature_value"] = float(value)
                    env_data["temperature_unit"] = unit.strip()
                except (ValueError, TypeError):
                    pass
        
        # Wind parsing
        wind = env.get("wind")
        env_data["wind"] = wind
        if wind:
            # Try to extract numeric value and unit
            wind_match = re.match(r'([\d.-]+)\s*([^\d]*)', str(wind))
            if wind_match:
                value, unit = wind_match.groups()
                try:
                    wind_value = float(value)
                    env_data["wind_value"] = wind_value
                    env_data["wind_unit"] = unit.strip()
                    
                    # Add wind description based on Beaufort scale
                    # Convert to mph for scale if in m/s
                    wind_mph = wind_value
                    if "m/s" in str(wind).lower():
                        wind_mph = wind_value * 2.237
                    
                    if wind_mph < 1:
                        env_data["wind_description"] = "Calm"
                    elif wind_mph < 4:
                        env_data["wind_description"] = "Light Air"
                    elif wind_mph < 8:
                        env_data["wind_description"] = "Light Breeze"
                    elif wind_mph < 13:
                        env_data["wind_description"] = "Gentle Breeze"
                    elif wind_mph < 19:
                        env_data["wind_description"] = "Moderate Breeze"
                    elif wind_mph < 25:
                        env_data["wind_description"] = "Fresh Breeze"
                    elif wind_mph < 32:
                        env_data["wind_description"] = "Strong Breeze"
                    elif wind_mph < 39:
                        env_data["wind_description"] = "Near Gale"
                    elif wind_mph < 47:
                        env_data["wind_description"] = "Gale"
                    elif wind_mph < 55:
                        env_data["wind_description"] = "Strong Gale"
                    elif wind_mph < 64:
                        env_data["wind_description"] = "Storm"
                    elif wind_mph < 73:
                        env_data["wind_description"] = "Violent Storm"
                    else:
                        env_data["wind_description"] = "Hurricane"
                except (ValueError, TypeError):
                    pass
        
        # Humidity parsing
        humidity = env.get("humidity")
        env_data["humidity"] = humidity
        if humidity:
            # Try to extract numeric value
            humidity_match = re.match(r'([\d.]+)', str(humidity))
            if humidity_match:
                try:
                    env_data["humidity_value"] = float(humidity_match.group(1))
                except (ValueError, TypeError):
                    pass
        
        # Pressure parsing
        pressure = env.get("pressure")
        env_data["pressure"] = pressure
        if pressure:
            # Try to extract numeric value and unit
            pressure_match = re.match(r'([\d.]+)\s*([^\d]*)', str(pressure))
            if pressure_match:
                value, unit = pressure_match.groups()
                try:
                    env_data["pressure_value"] = float(value)
                    env_data["pressure_unit"] = unit.strip()
                except (ValueError, TypeError):
                    pass
    
    return env_data

def extract_events(match):
    """Extract key events from the match"""
    events_data = []
    
    if "events" in match and isinstance(match["events"], list):
        for event in match["events"]:
            event_type = event.get("type")
            
            # Only include significant events like goals and cards
            if event_type in ["goal", "yellowcard", "redcard", "penalty", "substitution"]:
                events_data.append({
                    "type": event_type,
                    "time": event.get("time"),
                    "team": event.get("team"),
                    "player": event.get("player"),
                    "detail": event.get("detail")
                })
    
    return events_data

def generate_summary_json(matches):
    """Generate summary JSON data for all matches"""
    summary_data = {
        "generated_at": get_eastern_time(),
        "match_count": len(matches),
        "matches": []
    }
    
    for match in matches:
        summary_data["matches"].append(extract_summary_fields(match))
    
    return summary_data

def write_summary_json(matches):
    """Write the summary JSON to file and log"""
    logger = setup_summary_json_logger()
    
    # Generate the summary data
    summary_data = generate_summary_json(matches)
    
    # Write to JSON file
    with open(SUMMARY_JSON_FILE, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    # Create header for log
    header = "\n" + "="*50 + "\n"
    header += f"SUMMARY JSON DATA - {get_eastern_time()}\n"
    header += "="*50 + "\n\n"
    
    # Log the summary data (prepend new entries)
    if os.path.exists(SUMMARY_JSON_LOG):
        try:
            with open(SUMMARY_JSON_LOG, 'r+') as f:
                old_content = f.read()
                f.seek(0)
                f.write(header + json.dumps(summary_data, indent=2) + "\n\n" + old_content)
                f.truncate()
        except Exception as e:
            logger.error(f"Error prepending to summary JSON log: {e}")
    else:
        # File doesn't exist yet, create it with the new content
        with open(SUMMARY_JSON_LOG, 'w') as f:
            f.write(header + json.dumps(summary_data, indent=2))
    
    return summary_data

if __name__ == "__main__":
    # For testing directly
    import sys
    from merge_logic import merge_all_matches
    
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], 'r') as f:
            matches = json.load(f)
            result = write_summary_json(matches)
            print(f"Generated summary JSON with {len(result['matches'])} matches")
    else:
        print("Please provide a path to a merged matches JSON file")
        print("Usage: python summary_json_generator.py path/to/merge_logic.json")
