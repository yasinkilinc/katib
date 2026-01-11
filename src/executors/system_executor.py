from typing import Dict, Any
from .base_executor import BaseExecutor, ExecutionResult

class SystemExecutor(BaseExecutor):
    def execute(self, action: str, params: Dict[str, Any]) -> ExecutionResult:
        if action == "system.stop":
             # We return a specific signal that the main loop will look for
             return ExecutionResult(True, "STOP_SIGNAL")
        
        elif action == "system.lock":
             # Stub for lock screen
             return ExecutionResult(False, "system.lock not implemented yet")
             
        elif action == "system.hotkey":
             # Stub for hotkey
             return ExecutionResult(False, "system.hotkey not implemented yet")

        return ExecutionResult(False, f"Unknown System action: {action}")
