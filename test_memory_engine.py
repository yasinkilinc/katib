#!/usr/bin/env python3
"""Test script to verify MemoryEngine functionality"""

from src.core.memory import MemoryEngine

def test_import():
    """Test that MemoryEngine can be imported and instantiated"""
    try:
        mem = MemoryEngine()
        print("MemoryEngine imports successfully")
        return True
    except Exception as e:
        print(f"Error importing MemoryEngine: {e}")
        return False

def test_sanitization_methods():
    """Test that the new sanitization methods exist"""
    try:
        mem = MemoryEngine()
        # Check if the new methods exist
        assert hasattr(mem, '_sanitize_value'), "_sanitize_value method not found"
        assert hasattr(mem, 'sanitize_data'), "sanitize_data method not found"
        print("Sanitization methods exist")
        return True
    except Exception as e:
        print(f"Error testing sanitization methods: {e}")
        return False

if __name__ == "__main__":
    success = test_import() and test_sanitization_methods()
    if success:
        print("All tests passed!")
    else:
        print("Tests failed!")