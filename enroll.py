#!/usr/bin/env python3
import sys
import os
import sounddevice as sd
import soundfile as sf
import soundfile as sf
import numpy as np
import warnings
# Suppress annoying torchaudio/speechbrain warnings globally
warnings.filterwarnings("ignore", module="torchaudio")
warnings.filterwarnings("ignore", message=".*TorchCodec.*")
warnings.filterwarnings("ignore", category=UserWarning)
from src.perception.speaker import SpeakerVerifier

def record_audio(filename, duration=10, samplerate=16000):
    print(f"[*] Kayıt başlıyor... {duration} saniye boyunca normal bir tonda konuşun.")
    print("    (Örn: 'Benim adım Yasin, bu benim sesim ve Katib sistemini kullanmak istiyorum.')")
    
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    for i in range(duration):
        print(f"Recording... {duration-i}", end='\r')
        sd.sleep(1000)
        
    sd.wait()
    print("\n[*] Kayıt tamamlandı.")
    sf.write(filename, recording, samplerate)

def main():
    print("=== KATİB SES KAYIT (ENROLLMENT) ===")
    
    audio_file = "data/enrollment.wav"
    os.makedirs("data", exist_ok=True)
    
    record_audio(audio_file)
    
    print("[*] Profil oluşturuluyor...")
    verifier = SpeakerVerifier()
    if verifier.enroll_user(audio_file):
        print("\n[SUCCESS] Ses profiliniz başarıyla kaydedildi!")
        print("Artık Katib sadece sizin sesinize yanıt verecek.")
    else:
        print("\n[ERROR] Profil oluşturulamadı.")

if __name__ == "__main__":
    main()
