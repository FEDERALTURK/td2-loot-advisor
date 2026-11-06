import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// Yerel bildirimler yalnız kullanıcı açıkça içerik/sürüm bildirimi anahtarını
/// etkinleştirdiğinde kullanılır. Bu sınıf ağ veya Firebase tokenı saklamaz.
class LocalAlerts {
  LocalAlerts._();

  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  static bool _ready = false;

  static Future<void> initialize() async {
    if (_ready || kIsWeb) return;
    const settings = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      iOS: DarwinInitializationSettings(
        requestAlertPermission: false,
        requestBadgePermission: false,
        requestSoundPermission: false,
      ),
    );
    await _plugin.initialize(settings);
    _ready = true;
  }

  static Future<bool> requestPermission() async {
    if (kIsWeb) return false;
    await initialize();
    final android = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    final androidResult = await android?.requestNotificationsPermission();
    final ios = _plugin.resolvePlatformSpecificImplementation<
        IOSFlutterLocalNotificationsPlugin>();
    final iosResult = await ios?.requestPermissions(
      alert: true,
      badge: true,
      sound: true,
    );
    return androidResult ?? iosResult ?? true;
  }

  static Future<void> show({required int id, required String title, required String body}) async {
    if (kIsWeb) return;
    await initialize();
    const android = AndroidNotificationDetails(
      'td2_content_updates',
      'TD2 içerik güncellemeleri',
      channelDescription: 'Yeni TD2 haberleri ve Companion sürüm güncellemeleri',
      importance: Importance.high,
      priority: Priority.high,
    );
    await _plugin.show(id, title, body, const NotificationDetails(android: android));
  }
}
