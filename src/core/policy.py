from enum import Enum
from typing import Dict, List, Optional
import time

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
            cmd = params.get("command", "")
            if "rm " in cmd or "sudo " in cmd or ">" in cmd:
                level = PermissionLevel.HIGH_RISK

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

    def set_strict_mode(self, enabled: bool):
        self.strict_mode = enabled

    def grant_temporary_override(self, action: str, level: PermissionLevel, duration_seconds: int = 300):
        self.overrides[action] = (level, time.time() + duration_seconds)
