import requests
import json
import time
from typing import Dict, Any
from ..config import Config
from .logger import get_logger

logger = get_logger("LLMService")

class LLMService:
    def __init__(self):
        self.api_url = Config.OLLAMA_API_URL
        self.model = Config.OLLAMA_MODEL
        logger.info(f"Initialized Local LLM Service (Ollama) -> Model: {self.model}")

    def generate_response(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Sends a request to Ollama /api/generate endpoint.
        Expects a JSON response.
        """
        
        # Correct payload format for /api/generate
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 1024,
                "num_predict": 512
            }
        }

        try:
            logger.debug("Querying Ollama...")
            start_time = time.time()
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            duration = time.time() - start_time
            logger.info(f"Response received in {duration:.2f}s")
            
            data = response.json()
            # /api/generate uses "response" key, not "message"
            content = data.get("response", "{}")
            
            # Log raw response for debugging
            logger.debug(f"Raw LLM response: {content[:200]}...")
            
            # Parse JSON
            try:
                parsed_json = json.loads(content)
                return parsed_json
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from LLM: {content}")
                return {"error": "Invalid JSON output", "raw": content}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama Connection Error: {e}")
            return {"error": str(e)}
