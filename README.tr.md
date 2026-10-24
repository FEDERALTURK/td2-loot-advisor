# TD2 Loot Advisor v5

The Division 2 için masaüstü eşya, build ve görev asistanı.

Ekrandaki eşya tooltip'ini okur, senin build kurallarınla karşılaştırır ve
**SAKLA / DÜŞÜN / KIR / KONTROL ET** kararını oyunun üstünde gösterir.
Ayrıca eksik build parçalarını takip eder, loot istatistiği tutar, görevleri
Türkçeye çevirip listeler ve sesli asistan olarak çalışır.

---

## Önce bunu oku: ne yapar, ne yapmaz

| | |
|---|---|
| **Yapmaz** | Oyunun belleğini okumaz, offset kullanmaz, oyuna kod enjekte etmez, oyun sürecine bağlanmaz. |
| **Yapar** | Ekran görüntüsü alır, içindeki yazıyı OCR ile okur, kendi penceresinde karar gösterir. |

Projenin başında elinde offset dosyaları vardı ve onlarla bellek okuyan bir
script istemiştin. O yol hile yazılımı sayılır: Ubisoft'un kullanım şartlarını
ihlal eder ve hesabın kalıcı olarak banlanabilir. Bu yüzden proje en baştan
**ekran okuma (OCR)** yoluyla kuruldu.

Buna rağmen **riski sıfır varsayma**: program global klavye dinler, sürekli
ekran yakalar ve (istersen) başka bir uygulamaya senin yerine yazar. Bunların
Ubisoft tarafından nasıl değerlendirileceğine dair bir garanti verilemez.

---

## Klasör yapısı

```
Thedivision2program/
├── app.py              ← uygulamanın kendisi (buradan çalışır)
├── i18n.py             ← çeviri motoru
├── ui_theme.py         ← tema, renkler ve arayüz sesleri
├── ui_art.py           ← üst bant: arka planlar, build amblemleri, bayraklar
├── meta_sync.py        ← günlük meta build + görev senkronu
├── engine.py           ← karar motoru v2 + eşya kartı bulucu (21:9 dahil)
├── gamedata.py         ← oyun verisi + eşya tanıma motoru
├── wiki_sync.py        ← The Division Wiki canlı okuyucu (sezon, Manhunt, Classified Assignment)
├── meta/               ← meta_builds.json (merkezi akış) + UPDATER.md (güncelleme kuralları)
├── art/                ← görseller (ilk açılışta oluşur; kendi görsellerini ekleyebilirsin)
├── builds.json         ← build kuralları + ayarlar
├── requirements.txt    ← temel Python paketleri (zorunlu)
├── requirements-voice.txt ← ses paketleri (opsiyonel)
├── README.md
├── lang/               ← DİL DOSYALARI (10 dil)
│   ├── en.json  tr.json  de.json  fr.json  es.json
│   └── it.json  pt.json  ru.json  pl.json  nl.json
└── scripts/            ← BAŞLATMA / DERLEME BETİKLERİ
    ├── run.bat         ← paketleri kurar, uygulamayı açar
    ├── build_exe.bat   ← .exe üretir
    └── install_claude_code.bat ← asistan için Claude Code'u kurar ve giriş yaptırır (isteğe bağlı)
```

`app.py`, `i18n.py` ve `builds.json` kasıtlı olarak kök klasörde duruyor: uygulama
`lang/` klasörünü ve çalışırken oluşturduğu dosyaları (`progress.json`,
`logs/` vb.) kendi bulunduğu klasöre göre arar. Betikler `scripts/` içinden
çalışsa da önce kök klasöre geçtikleri için yolları bozulmaz.

---

## Diller / Languages

Arayüz **10 dilde** geliyor: English, Türkçe, Deutsch, Français, Español,
Italiano, Português, Русский, Polski, Nederlands.

Dil **Ayarlar → Dil** bölümünden seçilir. İlk açılışta işletim sisteminin dili
tahmin edilir, karşılığı yoksa İngilizce kullanılır. Dil değişikliği **anında** uygulanır
(yeniden başlatma yok) ve üst bantta 5 saniye o dilin bayrağı görünür.

**Yeni bir dil eklemek** (kod bilmeden):

1. `lang/en.json` dosyasını kopyala.
2. Sadece `:` işaretinin **sağındaki** değerleri çevir. Soldaki anahtarlara ve
   `{build}`, `{pct}` gibi süslü parantezli yer tutuculara **dokunma** — bunlar
   çalışma sırasında sayı ve isimle doluyor.
