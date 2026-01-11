"""
Policy Engine - Decides whether to allow, deny, or require approval
"""
from typing import Optional
from .capabilities import CapabilityRequest, PolicyResult, Origin
from .registry import get_capability, CapabilityDefinition
from .audit import get_audit_logger

class PolicyEngine:
    """
    Evaluates capability requests against policy rules.
    This is where security decisions are made.
    """
    
    def __init__(self):
        self.audit = get_audit_logger()
    
    def evaluate(self, request: CapabilityRequest) -> PolicyResult:
        """
        Evaluate a capability request and return policy decision.
        """
        capability = get_capability(request.name)
        
        if not capability:
            return PolicyResult(
                denied=True,
                reason=f"Unknown capability: {request.name}"
            )
        
        # Rule 1: Check if capability inherently requires approval
        if capability.requires_approval:
            return PolicyResult(
                requires_approval=True,
                reason=f"Capability '{request.name}' requires user approval"
            )
        
        # Rule 2: System origin + sensitive actions = blocked
        if request.origin == Origin.SYSTEM:
            if capability.requires_approval or capability.sandbox:
                return PolicyResult(
                    denied=True,
                    reason="System-originated requests cannot execute sensitive capabilities"
                )
        
        # Rule 3: History-based escalation
        recent_failures = self.audit.get_recent_failures(request.name, limit=5)
        if len(recent_failures) >= 3:
            return PolicyResult(
                requires_approval=True,
                reason=f"Capability '{request.name}' has failed {len(recent_failures)} times recently"
            )
        
        # Rule 4: Sandbox requirement check
        if capability.sandbox and request.origin != Origin.UI:
            # Non-UI requests to sandboxed capabilities need approval
            return PolicyResult(
                requires_approval=True,
                reason=f"Sandbox capability requires explicit approval for {request.origin.value} origin"
            )
        
        # All checks passed
        return PolicyResult(approved=True)
    
    def request_approval(self, request: CapabilityRequest, reason: str) -> bool:
        """
        Request user approval for a capability.
        Returns True if approved, False if denied.
        """
        print(f"\n[!] Approval Required: {reason}")
        print(f"    Capability: {request.name}")
        print(f"    Parameters: {request.parameters}")
        print(f"    Origin: {request.origin.value}")
        
        try:
            response = input("    Approve? [y/N]: ").strip().lower()
            return response == 'y'
        except:
            return False
