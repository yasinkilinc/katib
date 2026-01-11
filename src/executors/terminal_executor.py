from typing import Dict, Any
import subprocess
from .base_executor import BaseExecutor, ExecutionResult

class TerminalExecutor(BaseExecutor):
    def execute(self, action: str, params: Dict[str, Any]) -> ExecutionResult:
        if action != "terminal.run":
             return ExecutionResult(False, error=f"Unknown Terminal action: {action}")
        
        command = params.get("command")
        if not command:
             return ExecutionResult(False, error="Missing command")

        try:
            # Dangerous! Policy should block this unless Level 3.
            res = subprocess.run(command, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                return ExecutionResult(True, data=res.stdout)
            else:
                return ExecutionResult(False, error=res.stderr)
        except Exception as e:
            return ExecutionResult(False, error=str(e))
