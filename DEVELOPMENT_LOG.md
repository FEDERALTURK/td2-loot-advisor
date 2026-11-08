# Geliştirme Günlüğü

Önemli kararların ve sürümlerin kısa, kronolojik özeti. Tam ayrıntı için `git log` ve `.github/release_notes.md`.

## Konsol Modu — gamecaptionapp tarzı kamera modu, Faz 1 MVP kodu (mobil, 2026-11-08)

- Kullanıcı isteği: "Xbox Series X/S'de çalışan ve gamecaptionapp gibi çalışan bir uygulama
  geliştirelim" → netleştirme sorusunda kullanıcı "gamecaptionapp'ın aynısı, aynı mantıkla" dedi. Bu,
  yol haritasındaki (`docs/console_game_caption_roadmap.md`) Faz 1'e (mobil kamera modu — platform
  bağımsız, Xbox/PS/PC hepsinde aynı anda çalışır) karşılık geliyor; Faz 3a (doğrudan Xbox protokolü,
  XStreaming) DEĞİL — gamecaptionapp'ın kendisi de birincil modunda ("herhangi bir konsol/bilgisayar/
  film/dizide çalışır") bu mantığı kullanıyor.
- **Yeni dosyalar**: `mobile/lib/console/console_caption_page.dart` (kamera önizleme + yeşil hizalama
  kutusu + Xbox-stili alt altyazı kutusu + TTS aç/kapa + başlat/durdur düğmesi),
  `mobile/lib/console/console_translate_service.dart` (OCR + çeviri servisi, cihaz-üstü).
- **Yeni bağımlılıklar** (`mobile/pubspec.yaml`): `camera ^0.12.2`, `google_mlkit_text_recognition
  ^1.0.1`, `google_mlkit_translation ^1.0.1`, `flutter_tts ^4.2.5`. Gerçek versiyon numaraları
  pub.dev'den sorgulanarak alındı (tahmin edilmedi); her paketin kullanılan API'si (metod imzaları,
  enum alanları) `flutter-ml/google_ml_kit_flutter` deposu klonlanıp kaynağından tek tek doğrulandı.
- **Mimari**: tamamı cihaz-üstü (AGENTS.md madde 3 ile uyumlu — ekran/OCR verisi hiçbir sunucuya
  gitmiyor). ASR yok, yalnız ekrandaki yazı okunuyor (gamecaptionapp'ın kendi tanımladığı basitleştirme,
  bkz. yol haritası §1.5). `main.dart`'a "Konsol" adında 5. bir alt sekme eklendi.
  `android/app/src/main/AndroidManifest.xml`'e `CAMERA` izni + isteğe bağlı kamera donanım özellikleri,
  `ios/Runner/Info.plist`'teki `NSCameraUsageDescription` iki kullanım amacını (QR eşleştirme + Konsol
  Modu) kapsayacak şekilde güncellendi.
