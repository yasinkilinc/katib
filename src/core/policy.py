from enum import Enum
from typing import Dict, List, Optional
import time
import re

class PermissionLevel(Enum):
    READ_ONLY = 0      # Auto-execute (Safe)
    LOW_RISK = 1       # Auto-execute (Reversible)
    SENSITIVE = 2      # Notify -> Auto-execute
    HIGH_RISK = 3      # Explicit Confirmation Required

class PolicyDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_CONFIRMATION = "require_confirmation"

class PolicyEngine:
    def __init__(self):
        # Default policy mapping
        self.rules = {
            # LEVEL 0: Read Only
            "web.search": PermissionLevel.READ_ONLY,
            "interpreter.analyze": PermissionLevel.READ_ONLY,
            "app.list_running": PermissionLevel.READ_ONLY,
            "time.get": PermissionLevel.READ_ONLY,
            "weather.get": PermissionLevel.READ_ONLY,
            
            # LEVEL 1: Low Risk
            "app.focus": PermissionLevel.LOW_RISK,
            "system.volume": PermissionLevel.LOW_RISK,
            "tts.speak": PermissionLevel.LOW_RISK,
            "web.navigate": PermissionLevel.LOW_RISK, # Assuming harmless nav
            "system.stop": PermissionLevel.LOW_RISK, # User requested auto-approval
            
            # LEVEL 2: Sensitive
            "app.open": PermissionLevel.SENSITIVE,
            "app.close": PermissionLevel.SENSITIVE,
            "web.open_tab": PermissionLevel.SENSITIVE,
            "web.close_tab": PermissionLevel.SENSITIVE,
            
            # LEVEL 3: High Risk
            "interpreter.run_shell": PermissionLevel.HIGH_RISK,
            "interpreter.run_python": PermissionLevel.HIGH_RISK,
            "terminal.run": PermissionLevel.HIGH_RISK,
            "system.lock": PermissionLevel.HIGH_RISK,
            "email.send": PermissionLevel.HIGH_RISK,
            "file.write": PermissionLevel.HIGH_RISK,
            "file.delete": PermissionLevel.HIGH_RISK
        }
        
        # Temporary overrides: { "action": (PermissionLevel, expiry_timestamp) }
        self.overrides: Dict[str, tuple] = {}
        
        # Strict mode flag
        self.strict_mode = False

    def check_permission(self, action: str, params: Dict) -> PolicyDecision:
        """
        Determines if an action should be executed, denied, or confirmed.
        """

        # 1. Check for overrides
        if action in self.overrides:
            level, expiry = self.overrides[action]
            if time.time() < expiry:
                return self._evaluate_level(level)
            else:
                del self.overrides[action] # Expired

        # 2. Check hardcoded rules
        level = self.rules.get(action, PermissionLevel.HIGH_RISK) # Default to High Risk if unknown

        # 3. Dynamic Heuristics (e.g. "rm -rf" check)
        if action == "interpreter.run_shell":
            cmd = params.get("command", "").lower().strip()
            if self._is_dangerous_command(cmd):
                level = PermissionLevel.HIGH_RISK
            else:
                # For non-dangerous shell commands, reduce the risk level
                level = PermissionLevel.LOW_RISK

        return self._evaluate_level(level)

    def _evaluate_level(self, level: PermissionLevel) -> PolicyDecision:
        if self.strict_mode:
            # In strict mode, everything above Read-Only requires confirmation
            if level.value > 0:
                return PolicyDecision.REQUIRE_CONFIRMATION

        # In non-strict mode: READ_ONLY and LOW_RISK are auto-allowed
        # SENSITIVE and HIGH_RISK require confirmation
        if level == PermissionLevel.READ_ONLY:
            return PolicyDecision.ALLOW
        elif level == PermissionLevel.LOW_RISK:
            if not self.strict_mode:
                return PolicyDecision.ALLOW
            else:
                return PolicyDecision.REQUIRE_CONFIRMATION
        elif level == PermissionLevel.SENSITIVE:
            return PolicyDecision.REQUIRE_CONFIRMATION
        elif level == PermissionLevel.HIGH_RISK:
            return PolicyDecision.REQUIRE_CONFIRMATION

        return PolicyDecision.REQUIRE_CONFIRMATION

    def _is_dangerous_command(self, cmd: str) -> bool:
        """
        Enhanced heuristics for detecting dangerous shell commands.
        Returns True if the command is deemed dangerous.
        """
        # Basic command patterns that indicate danger
        dangerous_patterns = [
            r'\brm\b',                    # rm command
            r'\bsudo\b',                  # sudo command
            r'\bmv\b.*\/\.\.',            # mv moving to hidden directory
            r'\bchmod\b.*777',            # chmod 777 (too permissive)
            r'\bchown\b.*root',           # changing ownership to root
            r'rmdir\b',                   # removing directories
            r'\&\&',                     # chained commands
            r'\|\|',                      # conditional chaining
            r'\;\s*',                     # semicolon separators
            r'rm\s+-rf',                 # recursive delete
            r'rm\s+\/',                  # deleting from root
            r'rm\s+\~',                  # deleting home directory
            r'dd\b',                     # disk destruction utility
            r'kill\s+-9\s+',             # forced process termination
            r'pkill\b',                  # process killing
            r'killall\b',                # kill all processes
            r'passwd\b',                 # password change
            r'usermod\b',                # user modification
            r'groupmod\b',               # group modification
            r'adduser\b',                # user addition
            r'deluser\b',                # user deletion
            r'echo\b.*>.*\/etc\/',       # writing to system configs
            r'>\s*\/dev\/',              # writing to device files
            r'>\s*\/etc\/',              # redirecting to system configs
            r'docker\s+run.*--privileged', # privileged docker containers
            r'kubeadm\b',                # kubernetes admin commands
            r'kubectl\s+delete',         # kubernetes deletion
            r'format\b',                 # disk formatting
            r'fdisk\b',                  # disk partitioning
            r'umount\b',                 # unmounting disks
            r'cryptsetup\b',             # encryption setup
            r'wipe\b',                   # secure erase
            r'shred\b',                  # secure erase
        ]

        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, cmd):
                return True

        # Check for dangerous character sequences in specific contexts
        dangerous_sequences = [
            ('..', '/../'),               # Directory traversal
            ('~', 'rm ~'),                # Home directory deletion
            ('/', 'rm /'),                # Root directory deletion
            ('*', 'rm *'),                # Wildcard deletion
        ]

        for needle, haystack in dangerous_sequences:
            if needle in cmd and haystack in cmd:
                return True

        # Check if command contains multiple complex redirections
        redirection_count = cmd.count('>') + cmd.count('>>') + cmd.count('<')
        if redirection_count > 2:
            return True

        # Check for potential command injection
        if '`' in cmd or '$(' in cmd:
            return True

        return False

    def set_strict_mode(self, enabled: bool):
        self.strict_mode = enabled

    def grant_temporary_override(self, action: str, level: PermissionLevel, duration_seconds: int = 300):
        self.overrides[action] = (level, time.time() + duration_seconds)
