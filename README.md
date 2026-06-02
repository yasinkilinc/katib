# Katib (Kâtip)

> **Yerel, Otonom ve Ses Kontrollü Yapay Zeka Asistanı**

Katib, macOS işletim sistemi için geliştirilmiş, tamamen cihaz üzerinde çalışan (offline-first), kullanıcısının sesini tanıyan ve verilen komutları yerine getiren otonom bir AI ajanıdır.

## 🚀 Özellikler

*   **Gizlilik Odaklı & Yerel:** Tüm işlemler (Ses tanıma, LLM, Planlama) cihazınızda gerçekleşir. Verileriniz buluta gitmez.
*   **Ses Doğrulama (Speaker Verification):** Sadece *sizin* sesinize yanıt verir. Başka biri konuştuğunda komutları reddeder.
*   **Otonom Planlama:** Karmaşık istekleri anlar, adım adım planlar ve uygular.
    *   *Örn:* "Katib, Safari'yi aç, YouTube'a git ve Tarkan şarkıları çal."
*   **Geniş Yetenek Yelpazesi:**
    *   Uygulama Yönetimi (Açma, Kapama, Odaklanma)
    *   Web Gezintisi ve Arama
    *   Sistem Kontrolü (Ses, Ekran Kilidi vb.)
    *   TTS (Sesli Geri Bildirim)

## 🛠 Kurulum

### Gereksinimler
*   MacOS (Apple Silicon işlemci önerilir)
*   Python 3.11+
*   [Ollama](https://ollama.com)
*   FFmpeg

### Adım Adım Kurulum

1.  **Projeyi Klonlayın:**
    ```bash
    git clone <repo-url>
    cd katib
    ```

2.  **Sistem Bağımlılıklarını Yükleyin:**
    Ses işleme kütüphaneleri için gereklidir.
    ```bash
    brew install ffmpeg portaudio
    ```

3.  **Ollama Modelini Hazırlayın:**
    Katib, `qwen2.5:1.5b` modelini kullanır. Terminalden şunu çalıştırın:
    ```bash
    ollama pull qwen2.5:1.5b
    ```

4.  **Konfigürasyonu Başlatın:**
    `run.sh` scripti gerekli sanal ortamı kurar ve bağımlılıkları yükler.
    ```bash
    ./run.sh
    ```
    *(İlk çalıştırmada bağımlılıkların yüklenmesi biraz zaman alabilir.)*

## 🎙 Kullanım

### 1. Ses Profilinizi Oluşturun (İlk Kez)
Katib'in sizi tanıması için sesinizi kaydetmeniz gerekir. Bu işlem tek seferliktir.
```bash
python3 enroll.py
```
Ekranda çıkan talimatları izleyerek yaklaşık 10 saniye boyunca doğal bir şekilde konuşun.

### 2. Katib'i Başlatın
```bash
./run.sh
```

### 3. Komut Verin
Uygulama "Listening" moduna geçtiğinde konuşmaya başlayabilirsiniz:
*   *"Safari'yi aç ve Google'a git."*
*   *"Sesi %50 yap."*
*   *"Bana bir şaka yap."* (Not: Henüz sadece belirli yetenekleri var, sohbet yeteneği sınırlı olabilir)
*   *"Bilgisayarı kilitle."*

## 📂 Proje Yapısı

Teknik detaylar ve AI ajanları için proje yapısı hakkında bilgi almak isterseniz `AI_HANDOVER.md` dosyasına bakabilirsiniz.

*   `src/`: Kaynak kodlar
*   `data/`: Ses profilleri
*   `Modelfile`: LLM sistem promptu
*   `policies/`: Güvenlik politikaları

## ⚠️ Lisans
[MIT License](LICENSE)