- **Doğrulama durumu — ÖNEMLİ, dürüstçe belirtilmeli**: Bu konteynerde Flutter SDK YOK — `flutter pub
  get`, `flutter analyze`, `flutter test`, gerçek derleme hiçbiri çalıştırılamadı. Yazılan kod, ilgili
  paketlerin gerçek kaynak kodu klonlanıp API imzaları tek tek karşılaştırılarak "doğru çağrılıyor" (statik)
  seviyesinde doğrulandı — ama **sıfır gerçek cihaz testi** (kamera izni akışı, OCR doğruluğu, çeviri
  modeli indirme, pil/performans). Ayrıntı ve bilinçli MVP basitleştirmeleri (periyodik `takePicture()`
  vs canlı kare akışı, hizalama kutusunun OCR'ı kırpmaması) için `docs/console_game_caption_roadmap.md`
  Faz 1 bölümüne bakın.
- **Bekleyen**: Henüz commit/push edilmedi. Commit/push kod+doküman işi olduğu için (AGENTS.md madde 6)
  ayrı onay gerektirmiyor, ama CI'nin `flutter analyze`/`flutter test` adımlarının gerçekten geçip
  geçmediği push sonrası izlenmeli — bu paketler eklendiğinde bilinmeyen bir derleme hatası çıkma
  ihtimali gerçek ve göz ardı edilmemeli.

## Mobil companion v0.1.9 — imza sürekliliği P0 düzeltmesiyle ilk yayın (0.1.9, 2026-11-08)

- Kullanıcı isteği: Codex'in PC kopyasında yaptığı çalışmanın devir raporu (`CODEX_DEVIR_RAPORU.md`)
  incelendi; raporun P0 olarak işaretlediği "GitHub Actions her çalışmada farklı bir geçici debug anahtarıyla
  imzalıyor, bu yüzden kullanıcılar eski APK üstüne güncelleyemiyor" sorunu doğrulanıp giderildi, ardından
  kullanıcı bu düzeltmeyle birlikte yeni bir companion sürümü hazırlanmasını istedi ("evet").
- **İmza sürekliliği P0 düzeltmesi** (ayrıntı: `docs/mobile_beta_signing_tr.md`, `BUGS.md` #19):
  `mobile/android/app/build.gradle.kts`'e Play yükleme anahtarından tamamen ayrı, kalıcı bir
  `githubBetaRelease` imzalama yapılandırması eklendi (`beta-key.properties`, `.gitignore`'da);
  `.github/workflows/build-mobile.yml`'e bu anahtarı `TD2_BETA_KEYSTORE_BASE64`/`_PASSWORD`/`_ALIAS`
  secret'larından çözen bir adım eklendi. Gerçek bir `workflow_dispatch` CI çalışmasıyla (run 42502909839)
  doğrulandı: üretilen APK'nin v2 imza sertifikası (androguard), oluşturulan keystore'un kendi
  fingerprint'iyle (SHA256 `B1:FD:...:BA`) birebir eşleşti — **P0 doğrulandı ve giderildi.**
- **P2 düzeltmesi (yan ürün)**: `lib/main.dart` ve `lib/services/cloud_api.dart`'taki sabit kodlanmış
  eski `'TD2-Loot-Advisor-Companion/0.1.5'` User-Agent dizeleri, zaten var olan tek doğruluk kaynağı
  `lib/services/companion_release.dart`'taki `companionVersion` sabitine yönlendirildi (`cloud_api.dart`'a
  yeni `import 'companion_release.dart';` eklendi). Artık sürüm numarası yalnızca tek bir yerde değişiyor.
- **Sürüm artışı**: `mobile/pubspec.yaml` `0.1.8+10` → `0.1.9+11`; `companionVersion` `'0.1.8'` →
  `'0.1.9'`. `grep -rn "0\.1\.8" mobile/lib mobile/test` boş döndü (kalan eski referans yok).
- **Doğrulama**: Dart/Flutter derleyicisi bu konteynerde yok — değişiklikler statik olarak (import zinciri,
  sabit kullanım yerleri) doğrulandı; gerçek derleme doğrulaması `build-mobile.yml` CI'sinin
  `flutter build apk --release` adımında (tag push ile tetiklenince) gerçekleşecek.
- **Önemli göç notu**: Bu, P0 düzeltmesinden sonraki İLK yayın. Telefonlarda zaten kurulu olan eski beta
  APK'nin üzerine bu sürüm imza uyuşmazlığından dolayı kurulamayabilir — kullanıcıların bir kez elle
  kaldır/yeniden kur yapması gerekir; bundan sonraki sürümler normal şekilde zincirlenecek.
- **Yayınlandı (2026-11-08)**: AGENTS.md'nin zorunlu yayın onayı sorusu kullanıcıya soruldu, açık
  "Evet" alındı. Bu ortamın proxy'si hem `git push` ile tag push'u hem de GitHub API üzerinden tag
  oluşturmayı kalıcı olarak engellediği için (`403: Write access ... not permitted through this proxy`,
  tekrar denemekle çözülmedi), kullanıcı tag'i kendi GitHub web arayüzünden (Releases → New release →
  tag `companion-v0.1.9`, target `main`) oluşturup "Publish release"e tıkladı. Bu, CI'yi tag-push
  yoluyla tetikledi (run 42511119543): build + imzalama + **gerçek "Publish companion release" adımı
  bu kez çalışıp** `TD2LootAdvisor_Companion_0.1.9.apk` + `SHA256SUMS.sha256`'yı
  `https://github.com/FEDERALTURK/td2-loot-advisor/releases/tag/companion-v0.1.9` adresine ekledi
  (companion kanalı kasıtlı olarak her zaman `prerelease: true` işaretli — bkz.
  `build-mobile.yml`'deki `Publish companion release` adımı). Yayınlanan APK GitHub'dan indirilip
  androguard ile v2 imza sertifikası tekrar çıkarıldı — fingerprint yine
  `B1:FD:...:BA` ile birebir eşleşti. **P0 düzeltmesi artık gerçek bir public yayında da kanıtlandı**
  (ayrıntı: `docs/mobile_beta_signing_tr.md`).

## Üst yatay menü, dijital yağmur efekti, 3B radar + rastgele tespit noktaları (9.1.5.31, 2026-11-05)

- Kullanıcı isteği: "Arkada bulunan haritanın dah 3 boyutlu ve gerçek olmasını saatin dönmesiyle tespit
  edilen düşman noktalarının belirgin olmasını ve parlamasını istiyorum. Bu rasgele gelişecek sürekli aynı
  noktada düşman tespiti yapılıyor efekti olmasın. Menülerin üst kısmında ise yeşil kodların aşağıya doğru
  indiği animasyon efekti istiyorum menü yerleri değiştir..." Netleştirme soruları üzerine kullanıcının
  verdiği yanıtlar: (1) **"3B harita"** → gelişmiş prosedürel 3D radar (gerçek oyun haritası görüntüsü değil
  — proje zaten ekran-OCR dışında oyuna hiç dokunmuyor); (2) **"düşman tespiti"** → tamamen dekoratif/
  rastgele bir HUD efekti (gerçek oyun belleğinden okunan bir konum olamaz, `HANDOFF.md`'deki "oyunun
  process/belleğine asla dokunulmaz" kuralı korunur); (3) **üst menü** → sol kenar çubuğu tamamen kaldırılıp
  tüm navigasyon tek, yatay üst şeride taşınacak (önceki görevde eklenen, kullanılmayan
  `_build_field_command_shell()` kabuğundaki yatay-nav deseni referans alındı).
- **`td2app/ui/ui_hud.py`** (`DashboardScene` — Panel/dash sekmesinde her zaman görünen asıl arka-plan
  radarı; Windows-özel, varsayılan kapalı `fx.AgentWatch` değil): tüm halkalara/işaretlere `ry=0.50`
  dikey-sıkıştırma uygulanarak 3B/izometrik perspektif hissi eklendi (4 eşmerkezli elips halka, ekstra
  derinlik katmanı, 12 ışın/tarama çizgisi/merkez nabız hepsi aynı oranla yeniden hesaplandı). Yeni
  `_draw_blips()` metodu: her "tespit" noktası kendi rastgele açısı/yarıçapı/ömrüyle (`random.uniform`)
  doğup kısa süre parlayıp sönüyor; aynı anda en fazla 3 nokta, yeni doğuşlar arası rastgele bekleme
  (1.3–3.4 sn) — sabit/tekrarlayan bir "hep aynı yerde tarama" örüntüsü kasıtlı olarak önlendi.
- **`td2app/ui/fx.py`**: yeni `DigitalRain(tk.Canvas)` sınıfı (Matrix esintili, yalnızca ASCII-güvenli
  glif seti — Windows'ta CJK font eksikliği riskini önlemek için Katakana kullanılmadı). Persistent
  canvas-item havuzu deseni (proje genelinde `fx._ItemPool`/`ui_hud.DashboardScene` ile aynı felsefe —
  her karede item silip yeniden yaratmak yerine `itemconfigure`/`coords` ile güncelleniyor), `_animation_budget()`
  ile diğer dekoratif efektlerle tutarlı duraklatma/ölçekleme.
- **`app.py`**: `build_ui()`'daki dikey kenar çubuğu bloğu tamamen kaldırıldı; yerine `fx.DigitalRain`
  üzerine `canvas.create_window(...)` ile gerçek `ttk.Button` nav düğmeleri (Panel/Gear/Intel/Tools/
  Settings/More) gömülü yatay bir üst şerit geldi — düğmeler arası boş alanlarda arka plandaki kod
  animasyonu görünür kalıyor. Yeni `_layout_topnav_buttons()` metodu düğmeleri soldan sağa diziyor,
  sürüm metnini sağa yaslıyor ve **arkadan geçen yağmur glifleriyle görsel çakışmayı önlemek için** sürüm
  etiketinin arkasına opak dolgu dikdörtgeni (`canvas["bg"]` renginde, `tag_lower` ile metnin altında)
  ekliyor. `_sync_responsive_layout()`'taki artık geçersiz `button.pack_configure(...)` çağrısı (düğmeler
  artık `pack` değil `create_window` ile yönetiliyor — çalışsaydı `TclError` fırlatırdı) kaldırılıp
  `_layout_topnav_buttons()` çağrısıyla değiştirildi. `_sidebar_activate()` artık `hasattr(self, "sidebar")`
  ile hangi buton stilini (`FieldNav.TButton` vs `Nav.TButton`) kullanacağına karar veriyor. Eski
  `_build_field_command_shell()`/`_build_shd_terminal_shell()` kabukları (zaten `_cfg_defaults()` tarafından
  `ui_layout="standard"`a zorlandığı için erişilemez durumda) kapsam dışı bırakılıp dokunulmadan bırakıldı.
- **Doğrulama**: `ast.parse` ile tüm dosyalar temiz geçti. `xvfb-run -a python3.12 tests/test_stability_widgets.py`
  gerçek Tk widget'larıyla `callback_errors: []`, `ok: true` ile geçti. Ekran görüntüsü alınıp (Xvfb +
  ImageMagick `import`) yakınlaştırılarak doğrulandı: sürüm etiketi artık yağmur glifleriyle çakışmıyor,
  üst nav şeridi düğün/boşluk görünümü doğru, radar halkaları elips/3B perspektifte görünüyor. `test_core`,
  `test_app_stability`, `test_hardening`, `test_regression_crash_patterns`, `test_release_914`,
  `test_intelligence`, `test_translation_controls`, `test_project_structure` hepsi `xvfb-run` altında OK.
- **Bilerek dışarıda bırakılan**: dekoratif tespit noktaları yalnızca birkaç saniyede bir rastgele
  doğduğu için tek bir ekran görüntüsünde her zaman görünmeyebilir — bu beklenen davranış, tekrarlayan
  sabit-konum taraması hissini önlemek amacıyla kasıtlı.

## Tüm temalar silindi, baştan tek yeni tema/şema (9.1.5.30, 2026-11-05)

- Kullanıcı isteği: "Uygulamadaki tüm temaların sil ve baştan sıfırdan uygulama teması ve şemasını değiştir."
  Netleştirme soruları üzerine kullanıcının verdiği yanıtlar: (1) **tek tema, hiç seçim yok** — eski 17 tema
  (3 taban: dark/light/classic + 14 oyun-atmosferi paketi: darkzone, blacktusk, hunter, winter_ny, nightops,
  kenly, isac, tactical, rogue_signal, isac_operations, darkzone_rogue, field_terminal, shd_terminal, kaivolt)
  tamamen kaldırıldı; (2) **bambaşka, yeni bir görsel yön** — ne eski SHD turuncusu ne Kaivolt'un moru; (3)
  **geriye dönük uyumluluk otomatik ve sessiz** — eski kayıtlı tema adı/düzen bilgisiyle açılan kullanıcılar
  hatasız biçimde yeni temaya geçer. Ayrıca kullanıcı, menülerin/yazı tipinin/gölgeleme-derinlik hissinin
  Division 2'nin kendi arayüzüyle "nitelik ve nicelik olarak benzer" olmasını istedi.
- **`td2app/ui/ui_theme.py`**: `PALETTES`/`_PACKS`/`PACKS`/`THEME_MODES` tek bir `"default"` girdisine
  indirildi (koyu grafit zemin `#0a0d12`/`#121720`/`#1a212c`, camgöbeği-teal vurgu `#36e0c4`/hover `#6aedd9`,
  karar/işlev renkleri — KEEP/CONSIDER/DISMANTLE/REVIEW/success/danger/warning/info — okunabilirlik kanıtlı
  eski "dark" paletinden korundu). `apply_pack()` artık paket-özel dallanma içermiyor: tek koşulsuz davranış
  olarak `ui_nav_layout="tactical"` + `fx_transition_style="tactical"` + `ui_layout="standard"` uygular — bu,
  Division 2'nin kademeli/çaprazlı (HUD) kenar çubuğu ve geçiş temposunu zaten uygulayan mevcut altyapıyı
  (`fx.CommandRibbon`, `fx.NavMotif`, `fx.Transition`, kademeli kenar-çubuğu girintisi) yeniden kullanır —
  sıfırdan "gölgelik/HUD" kodu yazmaya gerek kalmadı. `apply()`'deki "classic" özel dalı (ham `clam` teması)
  kaldırıldı. Bağımsız bir özellik olan `event_fx`/`fx_watch_style` (ajan-saat dekoratif animasyon modu:
  standard/isac/rogue/field) kasıtlı olarak dokunulmadan bırakıldı — renk teması değil, ayrı bir dekoratif
  seçici; yeni temada sade biçimde `event_fx="standard"`'a düşüyor.
- **`app.py`**: iki sabit-kodlanmış `ui_theme.PALETTES["dark"]` referansı (`PAL` ilk ataması, build-share
  kartındaki verdict rengi) `"default"`e güncellendi. `DEFAULTS["ui_theme"]` `"kaivolt"` → `"default"`,
  `DEFAULTS["ui_nav_layout"]`/`["fx_transition_style"]` `"flat"`/`"soft"` → `"tactical"`/`"tactical"`.
  Ayarlar → Görünüm kutusundaki tema galerisi/açılır listesi (17 kart + combobox) tamamen kaldırıldı; artık
  yalnızca tema-dışı görünüm ayarları (sesler, arka plan aralığı, özel sanat klasörü, 3B derinlik) kalıyor.
  Artık çağrılmayan `apply_theme_pack()` yardımcı metodu ve ayarları-kaydet akışındaki eski tema-adı
  eşleştirme kodu silindi.
  - **Geriye dönük uyumluluk / göç**: `_cfg_defaults()`'a eklendi — `ui_theme` artık `THEME_MODES` içinde
    değilse (örn. eski `"kaivolt"`, `"isac"`, `"shd_terminal"`) sessizce `DEFAULTS["ui_theme"]`'e döner;
    ayrıca `ui_layout` `"standard"` değilse (silinen `field_terminal`/`shd_terminal` paketlerinin yan etkisi
    olarak ayarlanmış, artık palet anahtarları eksik kalacak `field_command`/`shd_terminal` özel kabuklarına
    yönlendiren `ui_layout` değerleri) sessizce `"standard"`'a sıfırlanır. Hiçbir hata/bildirim gösterilmez.
- Kapsam dışı bırakılan, bilinçli kararlar: `_build_field_command_shell`/`_build_shd_terminal_shell` (app.py)
  ve fx.py'deki "isac"/"rogue"/"field" saat varyantları yapısal/dekoratif kod olarak silinmedi (yalnızca artık
  hiçbir tema seçiminden tetiklenmiyor) — "tema/şema" kapsamına girmiyor. 10 dil dosyasındaki artık kullanılmayan
  `theme.*`/`themedesc.*`/`set.theme`/`set.theme_note`/`theme.pack_hint`/`theme.pack_includes` çeviri anahtarları
  (~340+ satır) bilerek silinmedi — zararsız, kullanılmayan çeviri anahtarları olarak bırakıldı; `set.theme_note`
  artık görüntülenmiyor (Ayarlar ekranındaki kullanımı kaldırıldı) ama JSON'larda duruyor.
- **Test güncellemeleri**: `tests/test_project_structure.py`'deki `field_terminal`'e özel tema testi, artık
  tek-palet yapısını ve eski paket adının geçersiz olduğunu doğrulayan testlerle değiştirildi (fx.py'nin "field"
  varyant kodunun kendisinin hâlâ var olduğu ayrı bir testte korundu). `tests/ui_translate_test.py`'deki
  `apply_theme_pack("nightops"/"blacktusk"/"dark")` adımları (artık var olmayan bir metod) kaldırıldı/basitleştirildi.
  CI'daki (`build-installer.yml`) 21 test dosyasının hepsi + bu iki dosya, gerçek Tk widget kurulumuyla
  (python3.12 + xvfb-run) tekrar çalıştırılıp doğrulandı — hepsi geçti, `test_stability_widgets.py` tüm
  sayfaları/sekmeleri hatasız kurdu (`ok: true`, `callback_errors: []`).
- Sürüm `9.1.5.30`'a yükseltildi. Etiket/GitHub Release henüz oluşturulmadı — kullanıcı onayı bekliyor.

## Canlı çeviri: çoklu dil, güven uyarısı, önbellek düzeltmesi (9.1.5.29, 2026-11-04)

- Kullanıcı isteği: "canlı çeviri daha iyi çalışması için ne yapılmalı" sorusuna yanıt olarak belirlenen 4
  iyileştirmenin tamamı ("hepsini yapalım").
- **Kök sorun**: `livetranslate.AIMT` (yapay zekâ motoru) her zaman sabit bir İngilizce→Türkçe `SYSTEM` yönergesi
  kullanıyordu — uygulamanın seçili arayüz dili (10 dil: tr/en/de/es/fr/it/nl/pl/pt/ru) ne olursa olsun. Yani "AI"
  motoru seçili olsa da canlı çeviri fiilen her zaman Türkçeye çeviriyordu.
  - Düzeltme: `AIMT.SYSTEM_TMPL` (biçim dizesi) + `LANGUAGE_NAMES` eklendi; `AIMT(complete, target_lang=...)` artık
    hedef dile göre yönergeyi diziyor. `app.py`'nin `lt_translator()` metodu, AI motoru seçiliyken
    `i18n.current_language()`'ı hedef dil olarak geçiriyor. Yerel model (OPUS-MT) tek dil çifti (EN→TR) olduğu
    için o motor seçiliyken hedef her zaman `"tr"` sabit kalıyor — bu artık `build_translate()`'te açıkça
    belirtiliyor (`lt.e_local_tr_only` uyarısı, arayüz dili tr değilken gösterilir).
  - Geriye dönük uyumluluk: `AIMT.SYSTEM` sınıf özelliği (örnek oluşturulmadan erişilen eski kod/testler için)
    Türkçe varsayılanla korunuyor; her örnek kendi `self.SYSTEM`'ini hedef diline göre kuruyor.
  - Türkçeye özel son-işleme (`UI_TR` sözlük eşleşmesi, `WORD_FIX` regex düzeltmeleri) ve topluluk-onaylı düzeltme
    hafızası (`tasks_live.Memory`, sunucu tarafı tamamen Türkçe şema) artık yalnızca `target_lang == "tr"` iken
    devreye giriyor — başka bir hedef dilde bu Türkçeye özel kurallar artık çeviriyi bozmuyor. Bu mekanizmaların
    tüm dillere genelleştirilmesi (sunucu şeması/`server/worker.js` değişikliği gerektirir) bu turun kapsamı
    dışında bırakıldı.
  - Yan düzeltme: `Translator.ck` (önbellek anahtarı) hedef dili içermiyordu — tek hedef dil varken sorun
    yaratmıyordu ama çoklu hedef dil mümkün olunca diller arası önbellek çakışmasına yol açacaktı; anahtara
    `target_lang` eklendi.
- **OCR güven uyarısı**: `blocks_from_lines()` zaten her blok için 0-1 arası bir güven skoru döndürüyordu
  (`conf < 0.5` olanlar zaten eleniyor) ama `_lt_run()` bunu hiç kullanmıyordu — bulanık/karanlık bir ekranda
  OCR bazı harfleri yanlış okursa model gramer açısından tutarlı ama **anlamca hatalı** bir çeviri üretebilir ve
  kullanıcı bunu fark edemez (ansiklopedi açıklamalarındaki önceki kesik-metin hatasına benzer bir sınıf).
  - Düzeltme: yeni `LOW_CONF_WARN = 0.68` eşiği; `_lt_run()` içinde gösterilen her blok için güven kontrol
    edilip eşiğin altındaysa durum satırında "şüpheli çeviri" uyarısı (`lt.low_conf`) gösteriliyor. `pairs`
    tuple şeklini değiştirmeden (7+ yerde kullanıldığı için) ayrı bir `low_conf` boole değişkeniyle yapıldı.
- **UI**: Çeviri sekmesine (`build_translate()`) üç yeni bilgi satırı eklendi: yerel motorun yalnız Türkçe
  ürettiğine dair uyarı (arayüz dili ≠ tr ise), hedef dilin adı (`lt.target`), ve AI motorunun kalitesinin
  Asistan sekmesinde seçilen modele bağlı olduğuna dair not (`lt.ai_quality_hint`).
- i18n: `lt.low_conf`, `lt.e_local_tr_only`, `lt.target`, `lt.ai_quality_hint` — 10 dilin hepsine eklendi.
- Regresyon bulundu ve düzeltildi: `tests/test_app_stability.py`'deki iki test `blocks_from_lines`'ı 2'li tuple
  `(metin, kutu)` ile taklit ediyordu (gerçek fonksiyon her zaman 3'lü `(metin, kutu, güven)` döndürür); yeni
  `low_conf` hesaplaması `b[2]`'ye doğrudan erişince bu testlerde `IndexError` → sessizce `_lt_failure`'a
  düşüyordu. `len(b) > 2` koruması eklenerek düzeltildi.
- Doğrulama: `ast.parse` (app.py, livetranslate.py) temiz; 10 dilin JSON'u geçerli ve `i18n.set_language` + `t()`
  ile tüm yeni anahtarlar biçimlendirmeyle test edildi; `tests/test_livetranslate.py` (29/29), `tests/
  test_translation_reliability.py` (9/9), `tests/test_translation_controls.py` (5/5), `tests/
  test_app_stability.py` (17/17) ve `tests/test_stability_widgets.py` (xvfb altında, 15 sayfa/6 sekme, callback
  hatası yok) PASS. (Bu ortamda `tkinter` yalnız `python3.12` + `python3-tk` ile vardı; testler ondan çalıştırıldı.)
- Kapsam dışı bırakılan: topluluk düzeltme/öneri sisteminin (`tasks_live.suggest`) sunucu tarafının tüm dillere
  genelleştirilmesi (büyük D1 şema değişikliği gerektirir); mevcut `"lt.partial"` anahtarının 10 dil dosyasının
  hiçbirinde bulunmaması (önceden var olan, bu turla ilgisiz bir boşluk — not düşüldü, düzeltilmedi).

## Sürüm geçmişi penceresi: herhangi bir sürümü kurma + bilinen sorunlar (2026-11-04)

- Kullanıcı isteği: kullanıcıların programın içinden istedikleri bir sürümü kurabilecekleri bir alan ve
  kurdukları sürümdeki bilinen sorunları görebilecekleri bir bölüm.
- Önceden var olan "Sürüm geçmişi" penceresi (`app.py` → `show_version_history`) yalnızca **mevcut sürümden
  eski** bir GitHub sürümüne dönüşe izin veriyordu (`upd.rollback_not_older` ile bloklanıyordu). Artık listedeki
  **herhangi bir sürüm** (eski ya da yeni, beta dahil) seçilip kurulabiliyor; tek engel, zaten kurulu olan
  sürümün seçilmesi (`upd.already_installed`).
  - Liste satırında kurulu sürüm "✓" ile işaretlenir ve pencere açılışında ilk satır otomatik seçilir.
- **Bilinen sorunlar / bu sürümde ne var:** Listede bir sürüm seçildiğinde, o GitHub Release'in notları (zaten
  `updater.releases()` ile çekilen `notes` alanı — `.github/release_notes.md`'deki içerik) pencere içinde ayrı bir
  kaydırılabilir metin alanında gösterilir. Ayrıca "🐞 Bilinen sorunlar (GitHub)" düğmesi, depodaki canlı
  `BUGS.md`'yi tarayıcıda açar (her zaman en güncel durum).
- Ağ/kurulum mantığında değişiklik yok (`updater.install_frozen`/`update_source` zaten yön bağımsız çalışıyor);
  yalnızca UI kısıtlaması gevşetildi ve bilgi paneli eklendi.
- i18n: `upd.history_title`, `upd.history_note`, `upd.history_ready`, `upd.rollback`, `upd.rollback_ask`
  metinleri (eski "geri dönüş" dilinden "kurulum" diline) güncellendi; `upd.notes_label`, `upd.notes_empty`,
  `upd.known_issues`, `upd.already_installed` eklendi. Önceden bu pencerenin metinleri **yalnızca tr/en**'de
  vardı (diğer 8 dil İngilizce'ye düşüyordu) — bu fırsatla **10 dilin hepsine** tam çeviri eklendi
  (`upd.history*`, `upd.rollback*`, `upd.close` dahil).
- Doğrulama: `tests/test_core.py` PASS; `ast.parse(app.py)` ile sözdizimi doğrulandı (bu ortamda `tkinter` yok,
  gerçek pencere açılış testi `tests/ui_update_shot.py` ile yalnız Windows CI'da çalışır — yayın akışında
  (`build-installer.yml`) zaten tetiklenecek).

## Ansiklopedi: 30 kesik açıklama düzeltildi (asıl kapsam 13 değil 30) (2026-11-04)

- Kullanıcı isteği "13 yarım ansiklopedi çevirisi" üzerine araştırma, asıl kapsamın **30 isim** olduğunu ortaya
  çıkardı. İlk tarama yöntemi (çevrilmiş metinde `…` arama) yalnızca 13'ünü buluyordu; kalan 17'si, kesik
  İngilizce kaynağın makine çevirisi tarafından gramer olarak tam görünen (ama içerik olarak eksik) cümlelere
  çevrilmesi nedeniyle görünür bir iz bırakmıyordu.
- Kök neden: `meta/sources/wiki_exotics.json`'da 18 egzotik kaydının `desc` alanı tam olarak **400 karakterde**,
  `meta/sources/wiki_talent_desc.json`'da 12 talent kaydı ise **~190 karakterde** kelime/cümle ortasında
  kesilmişti. `knowledge.py`'nin kaynak önceliği (`wiki_exotics.json`/`wiki_talent_desc.json` → `game_data.json`)
  bu kesik metni, `game_data.json`'da zaten eksiksiz bulunan açıklamanın önüne geçiriyordu.
- Düzeltme:
  - `meta/sources/wiki_exotics.json`: 18 kaydın `desc` alanı `game_data.json`'daki (`gear_talent_details`/
    `weapon_talent_details[].description`) tam metinle değiştirildi.
  - `meta/sources/wiki_talent_desc.json`: 12 kesik kayıt tamamen kaldırıldı — kod otomatik olarak
    `game_data.json`'daki tam metne düşüyor (`setdefault` ile dolduruluyor), ek kod değişikliği gerekmedi.
  - `meta/descriptions_i18n.json`: bu 30 ismin tr/de/fr/es/it/pt/ru/pl/nl çevirileri, artık tam olan İngilizce
    kaynağa göre sıfırdan yeniden yazıldı (270 metin).
- Yan etki ve ikinci düzeltme: yeni, tam çeviriler `descriptions_i18n.json`'ı proje için belirlenen
  510.000 bayt sınırının (bkz. `meta/UPDATER.md`, `tests/test_knowledge.py`) üzerine çıkardı (516.482 bayt).
  Kurala uygun olarak en büyük 3 kayıt (`Disruptor Rounds`, `Bluescreen`, `The Ravenous` — toplam ~17 KB)
  `meta/descriptions_i18n_2.json`'a taşındı (ilk kez oluşturuldu; `meta_sync.fetch_descriptions` iki dosyayı
  birleştirir, bir giriş iki dosyada birden bulunmaz).
- Doğrulama: `tests/test_knowledge.py` (boyut sınırı dahil tüm 30 kontrol), `tests/test_core.py`,
  `tests/test_regression_crash_patterns.py` — üçü de tam PASS.

## `server/` için eksik `package.json` eklendi — Workers Builds CI hatası çözüldü (2026-11-04)

- Kök neden: `server/` dizininde hiç `package.json`/`package-lock.json` yoktu. Cloudflare Workers Builds (CI servisi),
  deploy komutunu (`npx wrangler deploy`) çalıştırmadan önce paket yöneticisini tespit edip bir kurulum adımı
  yapıyor ve Wrangler sürümünü `package.json`'dan okuyor (bkz. Cloudflare resmi dokümantasyonu, workers/ci-cd/builds).
  `package.json` olmadan bu adım CI'da başarısız oluyordu.
- Yerelde neden fark edilmedi: `npx wrangler deploy` yerelde her çalıştırıldığında, yerel bir sürüm bulamayınca
  Wrangler'ı ağdan taze indirip çalıştırıyor (npx'in standart davranışı) — bu da `package.json` olmadan da yerel
  `--dry-run`'ın sorunsuz görünmesine yol açıyordu. CI ortamı ise farklı bir kurulum akışı izliyor.
