import 'package:flutter/material.dart';

import '../ui/theme.dart';
import 'api_key_store.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _store = ApiKeyStore();
  final _controller = TextEditingController();
  bool _obscure = true;
  bool _loading = true;
  bool _saved = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final key = await _store.read();
    if (!mounted) return;
    setState(() {
      _controller.text = key ?? '';
      _loading = false;
    });
  }

  Future<void> _save() async {
    await _store.write(_controller.text.trim());
    if (!mounted) return;
    setState(() => _saved = true);
  }

  Future<void> _clear() async {
    await _store.clear();
    if (!mounted) return;
    setState(() {
      _controller.clear();
      _saved = false;
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ayarlar')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Google Cloud API Anahtarı',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'GAMLETSOL, TV/konsol sesini metne çevirmek için Google Cloud '
                    'Speech-to-Text ve çeviri için Cloud Translation API kullanır. '
                    'Bu iki API için etkinleştirilmiş bir API anahtarı gerekir — '
                    'Google Cloud Console → Kimlik Bilgileri bölümünden oluşturulur. '
                    'Anahtar bu cihazda güvenli depoda (Android Keystore) saklanır, '
                    'hiçbir sunucuya veya loga gönderilmez.',
                    style: TextStyle(color: GamletsolColors.soft),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _controller,
                    obscureText: _obscure,
                    decoration: InputDecoration(
                      labelText: 'API anahtarı',
                      filled: true,
                      fillColor: GamletsolColors.panel,
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      suffixIcon: IconButton(
                        icon: Icon(_obscure ? Icons.visibility : Icons.visibility_off),
                        onPressed: () => setState(() => _obscure = !_obscure),
                      ),
                    ),
                    onChanged: (_) => setState(() => _saved = false),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      ElevatedButton(onPressed: _save, child: const Text('Kaydet')),
                      const SizedBox(width: 12),
                      TextButton(onPressed: _clear, child: const Text('Temizle')),
                    ],
                  ),
                  if (_saved) ...[
                    const SizedBox(height: 12),
                    const Text('Kaydedildi.', style: TextStyle(color: GamletsolColors.green)),
                  ],
                  const SizedBox(height: 24),
                  const Divider(),
                  const SizedBox(height: 12),
                  const Text(
                    'Bulut API kullanıldığı için ses/metin veri işleme sırasında '
                    'Google\'ın sunucularına gönderilir ve bu çağrılar ücretlidir '
                    '(Google Cloud fiyatlandırmasına bakın). AGENTS.md\'deki '
                    '"ekran/ses verisi kullanıcı izni olmadan uzak hizmete '
                    'gönderilmez" ilkesi burada açıkça sağlanıyor: bu ekrana API '
                    'anahtarı girip "Dinlemeyi Başlat"a basmak, o açık izindir.',
                    style: TextStyle(color: GamletsolColors.soft, fontSize: 12),
                  ),
                ],
              ),
            ),
    );
  }
}
