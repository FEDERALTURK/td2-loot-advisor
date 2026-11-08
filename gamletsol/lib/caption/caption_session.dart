// Mikrofon → Speech-to-Text → Çeviri boru hattını yöneten oturum sınıfı.
//
// Sıralı işleme kasıtlı: bir ses parçası hâlâ işlenirken yenisi gelirse,
// önceki bitene kadar kuyrukta beklemez — sadece en son parça tutulur (en eski
// atılır). Bu, STT/çeviri yanıtı parça süresinden uzun sürerse gecikmenin
// sürekli büyümesini (birikmeyi) önler; canlı altyazıda "güncel ama bazen
// atlamalı" davranış, "doğru ama sürekli geciken" davranışa tercih edilir.
import 'dart:async';
import 'dart:typed_data';

import '../audio/mic_capture_service.dart';
import '../stt/speech_to_text_service.dart';
import '../translate/translate_service.dart';
import 'caption_line.dart';

class CaptionSession {
  CaptionSession({
    required String apiKey,
    required this.sourceLanguageCode,
    required this.targetLanguageCode,
  })  : _stt = SpeechToTextService(apiKey: apiKey),
        _translate = TranslateService(apiKey: apiKey);

  final String sourceLanguageCode; // örn. "en-US" (STT için BCP-47)
  final String targetLanguageCode; // örn. "tr" (çeviri için ISO 639-1)

  final MicCaptureService _mic = MicCaptureService();
  final SpeechToTextService _stt;
  final TranslateService _translate;

  final _linesController = StreamController<CaptionLine>.broadcast();
  final _errorController = StreamController<String>.broadcast();

  Stream<CaptionLine> get lines => _linesController.stream;
  Stream<String> get errors => _errorController.stream;

  bool _processing = false;
  Uint8List? _pendingChunk;
  bool _running = false;

  bool get isRunning => _running;

  Future<void> start() async {
    if (_running) return;
    _running = true;
    await _mic.start(onChunk: _onChunk);
  }

  Future<void> stop() async {
    _running = false;
    await _mic.stop();
  }

  void _onChunk(Uint8List pcm16) {
    _pendingChunk = pcm16;
    if (!_processing) {
      unawaited(_drain());
    }
  }

  Future<void> _drain() async {
    _processing = true;
    try {
      while (_pendingChunk != null) {
        final chunk = _pendingChunk!;
        _pendingChunk = null;
        await _processChunk(chunk);
      }
    } finally {
      _processing = false;
    }
  }

  Future<void> _processChunk(Uint8List pcm16) async {
    try {
      final sttResult = await _stt.recognize(
        pcm16: pcm16,
        languageCode: sourceLanguageCode,
      );
      if (sttResult == null || sttResult.transcript.isEmpty) return;

      final sourceIso = sourceLanguageCode.split('-').first;
      final translated = await _translate.translate(
        text: sttResult.transcript,
        sourceLanguageCode: sourceIso,
        targetLanguageCode: targetLanguageCode,
      );

      _linesController.add(CaptionLine(
        original: sttResult.transcript,
        translated: translated,
        confidence: sttResult.confidence,
        timestamp: DateTime.now(),
      ));
    } catch (error) {
      _errorController.add(error.toString());
    }
  }

  Future<void> dispose() async {
    await stop();
    _mic.dispose();
    _stt.dispose();
    _translate.dispose();
    await _linesController.close();
    await _errorController.close();
  }
}
