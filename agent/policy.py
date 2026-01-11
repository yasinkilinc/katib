"""
Policy Engine - Advanced Guardrails for Agent
Decides whether to ALLOW, DENY, or REQUIRE_CONFIRMATION for tool calls based on context and rules.
"""
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import os

class PolicyDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    CONFIRM = "confirm"

@dataclass
class PolicyResult:
    decision: PolicyDecision
    reason: str

class PolicyEngine:
    """
    Evaluates tool calls against a set of security rules.
    """
    
    def __init__(self):
        # Configuration could be loaded from a file
        self.restricted_paths = ["/etc", "/var", "/usr", "/System"]
        self.max_volume = 80
        
    def evaluate(self, tool_name: str, arguments: Dict[str, Any], tool_metadata: Dict[str, Any]) -> PolicyResult:
        """
        Evaluate a tool call and return a decision.
        """
        
        # 1. Rule: Unsafe tools always require confirmation (Baseline)
        if tool_metadata.get("unsafe", False) or tool_metadata.get("requiresConfirmation", False):
            # We can refine this. Maybe generic unsafe check is enough for now to trigger CONFIRM
            # But let's check specific rules first that might DENY it outright.
            pass
            
        # 2. Rule: Filesystem Restrictions
        if tool_name in ["read_file", "write_file", "list_directory", "file_search"]:
            path = arguments.get("path", "")
            if path:
                # Resolve absolute path to check restrictions
                abs_path = os.path.abspath(path)
                for restricted in self.restricted_paths:
                    if abs_path.startswith(restricted):
                        return PolicyResult(
                            PolicyDecision.DENY, 
                            f"Access to '{restricted}' directories is prohibited by policy."
                        )
        
        # 3. Rule: Volume Safety Check
        if tool_name == "set_volume":
            level = arguments.get("level", 0)
            if level > self.max_volume:
                return PolicyResult(
                    PolicyDecision.CONFIRM,
                    f"Volume level {level} exceeds safety limit of {self.max_volume}. Confirm high volume?"
                )
        
        # 4. Rule: Default Unsafe Handling
        if tool_metadata.get("unsafe", False):
            return PolicyResult(
                PolicyDecision.CONFIRM,
                f"Tool '{tool_name}' is marked as UNSAFE. Operation requires approval."
            )
            
        # 5. Rule: Explicit Confirmation Flag
        if tool_metadata.get("requiresConfirmation", False):
             return PolicyResult(
                PolicyDecision.CONFIRM,
                f"Tool '{tool_name}' explicitly requires confirmation."
            )

        # Default: ALLOW
        return PolicyResult(PolicyDecision.ALLOW, "Safe operation.")

# Singleton
_policy_engine: Optional[PolicyEngine] = None

def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
