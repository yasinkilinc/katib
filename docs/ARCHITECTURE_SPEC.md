# KATİB NİHAİ MİMARİ SPESİFİKASYONU

## 1. Üst Düzey Dizin Yapısı

```text
katib/
├── main.py                     # Giriş noktası (Orkestratör)
├── config.py                   # Global konfigürasyon
├── run.sh                      # Başlatma betiği
├── requirements.txt
└── src/
    ├── core/                   # BEYİN: Mantık, Durum, Kontrol
    │   ├── __init__.py
    │   ├── intent.py           # Niyet sınıflandırma (Intent - LLM)
    │   ├── planner.py          # Çok adımlı planlama (Reasoning - LLM)
    │   ├── memory.py           # Kısa ve Uzun vadeli hafıza
    │   ├── policy.py           # Politika ve İzin Seviyeleri (Policy Layer)
    │   ├── safety.py           # Güvenlik kontrolleri
    │   └── llm.py              # LLM Sağlayıcı Soyutlaması
    │
    ├── perception/             # DUYULAR: Girdi İşleme
    │   ├── __init__.py
    │   ├── audio.py            # Mikrofon I/O
    │   ├── speaker.py          # Kimlik Doğrulama
    │   └── transcribe.py       # Sesten Yazıya (Whisper)
    │
    ├── mcp/                    # SİNİR SİSTEMİ: Araç Protokolü
    │   ├── __init__.py
    │   ├── resolver.py         # Yetenek Dağıtıcı (Dispatcher)
    │   ├── registry.py         # Araç Kayıt Defteri
    │   └── capabilities.py     # Veri Transfer Objeleri
    │
    └── executors/              # ELLER: Eylem Uygulama
        ├── __init__.py
        ├── base_executor.py    # Soyut Temel Sınıf
        ├── macos_executor.py   # OS Kontrolü (AppleScript/PyAutoGUI)
        ├── terminal_executor.py# Shell etkileşimi
        ├── windsurf_executor.py# IDE entegrasyonu
        └── interpreter.py      # Güvenli Python Yorumlayıcısı (Salt Okunur)
```

## 2. Modül Sorumlulukları

| Modül | Sorumluluk | Temel Kısıtlama |
|:---|:---|:---|
| **main.py** | **Orkestratör**: Sonsuz döngüyü çalıştırır. Algı → Çekirdek → MCP akışını yönetir. | Durumsuz (Stateless) olmalıdır; durum Memory'de tutulur. |
| **src/perception** | **Girdi Normalizasyonu**: Ham sinyalleri (ses) temiz metne/veriye dönüştürür. | Geçersiz veya doğrulanmamış girdileri erkenden reddetmelidir. |
| **src/core/intent** | **Anlama**: Kullanıcının Hedefini (Goal) ve Varlıklarını (Entities) çıkarır. | Yan etkisi olmamalıdır. Saf sınıflandırma yapar. |
| **src/core/planner** | **Muhakeme**: Hedefi alır, Yönlendirilmiş Acyclic Graph (DAG) şeklinde adımlara (Steps) dönüştürür. | SADECE kayıtlı yetenekleri kullanmalıdır. Şema farkındalığı şarttır. |
| **src/core/policy** | **Yönetişim (Governance)**: Her adımı yürütmeden önce yetkilendirir. Onay gereksinimini belirler. | "Güvenlik" için tek doğruluk kaynağıdır. Yüksek riskli kurallar kodlanmıştır. |
| **src/core/memory** | **Kalıcılık**: Konuşma geçmişini, yürütme sonuçlarını ve öğrenilen tercihleri saklar. | Yürütme denemesinden (başarı veya hata) SONRA yazılmalıdır. |
| **src/mcp** | **Protokol**: Araçları bulmak ve çağırmak için standart arayüzdür. | Aracın *ne* yaptığından bağımsızdır. Serileştirmeyi yönetir. |
| **src/executors** | **Uygulama**: OS/API'ler ile arayüz oluşturarak atomik eylemleri gerçekleştirir. | Atomik, izole ve mümkünse idempotent (tekrar edilebilir) olmalıdır. |

## 3. Nihai Orkestrasyon Akışı