3. Dosyayı `lang/<kod>.json` olarak kaydet (örn. `sv.json`, `ja.json`,
   `pt-br.json`) ve `__meta__` içindeki `name` ile `english_name` alanlarını doldur.
4. Uygulamayı yeniden başlat; yeni dosya listede çıkar.

Bir anahtarı çevirmeden bırakırsan ya da unutursan, o satır İngilizceye düşer —
uygulama çökmez.

**İki isteğe bağlı alan:**

- `help.body` — Yardım sekmesinin uzun metni. Şu an sadece İngilizce ve
  Türkçe dosyalarda dolu; diğer dillerde İngilizcesi gösteriliyor.
- `__task_dict__` — yapay zeka yokken görev çevirisinde kullanılan
  İngilizce→kendi diline kelime sözlüğü. Yoksa metin olduğu gibi bırakılır
  (yanlış çeviri üretmektense orijinali göstermek daha dürüst).

> **Çeviriler hakkında dürüst not:** İngilizce ve Türkçe dışındaki diller
> benim tarafımdan çevrildi, ana dili konuşan biri tarafından gözden
> geçirilmedi. Garip duran bir ifade görürsen ilgili `lang/<kod>.json`
> dosyasını düzeltmen yeterli, kodu değiştirmen gerekmez.

---

## Hızlı başlangıç

