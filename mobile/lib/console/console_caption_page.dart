// Konsol Modu — "Game Caption" tarzı kamera modu (bkz.
// docs/console_game_caption_roadmap.md, §1.5 ve Faz 1).
//
// Telefonun arka kamerası bir TV/monitöre doğrultulur; ekranda ne yazıyorsa
// (oyun altyazısı, görev metni, menü) periyodik olarak fotoğraflanıp cihaz
// üstünde OCR ile okunur, İngilizce→Türkçe çevrilir ve alt kısımda Xbox'ın
// resmi altyazı stiline benzer bir kutuda gösterilir; istenirse sesli de
// okunur (TTS). ASR (konuşma tanıma) YOK — gamecaptionapp.com'un kendi
// tanımladığı akışla aynı basitleştirme (bkz. yol haritası §1.5): yalnızca
// ekrandaki YAZI okunur, ses dinlenmez.
//
// Konsol markası/modeli bu modda önemsiz — Xbox Series X/S, PS4/PS5, PC veya
// bir film/dizi ekranı fark etmez; "ekranda ne görünüyorsa" okunur. Bu yüzden
// Xbox'a özel bir protokol/SDK gerektirmez (bkz. yol haritasındaki Faz 3a ile
// karşılaştırma).
import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:qr_flutter/qr_flutter.dart';

import 'console_translate_service.dart';
import 'tv_cast_service.dart';
import 'xbox/xbox_login_page.dart';

const _bg = Color(0xFF090C12);
const _panel = Color(0xFF121722);
const _orange = Color(0xFFFF6D10);
const _soft = Color(0xFF9AA4B5);
const _green = Color(0xFF3DDC84);

/// Yakalama döngüsünün periyodu. gamecaptionapp tarzı uygulamalarda altyazı
/// saniyede birkaç kez değişmez; 1.6 sn hem pil/performans hem de art arda
/// aynı altyazıyı yeniden OCR/çeviri hattından geçirmemek için makul bir denge.
const _captureInterval = Duration(milliseconds: 1600);

class ConsoleCaptionPage extends StatefulWidget {
  const ConsoleCaptionPage({super.key});

  @override
  State<ConsoleCaptionPage> createState() => _ConsoleCaptionPageState();
}

