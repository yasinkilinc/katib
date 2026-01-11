import json
from typing import Dict, Optional, List
import os
import re
from .llm import LLMService
from .memory import MemoryEngine
from .safety import SafetyLayer
class IntentEngine:
    def __init__(self):
        self.llm = LLMService()
        self.memory = MemoryEngine()
        self.safety = SafetyLayer()
        # self.normalizer = get_normalizer() # Deprecated in favor of LLM correction

    def warmup(self):
        """
        Sends a dummy request to load the model into memory.
        """
        print("[*] Warming up LLM (loading model)...")
        try:
            # Simple dummy prompt
            self.llm.generate_response("You are ready.", "Status check.")
            print("[✓] LLM Warmup Complete.")
        except Exception as e:
            print(f"[!] Warmup failed (non-critical): {e}")

    def process_command(self, user_command: str) -> Optional[Dict]:
        """
        Detects intent and entities from user command.
        Does NOT generate plan steps.
        """
        
        # Construct Prompt for Intent Classification with Phonetic Correction
        system_prompt = """
        You are the INTENT CLASSIFIER for KATİB.
        Your task is two-fold:
        1. CORRECT any phonetic/speech-to-text errors in the command (e.g. "uframda" -> "Chrome'da", "komşu" -> ".com").
        2. EXTRACT the user's Goal and Entities from the corrected command.

        Common Turkish Speech Errors to Contextualize:
        - "uframda", "kuronda" -> "Chrome'da"
        - "kom", "komşu", "kon" -> ".com"
        - "tezin", "tesine", "testini" -> "sitesini"
        - "aç" at end -> implies "open application" or "navigate"
        - "sahibinden kom" -> "sahibinden.com"

        Output JSON Schema:
        {
            "corrected_command": string, # The command after fixing errors
            "goal": string,              # High-level goal (e.g. "navigate to website")
            "entities": object,          # Extracted parameters (e.g. {"url": "sahibinden.com", "app": "Chrome"})
            "confidence": float          # 0.0 to 1.0
        }
        """
        user_prompt = f"COMMAND: {user_command}"
        
        response_data = self.llm.generate_response(system_prompt, user_prompt)
        
        if "error" in response_data:
            print(f"[!] LLM Logic Error: {response_data['error']}")
            return None
            
        if response_data.get("corrected_command"):
            print(f"[*] AI Correction: '{user_command}' -> '{response_data['corrected_command']}'")
            
        return response_data

    
    # record_outcome is moved to MemoryEngine directly in Phase 4
    # Legacy prompt methods are removed as Planner handles planning now.
