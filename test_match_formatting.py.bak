#!/usr/bin/env python3
"""
Simple test script to demonstrate the new match header formatting.
This creates synthetic match data and passes it to the combined_match_summary
function to show the new centered header format.
"""
import json
import logging
from pathlib import Path
import sys
import os

# Add current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the match summary function
from combined_match_summary import write_combined_match_summary

# Create sample match data
sample_match = {
    "competition": "Premier League",
    "country": "England",
    "home_team": "Arsenal FC",
    "away_team": "Manchester United",
    "status_id": 3,  # In progress
    "score": [None, None, [2, 1], [1, 0]],  # Home: 2 (HT: 1), Away: 1 (HT: 0)
    "odds": {
        "eu": [[1621453362, "1X2", 1.85, 3.5, 4.33, 4]],  # ML odds
        "asia": [[1621453362, "AH", -0.5, 1.95, 1.95, 4]],  # Spread odds
        "bs": [[1621453362, "O/U", 2.5, 1.85, 2.05, 4]]  # Total odds
    },
    "environment": {
        "weather": "Partly Cloudy",
        "temperature": 68,
        "humidity": 65,
        "wind": "Moderate Breeze, 13 mph"
    }
}

# Run a few test cases with different match numbers
test_matches = [
    (1, 10),    # First of 10
    (5, 20),    # Middle of 20
    (20, 20),   # Last of 20
    (123, 456)  # Large numbers
]

print("Testing new match header formatting with sample data:\n")

for match_num, total_matches in test_matches:
    print(f"\n--- Test Case: Match {match_num}/{total_matches} ---")
    write_combined_match_summary(sample_match, match_num, total_matches)
    print("Match summary logged with new header format")

print("\nAll test cases completed. Check the combined_match_summary.logger file for results.")
