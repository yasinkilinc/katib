import json
import os
import time
from typing import Dict, Any

class MemoryEngine:
    def __init__(self, storage_path="memory.json"):
        self.storage_path = storage_path
        self.history = []
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []

    def _save(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.history, f, indent=2)

    def record_execution(self, outcome: Dict[str, Any]):
        """
        Records the full cycle: Command -> Plan -> Execution Result
        """
        entry = {
            "timestamp": time.time(),
            "command": outcome.get("command"),
            "intent": outcome.get("intent"),
            "plan": outcome.get("plan"),
            "results": outcome.get("actions"), # List of capability request/result
            "success": outcome.get("success"),
            "error": outcome.get("error")
        }
        
        self.history.append(entry)
        # Keep last 1000
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
            
        self._save()
        
    def get_recent_context(self, limit=5):
        return self.history[-limit:]
