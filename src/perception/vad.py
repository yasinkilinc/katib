"""
Voice Activity Detection (VAD) module using energy-based detection and audio processing.
"""
import numpy as np
import os
import sys

# Create a minimal config to avoid dependency issues during testing
class MinimalConfig:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    SILENCE_THRESHOLD = 20.0  # Default threshold

try:
    from ..config import Config
except ImportError:
    # Use minimal config if full config is not available
    Config = MinimalConfig()


class VoiceActivityDetector:
    """
    Voice Activity Detector class that implements basic VAD functionality.
    Uses energy-based detection methods to determine speech presence in audio chunks.
    """

    def __init__(self, sample_rate=None, frame_duration_ms=30, energy_threshold_multiplier=1.5):
        """
        Initialize the VAD detector.

        Args:
            sample_rate: Audio sample rate (defaults to Config.SAMPLE_RATE if None)
            frame_duration_ms: Duration of each analysis frame in milliseconds
            energy_threshold_multiplier: Multiplier for dynamic threshold adjustment
        """
        self.sample_rate = sample_rate or Config.SAMPLE_RATE
        self.frame_duration_ms = frame_duration_ms
        self.energy_threshold_multiplier = energy_threshold_multiplier

        # Calculate frame size based on duration and sample rate
        self.frame_size = int((frame_duration_ms / 1000.0) * self.sample_rate)

        # Dynamic threshold for adaptive detection
        self.energy_threshold = Config.SILENCE_THRESHOLD  # Start with config threshold
        self.background_energy_history = []
        self.max_history_length = 100  # Number of frames to track for background noise

    def _calculate_energy(self, audio_chunk):
        """
        Calculate the energy (RMS) of an audio chunk.

        Args:
            audio_chunk: numpy array containing audio samples

        Returns:
            float: Energy value representing loudness of the chunk
        """
        if len(audio_chunk) == 0:
            return 0.0

        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        # Apply multiplier for better sensitivity
        return rms * 10.0

    def _update_background_noise_estimate(self, energy):
        """
        Update the background noise estimate based on recent energy readings.

        Args:
            energy: Current energy value
        """
        # Add current energy to history
        self.background_energy_history.append(energy)

        # Maintain history size
        if len(self.background_energy_history) > self.max_history_length:
            self.background_energy_history.pop(0)

        # Update threshold based on minimum energy in history
        if self.background_energy_history:
            min_energy = min(self.background_energy_history)
            avg_energy = np.mean(self.background_energy_history)

            # Use a combination of min and average to set threshold
            # This adapts to changing background noise levels
            self.energy_threshold = max(min_energy * 2, avg_energy * 1.2, Config.SILENCE_THRESHOLD)

    def is_voice_present(self, audio_chunk, update_threshold=True):
        """
        Detect if voice is present in the given audio chunk.

        Args:
            audio_chunk: numpy array containing audio samples
            update_threshold: Whether to update background noise estimate

        Returns:
            bool: True if voice activity detected, False otherwise
        """
        if len(audio_chunk) == 0:
            return False

        # Calculate energy of the chunk
        energy = self._calculate_energy(audio_chunk)

        # Update background noise estimate if requested
        if update_threshold:
            self._update_background_noise_estimate(energy)

        # Compare with threshold
        is_speech = energy > self.energy_threshold

        return is_speech

    def process_audio_stream(self, callback_func=None, duration=None):
        """
        Process audio stream in real-time and detect voice activity.

        Args:
            callback_func: Optional function to call when VAD result is available
                          Function signature: callback(is_voice_active, audio_chunk)
            duration: Duration to record in seconds (None for indefinite)

        Note: This method requires sounddevice to be installed separately.
        """
        try:
            import sounddevice as sd
        except ImportError:
            raise ImportError("sounddevice is required for real-time audio streaming. Install it with: pip install sounddevice")

        # Calculate number of frames to process if duration is specified
        total_frames = None
        if duration:
            total_frames = int((duration * self.sample_rate) / self.frame_size)

        # Start the audio stream
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=Config.CHANNELS,
            dtype='float32',
            blocksize=self.frame_size
        ) as stream:
            frame_count = 0
            while True:
                # Read a frame
                audio_data, overflowed = stream.read(self.frame_size)

                if overflowed:
                    print("Warning: Audio overflow in VAD")

                # Check for voice activity
                is_voice = self.is_voice_present(audio_data)

                # Call callback if provided
                if callback_func:
                    callback_func(is_voice, audio_data)

                # Yield the result
                yield (is_voice, audio_data)

                # Break if duration specified and reached
                frame_count += 1
                if total_frames and frame_count >= total_frames:
                    break

    def analyze_audio_file(self, audio_file_path):
        """
        Analyze a pre-recorded audio file for voice activity.

        Args:
            audio_file_path: Path to the audio file to analyze

        Returns:
            list: List of tuples (timestamp, is_voice_active) for each analyzed chunk
        """
        try:
            import soundfile as sf
        except ImportError:
            raise ImportError("soundfile is required for audio file analysis. Install it with: pip install soundfile")

        # Load the audio file
        audio_data, sr = sf.read(audio_file_path)

        # Resample if needed
        if sr != self.sample_rate:
            # Use librosa for resampling if available, otherwise use scipy
            try:
                import librosa
                audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
            except ImportError:
                # Fallback using scipy
                from scipy import signal
                num_samples = int(len(audio_data) * self.sample_rate / sr)
                audio_data = signal.resample(audio_data, num_samples)

        # Split audio into frames and analyze
        results = []
        timestamp = 0.0

        for i in range(0, len(audio_data), self.frame_size):
            chunk = audio_data[i:i + self.frame_size]

            # Pad chunk if it's smaller than frame size
            if len(chunk) < self.frame_size:
                padded_chunk = np.zeros(self.frame_size)
                padded_chunk[:len(chunk)] = chunk
                chunk = padded_chunk

            is_voice = self.is_voice_present(chunk)
            results.append((timestamp, is_voice))

            timestamp += self.frame_duration_ms / 1000.0

        return results


def simple_vad_check(audio_chunk, sample_rate=None):
    """
    Standalone function to perform simple VAD on an audio chunk.

    Args:
        audio_chunk: numpy array containing audio samples
        sample_rate: Sample rate of the audio (optional)

    Returns:
        bool: True if voice activity detected, False otherwise
    """
    vad = VoiceActivityDetector(sample_rate=sample_rate)
    return vad.is_voice_present(audio_chunk)


# Example usage
if __name__ == "__main__":
    print("Testing Voice Activity Detector...")

    # Create a simple test
    vad = VoiceActivityDetector()

    # Simulate some test data
    test_silent = np.random.normal(0, 0.01, 480)  # Silent audio (assuming 16kHz, 30ms)
    test_loud = np.random.normal(0, 0.5, 480)      # Loud audio (noise that should trigger VAD)

    print(f"Silent chunk detected as voice: {vad.is_voice_present(test_silent)}")
    print(f"Loud chunk detected as voice: {vad.is_voice_present(test_loud)}")

    print("VAD module test completed.")