- Düzeltme: `server/package.json` (Wrangler `^4.0.0` devDependency) ve `npm install` ile üretilen
  `server/package-lock.json` eklendi. `node_modules/server` zaten `.gitignore`'daydı. `npx wrangler deploy --dry-run`
  yeniden çalıştırılıp aynı binding listesiyle başarılı olduğu doğrulandı (gerçek deploy yapılmadı — sadece dry-run).
- **Doğrulandı (2026-11-04, aynı oturum):** Commit push edildikten sonra GitHub üzerinde "Workers Builds: td2-stats"
  check'i izlendi ve `success` ile tamamlandı (önceki commit'lerde `failure` idi). "Cloudflare Pages" ve "server"
  check'leri de `success`. Sorun tamamen çözüldü, CI'da canlı olarak doğrulandı.

## `recal_advisor` ücretsiz yapıldı — mx-division-builds lisans gri alanı çözüldü (2026-11-04)

- `features.py`: `"recal_advisor": "premium"` → `"free"`. Kullanıcı kararı: mx-division-builds (CC BY-NC-SA 4.0,
  "ticari olmayan kullanım") verisine dolaylı dayanan tek özellik artık hiçbir ücretli kapı arkasında değil, bu da
  `LICENSE_NOTES.md`'de belgelenen gri alanı ortadan kaldırıyor.
