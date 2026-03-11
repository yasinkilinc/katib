#!/usr/bin/env python3
from src.core.policy import PolicyEngine, PermissionLevel

def test_modes():
    # Test non-strict mode
    policy_engine = PolicyEngine()
    policy_engine.set_strict_mode(False)
    low_risk_result = policy_engine._evaluate_level(PermissionLevel.LOW_RISK)
    read_only_result = policy_engine._evaluate_level(PermissionLevel.READ_ONLY)

    print(f"Non-strict mode LOW_RISK: {low_risk_result.value}")
    print(f"Non-strict mode READ_ONLY: {read_only_result.value}")

    # Test strict mode
    policy_engine.set_strict_mode(True)
    low_risk_strict_result = policy_engine._evaluate_level(PermissionLevel.LOW_RISK)
    read_only_strict_result = policy_engine._evaluate_level(PermissionLevel.READ_ONLY)

    print(f"Strict mode LOW_RISK: {low_risk_strict_result.value}")
    print(f"Strict mode READ_ONLY: {read_only_strict_result.value}")

if __name__ == "__main__":
    test_modes()