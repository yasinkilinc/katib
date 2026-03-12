import subprocess
import shlex
from typing import Dict, Any
from .base_executor import BaseExecutor, ExecutionResult

class TerminalExecutor(BaseExecutor):
    def execute(self, action: str, params: Dict[str, Any]) -> ExecutionResult:
        if action != "terminal.run":
             return ExecutionResult(False, error=f"Unknown Terminal action: {action}")

        command = params.get("command")
        if not command:
             return ExecutionResult(False, error="Missing command")

        try:
            # Parse command safely to prevent shell injection
            # Split command into argument list to avoid shell=True
            cmd_parts = shlex.split(command)

            # Execute command without shell to prevent injection
            res = subprocess.run(cmd_parts, capture_output=True, text=True)
            if res.returncode == 0:
                return ExecutionResult(True, data=res.stdout)
            else:
                return ExecutionResult(False, error=res.stderr)
        except FileNotFoundError:
            return ExecutionResult(False, error=f"Command not found: {cmd_parts[0] if cmd_parts else 'unknown'}")
        except Exception as e:
            return ExecutionResult(False, error=str(e))
