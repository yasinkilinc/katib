import subprocess
import shlex
import os
from typing import Dict, Any
from .base_executor import BaseExecutor, ExecutionResult

class TerminalExecutor(BaseExecutor):
    def __init__(self):
        super().__init__()
        # Define dangerous command patterns that should be blocked
        self.dangerous_patterns = [
            'rm ', 'rm -', '>', '>>', '|', '&', ';',
            '`', '$(', '${', 'eval', 'exec', 'source',
            '/dev/null', '/dev/tcp/', '/dev/udp/',
            'chmod', 'chown', 'mv ', 'ln ',
            'cat /', 'less /', 'more /', 'head /', 'tail /'
        ]

        # Define allowed safe commands
        self.allowed_commands = [
            'ls', 'pwd', 'echo', 'date', 'whoami', 'hostname',
            'ps', 'top', 'htop', 'df', 'du', 'free',
            'cat', 'less', 'more', 'head', 'tail',
            'grep', 'find', 'which', 'whereis', 'whatis',
            'man', 'help', 'history', 'clear', 'uname'
        ]

    def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validates the command against dangerous patterns and allowed commands list.
        Returns (is_valid, error_message)
        """
        if not command.strip():
            return False, "Empty command provided"

        # Check for dangerous patterns
        command_lower = command.lower()
        for pattern in self.dangerous_patterns:
            if pattern in command_lower:
                return False, f"Dangerous pattern detected in command: {pattern}"

        # Extract the base command (first part before any arguments)
        parts = shlex.split(command)
        if parts:
            base_cmd = parts[0].split('/')[-1]  # Get command name without path
            if base_cmd not in self.allowed_commands:
                return False, f"Command '{base_cmd}' is not in the allowed list"

            # Additional checks for specific commands
            if base_cmd in ['cat', 'less', 'more', 'head', 'tail']:
                # Check if accessing potentially sensitive files
                for arg in parts[1:]:
                    if any(sensitive in arg.lower() for sensitive in ['passwd', 'shadow', 'etc/', '/root']):
                        return False, f"Access to sensitive file attempted: {arg}"

        return True, ""

    def sanitize_command(self, command: str) -> str:
        """
        Sanitizes the command by removing potentially dangerous elements.
        This is a conservative approach that complements the validation.
        """
        # Strip leading/trailing whitespace
        sanitized = command.strip()

        # Additional sanitization can be implemented here as needed
        # For now, returning the command after validation should be sufficient
        return sanitized

    def execute(self, action: str, params: Dict[str, Any]) -> ExecutionResult:
        if action != "terminal.run":
             return ExecutionResult(False, error=f"Unknown Terminal action: {action}")

        command = params.get("command")
        if not command:
             return ExecutionResult(False, error="Missing command")

        # Validate the command first
        is_valid, validation_error = self.validate_command(command)
        if not is_valid:
            return ExecutionResult(False, error=f"Command validation failed: {validation_error}")

        # Sanitize the command
        sanitized_command = self.sanitize_command(command)

        try:
            # Parse command safely to prevent shell injection
            # Split command into argument list to avoid shell=True
            cmd_parts = shlex.split(sanitized_command)

            # Execute command without shell to prevent injection
            res = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)
            if res.returncode == 0:
                return ExecutionResult(True, data=res.stdout)
            else:
                return ExecutionResult(False, error=res.stderr)
        except subprocess.TimeoutExpired:
            return ExecutionResult(False, error="Command execution timed out")
        except FileNotFoundError:
            return ExecutionResult(False, error=f"Command not found: {cmd_parts[0] if cmd_parts else 'unknown'}")
        except Exception as e:
            return ExecutionResult(False, error=str(e))
