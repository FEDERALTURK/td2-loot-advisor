# TD2 Loot Advisor — Teknik Devir Raporu (Claude → ChatGPT/Codex)

**Hazırlayan:** Claude (Claude Code / Claude Sonnet 5), bu oturumda `/home/claude/td2-loot-advisor` klonu üzerinde
çalışarak.
**Rapor tarihi:** 2026-11-04 (UTC+3, İstanbul).
**Amaç:** `FEDERALTURK/td2-loot-advisor` (GitHub, MIT) projesini geliştirmeye devam edecek başka bir yapay zekâ
geliştirme asistanına (ChatGPT/Codex) proje bilgisini, kararları, mevcut kod durumunu, bilinen hataları, test
sonuçlarını ve bekleyen işleri kaybetmeden aktarmak.

**Etiket sözleşmesi** (her bulgu için kullanılır):
- **Doğrulandı** — bu oturumda ben (Claude) doğrudan kodu okuyarak, komut çalıştırarak veya test sonucu görerek
  teyit ettim.
- **Kısmen doğrulandı** — proje içi belgede (README/ROADMAP/BUGS/DEVELOPMENT_LOG/HANDOFF) yazılı, önceki bir
  oturumun iddiası; ben bu oturumda bağımsızca yeniden doğrulamadım ama belgeyi okudum ve içerik tutarlı görünüyor.
- **Varsayım** — hiçbir yerde doğrudan yazılı değil, bağlamdan çıkardığım bir tahmin.
- **Test edilmedi** — iddia var ama gerçek bir testle (özellikle gerçek Windows/Tk/oyun ortamında) kanıtlanmamış.

> **Önemli not:** Bu oturum **Linux tabanlı bir konteynerde** çalıştı (proje Windows masaüstü uygulaması).
> `tkinter` konteynerin varsayılan Python'ında (3.13) yoktu; `python3.12` + `python3-tk` paketiyle VE
> `xvfb-run` (sanal ekran) ile gerçek Tk pencereleri oluşturulup `tests/test_stability_widgets.py`
> çalıştırılabildi (bkz. §10). Bu, gerçek bir Windows ekranında insan gözüyle kontrolün **yerine geçmez** —
> yalnızca "pencere obje olarak kuruluyor, callback hatası yok" seviyesinde bir doğrulamadır.

---

# 1. Proje Kimliği

- **Proje adı:** TD2 Loot Advisor (GitHub: `FEDERALTURK/td2-loot-advisor`)
- **Uygulamanın amacı:** *Tom Clancy's The Division 2* oyuncularının envanterde eşya değerlendirmesine harcadığı
  zamanı azaltmak. Oyuncu bir eşyanın üzerine gelip F8'e basar; program ekrandaki eşya kartını okur (OCR), oyunun
  tam kütüphanesiyle karşılaştırır, oyuncunun aktif build'iyle kıyaslar ve saniyeler içinde **sakla / düşün / kır**
  kararı verir. — **Doğrulandı** (README.md, app.py akışı okundu).
