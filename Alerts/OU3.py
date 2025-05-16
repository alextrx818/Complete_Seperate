# OU3.py - Over/Under threshold alert satellite
# This class extends BaseAlert and must implement check(match) only.

import logging
import json
import sys
from pathlib import Path
from typing import Dict, Optional, Union, Any

try:
    from .base_alert import Alert
    from .format_utils import format_match_summary
except ImportError:
    # Fallback if importing from relative path fails
    sys.path.append(str(Path(__file__).parent.parent))
    from Alerts.base_alert import Alert
    from Alerts.format_utils import format_match_summary

class OverUnderAlert(Alert):
    """
    Alert when the Over/Under line is at or above a given threshold,
    and the match is currently in first half, halftime, or second half.
    """
    
    # Default parameters that can be overridden by config
    DEFAULT_PARAMS = {"threshold": 3.0}
    # Status IDs typically: 1=Not Started, 2=First Half, 3=Halftime, 4=Second Half, 5=Finished
    # Define valid status IDs as integers only, we'll convert strings to integers when checking
    VALID_STATUS_IDS = {2, 3, 4}

    def __init__(self, threshold: float = 3.0):
        super().__init__(name="OU3")
        self.threshold = threshold

    def check(self, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if match meets Over/Under alert criteria
        
        Args:
            match: Enriched match object from merge_logic.py
            
        Returns:
            Alert payload dict or None if criteria not met
        """
        match_id = match.get("match_id", "unknown")
        
        # Extract home and away teams for better logs
        home = "Unknown Home"
        away = "Unknown Away"
        
        # Handle home team - might be string or dict
        home_team = match.get("home_team", {})
        if home_team:
            if isinstance(home_team, dict):
                home = home_team.get("name", "Unknown Home")
            elif isinstance(home_team, str):
                home = home_team
        else:
            home = match.get("home", "Unknown Home")
            
        # Handle away team - might be string or dict
        away_team = match.get("away_team", {})
        if away_team:
            if isinstance(away_team, dict):
                away = away_team.get("name", "Unknown Away")
            elif isinstance(away_team, str):
                away = away_team
        else:
            away = match.get("away", "Unknown Away")
        
        # 1. Check and log status ID
        status_id = match.get("status_id")
        if status_id is None:
            self.logger.debug(f"Match {match_id} ({home} vs {away}): Status ID is null, alert not triggered")
            return None
            
        # Convert status_id to int if it's a string
        original_status = status_id  # Keep original for logging
        if isinstance(status_id, str):
            try:
                status_id = int(status_id)
            except (ValueError, TypeError):
                self.logger.debug(f"Match {match_id} ({home} vs {away}): Could not convert status_id '{status_id}' to int")
                return None
                
        # Check if status is valid for alerting
        if status_id not in self.VALID_STATUS_IDS:
            self.logger.debug(f"Match {match_id} ({home} vs {away}): Status {status_id} not in valid statuses {self.VALID_STATUS_IDS}")
            return None
            
        self.logger.info(f"Match {match_id} ({home} vs {away}): Status {status_id} is valid for alerting")
        
        # 2. Extract the O/U line value - checking multiple formats
        value = None
        extraction_method = "none"
        
        # First try the odds.markets structure (from merge_logic)
        odds = match.get("odds", {})
        for market in odds.get("markets", []):
            if market.get("type") == "OVER_UNDER":
                try:
                    value = float(market.get("line"))
                    extraction_method = "markets"
                    self.logger.debug(f"Match {match_id}: Extracted O/U value {value} from markets structure")
                    break
                except (TypeError, ValueError):
                    pass
        
        # Second, try the direct bs arrays structure (from merged data structure)
        if value is None:
            odds = match.get("odds", {})
            
            # Direct access to bs array - this is the structure in merge_logic.json
            bs_data = odds.get("bs", [])
            if bs_data and len(bs_data) > 0 and len(bs_data[0]) >= 4:
                # Get the most recent bs entry (first in the list)
                try:
                    value = float(bs_data[0][3])  # O/U line is at index 3
                    extraction_method = "direct_bs"
                    self.logger.debug(f"Match {match_id}: Extracted O/U value {value} from direct bs array")
                except (ValueError, TypeError):
                    self.logger.debug(f"Match {match_id}: Failed to extract O/U value from direct bs array: {bs_data[0] if bs_data and len(bs_data) > 0 else 'no data'}")
                    
            # Also try the nested results structure as a fallback
            if value is None:
                results = odds.get("results", {})
                for period_id, markets in results.items():
                    bs_data = markets.get("bs", [])
                    if bs_data and len(bs_data) > 0 and len(bs_data[0]) >= 4:
                        try:
                            value = float(bs_data[0][3])  # O/U line is at index 3
                            extraction_method = "nested_bs"
                            self.logger.debug(f"Match {match_id}: Extracted O/U value {value} from nested bs array (period: {period_id})")
                            break
                        except (ValueError, TypeError):
                            self.logger.debug(f"Match {match_id}: Failed to extract O/U value from nested bs array")
                            pass
        
        # Third, try alternative betting structure
        if value is None:
            ou = match.get("betting", {}).get("over_under", {})
            line = ou.get("line")
            try:
                value = float(line)
                extraction_method = "betting"
                self.logger.debug(f"Match {match_id}: Extracted O/U value {value} from betting structure")
            except (TypeError, ValueError):
                self.logger.debug(f"Match {match_id}: Failed to extract O/U value from betting structure")
                pass
            
        if value is None:
            self.logger.debug(f"Match {match_id} ({home} vs {away}): No O/U value found in any structure")
            return None
            
        self.logger.info(f"Match {match_id} ({home} vs {away}): Extracted O/U value {value} via {extraction_method}")


        # 3. Fire alert if threshold met
        if value >= self.threshold:
            self.logger.info(f"Match {match_id} ({home} vs {away}): O/U value {value} meets threshold {self.threshold}")
            
            # Return the raw alert data - alerter_main will handle formatting
            alert_data = {
                "type": "OU3",
                "value": value,
                "threshold": self.threshold,
                "detail": f"Over/Under Line: {value:.2f}"
            }
            
            # Log the alert data for debugging
            self.logger.info(f"Match {match_id}: Generated alert data: {json.dumps(alert_data)}")
            return alert_data
        else:
            self.logger.debug(f"Match {match_id} ({home} vs {away}): O/U value {value} below threshold {self.threshold}")
        
        return None
