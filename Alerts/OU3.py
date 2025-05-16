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
        
        Uses the most recent over_under entry from the odds data and compares
        its line value against self.threshold. Only triggers for matches with
        status_id in {2,3,4} (first half, halftime, second half).
        
        Args:
            match: Enriched match object from merge_logic.py
            
        Returns:
            Alert payload dict or None if criteria not met
        """
        match_id = match.get("match_id", "unknown")
        
        # Guard on Game Status
        try:
            status_id = int(match.get("status_id", 0))
        except (ValueError, TypeError):
            self.logger.debug(f"Match {match_id}: Invalid status_id format")
            return None
            
        if status_id not in self.VALID_STATUS_IDS:
            self.logger.debug(f"Match {match_id}: Status {status_id} not in valid statuses {self.VALID_STATUS_IDS}")
            return None
        
        # Pull Over/Under Map
        odds = match.get("odds", {})
        ou_map = odds.get("over_under", {})
        
        if not isinstance(ou_map, dict) or not ou_map:
            self.logger.debug(f"Match {match_id}: No over_under data found or invalid format")
            return None
        
        # Find the Most Recent Entry
        try:
            latest_entry = max(ou_map.values(), key=lambda e: e.get("timestamp", 0))
        except (ValueError, AttributeError):
            self.logger.debug(f"Match {match_id}: Could not determine latest over_under entry")
            return None
        
        # Threshold Check
        try:
            line = float(latest_entry.get("line", 0))
        except (ValueError, TypeError):
            self.logger.debug(f"Match {match_id}: Invalid line format")
            return None
        
        if line <= self.threshold:
            self.logger.debug(f"Match {match_id}: Line {line} is below threshold {self.threshold}")
            return None
        
        # Return Alert Payload
        self.logger.info(f"Match {match_id}: Line {line} exceeds threshold {self.threshold}")
        
        try:
            over_value = float(latest_entry.get("over", 0))
        except (ValueError, TypeError):
            over_value = 0.0
        
        return {
            "type": self.name,
            "line": line,
            "value": over_value,
            "threshold": self.threshold,
            "timestamp": latest_entry.get("timestamp"),
            "detail": f"Over/Under Line: {line:.2f}"
        }
