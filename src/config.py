import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Available LLM Models with metadata
    LLM_MODELS = {
        "qwen-1.5b": {
            "name": "qwen2.5:1.5b",
            "url": "http://localhost:11434/api/generate",
            "speed": "fast",      # 10-15s
            "accuracy": "medium"  # ~70%
        },
        "llama-3b": {
            "name": "llama3.2:latest",
            "url": "http://localhost:11434/api/generate",
            "speed": "medium",    # 15-20s
            "accuracy": "high"    # ~85-90%
        },
        "llama-1b": {
            "name": "llama3.2:1b",
            "url": "http://localhost:11434/api/generate",
            "speed": "fast",      # 8-12s
            "accuracy": "low"     # ~60-70%
        },
        "llama-8b": {
            "name": "llama3:latest",
            "url": "http://localhost:11434/api/generate",
            "speed": "slow",      # 25-30s
            "accuracy": "very_high"  # ~95%+
        }
    }
    
    # Active Model Selection (change this line to switch models!)
    ACTIVE_LLM = os.getenv("ACTIVE_LLM", "llama-3b")
    
    # Dynamic LLM Settings
    OLLAMA_API_URL = LLM_MODELS[ACTIVE_LLM]["url"]
    OLLAMA_MODEL = LLM_MODELS[ACTIVE_LLM]["name"]
    
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
    CHUNK_DURATION_MS = 100
    SILENCE_THRESHOLD = 20.0
    
    # Safety
    REQUIRE_CONFIRMATION_THRESHOLD = "high"
    
    # Execution Mode
    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
    
    # TTS Feedback
    TTS_FEEDBACK_ENABLED = os.getenv("TTS_FEEDBACK", "true").lower() == "true"
    
    @staticmethod
    def ensure_dirs():
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)

Config.ensure_dirs()
