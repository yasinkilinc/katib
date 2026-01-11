# Katib

Katib, macOS üzerinde çalışan, sesle kontrol edilen ve kendi hatalarından öğrenen otonom bir yapay zeka ajanıdır.

## Kurulum

1. **Ollama Kurulumu:**
   Bilgisayarınızda [Ollama](https://ollama.com) kurulu olmalı ve bir model indirilmiş olmalıdır:
   ```bash
   ollama run mistral
   # veya
   ollama pull llama3
   ```

2. **FFmpeg Kurulumu:**
   Ses işleme için gereklidir:
   ```bash
   brew install ffmpeg
   ```

3. Başlatma Scriptini Çalıştırın:
   ```bash
   ./run.sh
   ```
   Bu script gerekli Python ortamını hazırlar ve programı başlatır.

## Özellikler
- **Yerel Zeka (Local LLM)**: İnternet gerekmez, verileriniz cihazda kalır.
- **Sesli Komut**: "Katib, Windsurf'ü aç ve yeni proje oluştur"
- **Otonom Eylem**: Klavye ve fare kullanarak gerçek uygulamaları yönetir.