- `features.Entitlements.has()` "free" tier'ı lisanssız her zaman `True` döndürdüğü için başka kod değişikliği
  gerekmedi; Premium sayfası (`app.build_premium_box`) listeyi `features.FEATURES`'tan otomatik çektiği için de
  elle güncelleme gerekmedi.
- Üç test dosyası güncellendi (artık premium örneği olarak `recal_advisor` yerine `optimizer_all` kullanıyorlar):
  `tests/test_core.py`, `tests/test_account.py`, `tests/ui_account_test.py`. `test_core.py` yerel olarak çalıştırıldı, 18/18 PASS.
- `LICENSE_NOTES.md`, `BUGS.md`, `HANDOFF.md`, `ROADMAP.md` güncellendi. [issue #153](https://github.com/mxswat/mx-division-builds/issues/153) nezaketen açık bırakıldı, artık engelleyici değil.

## 9.1.5.19 düzeltmelerinin gerçek Windows'ta doğrulanması (2026-11-04)

- Kullanıcının bağlı Windows bilgisayarında (v9.1.5.20, kurulu/installer sürüm) computer-use (ekran görüntüsü + tıklama) ile üç senaryo manuel olarak test edildi:
  1. **Ansiklopedi → "Wiki'de aç" düğmesi** (`webbrowser` global import düzeltmesi): "Acosta Kneepads" öğesinde tıklandı, Chrome yeni sekmede ilgili wiki sayfasını açtı, uygulama çökmedi/hata vermedi. ✅
  2. **Ayarlar → Genel → Sürüm geçmişi** (`except...as X` kapanış-değişkeni düzeltmesi, Sürüm Geçmişi yükleme hatası yolu): pencere açıldı, başlık metni göründü, içerik listesi boş kaldı (ayrı, teşhis edilmemiş bir görüntü davranışı — bkz. not altında) ama **hiçbir çökme/hata diyaloğu çıkmadı**. ✅ (çökme açısından)
  3. **Ayarlar → Hizmetler → Tanılama Merkezi → "Sorunları tara"** (aynı `except...as X` bug sınıfının asıl kaynağı — hata bildirimi `root.after` lambda'sı): tarama çalıştırıldı, sonuç bildirimi ("Tanılama bitti: 0 hata, 1 uyarı") üstte bildirim olarak göründü, olay kaydına INFO satırları eklendi, uygulama tamamen yanıt verir durumda kaldı. ✅
- Üçü de çökmesiz tamamlandı; 9.1.5.19'daki iki `NameError` çökmesinin gerçek Windows + DWM render yolunda da düzeldiği doğrulandı (önceden yalnızca Linux/Xvfb'de doğrulanmıştı).
- Not: "Sürüm geçmişi" penceresindeki boş liste alanı ayrı bir gözlem — kök nedeni araştırılmadı (muhtemelen GitHub Releases API'sinden veri çekme/gösterme ile ilgili, çökme hatasından bağımsız bir görüntü sorunu olabilir). Kayıt altına alındı, aktif olarak izlenmiyor.
- Sonuç: BUGS.md #5 ("Gerçek Windows render testi henüz yapılmadı") çözüldü olarak işaretlendi.

## Akış boyut sınırı: sıkıştırma ve ikinci açıklama dosyası (2026-11-03)

- Uygulama 512 KiB'tan büyük akışı reddediyor (`meta_sync.MAX_BYTES`). `descriptions_i18n.json` 520.801, `game_data.json` 522.958 bayta ulaşmıştı.
- Her iki dosya girintisiz yazıldı (475.914 ve 419.358 bayt), kullanılmayan `_src` kaldırıldı, veri içeriği değişmedi. `game_data.json` yazan betikler de girintisiz yazıyor.
- Çevrilmemiş 210 giriş (~370 KB) tek dosyaya sığmıyor. Sınırı yükseltmek eski sürümlerin indirmesini keseceği için `descriptions_i18n_2.json` eklendi; `meta_sync.fetch_descriptions` iki dosyayı birleştirir. Kural: `meta/UPDATER.md`.
- İkinci dosya, bu kodu içeren sürüm yayınlanınca kullanıcılara görünür.

## Web sitesi yayını + sunucu CI/CD (2026-11-03)

- `web/` (hesap/haberler/premium/tanıtım sayfaları) Cloudflare Pages'e yayınlandı: https://td2-loot-advisor.pages.dev — GitHub bağlantılı (Pages → `main` dalı, build output `web`), Direct Upload değil (native dosya seçici tarayıcı otomasyonundan görünmediği için GitHub entegrasyonuna geçildi).
- `td2-stats` Worker'ı (backend) artık GitHub'a bağlı: Cloudflare Workers Builds, `main` dalındaki `server/` dizininden `npx wrangler deploy` ile otomatik derleyip yayınlıyor (Root directory: `server`). Önceden Quick Edit'te elle kopyala-yapıştırla denendi; Monaco editörü ayrı origin'deki bir iframe'de olduğu için tarayıcı otomasyonunun `paste` olayı güvenilir çalışmadı — bu yüzden API token yerine (gereksiz yetki eklemeden) doğrudan Git entegrasyonu tercih edildi, kullanıcı onayıyla kuruldu.
- Bu commit, bağlantıdan sonraki ilk build'i tetiklemek için atıldı; `server/accounts.js` ve `worker.js`'deki CORS 204-gövde düzeltmesi ile `SITE_URL` tabanlı web girişi dalı zaten `main`'de mevcuttu, sadece canlıya alınması gerekiyordu.

## 9.1.5.19 — Kod taraması: çökme düzeltmeleri ve lisans şeffaflığı (2026-11)

- Tüm `.py` dosyaları `ruff`/`pyflakes` ile tarandı (bir AI oturumunda, "ADMİN YETKİSİ" ile tüm kod tabanını tarayıp sorunları kendi başına düzeltip yeni sürüm yayınlama talimatıyla).
- 2 gerçek çalışma zamanı çökme hatası bulundu ve düzeltildi (bkz. BUGS.md).
- ~30 ölü kod/kullanılmayan import temizlendi; davranış değişikliği yok, tam test paketiyle doğrulandı.
- `LICENSE_NOTES.md` eklendi: mx-division-builds (CC BY-NC-SA 4.0) verisinin ücretsiz/premium ayrımıyla ilişkisi belgelendi.
- `main`/`master` dal ayrışması `git merge --no-ff` ile birleştirildi (9.1.5.18'deki `td2app/ui` yeniden yapılanması ve `diagnostics_center.py` `main`'e taşındı).
- Ardından: `tests/test_regression_crash_patterns.py` eklendi (iki çökme hatasının kalıcı statik-analiz koruması); `DEVELOPMENT_LOG.md`, `BUGS.md`, `TESTING.md`, `DEPENDENCIES.md`, `HANDOFF.md` repoya eklendi.

## 9.1.5.18 — Tanılama motoru, güvenli düzeltmeler, arayüz kararlılığı

- Gerçek Tanılama Merkezi: ayar dosyası erişimi, log klasörü yazılabilirliği, Tesseract komutu, çeviri motoru/model hazırlığı, overlay durumu, görsel katmanlar, oyun penceresi — tamamı yerel kontrollerle (ağ isteği yok, oyun belleğine dokunmaz).
- Güvenli Görünüm: fare izi, özel imleç, video, saydam arka plan, geçiş katmanları tek adımda kapatılabilir.
- Canlı olay kaydı + maskelenmiş (kullanıcı yolu/e-posta/anahtar/token/webhook/yerel IP) rapor önizlemesi.
- İmleç kararlılığı: kararsız Win32 native cursor subclass köprüsü normal kullanımda devre dışı.
- `td2app/ui` paket göçü başladı (eski kök modüller uyumluluk köprüsü olarak korundu).

## 9.1.5.10 – 9.1.5.17 — Windows render/kararlılık düzeltmeleri serisi

Bu seri, Linux/Xvfb testlerinin yakalayamadığı, yalnızca gerçek Windows + DWM/DX12 birleşiminde ortaya çıkan görsel hataları sırayla düzeltti:
- 9.1.5.10: genel güvenilirlik düzeltmeleri; boş/siyah çeviri overlay'leri.
- 9.1.5.11: boş/siyah canlı çeviri penceresi (saydamlık renk anahtarı).
- 9.1.5.12: HDR durumunun bayat önbellekten değil dosyadan güncel okunması.
- 9.1.5.13: Windows'ta yerinde çeviri için büyük saydam Canvas yerine küçük opak kutular (DX12/DWM saydamlık hatasını by-pass).
- 9.1.5.14: küçük kutularda Label/Canvas font ölçü uyumsuzluğu (metin kırpılması) düzeltmesi.
- 9.1.5.15: native renderer'a göre eski UI testinin yanlış negatif üretmesi düzeltildi.
- 9.1.5.16–9.1.5.17: Panel/HUD/yerinde çeviri kutularında `WS_EX_LAYERED` kaldırıldı (bazı Windows/DWM+DX12 kombinasyonlarında metni görünmez yapıyordu).

### Sürüm geçmişi penceresi: "liste boş kalıyor" şikayetinin kök nedeni (2026-11-04, v9.1.5.23)

- **Semptom:** Kullanıcı Ayarlar → Genel → Güncellemeler → "Sürüm geçmişi" düğmesine tıkladığında hiçbir şey
  görmedi — ne sürüm listesi, ne durum metni, ne de tıklanabilecek bir buton. Bu, 9.1.5.22'de tam olarak
  kullanıcının istediği şekilde (herhangi bir sürümü seçip onaylayarak kurma) yeniden yazılan özellikle aynı
  anda, ve daha önce 9.1.5.20'nin gerçek Windows testinde not edilen "içerik listesi boş kaldı" gözlemiyle
  aynı belirtiydi (bkz. `BUGS.md` #5) — demek ki bu iki farklı olay değil, aynı, o zamandan beri çözülmemiş
  tek bir hataydı.
- **Teşhis:** Uzak bilgisayara ekran görüntüsü alma özelliği o sırada arızalıydı
  ("desktopCapturer returned no screen sources"), bu yüzden pencereyi gözle doğrulamak mümkün olmadı.
  Önce `app.log`'dan kullanıcının gerçekten v9.1.5.22'yi çalıştırdığı ve kurulu `lang/tr.json`'da yeni
  `upd.*` metinlerinin doğru şekilde mevcut olduğu doğrulandı (kod/çeviri dağıtımı sorunlu değildi).
  Kullanıcıya doğrudan ne gördüğü soruldu; yanıt ("liste yok, bakabileceğim bir tuş da yok") bir ağ/API
  hatasıyla (o zaman en azından bir hata metni görünürdü) değil, pencerenin **hiç kurulamadan** sessizce
  başarısız olduğuna işaret ediyordu. `app.py`'deki `show_version_history` kodu satır satır yeniden okunduğunda
  `lb = tk.Listbox(..., bg=PAL["panel"], ...)` ve `notes_txt = tk.Text(..., bg=PAL["panel"], ...)` satırları
  bulundu — `ui_theme.PALETTES`'teki hiçbir temada (`dark`, `light`, `classic`, ne de ondan türeyen oyun
  paketlerinde: `hunter`, `darkzone`, vb.) `panel` adlı bir anahtar yok (anahtarlar: `bg`, `surface`,
  `surface2`, `fg`, `accent`, …). Bu satırlar çalışınca Python `KeyError: 'panel'` fırlatıyor; bu bir
  Tkinter buton-komutu (callback) içinde olduğu için ve uygulamada `Tk.report_callback_exception` override'ı
  bulunmadığı için hata ne bir diyalogla kullanıcıya gösteriliyor ne de `log.py` tabanlı uygulama loguna
  yazılıyor (`--noconsole` build'de varsayılan Tk hatası stderr'e basılır, oraya kimse bakmaz) — sonuç:
  tamamen sessiz, iz bırakmayan bir başarısızlık.
- **Düzeltme:** İki `PAL["panel"]` kullanımı `PAL["surface"]` ile değiştirildi (dosyadaki tüm diğer
  temalı Listbox/Text widget'larının kullandığı anahtarla aynı — bkz. örn. `self.lt_hist_txt`,
  `self.enc_txt`, `self.diag_text`). Ardından `app.py`'deki tüm `PAL["…"]` kullanımları (`grep`) yeniden
  tarandı; geçersiz başka bir anahtar kalmadığı doğrulandı.
- **Doğrulama:** `ast.parse` (sözdizimi), `tests/test_core.py` + `tests/test_regression_crash_patterns.py`
  (20/20 PASS — Tkinter bu konteynerde yok, bu yüzden pencerenin gerçek açılışı yalnızca Windows CI/gerçek
  makinede doğrulanabilir). Bu tür bir hatanın bir daha sessizce geçmemesi için not: ileride benzer GUI
  değişikliklerinde `PAL[...]` anahtarları mutlaka `ui_theme.PALETTES["dark"]`'ın gerçek anahtar kümesiyle
  karşılaştırılmalı; ayrıca bu sınıfın (`Tk.report_callback_exception` yokluğu) bir sonraki fırsatta genel
  olarak ele alınması, benzer hataların geleceğe gizlenmesini önler (bkz. `TODO.md`/`ROADMAP.md`).

### Mobil: push-token sunucuya kaydı eksikti, kod yazıldı (2026-11-04)

- **Boşluk**: `server/mobile.js`'in `PUT/DELETE /v1/mobile/push-tokens/{id}` ucu hazırdı (Android/FCM canlı,
  iOS/APNs kodu hazır) ama Flutter uygulaması bu ucu hiçbir zaman çağırmıyordu — telefon kendi FCM/APNs
  token'ını sunucuya hiç kaydetmiyordu, bu yüzden hiçbir telefon push bildirimi alamıyordu.
- **Eklenenler**: `mobile/pubspec.yaml`'a `firebase_core`/`firebase_messaging`; yeni
  `mobile/lib/services/push_registration.dart` (izin isteme + token alma, Firebase kurulu değilse
  sessizce `null` döner — çökmez); `mobile/lib/services/cloud_api.dart`'a `putPushToken`/`deletePushToken`;
  `mobile/lib/services/cloud_link.dart`'a `registerPushTokenQuietly()` (eşleştirme sonrası + her açılışta
  zaten eşleşmişse çağrılır, `onTokenRefresh`'e abone olup token yenilenince otomatik tekrar kaydeder;
  `unpair()` artık sunucudaki kaydı da temizliyor); `AndroidManifest.xml`'e `POST_NOTIFICATIONS` izni;
  `settings.gradle.kts`'e `com.google.gms.google-services` plugin bildirimi (`apply false` — güvenli,
  dosya olmasa da derlemeyi bozmaz); `app/build.gradle.kts`'te asıl `apply` satırı **bilerek yorumlu**
  bırakıldı (gerçek `google-services.json` olmadan açılırsa Gradle derlemesi patlar).
