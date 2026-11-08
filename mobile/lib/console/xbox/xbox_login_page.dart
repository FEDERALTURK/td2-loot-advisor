// Xbox doğrudan bağlantı (DENEYSEL) — giriş ve konsol listesi ekranı.
//
// Bu ekran, docs/console_game_caption_roadmap.md'deki "Xbox Doğrudan
// Bağlantı" maddesinin İLK AŞAMASIDIR: Microsoft hesabıyla giriş yapıp
// hesaba kayıtlı Xbox konsollarını listelemek. Bu, XStreaming belgesindeki
// 1.Auth.md (kimlik doğrulama) ve 2.Web.md §2.1 (konsol listesi)
// adımlarının tamamını kapsar.
//
// BURADA OLMAYAN (çok daha büyük, ayrı bir aşama): Gerçek ekran/ses akışı
// (3.Stream.md) — WebRTC SDP/ICE müzakeresi, medya kod çözme, denetleyici
// girdisi gönderimi. Bu, `flutter_webrtc` gibi ek bir paket, haftalarca
// geliştirme ve GERÇEK bir Xbox Series X/S ile test gerektirir; bu oturumda
// kullanıcının böyle bir konsolu yok ve bu kum havuzunda da test edilemez.
// Bu ekran o aşamaya kadar "konsol bulundu, bağlanılabilir durumda" bilgisini
// doğrulamak için bir temel (foundation) niteliğindedir.
//
// Neden "elle yapıştırma" girişi: Gerçek XStreaming istemcileri Microsoft
// girişini bir WebView içinde açıp özel URL şemasını (ms-xal-...://)
// otomatik yakalar. Bu, Android/iOS'ta ayrı bir intent-filter / URL scheme
// kaydı ve WebView paketi gerektirir — kapsamı bu ilk sürüme sığdırmak için
// bilinçli olarak basitleştirildi: kullanıcı sistem tarayıcısında giriş
// yapar ve adres çubuğundaki son (yönlendirilen) adresi yapıştırır. Bu,
// PKCE tabanlı akışlarda "manuel kod yapıştırma" olarak bilinen, güvenli ve
// yaygın bir geçici yöntemdir.
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'xbox_auth_service.dart';
import 'xbox_console_service.dart';
import 'xbox_token_store.dart';

const _bg = Color(0xFF090C12);
const _panel = Color(0xFF121722);
const _orange = Color(0xFFFF6D10);
const _soft = Color(0xFF9AA4B5);

class XboxLoginPage extends StatefulWidget {
  const XboxLoginPage({super.key});

  @override
  State<XboxLoginPage> createState() => _XboxLoginPageState();
}

enum _Step { idle, awaitingRedirect, completing, loggedIn }

class _XboxLoginPageState extends State<XboxLoginPage> {
  final _auth = XboxAuthService();
  final _consoleService = XboxConsoleService();
  late Future<XboxTokenStore> _storeFuture;

  _Step _step = _Step.idle;
  String? _error;
  XboxLoginStart? _started;
  final _redirectController = TextEditingController();

  List<XboxConsole>? _consoles;
  bool _loadingConsoles = false;

  @override
  void initState() {
    super.initState();
    _storeFuture = XboxTokenStore.load().then((store) {
      if (store.hasUserLogin) {
        setState(() => _step = _Step.loggedIn);
        unawaited(_loadConsoles(store));
      }
      return store;
    });
  }

  @override
  void dispose() {
    _auth.dispose();
    _consoleService.dispose();
    _redirectController.dispose();
    super.dispose();
  }

