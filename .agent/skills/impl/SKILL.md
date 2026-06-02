## When to use this skill

- Use this skill when:
    - Kullanıcı yeni bir özellik, hata düzeltmesi veya kod değişikliği istediğinde ve uygulama öncesinde yapılandırılmış bir yaklaşım gerektiğinde.
- This is helpful for:
    - Karmaşık görevleri yönetilebilir adımlara bölmek.
    - Mimari uyumu sağlamak.
    - Kodlamadan önce tüm kısıtlamaların (dil yerelleştirmesi gibi) karşılandığını doğrulamak.

## How to use it

1.  **Bağlam ve Gereksinimleri Analiz Et**:
    -   Kullanıcının isteğini, mevcut kod tabanı durumunu ve aktif dosyaları incele.
    -   Temel hedefi, gerekli dosya değişikliklerini ve potansiyel riskleri belirle.
    -   **Kısıtlama**: Kullanıcı dil tercihi (örneğin "Bütün planlar Türkçe olsun") belirttiyse, çıktı içeriği için buna kesinlikle uy.

2.  **Plan Yapısını Tasarla**:
    -   Mantıksal akış oluştur: `Analiz` -> `Önerilen Değişiklikler` -> `Doğrulama Stratejisi`.
    -   Tonun profesyonel ve teknik olduğundan emin ol.

3.  **İçeriği Oluştur**:
    -   **Hedef Tanımı (Goal)**: Ne başarılacağını kısaca belirt.
    -   **Bileşen Dağılımı**: Değiştirilecek (`[MODIFY]`), oluşturulacak (`[NEW]`) veya silinecek (`[DELETE]`) dosyaları listele.
    -   **Detaylı Adımlar**: Her dosya için gerekli spesifik mantık değişikliklerini, fonksiyon imzalarını veya sınıf modifikasyonlarını açıkla.
    -   **Doğrulama**: Uygulamanın başarısını doğrulamak için kesin adımları (komutlar, testler veya manuel kontroller) tanımla.

4.  **Kısıtlamalara Göre Gözden Geçir**:
    -   Planda *hiçbir* uygulama kodu yazılmadığını (sadece açıklamalar/dokümantasyon) doğrula.
    -   Çıktı dilinin kullanıcının katı gereksinimine (Türkçe) uyduğunu doğrula.

5.  **Planı Çıktı Olarak Ver**:
    -   Nihai planı Markdown formatında net bir şekilde sun.

--------------------------------------------------
SKILL CONTEXT
--------------------------------------------------
Skill name: impl

Skill purpose:
 Yazılım geliştirme görevleri için kapsamlı, sağlam ve dile özgü (Türkçe) bir uygulama planı oluşturmak. Bu, kod yazılmadan önce önerilen değişikliklerin iyi anlaşıldığından, mimari açıdan sağlam olduğundan ve kullanıcının çalışma ortamıyla kültürel/dilsel olarak uyumlu olduğundan emin olmayı sağlar.

Environment:
 Kod tabanı analizi (salt okunur), Markdown belgesi oluşturma.

Constraints:
-   **Kesin Dil Zorunluluğu**: Çıktı planı MUTLAKA Türkçe yazılmalıdır ("Her zaman Türkçe", "Hazırlanan bütün planlar Türkçe olsun").
-   **Doğrudan Uygulama Yok**: Plan içinde gerçek kod mantığını yazma; amacı ve yapıyı tarif et.
-   **Deterministik Çıktı**: Planın yapısı her zaman tanımlanmış bölümleri takip etmelidir.

--------------------------------------------------
OUTPUT REQUIREMENTS
--------------------------------------------------
-   Çıktı geçerli bir Markdown belgesi olmalıdır.
-   İçerik %100 Türkçe olmalıdır.
-   Yapı şunları içermelidir: `Hedef (Goal)`, `Yapılacak Değişiklikler (Changes)`, `Doğrulama Planı (Verification)`.
-   Net dosya adları ve yolları kullan.
-   "Kullanıcı İncelemesi Gerekli" (User Review Required) bölümünü SADECE kırıcı değişiklikler (breaking changes) varsa ekle.
