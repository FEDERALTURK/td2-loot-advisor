# TD2 Loot Advisor — Claude Code → Codex Devir Teslimi

**Devir tarihi:** 2026-11-14  
**Çalışma dizini:** `C:\Users\PC\Desktop\Thedivision2program`  
**Devir kapsamı:** Yerel kaynak, Android Companion, CI signing hazırlığı, test durumu ve yayın sınırları

## 1. Genel durum

TD2 Loot Advisor; Windows üzerinde çalışan, The Division 2 ekran görüntüsünü yerel OCR ile okuyup eşya/build/loot kararları üreten, canlı çeviri overlay'i ve Android Companion bileşeni bulunan çok parçalı bir projedir.

Bu devir teslimi gerçek çalışma ağacı, yerel test çıktıları ve mevcut proje inceleme belgeleri esas alınarak hazırlanmıştır. Belgelerdeki her özellik kaynak kodda mevcut kabul edilmemiş; mevcut, kısmi, test edilmedi veya bloke olarak ayrılmıştır.

**Mevcut yayın durumu:** Yerel çalışma ve test aşaması. Bu devir sırasında GitHub push, public tag, GitHub Release, APK paylaşımı veya Windows installer yayını yapılmamıştır.

## 2. Git ve çalışma ağacı

Son bilinen commit:

```text
6fea365 fix: restrict companion installer paths
```

Çalışma ağacında kullanıcı/runtime dosyaları bulunuyor ve korunuyor:

```text
builds.json
18_pull_and_recheck.bat
19_cleanup.bat
Claude outputs/
flutter_recheck_log.txt
project_review/
scripts/build_signed_companion.ps1
tasks/
td2-companion-beta.jks
web_deploy/
```

Bu dosyalar devir sırasında silinmemeli, geri alınmamalı veya public commit'e eklenmemelidir. `td2-companion-beta.jks` özel signing anahtarıdır; içeriği veya parolası rapora yazılmaz.

## 3. Ortam

Son doğrulanan sürümler:

```text
Python 3.15.1
Node.js v24.22.1
npm 12.2.2
Flutter 3.47.8 stable
Dart 3.13.7
```

Fiziksel Android cihaz:

```text
ADB: AGCVVB5C01002525    device
Model: MTN-NX1M
Android: 16
```

## 4. Ana bileşenler

### Windows uygulaması

- `app.py`: Tkinter ana uygulaması, sekmeler, ayarlar ve koordinasyon. Büyük bir `App` sınıfı içerir.
- `capture.py`: MSS tabanlı ekran yakalama.
- `display.py`, `syncer.py`: pencere, DPI, çözünürlük ve OCR ölçümleri.
- `ocr_backend.py`, `winocr.py`: OCR motorları ve OCR kutuları.
- `gamedata.py`: eşya, set, marka, attribute ve talent eşleştirmesi.
- `engine.py`: skor, build koşulu ve loot kararı.
- `stash.py`: sandık, kopya, koruma ve optimizasyon işlemleri.
- `livetranslate.py`: yerel/AI çeviri ve çeviri önbelleği.
- `overlay.py`: OCR kutularına göre çeviri yerleştirme.
- `gameinfo.py`, `screenstate.py`, `service.py`: oyun penceresi ve tarama durumu.
- `localapi.py`, `companion.py`: token'lı yerel API, OBS/Stream Deck ve Companion bağlantısı.
- `safeio.py`: atomik JSON yazma, yedek ve Windows gizli ayarları.
- `updater.py`, `updates.py`: kaynak/EXE güncelleme akışı.

### Android Companion

- `mobile/lib/main.dart`: Companion UI ve güncelleme indirme/kurulum akışı.
- `mobile/lib/services/companion_release.dart`: release arama ve sürüm karşılaştırma.
- `mobile/lib/services/cloud_api.dart`: bulut API istekleri.
- `mobile/lib/services/cloud_link.dart`: eşleştirme, senkron ve token durumu.
- `mobile/lib/services/push_registration.dart`: Firebase/FCM izin ve token akışı.
- `mobile/android/app/src/main/kotlin/com/federalturk/td2companion/MainActivity.kt`: FileProvider ve APK installer kanalını yönetir.
- `mobile/android/app/src/main/res/xml/file_paths.xml`: FileProvider dosya kapsamı.

### Sunucu

- `server/worker.js`: Cloudflare Worker ana yönlendiricisi.
- `server/mobile.js`: Companion API ve push token işlemleri.
- `server/accounts.js`, `server/tasks.js`, `server/overview.js`: hesap, görev ve overview alanları.
- `server/schema.sql`: D1 şeması.

## 5. Gerçekten mevcut özellikler

### [Doğrulandı]

