import unittest
import sys
import os
import json
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.planner import Planner

class TestPlanner(unittest.TestCase):
    def setUp(self):
        # Patch LLMService inside planner module
        self.llm_patcher = patch('src.core.planner.LLMService')
        self.MockLLMService = self.llm_patcher.start()
        self.mock_llm_instance = self.MockLLMService.return_value
        
        self.planner = Planner()

    def tearDown(self):
        self.llm_patcher.stop()

    def test_generate_plan_simple(self):
        # Setup mock return value
        mock_response = {
            "steps": [
                {"action": "web.navigate", "parameters": {"url": "google.com"}}
            ],
            "reasoning": "Navigate to google"
        }
        self.mock_llm_instance.generate_response.return_value = mock_response
        
        # Call method
        plan = self.planner.generate_plan("Google'ı aç")
        
        # Verify
        self.assertEqual(len(plan["steps"]), 1)
        self.assertEqual(plan["steps"][0]["action"], "web.navigate")
        self.assertEqual(plan["steps"][0]["parameters"]["url"], "google.com")

    def test_generate_plan_media(self):
        # Setup mock return value for media control
        mock_response = {
            "steps": [
                {"action": "media.control", "parameters": {"command": "next"}}
            ],
            "reasoning": "Next song"
        }
        self.mock_llm_instance.generate_response.return_value = mock_response
        
        # Call method
        plan = self.planner.generate_plan("Sıradaki şarkı")
        
        # Verify
        self.assertEqual(len(plan["steps"]), 1)
        self.assertEqual(plan["steps"][0]["action"], "media.control")
        self.assertEqual(plan["steps"][0]["parameters"]["command"], "next")

    def test_generate_plan_empty_response(self):
        # Setup mock to return empty steps
        self.mock_llm_instance.generate_response.return_value = {"steps": []}
        
        plan = self.planner.generate_plan("Bilinmeyen komut")
        self.assertEqual(len(plan["steps"]), 0)

if __name__ == '__main__':
    unittest.main()
