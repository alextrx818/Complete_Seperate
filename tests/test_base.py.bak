#!/usr/bin/env python3
"""
Base test utilities for the Football Match Tracking System
"""
import os
import sys
import unittest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

# Import project modules
from log_config import get_logger, get_summary_logger, validate_logger_count, cleanup_handlers

class FootballTrackingTestCase(unittest.TestCase):
    """Base test case for all football tracking tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment before any tests run."""
        # Force non-strict mode for testing
        os.environ['LOG_STRICT'] = '0'
        
        # Ensure we're using a test logger that won't interfere with production logs
        cls.test_logger = get_logger("test_logger")
        
        # Directory for test fixtures
        cls.fixture_dir = Path(__file__).parent / "fixtures"
        cls.fixture_dir.mkdir(exist_ok=True)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests have run."""
        # Clean up logging handlers
        cleanup_handlers()
        
    def setUp(self):
        """Set up test environment before each test."""
        # Create mock objects
        self.mock_api_client = MagicMock()
        
    def tearDown(self):
        """Clean up after each test."""
        pass
        
    # Helper methods for all tests
    def create_test_match_data(self):
        """Create sample match data for testing."""
        return {
            "match_id": "12345",
            "status_id": "3",
            "home_team": "Team A",
            "away_team": "Team B",
            "score": "2-1",
            "competition": "Premier League",
            "country": "England",
            "created_at": "05/17/2025 09:00:00 PM EDT"
        }
    
    def create_test_api_response(self, include_data=True):
        """Create a sample API response for testing."""
        if include_data:
            return {
                "matches": [self.create_test_match_data() for _ in range(3)],
                "metadata": {
                    "timestamp": "05/17/2025 09:00:00 PM EDT",
                    "count": 3
                }
            }
        else:
            return {
                "matches": [],
                "metadata": {
                    "timestamp": "05/17/2025 09:00:00 PM EDT",
                    "count": 0
                }
            }
    
    def mock_fetch_function(self, *args, **kwargs):
        """Mock function for API fetches."""
        return self.create_test_api_response()
        
    def assert_logger_used_correctly(self, module_path):
        """Verify that a module is using the centralized logging correctly."""
        with open(module_path, 'r') as f:
            content = f.read()
            
        # Check for direct logging.getLogger calls
        self.assertNotIn("logging.getLogger(", content, 
                         f"Module {module_path} is using direct logging.getLogger calls")
        
        # Check for proper imports
        self.assertIn("from log_config import get_logger", content,
                      f"Module {module_path} is not importing get_logger from log_config")
        
        # Check for custom handler setup
        self.assertNotIn(".addHandler(", content,
                         f"Module {module_path} is adding custom handlers")
