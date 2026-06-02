#!/usr/bin/env python3
"""
Test script to validate Voice Activity Detection (VAD) accuracy and false trigger rate.

This script tests the VAD algorithm with various audio scenarios to measure:
1. Accuracy: How well VAD detects actual speech vs silence
2. False trigger rate: How often VAD incorrectly identifies speech in silence
3. Sensitivity: How well VAD captures actual speech segments
"""

import argparse
import numpy as np
import sys
import os
import json
from datetime import datetime

# Add the parent directory to the path to import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.perception.vad import VoiceActivityDetector

def generate_test_signal(duration, sample_rate=16000, signal_type="silence", amplitude=0.1, frequency=440):
    """
    Generate test audio signals of different types

    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        signal_type: Type of signal ('silence', 'sine', 'speech_like')
        amplitude: Signal amplitude
        frequency: Frequency for sine waves

    Returns:
        numpy array with audio samples
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    if signal_type == "silence":
        # Pure silence with slight random noise
        return np.random.normal(0, amplitude * 0.01, len(t))
    elif signal_type == "sine":
        # Pure sine wave tone
        return amplitude * np.sin(2 * np.pi * frequency * t)
    elif signal_type == "speech_like":
        # Simulated speech-like signal with varying amplitude
        envelope = np.random.uniform(0.3, 1.0, len(t))  # Random envelope
        carrier = np.sin(2 * np.pi * (frequency + 100 * np.sin(2 * np.pi * 5 * t)) * t)
        return amplitude * envelope * carrier
    else:
        return np.zeros(len(t))

def run_accuracy_test(vad_detector, test_scenarios, verbose=False):
    """
    Run accuracy tests with various audio scenarios

    Args:
        vad_detector: VoiceActivityDetector instance
        test_scenarios: List of tuples (signal_type, expected_result, duration, description)
        verbose: Print detailed results if True

    Returns:
        dict with test results
    """
    results = {
        "total_tests": 0,
        "correct_predictions": 0,
        "false_positives": 0,  # Detected voice when it was silence
        "false_negatives": 0,  # Missed voice when it was present
        "true_positives": 0,   # Correctly detected voice
        "true_negatives": 0,   # Correctly identified silence
        "accuracy": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0,
        "details": []
    }

    for scenario in test_scenarios:
        signal_type, expected_voice, duration, description = scenario
        sample_rate = vad_detector.sample_rate

        # Generate test signal
        audio_signal = generate_test_signal(
            duration=duration,
            sample_rate=sample_rate,
            signal_type=signal_type
        )

        # Calculate frame size based on VAD configuration
        frame_size = vad_detector.frame_size

        # Split signal into frames and test each frame
        frames_correct = 0
        frame_count = 0

        for i in range(0, len(audio_signal), frame_size):
            chunk = audio_signal[i:i + frame_size]

            # Pad if needed
            if len(chunk) < frame_size:
                padded_chunk = np.zeros(frame_size)
                padded_chunk[:len(chunk)] = chunk
                chunk = padded_chunk

            # Get VAD prediction
            vad_result = vad_detector.is_voice_present(chunk, update_threshold=False)

            # Count results
            if expected_voice and vad_result:
                results["true_positives"] += 1
                frames_correct += 1
            elif not expected_voice and not vad_result:
                results["true_negatives"] += 1
                frames_correct += 1
            elif not expected_voice and vad_result:
                results["false_positives"] += 1
            elif expected_voice and not vad_result:
                results["false_negatives"] += 1

            frame_count += 1

        accuracy_per_frame = frames_correct / frame_count if frame_count > 0 else 0

        if verbose:
            print(f"Scenario: {description}")
            print(f"  Expected: {'VOICE' if expected_voice else 'SILENCE'}, "
                  f"Detected: {frames_correct}/{frame_count} frames correctly "
                  f"({accuracy_per_frame:.2%})")
            print()

        results["details"].append({
            "scenario": description,
            "expected_voice": expected_voice,
            "true_positives": sum(1 for x in range(0, len(audio_signal), frame_size)
                                  if x + frame_size <= len(audio_signal) and
                                  vad_detector.is_voice_present(audio_signal[x:x + frame_size],
                                                              update_threshold=False) and expected_voice),
            "true_negatives": sum(1 for x in range(0, len(audio_signal), frame_size)
                                  if x + frame_size <= len(audio_signal) and
                                  not vad_detector.is_voice_present(audio_signal[x:x + frame_size],
                                                                  update_threshold=False) and not expected_voice),
            "false_positives": sum(1 for x in range(0, len(audio_signal), frame_size)
                                   if x + frame_size <= len(audio_signal) and
                                   vad_detector.is_voice_present(audio_signal[x:x + frame_size],
                                                               update_threshold=False) and not expected_voice),
            "false_negatives": sum(1 for x in range(0, len(audio_signal), frame_size)
                                   if x + frame_size <= len(audio_signal) and
                                   not vad_detector.is_voice_present(audio_signal[x:x + frame_size],
                                                                   update_threshold=False) and expected_voice),
            "frames_analyzed": frame_count,
            "accuracy": accuracy_per_frame
        })

        results["total_tests"] += frame_count
        results["correct_predictions"] += frames_correct

    # Calculate overall metrics
    if results["total_tests"] > 0:
        results["accuracy"] = results["correct_predictions"] / results["total_tests"]

        # Precision = True Positives / (True Positives + False Positives)
        if (results["true_positives"] + results["false_positives"]) > 0:
            results["precision"] = results["true_positives"] / (results["true_positives"] + results["false_positives"])

        # Recall = True Positives / (True Positives + False Negatives)
        if (results["true_positives"] + results["false_negatives"]) > 0:
            results["recall"] = results["true_positives"] / (results["true_positives"] + results["false_negatives"])

        # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
        if (results["precision"] + results["recall"]) > 0:
            results["f1_score"] = 2 * (results["precision"] * results["recall"]) / (results["precision"] + results["recall"])

    return results

def run_false_trigger_test(vad_detector, duration=10.0, background_noise_level=0.01, verbose=False):
    """
    Test false trigger rate with pure silence or low-level background noise

    Args:
        vad_detector: VoiceActivityDetector instance
        duration: Duration of test in seconds
        background_noise_level: Amplitude of background noise
        verbose: Print detailed results if True

    Returns:
        dict with false trigger statistics
    """
    sample_rate = vad_detector.sample_rate
    frame_size = vad_detector.frame_size

    # Generate silence with very low background noise
    silence_signal = generate_test_signal(
        duration=duration,
        sample_rate=sample_rate,
        signal_type="silence",
        amplitude=background_noise_level
    )

    false_triggers = 0
    total_frames = 0

    for i in range(0, len(silence_signal), frame_size):
        chunk = silence_signal[i:i + frame_size]

        # Pad if needed
        if len(chunk) < frame_size:
            padded_chunk = np.zeros(frame_size)
            padded_chunk[:len(chunk)] = chunk
            chunk = padded_chunk

        # Test VAD - should return False for pure silence
        vad_result = vad_detector.is_voice_present(chunk, update_threshold=False)

        if vad_result:
            false_triggers += 1

        total_frames += 1

    false_trigger_rate = false_triggers / total_frames if total_frames > 0 else 0

    if verbose:
        print(f"False Trigger Test:")
        print(f"  Duration: {duration}s")
        print(f"  Background noise level: {background_noise_level}")
        print(f"  Total frames analyzed: {total_frames}")
        print(f"  False triggers: {false_triggers}")
        print(f"  False trigger rate: {false_trigger_rate:.4f} ({false_trigger_rate * 100:.2f}%)")
        print()

    return {
        "duration": duration,
        "background_noise_level": background_noise_level,
        "total_frames": total_frames,
        "false_triggers": false_triggers,
        "false_trigger_rate": false_trigger_rate
    }

def run_adaptation_test(vad_detector, verbose=False):
    """
    Test how well the VAD adapts to changing background noise levels

    Args:
        vad_detector: VoiceActivityDetector instance
        verbose: Print detailed results if True

    Returns:
        dict with adaptation test results
    """
    sample_rate = vad_detector.sample_rate
    frame_size = vad_detector.frame_size

    # Start with low background noise
    initial_noise = generate_test_signal(
        duration=2.0,  # 2 seconds of initial low noise
        sample_rate=sample_rate,
        signal_type="silence",
        amplitude=0.01
    )

    # Then introduce higher background noise
    higher_noise = generate_test_signal(
        duration=2.0,  # 2 seconds of higher noise
        sample_rate=sample_rate,
        signal_type="silence",
        amplitude=0.05
    )

    # Combine the two
    combined_signal = np.concatenate([initial_noise, higher_noise])

    false_triggers_initial = 0
    false_triggers_higher = 0
    total_initial = 0
    total_higher = 0

    # Process initial low noise section
    for i in range(0, len(initial_noise), frame_size):
        chunk = initial_noise[i:i + frame_size]

        # Pad if needed
        if len(chunk) < frame_size:
            padded_chunk = np.zeros(frame_size)
            padded_chunk[:len(chunk)] = chunk
            chunk = padded_chunk

        vad_result = vad_detector.is_voice_present(chunk, update_threshold=True)  # Allow threshold updates

        if vad_result:
            false_triggers_initial += 1
        total_initial += 1

    # Process higher noise section
    for i in range(0, len(higher_noise), frame_size):
        chunk = higher_noise[i:i + frame_size]

        # Pad if needed
        if len(chunk) < frame_size:
            padded_chunk = np.zeros(frame_size)
            padded_chunk[:len(chunk)] = chunk
            chunk = padded_chunk

        vad_result = vad_detector.is_voice_present(chunk, update_threshold=True)  # Allow threshold updates

        if vad_result:
            false_triggers_higher += 1
        total_higher += 1

    false_rate_initial = false_triggers_initial / total_initial if total_initial > 0 else 0
    false_rate_higher = false_triggers_higher / total_higher if total_higher > 0 else 0

    if verbose:
        print(f"Adaptation Test:")
        print(f"  Initial noise level: 0.01, Frames: {total_initial}, False triggers: {false_triggers_initial}, Rate: {false_rate_initial:.4f}")
        print(f"  Higher noise level: 0.05, Frames: {total_higher}, False triggers: {false_triggers_higher}, Rate: {false_rate_higher:.4f}")
        print()

    return {
        "initial_noise_level": 0.01,
        "higher_noise_level": 0.05,
        "frames_initial": total_initial,
        "frames_higher": total_higher,
        "false_triggers_initial": false_triggers_initial,
        "false_triggers_higher": false_triggers_higher,
        "false_rate_initial": false_rate_initial,
        "false_rate_higher": false_rate_higher,
        "adaptation_improvement": false_rate_initial - false_rate_higher  # Positive if adaptation helps
    }

def main():
    parser = argparse.ArgumentParser(description="Test Voice Activity Detection accuracy and false trigger rate")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed results")
    parser.add_argument("--output", "-o", type=str, help="Output JSON file for detailed results")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Sample rate for testing (default: 16000)")
    parser.add_argument("--threshold-multiplier", type=float, default=1.5, help="Energy threshold multiplier (default: 1.5)")

    args = parser.parse_args()

    print("Voice Activity Detection (VAD) Accuracy Test")
    print("=" * 50)

    # Initialize VAD detector with specified parameters
    vad_detector = VoiceActivityDetector(
        sample_rate=args.sample_rate,
        energy_threshold_multiplier=args.threshold_multiplier
    )

    # Define test scenarios
    test_scenarios = [
        # (signal_type, expected_result, duration, description)
        ("silence", False, 3.0, "Pure silence"),
        ("sine", True, 2.0, "440Hz sine wave (simulated clear speech)"),
        ("speech_like", True, 3.0, "Simulated speech-like signal"),
        ("silence", False, 2.0, "Additional silence"),
        ("speech_like", True, 2.5, "More speech-like signal"),
    ]

    print(f"Test Configuration:")
    print(f"  Sample Rate: {args.sample_rate} Hz")
    print(f"  Threshold Multiplier: {args.threshold_multiplier}")
    print()

    # Run accuracy test
    print("Running accuracy tests...")
    accuracy_results = run_accuracy_test(vad_detector, test_scenarios, verbose=args.verbose)

    # Run false trigger test
    print("Running false trigger test...")
    false_trigger_results = run_false_trigger_test(vad_detector, duration=5.0, verbose=args.verbose)

    # Run adaptation test
    print("Running adaptation test...")
    adaptation_results = run_adaptation_test(vad_detector, verbose=args.verbose)

    # Print summary
    print("SUMMARY")
    print("=" * 50)
    print(f"Overall Accuracy: {accuracy_results['accuracy']:.4f} ({accuracy_results['accuracy'] * 100:.2f}%)")
    print(f"Precision: {accuracy_results['precision']:.4f}")
    print(f"Recall: {accuracy_results['recall']:.4f}")
    print(f"F1-Score: {accuracy_results['f1_score']:.4f}")
    print(f"Total Frames Tested: {accuracy_results['total_tests']}")
    print(f"False Trigger Rate: {false_trigger_results['false_trigger_rate']:.4f} ({false_trigger_results['false_trigger_rate'] * 100:.2f}%)")
    print()

    # Evaluate performance
    performance_score = 0
    max_performance_score = 100

    # Accuracy contributes up to 60 points
    accuracy_contribution = min(accuracy_results['accuracy'] * 100 * 0.6, 60)
    performance_score += accuracy_contribution

    # Low false trigger rate contributes up to 40 points
    false_trigger_penalty = min(false_trigger_results['false_trigger_rate'] * 100, 40)
    performance_score += (40 - false_trigger_penalty)

    print(f"Performance Score: {performance_score:.1f}/{max_performance_score}")

    if performance_score >= 90:
        print("Status: EXCELLENT - VAD performs very well")
    elif performance_score >= 75:
        print("Status: GOOD - VAD performs adequately")
    elif performance_score >= 60:
        print("Status: FAIR - VAD may need tuning")
    else:
        print("Status: POOR - VAD needs significant improvement")

    # Save results to file if requested
    if args.output:
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "sample_rate": args.sample_rate,
                "threshold_multiplier": args.threshold_multiplier
            },
            "accuracy_results": accuracy_results,
            "false_trigger_results": false_trigger_results,
            "adaptation_results": adaptation_results,
            "performance_score": performance_score
        }

        with open(args.output, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"\nDetailed results saved to: {args.output}")

    return 0

if __name__ == "__main__":
    sys.exit(main())