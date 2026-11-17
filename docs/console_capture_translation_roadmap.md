# Konsol Yakalama + Canlı Çeviri — Yol Haritası

**Durum:** Araştırma tamamlandı, mimari planlandı. **Kod yazılmadı.** Bu belge, kullanıcının isteği
üzerine ("Xbox Series S/X, PS5/PS4'te çalışan oyunları Türkçe'ye çevirecek bir uygulama entegre
etmek istiyorum") yapılan yapısal araştırmanın ve çıkan yol haritasının kaydıdır.

**Kapsam netliği (önemli):** Bu özellik TD2 Loot Advisor'ın eşya kartı OCR'ına (`ocr_backend.py`'nin
TD2'ye özel kırpma/şablonlarına) değil, projede zaten var olan **genel canlı çeviri** motoruna
(`livetranslate.py` + `overlay.py`/`InPlace`) dayanıyor — o motor zaten "herhangi bir oyunun
ekranındaki metni oku, çevir, üstüne bindir" mantığıyla genel yazılmış (sadece TD2'de kullanılıyor).
Konsol desteği, bu motora YENİ bir görüntü kaynağı (capture card) ekleyip aynı pipeline'ı çalıştırmak
anlamına geliyor — OCR ve çeviri tarafında sıfırdan iş yok, asıl iş görüntü kaynağı ve overlay'in
nereye çizileceği.

---

## 1. Capture card nasıl çalışır (araştırma özeti)

Kaynaklar: [Elgato — What is a capture card](https://www.elgato.com/ch/en/explorer/products/capture/what-is-a-capture-card/),
[AVerMedia — Capture cards: what they are and how they work](https://www.avermedia.com/blog/detail/capture-cards-what-they-are-and-how-they-work),
[OBS Sources Guide](https://obsproject.com/kb/Sources-Guide),
[BrightSideOfNews — PCIe 4K60 capture card latency karşılaştırması](https://brightsideofnews.com/gaming-hardware/pcie-4k60-capture-cards/).

- **Sinyal yolu:** Konsol (Xbox Series S/X, PS5/PS4) → HDMI çıkışı → capture card'ın HDMI girişi.
  Çoğu cihaz **passthrough** yapar: aynı anda ikinci bir HDMI ile görüntüyü TV'ye de gönderir —
  yani kullanıcı oyunu normal şekilde TV'de görmeye devam edebilir, capture card bir "kopya" alır.
- **PC'ye bağlantı:** Çoğu tüketici modeli **USB (3.0/3.2)** ile bağlanır; bazı üst segment modeller
  **PCIe** kartı olarak takılır (anakartta boş PCIe x4 slotu gerekir).
- **PC'nin gördüğü şey:** Kart, Windows'a bir **video capture cihazı** (webcam'e benzer bir sınıf
  cihazı — DirectShow/Media Foundation kaynağı) olarak görünür. Yazılım (OBS, veya bizim yazacağımız
  kod) bunu "Video Capture Device" kaynağı olarak **cv2.VideoCapture** / DirectShow API'siyle açar —
  TD2'nin ekran okumasında kullandığı `mss` (kendi monitörünü yakalama) burada **işe yaramaz**,
  çünkü yakalanacak görüntü PC'nin kendi ekranında değil, harici bir video akışında.
- **Gecikme (latency):** Ölçülen değerler — **USB3 kartlar ~45-65 ms**, **PCIe kartlar ~25-42 ms**
  ek gecikme ekliyor (BrightSideOfNews karşılaştırması). Bu, OCR+çeviri'nin kendi işlem süresine
  **eklenir** — toplam "metin ekranda belirdikten sonra çevirinin görünmesi" süresi muhtemelen
  birkaç yüz ms olacak. Mevcut `livetranslate.py` zaten "yazı değişip durulunca oku" mantığıyla
  çalıştığı için (altyazı/diyalog metni genelde birkaç saniye sabit kalır) bu gecikme büyük ölçüde
  tolere edilebilir; hızlı değişen HUD metinleri için sorun olabilir.
- **Lisans/SDK:** Çoğu capture card, Windows'un standart UVC/DirectShow sınıf sürücüsüyle çalışır —
  **vendor SDK'sına gerek yok** (Elgato/AVerMedia kendi SDK'larını sunar ama bu, daha düşük
  gecikme/daha fazla kontrol için opsiyoneldir, zorunlu değil). İlk sürüm için SDK'sız, jenerik
  DirectShow/Media Foundation yolu yeterli.

## 2. Mevcut mimariyle fark — ne değişiyor

| | Mevcut (PC oyunu, TD2) | Yeni (konsol) |
|---|---|---|
| Görüntü kaynağı | `mss` ile kendi monitör/pencere bölgesi | Capture card'dan `cv2.VideoCapture` (DirectShow/MF) ile canlı video karesi |
| "Oyun penceresi" | PC'de gerçek bir pencere/süreç var, overlay onun üstüne konumlanır | **Yok** — konsol görüntüsü PC'de bir pencere değil, bir video akışı |
| Overlay nereye çizilir | Harici oyun penceresinin üstüne şeffaf, click-through bir pencere (`overlay.py`) | **Kendi "Yakalama Önizleme" penceremizin üstüne** — çünkü overlay'in hedefleyeceği bir dış pencere yok |
| Kullanıcı oyunu nereden izliyor | Kendi PC ekranından (zaten oynadığı yer) | **Bu uygulamanın önizleme penceresinden** (TV'den izlerse çeviriyi GÖRMEZ — aşağıdaki §3'e bak) |
| Ekran yakalamadan dışlama | Overlay penceresi kendi OCR döngüsünden hariç tutuluyor (zaten kendi ekran bölgesini tekrar okumasın diye) | Aynı mantık geçerli, ama kaynak artık capture card karesi olduğu için zaten karışmaz |

## 3. En kritik mimari karar: kullanıcı oyunu nereden izleyecek?

Bu, projeye başlamadan önce netleşmesi gereken tek karar — yanlış varsayılırsa özelliğin tamamı
kullanıcı için anlamsız olur:

- **Passthrough + TV'den izleme:** Capture card görüntüyü PC'ye kopyalarken TV'ye de gönderiyor.
  Kullanıcı TV'den oynarsa, **PC'deki overlay TV'de görünmez** (overlay yalnızca PC ekranında
  çizilen bir pencere). Bu senaryoda çeviri sadece PC monitöründeki önizleme penceresinde görünür —
  kullanıcı pratikte "TV'de oyun, yanımda/altımda PC ekranında çeviri" şeklinde iki ekrana bakmak
  zorunda kalır.
- **Tek ekrandan izleme (PC monitörü = ana ekran):** Kullanıcı capture card'ın önizleme penceresini
  tam ekran yapıp oyunu doğrudan PC monitöründen oynarsa, çeviri doğal şekilde üstüne biner — en
  temiz senaryo.
- TV çıkışına çeviriyi de yansıtmak (PC'nin işlediği görüntüyü tekrar bir HDMI çıkışından TV'ye
  göndermek) **ek donanım (HDMI "dummy"/loopback çıkışı olan bir ikinci capture/çıkış kartı veya
  GPU'nun ikinci HDMI çıkışı + pencere klonlama) gerektirir** — bu, ilk sürümün kapsamı dışında,
  ayrı ve daha maliyetli bir faz olarak not edildi.

**Öneri:** İlk sürümde açıkça "çeviriyi görmek için oyunu bu uygulamanın önizleme penceresinden
oynamalısın" kısıtını kullanıcıya baştan anlat — belirsiz bırakılırsa "çeviri TV'de çıkmıyor" diye
yanlış bir hata/bug sanılır.

## 4. Donanım gereksinimi (kullanıcı tarafı)

Kod tarafında yapılacak hiçbir şey, kullanıcıda bir **capture card** olmadan test edilemez — bu,
mobil Flutter işindeki "Flutter SDK yok" kısıtından farklı, **fiziksel donanım** kısıtı:

- Tipik seçenekler: Elgato HD60 X / 4K60 S+ (USB3), AVerMedia Live Gamer serisi (USB3/PCIe).
  Hangisini aldığına karar kullanıcıya ait — proje tarafında "jenerik UVC/DirectShow cihazı" olarak
  ele alınacağı için marka bağımsız çalışması hedeflenecek, ama **gerçek test mutlaka kullanıcının
  Windows PC'sinde, gerçek bir kart ve gerçek bir konsolla yapılmalı** (bu konteynerde ne capture
  card ne de bir konsol var — bu özellik için sanal doğrulama bile mümkün değil, mobildeki gibi
  "en azından sözdizimi/mantık kontrolü" seviyesi de yok).
- Konsol tarafında HDR kapalı olması önerilir (ilk sürüm için) — HDR tonlamanın OCR kontrastını
  nasıl etkileyeceği bilinmiyor, doğrulanmadı.

## 5. Önerilen fazlar

**Faz 0 — Fizibilite denemesi (kullanıcının PC'sinde, kart elindeyken)**
- `cv2.VideoCapture(index, cv2.CAP_DSHOW)` ile cihazı aç, ham kare al, PNG'ye kaydet — kartın
  Python'dan görünüp görünmediğini, hangi index/çözünürlük/FPS geldiğini doğrula.
- Gerçek ek gecikmeyi ölçmek için basit bir sayaç testi (ekrana saniye sayacı gösterip capture'da
  kaç ms geriden geldiğini kronometre ile ölç) — yukarıdaki 25-65 ms tahminini kendi donanımında
  teyit et.
- **Çıkış kriteri:** Kare gerçekten alınabiliyor ve gecikme kabul edilebilir (<150 ms toplam) mı?

**Faz 1 — Yakalama Önizleme penceresi**
- Yeni bir Tkinter `Toplevel`: capture card karelerini canlı gösteren basit bir video penceresi
  (Canvas + `PhotoImage`, ~30 FPS yeterli — tam konsol FPS'i gerekmiyor, OCR için zaten örnekleme
  yapılacak). Cihaz seçici (birden fazla capture card/webcam varsa), çözünürlük/FPS göstergesi.
- Bu fazda çeviri YOK — sadece görüntü akışının PC'de düzgün, kabul edilebilir gecikmeyle
  göründüğünü doğrulamak.

**Faz 2 — OCR + çeviri pipeline'ına bağlama**
- `livetranslate.py`'nin görüntü kaynağını soyutlayan bir katman: şu an muhtemelen doğrudan `mss`
  çağrısı var — bunu "kare üret" diye genel bir fonksiyona çıkarıp, PC ekranı veya capture card
  karesi iki farklı implementasyon olacak şekilde ayır. OCR/çeviri/metin-stabilizasyon mantığının
  **tek satırı bile değişmeyecek** — sadece girdi kaynağı değişiyor.
- Aynı "yazı değişip durulunca oku" debounce mantığı capture card karelerine de uygulanacak.

**Faz 3 — Overlay'i önizleme penceresine bağlama**
- `overlay.py`/`InPlace`, şu an harici bir oyun penceresinin üstüne konumlanan şeffaf bir pencere
  varsayıyor. Konsol modunda hedef **kendi önizleme penceremiz** olduğu için bu aslında DAHA BASİT:
  harici pencere konumunu takip etmek yerine doğrudan kendi Canvas'ımızın üstüne çizebiliriz —
  şeffaf/click-through pencere karmaşası gerekmez.

**Faz 4 — Konsol/OS bildirimlerini filtreleme**
- Xbox Guide, PS5 Control Center gibi konsol arayüzleri capture'a karışabilir; mevcut `PRIVATE`
  regex'i (arkadaş bildirimi, Steam/Discord/Nvidia metinlerini filtreleyen) genişletilip konsol
  sistem metinlerini de (örn. "Press the Xbox button", "Control Center") kapsayacak şekilde
  güncellenecek — gerçek örnekler kullanıcının PC'sinde toplanmadan tam liste çıkarılamaz.

**Faz 5 — Ayarlar, cihaz profilleri, beta**
- Ayarlar sekmesine: capture cihazı seçimi, çözünürlük/FPS, "konsol modu" açma/kapama.
- Beta duyurusu + kullanıcıya önizleme penceresinden oynama kısıtının (bkz. §3) açıkça anlatılması.

## 6. Riskler / açık sorular

- **Lisans/telif:** Mevcut projenin zaten kabul ettiği risk kategorisiyle aynı (oyun metninin
  üstüne çeviri bindirme) — konsol desteği bu açıdan yeni bir risk eklemiyor.
- **Gizlilik/güvenlik ilkesi değişmiyor:** Konsola hiçbir şekilde dokunulmuyor (ne bellek ne ağ ne
  kontrolcü girişi) — sadece harici bir video sinyali okunuyor; bu, PC'nin kendi ekranını okumaktan
  bile daha "hands-off" bir yöntem.
- **HDR/renk doğruluğu:** OCR kontrastına etkisi doğrulanmadı — Faz 0'da test edilmeli.
- **Marka bağımsızlığı:** Jenerik DirectShow/UVC yaklaşımı çoğu kartla çalışmalı ama her kartın
  sürücü kalitesi farklı — "resmi desteklenen kart listesi" yerine "UVC/DirectShow uyumlu kartlar"
  diye genel bir uyumluluk beyanı önerilir, test edilmeden belirli bir marka garanti edilmemeli.
- **İkinci ekran gereksinimi netleşmeli:** §3'teki kısıt kullanıcıya baştan, belirsiz bırakılmadan
  anlatılmalı — bu özelliğin kabul kriterlerinden biri.

## 7. Bu belgenin doğrulama durumu

Bu belgedeki teknik bilgiler **web araştırmasına dayanıyor** (yukarıdaki kaynaklar), kod yazılmadı,
hiçbir iddia bu ortamda veya gerçek donanımda test edilmedi. "Doğrulandı" diye işaretlenebilecek
hiçbir satır yok — hepsi **araştırma bulgusu** veya **tasarım kararı** seviyesinde. Faz 0 tamamlanıp
kullanıcının PC'sinde gerçek bir capture card ile ilk kare gerçekten alınana kadar bu plan
**doğrulanmamış** sayılmalı.