  Future<void> _startLogin() async {
    setState(() {
      _error = null;
      _step = _Step.awaitingRedirect;
    });
    try {
      final store = await _storeFuture;
      final started = await _auth.startLogin(store);
      await store.save();
      _started = started;
      final uri = Uri.parse(started.msaOauthRedirect);
      final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!opened && mounted) {
        setState(() => _error =
            'Giriş adresi açılamadı. Aşağıdaki "Giriş adresini aç" düğmesine tekrar dokunun.');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = _friendlyError(e);
        _step = _Step.idle;
      });
    }
  }

  Future<void> _reopenLoginUrl() async {
    final started = _started;
    if (started == null) return;
    await launchUrl(Uri.parse(started.msaOauthRedirect), mode: LaunchMode.externalApplication);
  }

  Future<void> _completeLogin() async {
    final started = _started;
    if (started == null || _redirectController.text.trim().isEmpty) return;
    setState(() {
      _step = _Step.completing;
      _error = null;
    });
    try {
      final store = await _storeFuture;
      await _auth.completeLogin(
        store: store,
        redirectUrlFromUser: _redirectController.text,
        started: started,
      );
      if (!mounted) return;
      setState(() => _step = _Step.loggedIn);
      unawaited(_loadConsoles(store));
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = _friendlyError(e);
        _step = _Step.awaitingRedirect;
      });
    }
  }

  Future<void> _loadConsoles(XboxTokenStore store) async {
    setState(() => _loadingConsoles = true);
    try {
      final (webToken, uhs) = await _auth.getWebToken(store);
      final consoles = await _consoleService.listConsoles(webToken: webToken, uhs: uhs);
      if (!mounted) return;
      setState(() {
        _consoles = consoles;
        _loadingConsoles = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = _friendlyError(e);
        _loadingConsoles = false;
      });
    }
  }

  Future<void> _logout() async {
    final store = await _storeFuture;
    await store.clear();
    if (!mounted) return;
    setState(() {
      _step = _Step.idle;
      _consoles = null;
      _started = null;
      _redirectController.clear();
    });
  }

  String _friendlyError(Object e) {
    if (e is XboxAuthException) return e.toString();
    return 'Beklenmeyen bir hata oluştu: $e';
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: _bg,
    appBar: AppBar(
      title: const Text('Xbox\'a bağlan (deneysel)'),
      actions: [
        if (_step == _Step.loggedIn)
          IconButton(
            tooltip: 'Çıkış yap',
            onPressed: _logout,
            icon: const Icon(Icons.logout_rounded),
          ),
      ],
    ),
    body: SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _warningBanner(),
            const SizedBox(height: 20),
            if (_error != null) _errorBanner(_error!),
            if (_step == _Step.idle) _idleView(),
            if (_step == _Step.awaitingRedirect) _awaitingRedirectView(),
            if (_step == _Step.completing)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: Center(child: CircularProgressIndicator()),
              ),
            if (_step == _Step.loggedIn) _loggedInView(),
          ],
        ),
      ),
    ),
  );

  Widget _warningBanner() => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: _panel,
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: _orange.withValues(alpha: .4)),
    ),
    child: const Text(
      'Bu özellik DENEYSEL ve henüz gerçek bir Xbox ile test EDİLMEDİ. '
      'Şu an yalnızca Microsoft hesabıyla giriş yapıp hesaba kayıtlı '
      'konsolları listeleyebilirsiniz. Gerçek ekran/ses akışı (oyunu '
      'telefonda görüntüleme) henüz yazılmadı — bu, haftalarca sürecek '
      'ayrı ve çok daha büyük bir aşama.',
      style: TextStyle(color: _soft, fontSize: 13, height: 1.45),
    ),
  );

  Widget _errorBanner(String message) => Container(
    margin: const EdgeInsets.only(bottom: 16),
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: const Color(0xFF3A1414),
      borderRadius: BorderRadius.circular(10),
    ),
    child: Text(message, style: const TextStyle(color: Color(0xFFFFB4A9), fontSize: 13)),
  );

  Widget _idleView() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Text(
        'Microsoft hesabınızla giriş yapın. Sistem tarayıcınız açılacak; '
        'giriş yaptıktan sonra sayfa "ms-xal-...://auth" ile başlayan bir '
        'adrese yönlenmeye çalışacak (tarayıcı bunu açamayabilir, bu normal) '
        '— o anda adres çubuğundaki TAM adresi kopyalayıp bir sonraki adımda '
        'buraya yapıştıracaksınız.',
        style: TextStyle(color: _soft, height: 1.45),
      ),
      const SizedBox(height: 16),
      FilledButton.icon(
        onPressed: _startLogin,
        style: FilledButton.styleFrom(backgroundColor: _orange),
        icon: const Icon(Icons.login_rounded),
        label: const Text('Microsoft ile giriş yap'),
      ),
    ],
  );

  Widget _awaitingRedirectView() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Text(
        'Tarayıcıda Microsoft hesabınızla giriş yapın. Giriş tamamlanınca '
        'yönlendirileceğiniz adresi (ms-xal-...://auth/?code=...&state=...) '
        'kopyalayıp aşağıya yapıştırın.',
        style: TextStyle(color: _soft, height: 1.45),
      ),
      const SizedBox(height: 10),
      OutlinedButton.icon(
        onPressed: _reopenLoginUrl,
        icon: const Icon(Icons.open_in_browser_rounded),
        label: const Text('Giriş adresini tekrar aç'),
      ),
      const SizedBox(height: 16),
      TextField(
        controller: _redirectController,
        minLines: 2,
        maxLines: 4,
        style: const TextStyle(color: Colors.white, fontSize: 13),
        decoration: InputDecoration(
          filled: true,
          fillColor: _panel,
          hintText: 'ms-xal-000000004c20a908://auth/?code=...&state=...',
          hintStyle: const TextStyle(color: _soft, fontSize: 12),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        ),
      ),
      const SizedBox(height: 14),
      FilledButton.icon(
        onPressed: _completeLogin,
        style: FilledButton.styleFrom(backgroundColor: _orange),
        icon: const Icon(Icons.check_rounded),
        label: const Text('Girişi tamamla'),
      ),
    ],
  );

  Widget _loggedInView() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Row(
        children: [
          Icon(Icons.check_circle_rounded, color: Color(0xFF3DDC84)),
          SizedBox(width: 8),
          Text('Microsoft hesabına giriş yapıldı', style: TextStyle(color: Colors.white)),
        ],
      ),
      const SizedBox(height: 18),
      const Text('Hesaba kayıtlı konsollar', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
      const SizedBox(height: 10),
      if (_loadingConsoles) const Center(child: CircularProgressIndicator()),
      if (!_loadingConsoles && (_consoles?.isEmpty ?? false))
        const Text(
          'Bu hesaba kayıtlı konsol bulunamadı. Xbox konsolunuzda '
          'Ayarlar → Hesap → Uzaktan erişim/oynatım bölümünden bu '
          'hesabın yetkili olduğundan emin olun.',
          style: TextStyle(color: _soft),
        ),
      if (_consoles != null)
        for (final c in _consoles!)
          Card(
            color: _panel,
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
              leading: const Icon(Icons.videogame_asset_rounded, color: _orange),
              title: Text(c.name, style: const TextStyle(color: Colors.white)),
              subtitle: Text(
                '${c.consoleType} · ${c.powerState} · ${c.id}',
                style: const TextStyle(color: _soft, fontSize: 12),
              ),
            ),
          ),
    ],
  );
}
