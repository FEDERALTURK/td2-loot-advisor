// Xbox doğrudan bağlantı (deneysel) — yerel belirteç (token) saklama.
//
// 1.Auth.md §1.9 "Local tokenStore Overview" bölümünde tarif edilen üç
// nesneyi (userToken, sisuToken, jwtKeys) tek bir JSON belgesi olarak,
// uygulamanın zaten kullandığı flutter_secure_storage üzerinden saklar
// (Android Keystore / iOS Keychain — bkz. bulut eşleştirme oturumu için
// aynı yaklaşım zaten mobile_pairing_service.dart'ta kullanılıyor).
//
// Burada SADECE veri modelleri ve JSON (de)serileştirme var; ağ çağrıları
// xbox_auth_service.dart'ta.
import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'xbox_crypto.dart';

const _storageKey = 'xbox_token_store_v1';

class XboxUserToken {
  XboxUserToken({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresOn,
  });

  final String accessToken;
  final String refreshToken;
  final DateTime expiresOn;

  bool get isExpired => DateTime.now().isAfter(expiresOn);

  Map<String, dynamic> toJson() => {
        'access_token': accessToken,
        'refresh_token': refreshToken,
        'expires_on': expiresOn.toIso8601String(),
      };

  factory XboxUserToken.fromJson(Map<String, dynamic> j) => XboxUserToken(
        accessToken: j['access_token'] as String,
        refreshToken: j['refresh_token'] as String,
        expiresOn: DateTime.parse(j['expires_on'] as String),
      );
}

/// 1.Auth.md §1.8.3 yanıtı — DeviceToken/TitleToken/UserToken üçlüsü.
class XboxSisuToken {
  XboxSisuToken({
    required this.deviceToken,
    required this.titleToken,
    required this.userToken,
  });

  final String deviceToken;
  final String titleToken;
  final String userToken;

  Map<String, dynamic> toJson() => {
        'deviceToken': deviceToken,
        'titleToken': titleToken,
        'userToken': userToken,
      };

  factory XboxSisuToken.fromJson(Map<String, dynamic> j) => XboxSisuToken(
        deviceToken: j['deviceToken'] as String,
        titleToken: j['titleToken'] as String,
        userToken: j['userToken'] as String,
      );
}

class XboxTokenStore {
  XboxTokenStore({
    this.jwtKeys,
    this.userToken,
    this.sisuToken,
  });

  XboxJwtKeys? jwtKeys;
  XboxUserToken? userToken;
  XboxSisuToken? sisuToken;

  static final FlutterSecureStorage _secure = const FlutterSecureStorage();

  static Future<XboxTokenStore> load() async {
    final raw = await _secure.read(key: _storageKey);
    if (raw == null) return XboxTokenStore();
    try {
      final j = jsonDecode(raw) as Map<String, dynamic>;
      return XboxTokenStore(
        jwtKeys: j['jwtKeys'] != null
            ? XboxJwtKeys.fromJwk(j['jwtKeys'] as Map<String, dynamic>)
            : null,
        userToken: j['userToken'] != null
            ? XboxUserToken.fromJson(j['userToken'] as Map<String, dynamic>)
            : null,
        sisuToken: j['sisuToken'] != null
            ? XboxSisuToken.fromJson(j['sisuToken'] as Map<String, dynamic>)
            : null,
      );
    } catch (_) {
      // Bozuk/eski biçim — sıfırdan girişe zorla, çökmeye neden olma.
      return XboxTokenStore();
    }
  }

  Future<void> save() async {
    final j = <String, dynamic>{
      if (jwtKeys != null) 'jwtKeys': jwtKeys!.toJwk(),
      if (userToken != null) 'userToken': userToken!.toJson(),
      if (sisuToken != null) 'sisuToken': sisuToken!.toJson(),
    };
    await _secure.write(key: _storageKey, value: jsonEncode(j));
  }

  Future<void> clear() async {
    jwtKeys = null;
    userToken = null;
    sisuToken = null;
    await _secure.delete(key: _storageKey);
  }

  bool get hasUserLogin => userToken != null && jwtKeys != null;
}
