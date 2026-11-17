# Kurulum ve Yerel Geliştirme Rehberi (VS Code)

Bu belge, projeyi temiz bir Windows makinesinde VS Code ile sıfırdan ayağa kaldırmak için gereken
her şeyi içerir: klasör yapısı, bağımlılıklar, çalıştırma komutları, ortam değişkenleri ve
**repoda bulunmayan, yerel olarak oluşturulması gereken gizli dosyalar.**

Proje dört ayrı bileşenden oluşuyor ve her birinin kurulumu bağımsızdır. Yalnız masaüstü
uygulamasıyla ilgileniyorsan **§3 yeterlidir**; mobil, sunucu ve web bileşenleri isteğe bağlıdır.

---

## 1. Kodun aktarımı — `git clone` kullan

Projenin boyutu (2026-11-15 itibarıyla ölçüldü):

| | |
|---|---|
| Takipli dosya | 976 |
| Kaynak kod satırı | 43.559 (`.py`/`.dart`/`.js`/`.cs`/`.xaml`) |
| Python modülü | 144 |
| En büyük tek dosya | `app.py` — 10.094 satır |
| Çalışma kopyası | ~414 MB (`meta/` altındaki 577 veri dosyası dahil) |

Bu hacim sohbete yapıştırılarak aktarılamaz — kesilir, satır sonları ve girintiler bozulur,
birleştirmesi saatler alır ve sonuçta çalışmayan bir kopya elde edilir. Depo zaten public olduğu
için doğru yöntem tek komut:

```powershell
cd C:\Users\PC\Desktop
git clone https://github.com/FEDERALTURK/td2-loot-advisor.git
code td2-loot-advisor
```

**Zaten yerel bir kopyan var:** `C:\Users\PC\Desktop\Thedivision2program`. Onu doğrudan açabilirsin:

```powershell
code C:\Users\PC\Desktop\Thedivision2program
```

> ⚠️ Ama önce şunu kontrol et: o klasör bu depodan **ayrışmış** durumda (bkz. `HANDOFF.md` → "⚠️"
> bölümü). İçinde buraya hiç push edilmemiş commit'ler (`6fea365` gibi) ve takip edilmeyen yerel
> dosyalar var. Yeni bir `git clone` yaparsan o işleri **görmezsin**. Hangisiyle devam edeceğine
> karar vermeden ikisini birden açıp çalışmaya başlama.

Git kullanmak istemiyorsan GitHub'dan ZIP de indirebilirsin
(`Code → Download ZIP`) — ama o zaman git geçmişi ve güncelleme imkânı olmaz.

### Önerilen VS Code eklentileri

```text
ms-python.python              (Python dil desteği + hata ayıklama)
ms-python.vscode-pylance      (tip denetimi, otomatik tamamlama)
Dart-Code.flutter             (mobile/ için — yalnız mobil geliştirecekse)
ms-vscode.powershell          (scripts/*.bat ve PowerShell komutları)
```

---

## 2. Klasör yapısı (ağaç şeması)

