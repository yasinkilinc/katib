from typing import Dict, List
from ..config import Config

class SafetyLayer:
    @staticmethod
    def validate_plan(intent_data: Dict) -> bool:
        # Legacy method, kept for compatibility if needed, but new logic is in ask_api_confirmation
        return True

    @staticmethod
    def ask_api_confirmation(reason: str) -> bool:
        print(f"\n[SAFETY STOP] System requests confirmation.")
        print(f"Reason: {reason}")
        if Config.REQUIRE_CONFIRMATION_THRESHOLD == "high":
            response = input(">>> Do you authorize this plan? (y/N): ")
            return response.lower().strip() == 'y'
        return True
