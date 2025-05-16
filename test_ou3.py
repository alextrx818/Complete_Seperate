#!/usr/bin/env python3
# test_ou3.py - Unit tests for the OU3 alert

import unittest
from Alerts.OU3 import OverUnderAlert

class TestOverUnderAlert(unittest.TestCase):
    """Test the OverUnderAlert implementation."""
    
    def setUp(self):
        """Set up the alert instance and test data."""
        self.alert = OverUnderAlert(threshold=3.0)
        
        # Base match data with two over/under entries - one above and one below threshold
        self.match = {
            "match_id": "test-123",
            "status_id": "2",  # First half
            "odds": {
                "over_under": {
                    "2.5": {"line": 2.5, "over": 0.95, "under": 0.85, "timestamp": 100},
                    "4.0": {"line": 4.0, "over": 0.80, "under": 1.10, "timestamp": 200}
                }
            }
        }
    
    def test_live_match_above_threshold(self):
        """Test alert fires for live match with line above threshold."""
        result = self.alert.safe_check(self.match)
        
        # Verify alert fires
        self.assertIsNotNone(result)
        
        # Verify it picks the highest timestamp entry
        self.assertEqual(result["line"], 4.0)
        self.assertEqual(result["over"], 0.80)
        self.assertEqual(result["under"], 1.10)
        self.assertEqual(result["timestamp"], 200)
        
    def test_non_live_status(self):
        """Test alert doesn't fire for non-live match."""
        # Test not started match
        not_started = {**self.match, "status_id": "1"}
        self.assertIsNone(self.alert.safe_check(not_started))
        
        # Test finished match
        finished = {**self.match, "status_id": "5"}
        self.assertIsNone(self.alert.safe_check(finished))
    
    def test_missing_odds(self):
        """Test alert doesn't fire when odds data is missing."""
        # Test missing over_under
        missing_ou = {**self.match}
        missing_ou["odds"] = {}
        self.assertIsNone(self.alert.safe_check(missing_ou))
        
        # Test missing odds entirely
        no_odds = {**self.match}
        del no_odds["odds"]
        self.assertIsNone(self.alert.safe_check(no_odds))
    
    def test_threshold(self):
        """Test threshold comparison works correctly."""
        # Create alert with higher threshold
        high_alert = OverUnderAlert(threshold=5.0)
        self.assertIsNone(high_alert.safe_check(self.match))
        
        # Create alert with lower threshold
        low_alert = OverUnderAlert(threshold=2.0)
        result = low_alert.safe_check(self.match)
        self.assertIsNotNone(result)
        self.assertEqual(result["line"], 4.0)  # Still picks highest timestamp

if __name__ == "__main__":
    unittest.main()
