// Google Cloud Speech-to-Text REST API istemcisi (v1, speech:recognize).
//
// NOT (dürüstlük ilkesi): Bu, GERÇEK bir Google Cloud API anahtarıyla hiç
// denenmedi — bu kum havuzunda böyle bir anahtar yok ve olmamalı. İstek/yanıt
// şeması resmi Google Cloud dokümantasyonundan doğrulandı (bkz.
// DEVELOPMENT_LOG.md), ama ağ çağrısının gerçek bir hesapla çalıştığı
// doğrulanmamıştır.
import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../audio/mic_capture_service.dart' show micSampleRateHz;

class SpeechToTextResult {
  const SpeechToTextResult({required this.transcript, required this.confidence});

  final String transcript;
  final double confidence;
}

class SpeechToTextException implements Exception {
  SpeechToTextException(this.message);
  final String message;
  @override
  String toString() => 'SpeechToTextException: $message';
}

class SpeechToTextService {
  SpeechToTextService({required this.apiKey, http.Client? client})
      : _client = client ?? http.Client();

  final String apiKey;
  final http.Client _client;

  static const _endpoint = 'https://speech.googleapis.com/v1/speech:recognize';

  /// [pcm16] ham, tek kanallı, [micSampleRateHz] örnekleme hızında LINEAR16
  /// sesi. [languageCode] BCP-47 biçiminde olmalı (örn. "en-US", "tr-TR").
  Future<SpeechToTextResult?> recognize({
    required Uint8List pcm16,
    required String languageCode,
  }) async {
    final body = jsonEncode({
      'config': {
        'encoding': 'LINEAR16',
        'sampleRateHertz': micSampleRateHz,
        'languageCode': languageCode,
        'enableAutomaticPunctuation': true,
      },
      'audio': {'content': base64Encode(pcm16)},
    });

    final response = await _client.post(
      Uri.parse('$_endpoint?key=$apiKey'),
      headers: {'Content-Type': 'application/json'},
      body: body,
    );

    if (response.statusCode != 200) {
      throw SpeechToTextException(
        'Google Speech-to-Text hata döndürdü (${response.statusCode}): ${response.body}',
      );
    }

    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    final results = decoded['results'] as List<dynamic>?;
    if (results == null || results.isEmpty) {
      return null; // Bu parçada anlaşılır konuşma bulunamadı (sessizlik vb.).
    }

    final alternatives = (results.first as Map<String, dynamic>)['alternatives'] as List<dynamic>?;
    if (alternatives == null || alternatives.isEmpty) {
      return null;
    }

    final top = alternatives.first as Map<String, dynamic>;
    return SpeechToTextResult(
      transcript: (top['transcript'] as String?)?.trim() ?? '',
      confidence: (top['confidence'] as num?)?.toDouble() ?? 0.0,
    );
  }

  void dispose() => _client.close();
}
