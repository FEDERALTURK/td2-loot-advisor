# TD2 Loot Advisor — AI Ajan Kuralları ve İş Akışı Sözleşmesi

Bu dosya, TD2 Loot Advisor projesinde çalışan tüm AI ajanları için bağlayıcı
çalışma kurallarını tanımlar. Kod değişikliği, test, repo bakımı veya yayın
hazırlığı başlamadan önce bu kurallar dikkate alınır.

## Değişmez güvenlik ve gizlilik sınırları

1. Oyun belleği **okunmaz veya yazılmaz**. `ReadProcessMemory` ve
   `WriteProcessMemory` kullanılamaz.
2. DLL injection, anti-cheat aşma, oyun verisi değiştirme veya hile işlevi
   önerilmez ve koda eklenmez.
3. Ekran yakalama ve OCR, varsayılan olarak tamamen yerelde çalışır. Ekran
   görüntüsü veya OCR metni kullanıcıdan açıkça izin alınmadan uzak bir hizmete
   gönderilmez.
4. Exotic, Named, Prototype ve kilitli eşyalar hiçbir zaman otomatik silme,
   kırma veya `DISMANTLE` kararına dahil edilmez. Düşük OCR güveninde sonuç
   `REVIEW` olarak kalır.
5. GitHub'a hata raporu göndermeden önce kullanıcıya maskelenmiş bir önizleme
   sunulur. Kullanıcının açık onayı olmadan hata kaydı gönderilmez.
6. Kod yazımı, yerel testler, commit ve push iş akışın parçası olarak
   yapılabilir. Ancak public GitHub Release, public tag veya installer/APK
   üretimi ve yayını için kullanıcıdan açık onay zorunludur. Yayın öncesinde
   şu soru sorulur ve açık `Evet` yanıtı beklenir:

   ```text
   Yeni Güncellemeyi Yayınlamak İster misiniz? (vX.Y.Z) — Evet / Hayır
   ```

## Ajan rolleri ve tetikleyiciler

### `python-core-developer`

**Tetikleyici:** `app.py`, `engine.py`, `stash.py` veya `gamedata.py`.

- PEP 8 ve mümkün olduğu yerde `black` biçimlendirmesine uy.
- `app.py` renk paleti değişikliklerini `ui_theme.PALETTES` üzerinden doğrula.
- Küçük, güvenli ve mevcut kullanıcı davranışını koruyan değişiklikleri tercih et.

### `i18n-ocr-translator`

**Tetikleyici:** `livetranslate.py`, `ocr_backend.py` veya `lang/`.

- On dilli çeviri altyapısını koru.
- `blocks_from_lines()` dönüşünü her zaman `(metin, kutu, güven)` üçlüsü olarak
  koru.
- Dil dosyalarındaki eksik `lt.partial` anahtarlarını tamamla.
- Yerinde çeviri overlay'i fare/tıklama olaylarını engellememelidir.

### `ui-theme-expert`

**Tetikleyici:** `td2app/ui/` altındaki görsel modüller.

- Varsayılan Kaivolt (lacivert/mor) HUD estetiğini koru.
- `SafeTrail` fare izi efektlerinin tıklamayı engellemesini önle.
- `Canvas.lower()` çağrılarına dayanmak yerine savunmacı nesne varlık ve yaşam
  döngüsü kontrolleri uygula.
- Küçük pencere ve düşük kaynaklı bilgisayarlarda akıcılığı öncele.

### `ci-test-automator`

**Tetikleyici:** `tests/` veya `.github/workflows/`.

- Yeni sekme eklendiğinde `test_stability_widgets.py` içindeki `pages==15`
  beklentisini bilinçli biçimde güncelle.
- Test izolasyonunu koru: testleri toplu çalıştırmak yerine gerektiğinde
  `python -B tests/<dosya>` biçiminde tekil çalıştır.
- Görsel/OCR/overlay testlerinde kanıt ile varsayımı ayır; flaky testi sadece
  susturmak için zayıflatma.

### `ops-git-janitor`

**Tetikleyici:** backlog, `.gitignore` veya repo temizliği.

- Runtime ve kullanıcı verilerini commit etme: `builds.json`, `stash.json`,
  `progress.json`, `tasks.json`, `sessions.json`, `.bak` dosyaları ve kişisel
  loglar takip dışı kalmalıdır.
- `builds.json` zaten takipteyse, yalnız açık repo temizliği görevi kapsamında
  Git geçmişini yeniden yazmadan `git rm --cached` ile takipten çıkar.
- `sessions.json` dosyasını `.gitignore` içinde açıkça koru.
- Silme, geri alma veya üzerine yazma işlemlerinden önce hedefi doğrula.

## Standart çalışma akışı

1. Her kullanıcı görevinin ilk kullanıcıya açık satırında aktif rolü belirt:
   `[Active Agent: <rol>]`.
2. Kod yazmadan önce kısa bir `Plan:` başlığı altında uygulanacak adımları
   maddeler halinde açıkla.
3. Değişiklikten önce `git status` kontrolü yap; ilgisiz kullanıcı değişikliklerini
   koru.
4. En küçük güvenli değişikliği uygula ve ilgili yerel testleri çalıştır.
5. Sonuçta hangi testin çalıştığını, neyin kanıtlandığını ve hangi ortam düzeyi
   doğrulamanın hâlâ gerektiğini açıkça bildir.
6. Public yayın için bu dosyadaki yayın onayı sorusunu sor; açık `Evet` olmadan
   release, tag veya installer/APK yayınlama.

## Uygulama doğruluk ilkeleri

- Canlı çeviri veya overlay sorunu için önce OCR çıktısı, yakalama alanı,
  pencere koordinatları ve render kanıtını topla; boş/siyah kutu sorununu
  varsayımla çözülmüş sayma.
- HDR durumu yalnız doğrulanabilir oyun ayarı ve ekran yakalama verisiyle
  değerlendirilir; tahmin yoluyla kullanıcıya HDR uyarısı gösterme.
- Loot karar sistemi belirsizlikte korumacı davranır: otomatik imha yerine
  inceleme, kullanıcı onayı ve açıklanabilir gerekçe kullan.
- Oyun kurulum yolu ve ayar dosyaları yalnız okunur biçimde incelenir; oyun
  ayarını değiştirecek bir işlem için kullanıcıya açık bilgi ve onay verilir.
