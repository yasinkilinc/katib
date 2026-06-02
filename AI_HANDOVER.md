# Katib Projesi - AI Teknik Devir Dokümanı (AI Handover Document)

Bu doküman, Katib projesini devralacak veya üzerinde çalışacak bir Yapay Zeka (AI) asistanı için projenin mimarisini, bileşenlerini ve çalışma mantığını en ince detayına kadar açıklamak amacıyla hazırlanmıştır.

## 1. Proje Özeti
**Katib**, macOS işletim sistemi üzerinde çalışan, yerel LLM (Large Language Model) ve ses işleme teknolojilerini kullanan otonom bir yapay zeka ajanıdır. Kullanıcıdan sesli komut alır, bu komutu metne çevirir, bir plan oluşturur ve bu planı işletim sistemi üzerinde (uygulama açma, web araması, terminal komutu vb.) icra eder.

## 2. Teknoloji Yığını (Tech Stack)
*   **Dil:** Python 3.11+
*   **LLM (Akıl):** Ollama (Yerel) - Model: `qwen2.5:1.5b` (özelleştirilmiş `Modelfile` ile).
*   **Ses Tanıma (STT):** MLX-Whisper (Apple Silicon optimize) veya SpeechBrain.
*   **Ses Sentezi (TTS):** MacOS yerel `say` komutu veya SpeechBrain (henüz tam aktif değil).
*   **Ses Doğrulama:** SpeechBrain (Speaker Verification).
*   **Aksiyonlar:** `pyautogui` (Klavye/Fare), `applescript`, `subprocess`.
*   **Bağımlılık Yönetimi:** `requirements.txt` / `venv`.

## 3. Dizin ve Dosya Yapısı

```
katib/
├── run.sh                  # Uygulamayı başlatan ana script (Env kurulumu + Başlatma).
├── enroll.py               # Kullanıcı ses kaydı ve profil oluşturma scripti.
├── Modelfile               # Ollama için özelleştirilmiş model tanımları (System Prompt).
├── input.wav               # Geçici ses kayıt dosyası.
├── requirements.txt        # Python bağımlılıkları.
├── data/                   # Kullanıcı verileri (ses profilleri vb.).
├── logs/                   # Uygulama logları.
├── src/                    # Ana kaynak kodlar.
│   ├── main.py             # Uygulama giriş noktası (Loop döngüsü).
│   ├── config.py           # Konfigürasyon ayarları.
│   ├── core/               # Çekirdek mantık.
│   │   ├── planner.py      # LLM ile plan oluşturma (JSON çıktısı).
│   │   ├── memory.py       # Kısa/Uzun süreli hafıza ve loglama.
│   │   ├── policy.py       # Güvenlik ve kısıtlama kuralları.
│   │   └── logger.py       # Loglama altyapısı.
│   ├── perception/         # Algılama modülleri.
│   │   ├── audio.py        # Ses dinleme ve kaydetme (VAD - Voice Activity Detection).
│   │   ├── transcribe.py   # Sesi metne çevirme (Whisper).
│   │   └── speaker.py      # Konuşmacı doğrulama (Speaker Verification).
│   ├── mcp/                # Model Capability Protocol (Yetenekler).
│   │   ├── capabilities.py # Yetenek veri sınıfları.
│   │   └── resolver.py     # İsteği uygun executor'a yönlendirme.
│   └── executors/          # Eylemleri gerçekleştiren sınıflar.
│       ├── macos_executor.py       # MacOS özgü işlemler (App açma, TTS vb.).
│       ├── terminal_executor.py    # Terminal komutları.
│       ├── windsurf_executor.py    # Windsurf IDE kontrolü.
│       ├── interpreter_executor.py # Kod çalıştırma.
│       └── system_executor.py      # Sistem komutları (Kilit, Ses vb.).
```

## 4. Mimari İşleyiş (Main Loop)

`src/main.py` içerisindeki `start_loop` fonksiyonu sonsuz bir döngüde şu fazları işletir:

