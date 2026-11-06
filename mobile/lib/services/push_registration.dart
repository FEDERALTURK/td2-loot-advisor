// TD2 Loot Advisor Companion — push bildirimi cihaz token'ı (Faz 4).
//
// Sunucu tarafı (server/mobile.js) zaten hazır: Android/FCM canlı, iOS/APNs
// kodu hazır (bkz. docs/mobile_companion_roadmap.md). Eksik olan tek parça
// buydu — telefonun kendi FCM/APNs token'ını `PUT /v1/mobile/push-tokens/{id}`
// ile sunucuya kaydetmesi. Bu dosya SADECE token alma/izin isteme işini yapar;
// HTTP çağrısı ve durum (ne zaman kaydedilir) `cloud_link.dart`'ta kalır.
//
// Bilerek en-iyi-gayret (best-effort) tasarlandı: `android/app/google-services.json`
// henüz eklenmediyse (bkz. docs/push_notifications_setup.md (depo köküne göre)) Firebase başlatma
// başarısız olur — bu durumda uygulamanın çökmemesi, sessizce push kaydını
// atlaması gerekir (programın ana işlevi push bildirimine bağımlı değil).
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

class PushRegistration {
  static bool _firebaseReady = false;
  static bool _firebaseFailed = false;

  /// Firebase'i bir kez başlatır (sonraki çağrılar no-op). `google-services.json`
  /// yoksa/geçersizse başarısız olur ve bunu kalıcı olarak hatırlar — her
  /// çağrıda yeniden denemez (gereksiz gecikme/log gürültüsü olmasın).
  static Future<bool> _ensureFirebase() async {
    if (_firebaseReady) return true;
    if (_firebaseFailed) return false;
    try {
      await Firebase.initializeApp();
      _firebaseReady = true;
      return true;
    } catch (e) {
      _firebaseFailed = true;
      debugPrint('Push bildirimi: Firebase başlatılamadı (google-services.json eksik/hatalı olabilir): $e');
      return false;
    }
  }

  /// Bildirim izni ister (iOS her zaman, Android 13+'ta POST_NOTIFICATIONS) ve
  /// başarılıysa cihazın FCM/APNs token'ını döner. Herhangi bir adım
  /// başarısız olursa (izin yok, Firebase kurulu değil, vb.) `null` döner —
  /// çağıran taraf bunu "şimdilik push yok" olarak ele almalı, hata fırlatmaz.
  static Future<String?> requestPermissionAndGetToken() async {
    if (!await _ensureFirebase()) return null;
    try {
      final messaging = FirebaseMessaging.instance;
      final settings = await messaging.requestPermission(alert: true, badge: true, sound: true);
      final granted = settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional;
      if (!granted) return null;
      // firebase_messaging 17'deki yeni registration-ID akışı FCM tokenının
      // yerine geçmez: sunucunun HTTP v1 hedefi hâlâ gerçek FCM tokenı ister.
      // Bu nedenle paket bu geçişi tamamlayana kadar bu çağrı bilinçli olarak
      // korunur; kullanıcı açıkça bildirimleri etkinleştirmedikçe çalışmaz.
      // ignore: deprecated_member_use
      return await messaging.getToken();
    } catch (e) {
      debugPrint('Push bildirimi: token alınamadı: $e');
      return null;
    }
  }

  /// Token sonradan değişirse (ör. uygulama yeniden kurulduğunda, Firebase
  /// kendi içinde rotasyon yaptığında) tetiklenir. `cloud_link.dart` bu akışa
  /// abone olup sunucudaki kaydı güncel tutar. Firebase kurulu değilse boş
  /// (hiç olay yaymayan) bir stream döner.
  static Stream<String> get onTokenRefresh {
    if (_firebaseFailed) return const Stream.empty();
    // Yukarıdaki aynı FCM tokenı uyumluluk gerekçesi için.
    // ignore: deprecated_member_use
    return FirebaseMessaging.instance.onTokenRefresh;
  }
}
