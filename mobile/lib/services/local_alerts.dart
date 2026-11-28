import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Yerel bildirimler yalnız kullanıcı açıkça içerik/sürüm bildirimi anahtarını
/// etkinleştirdiğinde kullanılır. Bu sınıf ağ veya Firebase tokenı saklamaz.
class LocalAlerts {
  LocalAlerts._();

  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  static bool _ready = false;
  static bool quietHoursEnabled = false;
  static int quietStartMinute = 22 * 60;
  static int quietEndMinute = 8 * 60;
  static final ValueNotifier<String?> destination = ValueNotifier(null);
  static final Set<String> _shownEvents = {};

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
    await _plugin.initialize(
      settings,
      onDidReceiveNotificationResponse: _handleResponse,
    );
    final prefs = await SharedPreferences.getInstance();
    quietHoursEnabled = prefs.getBool('notification_quiet_enabled') ?? false;
    quietStartMinute = prefs.getInt('notification_quiet_start') ?? 22 * 60;
    quietEndMinute = prefs.getInt('notification_quiet_end') ?? 8 * 60;
    _shownEvents.addAll(prefs.getStringList('shown_notification_events') ?? []);
    final launch = await _plugin.getNotificationAppLaunchDetails();
    final payload = launch?.notificationResponse?.payload;
    if (launch?.didNotificationLaunchApp == true && payload != null) {
      destination.value = payload;
    }
    _ready = true;
  }

  static Future<bool> requestPermission() async {
    if (kIsWeb) return false;
    await initialize();
    final android = _plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    final androidResult = await android?.requestNotificationsPermission();
    final ios = _plugin
        .resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin
        >();
    final iosResult = await ios?.requestPermissions(
      alert: true,
      badge: true,
      sound: true,
    );
    return androidResult ?? iosResult ?? true;
  }

  static Future<void> configureQuietHours({
    required bool enabled,
    int startMinute = 22 * 60,
    int endMinute = 8 * 60,
  }) async {
    quietHoursEnabled = enabled;
    quietStartMinute = startMinute.clamp(0, 1439);
    quietEndMinute = endMinute.clamp(0, 1439);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('notification_quiet_enabled', enabled);
    await prefs.setInt('notification_quiet_start', quietStartMinute);
    await prefs.setInt('notification_quiet_end', quietEndMinute);
  }

  static bool get isQuietNow {
    if (!quietHoursEnabled) return false;
    final now = DateTime.now();
    final minute = now.hour * 60 + now.minute;
    if (quietStartMinute == quietEndMinute) return true;
    return quietStartMinute < quietEndMinute
        ? minute >= quietStartMinute && minute < quietEndMinute
        : minute >= quietStartMinute || minute < quietEndMinute;
  }

  static void _handleResponse(NotificationResponse response) {
    destination.value = response.payload;
  }

  static void consumeDestination() => destination.value = null;

  static Future<void> show({
    required int id,
    required String title,
    required String body,
    String category = 'news',
    String? eventKey,
  }) async {
    if (kIsWeb ||
        isQuietNow ||
        category != 'news' && category != 'update' && category != 'task') {
      return;
    }
    await initialize();
    if (eventKey != null && !_shownEvents.add(eventKey)) return;
    if (eventKey != null) {
      final prefs = await SharedPreferences.getInstance();
      final events = _shownEvents.toList();
      if (events.length > 100) {
        _shownEvents
          ..clear()
          ..addAll(events.skip(events.length - 100));
      }
      await prefs.setStringList(
        'shown_notification_events',
        _shownEvents.toList(),
      );
    }
    const android = AndroidNotificationDetails(
      'td2_content_updates',
      'TD2 içerik güncellemeleri',
      channelDescription:
          'Yeni TD2 haberleri ve Companion sürüm güncellemeleri',
      importance: Importance.high,
      priority: Priority.high,
    );
    await _plugin.show(
      id,
      title,
      body,
      const NotificationDetails(android: android),
      payload: category,
    );
  }
}