- **Kalan tek adım (kullanıcı/Firebase konsolu gerekiyor)**: `google-services.json`'ı mevcut
  "td2-loot-advisor" Firebase projesinden indirip `mobile/android/app/`'a koymak, sonra bir Gradle
  satırının yorumunu kaldırmak. Tam adımlar: `docs/push_notifications_setup.md` (yeni).
- **Doğrulama sınırı**: Bu konteynerde Flutter SDK'sı yok — kod sözdizimi elle (brace/parantez dengesi,
  satır satır okuma) kontrol edildi ama `flutter pub get`/`analyze`/`test` ÇALIŞTIRILMADI. Bir sonraki
  oturum veya kullanıcı bunu Windows PC'sinde (Flutter zaten kurulu ve doğrulanmış, bkz. yukarısı)
  çalıştırmalı. Ayrıntı ve gerekçe: `BUGS.md` #6, `docs/mobile_companion_roadmap.md`.

### Yeni özellik: "Bu oturumda ne kazandın?" oturum özeti (2026-11-04)

- **Amaç**: Kullanıcının envanterde harcadığı zamanı azaltmak olan proje hedefini somutlaştıran bir
  "wow" anı — oyun kapandığında (veya tepsi menüsünden istenince) o oturumda ne kadar eşya tarandığını,
  kaç tanesinin saklanıp/kırıldığını ve **tahmini kazanılan süreyi** gösteren bir özet penceresi.
