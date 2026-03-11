#!/usr/bin/env python3
"""
Test script to verify the MemoryEngine can be imported successfully
"""
try:
    from src.core.memory import MemoryEngine
    mem = MemoryEngine()
    print('SUCCESS: Modified MemoryEngine imports successfully')
except Exception as e:
    print(f'ERROR: Failed to import MemoryEngine: {e}')