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

### 1.5 Gerçek emsal: gamecaptionapp.com ("Game Caption" mobil uygulaması)
Kullanıcının kastettiği uygulama bu — gerçek, yayında, ücretli bir mobil uygulama (iOS + Android,
`gamecaptionapp.com`). Sayfası ve destek sayfası (`/support.html`) incelendi; mimarisi **önceki
bölümlerdeki tahminlerimizi doğruluyor**, ek olarak şu somut gerçek detayları veriyor:

- **Bu bir PC uygulaması değil, bir TELEFON uygulaması.** PC desteği yok — PC'de sadece kamera modu
  kullanılabilir ("bilgisayarda... herhangi bir konsol, bilgisayar, film veya dizide çalışır").
  **Önemli strateji çıkarımı:** Bizim de bu işlevi PC masaüstü uygulamasına değil, zaten var olan
  `mobile/` (Flutter) companion uygulamasına eklemek daha doğru eşleşme olur.
- **PS5 bağlantısı = resmi Sony Remote Play, doğrulandı (destek sayfasından birebir alıntı):**
  "PS5 tamamen açık olmalı ve telefonla aynı ağa bağlı olmalı", "PS5'te Uzaktan Oynama açık olmalı",
  "Game Caption'ı ikinci bir PSN hesabıyla bağlayın, kumandada kendi ana hesabınızı seçin." — Bu, bizim
  Bölüm 3 / Seçenek B'deki tahminimizle **tam örtüşüyor**: resmi Remote Play protokolü, ikinci (yardımcı)
  bir PSN hesabı üzerinden bağlanıyor, ana hesap kumandada kalıyor.
- **Mühendislik riski (yeni bulgu):** Sony'nin Remote Play protokolüne resmi/genel bir "üçüncü parti
  SDK"sı yok — bu tür entegrasyonlar genelde ya Sony ile özel ortaklık ya da **açık kaynak
  ters-mühendislik projeleri** (örn. `chiaki`/`chiaki-ng`, GPL lisanslı, PS Remote Play protokolünü
  bağımsızca uygulayan topluluk projeleri) üzerinden yapılır. Hangisini `gamecaptionapp.com`'un
  kullandığı **doğrulanamadı** — ama bu bizim için önemli bir **lisans/hukuki araştırma kalemi**:
  `chiaki-ng` GPL'dir, projemize (MIT) doğrudan kod olarak gömülürse lisans uyumu ayrıca incelenmeli.
- **Xbox bağlantısı: yöntem sayfada belirtilmemiş**, doğrulanamadı — muhtemelen Xbox'ın resmi olmayan/
  yarı-resmi "Smartglass"/konsol yayın protokolü (topluluk projesi: `xbox-smartglass`) kullanılıyor,
  ama bu **doğrulanmadı, sadece varsayım**.
- **ASR YOK — önemli basitleştirme:** Uygulama oyunun sesini DİNLEMİYOR. "Çeviri için yalnız altyazı
  metni kullanılır" deniyor. "Sesli çeviri" dedikleri şey, OCR'la okunan altyazı metninin **çevirisini
  telefonun kendi metin-okuma (TTS) sesiyle okutması** — konuşma tanıma (ASR) değil. **Bu, önceki
  mesajımdaki Faz 2'yi (ASR entegrasyonu) gereksiz kılıyor** — çok daha basit bir TTS okuma adımı
  yeterli, hem de TD2 Loot Advisor'da zaten `speech.py`/`voicepack.py` (Sesli Asistan modülü) içinde
  ses altyapısı mevcut, oradan TTS kısmı yeniden kullanılabilir.
- **Kamera modu, bizim Seçenek C ile birebir aynı:** "Kamera modunda telefonu sabitleyin ve ekrandaki
  yansımayı azaltın", "altyazının yeşil kutunun içinde olduğundan emin olun" (OCR bölgesi hizalama
  rehberi). Bu, **platform bağımsız, en az mühendislik riskiyle çalışan, tüm konsol+PC'yi aynı anda
  kapsayan tek mod** — rakip de bunu "her şeyle çalışır" olarak pazarlıyor.
