# TD2 Loot Advisor Companion 0.1.4.1-beta (Android yapı 6)

## Android kurulumu

1. `TD2LootAdvisor_Companion_0.1.4.1-beta.apk` dosyasını Android telefona aktarın.
2. Dosyayı açın ve Android'in istediği durumda bu kaynaktan uygulama yükleme iznini verin.
3. Uygulamayı başlatın. İlk kullanımda görev ve haber akışlarını yenilemek için internet bağlantısı gerekir.

## Uygulama içinden güncelleme

Yeni bir Companion beta sürümü yayımlandığında uygulama açılışta GitHub'daki
yalnız `companion-v...` etiketlerini denetler. **İçerik ve Güncellemeler**
kartındaki **Güncellemeyi indir** tuşu doğrudan imzalı APK indirmesini başlatır.
İndirme tamamlandığında Android, mevcut uygulamanın üstüne kurulumu kullanıcıya
onaylatır. Android güvenlik modeli nedeniyle sessiz/arka plan kurulumu yapılmaz.

## Beta kapsamı

- Görevler, haberler ve önerilen build listeleri uygulama açılırken herkese açık proje JSON verilerinden yenilenir; son başarılı veri cihazda önbelleğe alınır, bağlantı olmadığında önbellek veya uygulamayla gelen başlangıç verileri kullanılır.
- Görev ilerlemesi ve kullanıcı build'leri bu cihazda saklanır.
- Dış kaynak sayfaları bağlantıları kullanıcının tarayıcısında açılır.
- Android'de Windows programının Telefon Arkadaşı QR kodu okutularak aynı Wi-Fi üzerinden salt-okunur canlı masaüstü durumu görüntülenebilir.
- İsteğe bağlı Bulut eşleştirmesi, Windows uygulamasının ürettiği kısa ömürlü kodla çalışır; build senkronu ve masaüstü durumunu aynı Wi-Fi dışında da gösterir. Hesap ve bağlı bulut verilerini silme akışı uygulama içinde bulunur.
- Bildirimler varsayılan olarak kapalıdır. Kullanıcı Bulut eşleştirmesi veya İçerik ve güncellemeler alanındaki anahtarı açarsa izin istenir. Uygulama açıkken yeni haber ve Companion güncelleme bildirimi yerel olarak gösterilebilir; masaüstü tarama bildirimi için cihaz belirteci yalnız Bulut eşleştirmesi anahtarıyla kaydedilir.
- Oyun içi OCR, oyun belleği erişimi veya oyuna giriş gönderme yoktur.
- Uygulama Ubisoft veya Massive Entertainment tarafından yayımlanmamıştır ya da desteklenmemektedir.

Telefon ve Windows programını eşleştirmek için ayrıntılı kılavuz: `docs/mobile_companion_connection_tr.md`.

## Yayın notu

Bu APK, Flutter release yapılandırmasıyla üretilen yan yükleme beta paketidir. Google Play için yayın imzası, mağaza kaydı, gizlilik beyanları ve fiziksel cihaz kabul testleri henüz yapılmamıştır. iOS derlemesi ve App Store imzalama işlemi Apple'ın macOS/Xcode ortamını gerektirir.

## 0.1.2 hata düzeltmesi (korunur)

Android başlatıcı manifestindeki `MainActivity` paketi ile Kotlin sınıfının paketi eşleştirildi. Önceki APK'da bu fark uygulamanın açılışta kapanmasına neden oluyordu.

## Önceki beta üzerinden kurulum

Bu yerel 0.1.4.1 test APK'sı bilgisayardaki Android debug anahtarıyla imzalanabilir. Farklı anahtarla imzalanmış önceki bir APK varsa Android doğrudan üzerine kurulum izni vermeyebilir; böyle olursa eski sürümü kaldırıp bu sürümü kurun. Kaldırma uygulama içi verileri siler. Play Store için debug imzalı APK kullanılmaz.
