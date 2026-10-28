# TD2 Loot Advisor Companion 0.1.2-beta

## Android kurulumu

1. `TD2LootAdvisor_Companion_0.1.2-beta.apk` dosyasını Android telefona aktarın.
2. Dosyayı açın ve Android'in istediği durumda bu kaynaktan uygulama yükleme iznini verin.
3. Uygulamayı başlatın. İlk kullanımda görev ve haber akışlarını yenilemek için internet bağlantısı gerekir.

## Beta kapsamı

- Görevler, haberler ve önerilen build listeleri herkese açık proje JSON verilerinden alınır; bağlantı olmadığında uygulamayla gelen başlangıç verileri kullanılır.
- Görev ilerlemesi ve kullanıcı build'leri bu cihazda saklanır.
- Dış kaynak sayfaları bağlantıları kullanıcının tarayıcısında açılır.
- Android'de Windows programının Telefon Arkadaşı QR kodu okutularak aynı Wi-Fi üzerinden salt-okunur canlı masaüstü durumu görüntülenebilir.
- Hesap/giriş, anlık bildirim, oyun içi OCR veya oyun belleği erişimi yoktur.
- Uygulama Ubisoft veya Massive Entertainment tarafından yayımlanmamıştır ya da desteklenmemektedir.

Telefon ve Windows programını eşleştirmek için ayrıntılı kılavuz: `docs/mobile_companion_connection_tr.md`.

## Yayın notu

Bu APK, Flutter release yapılandırmasıyla üretilen yan yükleme beta paketidir. Google Play için yayın imzası, mağaza kaydı, gizlilik beyanları ve fiziksel cihaz kabul testleri henüz yapılmamıştır. iOS derlemesi ve App Store imzalama işlemi Apple'ın macOS/Xcode ortamını gerektirir.

## 0.1.2 hata düzeltmesi

Android başlatıcı manifestindeki `MainActivity` paketi ile Kotlin sınıfının paketi eşleştirildi. Önceki APK'da bu fark uygulamanın açılışta kapanmasına neden oluyordu.

## Önceki beta üzerinden kurulum

Bu yerel 0.1.2 test APK'sı bilgisayardaki Android debug anahtarıyla imzalandı. GitHub'dan indirilen 0.1.1 APK farklı anahtarla imzalandığı için Android doğrudan üzerine kurulum izni vermeyebilir; böyle olursa eski sürümü kaldırıp bu sürümü kurun. Kaldırma uygulama içi verileri siler. Önceki sürüm açılışta kapandığından görev/build kaydı oluşturamamış olması gerekir.