- **TV modu (ek, bizim planımızda yoktu):** Telefon OCR+çeviriyi yapıyor, sonucu aynı ağdaki bir TV
  uygulamasına (Android TV/Google TV native app, Samsung/LG için ayrı yöntemler) QR ile eşleştirip
  gönderiyor — telefonun küçük ekranına bakmak zorunda kalmadan büyük ekranda altyazı görme. Bizim
  mobil companion'ımızda da ucuz bir ek olabilir (zaten yerel ağ QR eşleştirme altyapımız var —
  `companion.py`'nin masaüstü-telefon QR eşleştirmesiyle aynı mantık, LAN içinde telefon-TV'ye
  genişletilebilir).
- **İş modeli:** Günlük kota + aylık/yıllık abonelik (Premium AI / Professional), tek seferlik ücretsiz
  deneme. Bizim projenin "ücretsiz/açık kaynak" ilkesiyle örtüşmüyor — bu bölüm bilgi amaçlı, kopyalama
  hedefi değil.

**Sonuç — plan güncellemesi:** Yukarıdaki bulgular ışığında Bölüm 5'teki fazlar şu şekilde revize edildi:
kamera modu (eski Faz 4) gerçek MVP olarak ÖNE alındı ve mobil companion'a taşındı; ASR fazı (eski Faz 2)
TTS-okuma ile değiştirildi (çok daha basit); Remote Play/Smartglass entegrasyonu açık lisans/hukuki
riskiyle birlikte ayrı, daha sonraki bir faz olarak işaretlendi. Güncel sıralama Bölüm 5'te.

**Kaynaklar:** [gamecaptionapp.com](https://gamecaptionapp.com/), [gamecaptionapp.com/support.html](https://gamecaptionapp.com/support.html), [gamecaptionapp.com/en/](https://gamecaptionapp.com/en/)

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

## 5. Aşamalı Yol Haritası (gamecaptionapp.com bulgularıyla güncellendi, §1.5)

### Faz 0 — Doğrulama (kod yazmadan önce)
- [ ] Mevcut mobil companion'ın (Flutter) kamera/OCR için hangi paketleri kullanabileceğini araştır
      (Google ML Kit Text Recognition — ücretsiz, cihaz-üstü, Android+iOS; alternatif: platform tarafı
      Tesseract binding). Gerçek bir telefon ile gerçek bir TV/monitör ekranına karşı OCR doğruluğunu
      test et (parlama, açı, uzaklık değişkenleriyle).
- [ ] PC/masaüstü rotası (Remote Play penceresi okuma) için: Xbox "Stream" ve PS Remote Play
      uygulamalarını gerçek bir Xbox Series S/X ve PS4/PS5 ile test et — pencere başlığı/HWND'si ne,
      gecikme ne kadar.
- [ ] Hukuki/lisans kontrolü: Remote Play protokolüne resmi SDK yoksa (bkz. §1.5), ters-mühendislik
      açık kaynak projelerinin (örn. `chiaki-ng`, GPL) lisansının MIT lisanslı TD2 Loot Advisor'a nasıl
      entegre edilebileceği (ayrı süreç/binary olarak çağırma vs. kod gömme — lisans etkisi farklı)
      netleştirilmeli. Bu netleşmeden Remote Play fazına (Faz 3) başlanmamalı.

### Faz 1 — MVP: Mobil companion'da kamera modu (Seçenek C — en düşük risk, platform bağımsız)
- [ ] `mobile/` Flutter app'e yeni bir sekme/mod: kamera önizleme + OCR hizalama rehberi (gamecaptionapp
      tarzı "yeşil kutu" — kullanıcı altyazının kutunun içinde kaldığından emin olur).