### Faz 1: Algılama (Sense)
1.  **Dinleme:** `AudioListener`, ortamı dinler ve konuşma algıladığında `input.wav` dosyasına kaydeder.
2.  **Doğrulama:** `SpeakerVerifier`, kaydedilen sesin yetkili kullanıcıya ait olup olmadığını `data/` altındaki profil ile karşılaştırır. Eşleşmezse işlem reddedilir.
3.  **Transkripsiyon:** `Transcriber`, sesi metne çevirir.

### Faz 2: Planlama (Plan)
1.  **LLM İsteği:** Metin, `Planner` aracılığıyla Ollama'ya gönderilir.
2.  **JSON Çıktısı:** Ollama (`Modelfile` promptuna göre), yapılacak işlemleri JSON formatında (Capability Request) döndürür.
    *   Örnek JSON: `{"capabilities": [{"name": "app.open", "parameters": {"app_name": "Safari"}}]}`
3.  **Parsinge:** JSON parse edilerek `steps` listesine dönüştürülür.

### Faz 3: Denetim ve Uygulama (Audit & Act)
1.  **Sıralı İşleme:** Her bir adım (`web.navigate`, `app.open` vb.) sırayla işlenir.
2.  **MCP Resolver:** `Resolver`, gelen isteği (`web.navigate`) ilgili Executor'a (`MacOSExecutor` vb.) yönlendirir.
3.  **Politika (Policy):** İşlem yapılmadan önce `PolicyEngine` (varsa) güvenlik kontrolü yapar.
4.  **İcra:** Executor işlemi gerçekleştirir (örn: `subprocess.run(["open", ...])`).

### Faz 4: Öğrenme (Learn)
1.  **Hafıza:** İşlem sonucu (başarılı/başarısız) `MemoryEngine`'e kaydedilir.
2.  **Geri Bildirim:** Kullanıcıya işlemin sonucu sesli olarak (TTS) bildirilir.

## 5. Önemli Bileşen Detayları

### Modelfile & Planner
*   **Model:** `qwen2.5:1.5b`. Hafif ve hızlı olduğu için seçilmiştir.
*   **System Prompt:** LLM'e sadece bir "Planlayıcı" olduğu ve OS detaylarını bilmediği, sadece belirli "Capabilities" (Yetenekler) listesinden JSON üretmesi gerektiği talimatı verilir.
*   **Capabilities List:**
    *   `web.search`, `web.navigate`
    *   `app.open`, `app.close`, `app.focus`
    *   `tts.speak`
    *   `system.volume`, `system.lock`, `system.hotkey`

### Executor Yapısı
Her Executor, belirli capability namespace'lerinden sorumludur.
*   **MacOSExecutor:** `app.*`, `tts.*`, `web.*` (Genellikle `osascript` veya `open` komutu kullanır).
*   **SystemExecutor:** `system.*` (Ses ayarı, kilit vb.).

## 6. Geliştirme ve Genişletme Rehberi

1.  **Yeni Yetenek Ekleme:**
    *   `Modelfile` içindeki `AVAILABLE CAPABILITIES` listesine ekle.
    *   İlgili `src/executors/ExampleExecutor.py` sınıfında bu yeteneği karşılayacak metodu yaz.
    *   `src/main.py` içinde `self.resolver.register_executor` ile yeni executor'ı veya metodu bağla.

2.  **Model Değiştirme:**
    *   `Modelfile` içindeki `FROM` satırını değiştir.
    *   `ollama pull <yeni-model>` komutunu çalıştır.

3.  **Sorun Giderme:**
    *   Loglar `logs/katib.log` dosyasında tutulur.
    *   `logs/` dizini yoksa oluşturulmalıdır.

## 7. Kurulum Notları
*   Proje ilk çalıştırıldığında `./run.sh` scripti otomatik olarak `.venv` oluşturur ve `requirements.txt` yükler.
*   FFmpeg (ses işleme için) sistemde kurulu olmalıdır (`brew install ffmpeg`).
*   İlk kullanımda `enroll.py` çalıştırılarak ses profili oluşturulmalıdır.