1.  **Duy (Sense)**:
    *   `AudioListener` standart `.wav` dosyası yakalar.
    *   `SpeakerVerifier` kullanıcıyı doğrular (bloklayan işlem).
    *   `Transcriber` sesi metne çevirir (Audio → Text).
2.  **Düşün (Think)**:
    *   `IntentEngine` metni normalize eder ve `Goal` (Hedef) çıkarır.
    *   `Planner` şunları alır: `Goal` + `MemoryContext`.
    *   `Planner` bir `Plan` üretir (Adımlar Listesi).
3.  **Denetle (Audit)**:
    *   Her bir `Step` için:
        *   `Resolver`, `PolicyEngine`'e `Step.action` ile sorar.
        *   `PolicyEngine` bir `Permission` (İZİN | ONAY_GEREKLİ | RED) döner.
        *   Eğer `ONAY_GEREKLİ`: Kullanıcıya sorulur. Reddedilirse plan iptal edilir.
        *   Eğer `RED`: Adım otomatik başarısız olur, `FailureHandler` tetiklenir.
4.  **Eyleme Geç (Act)**:
    *   `Resolver`, `Step.action` için uygun `Executor`'ı bulur.
    *   `Executor`, `execute(params)` fonksiyonunu çalıştırır.
    *   Sonuç (Başarı/Hata + Çıktı) döner.
5.  **Öğren (Learn)**:
    *   `MemoryEngine` şu üçlüyü kaydeder: `(Girdi, Plan, Sonuç)`.
    *   Hata durumunda: `MemoryEngine` gelecekteki düzeltmeler için bağlamı etiketler.

## 4. Nihai Politika Modeli

**Politika Seviyeleri:**

1.  **SEVİYE 0: SALT OKUNUR (Güvenli)**
    *   *Örnekler*: `web.search`, `interpreter.analyze`, `app.list_running`, `time.get`.
    *   *Kural*: **OTOMATİK YÜRÜT**.
2.  **SEVİYE 1: DÜŞÜK RİSK (Geri Alınabilir/Önemsiz)**
    *   *Örnekler*: `app.focus`, `system.volume`, `tts.speak`.
    *   *Kural*: **OTOMATİK YÜRÜT** ("Strict Mode" değilse).
3.  **SEVİYE 2: HASSAS (Durum Değişikliği)**
    *   *Örnekler*: `app.open`, `app.close`, `web.open_tab`.
    *   *Kural*: **BİLDİR** (Kısa bildirim/log göster) -> **OTOMATİK YÜRÜT**.
4.  **SEVİYE 3: YÜKSEK RİSK (Yıkıcı/Maliyetli)**
    *   *Örnekler*: `interpreter.run_shell`, `interpreter.run_python` (yazma), `system.lock`, `email.send`.
    *   *Kural*: **AÇIK ONAY GEREKTİR** (Bloklayan işlem).

