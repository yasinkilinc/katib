import sounddevice as sd
import numpy as np
import wave
import os
import time
from .vad import VoiceActivityDetector
from .wake_word import WakeWordDetector
from ..config import Config

class AudioListener:
    def __init__(self):
        self.sample_rate = Config.SAMPLE_RATE
        self.channels = Config.CHANNELS
        self.threshold = Config.SILENCE_THRESHOLD
        self.chunk_duration = Config.CHUNK_DURATION_MS / 1000.0
        self.chunk_size = int(self.sample_rate * self.chunk_duration)

        # Ring buffer to prevent cutting off start of sentence
        # 1.0 second buffer = 1.0 / chunk_duration chunks
        self.buffer_len = int(1.0 / self.chunk_duration)
        if self.buffer_len < 1: self.buffer_len = 1

        # Initialize the Voice Activity Detector
        self.vad = VoiceActivityDetector(sample_rate=self.sample_rate)

        # Initialize the Wake Word Detector if enabled
        if Config.WAKE_WORD_ENABLED:
            self.wake_word_detector = WakeWordDetector(
                wake_words=Config.WAKE_WORDS,
                threshold=Config.WAKE_WORD_THRESHOLD
            )
        else:
            self.wake_word_detector = None

    def listen_and_record(self, output_filename="input.wav", max_silence_seconds=4.0, detect_wake_word=False) -> bool:
        """
        Listens for speech using Voice Activity Detection (VAD) and includes 1s of pre-speech audio.
        Optionally detects wake word before recording if detect_wake_word is True.
        """
        import collections
        print("[*] Listening...")

        audio_buffer = [] # Main recording buffer
        pre_speech_buffer = collections.deque(maxlen=self.buffer_len) # Rolling buffer

        is_speaking = False
        silence_start = None

        # If wake word detection is enabled and requested, wait for wake word first
        if detect_wake_word and self.wake_word_detector:
            print(f"[*] Waiting for wake word: {', '.join(Config.WAKE_WORDS)}...")
            return self._listen_for_wake_word_then_record(output_filename, max_silence_seconds)

        # Normal listening flow
        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='float32') as stream:
            while True:
                data, overflowed = stream.read(self.chunk_size)
                if overflowed:
                    print("Warning: Audio overflow")

                # Use Voice Activity Detector instead of basic threshold
                vad_detected = self.vad.is_voice_present(data.flatten())

                # Calculate volume for visual feedback (keeping the old UI element)
                volume = np.linalg.norm(data) * 10

                # Visual Feedback
                bars = "#" * int(volume / 2)
                print(f"\r[*] Volume: {volume:.2f} | VAD: {'YES' if vad_detected else 'NO'} | {bars:20s}", end="", flush=True)

                if vad_detected:
                    if not is_speaking:
                        print("\n[*] Speech detected! Recording...", end="", flush=True)
                        is_speaking = True
                        # Dump pre-speech buffer into main buffer
                        audio_buffer.extend(list(pre_speech_buffer))
                        pre_speech_buffer.clear()

                    silence_start = None
                    audio_buffer.append(data)

                elif is_speaking:
                    audio_buffer.append(data)
                    if silence_start is None:
                        silence_start = time.time()

                    if time.time() - silence_start > max_silence_seconds:
                        print("\n[*] Silence detected. Processing...")
                        break
                else:
                    # Still waiting for speech, keep filling ring buffer
                    pre_speech_buffer.append(data)

                # Max Duration Timeout (60s)
                if is_speaking and (len(audio_buffer) * self.chunk_duration > 60.0):
                     print("\n[*] Max recording duration reached (60s). Processing...")
                     break

        if not audio_buffer:
            return False

        # Save to file
        full_audio = np.concatenate(audio_buffer, axis=0)
        # Normalize
        full_audio = full_audio / np.max(np.abs(full_audio))

        # Write wav
        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(self.sample_rate)
            # Convert float32 to int16
            audio_int16 = (full_audio * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())

        return True

    def _listen_for_wake_word_then_record(self, output_filename="input.wav", max_silence_seconds=4.0):
        """
        Listen for wake word first, then record after wake word is detected.
        """
        import collections
        print(f"[*] Listening for wake word: {', '.join(Config.WAKE_WORDS)}...")

        # Temporary buffer to hold audio while listening for wake word
        temp_buffer = []
        pre_wake_buffer = collections.deque(maxlen=self.buffer_len) # Rolling buffer

        wake_word_detected = False
        is_speaking = False
        silence_start = None

        # Record temporary audio for wake word detection
        temp_audio_path = "temp_wake_detection.wav"

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='float32') as stream:
            while not wake_word_detected:
                data, overflowed = stream.read(self.chunk_size)
                if overflowed:
                    print("Warning: Audio overflow")

                # Use Voice Activity Detector to check for activity
                vad_detected = self.vad.is_voice_present(data.flatten())

                # Calculate volume for visual feedback
                volume = np.linalg.norm(data) * 10

                # Visual Feedback
                bars = "#" * int(volume / 2)
                print(f"\r[*] Volume: {volume:.2f} | VAD: {'YES' if vad_detected else 'NO'} | {bars:20s}", end="", flush=True)

                # Add to temporary buffer for potential wake word analysis
                temp_buffer.append(data)

                # Keep ring buffer updated
                pre_wake_buffer.append(data)

                # Limit temp buffer size to avoid memory issues (about 5 seconds worth)
                if len(temp_buffer) > int(5.0 / self.chunk_duration):
                    temp_buffer.pop(0)

                # Periodically check for wake word if there's some audio
                if len(temp_buffer) > int(0.5 / self.chunk_duration):  # At least 0.5s of audio
                    # Save temp buffer to file for wake word detection
                    temp_audio = np.concatenate(temp_buffer[-int(1.0 / self.chunk_duration):], axis=0)  # Last 1 second
                    temp_audio = temp_audio / np.max(np.abs(temp_audio)) if np.max(np.abs(temp_audio)) != 0 else temp_audio

                    with wave.open(temp_audio_path, 'wb') as wf:
                        wf.setnchannels(self.channels)
                        wf.setsampwidth(2)  # 16-bit
                        wf.setframerate(self.sample_rate)
                        # Convert float32 to int16
                        audio_int16 = (temp_audio * 32767).astype(np.int16)
                        wf.writeframes(audio_int16.tobytes())

                    # Check for wake word in the temporary audio
                    if self.wake_word_detector.detect_wake_word(temp_audio_path):
                        print(f"\n[✓] Wake word detected! Starting conversation...")
                        wake_word_detected = True

                        # Now start the normal recording process
                        audio_buffer = []  # Main recording buffer
                        # Include the last bit of audio that contained the wake word
                        audio_buffer.extend(temp_buffer[-int(0.5 / self.chunk_duration):])  # Last 0.5s
                        is_speaking = True
                        silence_start = None

                        # Continue recording until silence
                        while True:
                            data, overflowed = stream.read(self.chunk_size)
                            if overflowed:
                                print("Warning: Audio overflow")

                            vad_detected = self.vad.is_voice_present(data.flatten())

                            volume = np.linalg.norm(data) * 10
                            bars = "#" * int(volume / 2)
                            print(f"\r[*] Volume: {volume:.2f} | VAD: {'YES' if vad_detected else 'NO'} | {bars:20s}", end="", flush=True)

                            if vad_detected:
                                if not is_speaking:
                                    print("\n[*] Speech detected! Recording...", end="", flush=True)
                                    is_speaking = True

                                silence_start = None
                                audio_buffer.append(data)

                            elif is_speaking:
                                audio_buffer.append(data)
                                if silence_start is None:
                                    silence_start = time.time()

                                if time.time() - silence_start > max_silence_seconds:
                                    print("\n[*] Silence detected. Processing...")
                                    break

                            # Max Duration Timeout (60s)
                            if is_speaking and (len(audio_buffer) * self.chunk_duration > 60.0):
                                 print("\n[*] Max recording duration reached (60s). Processing...")
                                 break

                        # Save to file
                        if audio_buffer:
                            full_audio = np.concatenate(audio_buffer, axis=0)
                            # Normalize
                            full_audio = full_audio / np.max(np.abs(full_audio))

                            # Write wav
                            with wave.open(output_filename, 'wb') as wf:
                                wf.setnchannels(self.channels)
                                wf.setsampwidth(2) # 16-bit
                                wf.setframerate(self.sample_rate)
                                # Convert float32 to int16
                                audio_int16 = (full_audio * 32767).astype(np.int16)
                                wf.writeframes(audio_int16.tobytes())

                        # Clean up temp file
                        if os.path.exists(temp_audio_path):
                            os.remove(temp_audio_path)

                        return True
