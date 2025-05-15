#!/usr/bin/env python3
"""
Utility functions for formatting match data consistently across all alerters.
This is extracted to a separate module to avoid circular imports between alerters and alerter_main.py.
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the parent directory to sys.path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import specific formatting functions from combined_match_summary
from combined_match_summary import (
    get_eastern_time, 
    format_odds_display, 
    summarize_environment,
    get_status_description,
    transform_odds,
    API_DATETIME_FORMAT
)

def format_match_summary(match):
    """Format match data exactly like combined_match_summary.py does.
    This is a direct duplicate of the formatting code from combined_match_summary.py
    to ensure consistent pretty-printing throughout the system.
    
    Args:
        match: The enriched match object from merge_logic
        
    Returns:
        List of formatted strings representing the match summary
    """
    lines = []
    
    # Headers and basic info
    lines.append("\n----- MATCH SUMMARY -----")
    lines.append("-------------------------")
    lines.append("")
    lines.append(f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}")
    
    # Try both ID formats
    match_id = match.get('id') or match.get('match_id', 'Unknown')
    lines.append(f"Match ID: {match_id}")
    
    # Competition info - handle both string format and object format
    competition = match.get('competition', {})
    comp_id = None
    comp_name = None
    comp_country = None
    
    if isinstance(competition, str):
        # Direct string format
        comp_name = competition
        comp_id = match.get('competition_id', 'Unknown')
        comp_country = match.get('country', 'Unknown Country')
    elif isinstance(competition, dict):
        # Object format
        comp_id = competition.get('id')
        comp_name = competition.get('name')
        comp_country = competition.get('country')
    else:
        # Alternative key formats
        comp_id = match.get('competition_id')
        comp_name = match.get('competition_name')
        comp_country = match.get('country') or match.get('competition_country')
    
    # Apply defaults if still missing
    comp_id = comp_id or 'Unknown'
    comp_name = comp_name or 'Unknown'
    comp_country = comp_country or 'Unknown Country'
    
    lines.append(f"Competition ID: {comp_id}")
    lines.append(f"Competition: {comp_name} ({comp_country})")
    
    # Team names with fallbacks for different structures
    home_team = None
    away_team = None
    
    # String access
    home_team = match.get('home_team')
    away_team = match.get('away_team')
    
    # Object structure access
    if not isinstance(home_team, str) and isinstance(match.get('home_team', {}), dict) and match.get('home_team', {}).get('name'):
        home_team = match.get('home_team', {}).get('name')
    if not isinstance(away_team, str) and isinstance(match.get('away_team', {}), dict) and match.get('away_team', {}).get('name'):
        away_team = match.get('away_team', {}).get('name')
    
    # Alternate keys
    home_team = home_team or match.get('home', 'Unknown')
    away_team = away_team or match.get('away', 'Unknown')
    
    lines.append(f"Match: {home_team} vs {away_team}")
    
    # Score handling for both object and array structures
    home_live = 0
    home_ht = 0
    away_live = 0
    away_ht = 0
    
    # Object structure
    score = match.get('score', {})
    if isinstance(score, dict):
        home_live = score.get('home', 0) 
        away_live = score.get('away', 0)
        home_ht = score.get('home_ht', 0)
        away_ht = score.get('away_ht', 0)
    # Array structure (from original data source)
    elif isinstance(score, list) and len(score) > 3:
        hs, as_ = score[2], score[3]
        if isinstance(hs, list) and len(hs) > 1:
            home_live, home_ht = hs[0], hs[1]
        if isinstance(as_, list) and len(as_) > 1:
            away_live, away_ht = as_[0], as_[1]
    
    lines.append(f"Score: {home_live} - {away_live} (HT: {home_ht} - {away_ht})")
    
    # Status with rich description
    status_id = match.get('status_id')
    status = match.get('status', get_status_description(status_id))
    lines.append(f"Status: {status} (Status ID: {status_id})")
    
    # Betting Odds section
    lines.append("\n--- MATCH BETTING ODDS ---")
    lines.append("--------------------------")
    lines.append("")

    # Handle different odds formats
    odds_data = match.get('odds', {})
    
    # Try to extract structured market data
    eu_data = odds_data.get('eu', [])
    if eu_data and len(eu_data) > 0:
        # Format moneyline odds
        eu_entry = eu_data[0]
        minute = eu_entry[1] if len(eu_entry) > 1 else "?"
        
        if len(eu_entry) >= 5:
            home_ml = eu_entry[2]
            draw_ml = eu_entry[3]
            away_ml = eu_entry[4]
            
            home_str = f"{int(float(home_ml) * 100):+d}" if home_ml else "+0"
            draw_str = f"{int(float(draw_ml) * 100):+d}" if draw_ml else "+0"
            away_str = f"{int(float(away_ml) * 100):+d}" if away_ml else "+0"
            
            lines.append(f"│ Home: {home_str} │ Draw: {draw_str} │ Away : {away_str} │ (@{minute}')")
    
    # Format spread odds
    asia_data = odds_data.get('asia', [])
    if asia_data and len(asia_data) > 0:
        asia_entry = asia_data[0]
        minute = asia_entry[1] if len(asia_entry) > 1 else "?"
        
        if len(asia_entry) >= 5:
            home_hcap = asia_entry[2]
            hcap = asia_entry[3]
            away_hcap = asia_entry[4]
            
            home_str = f"{int(float(home_hcap) * 100):+d}" if home_hcap else "+0"
            away_str = f"{int(float(away_hcap) * 100):+d}" if away_hcap else "+0"
            
            lines.append(f"│ Home: {home_str} │ Hcap: {hcap} │ Away : {away_str} │ (@{minute}')")
    
    # Format over/under odds
    bs_data = odds_data.get('bs', [])
    if bs_data and len(bs_data) > 0:
        bs_entry = bs_data[0]
        minute = bs_entry[1] if len(bs_entry) > 1 else "?"
        
        if len(bs_entry) >= 5:
            over = bs_entry[2]
            line = bs_entry[3]
            under = bs_entry[4]
            
            over_str = f"{int(float(over) * 100):+d}" if over else "+0"
            under_str = f"{int(float(under) * 100):+d}" if under else "+0"
            
            lines.append(f"│ Over: {over_str} │ Line: {line} │ Under: {under_str} │ (@{minute}')")
    
    # Environment info if available
    env = match.get('environment', {})
    if env:
        lines.append("\n--- MATCH ENVIRONMENT ---")
        lines.append("--------------------------")
        lines.append("")
        
        temp = env.get('temperature')
        if temp:
            lines.append(f"Temperature: {temp:.1f}°F")
            
        humidity = env.get('humidity')
        if humidity:
            lines.append(f"Humidity: {humidity}%")
            
        wind = env.get('wind')
        if wind:
            lines.append(f"Wind: {wind:.1f} mph")
    
    return lines