- [ ] OCR: cihaz-üstü (gizlilik ilkesiyle uyumlu — ekran görüntüsü sunucuya gitmez, sadece OCR çıktısı
      metni çeviri için kullanılır, aynı gamecaptionapp'ın yaptığı gibi).
- [ ] Çeviri: masaüstündeki `livetranslate.py` motor seçenekleriyle aynı sağlayıcı listesini mobilde de
      sun (zaten masaüstü 10 dilli; mobil bunu kalıtmalı, yeniden icat etmemeli).
- [ ] Sesli okuma (TTS): OCR+çeviri çıktısını telefonun yerel metin-okuma sesiyle okut — **ASR YOK**,
      sadece zaten elde var olan çeviri metnini sesli okuma (§1.5'teki basitleştirme).
- [ ] Overlay görünümü Xbox'ın resmi altyazı stiline benzetilecek (bkz. §1.4): yarı saydam siyah kutu,
      font boyutu seçenekleri.
- [ ] Bu modu PC için de öner (kamera telefonla, monitöre doğrultularak) — tek kod tabanıyla hem konsol
      hem PC hem de başka bir cihazı (TV, taşınabilir konsol) kapsar, ek entegrasyon gerekmez.
- [ ] Test: gerçek bir telefonla gerçek bir TV/monitör ekranına karşı, en az 2-3 farklı oyunla uçtan uca
      doğrulama.

### Faz 2 — PC masaüstünde Remote Play penceresi okuma (Seçenek B, ikincil rota)
- [ ] Pencere algılama: başlığına göre Xbox/PS Remote Play penceresini bul, bölgesini al.
- [ ] Mevcut `ocr_backend.py`'yi bu bölgeye yönlendir (mevcut tarama mantığı aynı, sadece kaynak farklı).
- [ ] Mevcut `livetranslate.py`/`overlay.py` hattını bu akışa bağla.
- [ ] Ayarlar'da yeni bir "Konsol Modu" sekmesi/aç-kapa.
- [ ] Test: gerçek Xbox/PS5 + Remote Play ile uçtan uca doğrulama (sadece kod okuyarak doğrulanmış
      sayılmaz).

### Faz 3 — Resmi olmayan Remote Play/Smartglass protokol entegrasyonu (yüksek risk, opsiyonel)
- [ ] Faz 0'daki lisans netleşmesi tamamlanmadan BAŞLANMAZ.
- [ ] gamecaptionapp'ın yaptığı gibi doğrudan telefon üzerinden PS5 Remote Play / Xbox konsol-yayın
      protokolüne bağlanma — bu, Faz 1/2'nin aksine kullanıcının ayrıca bir Remote Play penceresi
      açmasını gerektirmez (uygulama kendi içinde bağlanır), ama mühendislik + lisans maliyeti en yüksek
      kalemdir. İkinci bir PSN/Microsoft hesabı bağlama akışı gerekir (gamecaptionapp'ın yaptığı gibi).

### Faz 4 — Capture kart desteği (Seçenek A, ileri kullanıcı, düşük öncelik)
- [ ] Capture kartların PC'de bir "video capture device" (DirectShow/Media Foundation) olarak göründüğünü
      doğrula, bu akışı uygun bir API ile okuma.
- [ ] Dokümantasyon: hangi capture kartlar test edildi, hangi ayarlarla.

### Faz 5 — TV modu ve cilalama
- [ ] Mobil companion'ın OCR+çeviri sonucunu yerel ağdaki bir TV'ye QR eşleştirmeyle gösterme (mevcut
      `companion.py` masaüstü-telefon QR eşleştirme mantığının telefon-TV'ye genişletilmesi).
- [ ] Performans profili (pil etkisi, OCR döngü sıklığı).
- [ ] README/BUGS/ROADMAP güncellemesi, kurulum kılavuzu (`docs/console_mode_setup_tr.md`).

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
- **Doğrulanmadı (yeni, §1.5'ten):** `gamecaptionapp.com`'un Xbox bağlantısını ve PS5 Remote Play
  entegrasyonunu tam olarak hangi teknik yolla (resmi SDK mı, ters-mühendislik mi) yaptığı kamu
  sayfalarından çıkarılamadı — Faz 3'e geçmeden önce bu ayrıca araştırılmalı, resmi sayfanın iddiaları
  kesin teknik gerçeklik olarak alınmamalı.
- **Lisans riski (yeni, §1.5'ten):** Açık kaynak Remote Play ters-mühendislik projeleri (örn.
  `chiaki-ng`) GPL lisanslıdır; TD2 Loot Advisor MIT lisanslıdır. Bu ikisinin nasıl bir arada
  kullanılabileceği (ayrı süreç mi, kod gömme mi) bir hukuk/lisans uzmanı görüşü gerektirebilir —
  Claude bu konuda kesin hukuki tavsiye veremez, kullanıcı gerekirse bağımsızca doğrulamalı.
