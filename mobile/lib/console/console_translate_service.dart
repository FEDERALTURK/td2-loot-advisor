// Konsol Modu — OCR + çeviri motoru (bkz. docs/console_game_caption_roadmap.md, Faz 1).
//
// Tamamı cihaz-üstünde (on-device) çalışır: ekran görüntüsü veya OCR metni hiçbir
// sunucuya gönderilmez (proje genelindeki "ekran/OCR varsayılan olarak yerelde
// çalışır" ilkesiyle uyumlu, bkz. AGENTS.md madde 3). Google ML Kit'in metin
// tanıma ve çeviri modelleri telefonun kendisinde çalışır; çeviri modeli yalnız
// İLK kullanımda (bir kerelik) indirilir, sonrasında internet gerekmez.
import 'dart:io';

import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:google_mlkit_translation/google_mlkit_translation.dart';

/// Çeviri modelinin (İngilizce + Türkçe, ML Kit Translate) indirme durumu.
enum TranslationModelStatus { unknown, checking, downloading, ready, error }

class ConsoleTranslateService {
  // Alan adları private (_) olduğu için bu adlandırılmış parametreler
  // dışarıdan yalnızca varsayılan değerleriyle kullanılabilir (bkz.
  // ConsoleCaptionPage — zaten hep varsayılanla çağrılıyor). Bilerek
  // initializing-formal (`this._sourceLanguage`) kullanıldı.
  ConsoleTranslateService({
    this._sourceLanguage = TranslateLanguage.english,
    this._targetLanguage = TranslateLanguage.turkish,
  });

  final TranslateLanguage _sourceLanguage;
  final TranslateLanguage _targetLanguage;

  final TextRecognizer _recognizer = TextRecognizer(
    script: TextRecognitionScript.latin,
  );
  late final OnDeviceTranslator _translator = OnDeviceTranslator(
    sourceLanguage: _sourceLanguage,
    targetLanguage: _targetLanguage,
  );
  final OnDeviceTranslatorModelManager _modelManager =
      OnDeviceTranslatorModelManager();

  TranslationModelStatus _modelStatus = TranslationModelStatus.unknown;
  TranslationModelStatus get modelStatus => _modelStatus;
  String? modelError;

  bool _disposed = false;

  /// Çeviri modelini (gerekiyorsa) bir kerelik indirir. Zaten indirilmişse
  /// anında döner — her uygulama açılışında tekrar indirme yapılmaz.
  Future<void> ensureModelReady() async {
    _modelStatus = TranslationModelStatus.checking;
    try {
      final sourceReady = await _modelManager.isModelDownloaded(
        _sourceLanguage.bcpCode,
      );
      final targetReady = await _modelManager.isModelDownloaded(
        _targetLanguage.bcpCode,
      );
      if (sourceReady && targetReady) {
        _modelStatus = TranslationModelStatus.ready;
        return;
      }
      _modelStatus = TranslationModelStatus.downloading;
      if (!sourceReady) {
        await _modelManager.downloadModel(
          _sourceLanguage.bcpCode,
          isWifiRequired: false,
        );
      }
      if (!targetReady) {
        await _modelManager.downloadModel(
          _targetLanguage.bcpCode,
          isWifiRequired: false,
        );
      }
      _modelStatus = TranslationModelStatus.ready;
    } catch (e) {
      _modelStatus = TranslationModelStatus.error;
      modelError = '$e';
    }
  }

  /// Verilen fotoğraf dosyasındaki metni okuyup Türkçeye çevirir. Ekranda
  /// okunur metin yoksa `null` döner (ekranda hiç yazı olmayan karelerde
  /// gereksiz çeviri çağrısı yapılmaz).
  ///
  /// Dönen kayıt: `(kaynak metin, çevrilmiş metin)`.
  Future<(String, String)?> recognizeAndTranslate(String imagePath) async {
    if (_disposed) return null;
    final inputImage = InputImage.fromFilePath(imagePath);
    final recognized = await _recognizer.processImage(inputImage);
    final sourceText = recognized.text.trim();
    if (sourceText.isEmpty) return null;
    if (_modelStatus != TranslationModelStatus.ready) {
      // Model henüz hazır değilse ham metni göster, çeviriyi atla —
      // kullanıcı en azından ekranda bir şey okunduğunu görsün.
      return (sourceText, sourceText);
    }
    try {
      final translated = await _translator.translateText(sourceText);
      return (sourceText, translated.trim());
    } catch (e) {
      modelError = '$e';
      return (sourceText, sourceText);
    }
  }

  Future<void> dispose() async {
    _disposed = true;
    await _recognizer.close();
    await _translator.close();
  }
}

/// Yakalanan geçici fotoğraf dosyasını OCR sonrası siler — kamera eklentisinin
/// önbellek klasörü sınırsız büyümesin diye (her kare için bir dosya oluşur).
Future<void> deleteQuietly(String path) async {
  try {
    final file = File(path);
    if (await file.exists()) await file.delete();
  } catch (_) {
    // Silme başarısızsa yok sayılır — işlevsellik için kritik değil, sadece
    // geçici depolama temizliği.
  }
}
