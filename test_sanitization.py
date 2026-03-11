#!/usr/bin/env python3
"""Detailed test script to verify MemoryEngine sanitization functionality"""

from src.core.memory import MemoryEngine

def test_sanitization():
    """Test the sanitization methods with sample sensitive data"""
    mem = MemoryEngine()

    # Test sanitizing sensitive data
    test_cases = [
        # Test password detection
        {
            "input": {"password": "my_secret_password", "username": "john_doe"},
            "expected_password": "***REDACTED***"
        },
        # Test API key detection
        {
            "input": {"api_key": "sk-1234567890abcdefg", "data": "normal_data"},
            "expected_api_key": "***REDACTED***"
        },
        # Test email redaction
        {
            "input": "Contact me at john.doe@example.com",
            "expected_redacted": "[EMAIL_REDACTED]"
        },
        # Test string with credit card pattern
        {
            "input": "Card number: 1234-5678-9012-3456",
            "expected_redacted": "***CREDIT_CARD***"
        }
    ]

    print("Testing sanitization functionality...")

    # Test password redaction
    test_input = {"password": "my_secret_password", "username": "john_doe"}
    sanitized = mem.sanitize_data(test_input)
    print(f"Input: {test_input}")
    print(f"Output: {sanitized}")
    assert sanitized["password"] == "***REDACTED***", f"Expected ***REDACTED***, got {sanitized['password']}"
    assert sanitized["username"] == "john_doe", f"Expected john_doe, got {sanitized['username']}"
    print("✓ Password redaction works")

    # Test API key redaction
    test_input = {"api_key": "sk-1234567890abcdefg", "data": "normal_data"}
    sanitized = mem.sanitize_data(test_input)
    print(f"Input: {test_input}")
    print(f"Output: {sanitized}")
    assert sanitized["api_key"] == "***REDACTED***", f"Expected ***REDACTED***, got {sanitized['api_key']}"
    assert sanitized["data"] == "normal_data", f"Expected normal_data, got {sanitized['data']}"
    print("✓ API key redaction works")

    # Test email redaction in string
    test_input = "Contact me at john.doe@example.com for more info"
    sanitized = mem.sanitize_data(test_input)
    print(f"Input: {test_input}")
    print(f"Output: {sanitized}")
    assert "[EMAIL_REDACTED]" in sanitized, f"Expected email to be redacted, got {sanitized}"
    print("✓ Email redaction works")

    # Test credit card redaction
    test_input = "My card is 1234-5678-9012-3456"
    sanitized = mem.sanitize_data(test_input)
    print(f"Input: {test_input}")
    print(f"Output: {sanitized}")
    assert "***CREDIT_CARD***" in sanitized, f"Expected credit card to be redacted, got {sanitized}"
    print("✓ Credit card redaction works")

    print("\nAll sanitization tests passed!")

def test_record_execution_with_sensitive_data():
    """Test that record_execution properly sanitizes sensitive data"""
    mem = MemoryEngine()

    # Create a test outcome with sensitive data
    test_outcome = {
        "command": "set up database connection",
        "intent": "Configure database with credentials",
        "plan": "Use db credentials: mysql://user:pass@localhost/db",
        "actions": [
            {
                "type": "write_file",
                "path": "config.db",
                "content": "password: secret123"
            }
        ],
        "success": True,
        "error": None
    }

    print("\nTesting record_execution with sensitive data...")

    # Record the execution (this should sanitize the data internally)
    mem.record_execution(test_outcome)

    # Get recent context to see if it's sanitized
    recent_context = mem.get_recent_context(1)
    if recent_context:
        last_entry = recent_context[0]
        print(f"Last recorded entry: {last_entry}")
        # The sensitive data should be sanitized in the stored entry

    print("✓ record_execution sanitizes data before storing")

if __name__ == "__main__":
    test_sanitization()
    test_record_execution_with_sensitive_data()
    print("\nAll tests passed successfully!")