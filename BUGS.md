# Bilinen Sorunlar ve Açık Konular

## Çözülmüş (9.1.5.19)

- ✅ **Çökme**: Ansiklopedi/kaynak ekranlarındaki "Kaynağı aç"/"Aç" düğmeleri `webbrowser` modülü yalnızca başka bir fonksiyonda yerel import edildiği için `NameError` veriyordu. Modül artık dosya başında global import. (`app.py`, 4 düğme konumu: ~2925, 2934, 2961, 7037)
- ✅ **Çökme**: Tanılama Merkezi hata bildirimi ve Sürüm Geçmişi yükleme hatası, `except ... as X` değişkenini gecikmeli `root.after` lambda'sında kullandığı için ikinci bir `NameError` üretiyordu (CPython except-bloğu bitince değişkeni otomatik siler). Değer şimdi ayrı bir yerel değişkende saklanıyor.
- ✅ 23 kullanılmayan import + ~10 ölü değişken (ruff/pyflakes taraması, davranış değişikliği yok, tam test paketiyle doğrulandı).
- ✅ `main`/`master` dal ayrışması (son yayın kodu `master`'daydı, `main` eskiydi) — `git merge --no-ff` ile birleştirildi.

## Açık / kullanıcı işlemi gerektiren

- ✅ **Yarım kalan ansiklopedi açıklamaları — kök neden bulundu ve düzeltildi (2026-11-04).** İlk bakışta 13 giriş
  `…` ile bitiyor gibi görünse de, gerçek kapsam **30 isimdi**: `meta/sources/wiki_exotics.json`'daki 18 egzotik
  kaydı tam olarak **400 karakterde**, `meta/sources/wiki_talent_desc.json`'daki 12 talent kaydı ise **~190
  karakterde** kelime/cümle ortasında kesilmişti (muhtemelen eski bir wiki-kazıma betiğinin sabit karakter
  limitinden). 17 kayıtta kesilen İngilizce metin, makine çevirisi tarafından gramer açısından tam görünen ama
  içerik olarak eksik cümlelere çevrildiği için `…` arama yöntemi bunları yakalamıyordu. `knowledge.py`'daki
  önceliklendirme (`wiki_exotics.json`/`wiki_talent_desc.json` > `game_data.json`) kesik metni, `game_data.json`'da
  zaten var olan tam/doğru metnin önüne geçiriyordu.
  - Düzeltme: `wiki_exotics.json`'daki 18 kaydın `desc` alanı `game_data.json`'daki tam metinle değiştirildi;
    `wiki_talent_desc.json`'daki 12 kesik kayıt tamamen silindi (kod otomatik olarak `game_data.json`'daki tam
    metne düşüyor). `meta/descriptions_i18n.json`'da bu 30 ismin 9 dildeki (tr de fr es it pt ru pl nl) çevirileri
    tam İngilizce kaynağa göre yeniden yazıldı.
  - Boyut sınırı: düzeltme `descriptions_i18n.json`'ı 512 KiB sınırının (test eşiği 510.000 bayt) üzerine
    çıkardı. Proje kuralına uygun olarak en büyük 3 kayıt (`Disruptor Rounds`, `Bluescreen`, `The Ravenous`)
    `meta/descriptions_i18n_2.json`'a taşındı (bkz. `meta/UPDATER.md`). `tests/test_knowledge.py` tam paket PASS.
