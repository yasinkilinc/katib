import os
import torch
import numpy as np
from speechbrain.pretrained import EncoderClassifier
from speechbrain.dataio.util import read_audio
import warnings

# Suppress torchaudio/speechbrain warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")
warnings.filterwarnings("ignore", category=FutureWarning)

class WakeWordDetector:
    def __init__(self, wake_words=["hey computer", "computer"], threshold=0.7):
        """
        Initializes the Wake Word Detection model (SpeechBrain).
        Forces CPU usage to avoid MPS sparse tensor crashes on macOS.
        """
        self.wake_words = wake_words
        self.threshold = threshold

        # Determine device - Force CPU for PyTorch stability with SpeechBrain
        self.device = "cpu"
        print(f"[*] Initializing Wake Word Detection on {self.device.upper()}...")

        try:
            # Load pre-trained keyword spotter model
            self.classifier = EncoderClassifier.from_hparams(
                source="speechbrain/keyword-spotting-transformer-mobilenetv1-yesno",
                savedir="data/models/keyword_spotting",
                run_opts={"device": self.device}
            )
            print("[*] Wake word detection model loaded successfully.")

        except Exception as e:
            print(f"[!] Wake Word Model Init Error: {e}")
            self.classifier = None

    def detect_wake_word(self, audio_file_path: str) -> bool:
        """
        Detects if any of the wake words are present in the audio file.
        """
        if not self.classifier:
            return False

        if not os.path.exists(audio_file_path):
            return False

        try:
            # Load audio
            waveform = read_audio(audio_file_path)

            # Perform keyword spotting
            outs = self.classifier.classify_batch(waveform)
            predicted_words = outs[0][0]  # Extract predicted words

            # Check if any of the predicted words match our wake words
            for word in predicted_words:
                word_lower = word.lower()
                for wake_word in self.wake_words:
                    if wake_word.lower() in word_lower:
                        print(f"[*] Wake word '{wake_word}' detected!")
                        return True

            print(f"[*] No wake word detected. Predicted: {predicted_words}")
            return False

        except Exception as e:
            print(f"[!] Wake Word Detection Error: {e}")
            return False

    def is_wake_word_present(self, audio_data) -> bool:
        """
        Alternative method to check if wake word is present using raw audio data.
        This is useful for real-time detection scenarios.
        """
        if not self.classifier:
            return False

        try:
            # Convert numpy array to tensor if needed
            if isinstance(audio_data, np.ndarray):
                # Ensure proper shape and type
                if len(audio_data.shape) == 1:
                    audio_tensor = torch.tensor(audio_data, dtype=torch.float32).unsqueeze(0)
                else:
                    audio_tensor = torch.tensor(audio_data, dtype=torch.float32)
            else:
                audio_tensor = audio_data

            # Move to device
            audio_tensor = audio_tensor.to(self.device)

            # Perform keyword spotting
            outs = self.classifier.classify_batch(audio_tensor)
            predicted_words = outs[0][0]  # Extract predicted words

            # Check if any of the predicted words match our wake words
            for word in predicted_words:
                word_lower = word.lower()
                for wake_word in self.wake_words:
                    if wake_word.lower() in word_lower:
                        print(f"[*] Wake word '{wake_word}' detected!")
                        return True

            print(f"[*] No wake word detected in real-time audio. Predicted: {predicted_words}")
            return False

        except Exception as e:
            print(f"[!] Wake Word Detection Error (real-time): {e}")
            return False