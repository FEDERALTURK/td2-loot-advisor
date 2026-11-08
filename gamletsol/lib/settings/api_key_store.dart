// Google Cloud API anahtarı güvenli depoda (Android Keystore / iOS Keychain)
// saklanır — düz tercih dosyasına, loglara veya koda ASLA yazılmaz (AGENTS.md
// madde 3 ve genel "sırları koda/loglara yazma" ilkesiyle uyumlu).
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiKeyStore {
  ApiKeyStore({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _keyName = 'gamletsol_google_cloud_api_key_v1';

  final FlutterSecureStorage _storage;

  Future<String?> read() => _storage.read(key: _keyName);

  Future<void> write(String apiKey) => _storage.write(key: _keyName, value: apiKey);

  Future<void> clear() => _storage.delete(key: _keyName);
}
