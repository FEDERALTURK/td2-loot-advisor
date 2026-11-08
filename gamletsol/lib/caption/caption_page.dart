import 'dart:async';

import 'package:flutter/material.dart';

import '../settings/api_key_store.dart';
import '../settings/bcp47.dart';
import '../settings/language_option.dart';
import '../settings/settings_page.dart';
import '../ui/theme.dart';
import 'caption_line.dart';
import 'caption_session.dart';

class CaptionPage extends StatefulWidget {
  const CaptionPage({super.key});

  @override
  State<CaptionPage> createState() => _CaptionPageState();
}

class _CaptionPageState extends State<CaptionPage> {
  final _apiKeyStore = ApiKeyStore();

  String _sourceCode = 'en'; // TV/konsolda konuşulan dil
  String _targetCode = 'tr'; // kullanıcının görmek istediği dil

  CaptionSession? _session;
  StreamSubscription<CaptionLine>? _linesSub;
  StreamSubscription<String>? _errorsSub;

  final List<CaptionLine> _history = [];
  String? _lastError;
  bool _starting = false;

  bool get _isRunning => _session?.isRunning ?? false;

  @override
  void dispose() {
    _linesSub?.cancel();
    _errorsSub?.cancel();
    unawaited(_session?.dispose());
    super.dispose();
  }

  Future<void> _toggle() async {
    if (_isRunning) {
      await _stop();
      return;
    }
    await _start();
  }

  Future<void> _start() async {
    setState(() {
      _starting = true;
      _lastError = null;
    });

    final apiKey = await _apiKeyStore.read();
    if (apiKey == null || apiKey.trim().isEmpty) {
      setState(() {
        _starting = false;
        _lastError = 'Önce Ayarlar\'dan bir Google Cloud API anahtarı gir.';
      });
      return;
    }

    final session = CaptionSession(
      apiKey: apiKey.trim(),
      sourceLanguageCode: speechLocaleFor(_sourceCode),
      targetLanguageCode: _targetCode,
    );

    _linesSub = session.lines.listen((line) {
      setState(() {
        _history.insert(0, line);
        if (_history.length > 50) _history.removeLast();
      });
    });
    _errorsSub = session.errors.listen((message) {
      setState(() => _lastError = message);
    });

    try {
      await session.start();
      setState(() {
        _session = session;
        _starting = false;
      });
    } catch (error) {
      setState(() {
        _starting = false;
        _lastError = error.toString();
      });
      await session.dispose();
    }
  }

  Future<void> _stop() async {
    final session = _session;
    _session = null;
    await _linesSub?.cancel();
    await _errorsSub?.cancel();
    await session?.dispose();
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('GAMLETSOL'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: 'Ayarlar',
            onPressed: _isRunning
                ? null
                : () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const SettingsPage()),
                    ),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: _LanguageDropdown(
                    label: 'TV/konsol sesi',
                    value: _sourceCode,
                    enabled: !_isRunning,
                    onChanged: (v) => setState(() => _sourceCode = v),
                  ),
                ),
                const SizedBox(width: 12),
                const Icon(Icons.arrow_forward, color: GamletsolColors.soft),
                const SizedBox(width: 12),
                Expanded(
                  child: _LanguageDropdown(
                    label: 'Göster',
                    value: _targetCode,
                    enabled: !_isRunning,
                    onChanged: (v) => setState(() => _targetCode = v),
                  ),
                ),
              ],
            ),
          ),
          if (_lastError != null)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.symmetric(horizontal: 16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: GamletsolColors.red.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: GamletsolColors.red),
              ),
              child: Text(_lastError!, style: const TextStyle(color: GamletsolColors.red)),
            ),
          const SizedBox(height: 12),
          Expanded(
            child: _history.isEmpty
                ? Center(
                    child: Text(
                      _isRunning
                          ? 'Dinleniyor… TV/konsoldan konuşma bekleniyor.'
                          : 'Başlamak için aşağıdaki düğmeye bas.',
                      style: const TextStyle(color: GamletsolColors.soft),
                      textAlign: TextAlign.center,
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: _history.length,
                    itemBuilder: (context, index) {
                      final line = _history[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                line.translated,
                                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                line.original,
                                style: const TextStyle(color: GamletsolColors.soft, fontSize: 13),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _starting ? null : _toggle,
                icon: Icon(_isRunning ? Icons.stop : Icons.mic),
                label: Text(_starting
                    ? 'Başlatılıyor…'
                    : (_isRunning ? 'Dinlemeyi Durdur' : 'Dinlemeyi Başlat')),
                style: _isRunning
                    ? ElevatedButton.styleFrom(backgroundColor: GamletsolColors.red)
                    : null,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LanguageDropdown extends StatelessWidget {
  const _LanguageDropdown({
    required this.label,
    required this.value,
    required this.enabled,
    required this.onChanged,
  });

  final String label;
  final String value;
  final bool enabled;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      initialValue: value,
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: GamletsolColors.panel,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      ),
      items: LanguageOption.all
          .map((o) => DropdownMenuItem(value: o.code, child: Text(o.nativeName)))
          .toList(),
      onChanged: enabled ? (v) => onChanged(v!) : null,
    );
  }
}
