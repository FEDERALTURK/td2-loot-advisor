// TD2 Loot Advisor Companion — bulut API istemcisi (Faz 2/3, bkz.
// docs/mobile_companion_roadmap.md ve server/mobile.js).
//
// Telefon doğrudan masaüstüne bağlanmaz: her şey bu Cloudflare Worker üzerinden
// gider. Bu dosya yalnızca HTTP istek/yanıt mantığını içerir; durum (token,
// eşleştirme, senkron) `cloud_link.dart`'ta tutulur.
import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

/// Worker'ın canlı adresi (server/wrangler.toml → PUBLIC_URL ile aynı).
const String kCloudApiBase = 'https://td2-stats.td2loot.workers.dev';

/// Sunucudan dönen HTTP/ağ hatası. `code`, sunucunun `{"error": "..."}`
/// alanı (örn. "unauthorized", "rate limited") veya ağ/zaman aşımı için
/// "network" / "timeout" olur.
class CloudApiException implements Exception {
  CloudApiException(this.statusCode, this.code);
  final int statusCode;
  final String code;

  @override
  String toString() => 'CloudApiException($statusCode, $code)';
}

/// `PUT /v1/mobile/builds` sunucudaki revizyonla çakıştığında (409) fırlatılır.
class RevisionConflict implements Exception {
  RevisionConflict(this.serverRevision);
  final int serverRevision;
}

class CloudPairResult {
  const CloudPairResult({
    required this.deviceId,
    required this.token,
    required this.expiresIn,
  });
  final String deviceId;
  final String token;
  final int expiresIn;
}

class CloudApi {
  CloudApi({http.Client? client}) : _client = client ?? http.Client();
  final http.Client _client;

  static const _userAgent = 'TD2-Loot-Advisor-Companion/0.1.2';
  static const _timeout = Duration(seconds: 8);

  Uri _uri(String path) => Uri.parse('$kCloudApiBase$path');

  Map<String, String> _headers(String? token) => {
    'Content-Type': 'application/json',
    'User-Agent': _userAgent,
    if (token != null) 'Authorization': 'Bearer $token',
  };

  /// Ham istek: durum kodunu fırlatmadan döner, gövdeyi (varsa) JSON olarak çözer.
  Future<(int status, Map<String, dynamic> body)> _raw(
    String method,
    String path, {
    String? token,
    Map<String, dynamic>? body,
  }) async {
    final uri = _uri(path);
    final headers = _headers(token);
    final encoded = body == null ? null : jsonEncode(body);
    http.Response response;
    try {
      final future = switch (method) {
        'GET' => _client.get(uri, headers: headers),
        'POST' => _client.post(uri, headers: headers, body: encoded),
        'PUT' => _client.put(uri, headers: headers, body: encoded),
        'DELETE' => _client.delete(uri, headers: headers, body: encoded),
        _ => throw ArgumentError('desteklenmeyen HTTP metodu: $method'),
      };
      response = await future.timeout(_timeout);
    } on TimeoutException {
      throw CloudApiException(0, 'timeout');
    } on CloudApiException {
      rethrow;
    } catch (_) {
      throw CloudApiException(0, 'network');
    }
    if (response.body.isEmpty) return (response.statusCode, const <String, dynamic>{});
    try {
      final value = jsonDecode(utf8.decode(response.bodyBytes));
      return (
        response.statusCode,
        value is Map ? Map<String, dynamic>.from(value) : const <String, dynamic>{},
      );
    } catch (_) {
      return (response.statusCode, const <String, dynamic>{});
    }
  }

  /// 2xx dışı her durumda [CloudApiException] fırlatan genel istek yardımcısı.
  Future<Map<String, dynamic>> _send(
    String method,
    String path, {
    String? token,
    Map<String, dynamic>? body,
  }) async {
    final (status, decoded) = await _raw(method, path, token: token, body: body);
    if (status < 200 || status >= 300) {
      throw CloudApiException(status, '${decoded['error'] ?? 'http_$status'}');
    }
    return decoded;
  }

