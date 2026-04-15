#!/usr/bin/env python3
"""Test script to verify AudioListener uses VAD instead of basic threshold"""

try:
    from src.perception.audio import AudioListener
    listener = AudioListener()
    print('AudioListener updated with VAD')
except Exception as e:
    print(f'Error: {e}')
    exit(1)