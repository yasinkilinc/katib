#!/usr/bin/env python3
from src.core.policy import PolicyEngine, PermissionLevel

def test_strict_mode():
    policy_engine = PolicyEngine()
    policy_engine.set_strict_mode(True)
    result = policy_engine._evaluate_level(PermissionLevel.LOW_RISK)
    print(result.value)

if __name__ == "__main__":
    test_strict_mode()