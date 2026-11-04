# Üçüncü taraf oyun verisi — lisans notu

Bu dosya, `meta/game_data.json` ve `meta/sources/mxswat/*.csv` içindeki oyun verisinin lisans durumunu ve bunun ücretsiz/premium özellik ayrımıyla ilişkisini açıklar. Amaç, belirsizliği gizlemek değil, açıkça kayıt altına almaktır.

## Kaynaklar
- **The Division Wiki** (thedivision.fandom.com) — CC BY-SA.
- **mx-division-builds** (github.com/mxswat/mx-division-builds) by mxswat — **CC BY-NC-SA 4.0 (ticari olmayan kullanım, atıfla)**.

Atıf her iki README'de (EN/TR) ve üretilen Excel kütüphanesinde (`scripts/library_excel.py`) mevcut.

## Bu verinin programda nerede kullanıldığı
- `"scan"`, `"builds"` ve `"recal_advisor"` (eşya okuma, karar, build/eksik parça takibi, kalibrasyon danışmanı) — **hepsi ücretsiz** (`features.py`, 2026-11-04 itibarıyla). mx verisini doğrudan ya da dolaylı kullanan hiçbir özellik artık ücretli kapı arkasında değil.
- Diğer premium özellikler (`optimizer_all`, `stash_export`, `vendor_watch`, `companion`, `local_api`, `push_notify`, `cloud_sync`) zaten katalog verisini **yeniden paketlemiyor/satmıyor** — kullanıcının kendi envanterini, bildirimlerini veya bağlantı araçlarını konu ediyor.

## Değerlendirme (hukuki görüş değildir)
CC BY-NC-SA 4.0'daki "ticari olmayan kullanım" şartı, bu veriyi **doğrudan satan/erişimini ücretlendiren** bir kullanım için açıkça ihlal sayılır. Önceden `recal_advisor`'ın bu veriyi **dolaylı olarak** premium bir özelliğin çıktısına girdi yapması gri bir alandı — bu konuda kesin bir hukuki görüş veremem (ben avukat değilim), ama en temiz çözüm riski tamamen ortadan kaldırmaktı.

## Alınan karar (2026-11-04)
`recal_advisor` `features.py`'de `"premium"`'dan `"free"`'ye çevrildi (kullanıcı kararı). Artık mx verisine dolaylı dayanan hiçbir özellik parayla ilişkilendirilmiyor — "ticari olmayan kullanım" şartıyla ilgili gri alan pratikte kapandı. İlgili testler (`tests/test_core.py`, `tests/test_account.py`, `tests/ui_account_test.py`) güncellendi.

**Durum:** Soru yine de nezaketen mxswat'a GitHub Issues üzerinden sorulmuştu — [mxswat/mx-division-builds#153](https://github.com/mxswat/mx-division-builds/issues/153) (2026-11-03). Issue hâlâ açık, yanıt gelmedi; ama artık bir karara/engele bağlı değil, sadece bilgi amaçlı takip ediliyor.