```text
td2-loot-advisor/
│
├── app.py                      ⭐ Ana Tkinter uygulaması + 14 sekme (10.094 satır — giriş noktası)
├── engine.py                   ⭐ Loot karar motoru (sakla / düşün / kır / incele)
├── gamedata.py                 Oyun veri kütüphanesi (set, marka, talent, exotic eşleştirme)
├── knowledge.py                Ansiklopedi / bilgi tabanı katmanı
├── itempolicy.py               Eşya koruma kuralları (exotic/named/prototype asla otomatik imha)
│
├── ── EKRAN OKUMA / OCR ──
├── capture.py                  Ekran yakalama (mss, 21:9 / 32:9 / DPI farkındalığı)
├── ocr_backend.py              ⭐ RapidOCR (birincil) + Tesseract (yedek) soyutlaması
├── winocr.py                   Windows.Media.Ocr yerel motoru
├── ocr_lab.py                  OCR doğruluk ölçüm/karşılaştırma aracı
├── screenstate.py              Oyun ekranı durum tespiti (envanter açık mı vb.)
│
├── ── CANLI ÇEVİRİ (F6, OCR'dan BAĞIMSIZ boru hattı) ──
├── livetranslate.py            ⭐ Yerel OPUS-MT / CTranslate2 çeviri motoru
├── overlay.py                  Oyun üstü şeffaf overlay (tıklama geçirgen olmalı)
├── translation_probe.py        Çeviri/overlay teşhis sondası
├── trscreen.py                 Çeviri ekran bölgesi seçimi
│
├── ── ARAYÜZ / TEMA ──
├── td2app/
│   ├── __init__.py
│   └── ui/                     ⭐ Görsel modüllerin GERÇEK yeri
│       ├── ui_theme.py         Kaivolt (lacivert/mor) HUD paleti — PALETTES
│       ├── ui_art.py           Çizim yardımcıları
│       ├── ui_hud.py           HUD bileşenleri
│       ├── fx.py               Efektler, SafeTrail fare izi (1.393 satır)
│       ├── view3d.py           3B görünüm (756 satır)
│       ├── bgvideo.py          Arka plan videosu
│       └── splash.py           Açılış animasyonu
├── fx.py, view3d.py, ui_art.py, ui_theme.py, ui_hud.py, bgvideo.py, splash.py
│                               ⚠️ Bunlar kökte duran UYUMLULUK KÖPRÜSÜ — sadece
│                               td2app/ui/* içindekileri yeniden dışa aktarır.
│                               Düzenlemen gereken yer td2app/ui/, kök dosyalar DEĞİL.
│
├── ── VERİ / SENKRONİZASYON ──
├── stash.py                    Sandık analizi
├── syncer.py                   Veri senkronizasyonu
├── wiki_sync.py                thedivision.fandom.com MediaWiki okuyucu
├── meta_sync.py                Meta build günlük senkronizasyonu
├── vendor.py                   Haftalık satıcı taraması
├── tasks_live.py               Canlı görev akışı
├── dropstats.py                Anonim topluluk drop istatistikleri
├── intelligence.py             Hedef/aktivite istihbaratı
├── target_planner.py           Target loot planlayıcı
├── decision_center.py          Komuta merkezi
├── review_queue.py             İnceleme kuyruğu (REVIEW kararları)
│
├── ── SERVİS / ALTYAPI ──
├── localapi.py                 Yerel WebSocket API (telefon companion için)
├── companion.py                Yerel ağ web sunucusu + QR eşleştirme
├── service.py                  Arka plan servisi
├── game_runtime.py             Oyun süreç/pencere takibi
├── gameinfo.py                 Oyun kurulum yolu/ayar okuma (SALT OKUNUR)
├── single.py                   Tek kopya mutex
├── workqueue.py                İş kuyruğu / thread yönetimi
├── safeio.py                   Güvenli dosya yazma (atomik, .bak)
├── winpath.py                  Windows yol yardımcıları
├── performance.py              Performans ölçümü
├── diagnostics_center.py       Tanılama merkezi
├── reports.py                  Hata raporlama (maskeli önizleme + onay)
├── updater.py / updates.py     Otomatik güncelleme
├── backup_bundle.py            Yedekleme paketi
│
├── ── HESAP / LİSANS / BİLDİRİM ──
├── features.py                 ⭐ Ed25519 imzalı lisans + free/premium özellik haritası
├── account.py                  Hesap yönetimi
├── terms.py                    Kullanım koşulları onayı
├── notify.py                   Bildirimler
├── presence.py                 Discord Rich Presence
├── share.py                    Build ↔ kısa kod paylaşımı (sunucusuz)
│
├── ── SES / GİRDİ ──
├── speech.py                   Sesli komut (faster-whisper)
├── voicepack.py                Ses paketleri
├── gamepad.py                  Oyun kumandası desteği
├── game_assistant.py           Oyun asistanı
├── agent_scene.py              Ajan sahnesi (3B)
│
├── ── ÇEVİRİ (ARAYÜZ) ──
├── i18n.py                     ⭐ 10 dilli arayüz çeviri motoru
├── lang/                       10 dil dosyası (de, en, es, fr, it, nl, pl, pt, ru, tr)
│   └── *.json                  Yeni dil eklemek = buraya yeni .json koymak
│
├── ── VERİ DOSYALARI ──
├── meta/                       577 dosya — oyun verisi, meta build'ler, wiki önbelleği,
│   ├── game_data.json          görev akışı, açıklama çevirileri
│   ├── meta_builds.json
│   ├── tasks_feed.json
│   └── sources/wiki_*.json
├── builds.json                 ⚠️ KULLANICI VERİSİ (takipte ama runtime'da değişir — commit etme)
│
├── ── MOBİL COMPANION (Flutter / Android + iOS) ──
├── mobile/
│   ├── pubspec.yaml
│   ├── lib/
│   │   ├── main.dart           (2.403 satır)
│   │   ├── services/
│   │   │   ├── cloud_api.dart          Sunucu API istemcisi
│   │   │   ├── cloud_link.dart         QR/bulut eşleştirme
│   │   │   ├── companion_release.dart  GitHub Releases'ten güncelleme kontrolü
│   │   │   ├── local_alerts.dart       Yerel bildirimler
│   │   │   └── push_registration.dart  FCM token kaydı
│   │   └── console/                    Konsol modu (kamera tabanlı altyazı çevirisi)
│   │       ├── console_caption_page.dart
│   │       ├── console_translate_service.dart
│   │       ├── tv_cast_service.dart
│   │       └── xbox/                   Xbox doğrudan bağlantı (XStreaming — TEST EDİLMEDİ)
│   │           ├── xbox_auth_service.dart
│   │           ├── xbox_console_service.dart
│   │           ├── xbox_crypto.dart
│   │           ├── xbox_login_page.dart
│   │           └── xbox_token_store.dart
│   ├── android/                        build.gradle.kts, AndroidManifest, FileProvider
│   ├── ios/
│   └── test/
│
├── ── SUNUCU (Cloudflare Workers + D1) ──
├── server/
│   ├── worker.js               Ana Worker (yönlendirme)
│   ├── accounts.js             Hesap/Discord girişi
│   ├── mobile.js               Push bildirimi (FCM + APNs)
│   ├── tasks.js                Görev akışı
│   ├── overview.js             Genel bakış
│   ├── schema.sql              D1 veritabanı şeması
│   ├── wrangler.toml           ⭐ Yapılandırma (secret'lar BURADA DEĞİL)
│   └── test_*.mjs              Node test betikleri
│
├── ── WEB SİTESİ (Cloudflare Pages) ──
├── web/                        https://td2-loot-advisor.pages.dev
│   ├── index.html
│   ├── account/ news/ premium/
│   └── assets/js/config.js     API_BASE, REPO, GUMROAD_URL
│
├── ── XBOX COMPANION (UWP — DENEYSEL) ──
├── xbox-companion/             Klasik UWP referans uygulaması (CI yeşil, gerçek Xbox'ta
│                               hiç test edilmedi)
│
├── ── TEST / BETİK / CI ──
├── tests/                      57 test dosyası (§6'ya bak)
├── scripts/
│   ├── run.bat                 ⭐ Uygulamayı başlatma
│   ├── build_exe.bat           PyInstaller EXE
│   ├── build_installer.bat     Windows installer
│   └── launch.py               Başlatıcı (bağımlılık denetimi)
├── .github/workflows/          17 CI workflow
├── TD2LootAdvisor.spec         PyInstaller yapılandırması
│
├── ── BAĞIMLILIK ──
├── requirements.txt            ⭐ Zorunlu paketler
├── requirements-voice.txt      Opsiyonel (ses, video, RapidOCR)
├── requirements-dev.txt        Geliştirme araçları
│
└── ── BELGELER ──
    ├── AGENTS.md               ⭐ AI ajan kuralları — ÖNCE BUNU OKU
    ├── HANDOFF.md              ⭐ Devir notu (güncel durum + ayrışma uyarısı)
    ├── ROADMAP.md              Genel durum (tek doğru kaynak)
    ├── BUGS.md                 Bilinen hatalar
    ├── TESTING.md              Test prosedürleri
    ├── DEPENDENCIES.md         Bağımlılık gerekçeleri
    ├── DEVELOPMENT_LOG.md      Değişiklik günlüğü
    ├── README.md / README.tr.md
    ├── PRIVACY_POLICY.md
    ├── LICENSE (MIT) / LICENSE_NOTES.md
    └── docs/                   18 ayrıntı belgesi (mobil imzalama, konsol yol haritaları vb.)
```

