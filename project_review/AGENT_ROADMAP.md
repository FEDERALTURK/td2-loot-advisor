# TD2 Loot Advisor — Ajan Yol Haritası

## Durum

- Android cihaz ADB'de `device` olarak bağlı.
- `td2-companion-beta.jks` cihazdaki kurulu Companion sertifikasıyla eşleşiyor.
- Flutter analyze/test başarılı.
- İzole OCR, canlı çeviri ve overlay testleri başarılı.
- `tests/test_knowledge.py` canlı veri fixture ayrışması nedeniyle kırmızıydı; sentetik fixture ile düzeltildi.
- Gerçek APK güncelleme, FCM teslimatı, gerçek oyun overlay'i ve Windows installer testi tamamlanmadı.
- Public release, tag, APK veya installer yayınlanmadı.

## Ajan sahiplikleri

### Android release ve FCM

Sahiplik: `mobile/**`, `.github/workflows/build-mobile.yml`

Görevler: signing şemasını tekleştirmek, signed APK üretmek, fingerprint eşleştirmek, verileri koruyarak cihaz güncellemesi yapmak, FileProvider ve FCM teslimatını doğrulamak.

### OCR ve overlay kalibrasyonu

Sahiplik: `livetranslate.py`, `ocr_backend.py`, `overlay.py`, `translation_probe.py` ve ilgili testler.

Görevler: gerçek oyun kanıtları, OCR/capture/DPI kalibrasyonu, `canvas_items`, siyah/boş overlay kök nedeni ve click-through doğrulaması.

### CI, EXE ve installer

Sahiplik: `.github/workflows/build-installer.yml`, `TD2LootAdvisor.spec`, `scripts/` ve CI/packaging testleri.

Görevler: kırmızı testleri düzeltmek, Python sürümlerini ayırmak, PyInstaller smoke testini ve Windows installer testini çalıştırmak.

## Öncelikler

### P0

- Kullanıcı/runtime dosyalarını koru.
- Secret eksikliğinde debug signing fallback'ini engelle.
- Yanlış keystore ile release üretimini durdur.

### P1

- Signed APK'yı gerçek Android cihazda güncelle.
- FileProvider ve veri korunumu testini tamamla.
- FCM push teslimatını doğrula.
- Signing secret şemasını tekleştir.
- Signed release manifestini yeni gereksinim olarak ele al.

### P2

- HTTP Range ile indirme devam ettirme.
- FCM geçici hata retry davranışı.
- GitHub host/repository/path doğrulaması.
- Gerçek oyun overlay kalibrasyonu.
- EXE ve installer test matrisi.

### P3

- Devir belgelerini güncelle.
- Test envanterini genişlet.
- CI timeout ve flaky test raporlamasını iyileştir.

## Sıralı kabul kapıları

1. `test_knowledge.py` ve ilgili Python testleri geçer.
2. Signing secret şeması kararlaştırılır.
3. Signed APK fingerprint'i cihazla eşleşir.
4. Verileri silmeden APK güncellemesi tamamlanır.
5. FileProvider kurulumu tamamlanır.
6. FCM açık/arka plan/kapalı/telefon kilitli senaryoları doğrulanır.
7. Gerçek oyun overlay kanıtları toplanır.
8. EXE ve installer smoke testleri tamamlanır.
9. Kullanıcıya sonuç ve kalan riskler raporlanır.
10. Yayın kararı için kullanıcı onayı beklenir.

## Yayın sınırı

Kullanıcı açıkça şu soruya `Evet` demeden yayın yapılmaz:

```text
Yeni Güncellemeyi Yayınlamak İster misiniz? (vX.Y.Z) — Evet / Hayır
```
