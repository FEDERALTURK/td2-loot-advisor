# Geliştirme Günlüğü

Önemli kararların ve sürümlerin kısa, kronolojik özeti. Tam ayrıntı için `git log` ve `.github/release_notes.md`.

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

## Bu depoya dair AI-destekli geliştirme oturumları (genel not)

Bu proje, farklı AI oturumlarının (bu oturum dahil) ardışık olarak çalıştığı bir geliştirme modeliyle sürdürülüyor. Her oturum kendi kapsamını `HANDOFF.md`'de bırakmalı. Bu depoya ayrıca bir "ChatGPT" oturumunun yaptığı iş (Android companion app `mobile/` + bazı güvenilirlik/tanılama işi) bu Claude oturumunda doğrulanıp `main`'e entegre edildi (9.1.5.18 merge'i).