class _ConsoleCaptionPageState extends State<ConsoleCaptionPage>
    with WidgetsBindingObserver {
  CameraController? _controller;
  Future<void>? _initFuture;
  String? _initError;

  final _service = ConsoleTranslateService();
  final _tts = FlutterTts();
  final _tvCast = TvCastService();

  bool _scanning = false;
  bool _busy = false;
  Timer? _loopTimer;

  String? _sourceText;
  String? _translatedText;
  bool _ttsEnabled = false;
  String? _lastSpoken;
  bool _tvCastBusy = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _tts.setLanguage('tr-TR');
    _initFuture = _initCamera();
    // Çeviri modeli indirmesi kamerayla paralel başlar — ikisi birbirini
    // beklemek zorunda değil, UI model durumunu ayrıca gösterir.
    _service.ensureModelReady().then((_) {
      if (mounted) setState(() {});
    });
  }

  Future<void> _initCamera() async {
    setState(() => _initError = null);
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        setState(() => _initError = 'Bu cihazda kullanılabilir bir kamera bulunamadı.');
        return;
      }
      final back = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      final controller = CameraController(
        back,
        ResolutionPreset.medium,
        enableAudio: false,
      );
      await controller.initialize();
      if (!mounted) {
        await controller.dispose();
        return;
      }
      setState(() => _controller = controller);
    } on CameraException catch (e) {
      setState(
        () => _initError = e.code == 'CameraAccessDenied' || e.code == 'CameraAccessDeniedWithoutPrompt'
            ? 'Kamera izni verilmedi. Telefon Ayarları → Uygulamalar → TD2 Loot Advisor → İzinler bölümünden kamerayı açıp tekrar deneyin.'
            : 'Kamera başlatılamadı: ${e.description ?? e.code}',
      );
    } catch (e) {
      setState(() => _initError = 'Kamera başlatılamadı: $e');
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) return;
    if (state == AppLifecycleState.inactive || state == AppLifecycleState.paused) {
      _stopScanning();
      controller.dispose();
      _controller = null;
    } else if (state == AppLifecycleState.resumed) {
      _initFuture = _initCamera();
      setState(() {});
    }
  }

  void _toggleScanning() {
    if (_scanning) {
      _stopScanning();
    } else {
      _startScanning();
    }
  }

  void _startScanning() {
    if (_controller == null || !_controller!.value.isInitialized) return;
    setState(() => _scanning = true);
    _loopTimer?.cancel();
    _loopTimer = Timer.periodic(_captureInterval, (_) => _captureTick());
  }

  void _stopScanning() {
    _loopTimer?.cancel();
    _loopTimer = null;
    if (mounted) setState(() => _scanning = false);
  }

  Future<void> _captureTick() async {
    final controller = _controller;
    if (_busy || controller == null || !controller.value.isInitialized) return;
    if (controller.value.isTakingPicture) return;
    _busy = true;
    String? path;
    try {
      final file = await controller.takePicture();
      path = file.path;
      final result = await _service.recognizeAndTranslate(path);
      if (!mounted) return;
      if (result != null) {
        final (source, translated) = result;
        setState(() {
          _sourceText = source;
          _translatedText = translated;
        });
        if (_tvCast.isRunning) _tvCast.updateCaption(translated);
        if (_ttsEnabled && translated.isNotEmpty && translated != _lastSpoken) {
          _lastSpoken = translated;
          unawaited(_tts.speak(translated));
        }
      }
    } catch (_) {
      // Tek bir karenin OCR/çeviri hatası sessizce atlanır — bir sonraki
      // tur normal şekilde devam eder; kullanıcıya her kare için hata
      // göstermek deneyimi bozar.
    } finally {
      if (path != null) unawaited(deleteQuietly(path));
      _busy = false;
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _loopTimer?.cancel();
    _controller?.dispose();
    _service.dispose();
    _tts.stop();
    _tvCast.stop();
    super.dispose();
  }

  Future<void> _toggleTvCast() async {
    if (_tvCast.isRunning) {
      await _tvCast.stop();
      if (mounted) setState(() {});
      return;
    }
    setState(() => _tvCastBusy = true);
    final url = await _tvCast.start();
    if (!mounted) return;
    setState(() => _tvCastBusy = false);
    if (url == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Yerel ağ sunucusu başlatılamadı. Telefon Wi-Fi\'ye bağlı mı kontrol edin.',
          ),
        ),
      );
      return;
    }
    setState(() {});
    if (!mounted) return;
    _showTvCastDialog(url);
  }

  void _showTvCastDialog(String url) => showDialog<void>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: const Text('TV\'de görün'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'TV\'nizin (veya aynı Wi-Fi\'deki başka bir cihazın) tarayıcısından '
            'aşağıdaki adresi açın. Çeviri orada büyük fontla, canlı olarak '
            'güncellenir.\n\n'
            'Not: TV tarayıcısı kamerayla QR okutamıyorsa adresi uzaktan '
            'kumandayla elle yazabilirsiniz.',
            style: TextStyle(color: _soft, fontSize: 13, height: 1.4),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(10),
            ),
            child: QrImageView(data: url, size: 180),
          ),
          const SizedBox(height: 12),
          SelectableText(
            url,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(dialogContext),
          child: const Text('Kapat'),
        ),
      ],
    ),
  );

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: _bg,
    appBar: AppBar(
      title: const Text('Konsol Modu'),
      actions: [
        IconButton(
          tooltip: 'Xbox\'a bağlan (deneysel)',
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const XboxLoginPage()),
          ),
          icon: const Icon(Icons.videogame_asset_rounded),
        ),
        IconButton(
          tooltip: 'Nasıl çalışır?',
          onPressed: () => _showInfo(context),
          icon: const Icon(Icons.info_outline_rounded),
        ),
      ],
    ),
    body: SafeArea(
      child: Column(
        children: [
          Expanded(child: _cameraArea()),
          _controlsBar(),
        ],
      ),
    ),
  );

  Widget _cameraArea() {
    if (_initError != null) {
      return _errorState(_initError!);
    }
    return FutureBuilder<void>(
      future: _initFuture,
      builder: (context, snapshot) {
        final controller = _controller;
        if (controller == null || !controller.value.isInitialized) {
          return const Center(child: CircularProgressIndicator());
        }
        return Stack(
          fit: StackFit.expand,
          children: [
            Center(
              child: AspectRatio(
                aspectRatio: controller.value.aspectRatio,
                child: CameraPreview(controller),
              ),
            ),
            _alignmentGuide(),
            if (_translatedText != null) _captionBar(),
          ],
        );
      },
    );
  }

  Widget _errorState(String message) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.no_photography_rounded, color: _soft, size: 42),
          const SizedBox(height: 14),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(color: _soft, height: 1.45),
          ),
          const SizedBox(height: 18),
          FilledButton.icon(
            onPressed: () => setState(() => _initFuture = _initCamera()),
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Tekrar dene'),
          ),
        ],
      ),
    ),
  );

  /// gamecaptionapp'ın "altyazının yeşil kutunun içinde kaldığından emin
  /// olun" hizalama rehberiyle aynı fikir — yalnızca görsel bir kılavuz,
  /// OCR'ı bu bölgeyle sınırlamaz (tüm kare okunur, bkz. yol haritası §1.5
  /// ve 5/Faz 1 notu: kırpma yerine tam kare OCR tercih edildi).
  Widget _alignmentGuide() => Align(
    alignment: const Alignment(0, 0.62),
    child: FractionallySizedBox(
      widthFactor: 0.86,
      heightFactor: 0.16,
      child: Container(
        decoration: BoxDecoration(
          border: Border.all(color: _green, width: 2),
          borderRadius: BorderRadius.circular(10),
        ),
        alignment: Alignment.topCenter,
        child: Transform.translate(
          offset: const Offset(0, -26),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: _green.withValues(alpha: .9),
              borderRadius: BorderRadius.circular(6),
            ),
            child: const Text(
              'Altyazıyı bu kutunun içine hizala',
              style: TextStyle(
                color: Colors.black,
                fontSize: 11,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
      ),
    ),
  );

  /// Xbox'ın resmi altyazı stil kılavuzuna (XAccessibility Guidelines) göre
  /// tasarlandı: ekranın altında yarı saydam siyah kutu, okunaklı büyük font.
  /// Bkz. yol haritası §1.4.
  Widget _captionBar() => Align(
    alignment: const Alignment(0, 0.9),
    child: Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: .78),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_sourceText != null && _sourceText != _translatedText)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text(
                _sourceText!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: _soft, fontSize: 12, height: 1.2),
              ),
            ),
          Text(
            _translatedText ?? '',
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 19,
              fontWeight: FontWeight.w600,
              height: 1.3,
            ),
          ),
        ],
      ),
    ),
  );

  Widget _controlsBar() => Container(
    color: _panel,
    padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                _modelStatusLabel(),
                style: const TextStyle(color: _soft, fontSize: 12),
              ),
            ),
            const Icon(Icons.record_voice_over_rounded, color: _soft, size: 18),
            const SizedBox(width: 6),
            const Text('Sesli oku', style: TextStyle(color: _soft, fontSize: 12)),
            Switch(
              value: _ttsEnabled,
              onChanged: (v) => setState(() => _ttsEnabled = v),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _tvCastBusy ? null : _toggleTvCast,
                icon: _tvCastBusy
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Icon(
                        _tvCast.isRunning
                            ? Icons.cast_connected_rounded
                            : Icons.cast_rounded,
                      ),
                label: Text(_tvCast.isRunning ? 'TV yayınını durdur' : 'TV\'de görün'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: FilledButton.icon(
                onPressed: _controller == null ? null : _toggleScanning,
                style: FilledButton.styleFrom(
                  backgroundColor: _scanning ? const Color(0xFFB3261E) : _orange,
                ),
                icon: Icon(_scanning ? Icons.stop_rounded : Icons.play_arrow_rounded),
                label: Text(_scanning ? 'Durdur' : 'Taramayı başlat'),
              ),
            ),
          ],
        ),
      ],
    ),
  );

  String _modelStatusLabel() {
    switch (_service.modelStatus) {
      case TranslationModelStatus.unknown:
      case TranslationModelStatus.checking:
        return 'Çeviri modeli kontrol ediliyor…';
      case TranslationModelStatus.downloading:
        return 'Çeviri modeli indiriliyor (bir kerelik, ~30 MB)…';
      case TranslationModelStatus.ready:
        return 'Çeviri modeli hazır — tamamen cihaz üstünde çalışıyor';
      case TranslationModelStatus.error:
        return 'Çeviri modeli indirilemedi — ham İngilizce metin gösterilecek';
    }
  }

  void _showInfo(BuildContext context) => showDialog<void>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: const Text('Konsol Modu nedir?'),
      content: const Text(
        'Telefonun arka kamerasını TV/monitöre doğrult. Xbox, PlayStation, PC '
        'veya herhangi bir ekrandaki İngilizce yazı (oyun altyazısı, görev '
        'metni, menü) periyodik olarak okunur ve Türkçeye çevrilip altta '
        'gösterilir. Her şey telefonda çalışır — görüntü hiçbir sunucuya '
        'gönderilmez, yalnızca çeviri modeli ilk seferde bir kez indirilir.\n\n'
        'Konuşulan ses DİNLENMEZ — yalnızca ekrandaki yazı okunur.',
        style: TextStyle(height: 1.45),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(dialogContext),
          child: const Text('Anladım'),
        ),
      ],
    ),
  );
}