- **Veri kaynağı**: Yeni bir ölçüm sistemi kurulmadı — mevcut `service.SessionLog` sınıfı (zaten
  `scanned/keep/consider/dismantle/exotic/named/upgrades/highlights` tutuyordu) ve `App._game_event`'in
  `"game"/"stopped"` dalındaki `self.sessions.end()` çağrısı olduğu gibi kullanıldı; önceden bu veri
  sadece telefon push bildirimine gidiyordu, masaüstünde hiç gösterilmiyordu.
- **Tahmini kazanılan süre**: `SESSION_SAVE_SEC_PER_ITEM = 12` (saniye/eşya) sabiti — "bir eşyayı elle
  inceleyip build'e göre karar vermenin ortalama süresi" kabaca varsayımı. **Gerçek bir ölçüm değil**,
  bilerek yalnızca kaba bir gösterge; arayüzde her yerde "tahmini" ibaresiyle gösteriliyor (bkz. proje
  talimatları madde 5: "gerçek olmayan işlevleri tamamlanmış gibi sunma").
  `App._session_time_saved_min(c) = round(c["scanned"] * 12 / 60, 1)` dakika.
- **Eklenenler** (`app.py`): `App._show_session_summary(c)` (yeni `Toplevel` penceresi; `show_version_history`
  ile aynı stil kalıbı, `draw_bars`/`COLORS`/`verdict_label` ile mevcut İstatistik sekmesiyle görsel tutarlılık),
  `App._session_time_saved_min(c)`, `App._show_last_session_summary()` (tepsi menüsü girişi için). `_game_event`
  artık `self._last_session = c` tutuyor ve yeni `svc_session_popup` ayarı (varsayılan açık) açıksa **ve**
  pencere tepside gizli değilse (`self.root.state() != "withdrawn"`) pencereyi otomatik açıyor — sessiz
  tepside çalışırken odağı çalmamak için pop-up atlanıyor, ama özet `_last_session`'da kalıyor ve tepsi
  menüsündeki yeni "📊 Son oturum özeti" girişiyle her zaman tekrar açılabiliyor. Ayarlar sayfasına
  (`build_service_page`) "Oyun kapanınca oturum özetini göster" onay kutusu eklendi.
