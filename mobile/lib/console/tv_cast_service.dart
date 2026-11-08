// Konsol Modu — "TV'de görün" modu (bkz. docs/console_game_caption_roadmap.md,
// §1.5 ve Faz 5). gamecaptionapp'ın Chromecast/Android TV/Samsung/LG'ye özel
// native uygulamalarının YERİNE, çok daha basit ve test edilebilir bir
// yaklaşım: telefon kendi yerel ağında küçük bir HTTP sunucusu açar, TV'nin
// (veya herhangi bir cihazın) tarayıcısı bu adresi açtığında çeviriyi büyük
// fontla tam ekran gösterir ve saniyede birkaç kez kendini günceller.
//
// Bu, Android TV / Google TV / Samsung / LG'ye özel ayrı mağaza uygulamaları
// YAZMAZ (o, bambaşka bir proje — her platform için ayrı geliştirici hesabı,
// sertifikasyon, ayrı donanım testi gerektirir). Bunun yerine her modern TV'nin
// zaten sahip olduğu web tarayıcısını kullanır — kurulum gerektirmez, ve
// kullanıcı bunu bir laptop'ta bile hemen test edebilir (gerçek bir "smart
// TV" gerekmez). Dezavantajı: TV'nin tarayıcısında adresi elle açması ya da
// göstereceğimiz QR'ı KENDİ telefonunun kamerasıyla okutup linki paylaşması
// gerekebilir — gamecaptionapp'taki gibi TV ekranında QR gösterip telefonla
// okutma akışı, TV'ye ayrı bir uygulama yazmadan birebir uygulanamaz.
//
// Gizlilik: Bu sunucu yalnızca YEREL AĞDA (aynı Wi-Fi) çalışır, hiçbir bulut
// sunucusuna bağlanmaz — AGENTS.md madde 3 ile uyumlu.
import 'dart:convert';
import 'dart:io';

class TvCastService {
  HttpServer? _server;
  String _caption = '';
  String? _url;

  String? get url => _url;
  bool get isRunning => _server != null;

  /// Yeni bir altyazı geldiğinde çağrılır; TV sayfası bir sonraki
  /// yoklamasında (poll) bunu alır.
  void updateCaption(String text) {
    _caption = text;
  }

  /// Yerel HTTP sunucusunu başlatır ve `http://<telefon-ip>:<port>/`
  /// adresini döner. Ağ arayüzü bulunamazsa (ör. Wi-Fi kapalı) `null` döner.
  Future<String?> start() async {
    if (_server != null) return _url;
    final ip = await _localIPv4();
    if (ip == null) return null;
    try {
      final server = await HttpServer.bind(InternetAddress.anyIPv4, 0);
      _server = server;
      _url = 'http://$ip:${server.port}/';
      server.listen(_handle, onError: (_) {});
      return _url;
    } catch (_) {
      return null;
    }
  }

  Future<void> stop() async {
    await _server?.close(force: true);
    _server = null;
    _url = null;
  }

  Future<void> _handle(HttpRequest request) async {
    try {
      if (request.uri.path == '/caption.json') {
        request.response.headers.contentType = ContentType.json;
        request.response.write(jsonEncode({'text': _caption}));
      } else {
        request.response.headers.contentType = ContentType.html;
        request.response.write(_pageHtml);
      }
      await request.response.close();
    } catch (_) {
      // Bağlantı istemci tarafında kesilmiş olabilir — sunucuyu çökertmez.
    }
  }

  static Future<String?> _localIPv4() async {
    try {
      final interfaces = await NetworkInterface.list(
        type: InternetAddressType.IPv4,
        includeLoopback: false,
      );
      for (final interface in interfaces) {
        for (final address in interface.addresses) {
          if (!address.isLoopback) return address.address;
        }
      }
    } catch (_) {
      // Ağ arayüzü listesi okunamadı — başlatma iptal edilir.
    }
    return null;
  }

  static const String _pageHtml = '''
<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TD2 Loot Advisor — Konsol Modu (TV)</title>
<style>
  html, body { margin: 0; height: 100%; background: #090c12; }
  body {
    display: flex; align-items: flex-end; justify-content: center;
    padding-bottom: 6vh; box-sizing: border-box;
  }
  #cap {
    max-width: 90vw;
    background: rgba(0,0,0,.78);
    color: #fff;
    font-family: -apple-system, Segoe UI, Roboto, sans-serif;
    font-size: 5vw;
    font-weight: 600;
    line-height: 1.3;
    text-align: center;
    padding: 1.2vw 2.4vw;
    border-radius: 14px;
  }
  #hint {
    position: fixed; top: 16px; left: 0; right: 0; text-align: center;
    color: #556; font-family: sans-serif; font-size: 14px;
  }
</style>
</head>
<body>
  <div id="hint">TD2 Loot Advisor — Konsol Modu bağlı, çeviri bekleniyor…</div>
  <div id="cap"></div>
<script>
  const cap = document.getElementById('cap');
  const hint = document.getElementById('hint');
  async function tick() {
    try {
      const r = await fetch('/caption.json', {cache: 'no-store'});
      const j = await r.json();
      if (j.text) { cap.textContent = j.text; hint.style.display = 'none'; }
    } catch (e) { /* telefon ağdan düştüyse sessizce yeniden dener */ }
  }
  setInterval(tick, 700);
  tick();
</script>
</body>
</html>
''';
}
