import mlx_whisper
import os
from ..config import Config

class Transcriber:
    def __init__(self):
        # MLX Whisper loads model lazily or during transcribe.
        # We define the model path here.
        # Using the official MLX community converted model for 'turbo'
        self.model_path = "mlx-community/whisper-turbo" 
        print(f"[*] MLX-Whisper initialized. Model '{self.model_path}' will be loaded on demand (GPU/Metal).")

    def transcribe(self, audio_file_path: str) -> str:
        if not os.path.exists(audio_file_path):
            return ""
        
        print(f"[*] Transcribing {audio_file_path} with MLX (Metal)...")
        
        try:
            # MLX Whisper direct API
            result = mlx_whisper.transcribe(
                audio_file_path, 
                path_or_hf_repo=self.model_path,
                language='tr'
            )
            text = result["text"].strip()
            print(f"[*] Transcribed: '{text}'")
            return text
        except Exception as e:
            print(f"[!] MLX Transcription Error: {e}")
            return ""
