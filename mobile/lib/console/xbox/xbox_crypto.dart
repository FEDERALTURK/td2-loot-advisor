// Xbox doğrudan bağlantı (deneysel) — kimlik doğrulama imzalama katmanı.
//
// KAYNAK: Bu dosyadaki protokol detayları, XStreaming projesinin (MIT
// lisanslı, GiGanTe71/XStreaming) docs/1.Auth.md belgesinden satır satır
// doğrulanarak alınmıştır — tahmin edilmemiştir. Xbox Live, cihaz belirteci
// (device token) isteklerini imzalamak için standart bir JWS/JOSE akışı
// DEĞİL, özel bir ikili (binary) imza şeması kullanıyor:
//
//   1) EC P-256 anahtar çifti (bir oturum boyunca sabit kalır).
//   2) İmzalanacak arabellek (buffer):
//        [int32 BE version=1][1 bayt 0 dolgu]
//        [uint64 BE Windows epoch zaman damgası (100ns birim, 1601'den)]
//        [1 bayt 0 dolgu]
//        [null-sonlu 'POST'][null-sonlu path][null-sonlu authToken]
//        [null-sonlu payload]
//   3) Bu arabellek SHA-256 ile özetlenip ECDSA ile imzalanır — ancak imza
//      standart DER kodlamasında DEĞİL, "IEEE P1363" ham (raw) r||s
//      formatında olmalı (her biri 32 bayt, büyük-endian, gerekirse sıfır
//      dolgulu). Node.js tarafında bu `dsaEncoding: 'ieee-p1363'` ile
//      sağlanıyor.
//   4) Son `Signature` HTTP başlığı: [int32 BE version=1][uint64 BE zaman
//      damgası][ham imza bayt dizisi] — tamamı base64.
//
// Dart'ın resmi `package:crypto` paketi ECDSA desteklemiyor (yalnız özet/HMAC).
// `package:pointycastle`'ın gerçek kaynağı (bcgit/pc-dart) klonlanıp
// ECDSASigner.generateSignature()'ın zaten ECSignature(r, s) yani ham r/s
// döndürdüğü (DER değil) doğrulandı — bu yüzden bu şema için doğru araç.
//
// NOT (dürüstlük ilkesi — bkz. AGENTS.md): Bu dosya gerçek bir Xbox Live
// sunucusuna karşı HENÜZ test edilmedi. Bu oturumda ne gerçek bir Microsoft
// hesabıyla interaktif girişi ne de bir Xbox konsolunu test etme imkânı var.
// Kod, belgelenen protokolle bayt-bayt eşleşecek şekilde dikkatle yazıldı,
// ama "çalıştığı doğrulandı" iddiası YALNIZCA gerçek bir hesapla gerçek bir
// girişten sonra yapılabilir.
import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';

import 'package:pointycastle/export.dart';

/// EC P-256 JWK anahtar çifti (JOSE `x`/`y`/`d` alanları base64url, dolgusuz).
class XboxJwtKeys {
  XboxJwtKeys({
    required this.privateKey,
    required this.publicKey,
    required this.x,
    required this.y,
    required this.d,
  });

  final ECPrivateKey privateKey;
  final ECPublicKey publicKey;
  final String x;
  final String y;
  final String d;

  Map<String, String> toJwk() => {
        'kty': 'EC',
        'crv': 'P-256',
        'x': x,
        'y': y,
        'd': d,
      };

  /// JSON'dan geri yükleme (yalnız d/x/y saklanır yeterli; burada d'den
  /// yeniden private key kurulur, x/y doğrulama amaçlı yeniden hesaplanmaz —
  /// zaten orijinal x/y ile aynı d'den üretildiler).
  factory XboxJwtKeys.fromJwk(Map<String, dynamic> jwk) {
    final domain = ECDomainParameters('prime256v1');
    final d = _b64urlToBigInt(jwk['d'] as String);
    final priv = ECPrivateKey(d, domain);
    final q = domain.G * d;
    final pub = ECPublicKey(q, domain);
    return XboxJwtKeys(
      privateKey: priv,
      publicKey: pub,
      x: jwk['x'] as String,
      y: jwk['y'] as String,
      d: jwk['d'] as String,
    );
  }

  static BigInt _b64urlToBigInt(String b64url) {
    final bytes = base64Url.decode(_pad(b64url));
    return _bytesToBigInt(bytes);
  }
}

/// Yeni bir EC P-256 anahtar çifti üretir (bkz. 1.Auth.md §1.1).
XboxJwtKeys generateXboxJwtKeys() {
  final domain = ECDomainParameters('prime256v1');
  final keyGen = ECKeyGenerator();
  keyGen.init(ParametersWithRandom(
    ECKeyGeneratorParameters(domain),
    _secureRandom(),
  ));
  final pair = keyGen.generateKeyPair();
  final priv = pair.privateKey;
  final pub = pair.publicKey;

  final x = pub.Q!.x!.toBigInteger()!;
  final y = pub.Q!.y!.toBigInteger()!;
  final d = priv.d!;

  return XboxJwtKeys(
    privateKey: priv,
    publicKey: pub,
    x: _b64urlNoPad(_bigIntToBytes(x, 32)),
    y: _b64urlNoPad(_bigIntToBytes(y, 32)),
    d: _b64urlNoPad(_bigIntToBytes(d, 32)),
  );
}

