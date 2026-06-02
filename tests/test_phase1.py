import unittest
from unittest.mock import MagicMock
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.planner import Planner
from src.schemas.plan import Plan, Step

class TestPhase1(unittest.TestCase):
    def setUp(self):
        self.planner = Planner(memory_engine=None)
        # Mock LLM Service
        self.planner.llm = MagicMock()
    
    def test_planner_returns_plan_object(self):
        # Mock LLM response
        mock_response = {
            "goal": "Test Goal",
            "steps": [
                {
                    "id": 1,
                    "name": "test_step",
                    "capability": "test.cap",
                    "params": {"p": 1},
                    "requires_feedback": False
                }
            ],
            "reasoning": "Test reasoning"
        }
        self.planner.llm.generate_response.return_value = mock_response
        
        plan = self.planner.generate_plan("Test Command")
        
        self.assertIsInstance(plan, Plan)
        self.assertEqual(plan.goal, "Test Goal")
        self.assertEqual(len(plan.steps), 1)
        self.assertIsInstance(plan.steps[0], Step)
        self.assertEqual(plan.steps[0].name, "test_step")
        self.assertEqual(plan.steps[0].params["p"], 1)
        
    def test_planner_handles_invalid_response(self):
        # Mock Invalid LLM response (missing goal)
        self.planner.llm.generate_response.return_value = {"steps": []} 
        
        # Pydantic should raise validation error, Planner should catch and return empty plan
        # BUT wait, our planner code currently expects valid response or fallback
        # Let's see how I implemented it.
        # Impl: Plan(**response_dict) inside try-except.
        
        plan = self.planner.generate_plan("Invalid Command")
        
        # Since missing "goal" is required field, it should fail validation -> triggering except block -> returning fallback Plan
        self.assertEqual(plan.goal, "Error parsing plan")

if __name__ == '__main__':
    unittest.main()