  /// Masaüstünde üretilen kısa ömürlü kodu telefon adına talep eder.
  Future<CloudPairResult> claimPairing(String code, {required bool isIos}) async {
    final j = await _send(
      'POST',
      '/v1/mobile/pairings/claim',
      body: {'code': code, 'platform': isIos ? 'ios' : 'android'},
    );
    return CloudPairResult(
      deviceId: '${j['device_id']}',
      token: '${j['token']}',
      expiresIn: (j['expires_in'] as num?)?.toInt() ?? 0,
    );
  }

  /// Eşleştirilmiş masaüstünün çevrimiçi/son olay durumu.
  Future<Map<String, dynamic>> dashboard(String token) =>
      _send('GET', '/v1/mobile/dashboard', token: token);

  Future<List<Map<String, dynamic>>> listBuilds(String token) async {
    final j = await _send('GET', '/v1/mobile/builds', token: token);
    final raw = j['builds'];
    return raw is List
        ? raw.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
        : <Map<String, dynamic>>[];
  }

  /// Bir build'i buluta yazar. Sunucudaki revizyon [baseRevision]'dan farklıysa
  /// [RevisionConflict] fırlatılır (çağıran taraf bir sonraki senkronda bulut
  /// hâlini önceliklendirir).
  Future<int> putBuild(
    String token, {
    required String clientId,
    required String name,
    required Map<String, dynamic> payload,
    required int baseRevision,
  }) async {
    final (status, decoded) = await _raw(
      'PUT',
      '/v1/mobile/builds',
      token: token,
      body: {
        'client_id': clientId,
        'name': name,
        'payload': payload,
        'base_revision': baseRevision,
      },
    );
    if (status == 409) {
      throw RevisionConflict((decoded['revision'] as num?)?.toInt() ?? -1);
    }
    if (status < 200 || status >= 300) {
      throw CloudApiException(status, '${decoded['error'] ?? 'http_$status'}');
    }
    return (decoded['revision'] as num).toInt();
  }

  /// Build'i buluta "silindi" (tombstone) olarak işaretler; diğer cihazlar bir
  /// sonraki senkronda bunu görür. Zaten silinmişse de 200 döner (idempotent).
  Future<int> deleteBuild(String token, String clientId) async {
    final j = await _send('DELETE', '/v1/mobile/builds/$clientId', token: token);
    return (j['revision'] as num?)?.toInt() ?? 0;
  }

  /// Hesap silme talebi oluşturur (24 saat bekleme süresi, ardından kalıcı silme).
  /// Bu, SADECE bu telefonu değil, masaüstünün bağlı olduğu TÜM hesabı siler.
  Future<void> deleteAccount(String token) => _send('DELETE', '/v1/mobile/me', token: token);

  /// Bu cihazın FCM/APNs push belirtecini sunucuya kaydeder (bkz. server/mobile.js
  /// → putPushToken). `delivery` sunucunun dürüst durumu: "available" (ilgili
  /// platformun secret'ı tanımlı, gerçekten gönderilebilir) ya da
  /// "not_yet_implemented" (secret henüz yok — bkz. ROADMAP.md, iOS/APNs).
  Future<String> putPushToken(String token, String deviceId, String pushToken) async {
    final j = await _send(
      'PUT',
      '/v1/mobile/push-tokens/$deviceId',
      token: token,
      body: {'token': pushToken},
    );
    return '${j['delivery'] ?? 'unknown'}';
  }

  /// Bu cihazın kayıtlı push belirtecini siler (ör. eşleştirme kaldırılırken —
  /// artık eşleşmemiş bir cihaza bildirim gönderilmeye çalışılmasın).
  Future<void> deletePushToken(String token, String deviceId) =>
      _send('DELETE', '/v1/mobile/push-tokens/$deviceId', token: token);
}
