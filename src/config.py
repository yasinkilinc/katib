import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Local LLM Settings (Ollama)
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b") # Switch to faster model
    
    # Whisper Settings
    WHISPER_MODEL_SIZE = "turbo" 
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(BASE_DIR)
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
    LOGS_DIR = os.path.join(DATA_DIR, "logs")
    
    # Audio Settings
    SAMPLE_RATE = 16000
    CHANNELS = 1
    CHUNK_DURATION_MS = 100 # Increased for smoother metrics
    SILENCE_THRESHOLD = 20.0 # Increased to ignore background noise (was 10.0)

    # Wake Word Settings
    WAKE_WORD_ENABLED = os.getenv("WAKE_WORD_ENABLED", "false").lower() == "true"
    WAKE_WORDS = os.getenv("WAKE_WORDS", "hey computer,computer").split(",")
    WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", "0.7"))

    # Safety
    REQUIRE_CONFIRMATION_THRESHOLD = "high"
    
    # Execution Mode
    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
    
    @staticmethod
    def ensure_dirs():
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)

Config.ensure_dirs()
