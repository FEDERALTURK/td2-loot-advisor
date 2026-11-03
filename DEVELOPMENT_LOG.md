# Geliştirme Günlüğü

Önemli kararların ve sürümlerin kısa, kronolojik özeti. Tam ayrıntı için `git log` ve `.github/release_notes.md`.

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
