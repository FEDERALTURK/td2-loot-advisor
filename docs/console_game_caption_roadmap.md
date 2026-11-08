# Konsol Oyunları İçin Canlı Türkçe Çeviri/Altyazı — Araştırma ve Yol Haritası

## 1. Araştırma: "Game Caption" tarzı uygulamalar yapısal olarak nasıl çalışıyor?

Bu bölüm, piyasadaki benzer ürünlerin mimarisini özetler (kaynaklar sonda). Hepsi aynı 3 bileşenden
kuruludur, sadece ilk adımda (girdi) farklılaşırlar:

```
[GİRDİ]  →  [TANIMA/OKUMA]  →  [ÇEVİRİ]  →  [GÖSTERİM]
```

### 1.1 Windows 11 "Live Captions" (Microsoft, OS seviyesi)
- **Girdi:** Sistem sesi (WASAPI loopback) — hangi uygulama çalıyorsa onu yakalar, oyuna özgü bir şey yapmaz.
- **Tanıma:** Cihaz üstü (on-device) konuşma tanıma modeli — bulut gerekmez, gecikme düşük.
- **Çeviri:** Gerçek zamanlı çeviri **44+ dilden → yalnızca İngilizce'ye**. Türkçe hedef dil olarak
  **desteklenmiyor** (bu özelliğin bu haliyle bize doğrudan faydası yok — kaynak dil listesine Türkçe'nin
  girip girmediği değil, hedefin İngilizce'yle sınırlı olması önemli).
- **Gösterim:** Ekranın altında/üstünde sabit bir altyazı çubuğu (OS overlay, pencere bağımsız).
- **Önemli not:** Bu, konsol sesini DEĞİL, Windows'un kendi ses çıkışını dinler. Konsol ayrı bir cihaz
  olduğu için bu özellik konsollarda hiç çalışmaz.

### 1.2 CaptionsRush (Overwolf uygulaması, "Live Captions, Live Translation, for Every Game")
- **Girdi:** 4 modu var — Discord Bot (sesli sohbeti dinler), Mikrofon, Sistem Sesi, veya Process-bazlı (tek
  bir .exe'nin ses çıkışını hedefler). Ayrıca "Audio Cue Tags" ile ayak sesi/silah sesi gibi oyun içi sesleri
  de ayrı tanıyor.
  - **Bu kesinlikle hedefimizin DIŞI olan kısmı:** sayfası açıkça **"This app is made for Desktop gaming
    only"** diyor — konsol desteği yok.
- **Tanıma:** Konuşma tanıma "öncelikle cihaz üstü" çalışıyor.
  - Büyük metin/alıntı: *"primarily on-device"*.
- **Çeviri:** Ücretli katmanda "dozens of languages" arası çeviri — hangi diller tam liste değil, incelenmedi.
- **Platform:** Overwolf (Electron tabanlı, ~214 MB) — yani PC'de arka planda çalışan bir overlay uygulaması,
  sistem/process sesini dinliyor, görsel OCR YAPMIYOR (ses tabanlı).
- **Sonuç:** Bizim ihtiyacımıza en yakın ÜRÜN ama mimarisi (ses tabanlı, sadece PC process'i dinleme) bizim
  konsol senaryomuza doğrudan uygulanamaz — çünkü konsol sesi PC'nin process ses çıkışında yok.

### 1.3 Ekran/OCR tabanlı oyun çevirmenleri (Steam'deki "in-game translation overlay" araçları, Subtify vb.)
- **Girdi:** Ekran görüntüsü (screen capture), belirli bir bölge veya tam ekran.
- **Tanıma:** OCR (metin/altyazı okuma) — konuşma tanıma değil, ekrandaki YAZIYI okur.
- **Çeviri:** Bulut (Google/DeepL) veya yerel model.
- **Gösterim:** Orijinal metnin üstüne/yanına overlay kutusu.
- **Bizim projemizle örtüşme:** **TD2 Loot Advisor zaten tam olarak bu mimariye sahip** — `ocr_backend.py`
  (RapidOCR/Tesseract), `livetranslate.py` (OPUS-MT yerel EN→TR + bulut motor seçenekleri), `overlay.py` /
  `trscreen.py` (yerinde veya köşe overlay gösterimi). Yani OCR+çeviri+overlay "motoru" sıfırdan
  yazılmayacak — zaten var, ileride sadece GİRDİ kaynağını değiştireceğiz.

### 1.4 Xbox'ın kendi resmi "Game Caption" API'si (XClosedCaption / XAccessibility)
Kullanıcının "Game Caption uygulaması tarzında olacak" talebi üzerine ayrıca araştırıldı: Xbox'ta
**gerçekten "Game Caption" adında resmi bir sistem var**, ama bu genel-amaçlı bir uygulama değil, Xbox
GDK'nın (`XAccessibility` ad alanı, `XClosedCaptionSetEnabled`/`XClosedCaptionGetProperties` fonksiyonları)
sunduğu bir **geliştirici API'si**:
- **Nasıl çalışır:** Oyunu yapan stüdyo, kendi oyununa bu API'yi entegre eder; API konsolun sistem
  genelindeki altyazı tercihlerini (font, boyut, arka plan kutusu, konum, hoparlör rengi) oyuna bildirir,
  oyun da kendi altyazısını BUNA UYGUN RENDER EDER. Yani metni Xbox üretmiyor — **oyunun kendisi altyazıyı
  biliyor ve çiziyor**, Xbox sadece "nasıl görünsün" tercihini merkezi olarak yönetiyor.
- **Bizim için sonucu:** Bu API'ye DIŞARIDAN bağlanamayız — kendi oyunumuz olmadığı ve üçüncü parti
  oyunların koduna müdahale etmediğimiz için (projenin "oyuna dokunmaz" ilkesi) bu API'yi kullanamayız.
  Yani "Game Caption" adıyla andığın şey işlevsel olarak bize **kapalı bir sistem**; biz kendi OCR/ASR
  tabanlı bağımsız overlay'imizi üretmek zorundayız (yukarıdaki Bölüm 3).
- **Alınacak tek şey — görsel/UX kuralı:** Xbox'ın resmi altyazı stil kılavuzu (XAccessibility
  Guidelines) net bir görsel dil tanımlıyor: ekranın altında yarı saydam siyah kutu, okunaklı
  büyük/orta/küçük font seçeneği, gerekirse konuşmacı adı/rengi etiketi. **Kendi overlay'imizin (Faz 1-2)
  varsayılan görünümünü bu kurala benzer tasarlayacağız** — kullanıcı konsollarda gördüğü yerel altyazı
  stiline aşina olduğu için, bizim overlay'imiz de "resmi bir Xbox/PS özelliği" gibi hissettirecek, ama
  mühendislik olarak tamamen bağımsız (kendi OCR/ASR + çeviri + çizim) kalacak.
- **Kaynak:** [Xbox XAccessibility üye listesi](https://devdocs.xbox.com/reference/system/xaccessibility/xaccessibility_members.md),
  [XClosedCaptionSetEnabled referansı](https://devdocs.xbox.com/reference/system/xaccessibility/functions/xclosedcaptionsetenabled.md),
  [Xbox Accessibility Guidelines](https://devdocs.xbox.com/gaming/accessibility/xbox-accessibility-guidelines/104)

### Genel çıkarım
Üç yaklaşımın hepsinde aynı iki alt sistem var: **(A) konuşma-tanıma (ASR) hattı** (ses varsa) ve
**(B) OCR hattı** (ekranda yazı varsa — diyalog altyazısı, görev metni, menü). Hangisinin kullanılacağı
oyuna göre değişir: bazı oyunlarda sesli diyalog altyazısızdır (ASR gerekir), bazılarında her şey yazılı
altyazı/metindir (OCR yeterlidir). Sağlam bir çözüm ikisini de destekler.

**Kaynaklar:**
- [Microsoft: Use live captions to better understand audio](https://support.microsoft.com/windows/b52da59c-14b8-4031-aeeb-f6a47e6055df)
- [Windows Report: Real-Time Translation in Live Captions, 44+ languages into English](https://windowsreport.com/microsoft-improves-the-real-time-translation-in-live-captions-from-over-44-languages-into-english/)
- [CaptionsRush — Overwolf app listing](https://overwolf.com/app/equalgaming-captionsrush)
- [TechRadar: Windows 11 live captions trick for PC gamers](https://techradar.com/news/microsofts-drive-for-accessibility-has-ushered-in-a-nifty-trick-for-pc-gamers-in-windows-11)
- [Xbox accessibility / game chat transcription (sohbet metne dökme, oyun sesi değil)](https://learn.microsoft.com/gaming/gdk/_content/gc/accessibility/accessibility-overview)

---

## 2. Neden konsol farklı bir problem?

PC'de "sistem sesi" ve "ekran" zaten aynı makinede — yakalamak bir API çağrısı. Xbox Series S/X ve
PS4/PS5'te durum şu:

- Konsollar **üçüncü parti arka plan uygulaması çalıştırmaz** (jailbreak/homebrew hariç — bunu
  **düşünmüyoruz**: hem ToS ihlali hem güvensiz, projenin "oyuna dokunmaz" ilkesiyle taban tabana zıt).
- Konsolun sesi/görüntüsü PC'ye **hiç ulaşmaz**, bir aktarım yolu olmadan.
- Yani bizim için tek soru: **konsolun ses+görüntüsünü PC'ye nasıl taşırız?** Üç gerçekçi yol var —
  aşağıda karşılaştırıldı.

---

## 3. Üç mimari seçenek (girdi kaynağına göre)

### Seçenek A — HDMI Capture Kart (donanım, en genel çözüm)
```
Konsol (HDMI çıkış) → Capture kart (Elgato/AVerMedia vb., HDMI-in → USB) → PC
                                                                              │
                                                                   PC: video+ses akışı
                                                                              │
                                                        ┌─────────────────────┴─────────────────────┐
                                                   OCR (altyazı varsa)                    ASR (sesli diyalog)
                                                        └─────────────────────┬─────────────────────┘
                                                                              ▼
                                                                  Yerel çeviri (OPUS-MT EN→TR)
                                                                              ▼
                                                        Overlay (PC ikinci ekranda VEYA telefon companion'da)
```
- **Artı:** Her konsol/her oyun için çalışır, oyunun ekranına/sesine tam erişim, en yüksek doğruluk.
- **Eksi:** Kullanıcı ek donanım (capture kart, ~€30-150) almak zorunda. Kurulum karmaşıklığı var.
- **Mevcut kodla örtüşme:** En yüksek — `ocr_backend.py` + `livetranslate.py` + `overlay.py` olduğu gibi
  kullanılabilir, sadece girdi "ekran" yerine "capture kart video akışı" olur (OpenCV/`mss` yerine
  `pyaudio`/DirectShow/`python-vlc` ile capture kart okuma).

### Seçenek B — Resmi uzaktan oynama/yayın uygulamaları (donanımsız, EN PRATİK)
```
Xbox:  "Xbox" uygulaması (Windows) → "Stream"/"Oyunumu Yayınla" (aynı ağda) → PC'de pencere
PS5/4: "PS Remote Play" uygulaması (Windows/Mac resmi Sony uygulaması) → PC'de pencere
                                                                              │
                                                              PC: pencere görüntüsü + sistem sesi
                                                                              │
                                                         (Seçenek A'daki aynı OCR/ASR/çeviri/overlay hattı)
```
- **Artı:** Sıfır ek donanım — Xbox'ın kendi "Stream" özelliği ve Sony'nin resmi "PS Remote Play" uygulaması
  konsol görüntü+sesini zaten bir Windows penceresine akıtıyor. O pencere PC'de normal bir pencere olduğu
  için **mevcut `ocr_backend.py`/ekran-okuma mantığımız hiç değişmeden o pencereyi okuyabilir**, sistem
  sesi de Windows'ta normal şekilde yakalanabilir (ASR için).
- **Eksi:** Ağ gecikmesi ekler (yerel ağda genelde kabul edilebilir, uzaktan/mobil veride değil). Konsol
  aynı Wi-Fi/ağda olmalı. Sony/Microsoft bu uygulamaların arayüzünü değiştirirse pencere tanıma (otomatik
  bölge/HWND bulma) güncellenmesi gerekebilir.
- **Önerilen başlangıç noktası budur** — mevcut yatırımı (OCR+çeviri motoru) en az değişiklikle, kullanıcıya
  ek maliyet çıkarmadan devreye alır.

### Seçenek C — Telefon kamerası ile TV'yi okuma (mobil companion üzerinden, en basit ama en düşük kalite)
```
Telefon kamerası (TV'ye doğrultulmuş) → Mobil companion app → anlık kare çek → OCR/ASR
                                                                    │
                                                        (bulut veya telefon-içi çeviri)
                                                                    ▼
                                                        Telefon ekranında Türkçe altyazı overlay
```
- **Artı:** Donanım/yazılım kurulumu yok, mevcut mobil companion app'e (Flutter) bir "Konsol Modu" sekmesi
  eklemek yeterli. Konsol markası/modeli önemsiz, "ekranda ne görünüyorsa" okur.
- **Eksi:** Kamera açısı/parlama/TV yansıması OCR doğruluğunu ciddi düşürür; sesli diyalog için telefonun
  mikrofonuyla ASR arka plan gürültüsüne (TV hoparlörü + oda sesi) karşı dayanıksız. **Kalite olarak en
  zayıf seçenek**, ama "hiç kurulum yapmadan dene" senaryosu için makul bir MVP/demo.

### Karşılaştırma tablosu

| | A: Capture kart | B: Remote Play/Stream | C: Telefon kamerası |
|---|---|---|---|
| Ek donanım/maliyet | Var (capture kart) | Yok | Yok (telefon yeter) |
| Kurulum zorluğu | Orta-yüksek | Düşük | Çok düşük |
| Doğruluk (OCR) | Yüksek | Yüksek | Düşük-orta |
| Doğruluk (ASR) | Yüksek | Yüksek (sistem sesi temiz) | Düşük (ortam gürültüsü) |
| Gecikme | Düşük | Orta (ağ bağımlı) | Orta-yüksek |
| Mevcut koda uyum | Yüksek | Yüksek | Orta (mobil tarafta yeni) |
| Konsol kapsamı | Her ikisi, HDMI varsa | Xbox: yerel ağ; PS: yerel+uzak | Her ikisi |

**Öneri:** B'yi birincil hedef olarak geliştir, C'yi (mobil kamera) ileride "hızlı deneme modu" olarak
mobil companion'a ekle, A'yı (capture kart) "ileri kullanıcı" seçeneği olarak dokümante et ama ilk sürümde
zorunlu kılma.

---

## 4. Mevcut TD2 Loot Advisor modülleriyle eşleşme

| İhtiyaç | Yeniden kullanılacak modül | Değişiklik gereksinimi |
|---|---|---|
| Ekrandaki metni oku (altyazı/menü) | `ocr_backend.py` | Girdi kaynağı: oyun ekranı → Remote Play/Stream pencere bölgesi. Pencere bulma (HWND/başlık eşleşmesi "Xbox", "PS Remote Play") eklenecek. |
| Metni Türkçeye çevir | `livetranslate.py` (OPUS-MT EN→TR yerel + bulut seçenekleri) | Değişiklik gerekmez — zaten EN→TR'ye optimize. |
| Çeviriyi ekranda göster | `overlay.py`, `trscreen.py` | Hedef pencere TD2 oyunu değil Remote Play/Stream penceresi olacağı için overlay'in doğru pencereyi hedeflediğinden emin olunmalı (çoklu pencere desteği). |
| Sesli diyaloğu tanı (altyazı yoksa) | **YENİ** — proje genelinde ASR motoru yok | Yeni bağımlılık: yerel bir konuşma tanıma motoru (örn. `faster-whisper`, CPU/GPU'da offline çalışır, gizlilik ilkesiyle uyumlu — bulut göndermez). |
| Konsol penceresini otomatik bul | **YENİ** | Windows pencere listesini tarayıp başlığı "Xbox"/"PS Remote Play" içeren pencereyi bulma (zaten `view3d.py`/`display.py` içinde pencere/ekran yardımcıları olabilir, kontrol edilmeli). |
| Mobil kamera modu (Seçenek C) | `mobile/` (Flutter) | Yeni bir ekran/sekme: kamera önizleme + OCR (mobil cihazda) + çeviri API çağrısı. |

---

## 5. Aşamalı Yol Haritası

### Faz 0 — Doğrulama (kod yazmadan önce)
- [ ] Xbox "Stream"/"Oyunumu Yayınla" ve PS Remote Play uygulamalarını gerçek bir Xbox Series S/X ve
      PS4/PS5 ile test et: pencere başlığı/HWND'si ne, gecikme ne kadar, ses PC'nin sistem sesine
      gerçekten düşüyor mu (bazı remote-play istemcileri sesi kendi dahili oynatıcısında tutabilir,
      WASAPI loopback'e görünmeyebilir — bu DOĞRULANMALI).
- [ ] `faster-whisper` (veya benzeri offline ASR) için CPU-only makinede gerçek zamanlı performansı ölç
      (gecikme, CPU kullanımı) — kullanıcının donanımı GPU'suz olabilir.
- [ ] Hukuki/ToS kontrolü: Xbox/PlayStation'ın Remote Play/Stream özelliklerini üçüncü parti bir
      uygulamanın ekran+ses okuması için kullanmanın hizmet şartlarına aykırı bir tarafı var mı
      (muhtemelen yok — bu tamamen kullanıcının kendi ekranını/sesini okumak, normal bir ekran kaydı/OCR
      aracından farksız — ama doğrulanmalı, kesin değil).

### Faz 1 — MVP: PC üzerinden Remote Play penceresi okuma (Seçenek B)
- [ ] Pencere algılama: başlığına göre Xbox/PS Remote Play penceresini bul, bölgesini al.
- [ ] Mevcut `ocr_backend.py`'yi bu bölgeye yönlendir (mevcut tarama mantığı aynı, sadece kaynak farklı).
- [ ] Mevcut `livetranslate.py`/`overlay.py` hattını bu akışa bağla (EN→TR, yerinde veya köşe overlay).
- [ ] Ayarlar'da yeni bir "Konsol Modu" sekmesi/aç-kapa: kullanıcı "Xbox" veya "PlayStation" seçer, uygulama
      ilgili pencereyi arar.
- [ ] Overlay'in varsayılan görünümü Xbox'ın resmi altyazı stiline benzetilecek (bkz. §1.4): ekranın
      altında yarı saydam siyah kutu, 3 font boyutu seçeneği (küçük/orta/büyük), isteğe bağlı konuşmacı
      etiketi — mevcut `overlay.py`'deki köşe/yerinde modlarına ek bir üçüncü "alt bant" modu olarak.
- [ ] Test: en az 2-3 farklı oyunda (altyazılı diyalog içeren) gerçek Xbox/PS5 + Remote Play ile uçtan uca
      doğrulama — **gerçek konsol ve gerçek Remote Play penceresiyle, bu görevi sadece kod okuyarak
      "doğrulanmış" saymayın.**

### Faz 2 — Sesli diyalog desteği (ASR)
- [ ] `faster-whisper` (ya da Faz 0'da seçilen motor) entegrasyonu: sistem sesinden (WASAPI loopback)
      canlı ses alıp küçük parçalar (örn. 3-5 sn) halinde metne çevirme.
- [ ] ASR çıktısını mevcut `livetranslate.py` çeviri hattına besleme (OCR çıktısıyla aynı pipeline).
- [ ] Gecikme/doğruluk dengesini ayarlama (parça boyutu, model boyutu — tiny/base/small Whisper
      varyantları arasında denge).
- [ ] UI: OCR-altyazı modundan ASR-konuşma moduna otomatik/manuel geçiş (bazı oyunlarda ikisi birlikte de
      olabilir — çakışma/öncelik kuralı gerekir).

### Faz 3 — Capture kart desteği (Seçenek A, ileri kullanıcı)
- [ ] Capture kartların PC'de bir "video capture device" (DirectShow/Media Foundation) olarak göründüğünü
      doğrula, bu akışı OpenCV/`mss` yerine uygun bir API ile okuma.
- [ ] Remote Play'den farklı olarak gerçek HDMI gecikmesi/renk profili farklarını hesaba kat (OCR eşik
      ayarı gerekebilir).
- [ ] Dokümantasyon: hangi capture kartlar test edildi, hangi ayarlarla.

### Faz 4 — Mobil kamera modu (Seçenek C, mobil companion'a ek)
- [ ] `mobile/` Flutter app'e "Konsol Ekranı Oku" sekmesi: kamera önizleme + kare yakalama.
- [ ] OCR: telefon üstünde (ör. Google ML Kit / Tesseract mobil) veya PC'ye gönderip orada işleme —
      gizlilik ve gecikme dengesine göre karar verilmeli (yerel OCR tercih edilir).
- [ ] Çeviri: mevcut bulut çeviri motorlarından biri (zaten masaüstünde kullanılanlarla aynı sağlayıcı
      seçeneklerini mobilde de sun).
- [ ] Bu modu açıkça "deneme/düşük doğruluk" olarak etiketle — kullanıcı beklentisini yönet.

### Faz 5 — Cilalama ve yayın
- [ ] Performans profili (CPU/GPU kullanımı, pil etkisi mobilde).
- [ ] Çoklu dil: şu an yerel motor sadece EN→TR; bulut motor seçenekleriyle diğer hedef diller de konsol
      modunda desteklenmeli (masaüstü zaten 10 dilli; konsol modu bunu kalıtmalı, yeniden icat etmemeli).
- [ ] README/BUGS/ROADMAP güncellemesi, kullanıcıya hangi konsol+hangi yöntemde ne kadar doğruluk
      bekleyeceğini anlatan bir kurulum kılavuzu (`docs/console_mode_setup_tr.md` gibi).

---

## 6. Açık riskler / net olmayan noktalar

- **Doğrulanmadı:** Xbox "Stream" ve PS Remote Play'in sistem sesini Windows'un WASAPI loopback'ine
  gerçekten düşürüp düşürmediği — bazı uygulamalar kendi ses çıkışını ayrı bir sanal cihaza yönlendirebilir.
  Bu, ASR fazının (Faz 2) ön koşulu; Faz 0'da kesinlikle test edilmeli.
- **Doğrulanmadı:** PS Remote Play'in Türkiye'den (bölge kısıtı olmadan) PS4/PS5'e sorunsuz bağlandığı —
  genelde sorun yok ama kullanıcının kendi ağ/NAT durumu gecikmeyi etkileyebilir.
- **Varsayım:** `faster-whisper`'ın en küçük modelinin (tiny/base) CPU'da gerçek-zamanlı (veya ona yakın)
  çalışacağı — gerçek ölçüm yapılmadı, Faz 0'da ölçülmeli.
- **Kapsam dışı (şimdilik):** Konsolun kendi arayüzüne (dashboard, oyun dışı menüler) çeviri — bu yol
  haritası sadece OYUN İÇİ metin/ses için; konsol dashboard'u ayrı ve daha az öncelikli bir hedef.
