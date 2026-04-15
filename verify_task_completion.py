#!/usr/bin/env python3
from src.core.policy import PolicyEngine, PermissionLevel

def verify_sensitive_action():
    """Verify that SENSITIVE actions now require confirmation."""
    p = PolicyEngine()
    result = p._evaluate_level(PermissionLevel.SENSITIVE)
    print(f'SENSITIVE action evaluation result: {result.value}')

    # Verify expected behavior
    if result.value == "require_confirmation":
        print("SUCCESS: SENSITIVE actions now require confirmation")
        return True
    else:
        print(f"FAILURE: Expected 'require_confirmation', got '{result.value}'")
        return False

if __name__ == "__main__":
    success = verify_sensitive_action()
    exit(0 if success else 1)