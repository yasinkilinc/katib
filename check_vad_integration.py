#!/usr/bin/env python3
"""Test script to verify AudioListener class structure with VAD integration"""

import sys
import inspect

# Try to import just the class definition without initializing
try:
    # Import the source code as text to check structure
    with open('./src/perception/audio.py', 'r') as f:
        content = f.read()

    # Check if essential VAD elements are present
    has_import = 'from .vad import VoiceActivityDetector' in content
    has_vad_init = 'self.vad = VoiceActivityDetector(' in content
    has_vad_usage = 'self.vad.is_voice_present(' in content
    has_flatten_call = '.flatten()' in content

    print(f"✓ Import VAD: {has_import}")
    print(f"✓ Initialize VAD: {has_vad_init}")
    print(f"✓ Use VAD in loop: {has_vad_usage}")
    print(f"✓ Use flatten for multi-channel: {has_flatten_call}")

    if all([has_import, has_vad_init, has_vad_usage]):
        print("AudioListener updated with VAD")
    else:
        print("Missing some VAD integration elements")
        sys.exit(1)

except Exception as e:
    print(f"Error checking AudioListener: {e}")
    sys.exit(1)