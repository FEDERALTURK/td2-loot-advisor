# Özellik Taraması ve Geliştirme Yol Haritası (2026-11-14)

**İstek:** Kullanıcı "yeni özellikler ve gereksiz özellikleri çıkaralım, ekran okuma ve
tanımlama/çeviri gibi özellikleri açıkça tanımla, programı geliştirme sürecini tamamlayacak bir
yol haritası oluşturalım" dedi. Bu belge o isteğin cevabı: (1) mevcut özellik envanterinin tanımlı
bir dökümü, (2) "ekran okuma" ve "tanımlama/çeviri"nin kod düzeyinde ne anlama geldiğinin açık
tarifi, (3) kaldırılması/sınırlandırılması önerilen kalemler, (4) kalan geliştirmeyi fazlara bölen
öncelik sırası. **Bu bir uygulama planıdır, kod değişikliği içermez** — her fazın onayı/sırası
kullanıcıya ait.

Mevcut, dağınık duran alt-yol-haritalarla çakışmamak için bu belge onları **tekrar etmez, referans
verir**: `docs/mobile_companion_roadmap.md`, `docs/console_capture_translation_roadmap.md`,
`docs/console_game_caption_roadmap.md`, `docs/game_assistant_9.0.4.md`. Genel proje durumu için
tek doğru kaynak hâlâ `ROADMAP.md`.

---

## 1. "Ekran okuma" ve "tanımlama/çeviri" — açık tanım

Kullanıcının bu iki kavramı özellikle adlandırmasının nedeni muhtemelen programda bunların **iki
farklı, birbirine bağlı olmayan boru hattı** olarak var olması ve isimlerinin kullanıcıya net
görünmemesi. Kod düzeyinde durum şu:

### 1.1 Ekran okuma (eşya tarama) — `ocr_backend.py` + `engine.py`
- **Ne okur:** Oyun içi eşya kartı (tooltip). F8'e basınca ekranın eşya kartı olan bölgesi
  bulunur (21:9/32:9 dahil), RapidOCR (PP-OCR, ONNX) ile çok-geçişli okunur; Tesseract yalnız
  yedek motor (Ayarlar → OCR'dan seçilebilir).
- **Ne üretir:** `(metin, kutu, güven)` üçlüleri → `engine.py`'nin karar mantığı → **sakla /
  düşün / kır / incele** kararı, aktif build'e göre.
- **Kapsam dışı:** Oyun belleği okunmaz (AGENTS.md madde 1); set/expertise bonus metinleri
  bilinçli olarak atlanır (sadece core/attribute/mod okunur).
- **Zaten tanımlı, iyi test edilmiş:** `tests/test_ocr.py` 1440p/1080p/720p/480p gerçek kartlarda
  ölçülmüş (8/8 RapidOCR vs 3/8 Tesseract, bkz. README "Scanning & decisions").

### 1.2 Tanımlama (eşleştirme) — `gamedata.py` + `knowledge.py`
- OCR'dan çıkan ham metin, oyunun tam veri kütüphanesiyle (`meta/game_data.json`,
  `meta/sources/wiki_*.json`) eşleştirilip eşyanın **gerçek kimliği** (hangi set, hangi marka,
  hangi talent, hangi exotic) çıkarılır. Bu adım olmadan "sakla/kır" kararı verilemez — ekran
  okuma yalnız ham metin üretir, tanımlama o metni oyunun bilgi tabanına bağlar.

### 1.3 Çeviri — üç AYRI alt-sistem (kullanıcıya bunu açıkça ayırmak gerekiyor)
1. **Arayüz çevirisi (i18n, `i18n.py` + `lang/*.json`)** — programın kendi menü/metinleri, 10
   dil, herkes kendi dilini ekleyebiliyor (proje açıklamasındaki "Şu an 10 dilde" ifadesinin
   kaynağı budur).
2. **Görev çevirisi (`wiki_sync.py` + Tasks sekmesi)** — oyun içi görevler kullanıcının arayüz
   diline çevrilip gösteriliyor, The Division Wiki'den görsellerle birlikte.
3. **Canlı çeviri (`livetranslate.py`, F6, "Live translation" sekmesi)** — bu, 1.1'deki eşya
   taramasından **tamamen bağımsız** bir OCR+çeviri boru hattı: ekranın (genelde diyalog/altyazı
   bölgesinin) herhangi bir yerini sürekli okur, yerel OPUS-MT/CTranslate2 modeliyle çevirir
   (model ilk kullanımda indirilir, ~150-250 MB, SHA-256 doğrulanır), oyunun üstüne overlay
   olarak basar. Proper-noun/zamir koruması, glossary, sahne bazlı önbellek gibi oldukça olgun
   bir mantığı var (bkz. `BUGS.md`/`CHANGELOG` 9.0.7 notu). **Bu motor TD2'ye özel değil** —
   `docs/console_capture_translation_roadmap.md`'nin net ettiği gibi, konsol/capture-card
   entegrasyonu bu motora sadece yeni bir görüntü kaynağı eklemek anlamına gelir, OCR/çeviri
   tarafında sıfırdan iş yoktur.