---

## 3. Masaüstü uygulaması (Python / Windows) — zorunlu kurulum

### 3.1 Gereksinimler

- **Windows 10/11** (uygulama Windows'a özgü: `winocr`, `pystray`, DPI/pencere API'leri)
- **Python 3.13** (birincil — tüm CI bunu kullanıyor). 3.12 de çalışır. Daha yeni sürümlerde
  `faster-whisper` kurulamayabilir, o zaman yalnız sesli komut devre dışı kalır.
- Opsiyonel: **Tesseract OCR** (yalnız yedek motor olarak kullanacaksan)

### 3.2 Kurulum

```powershell
cd C:\Users\PC\Desktop\td2-loot-advisor

# Sanal ortam (önerilir)
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Zorunlu paketler
python -m pip install --upgrade pip
pip install -r requirements.txt

# Önerilen: RapidOCR (çok daha doğru OCR) + ses/video
pip install -r requirements-voice.txt

# Geliştirme araçları (isteğe bağlı)
pip install -r requirements-dev.txt
```

> `sentencepiece==0.2.2` bilinçli olarak sabitlendi — 0.2.3 PyInstaller ile paketlendiğinde
> `DLL load failed` ile çöküyor (bkz. `BUGS.md` #17). Bu sabiti kaldırma.

### 3.3 Çalıştırma

```powershell
# En kolay yol — Python sürümünü kendi seçer, bağımlılıkları denetler
scripts\run.bat

# Opsiyonel ses/video paketlerini de kurarak
scripts\run.bat --extras

# Bağımlılıkları yeniden denetle/onar
scripts\run.bat --repair

# Doğrudan (sanal ortam etkinken)
python app.py
```

Hata olursa ayrıntı: `logs\app.log`

### 3.4 EXE / installer üretimi

```powershell
scripts\build_exe.bat          # PyInstaller → dist\
scripts\build_installer.bat    # Inno Setup → installer çıktısı
```

> ⚠️ Bunlar yalnız yerel derleme. Public yayın (GitHub Release / tag) için `AGENTS.md` madde 6
> gereği açık kullanıcı onayı şart.

---

## 4. Ortam değişkenleri (.env)

**Masaüstü uygulaması bir `.env` dosyası okumaz** — normal çalışma için hiçbir ortam değişkeni
gerekmez, varsayılanlar koda gömülüdür. Aşağıdakiler yalnız geliştirme/test/özel durumlar için
isteğe bağlı geçersiz kılmalardır. PowerShell'de tek oturum için:

```powershell
$env:TD2_NO_SPLASH = "1"
```

Kalıcı yapmak isterseniz `setx TD2_NO_SPLASH 1` (yeni terminal gerekir).

| Değişken | Ne işe yarar |
|---|---|
| `TD2_NO_SPLASH` | Açılış animasyonunu atlar (geliştirirken hızlı başlatma) |
| `TD2_NO_WELCOME` | Hoş geldin ekranını atlar |
| `TD2_ACCOUNT_URL` | Hesap sunucusu adresini geçersiz kılar (varsayılan: canlı Worker) |
| `TD2_REPORT_URL` | Hata rapor uç noktasını geçersiz kılar |
| `TD2_TASKS_URL` | Görev akışı adresini geçersiz kılar |
| `TD2_ENT_PUBKEY` | Lisans doğrulama açık anahtarını geçersiz kılar (test için) |
| `TD2_SHOT_OVERLAY` | Overlay ekran görüntüsü teşhis modu |
| `TD2_CURSOR_NATIVE` | Yerel imleç davranışı (fare izi sorunlarını ayıklamak için) |
| `TD2_ACCOUNT_TEST_BROWSER` | Hesap testlerinde kullanılacak tarayıcı |
| `MT_MODEL_DIR` | Çeviri modeli klasörünü başka yere taşır |
| `ANTHROPIC_API_KEY` | Opsiyonel "Read with Claude" OCR yedeği (yoksa özellik kapalı) |
| `OPENAI_API_KEY` | Opsiyonel çevrimiçi çeviri sağlayıcısı (yoksa yalnız yerel çeviri) |

İstersen kök dizinde kendi `.env.example` dosyanı oluşturabilirsin (uygulama okumaz, yalnız not
amaçlı):

```dotenv
# Opsiyonel — yalnız geliştirme kolaylığı için
TD2_NO_SPLASH=1
TD2_NO_WELCOME=1

# Opsiyonel bulut özellikleri (boş bırakılırsa ilgili özellik sessizce kapanır)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

> 🔒 `.env` dosyasını **asla commit etme.**
>
> **Bu rehber yazılırken bulunan ve kapatılan açık (2026-11-15):** kök `.gitignore` dosyası `.env`,
> `*.jks`, `*.p8` ve `key.properties` desenlerini **içermiyordu**. `**/*.jks` kuralı yalnız
> `mobile/android/.gitignore` içindeydi ve o dosya sadece kendi alt ağacını kapsıyor — yani
> **depo kökündeki bir keystore korumasızdı.** Codex devir belgesine göre `td2-companion-beta.jks`
> tam olarak orada duruyor (`C:\Users\PC\Desktop\Thedivision2program\td2-companion-beta.jks`), yani
> dikkatsiz bir `git add -A` imzalama anahtarını public depoya gönderebilirdi. Desenler kök
> `.gitignore`'a eklendi ve `git check-ignore` ile doğrulandı. **Yerel kolunda bu düzeltme henüz
> yok** — orada çalışmaya devam edeceksen aynı satırları oraya da ekle, yoksa risk sürüyor.
>
> İyi haber: taramada hiçbir keystore/`.env`/`.p8` dosyasının bu depoda **takipli olmadığı**
> doğrulandı (`git ls-files` → 0 sonuç), yani geçmişe sızmış bir sır yok.

---

## 5. Opsiyonel bileşenler

### 5.1 Mobil Companion (Flutter)

```powershell
cd mobile
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
```

**Repoda OLMAYAN, yerel oluşturman gereken dosyalar:**

| Dosya | Nasıl elde edilir |
|---|---|
| `mobile/android/app/google-services.json` | Firebase Console → proje ayarları → Android uygulaması (`com.federalturk.td2companion`) |
| `mobile/android/key.properties` | `key.properties.example`'ı kopyala, kendi upload-key değerlerini gir |
| `mobile/android/upload-keystore.jks` | `keytool -genkeypair` ile kendin üret (Play yüklemesi için) |

GitHub beta kanalı imzalama (CI) ayrı bir keystore kullanır ve GitHub secret'ları üzerinden çalışır:
`TD2_BETA_KEYSTORE_BASE64`, `TD2_BETA_KEYSTORE_PASSWORD`, `TD2_BETA_KEY_ALIAS`. Ayrıntı:
`docs/mobile_beta_signing_tr.md`.

> ⚠️ Yerel kolda bu secret'lar `ANDROID_*` adlarıyla da anılıyor. İkisi çakışıyor — hangisinin
> geçerli olduğu netleşmeden yeniden adlandırma yapma (bkz. `HANDOFF.md`).

### 5.2 Sunucu (Cloudflare Workers + D1)

```powershell
cd server
npm install -g wrangler        # veya npx kullan
npx wrangler d1 create td2stats
npx wrangler d1 execute td2stats --file=schema.sql
npx wrangler dev               # yerel geliştirme
```

`wrangler.toml` içindeki `[vars]` açık değerlerdir (repoda duruyor). **Gizli değerler dosyaya
yazılmaz**, ayrı ayrı girilir:

```powershell
npx wrangler secret put HASH_SALT
npx wrangler secret put GITHUB_TOKEN              # hata raporu için
npx wrangler secret put FCM_SERVICE_ACCOUNT_JSON  # Android push (Firebase Admin SDK JSON'unun TAMAMI)
npx wrangler secret put APNS_AUTH_KEY_P8          # iOS push (.p8 dosyasının PEM metni)
npx wrangler secret put APNS_KEY_ID
npx wrangler secret put APNS_TEAM_ID
```

Her platform için secret seti tanımlı değilse push bildirimi **bağımsız olarak sessizce no-op**
olur — uygulama kırılmaz.

Testler:

```powershell
node test_accounts.mjs
node test_mobile.mjs
node test_overview.mjs
node test_reports.mjs
node test_tasks.mjs
```

### 5.3 Web sitesi

Statik dosyalar; derleme adımı yok. Yerel önizleme:

```powershell
cd web
npx serve .          # ya da herhangi bir statik sunucu
```

Yapılandırma: `web/assets/js/config.js` (`API_BASE`, `REPO`, `GUMROAD_URL`).
Yayın: Cloudflare Pages, GitHub entegrasyonu ile `main` dalından otomatik (build output: `web`).

### 5.4 Xbox Companion (UWP)

Visual Studio + UWP iş yükü gerektirir; Linux/macOS'ta derlenmez. CI'da derleme doğrulaması
yapılıyor (`.github/workflows/build-xbox.yml`, 2026-11-14'ten beri yeşil). **Gerçek bir Xbox
konsolunda hiç test edilmedi.**

---

## 6. Testler ve doğrulama

Testler **tek tek** çalıştırılır (toplu çalıştırma izolasyonu bozar — `AGENTS.md`
`ci-test-automator` kuralı):

```powershell
python -B tests/test_core.py
python -B tests/test_ocr.py
python -B tests/test_livetranslate.py
python -B tests/test_overlay.py
python -B tests/test_itempolicy.py
python -B tests/test_app_stability.py
python -B tests/test_stability_widgets.py
python -B tests/test_project_structure.py

# Tam liste (57 dosya)
Get-ChildItem tests\*.py
```

**Bilinen durum:** `tests/test_knowledge.py` şu an **kırmızı** — canlı veriye bağımlı bir fixture
yüzünden (`KeyError`). Kök nedeni `ROADMAP.md`'de belgeli, düzeltmesi düşük riskli ve bekliyor.
Yani ilk çalıştırmada bu testin patlaması **beklenen** durumdur, senin kurulumunda bir hata değil.

Söz dizimi hızlı kontrolü:

```powershell
python -m py_compile app.py engine.py livetranslate.py ocr_backend.py overlay.py
```

---

## 7. Dokunulmaması gereken dosyalar

Bunlar kullanıcı/runtime verisi veya gizli materyal — silmeyin, üzerine yazmayın, commit etmeyin:

```text
builds.json          stash.json           progress.json
tasks.json           sessions.json        *.bak
logs/                                     kişisel loglar
td2-companion-beta.jks                    mobile/android/key.properties
mobile/android/app/google-services.json   mobile/android/upload-keystore.jks
.env                 build/  dist/  installer/
```

`.gitignore` bunların çoğunu zaten dışlıyor. `builds.json` tarihsel olarak takipte kaldı —
çalışırken değişir, yanlışlıkla commit etmemeye dikkat et.

---

## 8. İlk okuma sırası (yeni geliştirici / yeni oturum)

1. `AGENTS.md` — bağlayıcı kurallar ve güvenlik sınırları
2. `HANDOFF.md` — şu an nerede kalındı, hangi ayrışma var
3. `ROADMAP.md` — bileşen bileşen genel durum
4. `BUGS.md` — bilinen hatalar
5. Bu dosya (`SETUP.md`) — ortamı ayağa kaldırma
6. `docs/feature_roadmap_2026-11-14.md` — özellik tanımları ve geliştirme fazları
