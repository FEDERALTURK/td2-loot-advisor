// Mikrofon yakalama servisi — TV/konsoldan çıkan sesi ODA SESİ olarak
// mikrofonla dinler (telefonun kendi çalan sesini değil). record paketinin
// startStream() akışı ham LINEAR16 (PCM16) örnekleri verir; bunlar WAV
// başlığı eklemeye gerek olmadan doğrudan Google Cloud Speech-to-Text
// REST API'sine (encoding: LINEAR16) gönderilebilir.
//
// Ses hiçbir zaman yerel diske kalıcı olarak yazılmaz; yalnızca kısa süreli
// bellek arabelleğinde tutulup ilgili parça tamamlanınca buluta gönderilir ve
// arabellek temizlenir (AGENTS.md madde 3 — ekran/ses verisi kullanıcı açık
// izni olmadan gönderilmez; burada gönderim kullanıcının açıkça başlattığı
// "dinlemeyi başlat" eylemine bağlıdır).
import 'dart:async';
import 'dart:typed_data';

import 'package:record/record.dart';

/// Google Cloud Speech-to-Text'in LINEAR16 için beklediği örnekleme hızı.
const int micSampleRateHz = 16000;

/// Bir ses parçasının yaklaşık süresi — gecikme/doğruluk dengesi için seçildi.
/// Bu, gerçek düşük-gecikmeli sürekli akış (streaming recognize) DEĞİL; her
/// parça tamamlanınca ayrı bir REST isteği gönderiliyor (bkz. README.md
/// "Bilinen sınırlamalar").
const Duration micChunkDuration = Duration(seconds: 4);

class MicCaptureService {
  final AudioRecorder _recorder = AudioRecorder();
  StreamSubscription<Uint8List>? _subscription;
  final BytesBuilder _buffer = BytesBuilder(copy: false);
  Timer? _chunkTimer;

  bool get isRecording => _subscription != null;

  Future<bool> hasPermission() => _recorder.hasPermission();

  /// Dinlemeyi başlatır. [onChunk], her ~[micChunkDuration] sürede bir
  /// birikmiş ham PCM16 verisiyle çağrılır.
  Future<void> start({required void Function(Uint8List pcm16) onChunk}) async {
    if (isRecording) return;
    if (!await hasPermission()) {
      throw StateError('Mikrofon izni verilmedi.');
    }

    final stream = await _recorder.startStream(
      const RecordConfig(
        encoder: AudioEncoder.pcm16bits,
        sampleRate: micSampleRateHz,
        numChannels: 1,
        autoGain: true,
        noiseSuppress: true,
      ),
    );

    _subscription = stream.listen((data) {
      _buffer.add(data);
    });

    _chunkTimer = Timer.periodic(micChunkDuration, (_) {
      if (_buffer.isEmpty) return;
      final bytes = _buffer.takeBytes();
      onChunk(bytes);
    });
  }

  Future<void> stop() async {
    _chunkTimer?.cancel();
    _chunkTimer = null;
    await _subscription?.cancel();
    _subscription = null;
    if (await _recorder.isRecording()) {
      await _recorder.stop();
    }
    _buffer.clear();
  }

  void dispose() {
    _chunkTimer?.cancel();
    unawaited(_subscription?.cancel());
    unawaited(_recorder.dispose());
  }
}
