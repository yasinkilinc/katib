import os
import torch
import shutil
import warnings
# Suppress torchaudio/speechbrain warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")
warnings.filterwarnings("ignore", category=FutureWarning)
from speechbrain.inference.speaker import SpeakerRecognition

class SpeakerVerifier:
    def __init__(self, profile_path="data/user_profile.npy", threshold=0.25):
        """
        Initializes the Speaker Verification model (SpeechBrain).
        Forces CPU usage to avoid MPS sparse tensor crashes on macOS.
        """
        self.profile_path = profile_path
        self.threshold = threshold
        
        # Determine device - Force CPU for PyTorch stability with SpeechBrain
        self.device = "cpu"
        print(f"[*] Initializing Speaker Verification on {self.device.upper()}...")

        try:
             self.verification = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb", 
                savedir="data/models/spkrec",
                run_opts={"device": self.device}
            )
             
             # Cache profile if exists
             if os.path.exists(self.profile_path):
                 self.user_embedding = torch.load(self.profile_path, map_location=self.device)
                 print("[*] User profile loaded into memory.")
             else:
                 self.user_embedding = None

        except Exception as e:
            print(f"[!] Speaker Model Init Error: {e}")
            self.verification = None
            self.user_embedding = None

    def enroll_user(self, audio_file_path: str) -> bool:
        """
        Creates a new user profile from the provided audio file.
        """
        if not self.verification:
            return False

        print(f"[*] Enrolling user profile from {audio_file_path}...")
        try:
            # Generate embedding
            embedding = self.verification.encode_batch(
                self.verification.load_audio(audio_file_path).unsqueeze(0)
            )
            # Save embedding to disk
            torch.save(embedding, self.profile_path)
            # Update cache
            self.user_embedding = embedding
            print("[✓] User profile saved.")
            return True
        except Exception as e:
            print(f"[!] Enrollment Error: {e}")
            return False

    def verify(self, audio_file_path: str) -> bool:
        """
        Checks if the audio file matches the enrolled user.
        """
        if not os.path.exists(self.profile_path):
            return True

        if not self.verification:
            return True 

        # Reload if None (maybe created after init) but strictly typically valid
        if self.user_embedding is None:
             if os.path.exists(self.profile_path):
                 self.user_embedding = torch.load(self.profile_path, map_location=self.device)
             else:
                 return True # Fail open if no profile

        try:
            # Use cached embedding
            # Shape: [1, 1, 192]
            
            # Encode new audio into embedding
            # Shape: [1, 1, 192]
            new_waveform = self.verification.load_audio(audio_file_path).unsqueeze(0)
            new_embedding = self.verification.encode_batch(new_waveform)
            
            # Compute Cosine Similarity
            # Flatten to [1, 192] for simple comparison
            user_emb_flat = self.user_embedding.squeeze(1)
            new_emb_flat = new_embedding.squeeze(1)
            
            similarity = torch.nn.functional.cosine_similarity(user_emb_flat, new_emb_flat, dim=-1).item()
            
            print(f"[*] Voice Similarity: {similarity:.4f} (Threshold: {self.threshold})")
            
            if similarity >= self.threshold:
                return True
            else:
                return False

        except Exception as e:
            print(f"[!] Verification Error: {e}")
            # If verification crashes safely, we might fail open or closed. 
            # Given user wants security, let's return False but print clearly.
            return False