**Sonuç:** "Ekran okuma" tek bir şey değil — eşya tarama (1.1) ile canlı çeviri (1.3) aynı OCR
altyapısını (RapidOCR) paylaşır ama tamamen ayrı tetiklenir (F8 vs F6) ve ayrı amaçlara hizmet
eder. Kullanıcıya dönük dokümantasyonda (README, Ayarlar sekmesi) bu ikisinin isimlerinin
("Eşya Tarama" / "Canlı Çeviri") birbirine karışmaması önerilir — şu an isimler zaten ayrı ama
README'de ikisi farklı başlıklar altında (bkz. "Scanning & decisions" vs sürüm notu 9.0.3/9.0.7)
anlatılıyor, tek bir "Özellikler" tablosunda yan yana görünmüyor.

---

## 2. Mevcut özellik envanteri (gruplu, `features.py` tier'leriyle)

| Grup | Özellikler | Tier |
|---|---|---|
| Çekirdek tarama | `scan`, `smart_scan` | free |
| Build | `builds`, `optimizer` | free |
| Build (gelişmiş) | `optimizer_all` (sandığa göre tüm build'ler sıralı) | premium |
| Sandık | `stash`, `recal_advisor` | free |
| Sandık (gelişmiş) | `stash_export` (CSV/HTML) | premium |
| Topluluk veri | `drop_stats_share` (gönderme) | free |
| Topluluk veri (gelişmiş) | `drop_stats_view` (görüntüleme) | premium |
| Satıcı | `vendor_watch` | premium |
| Telefon | `companion` (yerel web+QR), `local_api` (WebSocket) | premium |
| Bildirim | `push_notify` | premium |
| Oyun servisi | `game_service`, `discord_presence` | free |
| Görevler | `tasks` | free |
| **Henüz yapım aşamasında** | `cloud_sync` (`COMING` kümesinde, arayüzde "yakında") | premium |

13 sekme (`lang/en.json`'daki `tab.*` anahtarlarından): Panel, Builds, Missing pieces, Statistics,
Projects (Tasks), Assistant, Settings, History, Log, Help, About, Stash, Knowledge,
Live translation.

---

## 3. Kaldırılması / sınırlandırılması önerilen kalemler

Bu oturumda kod tabanında **doğrudan "gereksiz" olduğu kanıtlanmış** bir özellik bulunmadı — proje
zaten disiplinli bir geçmişe sahip (örn. birden fazla tema eklenip sonra hepsi kaldırıldı, bkz.
`BUGS.md` #14/#15; bu bir kendi-kendini-düzeltme örneği, tekrarlanan bir hata değil). Bulunan
somut riskler, "kaldır" değil "netleştir/birleştir" kategorisinde:

1. **Üç ayrı, örtüşen konsol/Xbox girişimi var — kullanıcı önceliklendirmesi gerekiyor.**
   - (a) `xbox-companion/` — statik UWP referans uygulaması (pakete gömülü görev çevirisi + build
     özeti, canlı tarama YOK). CI bugün (2026-11-14) nihayet yeşile çekildi.
   - (b) Mobil companion'daki "Xbox doğrudan bağlantı" (Faz 3a) — XStreaming tabanlı, gerçek
     ekran/ses akışı henüz yazılmadı, hiç gerçek Microsoft hesabıyla denenmedi.
   - (c) `docs/console_capture_translation_roadmap.md` — capture card + `livetranslate.py` ile
     genel konsol ekranı çevirisi; sadece araştırma, kod yok, kullanıcının fiziksel capture card
     edinmesi gerekiyor.
   Üçü de "Xbox/konsol" başlığı altında ama farklı sorunları çözüyor (statik referans vs canlı
   bağlantı vs canlı çeviri). Kullanıcı hangisinin (varsa) gerçekten istenen deneyim olduğunu
   netleştirmeden üçünde paralel ilerlemek kaynak dağıtır. **Öneri: Faz 1'de bir karar maddesi
   olarak ele alınsın (bkz. §4).**
2. **`cloud_sync` arayüzde "yakında" görünüyor ama hiç kod yazılmamış.** Kullanıcıya görünen bir
   vaat var ama sırası hâlâ belirsiz — ya yol haritasına somut bir faz olarak girsin ya da
   "yakında" etiketi şimdilik arayüzden çekilsin (beklenti yönetimi, kod değişikliği küçük).
3. **Görsel doğrulaması hiç yapılmamış 6 özellik birikmiş** (`BUGS.md` #11-16: oturum özeti, build
   karşılaştır, "karar yanlıştı" geri bildirimi, kaivolt tema→kaldırıldı, yeni tema/şema, üst
   menü+dijital yağmur+radar). Bunlar "gereksiz" değil ama doğrulanana kadar üstüne yeni UI
   eklemek riski büyütür — **Faz 0'da tek seferlik bir gözle-kontrol turu** öneriliyor.

---

## 4. Yol haritası (fazlar, öncelik sırasıyla)

### Faz 0 — Temizlik ve sağlamlaştırma (yeni özellikten önce)
- `tests/test_knowledge.py`'deki canlı-veriye-bağımlı `KeyError` fixture'ını düzelt (kök neden
  bulundu, `ROADMAP.md`'de belgeli, düşük riskli — tek dosya, test kodu).
- PR #3'ü (`fix/desc-offline-fallback`, `dirty`) rebase et veya kapat.
- `BUGS.md` #11-16'daki 6 özelliği kullanıcı Windows'ta tek seferde gözden geçirsin (liste zaten
  BUGS.md'de var, tekrar üretmeye gerek yok).
- Kod imzalama kararı (SignPath yeniden başvuru / Azure Trusted Signing / imzasız devam) —
  `ROADMAP.md` "Diğer açık kalemler"de zaten bekliyor, bu faza taşınabilir.

### Faz 1 — Konsol/Xbox stratejisi kararı
- §3.1'deki üç girişimden hangisine öncelik verileceğine kullanıcı karar versin: statik referans
  uygulaması (a) zaten CI'de yeşil ve en az riskli; canlı bağlantı (b) gerçek Xbox gerektiriyor;
  capture-card çevirisi (c) ek donanım gerektiriyor. Üçünü de paralel sürdürmek yerine birini ana
  hat, kalanını "beklemede" olarak işaretlemek önerilir.

### Faz 2 — Mobil companion'ı tamamla
- Push bildirimi uçtan uca gerçek cihazda test (Android canlı, iOS kod hazır/APNs secret bekliyor).
- Android/iOS gerçek cihaz kabul testi → Play Store / TestFlight hazırlığı.
- (Faz 1 kararına bağlı olarak) Xbox doğrudan bağlantının gerçek hesapla ilk denemesi.

### Faz 3 — Ekran okuma / tanımlama / çeviri derinleştirme
Mevcut üç boru hattı (§1.1-1.3) zaten olgun; önerilen artımlı iyileştirmeler:
- OCR güven eşiği ve "Read with Claude" devreye girme oranının (ne kadar sık düşük-güven fallback
  tetikleniyor) Tanılama Merkezi'nde görünür bir sayaç olarak gösterilmesi — şu an sessizce
  gerçekleşiyor, kullanıcı OCR kalitesini ölçemiyor.
- Çoklu monitör / 21:9-32:9 dışı en-boy oranlarının (örn. dikey/triple monitor) gerçek testinin
  teyit edilmesi — kod "destekler" diyor ama gerçek donanımda geniş test yok.
- `cloud_sync` için ya somut bir alt-faz açılsın ya da "yakında" etiketi kaldırılsın (§3.2).

### Faz 4 — Topluluk/veri katmanı büyütme
- `drop_stats_view`/`vendor_watch` kapsamını (hangi aktiviteler, hangi community kaynaklar)
  büyütmek — şu an hi-dep Division 2 Database'e bağımlı, tek kaynak riski var.
- Sürüm sayacı ve topluluk görev akışı (`meta/tasks_feed.json`) için basit bir kullanım
  panosu (kaç aktif kurulum, hangi sürümler) — zaten sunucu tarafında veri toplanıyor, görünür
  hâle getirilmedi.

### Faz 5 — Yayın altyapısı
- Kod imzalama (Faz 0'dan devam) kalıcı çözüm bulunca otomatik güncelleme akışına entegre.
- CI'deki bilinen kırmızı/kırılgan testlerin (Faz 0) sıfırlanması, yeni özellik eklerken regresyon
  riskini düşürür.

---

## 5. Not: bu belgenin kapsamı dışında bırakılanlar

- **Codex devir belgesindeki yerel Android imzalama senkronizasyonu** — bu, bir "yeni özellik"
  değil, iki çalışma kolunun (bulut klonu vs kullanıcının yerel Windows klasörü) birleştirilmesi
  sorunu. `ROADMAP.md` → "Diğer açık kalemler"de ayrı bir madde olarak takip ediliyor, kullanıcı
  yönü bekliyor.
- Bu belge yeni kod yazmadı; her faz kullanıcı onayıyla ayrı bir oturumda ele alınmalı (AGENTS.md
  standart iş akışı: plan → en küçük güvenli değişiklik → test → rapor).