- Yerel OCR ve çeviri test altyapısı.
- OCR kutularından overlay yerleşimi.
- Android Companion sürüm kontrolü.
- APK indirme ilerlemesi ve geçici `.part` dosyası temizliği.
- FileProvider için uygulama dosya dizini sınırı.
- Companion package: `com.federalturk.td2companion`.
- Android cihazda kurulu Companion sürümü: `0.1.9`, versionCode `11`.
- `flutter analyze` başarılı.
- `flutter test` başarılı.
- `test_livetranslate.py` başarılı.
- `test_overlay.py` başarılı.
- `test_project_structure.py` başarılı.
- Release signing için `td2-companion-beta.jks` dosyası mevcut.
- Keystore alias `td2-companion-beta` ve cihazdaki kurulu uygulamayla aynı sertifikaya sahip.

### [Kısmen doğrulandı]

- Firebase/FCM kodu mevcut ancak gerçek cihaz push teslimatı henüz test edilmedi.
- APK release workflow'u mevcut ancak GitHub secret'larının repository'de tanımlı olduğu doğrulanmadı.
- SHA-256 asset üretimi mevcut; imzalı manifest doğrulaması tamamlanmadı.
- Windows installer workflow'u geniş smoke testler içeriyor; yerelde aynı installer testi tekrarlanmadı.
- Canlı çeviri ve overlay'in izole testleri başarılı; gerçek The Division 2 ekranındaki davranış test edilmedi.

### [Yalnızca tasarım veya belge aşamasında]

- Public-key imzalı release manifest sistemi.
- Gerçek üretim FCM credential ve push teslimat doğrulaması.
- Tam Python 3.13/3.14/3.15.1 paketleme matrisi.
- Gerçek oyun ekranında borderless/DPI/HDR/overlay kanıt testi.

## 6. Android signing durumu

Cihazdaki kurulu uygulamanın sertifikası:

```text
SHA-256: b1fd54c87276e9753fcbaf4b6d93f0010ad9d3fdd93806e0462c7867a5ea0fba
```

`td2-companion-beta.jks` aynı sertifikayı üretiyor. Bu, doğru release keystore'un bulunduğunu doğrular.

Yerel debug APK'lar farklı sertifika kullanıyor ve cihazdaki kurulu uygulamanın üzerine güncelleme olarak kurulamaz.

Yerel signing script'i:

```text
scripts/build_signed_companion.ps1
```

Script parolayı etkileşimli ister, geçici `mobile/android/key.properties` oluşturur, release build yapar ve cleanup uygular. Parola kaynak koda veya loga yazılmaz.

CI workflow'unda signing hazırlığı için şu secret isimleri kullanılır:

```text
ANDROID_KEYSTORE_BASE64
ANDROID_KEYSTORE_PASSWORD
ANDROID_KEY_ALIAS
ANDROID_KEY_PASSWORD
```

`.github/workflows/build-mobile.yml` üzerinde yerel değişiklik vardır. Tag build'i için secret eksikse workflow'un fail-closed davranması ve debug imzasına sessizce düşmemesi hedeflenmiştir.

**Açık risk:** Secret'ların GitHub repository ayarlarında gerçekten tanımlandığı bu çalışma alanından doğrulanmadı.

## 7. APK güncelleme durumu

Kurulu uygulama cihazdan okunabildi. Ancak yeni yerel APK henüz aynı release key ile build edilip cihazda güncellenmedi.

Sıradaki test sırası:

1. Signed APK build.
2. Yeni APK fingerprint kontrolü.
3. Eski ve yeni fingerprint eşleşmesi.
4. Uygulama verilerini silmeden `adb install -r` veya Android installer güncellemesi.
5. VersionName/versionCode kontrolü.
6. QR/cloud eşleştirme korunması.
7. FileProvider installer akışı.
8. SHA-256 doğrulaması.

## 8. Firebase/FCM durumu

FCM servis kodu ve Android Firebase yapılandırması mevcut. Ancak aşağıdakiler gerçek cihazda doğrulanmadı:

- Bildirim izni
- Token kaydı
- Token yenilenmesi
- Geçersiz token temizliği
- Uygulama açık/kapalı/arka planda bildirim teslimi
- Bildirim tıklama yönlendirmesi

FCM credential değerleri rapora veya kaynağa yazılmamalıdır. Gerçek push testi için güvenli production/test credential yapılandırması ve fiziksel cihaz gerekir.

## 9. Canlı çeviri ve overlay

İzole testler:

```text
python -B tests/test_livetranslate.py  → RESULT: PASS
python -B tests/test_overlay.py        → RESULT: PASS
```

Bu testler OCR ve overlay mantığını doğrular; gerçek oyunun ekran yakalama davranışını doğrulamaz.

Gerçek oyun testi henüz yapılmadı. Aşağıdaki kanıtlar eksik:

- Oyun pencere koordinatları
- Gerçek capture alanı
- Ham OCR ve güven skorları
- Overlay render öğe sayısı
- `canvas_items`
- Siyah/boş pencere nedeni
- Ana pencere çakışması
- HDR kaynağı
- DPI ve borderless koordinat davranışı

