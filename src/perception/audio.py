import sounddevice as sd
import numpy as np
import wave
import os
import time
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

    def listen_and_record(self, output_filename="input.wav", max_silence_seconds=4.0) -> bool:
        """
        Listens for speech and includes 1s of pre-speech audio.
        """
        import collections
        print("[*] Listening...")
        
        audio_buffer = [] # Main recording buffer
        pre_speech_buffer = collections.deque(maxlen=self.buffer_len) # Rolling buffer
        
        is_speaking = False
        silence_start = None
        
        # Prepare stream
        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='float32') as stream:
            while True:
                data, overflowed = stream.read(self.chunk_size)
                if overflowed:
                    print("Warning: Audio overflow")
                
                volume = np.linalg.norm(data) * 10
                
                # Visual Feedback
                bars = "#" * int(volume / 2)
                print(f"\r[*] Volume: {volume:.2f} | {bars:20s}", end="", flush=True)

                if volume > self.threshold:
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
