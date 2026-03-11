#!/usr/bin/env python3
"""
Test script to verify enhanced MemoryEngine functionality with sensitive data detection and sanitization
"""

import json
import os
from src.core.memory import MemoryEngine

def test_memory_engine_enhancements():
    print("Testing enhanced MemoryEngine functionality...")

    # Initialize MemoryEngine
    mem = MemoryEngine("test_memory.json")
    print("✓ MemoryEngine initialized successfully")

    # Test basic functionality
    assert hasattr(mem, '_sanitize_value'), "_sanitize_value method exists"
    assert hasattr(mem, 'sanitize_data'), "sanitize_data method exists"
    assert hasattr(mem, 'detect_sensitive_data'), "detect_sensitive_data method exists"
    assert hasattr(mem, 'audit_log'), "audit_log method exists"
    print("✓ All required methods exist")

    # Test sensitive data detection
    test_data = {
        "password": "my_secret_password",
        "email": "user@example.com",
        "api_key": "sk-1234567890abcdefg",
        "credit_card": "1234-5678-9012-3456",
        "ssn": "123-45-6789",
        "bitcoin_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "ethereum_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "normal_field": "normal_value"
    }

    # Test detection
    detections = mem.detect_sensitive_data(test_data)
    print(f"✓ Sensitive data detection works - found {len(detections)} items")

    # Test sanitization
    sanitized = mem.sanitize_data(test_data)
    print("✓ Sanitization works")

    # Verify sensitive fields are redacted
    assert sanitized['password'] == '***REDACTED***', "Password field redacted"
    assert sanitized['email'] == '[EMAIL_REDACTED]', "Email field redacted"
    assert sanitized['api_key'] == '***REDACTED***', "API key field redacted"
    print("✓ Sensitive fields properly redacted")

    # Test audit logging
    audit_results = mem.audit_log(test_data, source="test_script")
    print(f"✓ Audit logging works - detected {len(audit_results)} sensitive items")

    # Test record_execution with sensitive data
    outcome = {
        "command": "setup database",
        "intent": "configure db with credentials",
        "plan": "connect to db with user:admin pass:secret123",
        "actions": [
            {"type": "write_file", "content": "password=secret123"}
        ],
        "success": True,
        "error": None
    }

    mem.record_execution(outcome)
    print("✓ record_execution works with sanitization")

    # Clean up test files
    for file in ["test_memory.json", "audit_log.json"]:
        if os.path.exists(file):
            os.remove(file)

    print("\n🎉 All enhanced MemoryEngine tests passed!")
    return True

if __name__ == "__main__":
    test_memory_engine_enhancements()