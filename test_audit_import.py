#!/usr/bin/env python3
"""
Test script to verify that the AuditLogger can be imported successfully
after adding sensitive data detection and sanitization methods.
"""

try:
    from src.mcp.audit import AuditLogger

    # Create an instance of the logger
    logger = AuditLogger()

    # Test the sanitization methods
    test_data = {
        "password": "my_secret_password",
        "email": "user@example.com",
        "api_key": "abc123def456ghi789",
        "normal_param": "value"
    }

    sanitized = logger._sanitize_dict(test_data)

    print("SUCCESS: AuditLogger imports successfully")
    print(f"Original data: {test_data}")
    print(f"Sanitized data: {sanitized}")

    # Verify that sensitive data was redacted
    assert sanitized["password"] == "***REDACTED***", "Password was not redacted"
    assert sanitized["api_key"] == "***REDACTED***", "API key was not redacted"
    assert sanitized["normal_param"] == "value", "Normal param was incorrectly modified"

    print("SUCCESS: Sanitization methods work correctly")

except ImportError as e:
    print(f"ERROR: Import failed - {e}")
except Exception as e:
    print(f"ERROR: Unexpected error - {e}")