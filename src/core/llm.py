import requests
import json
import time
from typing import Dict, Any, Optional
from ..config import Config

class LLMService:
    def __init__(self):
        self.api_url = Config.OLLAMA_API_URL
        self.model = Config.OLLAMA_MODEL
        print(f"[*] Initialized Local LLM Service (Ollama) -> Model: {self.model}")

    def generate_response(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Sends a request to Ollama with a strict system prompt.
        Expects a JSON response.
        """
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": "json", # Ollama JSON mode
            "keep_alive": "30m", # Keep model in memory for 30 minutes
            "stream": False,
            "options": {
                "temperature": 0.1, # Low temperature for deterministic plans
                "num_ctx": 512,       # Aggressively reduce context window
                "num_predict": 256    # Increase limit slightly for valid JSON
            }
        }

        try:
            print("[...] Querying Ollama...")
            start_time = time.time()
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            duration = time.time() - start_time
            print(f"[✓] Response received in {duration:.2f}s")
            
            data = response.json()
            content = data.get("message", {}).get("content", "{}")
            
            # Parse JSON
            try:
                parsed_json = json.loads(content)
                return parsed_json
            except json.JSONDecodeError:
                print(f"[!] Invalid JSON from LLM: {content}")
                return {"error": "Invalid JSOn output", "raw": content}
                
        except requests.exceptions.RequestException as e:
            print(f"[!] Ollama Connection Error: {e}")
            return {"error": str(e)}
