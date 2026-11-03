# Üçüncü taraf oyun verisi — lisans notu

Bu dosya, `meta/game_data.json` ve `meta/sources/mxswat/*.csv` içindeki oyun verisinin lisans durumunu ve bunun ücretsiz/premium özellik ayrımıyla ilişkisini açıklar. Amaç, belirsizliği gizlemek değil, açıkça kayıt altına almaktır.

## Kaynaklar
- **The Division Wiki** (thedivision.fandom.com) — CC BY-SA.
- **mx-division-builds** (github.com/mxswat/mx-division-builds) by mxswat — **CC BY-NC-SA 4.0 (ticari olmayan kullanım, atıfla)**.

Atıf her iki README'de (EN/TR) ve üretilen Excel kütüphanesinde (`scripts/library_excel.py`) mevcut.

## Bu verinin programda nerede kullanıldığı
- `"scan"` ve `"builds"` (eşya okuma, karar, build/eksik parça takibi) — **ücretsiz** (`features.py`). Bu, mx verisinin asıl kullanıldığı yer.
- `"recal_advisor"` (kalibrasyon danışmanı, `stash.recal_advice()`) — **premium**. Bu fonksiyon, hangi attribute'un hangi eşyadan geldiğine dair önerilerinde oyun kataloğunu (dolayısıyla kısmen mx verisini) kullanabiliyor.
- Diğer premium özellikler (`optimizer_all`, `stash_export`, `vendor_watch`, `companion`, `local_api`, `push_notify`, `cloud_sync`) katalog verisini **yeniden paketlemiyor/satmıyor** — kullanıcının kendi envanterini, bildirimlerini veya bağlantı araçlarını konu ediyor.

## Değerlendirme (hukuki görüş değildir)
CC BY-NC-SA 4.0'daki "ticari olmayan kullanım" şartı, bu veriyi **doğrudan satan/erişimini ücretlendiren** bir kullanım için açıkça ihlal sayılır — program bunu yapmıyor (katalog erişimi `"scan"`/`"builds"` ile her zaman ücretsiz). Ancak `recal_advisor`'ın bu veriyi **dolaylı olarak** bir ücretli özelliğin çıktısına girdi yapması, "ticari olmayan" şartının ne kadar geniş yorumlanacağına bağlı gri bir alandır — bu konuda kesin bir hukuki görüş veremem (ben avukat değilim).

## Önerilen adım
En sağlam çözüm, mxswat'a (GitHub üzerinden, repo'nun Issues'ı veya profili) kısaca ulaşıp bu küçük, açık kaynaklı, kâr amacı gütmeyen projede verinin bu şekilde (bir kısmı ücretsiz katalog, bir kısmı dolaylı olarak premium bir öneri özelliğinde) kullanılmasının uygun olup olmadığını sormak ve yanıtı burada (bu dosyada) kayıt altına almaktır. Yanıt olumsuz veya belirsiz kalırsa, en güvenli adım `recal_advisor`'ı yalnızca kullanıcının kendi taranmış/girilmiş eşya verisiyle çalışacak şekilde sınırlamak (mx kaynaklı katalog alanlarını bu öneri motorundan çıkarmak) olur.

**Durum (2026-11-03):** Soru mxswat'a GitHub Issues üzerinden soruldu — [mxswat/mx-division-builds#153](https://github.com/mxswat/mx-division-builds/issues/153). Yanıt bekleniyor; gelince bu bölüm güncellenecek.