**Eskalasyon Mantığı:**
*   Sezgisel otomatik yükseltme (örn. argüman "rm -rf" veya genel joker karakterler içeriyorsa, SEVİYE 3'e yükselt).
*   Kullanıcı geçersiz kılması: "[Süre] boyunca [Eylem] için her zaman izin ver" (Zaman sınırlı izin).

## 5. Yorumlayıcı Rolü ve Sınırları

**Interpreter Executor** (`interpreter_executor.py`), OS kontrolcüsü DEĞİL, genel bir hesaplama/analiz aracıdır.

*   **Rolü**: Hesaplama, Veri Ayrıştırma (Parsing), Metin İşleme, İnceleme.
*   **Sınırları**:
    *   **Ağ**: DEVRE DIŞI (açıkça `web` araçları kullanılmadıkça).
    *   **Dosya Sistemi**: Varsayılan olarak SALT OKUNUR. Yazma izni sadece `/tmp` veya özel sandbox alanına verilir.
    *   **Alt Süreçler (Subprocesses)**: ENGELLİ (Python mantığı içinde `subprocess.Popen`, `os.system` yok).
*   **İzin Verilen Kütüphaneler**: `math`, `json`, `datetime`, `re`, `random`.
*   **Yasaklı**: `socket`, `requests` (bunun için global araçları kullanın).

*Planner'ın eyleme geçmeden önce düşünmesini destekler, ancak OS etkileşimi için asla özelleşmiş `MacOSExecutor`'ın yerini almaz.*

## 6. Planlayıcı Sözleşmesi

*   **Girdi**:
    *   `UserCommand` (str - Kullanıcı Komutu)
    *   `ConversationHistory` (List[Dict] - Konuşma Geçmişi)
    *   `AvailableTools` (Schema - Mevcut Araçlar)
*   **Çıktı**:
    *   `Plan` objesi:
        *   `steps`: List[Step] (Adımlar Listesi)
        *   `reasoning`: String (Düşünce Zinciri özeti)
*   **Garantiler**:
    *   **Şema Uyumluluğu**: Her adım birebir kayıtlı bir MCP Yeteneği ile eşleşir.
    *   **Parametre Geçerliliği**: Parametreler `AvailableTools` içinde tanımlanan tiplerle kesinlikle eşleşir.
    *   **Doğrusallık**: Sıralı bir liste döner (DAG desteği v2'ye ertelendi).
    *   **Atomiklik**: "Birleşik" adımlar yoktur; görevleri atomik araç çağrılarına böler.

## 7. Yürütücü Sözleşmesi

Tüm Yürütücüler (Executors) `BaseExecutor` sınıfını uygulamalıdır.

*   **Metotlar**:
    *   `execute(action: str, params: dict) -> ExecutionResult`
    *   `validate(action: str, params: dict) -> bool` (Hızlı ön kontrol)
*   **Garantiler**:
    *   **Idempotency (Tekrarlanabilirlik)**: Safari zaten açıkken `open_app("Safari")` çağırmak başarılı bir "işlem yok" (no-op) durumudur.
    *   **Yapılandırılmış Çıktı**: `ExecutionResult(success: bool, data: Any, error: str)` döner. ASLA yakalanmamış hata fırlatmaz.
    *   **Zaman Aşımı**: Executor sarmalayıcısı tarafından zorlanan katı yürütme sınırı (varsayılan 30sn).
*   **Geri Alma (Rollback - Opsiyonel)**:
    *   Durum değiştiren eylemleri sergileyen yürütücüler, meta verilerinde bir `rollback_action` sunmalıdır (örn. `close_app`, `open_app` işlemini tersine çevirir), ancak otomasyon politikaya bağlıdır.

## 8. Hata Sınıflandırması

1.  **ERR_PERCEPTION**: Girdi anlaşılmaz veya gürültü.
    *   *Eylem*: Yoksay, hafızaya kaydetme.
2.  **ERR_INTENT_AMBIGUOUS**: Güven Skoru < Eşik Değer.
    *   *Eylem*: `UI_Fallback` tetikle (Netleştirme iste).
3.  **ERR_POLICY_REJECTION**: Kullanıcı reddetti veya Politika engelledi.
    *   *Eylem*: Planı iptal et, "İptal Edildi" durumunu kaydet.
4.  **ERR_EXECUTION_FAIL**: Araç çöktü veya başarısız döndü.
    *   *Eylem*:
        *   Mantık hatası ise: Planner parametreleri ayarlayarak 1 kez yeniden dener.
        *   Sistem hatası ise: Dur. Kullanıcıya raporla.
5.  **ERR_PLAN_INVALID**: LLM olmayan bir araç uydurdu (halüsinasyon).
    *   *Eylem*: LLM'e geri bildirim döngüsü ("Araç bulunamadı, mevcut araçlar: [...]").

## 9. Evrim Yolu

Bu mimari, **REFACTORING YAPMADAN** ölçeklenmeye izin verir:

*   **Görüntü Ekleme**: `src/perception/vision.py` oluşturun. Görüntü bağlamını `IntentEngine` içine enjekte edin. Çekirdek (Core) değişmez.
*   **Uzak Araçlar Ekleme**: `MCP Resolver` istekleri HTTP uç noktalarına proxyleyebilir. Core Planner, aracın yerel mi yoksa uzak mı olduğunu umursamaz.
*   **Daha Akıllı Hafıza**: `MemoryEngine` iç yapısını bir Vektör Veritabanı (Chroma/Qdrant) ile değiştirin. `record_execution()` arayüzü aynı kalır.
*   **Yeni Beceriler**: Yeni `Executor` alt sınıfı ekleyin, `main.py` içinde kaydedin. Planner, şema enjeksiyonu yoluyla bunu otomatik olarak keşfeder.