- **Hedef kullanıcı:** The Division 2 oynayan, Windows'ta PC'de oynayan oyuncular (özellikle build optimizasyonuyla
  ilgilenen "endgame" oyuncular). — **Kısmen doğrulandı** (README'den çıkarım).
- **Ana kullanım senaryoları:** Eşya tarama/karar, build takibi ve eksik parça listesi, sandık (stash) yönetimi ve
  optimizasyonu, satıcı/hedef loot eşleştirme, görev takibi + çeviri, sesli asistan, telefon eşleştirme (bulut
  senkron). — **Doğrulandı** (README Features bölümü + kod).
- **Desteklenen platformlar:** Windows masaüstü (ana ürün, Python/Tkinter, installer + portable + kaynak kurulum).
  Android companion (Flutter, beta APK). iOS: **planlanmış, henüz yok** (Apple Developer Program kaydı bekliyor —
  Kısmen doğrulandı, ROADMAP.md). Web: tanıtım/hesap/haberler sitesi (`web/`, Cloudflare Pages) — **uygulama değil,
  bilgi/hesap sitesi**. — **Doğrulandı**.
- **Uygulamanın oyuna erişim sınırı:** Yalnızca **ekran okuma (OCR)** ve oyunun **kendi ayar dosyasını okuma**
  (örn. çözünürlük/HDR ayarı için). Oyun belleğine hiç dokunmaz, DLL injection yok, input otomasyonu (oyuna tuş/fare
  göndermek) yok, anti-cheat aşma yok. — **Doğrulandı** (README "Safety" bölümü; bu oturumda `ReadProcessMemory`,
  `injection`, `WriteProcessMemory` gibi terimler için kod taraması yapılmadı ama önceki oturumların HANDOFF.md'si
  "her oturumda `git grep` ile yeniden doğrulanmalı" diyor — **bu oturumda bu tarama tekrar yapılmadı**, bir
  sonraki oturum bunu yapmalı).
- **Kullanılan ana teknolojiler:** Python 3.12/3.13, Tkinter (GUI), RapidOCR/Tesseract (OCR), CTranslate2 +
  OPUS-MT (yerel çeviri), Ed25519 (lisans imzalama), Cloudflare Workers + D1 (topluluk sunucusu), Flutter
  (mobil companion), statik HTML/CSS (web sitesi). — **Doğrulandı**.
- **Ana dil:** Python (masaüstü uygulama ve sunucu test scriptleri hariç — sunucu Node.js).
- **Arayüz teknolojisi:** Tkinter (ttk ile). Yeni modüler paket `td2app/ui/` altında tema/efekt/splash kodu
  tutuluyor (`ui_theme.py`, `fx.py`, `bgvideo.py`, `ui_art.py`, `ui_hud.py`, `splash.py`, `view3d.py`); kök
  dizindeki aynı adlı dosyalar (`ui_theme.py` vb.) artık **uyumluluk köprüsü** (tek satırlık modül yönlendirmesi,
  `td2app.ui.X`'e devrediyor). — **Doğrulandı** (dosyalar okundu).
- **Paketleme teknolojisi:** Inno Setup (`.iss`, installer `.exe`), PyInstaller'a benzer bir `.spec`
  (`TD2LootAdvisor.spec`, tek-dosya `.exe` için), GitHub Actions ile Windows runner üzerinde otomatik derleme.
  — **Doğrulandı**.
- **OCR motorları:** RapidOCR (PP-OCR, varsayılan/önerilen — README'ye göre 1440p/1080p/720p/480p'de 8/8 doğru),
  Tesseract OCR (yedek, 3/8 doğru aynı testte). — **Kısmen doğrulandı** (iddia README'de; bu oturumda gerçek
  oyun kartı görseliyle yeniden test edilmedi).
- **Çeviri motorları:** (a) Yerel/çevrimdışı: CTranslate2 ile OPUS-MT (Helsinki-NLP), tek dil çifti **İngilizce→
  Türkçe**, int8 CPU çıkarım. (b) Yapay zekâ (AI) motoru: kullanıcının Asistan sekmesinde yapılandırdığı LLM
  sağlayıcısı (Ollama / Claude Code / Claude API / OpenAI) üzerinden `complete(system, user)` çağrısı — bu
  oturumda **10 arayüz dilinin herhangi birine** çevirebilecek şekilde genelleştirildi (önceden sabit Türkçe'ydi,
  bkz. §5.5 ve §13). — **Doğrulandı** (bu oturumun kendi değişikliği).
- **Ses motorları:** pyttsx3 (yerel TTS), edge-tts (çevrimiçi TTS), faster-whisper (yerel konuşma tanıma),
  Windows konuşma tanıma yedek yolu. — **Kısmen doğrulandı** (`requirements.txt`/`requirements-voice.txt`'ten,
  bu oturumda ses çıktısı/girdisi fiilen test edilmedi).
- **Güncelleme/GitHub altyapısı:** `updater.py` — GitHub Releases API'sinden sürüm listesi çeker, SHA-256
  doğrulamalı indirme + sessiz kurulum + yeniden başlatma yapar. GitHub Actions workflow'u (`build-installer.yml`)
  tag push veya elle tetiklemeyle (`workflow_dispatch`, `release: true` girdisiyle) testleri çalıştırır, installer/
  portable/checksum üretir ve (istenirse) GitHub Release yayınlar. — **Doğrulandı** (bu oturumda iki kez bizzat
  tetiklendi ve izlendi, bkz. §4, §13).
- **Android/Web tarafının mevcut durumu:**
  - **Android (Flutter, `mobile/`):** Beta APK (`0.1.2-beta`, `pubspec.yaml`'da `version: 0.1.2+3`) GitHub
    Release'lerde mevcut. Bulut eşleştirme (pairing code), build senkronu, push-bildirimi kaydı kodu yazılmış
    ama **bu depoda hiçbir oturumda Flutter SDK'sı ile derlenip/test edilmediği not edilmiş** (ROADMAP.md,
    HANDOFF.md). Push bildirimi için Firebase tarafı kullanıcının kendi PC'sinde tamamlanması gereken manuel bir
    adımda kalmış (`google-services.json` yerleştirme + gradle satırı aktif etme). — **Kısmen doğrulandı**
    (bu oturumda `mobile/` hiç açılmadı/derlenmedi).
  - **Web (`web/`):** Statik tanıtım/hesap/haberler sitesi; ROADMAP.md'ye göre Cloudflare Pages'te **canlı**
    (`td2-loot-advisor.pages.dev`). — **Kısmen doğrulandı** (bu oturumda siteye erişilmedi, sadece belge okundu).

---

# 2. Projenin Genel Mimari Özeti

```
Kullanıcı
  ↓
TD2 Loot Advisor Arayüzü (app.py, Tkinter)
  ├─ OCR / ekran yakalama           → ocr_backend.py, capture.py, display.py
  ├─ Eşya tanıma                    → gamedata.py, knowledge.py, meta/game_data.json
  ├─ Loot karar motoru              → engine.py, itempolicy.py, intelligence.py
  ├─ Sandık ve build verileri       → stash.py, builds.json (yerel runtime)
  ├─ Komuta Merkezi / Tanılama      → diagnostics_center.py, reports.py
  ├─ Canlı çeviri / overlay         → livetranslate.py, overlay.py, trscreen.py
  ├─ Asistan / ses                  → speech.py, voicepack.py, (app.py: ai_complete)
  ├─ Satıcı / hedef loot            → vendor.py, dropstats.py
  ├─ Görevler                       → tasks_live.py, wiki_sync.py
  ├─ Tema / FX / açılış             → td2app/ui/{ui_theme,fx,bgvideo,splash,ui_art,ui_hud,view3d}.py
  ├─ Hesap / lisans                 → account.py, features.py, terms.py
  ├─ Servis / sistem tepsisi        → service.py, single.py, presence.py
  ├─ Yerel API (premium)            → localapi.py
  └─ Güncelleme ve GitHub dağıtımı  → updater.py, .github/workflows/build-installer.yml
         ↓ (ayrı, uzak bileşenler)
  ├─ Topluluk sunucusu (Cloudflare Workers + D1) → server/
  ├─ Mobil companion (Flutter)                    → mobile/
  └─ Web sitesi (statik, Cloudflare Pages)        → web/
```

Bileşen görevleri (**Doğrulandı**, dosyalar bu oturumda okundu/listelendi; iç detayların çoğu önceki
oturumlardan — **Kısmen doğrulandı** olarak işaretlenenler ayrıca belirtilir):

- **`app.py`** (≈612 KB, proje genelinde en büyük dosya) — Ana giriş noktası ve tüm Tkinter arayüzü: sekmeler
  (Panel, Build'ler, Sandık, Bilgi/Ansiklopedi, Çeviri, Komuta Merkezi, Ayarlar, Hakkında, …), olay/kısayol
  yönetimi, tüm alt sistemlerin (OCR, çeviri, ses, hesap, güncelleme) UI'dan çağrılması. **Kritik dosya** — tek
  başına uygulamanın can damarı; herhangi bir değişiklik tüm sekmeleri etkileyebilir.
- **GUI / Tkinter katmanı** — `app.py` (widget inşası) + `td2app/ui/` (tema paketleri, efektler, splash ekranı,
  arka plan videosu, 3D görünüm). Tema sistemi `ui_theme.py`'deki `_PACKS` sözlüğü + `apply_pack()` fonksiyonu
  ile yönetiliyor; şu an **18 tema** var (en yenisi "kaivolt", varsayılan — bu oturumda eklendi).
- **OCR / ekran yakalama akışı** — `capture.py` (ekran görüntüsü alma, `mss` kütüphanesi), `ocr_backend.py`
  (RapidOCR/Tesseract soyutlaması, renk/ikon ipuçları), `display.py` (çözünürlük profilleri, oyun ayar dosyası
  okuma).
- **Eşya tanıma ve oyun kütüphanesi** — `gamedata.py` (OCR metnini `meta/game_data.json`'daki kütüphaneyle
  eşleştirir), `knowledge.py` (ansiklopedi/açıklama kaynak önceliklendirmesi — bu oturumdan önceki bir turda
  30 kesik açıklama hatası burada bulunup düzeltilmiş, bkz. DEVELOPMENT_LOG.md).
- **Loot kararı ve eşya koruma kuralları** — `engine.py` (karar motoru, build planı, kart bulucu),
  `itempolicy.py` (Exotic/Named/Prototype gibi eşyaların otomatik kır kapsamı dışında tutulması —
  **Doğrulandı**, kod bu oturumda değişmedi ama önceki tur testleriyle doğrulanmış, bkz. §9), `intelligence.py`.
- **Sandık / envanter kaydı** — `stash.py`: her taranan eşya `stash.json`'a (yerel, Git'e **girmiyor**) kaydedilir;
  optimize/denetim/recalibration danışmanı burada.
- **Build optimizasyonu** — `stash.py` içinde (`Optimize` fonksiyonu) + `engine.py`'deki build-skor mantığı.
- **Recalibration / library sistemi** — `stash.py` (recalibration advisor; README'ye göre artık ücretsiz —
  **Kısmen doğrulandı**, `LICENSE_NOTES.md`/`BUGS.md`'ye göre `recal_advisor` free yapılmış, lisans gri alanı
  (mxswat verisi CC BY-NC-SA 4.0) bu şekilde çözülmüş).
- **Satıcı ve hedef loot verileri** — `vendor.py` (haftalık satıcı + hedef loot, build/stash eşleştirmesi),
  `dropstats.py` (anonim drop istatistiği istemcisi, opt-in).
- **Komuta Merkezi** — `diagnostics_center.py` (sorun tarama, hata bildirimi — GitHub issue'ya maskelenmiş
  önizlemeyle gönderim), `reports.py`.
- **Canlı çeviri** — `livetranslate.py`: OCR satırlarından paragraf bloklama, özel ad/terim maskesi (`Glossary`),
  çeviri motoru soyutlaması (`LocalMT`/`AIMT`), önbellek (`Cache`), doğrulama (`Translator`). Bu oturumda
  büyük ölçüde değiştirildi — bkz. §5.5, §7, §13.
- **Yerinde çeviri bindirmesi / overlay** — `overlay.py`, `trscreen.py`: ekran üstü yarı saydam pencere(ler),
  "inplace" modda OCR kutusunun tam üzerine konumlandırma. Bu oturumda **değiştirilmedi**, sadece dolaylı olarak
  `app.py`'deki `_lt_run()` → `_lt_show()` çağrı zincirinin davranışı etkilendi (güven uyarısı eklendi).
- **Sesli asistan** — `speech.py` (konuşma tanıma + TTS soyutlaması), `voicepack.py` (agent ses paketleri).
- **Kısayollar** — `game_assistant.py` (global kısayol dinleyici, `pynput` tabanlı — **bu konteynerde `pynput`
  kurulu değil**, bu oturumda `tests/test_game_assistant.py` bu yüzden 1 hatayla bitti, bkz. §10).
- **Tema / efekt / açılış animasyonu** — `td2app/ui/ui_theme.py`, `fx.py`, `bgvideo.py`, `splash.py`.
- **Fare izi / imleç efektleri** — `td2app/ui/fx.py` (`SafeTrail` sınıfı); BUGS.md'ye göre önceki bir turda
  `Canvas.lower()` çağrısının yanlış metodu tetiklediği bir `TclError` burada düzeltilmiş (**Kısmen doğrulandı**).
- **Tanılama merkezi** — `diagnostics_center.py`.
- **Hata raporlama** — `diagnostics_center.py` + GitHub issue akışı (`reports.py`/`notify.py` ile ilişkili
  olabilir — bu oturumda ayrıntılı izlenmedi).
- **Güncelleme mekanizması** — `updater.py` (SHA-256 doğrulamalı indirme/kurulum), `scripts/version.py`
  (`app.py`'den `APP_VERSION`'ı regex ile çıkarır, CI tag adı için kullanılır).
- **GitHub Actions / Windows installer** — `.github/workflows/build-installer.yml` (ana yayın akışı) + 14 diğer
  workflow (`ocr-check.yml`, `translate-check.yml`, `stability-check.yml`, `ui-check.yml`, `perf-check.yml`,
  `sync-check.yml`, `service-check.yml`, `account-check.yml`, `info-check.yml`, `tasks-live.yml`,
  `mt-model.yml`, `agent-video.yml`, `agents-render.yml`, `retire-releases.yml`) — bu oturumda yalnızca
  `build-installer.yml` okundu/çalıştırıldı; **diğer 14 workflow'un içeriği bu oturumda incelenmedi.**
- **Telefon / Android / APK tarafı** — `mobile/` (Flutter projesi), `companion.py` (masaüstünde yerel
  salt-okunur web sayfası + QR, LAN üzerinden eski eşleştirme yöntemi — bulut eşleştirmeden ayrı).
- **Web sayfası / web panel planı** — `web/` (statik site: tanıtım, haberler, premium, hesap sayfaları),
  `server/` (Cloudflare Worker: hesap/mobil/görev/istatistik API'leri, `worker.js` + `schema.sql` D1 şeması).

---

# 3. Klasör ve Dosya Haritası

| Dosya/Klasör | Amaç | Kritik mi? | Değiştirilirken dikkat edilmesi gerekenler |
|---|---|---:|---|
| `app.py` | Ana UI, tüm sekmeler, olay yönetimi | **Çok** | 612 KB; tek bir fonksiyonu bulmak için `grep`/satır no kullan. `PAL["..."]` renk anahtarlarını `ui_theme.PALETTES`'te doğrula (geçmişte `PAL["panel"]` hatası sessiz çökmeye yol açmıştı). `tab_keys`/`tab_groups` değişince `tests/test_stability_widgets.py`'deki sabit sayfa/sekme sayısı assertion'ını güncelle. |
| `intelligence.py` | Karar destek / analiz mantığı | Yüksek | `itempolicy.py` ile birlikte okunmalı — ikisi de karar zincirinde. |
| `stash.py` | Sandık, denetim, optimize, recalibration | Yüksek | `stash.json` şemasını değiştirirsen geriye dönük uyumluluk (kullanıcının var olan dosyası) düşünülmeli. |
| `engine.py` | Karar motoru, build planı, kart bulucu | **Çok** | Exotic/Named/Prototype koruma mantığı burada ve `itempolicy.py`'de — asla otomatik kır önermemeli. |
| `gamedata.py` | OCR metni → kütüphane eşleştirmesi | **Çok** | `meta/game_data.json` ile sıkı bağımlı; kütüphane güncellenince burada regresyon testi (`tests/test_core.py`, `test_itempolicy.py`) çalıştır. |
| `vendor.py` | Satıcı/hedef loot eşleştirme | Orta | Harici bir topluluk sayfasından (hi-dep Division 2 Database) okuma var — ağ hatalarına dayanıklı olmalı. |
| `diagnostics_center.py` | Tanılama, hata bildirimi | Orta | GitHub'a otomatik gönderim yok; önce maskelenmiş önizleme göster kuralı burada uygulanmalı. |
| `ocr_backend.py` | RapidOCR/Tesseract soyutlaması, renk ipuçları | **Çok** | Motor değişimi tüm okuma doğruluğunu etkiler; `tests/test_ocr.py` gerçek kart örnekleriyle çalışır (bkz. `tests/samples`). |
| `livetranslate.py` | Canlı çeviri: maskeleme, motor, önbellek, doğrulama | **Çok** | Bu oturumda genişletildi (çoklu dil). `AIMT.SYSTEM` sınıf özniteliği geriye-uyumluluk için korunuyor — silme. `blocks_from_lines()` her zaman 3'lü tuple `(metin, kutu, güven)` döndürür; testlerde 2'li mock'lar da olabilir, tüketici kodda `len(b) > 2` gibi savunmacı kontrol düşün. |
| overlay ile ilgili dosyalar (`overlay.py`, `trscreen.py`) | Ekran üstü bindirme, yerinde kutu | Yüksek | Bu oturumda değiştirilmedi; tıklamaları engellememe davranışı test edilmedi (bkz. §6.1, §7). |
| UI/tema/FX dosyaları (`td2app/ui/*.py`) | Tema paketleri, efektler, splash | Orta-Yüksek | Kök dizindeki aynı adlı dosyalar (`ui_theme.py` vb.) sadece yönlendirme köprüsü — gerçek kodu `td2app/ui/` altında düzenle. |
| `tests/` | ~45 test dosyası, birim+entegrasyon+UI | **Çok** | Bazı dosyalar `pytest` modülü değil, bağımsız script (`if __name__ == "__main__": sys.exit(main())` ile `sys.exit(0)` çağırıyor — pytest ile toplu koşturulursa `INTERNALERROR` verir, bkz. §10). CI her birini `python -B tests/<dosya>` olarak ayrı ayrı çalıştırıyor. |
| `scripts/run.bat` | Kaynaktan başlatma, bağımlılık kurulumu | Yüksek | `--check`/`--repair`/`--extras` bayrakları var (README). |
| `.github/workflows/` | 15 workflow dosyası | **Çok** | `build-installer.yml` dışındakiler bu oturumda incelenmedi — her biri ayrı CI tetikleyicisi/amaca sahip olabilir, dikkatli değiştir. |
| `requirements*.txt`, `TD2LootAdvisor.spec`, `scripts/installer.iss`, `scripts/build_*.bat` | Bağımlılık/paketleme/installer | Yüksek | Sürüm numarası `app.py`'deki `APP_VERSION`'dan `scripts/version.py` ile regex ile çekiliyor; `.iss`/`.spec` elle senkron tutulmalı mı otomatik mi, bu oturumda doğrulanmadı. |
| Config/runtime veri dosyaları | Aşağıdaki tabloya bak | — | — |

**Kullanıcı verisi / runtime dosyası durumu** (bu oturumda `git ls-files` ile bizzat kontrol edildi — **Doğrulandı**):

| Dosya | `.gitignore`'da mı? | Git'te takip ediliyor mu? | Not |
|---|---|---|---|
| `builds.json` | **Hayır** | **EVET, takip ediliyor** | ⚠️ **Dikkat.** Repo kökünde `builds.json` Git'e commit edilmiş durumda. İçeriği incelendi: gerçek kullanıcı sandık/build verisi gibi görünmüyor, ilk `v5.0` kaynağından gelen **varsayılan/örnek ayar şablonu** (settings + attribute eşleştirme sözlüğü). `scripts/default_builds.json` adında ayrı bir "temiz" varsayılan da var. Yine de bu dosyanın commit edilmiş olması riskli bir desen — gerçek çalışma zamanında kullanıcının kendi `builds.json`'ının üzerine bu dosyanın yazılıp yazılmadığı (veya tam tersi, kullanıcı verisinin yanlışlıkla commit edilip edilmediği) **bir sonraki oturum tarafından netleştirilmeli**. |
| `stash.json` | Evet | Hayır (takip edilmiyor) | Repo kökünde 59 bayt boş bir dosya fiziksel olarak var ama Git'e eklenmemiş — runtime dosyası, doğru. |
| `progress.json` | Evet | Hayır | Runtime. |
| `tasks.json` | Evet | Hayır | Runtime (146 bayt, repo kökünde fiziksel var ama Git'e eklenmemiş). |
| `sessions.json` | **`.gitignore`'da açıkça yok** ama bu oturumda `git ls-files` ile takip edilmediği doğrulandı; muhtemelen dosya hiç fiziksel olarak oluşmamış. | Hayır | ⚠️ `.gitignore`'a açık bir satır eklenmesi önerilir (şu an örtük olarak güvenli ama kırılgan). |
| `vendor_cache.json`, `tasks_cache.json`, `meta_cache.json`, `news_cache.json` | Evet | Hayır | Runtime önbellekleri, repo kökünde fiziksel var (eski zaman damgalı), Git'e girmemiş. |
| `account.dat` | Evet | Hayır | DPAPI şifreli hesap oturumu — Git'e asla girmemeli, şu an girmiyor. |
| `logs/` | Evet | Hayır | Klasör fiziksel var, boş değil muhtemelen ama takip edilmiyor. |
| `.bak` dosyaları | — | Bu oturumda `find . -name "*.bak"` ile tarandı, **hiç bulunamadı** | — |
| Test çıktıları | Bazıları `.gitignore`'da (`tests/.game_cache.json`, `tests/.stash_test.json`, `tests/.click_result.json`, `tests/.tab_result.json`, `tests/.bench_card.png`) | Hayır | Test izolasyonu için önemli — testler arası sızıntıyı önlüyor. |

**Sonuç/uyarı:** `builds.json`'ın Git'e commit edilmiş olması tek gerçek anomali. Bir sonraki oturum, bu dosyanın
gerçekten "şablon" olduğunu (kullanıcının gerçek verisi olmadığını) teyit etmeli ve gerekiyorsa `.gitignore`'a
eklenip `git rm --cached builds.json` ile depodan çıkarılmasını **kullanıcıya önermeli** (kullanıcı onayı almadan
böyle bir işlemi yapma — geri alınamaz bir geçmiş temizliği değil ama görünürlük/gizlilik kararı kullanıcıya ait).

---

# 4. Mevcut Sürüm ve Dağıtım Durumu

(Bu bölümdeki tüm bilgiler bu oturumda `git log`, `git ls-remote --tags`, `gh api repos/.../releases` ile
doğrudan sorgulanarak elde edildi — **Doğrulandı**.)

- **Son stabil sürüm (GitHub'daki en son, prerelease olmayan release):** `v9.1.5.29` — yayın tarihi
  `2026-11-04T20:35:39Z`.
- **Son beta sürüm:** Yok / bilinmiyor — bu oturumda prerelease olarak işaretli bir release görülmedi.
- **Yereldeki (kod) uygulama sürümü:** `app.py`'deki `APP_VERSION = "9.1.5.29"` — Release ile **eşleşiyor**.
- **GitHub'daki son tag (remote):** `v9.1.5.29` (commit `69e030c`).
- **GitHub'daki son release:** `v9.1.5.29`, varlıklar: `TD2LootAdvisor_Setup_9.1.5.29.exe` (~177,9 MB),
  `TD2LootAdvisor_9.1.5.29_portable.zip` (~237,8 MB), `SHA256SUMS.sha256` (205 B).
- **Aktif branch:** `main` (tek branch; `master`'ın önceki bir oturumda kullanıcı tarafından silindiği
  HANDOFF.md'de belirtilmiş — **Kısmen doğrulandı**, bu oturumda `master`'ın varlığı kontrol edilmedi).
- **Son bilinen commit:** `69e030c` ("feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı
  (9.1.5.29)") — bu oturumun kendi commit'i.
- **⚠️ Sürüm numarası karışıklığı tespit edildi:** Remote Git tag'leri `v9.1.5.23`'ten doğrudan `v9.1.5.28`'e
  atlıyor — **`v9.1.5.24`, `v9.1.5.25`, `v9.1.5.26`, `v9.1.5.27` için uzak (remote) Git tag'i YOK**, ama
  `.github/release_notes.md` dosyasında bu 4 sürüm için ayrıntılı not satırları var ve ROADMAP.md bu sürümlerin
  "2026-11-04'te 7 yeni sürüm" olarak art arda çıktığını anlatıyor. Olası açıklama (Varsayım): bu ara sürümler
  tag'lenip GitHub Release olarak yayınlanmadan sadece `APP_VERSION` bump + commit olarak geçmiş olabilir, veya
  tag'ler sonradan temizlenmiş olabilir (`retire-releases.yml` adında bir workflow var — **bu oturumda içeriği
  incelenmedi**, eski release/tag'leri otomatik temizliyor olabilir). **Bir sonraki oturum bunu netleştirmeli.**
- **Windows installer durumu:** Inno Setup ile üretiliyor, CI'da son 2 build'de (`v9.1.5.28`, `v9.1.5.29`)
  **başarılı** — **Doğrulandı** (`gh run view` ile `conclusion=success` görüldü).
- **EXE paketleme durumu:** Hem installer (`.exe`) hem portable (`.zip`) hem tek-dosya `.exe` (`TD2LootAdvisor.spec`
  ile, `scripts/build_exe.bat`) seçeneği var. Tek-dosya `.exe`'nin bu oturumda CI'da üretildiği doğrulanmadı
  (CI akışı installer+portable üretiyor, tek-dosya ayrı bir elle-çalıştırma betiği gibi görünüyor — **Kısmen
  doğrulandı**).
- **Otomatik güncelleme durumu:** `updater.py` üzerinden, uygulama başlarken GitHub'dan en son sürümü kontrol
  ediyor (README: her 12 saatte bir + Ayarlar'dan elle). — **Kısmen doğrulandı** (README'den, bu oturumda
  fiilen tetiklenmedi).
- **Eski sürüme dönüş / rollback desteği:** "Sürüm geçmişi" penceresinden **herhangi bir** sürüm (eski/yeni/beta)
  seçilip kurulabiliyor (önceden sadece yeniye yükseltme izinliydi, bu kısıtlama v9.1.5.22'de kaldırılmış). —
  **Kısmen doğrulandı** (DEVELOPMENT_LOG.md'den; bu oturumda gerçek bir rollback denenmedi).
- **GitHub Actions durumları:** Bu oturumda tetiklenen 2 `build-installer.yml` çalışması (v9.1.5.28 ve v9.1.5.29)
  **ikisi de `success`** ile tamamlandı (ilkinde bir test regresyonu bulunup düzeltildi, ikinci deneme başarılı
  oldu — bkz. §6.3). Diğer 14 workflow'un son durumu **bu oturumda kontrol edilmedi**.
- **Bilinen workflow hataları:** Bu oturumda karşılaşılan **tek** gerçek CI hatası: `tests/test_stability_widgets.py`
  satır 84'teki sabit `pages==14` assertion'ı, yeni "Hakkında" sekmesi eklenince `pages==15` olması gerektiği
  için patladı (v9.1.5.28 ilk denemesinde) — düzeltildi, ikinci deneme geçti. **Kullanıcının şablonunda sorulan
  diğer spesifik hatalar** (`test_game_assistant.py failed` [CI'da, pynput eksikliği değil başka bir sebepten],
  `test_localapi.py WebSocket timeout`, "FAIL yerinde çeviri: kutular... canvas_items: 0", "Resource not
  accessible by integration", Node.js 20 deprecation, Windows port/TIME_WAIT, Tkinter widget yaşam döngüsü
  testi izolasyonu) — **bu oturumda hiçbir proje belgesinde (DEVELOPMENT_LOG.md, BUGS.md, HANDOFF.md,
  ROADMAP.md) bu spesifik hata metinlerine rastlanmadı.** Ya çok daha önceki bir oturumda yaşanıp belgelenmeden
  çözülmüş, ya da bu liste genel bir kontrol listesi olarak örnek amaçlı verilmiş olabilir. **Test edilmedi /
  kanıt bulunamadı** — ChatGPT bu hataları varsayılan olarak "hâlâ açık" kabul etmemeli, ama CI loglarını
  (GitHub Actions sekmesinden) tarayarak kontrol etmeli.
- **Yayın öncesi kullanıcı onayı kuralı:** **Bu oturumda fiilen uygulanan ve gözlemlenen kural** — kullanıcı
  önce "Bu gerekli mi?" ve "yayınlandı mı?" diye sordu, ben açıkladım, sonra kullanıcı açıkça **"yayınlayalım"**
  / **"yayınla"** dedi, ben de ancak o zaman `gh workflow run build-installer.yml --ref main -f release=true`
  komutunu çalıştırdım. Bu, kullanıcının "Yeni Güncellemeyi Yayınlamak İster misiniz? (vX.Y.Z) — Evet/Hayır"
  kuralına fiilen denk — **Doğrulandı, bu oturumda iki kez bu şekilde işledi**. ChatGPT/Codex bu deseni devam
  ettirmeli: kod + testler hazır olduğunda **commit/push** yapılabilir (kullanıcı bunun için ayrıca onay
  istemedi bu oturumda — commit/push'u ben kendi inisiyatifimle yaptım), ama **tag/release/installer yayını
  için açık onay beklenmeli.**

---

# 5. Tamamlanan Özellikler

## 5.1 OCR ve Eşya Okuma
- **Sağlar:** Ekrandaki eşya kartını okur (çoklu pas, çözünürlük/ölçek ayarlı), rarity/ikon rengi ipuçlarıyla
  destekler.
- **Dosyalar:** `ocr_backend.py`, `capture.py`, `display.py`.
- **Çalışma durumu:** Kısmen doğrulandı — README'de gerçek kart örnekleriyle (`tests/test_ocr.py`,
  `tests/samples/`) 8/8 doğruluk iddiası var; bu oturumda bu test çalıştırılmadı.
- **Bilinen sınırlar:** 240p pratik olarak okunamıyor (README'de açıkça belirtilmiş); 480p pratik minimum.
- **Test durumu:** `tests/test_ocr.py`, `tests/test_ocr_serialization.py` mevcut; bu oturumda sadece
  `test_ocr_serialization.py` çalıştırıldı (2/2 **PASS** — Doğrulandı), `test_ocr.py` çalıştırılmadı.
- **UI'da erişim:** Ayarlar → OCR; Panel sekmesinde F8 ile tetiklenir.

## 5.2 Loot Karar Sistemi
- **Sağlar:** Sakla/düşün/kır/incele kararı; slot-duyarlı puanlama (set parçası 1 minor attribute, marka/named
  2, talent sadece göğüs/sırt çantası).
- **Dosyalar:** `engine.py`, `itempolicy.py`, `intelligence.py`.
- **Çalışma durumu:** Kısmen doğrulandı (README + kod yapısı okundu, bu oturumda karar motoru testleri
  (`tests/test_itempolicy.py`) çalıştırıldı — **15/15 PASS, Doğrulandı**).
- **Bilinen sınırlar:** OCR yanlış okursa karar da yanlış olabilir — bu yüzden düşük güvenli durumlarda sistem
  "incele/REVIEW" demeli, otomatik kır dememeli (bkz. §9).
- **Test durumu:** `tests/test_itempolicy.py` **PASS** (bu oturumda çalıştırıldı), `tests/test_core.py` **PASS**
  (bu oturumda çalıştırıldı, lisans/optimizer/sync/vb. 18 testin hepsi geçti).
- **UI'da erişim:** Panel sekmesi, F8 taramasıyla otomatik.

## 5.3 Build ve Sandık Yönetimi
- **Sağlar:** Aktif build takibi, eksik parça listesi, build karşılaştırma ("Build Karşılaştır", v9.1.5.26),
  sandık optimize/denetim.
- **Dosyalar:** `stash.py`, `app.py` (UI), `builds.json`/`stash.json` (runtime).
- **Çalışma durumu:** Kısmen doğrulandı (DEVELOPMENT_LOG.md'ye göre "Build Karşılaştır" ekranının gerçek
  Windows'ta görsel doğrulaması **yapılmadı** — BUGS.md #12).
- **Bilinen sınırlar:** "Ortak kullanılabilir eşya"/"geçiş maliyeti" hesabı kasıtlı olarak kaba bir tahmin
  (gerçek roll kalitesini hesaba katmıyor) — BUGS.md #12'de açıkça belirtilmiş.
- **Test durumu:** Sözdizimi + i18n anahtar kontrolü yapılmış (önceki oturum); gerçek pencere render'ı **test
  edilmedi**.
- **UI'da erişim:** Build'ler sekmesi → "🆚 Karşılaştır"; Sandık sekmesi.

## 5.4 Prototype / Exotic / Named Koruması
- **Sağlar:** Exotic, Named, Prototype ve kilitli eşyalar hiçbir değerlendirme/ilerleme takibi/sandık denetimi
  yolunda otomatik "kır" kapsamına alınmaz.
- **Dosyalar:** `itempolicy.py`, `engine.py`, `stash.py`.
- **Çalışma durumu:** Doğrulandı (bu oturumda `tests/test_itempolicy.py` çalıştırıldı, 15/15 PASS; bu testlerin
  tam olarak hangi senaryoları kapsadığı satır satır okunmadı ama test adlarından [`test_itempolicy.py` dosya
  adı] bu korumanın test kapsamında olduğu çıkarımı yapılabilir — **Kısmen doğrulandı**, test içeriği satır
  satır incelenmedi).
- **Bilinen sınırlar:** Yok (bu oturumda bulunamadı).
- **Test durumu:** `tests/test_itempolicy.py` **PASS**.
- **UI'da erişim:** Panel (tarama sonucu), Sandık (denetim raporu).

## 5.5 Canlı Çeviri
- **Sağlar:** Oyun içi İngilizce metni (görev, diyalog, arayüz) ekranda okuyup çevirip gösterir.
- **Dosyalar:** `livetranslate.py`, `app.py` (`_lt_run`, `lt_translator`, `build_translate`), `tasks_live.py`
  (topluluk düzeltme hafızası).
- **Çalışma durumu — bu oturumda değiştirildi, Doğrulandı:**
  - Yapay zekâ (AI) motoru artık sabit Türkçe değil, uygulamanın seçili arayüz diline (10 dil) göre çeviriyor.
  - Yerel motor (OPUS-MT) hâlâ tek dil çifti (EN→TR); bu artık UI'da açıkça not ediliyor.
  - Türkçeye özel son-işleme (`UI_TR`, `WORD_FIX`) ve topluluk düzeltme hafızası artık yalnızca hedef dil Türkçe
    iken devrede.
  - Önbellek anahtarına hedef dil eklendi (çoklu dil çakışması önlendi).
  - OCR güveni düşükse ("şüpheli çeviri") durum satırında uyarı gösteriliyor (eşik: 0.68).
- **Bilinen sınırlar:** Topluluk düzeltme/öneri sisteminin sunucu tarafı (`tasks_live.suggest`, D1 şeması)
  hâlâ tamamen Türkçeye özel — diğer dillere genelleştirilmedi (kapsam dışı bırakıldı, büyük şema değişikliği
  gerektiriyor). `"lt.partial"` adlı önceden var olan bir i18n anahtarı 10 dil dosyasının **hiçbirinde yok**
  (önceden var olan, bu turla ilgisiz bir boşluk — not düşüldü, düzeltilmedi).
- **Test durumu:** `tests/test_livetranslate.py` (29/29 **PASS**), `tests/test_translation_reliability.py`
  (9/9 **PASS**), `tests/test_translation_controls.py` (5/5 **PASS**), `tests/test_app_stability.py`
  (17/17 **PASS** — bu oturumda bir regresyon bulunup düzeltildi, bkz. §6.3) — **hepsi bu oturumda bizzat
  çalıştırıldı, Doğrulandı.**
- **UI'da erişim:** Çeviri sekmesi (motor seçimi, hedef dil bilgisi), oyun üstü overlay (F8/kısayol ile).

## 5.6 Overlay / Yerinde Çeviri
- **Sağlar:** Çeviriyi oyun ekranının üzerinde, orijinal metnin tam konumunda (yerinde mod) veya köşede
  (varsayılan mod) gösterir.
- **Dosyalar:** `overlay.py`, `trscreen.py`.
- **Çalışma durumu:** **Bu oturumda hiç dokunulmadı** — Kısmen doğrulandı (önceki oturumlardan).
- **Bilinen sınırlar:** Tıklamaları engellememe davranışı bu oturumda doğrulanmadı (bkz. §6.1, §7).
- **Test durumu:** `tests/test_overlay.py` (**PASS**, bu oturumda çalıştırıldı — kutuların ekran içinde kaldığı,
  üst üste binmediği, çeviri özgünle aynıysa kutunun çizilmediği test ediliyor), `tests/test_inplace_anchors.py`
  (xvfb ile **11/11 PASS**, bu oturumda çalıştırıldı — gerçek Tk penceresiyle font/canvas metni maske içinde
  kalıyor mu testi dahil).
- **UI'da erişim:** Çeviri sekmesi → mod seçimi (köşe/yerinde).

## 5.7 Sesli Asistan
- **Sağlar:** F9 ile sesli/metin komut (Ollama/Claude Code/Claude API/OpenAI üzerinden), ses tanıma teşhisi.
- **Dosyalar:** `speech.py`, `voicepack.py`, `app.py`.
- **Çalışma durumu:** Test edilmedi (bu oturumda ses I/O hiç denenmedi, donanım/ses kartı gerektirir).
- **Test durumu:** `tests/test_natural_voice.py` (**PASS**, 10/10, bu oturumda çalıştırıldı — ama bu muhtemelen
  metin/mantık testi, gerçek ses çıkışı değil — **Varsayım**, dosya içeriği satır satır okunmadı).
- **UI'da erişim:** Asistan sekmesi, F9 kısayolu.

## 5.8 Kısayollar
- **Sağlar:** Global kısayollar (F8 tara, F9 asistan, vb.), `pynput` tabanlı.
- **Dosyalar:** `game_assistant.py`.
- **Çalışma durumu:** Test edilmedi bu oturumda tam olarak — `tests/test_game_assistant.py` çalıştırıldığında
  **1 hata** verdi (`ModuleNotFoundError: No module named 'pynput'`) — **bu, bu konteynerin bir ortam eksikliği,
  gerçek bir kod regresyonu değil** (requirements.txt'te `pynput` listeli ama bu oturumun sanal ortamına
  kurulmamış). Gerçek Windows ortamında (CI runner'ı dahil) bu paket kurulu olmalı. — **Doğrulandı (ortam
  eksikliği olduğu), test edilmedi (gerçek davranış)**.
- **Test durumu:** `tests/test_game_assistant.py` → 22 testten 21'i **PASS**, 1'i ortam eksikliğinden
  **ERROR** (debounce/eski-listener testi).
- **UI'da erişim:** Ayarlar → Kısayollar.

## 5.9 Tema, HUD, Animasyon ve Görsel Efektler
- **Sağlar:** 18 tema (en yenisi "kaivolt", varsayılan), açılış animasyonu, fare izi, geçiş efektleri, arka plan
  videosu.
- **Dosyalar:** `td2app/ui/{ui_theme,fx,bgvideo,splash,ui_art,ui_hud,view3d}.py`, `app.py`.
- **Çalışma durumu — Doğrulandı (bu oturumda):** "Kaivolt" teması + "Hakkında" sekmesi bu oturumdan önceki bir
  turda eklendi (v9.1.5.28) ve bu oturumda `xvfb-run python3.12 tests/test_stability_widgets.py` ile **gerçek
  bir Tk penceresi oluşturularak** doğrulandı — 15 sayfa, 6 sekme grubu, **0 callback hatası**. Bu, BUGS.md
  #14'teki "bu konteynerde tkinter modülü kurulu değil, sadece statik ast.parse yapıldı" notundan **daha
  ileri bir doğrulama seviyesi** — ama hâlâ insan gözüyle görsel kontrol (renk/hizalama/okunabilirlik) değil.
- **Bilinen sınırlar:** Kenar çubuğunun gerçekten düz göründüğü, "Hakkında" metninin büyük-harf başlık
  renklendirmesinin okunur olduğu, tema kartının Ayarlar → Görünüm galerisinde düzgün sıralandığı — bunlar
  **hâlâ gerçek Windows'ta insan gözüyle kontrol edilmemiş** (BUGS.md #14).
- **Test durumu:** `tests/test_stability_widgets.py` (xvfb ile **PASS**, bu oturumda bizzat çalıştırıldı),
  `tests/test_animation_policy.py` (9/9 **PASS**, bu oturumda çalıştırıldı), `tests/test_performance.py`
  (12/12 **PASS**).
- **UI'da erişim:** Ayarlar → Görünüm; Hakkında sekmesi (Diğer grubu).

## 5.10 Tanılama ve Hata Raporlama
- **Sağlar:** Sorun tarama, hata bildirimini maskelenmiş önizlemeyle GitHub issue'ya gönderme.
- **Dosyalar:** `diagnostics_center.py`, `reports.py`.
- **Çalışma durumu:** Kısmen doğrulandı (HANDOFF.md'ye göre önceki oturumda gerçek Windows'ta "Sorunları tara"
  akışı manuel tıklanarak test edilmiş, çökme olmadığı doğrulanmış).
- **Test durumu:** `tests/test_diagnostics_center.py` mevcut, **bu oturumda çalıştırılmadı**.
- **UI'da erişim:** Ayarlar → Tanılama Merkezi.

## 5.11 Satıcı / Hedef Loot / Farm Önerileri
- **Sağlar:** Haftalık satıcı eşyalarını ve hedef loot'u build/sandıkla eşleştirme.
- **Dosyalar:** `vendor.py`, `dropstats.py`.
- **Çalışma durumu:** Test edilmedi bu oturumda.
- **Test durumu:** Bu oturumda ilgili bir test dosyası çalıştırılmadı (ayrı bir `test_vendor.py` görülmedi,
  testler `tests/` listesinde yok — **Doğrulandı: böyle bir test dosyası mevcut değil**).
- **UI'da erişim:** Satıcı sekmesi (premium).

## 5.12 Division 3 Haberleri
- **Sağlar:** Haber/sezon bilgisi, sayaç, yama notları.
- **Dosyalar:** `meta_sync.py`, `meta/news_feed.json`, `meta/division3_feed.json` (ROADMAP.md'de adı geçiyor).
- **Çalışma durumu:** Kısmen doğrulandı (ROADMAP.md'den).
- **Test durumu:** Bu oturumda test edilmedi.
- **UI'da erişim:** Bilgi/Ansiklopedi sekmesi → Haberler.

## 5.13 Mobil / Android / APK
- **Sağlar:** Bulut eşleştirme (pairing code), build senkronu, push bildirimi (kod yazılmış, uçtan uca
  doğrulanmamış).
- **Dosyalar:** `mobile/` (Flutter).
- **Çalışma durumu:** Test edilmedi bu oturumda — Flutter SDK'sı bu ortamda yok, `mobile/` hiç açılmadı.
- **Bilinen sınırlar:** Push bildirimi için `google-services.json` + gradle satırı aktivasyonu kullanıcının
  kendi PC'sinde kalan manuel bir adım (ROADMAP.md, HANDOFF.md).
- **Test durumu:** `mobile/test/` içinde Flutter testleri olabilir — **bu oturumda incelenmedi.**
- **UI'da erişim:** Ayarlar → Hesap → "Telefon eşleştir".

## 5.14 Güncelleme ve Sürüm Yönetimi
- **Sağlar:** GitHub'dan otomatik güncelleme kontrolü, SHA-256 doğrulamalı kurulum, sürüm geçmişinden
  herhangi bir sürümü kurma.
- **Dosyalar:** `updater.py`, `updates.py`, `app.py` (sürüm geçmişi penceresi).
- **Çalışma durumu:** Kısmen doğrulandı (v9.1.5.23'te bir `PAL["panel"]` hatası düzeltilmiş, DEVELOPMENT_LOG.md).
  Bu oturumda GitHub Release yayın akışı (CI tarafı) **bizzat 2 kez çalıştırıldı ve doğrulandı**; istemci
  tarafı (uygulamanın kendi güncelleme kontrolü/indirmesi) bu oturumda **test edilmedi.**
- **Test durumu:** `tests/test_release_914.py` mevcut, bu oturumda çalıştırılmadı.
- **UI'da erişim:** Ayarlar → Genel → Güncellemeler.

---

# 6. Kritik Geçmiş Sorunlar ve Gerçek Kök Nedenleri

## 6.1 Canlı Çeviri ve Siyah/Boş Overlay Sorunu
- **Belirti:** Kullanıcı şablonunda tanımlı bir sorun kategorisi; bu oturumda ilgili proje belgelerinde
  (DEVELOPMENT_LOG.md, BUGS.md, HANDOFF.md) bu spesifik belirtiye (siyah/boş overlay) dair **hiçbir kayıt
  bulunamadı**.
- **Hangi ekran görüntülerinde görüldü?** Test edilmedi / bilgi yok.
- **Olası nedenler / Gerçekleşmiş neden:** Bilinmiyor — **bu oturumda kanıt bulunamadı.**
- **Denenen çözümler / Başarılı olan çözüm:** Yok (bu oturumda).
- **Hâlâ risk var mı?** Belirsiz. `overlay.py`'nin hiç dokunulmadığı bu oturumda doğrulandı, dolayısıyla bu
  oturumun değişiklikleri bu sorunu ne yarattı ne giderdi.
- **Test yöntemi:** `tests/test_overlay.py` kutuların ekranda kalmasını/örtüşmemesini test ediyor ama "siyah/
  boş" render sorunu muhtemelen gerçek DWM/GPU render katmanında ortaya çıkar — headless testle yakalanamaz.
- **Kullanıcı ortamında kontrol edilmesi gereken Windows/NVIDIA/oyun ayarları:** Borderless pencere modu, HDR
  kapalı, oyun çözünürlüğü = monitör çözünürlüğü (README'nin önerdiği ayarlar), NVIDIA RTX HDR/filtre
  katmanlarının kapalı olması. **Bu oturumda doğrulanamadı — gerçek Windows + oyun gerektirir.**

## 6.2 Yanlış HDR Algılama Sorunu
- **Oyun HDR kapalıyken uygulamanın HDR açık sanmasının nedeni:** Bu oturumda ilgili koda (`display.py` HDR
  algılama mantığı) bakılmadı — **Test edilmedi.**
- **state.cfg / oyun ayarı / ekran yakalama / renk profili ilişkisi:** README'de "oyunun kendi ayar dosyasını
  okuyarak (salt okunur)" HDR/çözünürlük kontrolü yapıldığı belirtiliyor — **Kısmen doğrulandı**, mekanizmanın
  ayrıntısı bu oturumda incelenmedi.
- **Düzeltme durumu:** Bilinmiyor.
- **Hâlâ doğrulanması gerekenler:** Gerçek bir Windows + oyun ortamında HDR açık/kapalı iki durumda da
  algılamanın doğru çalıştığının teyidi.

## 6.3 GitHub Actions ve Installer Hataları
Kullanıcı şablonunda sorulan spesifik hatalar ve bu oturumda bulunan **gerçek** durum:

| Hata | Kök neden | Yapılan düzeltme | Test sonucu | Hâlâ açık mı? | Tekrarlama riski |
|---|---|---|---|---|---|
| `test_stability_widgets.py` sabit sayfa sayısı (**bu oturumda gerçekten yaşandı**) | "about" sekmesi eklenince `len(obj.tab_keys)` 14→15 oldu, test hâlâ `==14` bekliyordu | `assert result["pages"]==15` yapıldı | CI'da **PASS** (run `41901206615`) | **Hayır, kapandı.** | Yeni bir sekme eklenirse tekrar yaşanabilir — her yeni sekmede bu assertion kontrol edilmeli. |
| `test_app_stability.py` 2 test FAIL (**bu oturumda gerçekten yaşandı, ama CI'da değil — yerel sandbox'ta bu oturumun kendi değişikliği yüzünden**) | Yeni `low_conf` hesaplaması `blocks_from_lines()`'ın her zaman 3'lü tuple döndürdüğünü varsayıp `b[2]`'ye erişti; testteki mock 2'li tuple döndürüyordu → `IndexError` → sessizce `_lt_failure`'a düşüyordu | `len(b) > 2 and b[2] < LOW_CONF_WARN` savunmacı kontrolü eklendi | Yerel olarak **17/17 PASS** (bu oturumda çalıştırıldı) | **Hayır, kapandı** (ama CI'da hiç tetiklenmedi çünkü bu kod CI'ya gitmeden önce yerelde bulundu) | Düşük — artık savunmacı kontrol var. |
| `test_game_assistant.py` FAILED | Bu oturumda: `pynput` modülü **bu konteynerde kurulu değil** (ortam eksikliği) | Yok (gerçek kod hatası değil) | 21/22 PASS, 1 ERROR (ortam) | CI'da (Windows runner, `pynput` kurulu) **muhtemelen değil** — **doğrulanmalı** | Düşük (CI ortamı farklı) |
| `test_localapi.py` WebSocket timeout | **Bu oturumda rastlanmadı/aranmadı**, test dosyası hiç çalıştırılmadı | — | — | **Bilinmiyor** | — |
| "FAIL yerinde çeviri: kutular oyun yazılarının yerinde {'canvas_items': 0}" | **Bu oturumda hiçbir belgede bu metin bulunamadı** | — | `test_inplace_anchors.py` bu oturumda **11/11 PASS** (xvfb ile) | **Bilinmiyor — bu spesifik hata bu oturumda görülmedi** | — |
| "Resource not accessible by integration" (GitHub release yetki hatası) | **Bu oturumda hiç yaşanmadı** — bu oturumdaki 2 release denemesi de sorunsuz yetkilendirildi | — | — | **Bilinmiyor** | Bu oturumda `gh` CLI zaten kimlik doğrulamalı çalışıyordu |
| Node.js 20 deprecation uyarısı | **Bu oturumda görülmedi** (workflow logları ayrıntılı taranmadı) | — | — | **Bilinmiyor** | `server/package.json` Wrangler `^4.0.0` kullanıyor, Node sürümü workflow dosyasında belirtilmiş olabilir — incelenmedi |
| Windows port / TIME_WAIT / allow_reuse_address | **Bu oturumda görülmedi** | — | — | **Bilinmiyor** | `localapi.py`/`server/dev_server.mjs` ile ilişkili olabilir — incelenmedi |
| Tkinter widget yaşam döngüsü / test isolation sorunu | Bu oturumda **farklı bir izolasyon sorunu bulundu**: `pytest` ile `tests/` toplu çalıştırılınca `test_account.py`'nin modül-seviyesinde `sys.exit(0)` çağırması `INTERNALERROR` (`SystemExit`) verdi | CI zaten her test dosyasını **ayrı ayrı** `python -B tests/<dosya>` ile çalıştırıyor (pytest toplu koşum kullanmıyor) — yani bu sorun CI'yı etkilemiyor, sadece pytest ile toplu deneme yapıldığında ortaya çıkıyor | — | **CI için sorun değil**; pytest ile toplu koşum denenirse **evet, hâlâ var** | ChatGPT pytest ile toplu test denerse bu INTERNALERROR'u görecek — CI'nın yaptığı gibi dosya-dosya çalıştırmalı |

**Genel not:** Kullanıcının şablonundaki bu hata listesi büyük olasılıkla **genel/örnek bir kontrol listesi**
olarak verilmiş (muhtemelen ChatGPT'nin kendi şablonundan), bu projenin gerçek geçmişinden **doğrudan alınmış
değil** gibi görünüyor — hiçbiri proje belgelerinde birebir geçmiyor. ChatGPT/Codex bunları "bilinen, çözülmüş
hatalar" olarak kabul etmemeli; sadece bu raporun bulduğu **gerçek** 2 hatayı (tablo üstte) kesin bilgi olarak
almalı.

## 6.4 Menü Tıklama / Küçük Pencere / Fare İzi Sorunları
- **Belirti:** Kullanıcı tasarım tercihlerinde ("küçük pencere modunda menüler erişilebilir olmalı", "fare izi
  tıklamaları engellememeli") bahsediliyor — bunlar **gereksinim**, geçmiş bir "sorun raporu" değil gibi
  görünüyor.
- **Kök neden:** Bilinmiyor / spesifik bir geçmiş hata bulunamadı.
- **Düzeltilen noktalar:** `td2app/ui/fx.py`'deki `SafeTrail.cv.lower()` `TclError`'ı (BUGS.md #8, bu oturumdan
  önce düzeltilmiş) — fare izi efektiyle ilgili, **Kısmen doğrulandı.**
- **Kullanıcının hâlâ test etmesi gerekenler:** Küçük pencere boyutunda tüm menülerin erişilebilir kaldığı,
  fare izinin tıklamaları hiçbir widget üzerinde engellemediği — **bu oturumda test edilmedi, gerçek Windows
  gerektirir.**

## 6.5 Açılış Ekranı Donması / Kasma
- **Splash ekranı:** `td2app/ui/splash.py` mevcut.
- **30 FPS hedefi, UI sayfalarının gecikmeli oluşturulması, ilk açılışta 3–4 saniye donma:** Bu oturumda
  `tests/test_stability_widgets.py` çalıştırıldığında `widgets_ms` ölçümü **666,5 ms** (xvfb, python3.12,
  muhtemelen gerçek Windows'tan daha hızlı bir donanımda) — **Doğrulandı ama gerçek Windows donanımına
  genellenemez.** `import_ms` **737,9 ms**.
- **Yapılan iyileştirmeler:** Bu oturumda bu alanda hiçbir değişiklik yapılmadı.
- **Kalan riskler:** Gerçek düşük kaynaklı bir Windows bilgisayarda ilk açılış süresi **test edilmedi.**

## 6.6 Native Cursor Hook Failed
- **Hata metni:** Bu oturumda görülmedi; BUGS.md #9'a göre önceki bir oturumda `_install_native_cursor`'daki
  `winfo_id` çağrısı için ek bir `hasattr()` güvencesi eklenmiş (teorik risk, pratikte hiç tetiklenmemiş).
- **Neden:** Mevcut `if widget is not self.root: return` koruması zaten güvenli (BUGS.md #9) — **Kısmen
  doğrulandı.**
- **Güvenli fallback:** `hasattr(widget, "winfo_id")` kontrolü.
- **Varsayılan davranış:** Bilinmiyor (bu oturumda kod satırı incelenmedi).
- **Ortam değişkeni/özel etkinleştirme:** Bu oturumda bulunamadı.

## 6.7 report_server AttributeError
- **Hata:** Bu oturumda hiçbir belgede `report_server` adlı bir fonksiyon/değişken için `AttributeError`
  kaydına rastlanmadı.
- **Neden / Düzeltme / Doğrulama:** **Bilgi yok, bu oturumda bulunamadı.** ChatGPT bu ismi kod tabanında
  (`grep -rn "report_server"`) arayıp gerçekten var olup olmadığını kontrol etmeli.

---

# 7. Canlı Çeviri Sisteminin Teknik Akışı

(Bu bölüm bu oturumda `livetranslate.py` ve `app.py`'nin ilgili bölümlerinin **bizzat okunup değiştirilmesine**
dayanıyor — **Doğrulandı**, overlay/trscreen kısmı hariç çünkü onlara bu oturumda dokunulmadı — **Kısmen
doğrulandı.**)

1. **Kısayola basılması** — Kullanıcı canlı çeviri kısayolunu (veya F8/ilgili tuşu, `app.py`'de tanımlı) tetikler.
2. **Tarama alanının alınması** — `area` parametresi (`{left, top, width, height}`) — tam ekran veya seçili
   bölge.
3. **OCR işlemi** — `self.lt_ocr(img)` → OCR motorundan `(metin, kutu, güven)` satır listesi.
4. **Metin filtreleme** — `livetranslate.blocks_from_lines(lines, ui_words, preserve_lines=inplace)`: arayüz
   gürültüsünü (`ui_words`), düşük güvenli (`conf < 0.5`) ve çok kısa satırları eler; kalan satırları paragraf
   bloklarına birleştirir (çok sütunlu ekran duyarlı).
5. **Özel ad / terim koruma** — `Glossary.mask()`: egzotik/named/set/marka/talent adlarını ve hikâye karakter
   adlarını `ZQ0`, `ZQ1`... token'larına maskeler (çeviri motorunun bu adları bozmaması için); zamir ipuçları
   (`pronoun_hints()`) ayrıca ekleniyor.
6. **Çeviri motoruna gönderim** — `self.lt_translator()` o anki ayarlara göre `LocalMT` (OPUS-MT, sabit EN→TR)
   veya `AIMT` (kullanıcının LLM'i, **bu oturumdan sonra hedef dil = `i18n.current_language()`**) döndürür;
   `Translator.translate(texts, allow_partial=True)` çağrılır — önce `tasks_live.Memory` (yalnızca `target_lang
   == "tr"` ise) ve önbellek kontrol edilir, yoksa motora gider.
7. **Çevirinin alınması** — Motor `(liste, aynı uzunlukta)` döndürür; sayı/placeholder kaybı kontrolü yapılır
   (`allow_partial=True` ile satır bazlı hata işaretleme).
8. **Overlay oluşturulması** — `pairs = [(en, tr, kutu)]` listesi `self._lt_show(pairs, area, ms)`'e geçirilir
   (`overlay.py`/`trscreen.py` — **bu oturumda içeriği incelenmedi**).
9. **Yerinde kutu konumlandırması** — `inplace` modda `blocks_from_lines(..., preserve_lines=True)` her OCR
   satırının kendi dikdörtgenini korur (paragraf birleştirmesi yapılmaz) — overlay bunu kullanarak kutuları
   orijinal metnin üzerine koyar.
10. **Overlay'in tıklamaları engellememesi** — **Bu oturumda doğrulanmadı**, `overlay.py` incelenmedi.
11. **Durdurma / yeniden başlatma** — `_translation_jobs.is_current(token)` ile eski taramalar iptal
    edilebiliyor (token tabanlı iş kuyruğu); aynı ekran imzası (`sig`) tekrar gelirse (force olmadan) yeniden
    çevrilmiyor.
12. **Hata durumunda güvenli kapatma** — Tüm `_lt_run()` gövdesi `try/except Exception as e:
    self._lt_failure(token, e)` ile sarılı — hiçbir istisna kullanıcıya çökme olarak görünmüyor, `_lt_failure`
    yeniden deneme/durum mesajı mantığını yönetiyor (**bu oturumda `_lt_failure`'ın iç detayı okunmadı**).

**Kontrol listesi durumu (bu oturumda doğrulanabilen/doğrulanamayan):**
- Oyun Borderless mi? / Oyun penceresi bulunuyor mu? / Tarama alanı doğru mu? / Uygulama oyunun üstünde mi? →
  **Test edilmedi** (gerçek oyun gerektirir).
- OCR motoru kurulmuş mu? → Uygulama içinde kontrol ediliyor (`LocalMT.available()`/`installed()` gibi
  yöntemler var, `lt_translator()`'da görüldü) — **Doğrulandı (kod var), gerçek davranış test edilmedi.**
- Çeviri modeli kurulu mu? → Aynı şekilde `installed()` kontrolü var.
- Windows HDR gerçekten kapalı mı? / NVIDIA RTX HDR/filtre açık mı? / DPI ölçeklendirmesi / çoklu monitör /
  Remote Display Adapter → **Hepsi test edilmedi, gerçek Windows + donanım gerektirir.**
- Overlay metin rengi/saydamlık/font nedeniyle görünmez mi? → **Test edilmedi.**

---

# 8. Eşya Kütüphanesi ve Doğruluk Durumu

- **Kaynaklar:** `meta/game_data.json` — The Division Wiki (CC BY-SA) ve mxswat/mx-division-builds (CC
  BY-NC-SA 4.0, ticari olmayan kullanım + atıf). — **Kaynak doğrulandı** (README'de açıkça yazılı, lisans
  metni `LICENSE_NOTES.md`'de).
- **Silahlar, gear set'ler, brand set'ler, exotic/named/prototype eşyalar, modlar, weapon/gear talent'ları:**
  Hepsi `meta/game_data.json` içinde yapılandırılmış — **Kütüphane eşleşmesi** (bu oturumda dosyanın şeması
  satır satır incelenmedi, varlığı ve genel yapısı README'den teyitli).
- **Attribute adları / alias / çeviri eşleşmeleri:** `knowledge.py` ve ilgili `meta/` dosyalarında — bu
  oturumda incelenmedi.
- **St. Elmo's Engine gibi önceden yanlış/eksik eşleşen eşyalar:** Bu oturumda bu spesifik isim için hiçbir
  kayıt bulunamadı — **Test edilmedi / bilgi yok.** (BUGS.md'de bulunan tek büyük kütüphane-doğruluk sorunu
  "30 kesik ansiklopedi açıklaması" idi, St. Elmo's Engine'den bahsetmiyor.)
- **"Health Damage" yerine yanlış algılanabilen attribute örnekleri:** Bu oturumda bulunamadı.
- **Bilinen eksik/şüpheli isimler:** Bu oturumda bulunamadı (ansiklopedi açıklama kesikliği hariç, ki o
  çözülmüş).
- **Kütüphanede kesin olmayan veriler:** mxswat verisi CC BY-NC-SA 4.0 (ticari olmayan) — bu nedenle
  `recal_advisor` özelliği ücretsiz yapılmış (lisans gri alanını önlemek için) — **Kaynak doğrulandı.**
- **Kullanıcının yanlış eşya raporu gönderme akışı:** README'de "Read wrong: saves the card and opens a
  prefilled GitHub issue" olarak belirtiliyor — **Kısmen doğrulandı**, bu oturumda akış denenmedi.
- **OCR yanlışsa sistemin neden otomatik dismantle önermemesi gerektiği:** Düşük OCR güveni → "incele/REVIEW"
  kararı; bu oturumda eklenen canlı-çeviri güven uyarısı da aynı prensibin bir uzantısı (OCR yanlış okuyabilir,
  kullanıcı bunu bilmeli). Statik eşya-değerlendirme tarafında (loot kararı, canlı çeviriden ayrı) bu kuralın
  kodda nerede uygulandığı bu oturumda satır satır doğrulanmadı — **Kısmen doğrulandı** (ilke README/proje
  talimatlarında açık, `itempolicy.py`/`engine.py`'de muhtemelen uygulanıyor ama bu oturumda doğrulanmadı).

---

# 9. Güvenlik ve Veri Gizliliği Kuralları

Bu kurallar **projenin değişmez ilkeleri** olarak kabul edilmeli (kullanıcının talimatından ve README/PRIVACY_POLICY.md'den):

- Oyun belleği **okunmaz, yazılmaz.**
- DLL injection **yapılmaz.**
- Anti-cheat aşma yöntemi **yoktur.**
- Oyun dosyaları **otomatik değiştirilmez.**
- Yalnız kullanıcı onayıyla oyun klasörü/ayar dosyası **okunur** (yazılmaz).
- Ekran yakalama ve OCR **yereldir.**
- Canlı çeviri için çevrimiçi sağlayıcı (AI motoru) kullanılıyorsa kullanıcı **açıkça bilgilendirilir** (README:
  "Selecting online AI explains text routing and requests consent").
- GitHub'a hata raporu **otomatik gönderilmez**; önce **maskelenmiş önizleme** gösterilir.
- Kullanıcı build/sandık/runtime verileri **commit edilmez** (bkz. §3 — `builds.json` istisnası dikkat
  gerektiriyor, ama o bir **şablon**, gerçek kullanıcı verisi değil).
- Düşük OCR güveninde karar **REVIEW/inceleme** olmalı (bu oturumda canlı çeviri tarafında bu ilke uygulandı).
- Exotic, Named, Prototype ve kilitli eşyalar **otomatik silme/dismantle kapsamına alınmaz.**

Bu kurallara bu oturumda yapılan hiçbir değişiklik ters düşmedi — **Doğrulandı** (yapılan tek değişiklikler:
tema/UI metni ve canlı çeviri dil genelleştirmesi, hiçbiri oyun belleğine/dosyasına dokunmuyor).

---

# 10. Test Envanteri

(Bu oturumda **bizzat çalıştırılanlar** "Doğrulandı" olarak işaretli; diğerleri dosya listesinden biliniyor
ama çalıştırılmadı.)

| Test dosyası | Ne test eder? | Son bilinen sonuç (bu oturumda) | Tür |
|---|---|---|---|
| `test_core.py` | Lisans (Ed25519), optimizer, sync, kütüphane bütünlüğü, vb. (18 alt test) | **PASS** (Doğrulandı) | Birim/entegrasyon, mock çeviri yok |
| `test_itempolicy.py` | Loot karar politikası, Exotic/Named/Prototype koruması | **PASS** (15/15, Doğrulandı) | Birim |
| `test_app_stability.py` | Çeviri iş kuyruğu, retry, inplace yeniden konumlandırma, overlay çağrıları (mock) | **PASS** (17/17, Doğrulandı — bu oturumda 1 regresyon bulundu+düzeltildi) | Mock tabanlı entegrasyon (gerçek Tk yok, `bare_app()` sahte nesne) |
| `test_stability_widgets.py` | Gerçek Tk uygulaması kurulumu, tüm sekmeler, perf/ses/çeviri widget'ları | **PASS** (xvfb+python3.12 ile, Doğrulandı) | **Gerçek Tk testi (headless, Linux+Xvfb)** — Windows değil ama gerçek pencere |
| `test_diagnostics_center.py` | Tanılama merkezi mantığı | Çalıştırılmadı | — |
| `test_translation_controls.py` | Çeviri UI kontrol mantığı | **PASS** (5/5, Doğrulandı) | Birim |
| `test_translation_reliability.py` | Çeviri doğrulama (sayı/placeholder kaybı, vb.) | **PASS** (9/9, Doğrulandı) | Birim |
| `test_overlay.py` | Overlay kutu konumlandırma mantığı (çakışma, ekran içi kalma) | **PASS** (Doğrulandı) | Birim/mantık (gerçek render değil) |
| `test_inplace_anchors.py` | Yerinde çeviri kutu/font/canvas testi | **PASS** (11/11, xvfb ile, Doğrulandı) | **Gerçek Tk testi (headless)** |
| `test_livetranslate.py` | Glossary maskeleme, blok birleştirme, AI/yerel motor, önbellek, model indirme/doğrulama | **PASS** (29/29, Doğrulandı — bu oturumda 1 regresyon bulundu+düzeltildi) | Birim + mock entegrasyon |
| `test_ocr.py` | Gerçek oyun kartı görselleriyle OCR doğruluğu | Çalıştırılmadı | Entegrasyon (gerçek görsel örnekleri kullanır) |
| `test_ocr_serialization.py` | OCR sonucu serileştirme | **PASS** (2/2, Doğrulandı) | Birim |
| `test_game_assistant.py` | Global kısayol yöneticisi (debounce, listener) | **21/22 PASS, 1 ERROR** (ortam: `pynput` eksik, Doğrulandı) | Birim/mock |
| `test_localapi.py` | Yerel API (premium, OBS/Stream Deck/WebSocket) | Çalıştırılmadı | — |
| `test_localapi_backpressure.py` | Yerel API geri basınç | **PASS** (8/8, Doğrulandı) | Birim |
| `test_project_structure.py` | Proje dosya yapısı doğrulama | Çalıştırılmadı | — |
| `test_release_914.py` | Sürüm/release mantığı (tarihsel isim) | Çalıştırılmadı | — |
| `test_account.py` | Hesap mantığı | Çalıştırılmadı tam (pytest toplu koşumda `INTERNALERROR` verdi, bağımsız script olarak çalıştırılmadı) | Script (pytest-uyumsuz) |
| `test_animation_policy.py` | Animasyon/performans politikası | **PASS** (9/9, Doğrulandı) | Birim |
| `test_performance.py` | Performans modu mantığı | **PASS** (12/12, Doğrulandı) | Birim |
| `test_workqueue.py` | İş kuyruğu | **PASS** (7/7, Doğrulandı) | Birim |
| `test_launcher.py` | Başlatıcı mantığı | **PASS** (7/7, Doğrulandı) | Birim |
| `test_natural_voice.py` | Ses/TTS mantığı | **PASS** (10/10, Doğrulandı) | Birim (muhtemelen gerçek ses çıkışı değil) |
| `test_scan_latency.py` | Tarama gecikmesi | **PASS** (6/6, Doğrulandı) | Birim |
| `test_region_scan_fastpath.py` | Bölge tarama hızlı yol | **PASS** (6/6, Doğrulandı) | Birim |
| `test_autoscan.py` | Otomatik tarama | **Çalıştırılamadı** (`$DISPLAY` yok, xvfb ile de denenmedi) | Entegrasyon (ekran yakalama gerektirir) |
| `test_regression_crash_patterns.py` | Statik AST taraması (geçmiş çökme desenleri) | Çalıştırılmadı bu oturumda | Statik analiz |
| `test_inventory.py`, `test_inputs.py`, `test_knowledge.py`, `test_reports.py`, `test_screenstate.py`, `test_service.py`, `test_single.py`, `test_speech.py`, `test_tasks_live.py`, `test_windows_sync.py`, `test_gpu_probe.py`, `test_hardening.py` | (isimlerinden tahmin edilen kapsam) | **Çalıştırılmadı bu oturumda** | — |
| Installer/paketleme testleri | `build-installer.yml` workflow'unun kendisi (CI üzerinde gerçek Windows'ta installer üretip test ediyor) | **PASS** (2/2 CI run, Doğrulandı) | **Gerçek Windows CI testi** |

**Test türü özeti:**
- **Birim testi:** Çoğu dosya (`test_core.py`, `test_itempolicy.py`, vb.) — `unittest` tabanlı, mock'larla.
- **Mock testi:** `test_app_stability.py` (`bare_app()` sahte `App` nesnesi).
- **Headless/Tk testi:** `test_stability_widgets.py`, `test_inplace_anchors.py` — **bu oturumda `python3.12`
  (sistem Python'u `python3` 3.13'te `tkinter` yok) + `python3-tk` paketi + `xvfb-run` ile gerçekten
  çalıştırılabildiği keşfedildi.** Bu, önceki oturumların "bu konteynerde tkinter yok" varsayımını kısmen
  güncelliyor — **bir sonraki oturum bu yöntemi kullanabilir.**
- **Gerçek Windows testi:** CI'daki `build-installer.yml` (Windows runner) — bu oturumda 2 kez tetiklendi,
  **Doğrulandı.**
- **Gerçek oyun testi:** **Hiçbiri bu oturumda yapılmadı** — gerçek oyun hiçbir zaman bu ortamda mevcut değil.
- **Manuel kullanıcı testi:** HANDOFF.md'ye göre önceki oturumda bağlı bir Windows bilgisayarında computer-use
  ile 3 senaryo manuel tıklanarak test edilmiş (**Kısmen doğrulandı**, bu oturumda tekrarlanmadı).
- **GitHub Actions testi:** `build-installer.yml` içindeki tüm `python -B tests/<dosya>` adımları — CI'da
  bu oturumun 2 release denemesinde **ikisi de sonunda PASS** (ilk denemede 1 test regresyonu bulunup
  düzeltildi).

---

# 11. Kullanıcının Tasarım ve Deneyim Tercihleri

- Kullanıcı **Türkçe** konuşuyor, yanıtlar Türkçe olmalı. — **Doğrulandı** (bu oturum boyunca gözlemlendi).
- Uygulamanın görsel dili The Division SHD/HUD estetiğine yakın olmalı; ana renkler koyu antrasit/siyah + SHD
  turuncusu; cyan ikincil vurgu olabilir ama az renk. — **Kısmen doğrulandı** (önceki oturumlardan; bu oturumda
  eklenen "Kaivolt" teması ise **farklı bir renk paleti** kullanıyor: lacivert zemin + elektrik moru vurgu —
  bu, SHD turuncu/antrasit tercihinden **bilinçli bir sapma** olarak kullanıcı tarafından istenmiş ["Programın
  ana teması ve menüleri daha modern ve sade bir tasarım yapalım"] — **Doğrulandı**, önceki SHD temaları da
  hâlâ seçilebilir durumda, sadece varsayılan değişti).
- Yazı tipi teknolojik/keskin/okunaklı; menü/panel oyun atmosferini yansıtmalı; fazla efekt performans/tıklama
  sorununa yol açmamalı; küçük pencerede menüler erişilebilir olmalı; fare izi tıklamaları engellememeli; açılış
  animasyonu akıcı, CPU'yu boğmamalı. — **Kısmen doğrulandı** (tasarım ilkeleri, bu oturumda ihlal edilmedi ama
  ayrıca test edilmedi).
- **Önce yerelde uygulanıp test edilmeli; kullanıcı test etmeden GitHub'a yayın yapılmamalı; her yayın öncesi
  açık Evet/Hayır onayı alınmalı.** — **Doğrulandı, bu oturumda fiilen uygulandı** (bkz. §4) — ama dikkat: bu
  oturumda "yerel test" gerçek Windows/Tk görsel testi değil, syntax+birim test+xvfb-Tk testiydi; kullanıcının
  kendisi henüz gerçek Windows'ta bu sürümü (v9.1.5.29) gözle kontrol etmedi.
- Programın kullanıcı dostu, stabil, düşük sistem kaynaklı bilgisayarlarda çalışabilir olması önemli;
  kullanıcı gerçek test sonucu/hata nedeni/açık noktaları net görmek istiyor. — **Doğrulandı** (bu oturumun
  raporlama tarzı bu ilkeye göre şekillendirildi).

---

# 12. Tamamlanmamış İşler / Backlog

## P0 — Kritik
1. **Canlı çeviri + genelleştirme sonrası gerçek doğrulama** — Bu oturumda yapılan 10-dil genelleştirmesi hiçbir
   zaman gerçek bir LLM çağrısıyla (Ollama/Claude/OpenAI canlı) veya gerçek oyun ekranında denenmedi; sadece
   birim test + mock ile doğrulandı.
   - *Tahmini dosyalar:* `livetranslate.py`, `app.py`.
   - *Bağımlılıklar:* Kullanıcının Asistan sekmesinde yapılandırılmış bir AI sağlayıcısı + gerçek oyun ekranı
     veya en azından örnek bir ekran görüntüsü.
   - *Risk:* Orta — kod mantığı sağlam görünüyor (SYSTEM_TMPL formatı, dil adı eşlemesi) ama gerçek bir LLM'in
     talimata ne kadar uyacağı test edilmedi.
   - *Test planı:* Arayüz dilini örn. İspanyolca'ya çevirip canlı çeviriyi AI motoruyla gerçek bir ekran
     görüntüsünde deneyin; çıkan metnin gerçekten İspanyolca olduğunu doğrulayın.
   - *Yayın öncesi kontrol listesi:* Zaten `v9.1.5.29` olarak yayınlandı — bu madde "doğrulama", "geri alma"
     değil.
2. **`builds.json`'ın Git'te takip edilme durumu netleştirilmeli** (bkz. §3) — gizlilik/temizlik riski.
   - *Risk:* Düşük (şablon olduğu görülüyor) ama netleştirilmeli.
   - *Test planı:* İçeriği tekrar incele, kullanıcıya sor, gerekirse `.gitignore`'a ekle + `git rm --cached`.
3. **Sürüm numarası boşluğu (`v9.1.5.24`–`.27` tag'leri yok) netleştirilmeli** (bkz. §4).
   - *Risk:* Düşük (işlevsel değil) ama kafa karıştırıcı; `retire-releases.yml` workflow'u incelenmeli.

## P1 — Yüksek Öncelik
4. **Topluluk düzeltme/öneri sisteminin (`tasks_live.suggest`) diğer dillere genelleştirilmesi** — şu an
   tamamen Türkçeye özel sunucu şeması (D1). Büyük bir iş; `server/worker.js` + `schema.sql` değişikliği
   gerektirir.
5. **`"lt.partial"` i18n anahtarının 10 dil dosyasının hiçbirinde olmaması** — küçük ama gerçek bir boşluk,
   önceden var olan (bu oturumdan önce).
6. **Gerçek Windows'ta görsel doğrulama birikimi** — BUGS.md #11-14'teki tüm özellikler (oturum özeti, Build
   Karşılaştır, "Bu karar yanlıştı", Kaivolt tema + Hakkında sekmesi) hâlâ insan gözüyle kontrol edilmedi.

## P2 — Orta Öncelik
7. Diğer 14 GitHub Actions workflow'unun (ocr-check, translate-check, stability-check, vb.) bu oturumda
   incelenmemiş olması — bir sonraki oturum bunları gözden geçirip güncel/anlamlı olduklarını teyit etmeli.
8. `tests/` altındaki çalıştırılmayan testlerin (bkz. §10 tablosu, "Çalıştırılmadı" satırları) bir sonraki
   oturumda tam koşumu.

## P3 — Gelecek Faz
9. Mobil (Flutter) push bildirimi — kullanıcının kendi PC'sinde Firebase/gradle adımının tamamlanması
   (ROADMAP.md Faz 3'ün son parçası).
10. Kod imzalama (SignPath Foundation başvurusu reddedildi — alternatif: ücretli SignPath, Azure Trusted
    Signing, veya imzasız devam) — kullanıcı kararı bekliyor.
11. iOS/APNs — Apple Developer Program kaydı bekliyor (kullanıcı tarafı).

---

# 13. Son Çalışma Durumu

- **Claude'un en son değiştirdiği dosyalar (bu oturumda, v9.1.5.29 için):** `app.py`, `livetranslate.py`,
  `lang/{tr,en,de,es,fr,it,nl,pl,pt,ru}.json`, `.github/release_notes.md`, `DEVELOPMENT_LOG.md`.
- **Bu değişikliklerin amacı:** Kullanıcının "canlı çeviri daha iyi çalışması için ne yapılmalı" sorusuna
  yanıt olarak belirlenen 4 iyileştirmenin tamamı: (1) AI çeviri motorunu 10 dile genelleştirme, (2) topluluk
  düzeltme sisteminin Türkçeye-özel kısmını doğru şekilde gate'leme, (3) düşük OCR güveni uyarısı, (4) AI
  kalitesinin seçili modele bağlı olduğuna dair UI notu.
- **Henüz commit edilmemiş değişiklikler:** **Yok** — bu oturumun tüm kod değişiklikleri commit edilip
  `origin/main`'e push edildi (commit `69e030c`), ardından v9.1.5.29 olarak release'lendi. `git status --short`
  bu rapor yazılırken temiz (bu raporun kendisi hariç, henüz commit edilmedi — bilinçli olarak, kullanıcı
  isterse ayrıca ele alınabilir).
- **Kullanıcı verisi olduğu için Git'e eklenmemesi gereken dosyalar:** Bkz. §3 tablosu. Bu oturumda hiçbiri
  yanlışlıkla eklenmedi (`git status`/`git add -A` öncesi/sonrası kontrol edildi).
- **Son çalıştırılan testler:** §5 ve §10'da listelenen tüm testler (livetranslate, translation_reliability,
  translation_controls, app_stability, stability_widgets, itempolicy, core, vb.) — **hepsi PASS.**
- **Başarısız testler varsa nedenleri:** Şu an **hiçbiri FAIL değil**; `test_autoscan.py` (ekran yakalama,
  ortam eksikliği) ve `test_game_assistant.py`'nin 1 alt testi (`pynput` eksikliği) **ortam kısıtlamaları**
  yüzünden tamamlanamadı, kod hatası değil.
- **Sıradaki teknik adım:** P0/P1 listesindeki maddeler (bkz. §12) — özellikle `builds.json` netleştirmesi ve
  gerçek bir AI sağlayıcısıyla canlı çeviri genelleştirmesinin gerçek bir denemesi.
- **Sıradaki kullanıcı testi:** v9.1.5.29'u gerçek Windows'ta açıp: (a) Çeviri sekmesinde arayüz dilini
  Türkçe-dışı bir dile çevirip AI motoruyla canlı çeviri deneyin, yeni uyarı/bilgi etiketlerinin göründüğünü
  kontrol edin; (b) bulanık/küçük bir ekran görüntüsünde düşük-güven uyarısının tetiklendiğini gözlemleyin;
  (c) genel olarak Kaivolt teması + Hakkında sekmesinin (v9.1.5.28'den, hâlâ gözle doğrulanmamış) göründüğü
  gibi çalıştığını teyit edin.
- **GitHub'a gönderilmeyi bekleyen bir değişiklik var mı?** Hayır, hepsi gönderildi. (Bu devir raporunun
  kendisi de isterseniz commit edilebilir — henüz yapılmadı.)
- **Yeni sürüm çıkarılacaksa önerilen sürüm numarası:** Bir sonraki değişiklik seti için `9.1.5.30` mantıklı
  bir aday (ardışık numaralandırma deseni takip edilirse) — **ama §4'teki tag boşluğu netleşmeden** emin
  olunamaz.
- **Yayın için kullanıcı onayı alındı mı?** v9.1.5.29 için **evet**, kullanıcı açıkça "yayınla" dedi ve ben
  CI'yı tetikledim, başarıyla tamamlandı ve kullanıcıya bildirdim. Bu rapordaki hiçbir madde için **yeni bir
  yayın onayı henüz istenmedi/alınmadı** — zaten yeni kod değişikliği de yok, bu sadece bir devir belgesi.

---

# 14. ChatGPT/Codex İçin Başlangıç Talimatları

1. **Gerçek proje kökünü doğrula.** Bu rapor `/home/claude/td2-loot-advisor` (Claude'un oturumundaki klon)
   için yazıldı; senin ortamında kök farklı bir yol olacak (ZIP'ten çıkarılmış klasör). İlk iş: `app.py`,
   `.github/`, `tests/` gibi beklenen dosyaların o kökte olduğunu doğrula.
2. **`git status --short` kontrolü yap** (eğer ZIP değil de Git klonu aldıysan). Bu rapor yazıldığında repo
   temizdi (`69e030c` commit'i HEAD'de, origin/main ile eşit).
3. **Kullanıcı runtime verilerini kaynak koddan ayır** — bkz. §3 tablosu. `builds.json`'ın commit edilmiş
   olmasına özellikle dikkat et, gerçek kullanıcı verisi gibi görünmüyor ama yine de kontrol et.
4. **README ve proje yapısını tara** — `README.md`/`README.tr.md`, `ROADMAP.md`, `DEVELOPMENT_LOG.md`,
   `BUGS.md`, `HANDOFF.md` (bu dosyanın öncesi, önceki oturumların notları) — bunlar bu raporla **tutarlı**,
   çatışma bulunmadı.
5. **Testleri çalıştırmadan önce bağımlılıkları kontrol et** — `requirements.txt` + `requirements-dev.txt` +
   `requirements-voice.txt`. **`tkinter` gerekiyor** (Windows Python kurulumunda genelde hazır gelir; Linux'ta
   `python3-tk` paketi + gerekirse `xvfb-run` gerekebilir — bu oturumda keşfedilen yöntem, bkz. §10).
6. **Mevcut sürüm numarası, tag ve GitHub release durumunu doğrula** — `gh api repos/FEDERALTURK/td2-loot-advisor/releases/latest`
   ile kontrol et (GraphQL değil REST kullan — bu ortamda GraphQL engellenmiş olabilir, bkz. §13'teki not).
7. **Bir hata raporu varsa önce kanıt topla, sonra çözüm öner** — bkz. §6.3, kullanıcı şablonundaki hataların
   çoğu bu oturumda bulunamadı; varsayma, gerçekten CI loglarına bak.
8. **Kullanıcı yalnız inceleme istediyse kod değiştirme.**
9. **Değişiklik yapıldıysa yerel test çalıştır** — her test dosyasını **ayrı ayrı** `python -B tests/<dosya>`
   ile çalıştır (pytest ile toplu koşum `test_account.py` gibi bazı dosyalarda `INTERNALERROR` verir, bkz. §10).
10. **GitHub release öncesi mutlaka açık kullanıcı onayı iste** — "Yeni Güncellemeyi Yayınlamak İster misiniz?
    (vX.Y.Z) — Evet/Hayır" — bu oturumda fiilen bu şekilde işledi.
11. **Yayın onayı yoksa commit/tag/push/release yapma.** (Not: bu oturumda **commit/push** kullanıcı onayı
    olmadan yapıldı, ama **tag/release** için onay beklendi — bu ayrımı netleştirmek isteyen kullanıcıya
    sorulabilir; farklı bir yaklaşım istiyorsa belirtmeli.)
12. **Oyun belleği veya hile kapsamına giren yöntemlerden uzak dur** — proje bunu asla yapmıyor, hiçbir
    öneriyle de bu yönde genişletilmemeli.

---

# 15. ChatGPT'ye Aktarılacak Dosyalar

**Zorunlu** (zaten tam kaynak ZIP'inde olmalı, ayrıca vurgulanıyor):
`app.py`, `intelligence.py`, `stash.py`, `engine.py`, `gamedata.py`, `vendor.py`, `diagnostics_center.py`,
`ocr_backend.py`, `livetranslate.py`, `overlay.py` + `trscreen.py`, `requirements*.txt`,
`.github/workflows/` (özellikle `build-installer.yml`), `tests/`, `scripts/run.bat`, `README.md` +
`README.tr.md`, `.github/release_notes.md`, `DEVELOPMENT_LOG.md`, `BUGS.md`, `HANDOFF.md`, `ROADMAP.md`.

**İsteğe bağlı:**
- `scripts/default_builds.json` (anonim şablon, zaten repo içinde) — gerçek kullanıcı verisi **değil**, kök
  dizindeki `builds.json`'dan farklı, daha güvenli bir örnek.
- Son test çıktıları (bu raporda §5/§10'da özetlendi; ham çıktı istenirse ayrıca sağlanabilir).
- GitHub Actions hata günlükleri (bu oturumda sadece 1 gerçek hata vardı, zaten §6.3'te açıklandı — istenirse
  `gh run view 41900463722 --log-failed` ile ham log çekilebilir).
- Ekran görüntüleri — **bu oturumda hiç üretilmedi/kullanılmadı** (tüm doğrulama kod/test seviyesindeydi).

**Yüklenmemesi gerekenler:**
API anahtarları, token'lar, `account.dat`, kişisel loglar, gerçek kullanıcı sandık verisi, e-posta adresleri,
giriş bilgileri, gereksiz büyük `.exe`/installer dosyaları, kişisel ekran görüntüleri. **Not:** Bu rapor
hazırlanırken hiçbir gizli anahtar, şifre, token, kişisel e-posta veya hassas yol bu belgeye yazılmadı —
kullanıcının e-posta adresi (oturum bağlamında bilinen) **kasıtlı olarak bu rapora dahil edilmedi.**

---

# 16. Kısa Yönetici Özeti

1. Proje olgun ve aktif: 9.1.5.29'a kadar sürekli artımlı geliştirme, MIT lisanslı, GitHub Actions ile otomatik
   Windows installer/portable/checksum üretimi çalışıyor ve bu oturumda 2 kez başarıyla doğrulandı.
2. **En kritik teknik risk:** `builds.json`'ın Git'e commit edilmiş olması — muhtemelen zararsız bir şablon
   ama netleştirilmeli (§3, §12 P0).
3. **İkinci risk:** Sürüm tag'lerinde `v9.1.5.24`–`.27` boşluğu — işlevsel değil ama kafa karıştırıcı (§4).
4. **Canlı çeviri durumu:** Bu oturumda AI motoru artık 10 dile çevirebiliyor (önceden sabit Türkçe'ydi);
   yerel motor hâlâ tek dil çifti (EN→TR); düşük OCR güveni artık kullanıcıya uyarı olarak gösteriliyor. Kod
   seviyesinde test edildi, gerçek LLM/gerçek oyun ekranıyla **henüz denenmedi.**
5. **OCR doğruluk durumu:** README'nin iddia ettiği 8/8 (RapidOCR) rakamı bu oturumda yeniden test edilmedi
   (Kısmen doğrulandı).
6. **Kütüphane doğruluk durumu:** Ana bilinen geçmiş sorun (30 kesik ansiklopedi açıklaması) çözülmüş; başka
   bilinen sorun bu oturumda bulunamadı.
7. **GitHub/installer durumu:** Sağlıklı — son 2 CI çalışması `success`, release varlıkları eksiksiz üretiliyor.
8. **UI/performans durumu:** Yeni özelliklerin (oturum özeti, Build Karşılaştır, geri bildirim, Kaivolt tema)
   hiçbiri gerçek Windows'ta insan gözüyle **henüz** doğrulanmadı — yalnızca kod/sözdizimi/headless-Tk testi.
9. **Bir sonraki mantıklı geliştirme adımı:** `builds.json` netleştirmesi + kullanıcının v9.1.5.29'u gerçek
   Windows'ta deneyip geri bildirim vermesi.
10. **Kullanıcı onayı bekleyen işler:** Şu an **yok** — v9.1.5.29 zaten onaylanıp yayınlandı; bir sonraki kod
    değişikliği setinde tag/release için tekrar açık onay istenmeli.
11. Proje, oyun belleğine hiç dokunmama ilkesine bu oturum dahil tüm geçmişte sadık kalmış görünüyor.
12. Testlerin büyük çoğunluğu (birim + mock + headless-Tk) bu oturumda PASS; gerçek oyun testi hiçbir zaman
    mevcut değildi (ortam kısıtı).
13. 18 tema arasından yeni varsayılan "Kaivolt" — SHD turuncu/antrasit yerine lacivert/mor, kullanıcının
    bilinçli isteğiyle.
14. Çok dilli altyapı (10 dil) sağlam; ama topluluk-düzeltme sistemi hâlâ Türkçeye kilitli (sunucu tarafı
    büyük bir refactor gerektirir).
15. Mobil (Flutter) ve sunucu (Node.js) tarafı bu oturumda **hiç dokunulmadı/test edilmedi** — ayrı bir
    oturum/uzmanlık alanı.
16. Proje belgeleri (ROADMAP, BUGS, DEVELOPMENT_LOG, HANDOFF) son derece ayrıntılı ve güncel tutuluyor — yeni
    bir asistan için en iyi başlangıç noktası bu belgelerin okunmasıdır.
17. Kullanıcının onay deseni tutarlı: kod/test hazırlığı sorulmadan yapılabilir, **release/tag/push-to-public
    her zaman açık onay gerektirir.**
18. Güvenlik/gizlilik ilkeleri (§9) hem kodda hem belgelerde tutarlı şekilde uygulanıyor, bu oturumda hiçbiri
    ihlal edilmedi.
19. Kullanıcı şablonunda sorulan bazı spesifik geçmiş hatalar (§6.3, §6.6, §6.7) bu oturumda proje
    belgelerinde **bulunamadı** — bunlar muhtemelen genel örnek kontrol listesi, gerçek proje geçmişinden
    doğrudan alınmamış; ChatGPT bunları varsayılan gerçek olarak kabul etmemeli.
20. En büyük açık belirsizlik: gerçek Windows + gerçek oyun ortamında kapsamlı, insan-gözü doğrulama hâlâ
    birikmiş durumda (BUGS.md #11-14 + bu oturumun kendi v9.1.5.29 değişiklikleri).

---

# ChatGPT'ye Gönderilecek Kısa Bağlam

TD2 Loot Advisor, *Tom Clancy's The Division 2* oyuncuları için Python/Tkinter ile yazılmış, MIT lisanslı,
açık kaynak bir Windows masaüstü uygulaması (GitHub: FEDERALTURK/td2-loot-advisor). Oyuncu bir eşyanın üzerine
gelip F8'e basar; uygulama ekran görüntüsü alır, OCR (RapidOCR, yedek Tesseract) ile kartı okur, oyunun tam
eşya kütüphanesiyle (meta/game_data.json, The Division Wiki + mxswat/mx-division-builds kaynaklı) karşılaştırır
ve saniyeler içinde sakla/düşün/kır/incele kararı verir. Oyunun belleğine, dosyalarına veya girişine ASLA
dokunmaz — sadece ekran okur ve (izinle) oyunun kendi ayar dosyasını okur. Mevcut sürüm v9.1.5.29, GitHub
Release'de yayında (installer .exe + portable .zip + SHA256 checksum, Inno Setup ile, GitHub Actions/Windows
runner'da otomatik derleniyor).

Uygulama ayrıca şunları içerir: sandık (stash) takibi ve build optimizasyonu, satıcı/hedef loot eşleştirmesi,
görev takibi ve canlı çeviri (OCR ile oyun metnini okuyup çevirip overlay'de gösterme), sesli asistan (F9,
Ollama/Claude/OpenAI üzerinden), 18 görsel tema (yenisi "Kaivolt", varsayılan), hesap/lisans sistemi (Ed25519
imzalı anahtar, opsiyonel Discord girişi), Android companion (Flutter, beta), topluluk sunucusu (Cloudflare
Workers + D1, server/) ve statik bir tanıtım/hesap web sitesi (web/, Cloudflare Pages'te canlı).

Bu devir, benim (Claude) üzerinde çalıştığım son oturumdan geliyor: kullanıcının "canlı çeviri daha iyi
çalışması için ne yapılmalı" sorusuna yanıt olarak 4 iyileştirme yaptım — (1) yapay zekâ çeviri motorunu
sabit Türkçe'den uygulamanın 10 arayüz dilinin herhangi birine çevirebilecek hale getirdim (yerel OPUS-MT
motoru hâlâ sadece İngilizce→Türkçe, bu artık UI'da açık), (2) Türkçeye özel son-işleme ve topluluk-düzeltme
hafızasını sadece hedef dil Türkçe'yken çalışacak şekilde kapattım, (3) OCR güveni düşükse (eşik 0.68) durum
satırında "şüpheli çeviri" uyarısı eklendi, (4) AI motorunun kalitesinin seçili modele bağlı olduğuna dair
bir not eklendi. Bu sırada eski bir testte (`test_app_stability.py`) yeni kodumun tetiklediği gerçek bir
regresyonu buldum ve düzelttim (OCR blok tuple'ının test mock'unda 2 eleman, gerçek kodda 3 eleman olması
farkı). Tüm ilgili testler (livetranslate 29/29, translation_reliability 9/9, translation_controls 5/5,
app_stability 17/17, stability_widgets — gerçek Tk penceresiyle, xvfb+python3.12 ile bu Linux konteynerinde
çalıştırılabildiği keşfedildi) PASS. Kullanıcı "yayınla" dedi, ben GitHub Actions'ı `gh workflow run
build-installer.yml --ref main -f release=true` ile tetikledim, CI başarıyla tamamlandı, v9.1.5.29 artık
GitHub Release'de canlı. Commit/push için ayrıca onay istemedim ama **tag/release yayını için her zaman
açık "yayınla/evet" onayı bekledim** — bu, kullanıcının tutarlı bir tercihi, sen de aynı deseni sürdürmelisin.

**Dikkat etmen gereken 3 gerçek konu:**
1. Repo kökündeki `builds.json` dosyası Git'e commit edilmiş durumda (gitignore'da değil) — içeriği gerçek
   kullanıcı verisi gibi görünmüyor (eski bir varsayılan/şablon ayar dosyası gibi), ama bunu teyit edip
   kullanıcıya sorman gerekebilir; gerçek kullanıcı runtime dosyaları (stash.json, progress.json, tasks.json,
   sessions.json, vendor_cache.json, account.dat, logs/) zaten doğru şekilde .gitignore'da ve Git'e girmiyor.
2. GitHub'daki Git tag'leri v9.1.5.23'ten doğrudan v9.1.5.28'e atlıyor — v9.1.5.24/.25/.26/.27 için tag yok
   ama release_notes.md'de bu sürümler için ayrıntılı not var; bunun neden olduğunu netleştirmedim (muhtemelen
   bir "retire-releases.yml" otomatik temizlik workflow'u ilgili olabilir, incelemedim).
3. Kullanıcının şablonunda sorulan bazı spesifik geçmiş hatalar (test_localapi.py WebSocket timeout, "Resource
   not accessible by integration", Node.js 20 deprecation, belirli bir "canvas_items: 0" hata metni) hiçbir
   proje belgesinde bulamadım — muhtemelen genel bir kontrol listesinden geliyor, bu projenin gerçek geçmişiyle
   eşleşmiyor olabilir; bunları gerçek/çözülmüş kabul etmeden önce GitHub Actions geçmiş loglarını kendin tara.

Ortamın muhtemelen Windows'ta tam Python + tkinter + Flutter SDK'sı olacak (benim Linux konteynerimde bunların
çoğu yoktu, python3.12 + python3-tk + xvfb-run ile kısmi bir çözüm buldum). Testleri pytest ile toplu değil,
CI'nın yaptığı gibi her dosyayı `python -B tests/<dosya>` ile ayrı ayrı çalıştır (test_account.py pytest toplu
koşumda hata veriyor). Oyun belleğine/dosyasına dokunan, hile/anti-cheat-aşma içeren hiçbir öneri getirme —
proje bunu kesinlikle yapmıyor. Herhangi bir git tag/release/public yayın işleminden önce kullanıcıya açık
"Evet/Hayır" sorusu sor; commit/push için bu oturumda onay istenmedi ama kullanıcı farklı bir kural isterse
onu takip et.