/// 1.Auth.md §1.2 — istek imzası (Signature HTTP başlığı, base64).
///
/// [path] yalnızca URL'nin yol kısmı olmalı (ör. `/device/authenticate`),
/// sorgu dizesi olmadan — Node örneğindeki `new URL(url).pathname` ile aynı.
String signXboxRequest({
  required XboxJwtKeys keys,
  required String path,
  required String authorizationToken,
  required String payload,
}) {
  // Windows/NT epoch (1601-01-01) tabanlı 100ns birimli zaman damgası.
  final unixSeconds = DateTime.now().toUtc().millisecondsSinceEpoch ~/ 1000;
  final windowsTimestamp =
      (BigInt.from(unixSeconds) + BigInt.from(11644473600)) *
          BigInt.from(10000000);

  final pathBytes = utf8.encode(path);
  final authBytes = utf8.encode(authorizationToken);
  final payloadBytes = utf8.encode(payload);

  // [int32 ver][1 dolgu][uint64 ts][1 dolgu]['POST'\0][path\0][auth\0][payload\0]
  final buf = BytesBuilder();
  buf.add(_int32be(1));
  buf.addByte(0);
  buf.add(_uint64be(windowsTimestamp));
  buf.addByte(0);
  buf.add(utf8.encode('POST'));
  buf.addByte(0);
  buf.add(pathBytes);
  buf.addByte(0);
  buf.add(authBytes);
  buf.addByte(0);
  buf.add(payloadBytes);
  buf.addByte(0);

  final message = buf.toBytes();

  final signer = ECDSASigner(SHA256Digest());
  signer.init(
    true,
    ParametersWithRandom(PrivateKeyParameter(keys.privateKey), _secureRandom()),
  );
  final sig = signer.generateSignature(message) as ECSignature;

  // IEEE P1363 ham imza: r (32B BE) || s (32B BE).
  final rawSig = Uint8List(64)
    ..setRange(0, 32, _bigIntToBytes(sig.r, 32))
    ..setRange(32, 64, _bigIntToBytes(sig.s, 32));

  // Son başlık: [int32 ver][uint64 ts][imza].
  final header = BytesBuilder();
  header.add(_int32be(1));
  header.add(_uint64be(windowsTimestamp));
  header.add(rawSig);

  return base64.encode(header.toBytes());
}

/// 1.Auth.md §1.4 — PKCE code challenge/verifier.
class XboxCodeChallenge {
  XboxCodeChallenge({required this.value, required this.verifier})
      : method = 'S256';

  final String value;
  final String method;
  final String verifier;
}

XboxCodeChallenge generateXboxCodeChallenge() {
  final rnd = Random.secure();
  final verifierBytes = Uint8List.fromList(
    List<int>.generate(32, (_) => rnd.nextInt(256)),
  );
  final verifier = _b64urlNoPad(verifierBytes);
  final challengeBytes = _sha256(utf8.encode(verifier));
  return XboxCodeChallenge(
    value: _b64urlNoPad(Uint8List.fromList(challengeBytes)),
    verifier: verifier,
  );
}

/// 1.Auth.md §1.5 — 64 baytlık rastgele `state` (standart base64, + / ve =
/// içerebilir — Node `Buffer.toString('base64')` ile aynı, base64url değil).
String generateXboxState() {
  final rnd = Random.secure();
  final bytes = Uint8List.fromList(List<int>.generate(64, (_) => rnd.nextInt(256)));
  return base64.encode(bytes);
}

/// Rastgele UUID v4 üretir (Properties.Id / Properties.SerialNumber için).
String generateUuidV4() {
  final rnd = Random.secure();
  final bytes = Uint8List.fromList(List<int>.generate(16, (_) => rnd.nextInt(256)));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-'
      '${hex.substring(16, 20)}-${hex.substring(20, 32)}';
}

// --- yardımcılar ------------------------------------------------------

SecureRandom _secureRandom() {
  final secureRandom = FortunaRandom();
  final seedSource = Random.secure();
  final seeds = Uint8List.fromList(List<int>.generate(32, (_) => seedSource.nextInt(256)));
  secureRandom.seed(KeyParameter(seeds));
  return secureRandom;
}

List<int> _sha256(List<int> data) {
  final digest = SHA256Digest();
  final out = Uint8List(digest.digestSize);
  digest.update(Uint8List.fromList(data), 0, data.length);
  digest.doFinal(out, 0);
  return out;
}

Uint8List _int32be(int value) {
  final b = Uint8List(4);
  b.buffer.asByteData().setInt32(0, value, Endian.big);
  return b;
}

Uint8List _uint64be(BigInt value) {
  final b = Uint8List(8);
  var v = value;
  for (var i = 7; i >= 0; i--) {
    b[i] = (v & BigInt.from(0xff)).toInt();
    v = v >> 8;
  }
  return b;
}

Uint8List _bigIntToBytes(BigInt value, int length) {
  final out = Uint8List(length);
  var v = value;
  for (var i = length - 1; i >= 0; i--) {
    out[i] = (v & BigInt.from(0xff)).toInt();
    v = v >> 8;
  }
  return out;
}

BigInt _bytesToBigInt(List<int> bytes) {
  var result = BigInt.zero;
  for (final b in bytes) {
    result = (result << 8) | BigInt.from(b);
  }
  return result;
}

String _b64urlNoPad(Uint8List bytes) {
  return base64Url.encode(bytes).replaceAll('=', '');
}

String _pad(String b64url) {
  final mod = b64url.length % 4;
  if (mod == 0) return b64url;
  return b64url + ('=' * (4 - mod));
}
