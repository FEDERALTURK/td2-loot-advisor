// Google Cloud Translation API v2 istemcisi.
//
// NOT (dürüstlük ilkesi): İstek/yanıt şeması resmi Google Cloud
// dokümantasyonundan doğrulandı, ama gerçek bir API anahtarıyla bu kum
// havuzunda hiç denenmedi (bkz. speech_to_text_service.dart'taki aynı not).
import 'dart:convert';

import 'package:http/http.dart' as http;

class TranslateException implements Exception {
  TranslateException(this.message);
  final String message;
  @override
  String toString() => 'TranslateException: $message';
}

class TranslateService {
  TranslateService({required this.apiKey, http.Client? client})
      : _client = client ?? http.Client();

  final String apiKey;
  final http.Client _client;

  static const _endpoint = 'https://translation.googleapis.com/language/translate/v2';

  /// [sourceLanguageCode] ve [targetLanguageCode] ISO 639-1 (örn. "en", "tr").
  Future<String> translate({
    required String text,
    required String sourceLanguageCode,
    required String targetLanguageCode,
  }) async {
    if (text.trim().isEmpty) return '';
    if (sourceLanguageCode == targetLanguageCode) return text;

    final response = await _client.post(
      Uri.parse('$_endpoint?key=$apiKey'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'q': text,
        'source': sourceLanguageCode,
        'target': targetLanguageCode,
        'format': 'text',
      }),
    );

    if (response.statusCode != 200) {
      throw TranslateException(
        'Google Translate hata döndürdü (${response.statusCode}): ${response.body}',
      );
    }

    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    final data = decoded['data'] as Map<String, dynamic>?;
    final translations = data?['translations'] as List<dynamic>?;
    if (translations == null || translations.isEmpty) {
      throw TranslateException('Google Translate beklenmeyen yanıt döndürdü.');
    }
    return (translations.first as Map<String, dynamic>)['translatedText'] as String? ?? '';
  }

  void dispose() => _client.close();
}
