# TD2 Loot Advisor — Türkçe kılavuz

*The Division 2* için ekran okuyan (OCR) yardımcı. Envanterde bir eşyanın üstüne gelip **F8**'e basarsın;
program kartı okur, oyunun eşya kütüphanesiyle doğrular, **aktif build'inle** karşılaştırır ve saniyeler
içinde **SAKLA / DÜŞÜN / KIR / KONTROL ET** der. Build'in eksik parçalarını takip eder, oyun görevlerini
senin dilinde gösterir. 10 dil; herkes kendi dilini ekleyebilir.

## Ne yapar, ne yapmaz

- ✅ Yalnızca **ekranı** okur (OCR) ve oyunun kendi **ayar dosyasını** (`state.cfg`) okur.
- ❌ Oyunun **belleğini okumaz/yazmaz**, oyun dosyalarını değiştirmez, oyuna tuş göndermez.
- ⚠️ Kararlar ekran okumaya dayanır; kritik eşyalarda karta bir göz at. Egzotikler hiçbir zaman "KIR" çıkmaz.

## Kurulum

1. **Python 3.13** (önerilen; 3.12 da olur) ve **Tesseract OCR** kur
   (UB Mannheim sürümü, varsayılan yol `C:\Program Files\Tesseract-OCR`).
2. Depoyu indir: **Code → Download ZIP**, bir klasöre çıkar.
3. **`scripts\run.bat`** ile başlat. İlk açılışta gerekli paketleri kurar; sesli komut ve video için
   isteğe bağlı paketleri (pyttsx3, sounddevice, faster-whisper, av) dener. Kurulamayan paket atlanır.
   > Programı her zaman run.bat ile aç: doğru Python sürümünü (3.13) seçer. app.py'ye çift tıklamak
   > bilgisayardaki en yeni Python'u kullanır; orada ses/video paketleri olmayabilir.
4. İsteğe bağlı: `scripts\build_exe.bat` tek dosyalık `.exe` üretir; `scripts\install_claude_code.bat`
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
- **OCR:** eşik, ölçek, PSM, çoklu geçiş, **Otomatik ayarla** (son kartta en iyi ayarı bulur), canlı **Önizle**.
- **Efektler:** özel fare imleci (genel nişangâh/silah siluetleri ya da kendi resmin), fare izi, menü geçişleri
  (hız ayarlı), **arka planda ajan saati** (tüm pencere; turuncu ışık fareyi takip eder) ve başlık videosu
  (program kendi özgün animasyonlarını üretir; "Videoları çoğalt" yenilerini ekler). Hepsi kapatılabilir.

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
| `display.py` | Çözünürlük profilleri, oyun ayar dosyası okuyucu |
| `fx.py`, `bgvideo.py`, `view3d.py`, `ui_art.py`, `ui_theme.py` | Efektler, arka plan videoları, 3D, görseller, tema |
| `meta_sync.py`, `wiki_sync.py` | Günlük meta/görev senkronu, canlı wiki okuyucu |
| `i18n.py`, `lang/*.json` | Diller |
| `builds.json` | Ayarlar ve build'lerin |
| `progress.json`, `tasks.json`, `loot_log.csv` | İlerleme, görevler, tarama geçmişi |
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
| Tesseract bulunamadı | Ayarlar → Tarama → Tesseract yolu. |

## Lisans

MIT (`LICENSE`). Oyun verisinin bir kısmı CC BY-NC-SA 4.0 (mx-division-builds) ve CC BY-SA (The Division Wiki) lisanslıdır.
The Division ve ilgili adlar Ubisoft'a aittir; bu proje Ubisoft ile bağlantılı değildir.
