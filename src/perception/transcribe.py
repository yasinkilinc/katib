import mlx_whisper
import os
import shutil
from datetime import datetime
from ..config import Config
from ..core.logger import get_logger

logger = get_logger("Transcriber")

class Transcriber:
    def __init__(self):
        # MLX Whisper loads model lazily or during transcribe.
        # We define the model path here.
        # Using the official MLX community converted model for 'turbo'
        self.model_path = "mlx-community/whisper-turbo"
        
        # Audio artifacts directory for debugging
        self.artifacts_dir = "data/audio_artifacts"
        os.makedirs(self.artifacts_dir, exist_ok=True)
        
        logger.info(f"MLX-Whisper initialized. Model '{self.model_path}' will be loaded on demand (GPU/Metal).")

    def transcribe(self, audio_file_path: str) -> str:
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return ""
        
        logger.info(f"Transcribing {audio_file_path} with MLX (Metal)...")
        
        try:
            # MLX Whisper direct API
            result = mlx_whisper.transcribe(
                audio_file_path, 
                path_or_hf_repo=self.model_path,
                language='tr'
            )
            text = result["text"].strip()
            
            # Save audio artifact with timestamp for debugging
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            artifact_path = os.path.join(self.artifacts_dir, f"{timestamp}.wav")
            shutil.copy(audio_file_path, artifact_path)
            
            # Log detailed transcription info
            logger.info(f"Transcribed: '{text}'")
            logger.info(f"Audio saved to: {artifact_path}")
            
            # Log to console for immediate feedback
            print(f"[*] Transcribed: '{text}'")
            
            return text
        except Exception as e:
            logger.error(f"MLX Transcription Error: {e}", exc_info=True)
            print(f"[!] MLX Transcription Error: {e}")
            return ""
