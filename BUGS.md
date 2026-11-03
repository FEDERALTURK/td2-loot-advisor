# Bilinen Sorunlar ve Açık Konular

## Çözülmüş (9.1.5.19)

- ✅ **Çökme**: Ansiklopedi/kaynak ekranlarındaki "Kaynağı aç"/"Aç" düğmeleri `webbrowser` modülü yalnızca başka bir fonksiyonda yerel import edildiği için `NameError` veriyordu. Modül artık dosya başında global import. (`app.py`, 4 düğme konumu: ~2925, 2934, 2961, 7037)
- ✅ **Çökme**: Tanılama Merkezi hata bildirimi ve Sürüm Geçmişi yükleme hatası, `except ... as X` değişkenini gecikmeli `root.after` lambda'sında kullandığı için ikinci bir `NameError` üretiyordu (CPython except-bloğu bitince değişkeni otomatik siler). Değer şimdi ayrı bir yerel değişkende saklanıyor.
- ✅ 23 kullanılmayan import + ~10 ölü değişken (ruff/pyflakes taraması, davranış değişikliği yok, tam test paketiyle doğrulandı).
- ✅ `main`/`master` dal ayrışması (son yayın kodu `master`'daydı, `main` eskiydi) — `git merge --no-ff` ile birleştirildi.

## Açık / kullanıcı işlemi gerektiren

1. **`master` dalı silinmedi.** İçeriği tamamen `main`'e merge edildi (kayıpsız), ama bu AI oturumunun ortam politikası `git push --delete` ve GitHub API `DELETE /git/refs` çağrılarını "bu proxy üzerinden yazma erişimine izin verilmiyor" diyerek engelliyor — kullanıcı onayıyla bile aşılamayan sabit bir platform kısıtlaması. **Kullanıcı kendisi silmeli**: GitHub → Settings → Branches, veya yerel `git push origin --delete master`, veya Actions sekmesinden `retire-releases.yml` workflow'unu `branches: master` ile manuel tetikleyerek.
2. **mx-division-builds (CC BY-NC-SA 4.0) lisans gri alanı.** `recal_advisor` premium özelliği bu ticari-olmayan veriye dolaylı dokunuyor olabilir. `LICENSE_NOTES.md`'de belgelendi; mxswat'a soru [issue #153](https://github.com/mxswat/mx-division-builds/issues/153) ile soruldu (2026-11-03), yanıt bekleniyor (bkz. HANDOFF.md).
3. **Tanıtım videoları yayınlanmadı.** Private `td2-loot-advisor-reports` reposundaki `promo` dalı kendi `main`'ine merge edilmemiş; README/Release/YouTube'a koyma kararı kullanıcı onayı bekliyor.
4. **SignPath Foundation (ücretsiz OSS kod imzalama) başvurusu reddedildi (2026-11-03).** Gerekçe: proje henüz
   yeterli kamuya görünürlük sinyaline (GitHub star/fork/katkıcı, dış makale/referans, kurumsal destek, sürekli
   aktivite) sahip değil — kod/proje kalitesiyle ilgisiz, tekrar başvuru açıkça teşvik ediliyor. Ayrıntı ve
   alternatifler için `ROADMAP.md` → "Diğer açık kalemler" bölümüne bakın. Karar kullanıcıya ait: (a) görünürlük
   biriktirip yeniden başvurmak, (b) ücretli bir imzalama sağlayıcısına geçmek, (c) şimdilik imzasız devam etmek.

## Doğrulanmamış / gerçek Windows'ta teyit gerekli

5. **Gerçek Windows render testi henüz yapılmadı.** Bu düzeltmeler Linux + Xvfb'de doğrulandı; gerçek Windows + DWM/DX12 render yolu geçmişte (9.1.5.10–9.1.5.17) birkaç kez Linux testinin yakalayamadığı görsel hatalar çıkarmıştı. Bağlı Windows bilgisayarı üzerinden gerçek doğrulama ayrıca planlandı (bkz. HANDOFF.md "Sıradaki adım").
6. **Mobil companion (`mobile/`, Flutter) bu oturumda build/test edilmedi.** Sadece dosya varlığı ve sır taraması yapıldı.
7. **`server/test_*.mjs` (Node.js sunucu testleri) bu oturumda çalıştırılmadı.**

## Bilinen test kapsamı boşlukları

- `webbrowser`/except-closure hata sınıfı için statik AST taraması var (`tests/test_regression_crash_patterns.py`), ama gerçek Tk buton `invoke()` ile uçtan uca test yok.