- **Çeviri**: 10 dilin hepsine (`lang/*.json`) `session.*` (summary_title, duration, time_saved,
  time_saved_note, scanned, breakdown, exotic_n, named_n, upgrades_n, highlights_label, none_yet) ve
  `svc.session_popup`/`svc.tray_last_session` anahtarları eklendi — mevcut raw-metin-ekleme kuralına
  uyularak (tam `json.dump` yerine, var olan dosyaların satır bazlı yama'sı), `python3 -c "import json;
  json.load(...)"` ile 10 dosyanın da geçerli JSON kaldığı doğrulandı.
- **Doğrulama**: `python3 -I -m py_compile app.py` temiz geçti; `i18n` modülü ile 10 dilin tamamında
  yeni anahtarlar gerçekten okunabiliyor mu (`i18n.missing_keys()` boş) test edildi. Gerçek bir Tkinter
  penceresinin görsel olarak açılması bu (ekransız) konteynerde doğrulanamadı — kullanıcının programı
  bir oturum sonunda çalıştırıp pencereyi görmesi gerekiyor.

### Yeni özellik: "Build Karşılaştır" ekranı (2026-11-04, v9.1.5.26)

- **Amaç**: Kullanıcının birden fazla build'i olduğunda hangisine odaklanmasının daha mantıklı olduğuna
  karar vermesini kolaylaştırmak — iki build'i yan yana, yuva yuva tamamlanma durumuyla karşılaştıran
  yeni bir ekran. Proje hedefi olan "envanterde harcanan zamanı azaltma"ya, bu kez build seçimi
  aşamasında hizmet ediyor.
- **Veri kaynağı**: Yine yeni bir ölçüm sistemi yok — mevcut `App.build_status`/`plan_of`/`self.progress`
  (zaten "Build Planı" sekmesinin tek-build görünümünde kullanılıyordu) olduğu gibi iki build için
  paralel çağrılıyor.
- **Eklenenler** (`app.py`): `App._slots_shareable(req1, req2)` — iki yuva şartının aynı fiziksel eşyayla
  karşılanıp karşılanamayacağının kaba tahmini (aynı özel eşya, ya da aynı çekirdek attribute + ortak
  set/marka adı → "ortak kullanılabilir"; kesin bir garanti değil, sadece gösterge). `App.show_build_compare()`
  — yeni `Toplevel` penceresi: iki `Combobox` ile build seçimi, her build için ilerleme çubuğu/yüzde,
  8 yuvalık karşılaştırma tablosu (renk kodlu durum + `req_lines_short` ile kısa özet + "🔁 Ortak" etiketi),
  ortak set/marka/özel eşya/talent listesi, ve hangi build'in tamamlanmaya daha yakın olduğu + diğerine
  geçerken kaç yuva için farklı eşya gerekeceğinin (tahmini) özeti. "Build'ler" sekmesindeki sol panele
  "🆚 Karşılaştır" düğmesi eklendi (varsayılan seçim: şu an açık build + listedeki ilk farklı build).
- **Çeviri**: 10 dilin hepsine `cmp.*` (compare_btn, title, pick_a, pick_b, need_two, overlap, shared_sets,
  shared_items, shared_talents, none, shareable, verdict_equal, verdict_closer, switch_cost) anahtarları
  eklendi — aynı satır bazlı yama kuralıyla, 10 dosyanın da geçerli JSON kaldığı ve `i18n.missing_keys()`
  boş döndüğü doğrulandı.
- **Doğrulama**: `python3 -I -m py_compile app.py` temiz geçti; gerçek Tk penceresinin görsel render'ı bu
  ekransız konteynerde teyit edilemedi (bkz. `BUGS.md` #12). "Ortak kullanılabilir eşya" tahmini kasıtlı
  olarak kaba bir heuristik — gerçek roll kalitesini hesaba katmaz.

### Yeni özellik: "Bu karar yanlıştı" geri bildirimi (2026-11-04, v9.1.5.27)

- **Amaç**: Program bir eşyayı SAKLA/DÜŞÜN/KIR olarak yanlış değerlendirdiğinde kullanıcının bunu tek
  tıkla işaretleyebilmesi — "yanlış karar verilerinin toplanıp kuralların iyileştirilmesi" proje hedefine
  hizmet eder. **Bilerek açık netlik**: bu, programın kendi kurallarını (attribute ağırlıkları, eşikler)
  otomatik değiştiren bir öğrenme sistemi DEĞİL — öyle bir altyapı yok ve proje talimatları "gerçek olmayan
  işlevi tamamlanmış gibi sunma" diyor. Yaptığı: kullanıcının gözlemini yapılandırılmış biçimde yerel bir
  kayda (ve istersen mevcut geri bildirim kanalıyla geliştiriciye) iletmek; build ince ayarı (attribute/
  weight) kullanıcının kendi elinde kalıyor.
- **Eklenenler** (`app.py`): `VERDICT_FEEDBACK_PATH`/`VERDICT_FEEDBACK_KEEP` sabitleri, `load_verdict_feedback`/
  `save_verdict_feedback` (mevcut `safeio.write_json`/`read_json` — atomik yazım + `.bak` yedek — kullanılarak,
  yeni bir dosya I/O şeması kurulmadı). `App.report_wrong_verdict()` — Panel'deki "⚠ Bu karar yanlıştı"
  düğmesi (mevcut "⚑ Yanlış okundu" düğmesinin yanına, `self.last_shown`'daki son taranan eşya/karar/skor
  üzerinden çalışır): doğru kararı seçtirir, isteğe bağlı not aldırır, "💾 Kaydet" (yalnız yerel) veya
  "Kaydet ve gönder" (yerel + mevcut `open_feedback`/`reports.Store` akışına, `report_wrong`'daki gibi
  `type="bug"` ile, yapılandırılmış JSON gövdeyle devam). `App.show_verdict_feedback_log()` — Tanılama
  Merkezi'ne eklenen "⚠ Yanlış karar bildirimlerim" düğmesiyle açılan, kaydedilen tüm bildirimleri listeleyen
  bir Treeview penceresi.
- **Çeviri**: 10 dilin hepsine `vf.*` (btn, title, ask, note_label, need_pick, saved_local, save_local,
  save_send, fb_title, fb_body, log_btn, log_title, log_empty, col_time/item/given/correct/build/note)
  anahtarları eklendi — aynı satır bazlı yama kuralıyla, 10 dosyanın da geçerli JSON kaldığı ve
  `i18n.missing_keys()` boş döndüğü doğrulandı.
- **Doğrulama**: `python3 -I -m py_compile app.py` temiz geçti; gerçek Tk penceresinin görsel render'ı bu
  ekransız konteynerde teyit edilemedi (bkz. `BUGS.md` #13).

### Ana tema/menü modernizasyonu + "Hakkında" sekmesi (2026-11-04, v9.1.5.28)

- **Amaç**: Kullanıcının isteği — "Programın ana teması ve menüleri daha modern ve sade bir tasarım
  yapalım. Menüler açık ve net olmalı. Programın içerisinde Program hakkında ve kurucu şirket bilgileri
  içeren bir bölüm olsun." Not: programın herhangi bir geleneksel menü çubuğu (`tk.Menu`) yok — "menüler"
  burada mevcut kenar-çubuğu-grup-düğmeleri + iç notebook-sekme sistemi anlamına geliyor (`app.py`
  `grep "tk.Menu("` sıfır sonuç verdi, bu araştırılıp doğrulandı).
- **Yeni tema paketi "kaivolt"** (`td2app/ui/ui_theme.py` `_PACKS`): kurucu stüdyo Kaivolt'un marka
  renkleri — Deep Space Navy zemin (`#0b1120`), Electric Violet vurgu (`#7c5cfc`), Volt Cyan ikincil renk
  (`#22d3ee`), Ivory metin (`#f5f7ff`). Var olan `PALETTES`/`apply()` boyama altyapısı aynen yeniden
  kullanıldı — `apply()` fonksiyonuna hiç dokunulmadı, sadece palet tablosuna yeni bir giriş eklendi.
  `apply_pack()`'e yeni bir `elif mode == "kaivolt"` dalı eklendi: `ui_nav_layout="flat"` (var olan
  kademeli/"tactical" kenar-çubuğu ofseti mantığı zaten bu değer için düz, hizalı bir görünüm üretiyordu —
  `app.py build_ui()`'daki `tactical_nav` kontrolü sayesinde YENİ bir düzen kodu yazılmadı), `ui_layout=
  "standard"` (alternatif "field_command"/"shd_terminal" kabuklarına girmez), `fx_transition_style="soft"`,
  dekoratif arka plan animasyonu (`fx_bgwatch`) kapalı.
- **Yeni varsayılan**: `DEFAULTS["ui_theme"]` `"isac"` → `"kaivolt"` (yalnız SIFIRDAN kurulumları etkiler —
  var olan kullanıcıların kayıtlı `ui_theme` değeri dokunulmadan kalır). `build_ui()`'daki geri dönüş
  değeri de güncellendi. Diğer 17 tema (ISAC dahil) Ayarlar → Görünüm'de seçilebilir kalıyor; "◆ ISAC"
  kenar-çubuğu marka etiketi bilerek değiştirilmedi (oyun-içi ISAC referansı diğer tüm temalarla uyumlu;
  Kaivolt kimliği yeni "Hakkında" sekmesine taşındı — bkz. altta).
- **Yeni "Hakkında" sekmesi** (`app.py` `App.build_about()`, "Diğer" grubu, Geçmiş/Kayıt/Yardım'ın
  yanında): sürüm numarası + GitHub bağlantısı + geri bildirim düğmesi üstte; alt kısımda `help.body`
  ile aynı mekanizmayı (`Text` widget, BÜYÜK HARFLİ satırlar başlık rengiyle) kullanan `about.body` metni
  — programın ne yaptığı/yapmadığı (ekranı okur, oyunun belleğine dokunmaz), açık kaynak/MIT lisansı, ve
  kurucu stüdyo Kaivolt'un tanıtımı (vizyon/değerler, "Yazılım ve Ses, Mühendislikle." sloganı). İçerik
  claude.ai projesindeki `kaivolt-brand-identity.md` belgesinden alındı. `TAB_ICONS`'a `"about": "🏢"`,
  `tab_keys`/`tab_groups`'a `"about"` eklendi; normal/field_command/shd_terminal kabuklarının üçünün de
  `_ui_builders` listesine `self.build_about` eklendi (üç kabuk da aynı `tab_keys`'i paylaşıyor).
- **Çeviri**: 10 dilin hepsine `tab.about` + `about.body` anahtarları eklendi (satır bazlı yama, `"tab.help"`
  çapası kullanılarak — `vf.*`/`cmp.*` yama script'leriyle aynı yöntem). `theme.kaivolt`/`themedesc.kaivolt`
  ise yalnızca `tr.json` ve `en.json`'a eklendi — proje zaten tema-paketi çevirilerini (ör. `theme.isac`,
  `theme.shd_terminal`) sadece bu iki dosyada tutuyor ve diğer 8 dil `i18n.t()`'nin İngilizce yedeğiyle
  otomatik düşüyor (bu davranış doğrulandı, kod değişikliği gerekmedi).
- **Doğrulama**: `python3 -I -c "import ast; ast.parse(...)"` ile `app.py` ve `ui_theme.py` temiz geçti.
  10 dilin hepsi `json.load` ile geçerli JSON olarak doğrulandı. `i18n.init('.')` + her dil için
  `i18n.set_language(code)` sonrası `i18n.missing_keys()` boş döndü (yeni anahtarların hepsi gerçekten
  okunabiliyor, sessizce anahtar adına düşmüyor). Başlık-satırı algılama mantığı (`satır == satır.upper()`)
  Türkçe/Rusça/Almanca/Fransızca başlıklar için de ayrı ayrı test edildi. **Bu konteynerde `tkinter` modülü
  kurulu değil** (`ModuleNotFoundError`) — gerçek pencerenin görsel render'ı, kenar çubuğunun düz
  hizalandığı ve "Hakkında" sekmesinin okunur göründüğü yalnızca statik olarak (kod akışı + palet/çeviri
  anahtarları) doğrulanabildi; kullanıcının Windows'ta çalıştırıp görsel olarak teyit etmesi gerekiyor.
- **Bilerek dışarıda bırakılan**: Space Grotesk marka fontu (web fontu, Windows sistem fontu değil —
  mevcut "Segoe UI"/"Segoe UI Semibold" korundu); "◆ ISAC" kenar-çubuğu etiketinin değiştirilmesi/
  kaldırılması (yukarıda açıklandı).

## Bu depoya dair AI-destekli geliştirme oturumları (genel not)

Bu proje, farklı AI oturumlarının (bu oturum dahil) ardışık olarak çalıştığı bir geliştirme modeliyle sürdürülüyor. Her oturum kendi kapsamını `HANDOFF.md`'de bırakmalı. Bu depoya ayrıca bir "ChatGPT" oturumunun yaptığı iş (Android companion app `mobile/` + bazı güvenilirlik/tanılama işi) bu Claude oturumunda doğrulanıp `main`'e entegre edildi (9.1.5.18 merge'i).
