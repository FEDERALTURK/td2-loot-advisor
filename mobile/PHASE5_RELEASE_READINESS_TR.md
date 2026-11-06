# Faz 5 — İlk Halka Açık Sürüm Hazırlığı

Son doğrulama: 6 Kasım 2026. Bu belge, mağaza yayını için doğrulanmış teknik
durumu ve kullanıcı hesabı/cihaz erişimi gerektiren açık adımları ayırır.

## Bu çalışma alanında doğrulananlar

- Flutter `3.47.8` ve Dart `3.13.7` ile `flutter analyze` temiz geçti.
- `flutter test` geçti; başlangıç testi asenkron splash ekranını doğrulayacak
  şekilde güncellendi.
- Android debug APK yerelde üretildi.
- Android release AAB yerelde üretildi.
- Android uygulama kimliği `com.federalturk.td2companion`, hedef API seviyesi
  `36` olarak kaynakta tanımlı.
- Bulut eşleştirme oturum kimliği ve belirteci artık düz uygulama tercihlerinde
  değil, Android Keystore/iOS Keychain tabanlı güvenli depoda tutulur. Eski
  beta değeri varsa ilk açılışta taşınır.
- Bildirim izni, uygulama açılışında veya sadece eşleştirme yapıldığı için
  istenmez; kullanıcı Bulut eşleştirmesi ekranındaki anahtarı açarsa istenir.
- Gizlilik politikası, isteğe bağlı bulut eşleştirmesi, build senkronu,
  bildirim belirteci ve hesap silme akışıyla güncellendi.

## Yayından önce kullanıcı tarafında yapılması gerekenler

1. **Gerçek Android cihaz testi:** Bir Android 16 cihazda uygulamayı açın;
   görev/haber yenileme, yerel QR eşleştirmesi, bulut eşleştirmesi, build
   senkronu, bildirim anahtarı ve hesap silme uyarısını deneyin.
2. **Google Play hesabı ve upload key:** Play Console kaydı tamamlandıktan
   sonra `PLAY_STORE_RELEASE_TR.md` içindeki upload keystore adımlarını kendi
   cihazınızda yapın. Keystore ve `key.properties` kesinlikle Git'e eklenmez.
3. **Mağaza metinleri:** Destek e-postası, gizlilik politikası için herkese
   açık URL, Data safety formu, ikon/özellik görseli ve gerçek cihaz ekran
   görüntüleri hazırlanmalı.
4. **Push bildirimi:** Firebase yapılandırması gerçekten eklenmeden ve cihazda
   doğrulanmadan bildirim anahtarı mağaza ekran görüntülerinde vaat edilmemeli.
   `google-services.json` ile Google Services Gradle eklentisi kasıtlı olarak
   kaynakta kapalıdır; yapılandırma yokken uygulamanın ana işlevi çalışır.
5. **iOS:** App Store yayını için macOS/Xcode, ücretli Apple Developer üyeliği,
   imzalama ve gerçek iPhone/TestFlight testi gerekir. Bunlar Windows'tan
   tamamlanamaz.

## Takip edilmesi gereken teknik notlar

- Release AAB bu ortamda özel Play upload anahtarı olmadan üretildi; bu sadece
  derlenebilirlik kanıtıdır, Play Console'a yüklenebilecek imzalı sürüm değildir.
- Flutter derlemesi Firebase Core'un gelecekteki Kotlin Gradle "Built-in
  Kotlin" geçişi için uyarı veriyor. Mevcut derlemeyi engellemez; fakat Firebase
  paket yükseltmesi ayrı bir bakım turunda test edilmelidir.
- Mağaza yayını yapılmadan önce bu belgedeki gerçek cihaz denetimleri ve
  `PLAY_STORE_RELEASE_TR.md` kontrol listesi tamamlanmalıdır.

## Yayın sınırı

Bu belge veya yerel AAB/APK çıktıları mağazaya yükleme izni vermez. Google Play
veya App Store'a yükleme, kapalı test başlatma ya da üretim yayını her seferinde
kullanıcının açık onayını gerektirir.