1. **Python 3.10+** kur ([python.org](https://www.python.org/downloads/)) — kurulumda "Add Python to PATH" işaretli olsun.
2. **Tesseract OCR** kur: <https://github.com/UB-Mannheim/tesseract/wiki>
3. Proje klasörünü alt klasörleriyle (`lang/`, `scripts/`) birlikte bir yere koy ve
   **`scripts\run.bat`**'a çift tıkla. Gerekli paketler kendiliğinden kurulur ve
   uygulama açılır.
   - Önce temel paketler (`requirements.txt`) kurulur; bunlar olmadan uygulama açılmaz.
   - Sonra ses paketleri (`requirements-voice.txt`) tek tek denenir. Biri kurulamazsa
     (örn. çok yeni bir Python sürümünde `faster-whisper`) uygulama yine açılır, sadece
     o ses özelliği kapalı kalır. Kurulamayan paket `optional_skip.txt` dosyasına yazılır
     ve her açılışta tekrar denenmez; yeniden denemek için bu dosyayı sil.
   - Sesli komut (Whisper) için en sorunsuz sürüm Python 3.12 veya 3.13'tür. Bilgisayarda
     kuruluysa `run.bat` ve `build_exe.bat` önce 3.13'ü, sonra 3.12'yi kendiliğinden kullanır;
     yoksa varsayılan `python` ile devam eder. Hangi sürümün seçildiği pencerenin başında yazar.
4. Oyunu **İngilizce** ve **Borderless Windowed** modunda aç.
5. Panel sekmesi → **Bölge seç** → oyunda bir eşyanın üstüne gel → 5 saniye
   sonra donan ekranda tooltip'in etrafına kutu çiz. Bunu bir kere yapman yeterli.
6. **Başlat**'a bas. Artık eşyanın üstüne gelip **F8**'e bastığında karar çıkar.

### .exe yapmak istersen

`scripts\build_exe.bat`'ı çalıştır, sonuç kök klasördeki `dist` klasöründe çıkar.

- `builds.json` dosyası ve `lang` klasörü .exe ile **aynı klasörde** durmalı.
  (İlk açılışta .exe bunları kendi yanına çıkarır, ama elle kopyalamak daha güvenli.)
- Tesseract .exe'nin içinde gelmez, bilgisayarda ayrıca kurulu olmalı.
- Ses özellikleri (faster-whisper) .exe'yi yüzlerce MB büyütür ve bu derleme
  betiği test edilmedi. **En güvenli yol `scripts\run.bat` ile çalıştırmak.**
- Windows Defender imzasız .exe'ye yanlış alarm verebilir.

---

## Görünüm ve sesler

Arayüz varsayılan olarak **koyu temada** ve oyunun SHD turuncusuyla açılır: üstte durum
rozetleri, renkli ve ikonlu butonlar, büyük karar kartı ve oturum sayaç rozetleri.
**Ayarlar → Görünüm** bölümünden:

- **Tema:** Koyu (TD2 turuncu), Açık veya Klasik (eski görünüm). Kaydet'e basınca **anında** uygulanır;
  tarama durumu, sayaçlar ve asistan sohbeti korunur.
- **Arka plan değişim süresi:** üst banttaki Division havası arka planları bu aralıkla yumuşak
  geçişle değişir (varsayılan 15 sn, 0 = sabit).
- **Buton ve tıklama sesleri:** butonlara, sekmelere ve kutucuklara basınca kısa bir tık sesi;
  Başlat/Durdur'da ayrı sesler. Hemen açılıp kapanır.

Karar sesleri (SAKLA, KIR, KONTROL ET…) **Ayarlar → Tarama → Sesli uyarı** ile yönetilir
(sesli karar okuma açıksa onun yerine konuşma duyulur). Sesler ilk açılışta `sounds/`
klasörüne küçük WAV dosyaları olarak üretilir; görünüm kodu `ui_theme.py` içindedir ve ek
bir kütüphane gerektirmez.

### Üst bant: arka planlar, amblemler, bayraklar

- **Arka planlar:** ilk açılışta `art/backgrounds/` içine 5 özgün arka plan üretilir (şehir silüeti,
  altıgen ızgara, radar, topografya, duman). Klasöre kendi `.png`/`.jpg` görsellerini koyarsan
  onlar da döngüye girer.
- **Build amblemleri:** Build'ler sekmesinde bir build'e tıklayınca bantta 5 saniye o build'in amblemi
  görünür, sonra arka plana döner. Amblemler rolüne göre üretilir (DPS/Striker turuncu, Heartbreaker
  kırmızı nabız, tank mavi kalkan, skill turkuaz, yakın mesafe sarı, hassas atış yeşil nişangâh).
  Kendi görselini kullanmak için `art/emblems/<build adı>.png` koy.
- **Bayraklar:** dil seçince veya uygulayınca 5 saniye o dilin bayrağı görünür. Değiştirmek için
  `art/flags/<dil kodu>.png` (örn. `tr.png`).
- Resmî Ubisoft logoları ve set amblemleri telif hakkı nedeniyle pakete eklenmedi; görseller bu
  uygulama için özgün olarak çizildi. Klasörü **Ayarlar → Görünüm → Görsel klasörünü aç** ile açabilirsin.



## Panel, Build'ler ve Eksik Parça (v2) — geniş ekran (21:9, 3440×1440) desteği

- **Panel:** iki sütun. Solda kontroller, büyük karar kartı ve **okunan eşya kartının küçük resmi** (programın
  gerçekte neyi okuduğunu görürsün); sağda eşya tablosu (özellik · değer · oyundaki max · kalite çubuğu),
  set/marka + talent'ler, tanıma güveni ve **build eşleşmeleri** tablosu (puan + nedenleri).
- **Kaynak: Tüm ekran (önerilen)** — bölge seçmeden çalışır. Program 3440×1440 dahil her çözünürlükte eşya kartını
  ekranda kendisi bulur (Core Stats / Attributes / Talents hizasından), sınırlarını hatırlar; kart yer değiştirirse
  yeniden bulur. İstersen *Seçili bölge* moduna geçebilirsin.
- **Karar motoru v2** (`engine.py`): ekipmanda set/marka eşleşmesi (başka set/marka ise puan düşer), attribute'lar
  oyundaki en yüksek değere göre, talent; **silahlarda** silah türü (build adından tahmin ya da build'de seçilen tür)
  + silah talent'i + rulolar. Egzotik/named eşya build'inde geçiyorsa **SAKLA**, geçmiyorsa açıklamalı **KONTROL ET**.
- **Build'ler:** set/marka ve talent'ler oyun verisinden seçilir (yazım hatası olmaz), attribute eklerken oyundaki
  max ve önerilen "iyi değer" (%90) otomatik gelir, yuvalar onay kutusu, **silah türleri** seçilebilir,
  *Son taranan eşyayla test et* ile build'in o eşyaya verdiği puan ve nedenleri görülür; arama ve çoğaltma var.
- **Eksik Parça:** seçili build'in 8 yuvası (6 zırh + silah + tabanca) kart olarak; dolu kartta parça, set/marka,
  puan, tarih ve rulolar (kalite %), boş kartta neyin arandığı (set/marka ya da silah türü + öncelikli özellikler).
  Her kartta *Son taramayı koy* / *Temizle*; altta tüm build'lerin eksik yuvaları.
- Teşhis için her taramada `last_card.png` (okunan kart) ve `logs/last_ocr.txt` (okunan metin) kaydedilir.

## Eşya tanıma: oyun verisiyle doğrulama

Ekran okuma (OCR) tek başına gürültülüdür. Program okunan metni **gerçek oyun verisiyle** düzeltir
(`gamedata.py` + `meta/game_data.json`, kaynak: The Division Wiki):

- **Bilinen adlar:** tüm gear set'ler, marka setleri, egzotikler ve named eşyalar → bozuk okunan ad en yakın gerçek
  ada eşlenir (ör. "Strikers Gtoves" → *Striker's Battlegear*, eldiven).
- **Talent'ler** (silah + ekipman, *Perfect* sürümleri dahil) ve **attribute'lar**; her attribute oyundaki
  **en yüksek değere göre yüzde** olarak gösterilir (Critical Hit Chance en fazla %6, Weapon Damage %15,
  Armor 170.370; Prototype ×1,5). Panelde "📊 Rulo" satırı.
- **Tür ve yuva:** silah/ekipman, Mask/Chest/Backpack/Gloves/Holster/Kneepads, Weapon/Sidearm.
- **Kart bulma:** seçilen bölge envanter listesini de içeriyorsa program eşya kartını (Core Stats / Attributes /
  Talents başlıklarından) kendisi bulup sadece onu okur; konumu hatırlar.
- **Kendi penceresini okumaz:** tarama başlarken program penceresi bölgenin üstündeyse küçülür; bildirim kartı
  bölgenin dışındaki bir köşeye konur.
- Oyun verisi ortak listeden (GitHub) günlük güncellenir; oyunun belleğine dokunulmaz.

## Meta build senkronu (günlük, otomatik)

Uygulama herkese açık olduğu için meta listesi **tek bir merkezde** tutulur: GitHub deposundaki
`meta/meta_builds.json`. Bu dosya her gün güncellenir; her kullanıcının programı açılıştan birkaç
saniye sonra, son denemeden bu yana 20 saat geçtiyse listeyi arka planda indirir.

- **Kendi build'lerine dokunulmaz.** Meta build'ler listede ⭐ ile, popülerlikleri 🔥 ile görünür.
- Bir meta build'i düzenleyip kaydedersen 🔒 kilitlenir; senkron artık onu değiştirmez.
- Sildiğin meta build bir daha eklenmez (Ayarlar → Meta → *Gizlenen meta build'leri geri getir*).
- İnternet yoksa son indirilen kopya (`meta_cache.json`) kullanılır; açılış beklemez.
- Güvenlik: yalnızca HTTPS, en fazla 512 KB, bilinmeyen alanlar ve attribute'lar atılır.
  Ana adres olmazsa jsDelivr CDN yedeğine geçilir.
- **Ayarlar → Meta build senkronu:** aç/kapat, *şimdi senkronize et*, istersen kendi akış adresin
  (topluluk veya klan listesi gibi).
- Popülerlik (0-100): kaç bağımsız kaynakta geçtiği, herkese açık etkileşim (görüntülenme/oy) ve
  güncellik. Akışın nasıl güncellendiği `meta/UPDATER.md` içinde yazılı.


### Ortak görev listesi ve "Nasıl yapılır"

- **Görevler** sekmesi açılışta (günde bir) ve her oyun sıfırlamasından sonra `meta/tasks_feed.json`'u indirir:
  oyundaki menülerle aynı üç kategori: **Projeler** (Günlük / Haftalık / Yerleşim / Sezonluk), **Journey** (sezon yolculuğu, Classified Assignment) ve **Manhunt** — hepsi senin dilinde (🌐).
- Bir göreve tıklayınca altında **💡 Nasıl yapılır** paneli açılır (nerede, hangi ayarla, püf noktaları) ve
  **Kaynağı aç** ile rehbere gidilir.
- **Günlük/haftalık projeler** herkese açık hiçbir sitede yayımlanmıyor; bu yüzden oyundaki Projeler ekranından
  okunur: kategoriden *Projeler – Günlük* veya *Projeler – Haftalık*ı seç → **📋 Proje ekranını oku**. Bölge bir kez seçilir, sonra tek tık. Okunan projeler
  çevrilir ve türüne uyan ipucu (kontrol noktası, bounty, Countdown, Summit, Dark Zone, bağış, kafa vuruşu,
  silah türü, yetenek, elit, Conflict…) otomatik eklenir.
- Sıfırlama saatleri oyunun resmî UTC saatinden senin saat dilimine otomatik çevrilir.


### 📚 Canlı Wiki okuyucu

- Program **The Division Wiki**'yi (thedivision.fandom.com) senin bilgisayarından, wiki'nin herkese açık
  veri arayüzüyle (MediaWiki API, anahtar gerekmez) günde bir okur — `wiki_sync.py`.
- Güncel sezon sayfasından çıkarılanlar: **Manhunt Scout'ları** (adı + ne yapılacağı), **Classified Assignment'lar**
  (açıklama, çıkış tarihi, ECHO / sırt çantası süsü bulmaca ipuçları) ve **tarihli sezon projeleri**
  ("Project Chain from … to …" → *Projeler – Sezonluk*, bitiş tarihinde kendiliğinden kalkar).
- Yeni sezon açılınca sezon kutusundaki `next=` bağlantısını izleyip yeni sayfaya kendiliğinden geçer.
- Ortak listede (🌐, 10 dilde) zaten ayrıntılı olan görevler wiki'den tekrar eklenmez; eksikler 📚 ile gelir.
- Wiki İngilizcedir; Asistan sekmesinde bir yapay zekâ (Claude Code, Ollama…) seçiliyse görevler ve
  ipuçları arka planda senin diline çevrilir. İçerik CC BY-SA; her görevde **Kaynağı aç** wiki bölümüne gider.
- Görevler sekmesi → *Ortak görev listesi* kutusu: **📚 Wiki'den güncelle**, otomatik okuma seçeneği ve
  **Wiki sayfasını aç**.

## Sekmeler

### Panel — tarama ve karar

İki tarama modu var:

| Mod | Nasıl çalışır | Ne zaman kullan |
|---|---|---|
| **Kısayol tuşu** | Eşyanın üstüne gel, F8'e bas. | Oyun oynarken, günlük kullanım. |
| **Otomatik** | Bölgeyi sürekli izler, tooltip oturunca kendiliğinden okur. Aynı eşyayı 30 sn içinde tekrarlamaz. | **Sadece envanter/depo açıkken.** Oynarken açık bırakma, boşuna OCR tetikler. |

Karar renkleri: yeşil **SAKLA**, sarı **DÜŞÜN**, kırmızı **KIR**, mavi **KONTROL ET**.
Exotic, Named ve Prototype eşyalarda asla "kır" demez, her zaman "kontrol et" der.

Ayrıca: "Şimdi tara" butonu ve "Ekran görüntüsünden test" (oyun kapalıyken OCR
metnini ve ayrıştırılan değerleri gösterir — sorun çözmek için en faydalı araç).

### Build'ler — kuralların

Her build için set/marka adı, attribute ağırlıkları, "iyi" sayılan değerler ve
talent'ler burada ayarlanır. Skorun kalitesi tamamen buraya girdiğin verilere bağlı.

- **Takip slotları** alanı boş bırakılırsa tüm slotlar takip edilir.
- **Dışa aktar / İçe aktar**: build'lerini tek bir `.json` dosyasına kaydedip
  yedekleyebilir ya da arkadaşına gönderebilirsin. İçe aktarırken aynı isimli
  build varsa üzerine yazmaz, sonuna `(2)` ekler.

> `builds.json` içindeki talent adları ve `good_at` değerleri **örnektir**.
> Oyundaki birebir İngilizce adlarla değiştirmen gerekiyor.

### Eksik Parça — build tamamlama

SAKLA denen ve slotu tespit edilen parçalar, en uyumlu build'in slotuna kaydedilir.

Slotlar: Mask, Backpack, Chest, Gloves, Holster, Kneepads, Weapon, Sidearm.

Bildirimde çıkan notlar:
- **EKSİK PARÇA DOLUYOR** — o slot boştu.
- **YÜKSELTME: 63% → 80%** — elindekinden daha iyi.
- **Elindeki daha iyi** — bu durumda SAKLA, DÜŞÜN'e düşürülür.

**Rulo karşılaştırması:** Kayıtlı bir parçayla kıyaslandığında Panel'de
attribute attribute fark gösterilir, örn. `weapon_damage: 11 → 15 (↑4.0)`.

*Sınır:* Tooltip'te "birincil/ikincil" yazmadığı için tabanca dışındaki tüm
silahlar tek bir **Weapon** slotunda toplanır.

### İstatistik

Dönem seçilir (bugün / 7 gün / 30 gün / tümü). Toplam tarama, SAKLA oranı,
ortalama skor, Exotic sayısı ve dört grafik: karar dağılımı, build bazlı SAKLA,
günlük tarama, slot dağılımı.

### Görevler — çeviri ve takip

Kategoriler oyundaki menülerle aynı: **Projeler** (Günlük / Haftalık / Yerleşim / Sezonluk), **Journey** ve **Manhunt**.
Eski sürümdeki Günlük/Haftalık görevler otomatik olarak *Projeler*'e taşınır.

**Görev eklemenin üç yolu:**

1. **Kopyala-yapıştır** — oyundaki İngilizce metni yapıştır, "Çevir ve ekle".
   Birden fazla satır = birden fazla görev.
2. **📷 Ekrandan oku** — oyunda açık olan görev ekranını OCR ile metin kutusuna aktarır. *En güvenilir yöntem.*
3. **ChatGPT'den otomatik getir** — aşağıda anlatılıyor.

**Çeviri kaynağı:** Asistan sekmesinde seçtiğin yapay zeka varsa onunla doğal
Türkçeye çevirir. Yoksa oyun terimlerine özel bir sözlükle kaba çeviri yapar ve
satırı `sözlük` diye işaretler — bu durumda cümle akışı bozuk olabilir,
İngilizce orijinaline de bak.

**Reset:** Günlük ve haftalık projeler sıfırlama saatinde kendiliğinden temizlenir. Saatler ortak listeden
oyunun resmî UTC saatine göre senin saat dilimine otomatik ayarlanır (Türkiye: günlük 11:00, haftalık Salı
11:00). Elle değiştirirsen otomatik ayar kapanır. Journey ve Manhunt sezon boyunca kalır.

#### ChatGPT otomasyonu (F10)

Bu, kurulu ChatGPT uygulamana **senin yerine yazıp Enter'a basan ve ekrandaki
yanıtı OCR ile okuyan bir klavye/pencere makrosudur**. API'ye bağlanmaz,
hesabına dokunmaz.

Kurulum: "Yanıt bölgesini seç" ile ChatGPT'nin cevap alanını bir kere işaretle.
Sonra F10'a bas → pencere öne gelir → istek yazılıp gönderilir → beklenir →
yanıt okunup `GÜNLÜK / HAFTALIK / JOURNEY / GLOBAL EVENT / MANHUNT`
başlıklarına göre kategorilere dağıtılır. Ham OCR metni altta kalır.

> ⚠️ **ChatGPT'nin "bugün aktif olan görevler" bilgisini gerçekten bilmesi
> garanti değil.** İnternete bakmıyorsa uydurabilir. Prompt'a "emin değilsen
> söyle" eklendi ama bu kesin koruma değil. Asıl görev listesi için
> **📷 Ekrandan oku** daha güvenilir; ChatGPT'yi "bunu nasıl yapayım" tarzı
> strateji sorularında kullan.

Ayarlanabilir: pencere başlığı, tuş, bekleme süresi, istek metni (`{tarih}`
otomatik dolar). Zamanlama tutmazsa "📖 Yanıtı şimdi oku" ile göndermeden okur.

### Log — uygulama günlüğü

Uygulamanın yaptığı her şey `logs/app.log` dosyasına yazılır: açılış, dil
seçimi, tarama sonuçları, kaydedilen parçalar, ayar değişiklikleri ve tüm
hatalar (tam yığın izleriyle).

- **Seviye filtresi:** sadece ERROR ya da WARNING satırlarını göster.
- **Farklı kaydet:** günlüğün bir kopyasını alır — yardım isterken eklenecek
  en iyi dosya budur.
- **Temizle:** günlüğü ve yedeklerini siler.
- **Ayarlar → Uygulama kaydı:** seviye (DEBUG/INFO/WARNING/ERROR), en büyük
  dosya boyutu ve saklanacak yedek sayısı. Dosya belirlenen boyutu aşınca
  kendiliğinden döner (`app.log.1`, `app.log.2`...), yani sınırsız büyümez.

Bir şey ters giderse ilk bakılacak yer burası.

### Asistan — ses ve sohbet

| Özellik | Açıklama |
|---|---|
| **Sesli karar** | "Sakla. Striker, yüzde 90. Eldiven. Eksik parça doluyor." Çevrimdışı. Windows'a Türkçe ses paketi (Tolga/Emel) kurulu olmalı. |
| **Sesli komut (F9)** | Bas, konuş, tekrar bas. Yerel Whisper yazıya çevirir. İlk kullanımda model indirilir. |
| **Sohbet** | Asistan build'lerini, kayıtlı/eksik parçalarını, son eşyayı ve geçmişi bilir. |

**Yapay zeka sağlayıcıları:**

| Sağlayıcı | İnternet | Maliyet | Not |
|---|---|---|---|
| Ollama (yerel) | Hayır | Ücretsiz | `ollama pull gemma3:12b`. Oyunla VRAM paylaşır. |
| Claude (abonelik, Claude Code) | Evet | Aboneliğin limitinden düşer | API anahtarı gerekmez. Pro/Max aboneliği ve bir kez `scripts\install_claude_code.bat` gerekir. Her soruda birkaç saniye açılış gecikmesi olur. |
| Claude API | Evet | Token başına | Anahtar gerekir. |
| ChatGPT API | Evet | Token başına | **ChatGPT Go aboneliği API anahtarı vermez**, platform.openai.com'dan ayrıca alınır. |
| Yerleşik | Hayır | Ücretsiz | Yapay zekasız; eksikler/istatistik/son eşya sorularını yanıtlar. |

Yapay zeka yanıt vermezse otomatik olarak yerleşik moda düşer.

**Claude (abonelik, Claude Code) nasıl çalışır?** Program, resmi `claude` komut satırı
aracını `claude -p` ile çağırır; giriş Claude Code içinde senin aboneliğinle yapılır, bu
program hiçbir giriş bilgisini okumaz ya da saklamaz. Araçlar kapalı çalışır (dosyaya veya
komuta dokunmaz), sadece cevap yazar. Bu yol **kişisel kullanım** içindir: Anthropic'in
kurallarına göre abonelik girişini başka araçlara aktarmak ya da başkalarına sunulan bir
ürünü aboneliğe bağlamak yasaktır. Programı başkalarıyla paylaşacaksan onlar için API
anahtarı ya da Ollama seçeneğini öner.

> 🔒 API anahtarları `builds.json`'a **düz metin** yazılır. Bu dosyayı kimseyle
> paylaşma, GitHub'a yükleme. Alternatif: `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`
> ortam değişkenlerini kullan.

---

## Sistem yükü (yaklaşık, ölçülmedi)

| Özellik | Yük |
|---|---|
| Kısayol tuşu modu | Boşta neredeyse sıfır, ~60-100 MB RAM |
| Otomatik mod | İşlemcinin ~%1-3'ü |
| Sesli okuma | Önemsiz |
| Sesli komut (Whisper) | ~0,5-1 GB RAM, çözerken birkaç saniye yoğun işlemci |
| Ollama gemma3:12b | ~8-9 GB VRAM — **oyunla birlikte 12 GB'a sığmayabilir** |
| Claude/ChatGPT API | Neredeyse sıfır, sadece internet trafiği |

**Oyunu akıcı tutan kurulum:** kısayol tuşu modu + sesli okuma + (gerekirse)
API tabanlı sohbet. Yerel büyük modeli ve otomatik modu oyun kapalıyken ya da
envanterdeyken kullan. Oyunla beraber yerel model çalıştıracaksan `gemma3:4b`
gibi küçük bir model seç.

---

## Dosyalar

**Projeyle gelen:**

| Dosya | Ne işe yarar |
|---|---|
| `app.py` | Uygulamanın tamamı |
| `builds.json` | Build kuralları + tüm ayarlar + API anahtarları |
| `i18n.py` | Çeviri motoru |
| `ui_theme.py` | Tema (koyu/açık/klasik), renkler ve arayüz sesleri |
| `ui_art.py` | Üst bant: dönen arka planlar, build amblemleri, bayraklar |
| `meta_sync.py` | Günlük meta build + görev senkronu (indir, doğrula, birleştir) |
| `wiki_sync.py` | The Division Wiki canlı okuyucu |
| `engine.py` | Karar motoru v2 ve ekranda eşya kartı bulma |
| `gamedata.py` | Oyun verisiyle eşya tanıma (ad, set, talent, rulo kalitesi) |
| `meta/game_data.json` | Oyun verisi sözlüğü (wiki + oyun değerleri) |
| `meta/meta_builds.json` | Merkezi meta akışı (depoda günlük güncellenir) |
| `meta_cache.json` | Son indirilen meta listesi (otomatik oluşur) |
| `art/` | Arka plan / amblem / bayrak görselleri (kullanıcı ekleyebilir) |
| `lang/*.json` | Dil dosyaları (10 dil) |
| `requirements.txt` | Temel Python paketleri (zorunlu) |
| `requirements-voice.txt` | Ses paketleri (opsiyonel) |
| `scripts/run.bat` | Paketleri kurar ve uygulamayı açar |
| `scripts/build_exe.bat` | .exe üretir |
| `scripts/install_claude_code.bat` | Claude Code'u kurar ve aboneliğinle giriş yaptırır (Asistan için, isteğe bağlı) |
| `README.md` | Bu dosya |

**Çalışırken oluşan** (kök klasörde):

| Dosya | İçerik |
|---|---|
| `progress.json` | Build slotlarına kaydedilen parçalar |
| `tasks.json` | Görev listeleri ve reset takibi |
| `loot_log.csv` | Tüm tarama geçmişi (İstatistik buradan okur) |
| `last_crop.png` | Son yakalanan görüntü — OCR hatalarını çözmek için bak |
| `logs/app.log` | Uygulama günlüğü (Log sekmesi buradan okur) |
| `sounds/*.wav` | Arayüz sesleri (ilk açılışta üretilir, silinirse yeniden oluşur) |

---

## Sorun çözme

| Belirti | Çözüm |
|---|---|
| "Tesseract bulunamadı" | Ayarlar → Tesseract yolunu "Gözat" ile seç. |
| Eşya yanlış okunuyor | `last_crop.png`'ye bak: kutu tooltip'i tam kapsıyor mu, yazı net mi? Gerekirse bölgeyi yeniden seç. |
| Her şey "KIR" çıkıyor | `builds.json`'daki talent adları oyundakilerle birebir aynı mı? Eşikleri Ayarlar'dan düşürmeyi dene. |
| Sesli okuma çalışmıyor | Windows'a Türkçe ses paketi kurulu mu? "🔊 Sesi dene" ile kontrol et. |
| Mikrofon hatası | `pip install sounddevice numpy` |
| Uygulama açılıp hemen kapanıyor | `scripts\run.bat` artık hata olunca pencereyi açık tutar; mesajı oku. Çoğunlukla temel paketlerden biri kurulamamıştır. |
| Sesli komut çalışmıyor | `faster-whisper` kurulamamış olabilir (`optional_skip.txt`'ye bak). Python 3.12/3.13 kullan, sonra bu dosyayı silip `run.bat`'ı yeniden çalıştır. |
| ChatGPT penceresi bulunamıyor | Uygulama açık mı, pencere başlığında "ChatGPT" geçiyor mu? |
| Otomatik mod oyunu yavaşlatıyor | Tarama aralığını artır (Ayarlar) ya da sadece envanterdeyken çalıştır. |
| Arayüz hâlâ eski dilde | Ayarlar → Dil'de **Uygula**'ya bastın mı? Seçmek tek başına yetmez. |
| Bazı yazılar İngilizce kalmış | O anahtar senin dil dosyanda yok; `lang/<kod>.json`'a ekle. |
| Dilim listede yok | `lang/en.json`'u kopyalayıp çevir, `lang/<kod>.json` olarak kaydet. |
| Dil listesi boş / hep İngilizce | `lang/` klasörü `app.py` ile aynı klasörde mi? Dil dosyalarını başka yere taşıma. |
| Bir şey çalışmıyor, sebebi belirsiz | Log sekmesini aç, seviyeyi ERROR yap, `logs/app.log`'a bak. |

---

## Geliştirme aşamaları

| Sürüm | Eklenenler |
|---|---|
| **Başlangıç** | Bellek/offset yolu reddedildi, OCR yaklaşımı seçildi. Tek dosyalık script: bölge kalibrasyonu, OCR, build skorlama, overlay, CSV log. |
| **v1** | Masaüstü uygulamaya dönüştü: sekmeli arayüz, görsel bölge seçimi, build editörü, ayarlar, geçmiş, .exe betiği. |
| **v2** | Tuşsuz otomatik tarama, eksik parça takibi, loot istatistikleri ve grafikler. |
| **v3** | Sesli karar okuma, sesli komut (Whisper), yerel (Ollama) ve internetli sohbet asistanı. |
| **v3.5** | Silah/tabanca slotu takibi, rulo karşılaştırması, build dışa/içe aktarma, ChatGPT API desteği. |
| **v4** | Görevler sekmesi: İngilizce→Türkçe çeviri, kategori bazlı takip, otomatik reset, ChatGPT pencere otomasyonu (F10). |
| **v5** | 10 dilli arayüz + Ayarlar'da dil seçimi, Log sekmesi ve dönen dosyalı günlük kayıt sistemi. Dosyalar `lang/` ve `scripts/` klasörlerine ayrıldı. |

## Sıradaki adımlar

1. **Önce gerçek oyunda test et.** Birkaç düzine eşya tara, yanlış okunanları not al.
2. `builds.json`'u oyundaki gerçek talent adlarıyla doldur — en büyük kalite kazancı burada.
3. Çevirilerde garip duran yerleri `lang/<kod>.json` içinde düzelt.
4. İstersek sonra: sistem tepsisine küçülme, Windows ile otomatik başlama,
   hazır build şablonları, asistanın görevleri de bilmesi, daha fazla dil
   (Japonca, Korece, Çince, İsveççe...).

---

*Bu araç Ubisoft veya Massive Entertainment ile ilişkili değildir.*