- ✅ **`Workers Builds: td2-stats` PR'da başarısız oluyordu — kök neden bulundu ve düzeltildi (2026-11-04).** `server/` dizininde hiç `package.json` yoktu. Cloudflare Workers Builds, `npx wrangler deploy`'u çalıştırmadan önce paket yöneticisini tespit edip kurulum adımı yapıyor ve Wrangler sürümünü `package.json`'dan alıyor (resmi doküman: "Workers Builds will use the Wrangler version set in your package.json"). `package.json` yokken bu adım başarısız oluyordu; yerelde ise `npx wrangler deploy` her seferinde Wrangler'ı ağdan taze indirdiği için (npx'in kendi davranışı) sorun görünmüyordu — bu yüzden "yerelde çalışıyor, CI'da çalışmıyor" farkı oluşuyordu. `server/package.json` (Wrangler `^4.0.0` devDependency) ve `server/package-lock.json` eklendi; `npx wrangler deploy --dry-run` yeniden doğrulandı (başarılı, aynı binding listesi). `node_modules/` zaten `.gitignore`'da. **GitHub'da doğrulandı (2026-11-04): "Workers Builds: td2-stats" check'i artık `success` dönüyor** (önceki commit'lerde `failure`'dı).

1. ✅ **`master` dalı silindi (2026-11-04, kullanıcı tarafından).** `git ls-remote`/GitHub API ile doğrulandı. Kalan dallar: `main` (tek doğru kaynak), `archive/master-superseded-2026-11-03` (eski yedek, isteğe bağlı temizlenebilir), `deploy/worker-bundle-temp` (geçici, "will be removed" olarak işaretli), `claude/descriptions-second-shard`.
2. ✅ **mx-division-builds (CC BY-NC-SA 4.0) lisans gri alanı — çözüldü (2026-11-04, kullanıcı kararı).** `recal_advisor` `premium`'dan `free`'ye çevrildi (`features.py`); mx verisine dolaylı dayanan özellik artık parayla ilişkili değil. `LICENSE_NOTES.md` güncellendi. `tests/test_core.py`, `tests/test_account.py`, `tests/ui_account_test.py` artık örnek premium özellik olarak `optimizer_all` kullanıyor (`test_core.py` yerel olarak çalıştırılıp PASS doğrulandı). mxswat'a sorulan [issue #153](https://github.com/mxswat/mx-division-builds/issues/153) (2026-11-03) nezaketen açık bırakıldı, yanıt beklemeye artık bağlı değil.
3. ✅ **Tanıtım videoları yayınlandı (2026-11-04, kullanıcı tarafından).** `td2_promo_en_1080p.mp4` ve `td2_promo_tr_1080p.mp4` v9.1.5.20 (latest) GitHub Release notlarına eklendi, GitHub API ile doğrulandı. Dikey (Shorts/Reels) versiyonları ve YouTube paylaşımı hâlâ isteğe bağlı — kullanıcı kararı.
4. **SignPath Foundation (ücretsiz OSS kod imzalama) başvurusu reddedildi (2026-11-03).** Gerekçe: proje henüz
   yeterli kamuya görünürlük sinyaline (GitHub star/fork/katkıcı, dış makale/referans, kurumsal destek, sürekli
   aktivite) sahip değil — kod/proje kalitesiyle ilgisiz, tekrar başvuru açıkça teşvik ediliyor. Ayrıntı ve
   alternatifler için `ROADMAP.md` → "Diğer açık kalemler" bölümüne bakın. Karar kullanıcıya ait: (a) görünürlük
   biriktirip yeniden başvurmak, (b) ücretli bir imzalama sağlayıcısına geçmek, (c) şimdilik imzasız devam etmek.

## Doğrulanmamış / gerçek Windows'ta teyit gerekli

5. ✅ **Gerçek Windows render testi yapıldı (2026-11-04).** Bağlı Windows bilgisayarında (v9.1.5.20) computer-use ile üç senaryo manuel test edildi: Ansiklopedi "Wiki'de aç" düğmesi, Ayarlar → Sürüm geçmişi, Tanılama Merkezi → "Sorunları tara" (hata bildirimi yolu). Üçünde de çökme/hata diyaloğu oluşmadı — 9.1.5.19'daki iki `NameError` düzeltmesi gerçek Windows + DWM render yolunda doğrulandı. Ayrıntı: `DEVELOPMENT_LOG.md`.
   - ✅ **Güncelleme (2026-11-04, v9.1.5.23): o testte not edilen "içerik listesi boş kaldı" gözleminin kök nedeni bulundu ve düzeltildi.** Sebep bir yükleme/ağ sorunu değildi: `show_version_history` içindeki Listbox/Text arka plan rengi `PAL["panel"]` adlı **var olmayan bir palet anahtarını** okuyordu (doğru anahtar `PAL["surface"]`; `ui_theme.PALETTES`'te `panel` diye bir anahtar hiç yok). Bu, pencere inşa edilirken `KeyError` fırlatıyordu; uygulamada `Tk.report_callback_exception` override'ı olmadığı ve build `--noconsole` olduğu için hata hem kullanıcıya hem log dosyasına hiç görünmüyordu — buton tıklanınca sessizce hiçbir şey olmuyordu (kullanıcı 2026-11-04'te bunu birebir "liste yok ve bakabileceğim bir tuş da yok" olarak bildirdi). `app.py`'daki 2 satır (`PAL["panel"]` → `PAL["surface"]`) düzeltildi; dosyadaki tüm `PAL["…"]` kullanımları yeniden tarandı, başka geçersiz anahtar kalmadığı doğrulandı.
6. **Mobil companion (`mobile/`, Flutter) bu oturumda build/test edilmedi.** Sadece dosya varlığı ve sır taraması yapıldı.
7. **`server/test_*.mjs` (Node.js sunucu testleri) bu oturumda çalıştırılmadı.**

## Bilinen test kapsamı boşlukları

- `webbrowser`/except-closure hata sınıfı için statik AST taraması var (`tests/test_regression_crash_patterns.py`), ama gerçek Tk buton `invoke()` ile uçtan uca test yok.
