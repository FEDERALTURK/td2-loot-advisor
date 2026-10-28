# TD2 Loot Advisor — Türkçe kılavuz

*The Division 2* için ekran okuyan (OCR) yardımcı. Envanterde bir eşyanın üstüne gelip **F8**'e basarsın;
program kartı okur, oyunun eşya kütüphanesiyle doğrular, **aktif build'inle** karşılaştırır ve saniyeler
içinde **SAKLA / DÜŞÜN / KIR / KONTROL ET** der. Build'in eksik parçalarını takip eder, oyun görevlerini
senin dilinde gösterir. 10 dil; herkes kendi dilini ekleyebilir.

## İndir

**[En son sürüm → Releases](https://github.com/FEDERALTURK/td2-loot-advisor/releases/latest)**:
`TD2LootAdvisor_Setup_<sürüm>.exe` (kurulum, önerilen), `TD2LootAdvisor_<sürüm>_portable.zip` (kurulumsuz) ve Android için `TD2LootAdvisor_Companion_0.1.1-beta.apk`.
Telefon eşleştirme adımları: [Türkçe bağlantı kılavuzu](docs/mobile_companion_connection_tr.md).

## Güncelleme

Program açılışta (12 saatte bir) GitHub'daki en son sürümü denetler ve sorar. Ayarlar → Genel → **Güncellemeler**'den elle de
denetlenir. Kurulu sürüm yeni kurulum dosyasını indirip SHA-256 ile doğrular, sessiz kurar ve kendini yeniden açar; kaynaktan çalışan
sürüm yalnız program dosyalarını yeniler (eskileri `backup/` altına). Ayarlar, build'ler, sandık ve `private/` hiçbir zaman değişmez.

## Ne yapar, ne yapmaz

- ✅ Yalnızca **ekranı** okur (OCR) ve oyunun kendi **ayar dosyasını** (`state.cfg`) okur.
- ❌ Oyunun **belleğini okumaz/yazmaz**, oyun dosyalarını değiştirmez, oyuna tuş göndermez.
- ⚠️ Kararlar ekran okumaya dayanır; kritik eşyalarda karta bir göz at. Egzotikler hiçbir zaman "KIR" çıkmaz.

## Kurulum

1. **Python 3.13** kur (önerilen; 3.12 da olur). OCR motorunu (RapidOCR) `run.bat` kendisi kurar.
   **Tesseract OCR** artık isteğe bağlı, yalnızca yedek (UB Mannheim sürümü, `C:\Program Files\Tesseract-OCR`).
2. Depoyu indir: **Code → Download ZIP**, bir klasöre çıkar.
3. **`scripts\run.bat`** ile başlat. İlk açılışta gerekli paketleri kurar; sesli komut ve video için
   isteğe bağlı paketleri (rapidocr, onnxruntime, pyttsx3, sounddevice, faster-whisper, av) dener. Kurulamayan paket atlanır.
   > Programı her zaman run.bat ile aç: doğru Python sürümünü (3.13) seçer. app.py'ye çift tıklamak
   > bilgisayardaki en yeni Python'u kullanır; orada ses/video paketleri olmayabilir.
4. **Kurulum dosyası:** `scripts\build_installer.bat`'a çift tıkla → `installer\TD2LootAdvisor_Setup_<sürüm>.exe`
   (yönetici izni istemeyen gerçek bir Windows kurulumu; kişisel ayarların ve lisansın pakete girmez).
   İsteğe bağlı: `scripts\build_exe.bat` tek dosyalık `.exe` üretir; `scripts\install_claude_code.bat`
   asistan ve "Claude ile getir" için Claude Code'u kurar (Claude aboneliğiyle, API anahtarı gerekmez).

## Oyun ayarları (önerilen)

Oyun dili **İngilizce**, **kenarlıksız pencere**, **HDR kapalı**, oyun çözünürlüğü = monitör çözünürlüğü.
Ayarlar → **Ekran ve oyun** sayfası oyunun ayar dosyasını okuyup bunları senin için kontrol eder.

## Hızlı başlangıç

1. **Aktif build** seç (Panel'in üstünde, Build'ler'de ya da Eksik Parça'da — üçü aynı build'i kullanır).
2. **Başlat**'a bas. Oyunda eşyanın üstüne gel, **F8**. (Envanterde gezerken **Otomatik** mod da var.)
3. Kart tüm ekranda kendiliğinden bulunur; bölge seçmek gerekmez.
4. **Uzun kartlar** ekrana sığmaz: önce üst kısmı oku, kartı kaydır, alt kısmı oku — iki okuma tek eşya olarak birleşir.

## Sekmeler

### Panel
Karar, tanınan eşya (ad, set/marka, yuva, tür), attribute'lar ve **oyundaki en yüksek değere göre rulo kalitesi**,
build eşleşmeleri ve aktif build'in o yuvası için **✔/✖ şart listesi** (set/marka, çekirdek, attribute, talent).
Oyunda bindirme kartın **hemen yanında** çıkar.

### Build'ler
- **📋 Build ayrıntısı:** özet, kaynaklar, set/marka bonusları ve 8 yuvanın her biri için *ne aranmalı*
  (gear set parçası / marka / named-egzotik eşya, çekirdek, attribute'lar, göğüs-sırt talent'i, silah türü ve talent'i)
  ile elindeki parça ve şartların ✔/✖ durumu.
- **✏ Düzenle:** set/marka, named-egzotik eşyalar, "iyi değer"li attribute'lar, talent'ler, silah türleri.
- **Meta build'ler** her gün ortak listeden (`meta/meta_builds.json`) gelir; kendi build'lerine dokunulmaz.

### Eksik Parça
Döndürülebilir **3D ajan** (yeşil = var, kırmızı = eksik; parçaya tıkla), şartlarıyla yuva kartları ve
tüm build'ler için **3D puan çubukları**. Uyan eşyalar otomatik kaydedilir; build tamamlanınca haber verilir.

### Sandık (yeni)
- **Envanter:** taranan her eşya sandığa kaydedilir (`stash.json`); kırdıklarını "Kırıldı" işaretle.
- **Optimize et:** seçili build için sendeki en iyi parçalar. Set parçaları herhangi bir yuvada olabilir ama 4 parça bonusu
  korunur; named/egzotik eşyalar kendi yuvasında kalır. Her yuva için uyum %, ✔/✖ şartlar ve **sıradaki en değerli düşüş**.
- **Denetim raporu:** kırılabilecekler (kararı KIR ya da daha iyi kopyası olanlar; en yakın 5 build'inde kullanılan parçalar
  ve egzotikler asla), kopyalar ve kırmadan önce kalibrasyon kütüphanesine eklenecekler.
- Premium: **kalibrasyon danışmanı** (hangi attribute hangi eşyadan; silah ve ekipman kütüphaneleri ayrı, egzotik kaynak
  önerilmez), tüm build'lerin sandığa göre sıralaması, CSV dışa aktarma.

### Satıcılar, telefon, paylaşım (yeni)
- **Satıcılar** (Sandık → Satıcılar): haftalık satıcılar ve bugünün hedefli loot'u build'lerin ve sandığınla eşleştirilir:
  "Cassie'de healer build'ine %95 uyan Future Initiative eldiveni var". İki kaynak: kendi taraman (**Satıcı modu**: satıcı
  ekranında F8) ve topluluk verisi [hi-dep Division 2 Database](https://hidep-division2.pages.dev/?view=vendor) — senin
  bilgisayarında herkese açık sayfasından doğrudan okunur, bu depoya kopyalanmaz. Salı sıfırlamasından sonra bir kez yenilenir.
  Premium.
- **Telefon arkadaşı** (Ayarlar → Senkron): ev Wi-Fi'nde yalnız okunur bir sayfa (gizli anahtarlı adres + QR): son karar,
  aktif build ve satıcı eşleşmeleri. Premium.
- **Build paylaşımı** (Build'ler → 🔗 Paylaş): build kısa bir koda (`TD2B-…`) ve QR'a dönüşür; Build'ler → Kodu yapıştır ile
  eklenir. Ücretsiz.

### Topluluk ve yapay zekâ (yeni)
- **Anonim düşüş istatistiği** (gönüllü, bir kez sorulur): Panel'de oynadığın aktiviteyi seç; taradığın her YENİ eşya o
  aktiviteye sayılır. Gönderilen: eşya, yuva, nadirlik, attribute türleri, en iyi rulo %, aktivite, rastgele kimlik —
  değerler, ad, e-posta, lisans anahtarı, bilgisayar bilgisi asla; sunucu IP saklamaz. Premium: aktivite başına en çok
  düşenler, bir eşyanın nerede düştüğü (1000 düşüşte). Sunucu: Cloudflare Workers + D1 — [`server/README.md`](server/README.md).
- **Sürüm sayacı** (6.0.1+): program topluluk görev listesini indirirken yalnız sürüm numarasını ve açılıştaki ilk
  istek olup olmadığını gönderir. Sunucu sürüm başına günlük toplam tutar (kimlik, IP, hesap yok); böylece hangi sürümlerin
  hâlâ kullanıldığı görülür. Topluluk görevleri kapatılırsa bu da kapanır.
- **Asistana sor**: taranan eşyayı, aktif build'inin o yuva için şartlarıyla birlikte asistana sorar.
- **Claude ile oku**: OCR başarısız olursa kart resmi Claude Code ile okunur (isteğe bağlı; gerçek kartla denendi: 5 sn, tüm değerler doğru).
- **Yanlış okundu**: kartı kaydeder ve hazır doldurulmuş bir GitHub hata bildirimi açar; kart test setine eklenebilir.

### Bilgi (yeni)
- **Ansiklopedi** (egzotikler, adlı eşyalar, setler, markalar, yetenekler; build'e ekle), **meta build vitrini**
  (etiketler, popülerlik, yükselenler, favoriler), **haberler ve sezon** (sıfırlama geri sayımı, etkinlikler, yama
  notları; günlük akış `meta/news_feed.json`) ve **bilgi yarışması** (sorular oyun kütüphanesinden, XP ve seviye).
- **Ajan sesi:** özgün taktik asistan cümleleri, 3 paket, 10 dil, isteğe bağlı telsiz efekti (`meta/voice_lines.json`).

### Hesap ve hizmet (yeni)
- **Hesap (isteğe bağlı):** 👤 Giriş yap → Discord ile giriş. Şifre yok; oturum bilgisayarda Windows şifrelemesiyle
  durur. Lisans anahtarı (`TD2K-…`), davet / hediye kodu (`TD2I-…`) ya da satın alma anahtarı tek kutudan kullanılır.
  Bir lisans bir bilgisayarda çalışır; premium 7 gün internetsiz geçerlidir.
- **🛰 Hizmet (Ayarlar):** oyun açılınca tarama kendiliğinden başlar, kapanınca durur ve oturum özeti kaydedilir;
  tepsi simgesi, Windows ile başlat. **Akıllı tarama** menü / saha / yükleme ekranlarını kendi öğrenir ve sahada
  boşuna okumaz. **Discord durumu** isteğe bağlı. Premium: **yerel API** (OBS kaplaması, Stream Deck, WebSocket) ve
  **telefon bildirimleri** (ntfy uygulaması ya da Discord webhook).

### Görevler
- Yalnızca **arayüz dilinde**, gruplu ve kısa: Journey görevleri, Manhunt scout'ları, Gizli Görevler,
  günlük/haftalık projeler. Farklı kaynaklardan gelen aynı görev tek satır görünür.
- **Çift tıkla** → ayrıntı penceresi: adım adım "nasıl yapılır", kaynak bağlantısı, tamamlandı düğmesi ve
  **The Division Wiki görselleri** (bir kez indirilip saklanır).
- **🤖 Claude ile getir (F10):** Claude Code internette (Ubisoft haberleri, yama notları, wiki) güncel
  görevleri arar ve senin dilinde ekler. Ayrıca ortak görev listesi ve canlı wiki her gün senkronize edilir.
- **➕ Ekle / ekrandan oku:** oyundaki Projeler ekranını okuyup çevirerek ekler.

### Asistan
Sohbet ve **sesli komut (F9)**. Ollama (yerel), Claude Code (abonelik), Claude API ya da OpenAI.
**🩺 Ses testi** mikrofonu ve konuşma tanımayı kontrol eder; hata ayrıntısı `logs\app.log`'a yazılır.
faster-whisper yoksa Windows'un kendi konuşma tanıması denenir.

### Ayarlar
Genel · **Efektler** · Tarama · **Ekran ve oyun** · **OCR** · Bindirme · Senkron · Kayıtlar.

- **Ekran ve oyun:** 240p'den 4K'ya çözünürlük profilleri (pencere ve yazılar ekrana göre ölçeklenir; değişince
  program ~2 sn'de yeniden açılır), oyun ayar dosyası kontrolü (yalnız okuma).
- **OCR:** motor seçimi (**RapidOCR** önerilen; Tesseract yedek), ölçek, çoklu geçiş (Tesseract'ta eşik ve PSM),
  **Otomatik ayarla**, canlı **Önizle** (RapidOCR'da bulunan satırları kutuyla gösterir).
  Gerçek kartlarla ölçüm (`tests/test_ocr.py`): RapidOCR 1440p/1080p/720p/480p'de tüm attribute'ları doğru okudu (8/8),
  Tesseract 3/8. 240p'de kart yazısı fiziksel olarak okunamayacak kadar küçük; pratik alt sınır 480p.
  Kartın rengi egzotik görünüyorsa program asla "KIR" demez.
- **Efektler:** özel fare imleci (genel nişangâh/silah siluetleri ya da kendi resmin), fare izi, menü geçişleri
  (hız ayarlı), **arka planda ajan saati** (tüm pencere; turuncu ışık fareyi takip eder) ve başlık videosu
  (program kendi özgün animasyonlarını üretir; "Videoları çoğalt" yenilerini ekler). Hepsi kapatılabilir.

## Ücretsiz ve premium

Okuma, build'ler, görevler, sandık ve aktif build optimize edicisi ücretsiz. Premium özellikler Ayarlar → **Premium**
sayfasında ve `features.py`'de listeli. Lisans anahtarı Ed25519 ile imzalı küçük bir belirteçtir, bilgisayarda doğrulanır
(internet gerekmez). Anahtarları yayıncı `scripts/license_tool.py` ile üretir; gizli anahtar `private/` klasöründe durur ve
asla git'e girmez. Hesapla gelen premium, sunucunun imzaladığı ve bilgisayara bağlı bir yetki belgesiyle açılır
(kurulum: `server/README.md` → Hesap sistemi). Program açık kaynak olduğu için premium asıl olarak sunucu tarafı özelliklerde (topluluk düşüş
istatistikleri, bulut eşitleme, satıcı bildirimleri) korunur.

## Oyun kütüphanesi

`meta/game_data.json`: tüm gear set'ler, markalar, named/egzotik eşyalar (yuvasıyla), silahlar (türüyle),
silah/ekipman talent'leri (göğüs/sırt ayrımıyla), ekipman ve silah modları, yetenekler, uzmanlık silahları ve
attribute'ların en yüksek değerleri. Program bununla ekipmanı silahtan, modlardan, kozmetiklerden ve uzmanlık
silahlarından ayırır; uzmanlık (expertise) bonuslarını attribute saymaz.
Kaynaklar: The Division Wiki ve mx-division-builds verisi (CC BY-NC-SA 4.0).

## Dosyalar

| Dosya / klasör | Ne |
|---|---|
| `app.py` | Arayüz ve uygulama |
| `engine.py` | Karar motoru, build planı, kart bulucu |
| `gamedata.py` | Eşya tanıma (oyun verisiyle) |
| `ocr_backend.py` | OCR motorları (RapidOCR / Tesseract), simge ve nadirlik renk ipuçları |
| `stash.py` | Sandık, denetim raporu, build optimize edici, kalibrasyon danışmanı |
| `vendor.py` | Haftalık satıcılar, hedefli loot, build eşleştirme |
| `companion.py` | Telefon arkadaşı (yerel, yalnız okunur web sayfası + QR) |
| `share.py` | Build paylaşım kodları |
| `dropstats.py` | Anonim düşüş istatistiği istemcisi |
| `server/` | Topluluk istatistik sunucusu (Cloudflare Worker + D1) |
| `features.py` | Ücretsiz/premium özellikler, lisans anahtarı doğrulama (Ed25519) |
| `tests/` | Gerçek kartlarla OCR testi (`tests/test_ocr.py`), lisans ve optimize edici testleri (`tests/test_core.py`) |
| `display.py` | Çözünürlük profilleri, oyun ayar dosyası okuyucu |
| `fx.py`, `bgvideo.py`, `view3d.py`, `ui_art.py`, `ui_theme.py` | Efektler, arka plan videoları, 3D, görseller, tema |
| `meta_sync.py`, `wiki_sync.py` | Günlük meta/görev senkronu, canlı wiki okuyucu |
| `i18n.py`, `lang/*.json` | Diller |
| `builds.json` | Ayarlar ve build'lerin |
| `progress.json`, `stash.json`, `tasks.json`, `loot_log.csv` | İlerleme, sandık, görevler, tarama geçmişi |
| `private/` | Yalnız yayıncıda: lisans gizli anahtarı (git'e girmez, yedekle) |
| `logs/app.log` | Günlük (sorun olursa buna bak) |
| `art/` | Arka planlar, amblemler, imleçler, videolar |

## Yeni dil eklemek

`lang/en.json`'u kopyala, değerleri çevir, `lang/<kod>.json` olarak kaydet. Program bir sonraki açılışta bulur.
Kayıtlı build, görev ve ilerleme sabit kimliklerle tutulduğu için dil değiştirmek hiçbir şeyi kaybettirmez.

## Sorun çözme

| Sorun | Çözüm |
|---|---|
| Eşya yanlış okunuyor | Oyun İngilizce mi, HDR kapalı mı? Ayarlar → OCR → **Otomatik ayarla**, sonra **Önizle**. |
| Kartın bir kısmı okunmuyor | Kartı kaydırıp ikinci kez F8 — okumalar birleşir. |
| "Bu bir eşya kartı değil" | Menü/harita ekranı okunmuş; eşyanın üstüne gelip tekrar dene. |
| Sesli komut çalışmıyor | Programı run.bat ile aç; Asistan → **🩺 Ses testi**; ayrıntı `logs\app.log`. |
| Arka plan videosu/saat yok | Ayarlar → Efektler'de açık mı? Ajan saati Windows ve koyu temada çalışır. |
| Bindirme görünmüyor | Oyunu kenarlıksız pencerede çalıştır (tam ekranda Windows gizleyebilir). |
| Tesseract bulunamadı | RapidOCR kuruluysa gerekmez (Ayarlar → OCR → motor). Değilse run.bat ile aç ya da Tesseract yolunu gir. |

## Lisans

MIT (`LICENSE`). Oyun verisinin bir kısmı CC BY-NC-SA 4.0 (mx-division-builds) ve CC BY-SA (The Division Wiki) lisanslıdır.
The Division ve ilgili adlar Ubisoft'a aittir; bu proje Ubisoft ile bağlantılı değildir.


### Kararlılık ve performans geliştirmeleri (yerel kaynak sürümü)

Dengeli profil varsayılandır; başlıktaki performans düğmesiyle Oyun öncelikli profile geçilir. Bu profil otomatik OCR deneme sayısını ve tarama sıklığını azaltır. Elle tarama ayarları korunur. Oyun öndeyken veya pencere küçültülmüşken arka plan animasyonları bekler. GPU seçimi otomatik değiştirilmez; oyun içindeki etkisi ayrıca ölçülmelidir.

Eksik veya geçersiz OCR sonucu incelemeye yönlendirilir. Exotic, Named ve Prototype eşyalar değerlendirme, ilerleme ve depo denetimi yollarında KIR sonucuna düşmez. Çeviri işleri bir etkin ve en fazla bir güncel bekleyen işle sınırlandırılır; eski isteklerin sonuçları arayüze uygulanmaz. Çeviride sayı ve oyun terimi kaybı doğrulanır; hatalı çıktı önbelleğe alınmaz.

Yeni ayarlarda yerel çeviri kullanılır. Mevcut kullanıcı ayarları korunur. Çevrimiçi AI seçimi veri aktarımını açıklayan onay gösterir; ses tanıma yereldir fakat seçilen çeviri sağlayıcısı metni çevrimiçi alabilir. Çeviri metni günlüğü ve OCR hata ayıklama görüntüsü yeni ayarlarda kapalıdır. Ölçüm düğmesi sınırlı sayıda süre örneği ve iş kuyruğu durumunu gösterir.

Kaynak koddan başlatma: `scripts\run.bat`. Kurulu bağımlılıklar değişmemişse normal açılışta pip çalışmaz. `scripts\run.bat --check` kurulum yapmadan gerekli modülleri denetler; `--repair` gereksinimleri yeniden kurar; `--extras` isteğe bağlı ses/video paketlerini kurar. Test için `python -m pip install -r requirements-dev.txt` kullanılabilir.

Bu geliştirmeler 6.0.2 sürümüne dahildir. Test kapsamı ve sınırlar: [yerel doğrulama raporu](docs/stability-6.0.2.md). Gerçek 8 GB bilgisayarda ve oyun açıkken FPS/GPU ölçümü ayrıca gereklidir.


### Yerinde çeviri ve doğal ses: 6.0.3

Yerinde çevirinin satır konumlarını koruyan düzeltmeler, iki hazır Türkçe/İngilizce Neural bildirim paketi ve isteğe bağlı çevrimiçi doğal ses eklendi. Bu değişiklikler 6.0.3 sürümüne dahildir. Kullanım, veri aktarımı ve doğrulama: [6.0.3 notları](docs/overlay_voice_local.md).


### 9.0.8: Android telefon arkadaşı ve QR eşleştirme

Android beta APK'sı görev, haber ve yerel build özelliklerine ek olarak Windows programındaki Telefon Arkadaşı QR kodunu tarayıp aynı güvenilir Wi-Fi üzerinden son eşya kararı ve build durumunu salt okunur gösterir. Telefon uzaktan tarama/ayar komutu göndermez. Bu sürüm ayrıca Agent saati açılış animasyonunu içerir. APK, Windows kurulum/taşınabilir paketleri ve SHA-256 listesi GitHub Release'e eklenir. Ayrıntılar: [Telefon-bağlantı kılavuzu](docs/mobile_companion_connection_tr.md).

### 9.0.7: canlı çeviride özel ad ve zamir doğruluğu

Hikâye ve dünya özel adları kaynaklarıyla birlikte sözlüğe eklendi ve canlı çeviride korunuyor. Zamirler maskelenmeden, gönderme yaptığı kişi ve tekil/çoğul anlamı korunarak Türkçeye çevriliyor. Zamir içeren çok cümleli satırlar yerel motora birlikte gönderiliyor; eski çeviri önbelleği yeni kurallarla yenileniyor. Envanter OCR testinde RapidOCR yoksa eksik bağımlılık açıkça belirtiliyor; CI'da RapidOCR kuruluysa gerçek kart kontrolü devam ediyor.

### 9.0.6: genişletilmiş oyun kütüphanesi ve daha doğru eşya tanıma

9.0.5 sonrasında biriken eşya kütüphanesi ve OCR tanıma düzeltmeleri bu sürümde yayımlanıyor. Sabitlenmiş Div2Hub topluluk veri anlık görüntüsü ve mevcut kaynaklar birleştirilerek 898 ekipman kaydı, 379 silah indeksi kaydı, yetenek/mod ayrıntıları, 43 skill varyantı ve 9 Prototype Augment eklendi veya doğrulandı. Health Damage artık Health ile karıştırılmaz; sayı okuma, aksanlı ad normalizasyonu ve Perfect yetenek eşleştirmesi düzeltildi. Named/Exotic silahların sabit yetenekleri ve Prototype Augment'ler tarama/build akışında tanınır; build puanlaması yetenekleri yalnız uygun eşya türünde karşılaştırır. Ansiklopedi yetenek açıklamalarını gösterir ve gear set parçalarını yuva başına tekilleştirir. Excel kütüphanesi de bu ayrıntılarla yeniden üretildi. Kaynak atıfları depoda bulunur. Skill Modları için doğrulanmış tam katalog mevcut olmadığından bu sürüm eksik değer uydurmaz.

### 9.0.5: düzenli menüler, kısayollar ve Division 3 haberleri

Uygulamanın 14 sayfası altı ana grupta toplandı. Ayarlar dört başlık altında düzenlendi. Tüm uygulama kısayolları tuş yakalama ve çakışma kontrolüyle Ayarlar → Temel → Kısayollar alanından değiştirilebilir. Yeni Division 3 sayfası doğrulanmış Ubisoft bilgilerini gösterir ve mevcut resmî haber akışından yeni gelişmeleri izler. Görev eşitleme sayfasına resmî ve topluluk rehberi kaynakları eklendi.

### 9.0.4: oyun içi sesli asistan

F6 canlı çeviriyi durdurur/devam ettirir. F9 mikrofonu açar, tekrar basış soruyu gönderir; yanıt sesli okunur. F12 isteği ve sesi iptal eder. Kısayollar eşya taramasından bağımsızdır. İlk kullanımdan önce Asistan sekmesinden konuşma modelini hazırla ve AI sağlayıcısını yapılandır. Mikrofon sesi yerelde metne dönüşür; soru ve eşya/build bağlamı seçili sağlayıcıya iletilir. [Kurulum, veri aktarımı ve test kapsamı](docs/game_assistant_9.0.4.md).
