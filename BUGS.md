# Bilinen Sorunlar ve Açık Konular

## Çözülmüş (9.1.5.19)

- ✅ **Çökme**: Ansiklopedi/kaynak ekranlarındaki "Kaynağı aç"/"Aç" düğmeleri `webbrowser` modülü yalnızca başka bir fonksiyonda yerel import edildiği için `NameError` veriyordu. Modül artık dosya başında global import. (`app.py`, 4 düğme konumu: ~2925, 2934, 2961, 7037)
- ✅ **Çökme**: Tanılama Merkezi hata bildirimi ve Sürüm Geçmişi yükleme hatası, `except ... as X` değişkenini gecikmeli `root.after` lambda'sında kullandığı için ikinci bir `NameError` üretiyordu (CPython except-bloğu bitince değişkeni otomatik siler). Değer şimdi ayrı bir yerel değişkende saklanıyor.
- ✅ 23 kullanılmayan import + ~10 ölü değişken (ruff/pyflakes taraması, davranış değişikliği yok, tam test paketiyle doğrulandı).
- ✅ `main`/`master` dal ayrışması (son yayın kodu `master`'daydı, `main` eskiydi) — `git merge --no-ff` ile birleştirildi.

## Açık / kullanıcı işlemi gerektiren

- **Yarım kalan ansiklopedi açıklamaları.** 13 girişin çevirisi `…` ile bitiyor (ör. Eagle Bearer, NinjaBike Messenger Bag). Bakılan örneklerde İngilizce kaynak metin de yarım; önce kaynak metin tamamlanmalı.
- **`Workers Builds: td2-stats` PR dalında anında başarısız oluyor** (PR #2, derleme çalışmadan). Yerel `wrangler deploy --dry-run` başarılı; kök neden doğrulanmadı, Cloudflare panelindeki dal yapı ayarı kontrol edilmeli.

1. ✅ **`master` dalı silindi (2026-11-04, kullanıcı tarafından).** `git ls-remote`/GitHub API ile doğrulandı. Kalan dallar: `main` (tek doğru kaynak), `archive/master-superseded-2026-11-03` (eski yedek, isteğe bağlı temizlenebilir), `deploy/worker-bundle-temp` (geçici, "will be removed" olarak işaretli), `claude/descriptions-second-shard`.
2. ✅ **mx-division-builds (CC BY-NC-SA 4.0) lisans gri alanı — çözüldü (2026-11-04, kullanıcı kararı).** `recal_advisor` `premium`'dan `free`'ye çevrildi (`features.py`); mx verisine dolaylı dayanan özellik artık parayla ilişkili değil. `LICENSE_NOTES.md` güncellendi. `tests/test_core.py`, `tests/test_account.py`, `tests/ui_account_test.py` artık örnek premium özellik olarak `optimizer_all` kullanıyor (`test_core.py` yerel olarak çalıştırılıp PASS doğrulandı). mxswat'a sorulan [issue #153](https://github.com/mxswat/mx-division-builds/issues/153) (2026-11-03) nezaketen açık bırakıldı, yanıt beklemeye artık bağlı değil.
3. ✅ **Tanıtım videoları yayınlandı (2026-11-04, kullanıcı tarafından).** `td2_promo_en_1080p.mp4` ve `td2_promo_tr_1080p.mp4` v9.1.5.20 (latest) GitHub Release notlarına eklendi, GitHub API ile doğrulandı. Dikey (Shorts/Reels) versiyonları ve YouTube paylaşımı hâlâ isteğe bağlı — kullanıcı kararı.
4. **SignPath Foundation (ücretsiz OSS kod imzalama) başvurusu reddedildi (2026-11-03).** Gerekçe: proje henüz
   yeterli kamuya görünürlük sinyaline (GitHub star/fork/katkıcı, dış makale/referans, kurumsal destek, sürekli
   aktivite) sahip değil — kod/proje kalitesiyle ilgisiz, tekrar başvuru açıkça teşvik ediliyor. Ayrıntı ve
   alternatifler için `ROADMAP.md` → "Diğer açık kalemler" bölümüne bakın. Karar kullanıcıya ait: (a) görünürlük
   biriktirip yeniden başvurmak, (b) ücretli bir imzalama sağlayıcısına geçmek, (c) şimdilik imzasız devam etmek.

## Doğrulanmamış / gerçek Windows'ta teyit gerekli

5. ✅ **Gerçek Windows render testi yapıldı (2026-11-04).** Bağlı Windows bilgisayarında (v9.1.5.20) computer-use ile üç senaryo manuel test edildi: Ansiklopedi "Wiki'de aç" düğmesi, Ayarlar → Sürüm geçmişi, Tanılama Merkezi → "Sorunları tara" (hata bildirimi yolu). Üçünde de çökme/hata diyaloğu oluşmadı — 9.1.5.19'daki iki `NameError` düzeltmesi gerçek Windows + DWM render yolunda doğrulandı. Ayrıntı: `DEVELOPMENT_LOG.md`. Küçük, çökmeyle ilgisiz bir gözlem: Sürüm geçmişi penceresinin içerik listesi boş kaldı — kök nedeni araştırılmadı, ayrı bir görüntü/veri-yükleme konusu olabilir, izlemeye değer ama acil değil.
6. **Mobil companion (`mobile/`, Flutter) bu oturumda build/test edilmedi.** Sadece dosya varlığı ve sır taraması yapıldı.
7. **`server/test_*.mjs` (Node.js sunucu testleri) bu oturumda çalıştırılmadı.**

## Bilinen test kapsamı boşlukları

- `webbrowser`/except-closure hata sınıfı için statik AST taraması var (`tests/test_regression_crash_patterns.py`), ama gerçek Tk buton `invoke()` ile uçtan uca test yok.