## 10. Bilinen teknik riskler

### P0

- [Kısmen doğrulandı] Release signing secret/configuration tamamlanmadan production APK üretmemek gerekir.
- [Doğrulandı] Kullanıcı/runtime dosyaları çalışma ağacında kirli durumda; yayın öncesi korunmalıdır.

### P1

- [Test edilmedi] Signed APK’nın gerçek cihaz üzerine verileri koruyarak güncellenmesi.
- [Test edilmedi] FCM gerçek cihaz push teslimatı.
- [Test edilmedi] İmzalı manifest doğrulaması.
- [Test edilmedi] Gerçek The Division 2 overlay testi.

### P2

- [Statik inceleme] OCR geçersiz girdilerinin tüm karar yollarında merkezi doğrulanması gerekiyor.
- [Statik inceleme] Prototype/Named koruma politikası karar motoru ve stash arasında tutarlı değil.
- [Statik inceleme] Canlı çeviri ekran imzası başarılı olmadan atanırsa hata sonrası aynı ekranın yeniden denenmesi engellenebilir.
- [Statik inceleme] Çok sayıda canlı çeviri çağrısı paralel iş parçacığı/kuyruk baskısı oluşturabilir.
- [Statik inceleme] `app.py` çok büyük bir koordinatör sınıf içeriyor.

### P3

- [Statik inceleme] Sunucu README’si modüllü Wrangler yapısıyla tam uyumlu olmayabilir.
- [Statik inceleme] CI testleri farklı commit’lerde çalıştığı için geçmiş başarılar güncel commit kanıtı sayılmamalı.
- [Statik inceleme] Görev/meta feed’lerinin güncelliği runtime senkronu ile tekrar doğrulanmalı.

## 11. Yerel test kanıtları

Son başarılı testler:

```text
flutter analyze                  → No issues found
flutter test                     → All tests passed
python -B tests/test_livetranslate.py → RESULT: PASS
python -B tests/test_overlay.py       → RESULT: PASS
python -B tests/test_project_structure.py → 7 tests passed
PowerShell signing script parse  → POWERSHELL_PARSE_OK
build-mobile.yml YAML parse      → YAML_OK
```

Henüz çalıştırılmamış veya gerçek ortam gerektiren testler:

- Signed APK build ve device update.
- FCM gerçek push.
- Gerçek The Division 2 overlay.
- Windows packaged EXE ve installer.
- Python 3.13/3.14/3.15.1 tam paketleme matrisi.

## 12. Codex’in sonraki çalışma sırası

### P0/P1 sırası

1. Yerel signed APK üret.
2. APK fingerprint’ini keystore ve cihazla karşılaştır.
3. Verileri silmeden Android update testini yap.
4. FileProvider ve installer akışını doğrula.
5. Firebase/FCM gerçek cihaz testini yap.
6. Signed release manifest tasarımını ve testlerini tamamla.
7. Gerçek The Division 2 overlay kanıt testini yap.

### P2 sırası

1. OCR karar yollarını merkezi `REVIEW` politikasına al.
2. Prototype/Named/kilitli korumasını tek politikada birleştir.
3. Canlı çeviri kuyruk ve tekrar deneme davranışını düzelt.
4. EXE/installer smoke testlerini Python matrisiyle çalıştır.

### P3 sırası

1. Devir ve Firebase/signing yönergelerini güncelle.
2. CI commit kapsamını ve timeout’ları netleştir.
3. Sunucu README’sini güncel Wrangler yapısına göre düzenle.

## 13. Yayın sınırı

Bu devir tesliminde yayın yapılmadı. Bundan sonraki işlemlerde kullanıcı onayı olmadan şu işlemler yapılmayacak:

- `git push`
- Public tag
- GitHub Release
- APK paylaşımı
- Windows installer paylaşımı

Yayın öncesinde kullanıcıya tam olarak şu soru sorulmalıdır:

```text
Yeni Güncellemeyi Yayınlamak İster misiniz? (vX.Y.Z) — Evet / Hayır
```

Kullanıcı açıkça `Evet` demeden yayın yapılmamalıdır.

## 14. Devir teslim özeti

Codex’in devraldığı güvenilir durum şudur:

- Kaynak ve test altyapısı yerel olarak mevcut.
- Flutter analiz ve testleri geçiyor.
- İzole canlı çeviri ve overlay testleri geçiyor.
- Fiziksel Android cihaz ADB’de bağlı.
- Doğru Android release keystore bulundu ve cihaz sertifikasıyla eşleşiyor.
- CI signing hazırlığı yerelde güncellendi.
- Gerçek APK güncellemesi, FCM, oyun overlay’i ve installer testleri henüz tamamlanmadı.
- Secret, private key ve runtime dosyaları korunmalı.
- Yayın yapılmadı.

