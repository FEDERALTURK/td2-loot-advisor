// Xbox doğrudan bağlantı (deneysel) — kimlik doğrulama akışı.
//
// KAYNAK: Her adımın URL'si, başlığı ve gövdesi XStreaming projesinin
// (MIT lisanslı, GiGanTe71/XStreaming) docs/1.Auth.md belgesinden satır
// satır alınmıştır (tahmin edilmemiştir). Bölüm numaraları (§1.x) o
// belgeye referans verir.
//
// AKIŞ ÖZETİ:
//   1. Cihaz belirteci (deviceToken)                — §1.3
//   2. PKCE challenge + rastgele state                — §1.4 / §1.5
//   3. SisuAuthentication → Microsoft giriş adresi    — §1.6
//      (Kullanıcı bu adresi sistem tarayıcısında açıp Microsoft hesabıyla
//      giriş yapar, sonra `ms-xal-...://auth?code=...&state=...` adresine
//      yönlendirilir. Bu uygulama henüz özel URL şeması/WebView yakalama
//      kurmadığı için kullanıcı bu son adresi ELLE YAPIŞTIRIR — bkz.
//      xbox_login_page.dart. Bu, PKCE tabanlı OAuth akışlarında yaygın
//      kullanılan basit ve güvenli bir geçici yöntemdir.)
//   4. authenticateUserUsingCode → userToken          — §1.7
//   5. Taze deviceToken + SisuAuthorization → sisuToken — §1.8.2 / §1.8.3
//   6. XSTS webToken + streamingToken                  — §1.10
//   7. xhome streaming token exchange → gsToken+baseUri — §1.11.1
//
// NOT (dürüstlük ilkesi): Bu akış gerçek bir Microsoft/Xbox hesabına karşı
// bu oturumda TEST EDİLMEMİŞTİR — bu kum havuzunda interaktif Microsoft
// girişi yapılamaz. Her adım dokümantasyonla bayt-bayt eşleştirilerek
// yazıldı ama ilk gerçek koşturmada küçük sürpriz hatalar (ör. Microsoft'un
// sunucu tarafı küçük bir alan adı/başlık beklentisi) çıkması olası —
// bu tür koşullarda sistematik hata ayıklama (bkz. AGENTS.md madde 10)
// uygulanmalı, körlemesine tekrar denenmemelidir.
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'xbox_crypto.dart';
import 'xbox_token_store.dart';

const _appId = '000000004c20a908';
const _titleId = '328178078';
const _redirectUri = 'ms-xal-000000004c20a908://auth';

class XboxAuthException implements Exception {
  XboxAuthException(this.step, this.message, {this.statusCode, this.body});
  final String step;
  final String message;
  final int? statusCode;
  final String? body;

  @override
  String toString() =>
      'XboxAuthException[$step]: $message'
      '${statusCode != null ? ' (HTTP $statusCode)' : ''}'
      '${body != null ? '\n$body' : ''}';
}

/// §1.6 SisuAuthentication sonucu — kullanıcıya açılacak giriş adresi ve
/// 1.7'de doğrulanacak `state`/`verifier` çifti.
class XboxLoginStart {
  XboxLoginStart({
    required this.msaOauthRedirect,
    required this.state,
    required this.codeVerifier,
  });
  final String msaOauthRedirect;
  final String state;
  final String codeVerifier;
}

class XboxAuthService {
  final http.Client _client = http.Client();

  /// Adım 1–3: cihaz belirteci + PKCE + SisuAuthentication.
  /// Döndürülen [XboxLoginStart.msaOauthRedirect] sistem tarayıcısında
  /// açılmalı; kullanıcı giriş yaptıktan sonra yönlendirilen
  /// `ms-xal-...://auth?...` adresi [completeLogin]'e verilmelidir.
  Future<XboxLoginStart> startLogin(XboxTokenStore store) async {
    store.jwtKeys ??= generateXboxJwtKeys();
    final keys = store.jwtKeys!;

    final deviceToken = await _requestDeviceToken(keys);
    final challenge = generateXboxCodeChallenge();
    final state = generateXboxState();

    const path = '/authenticate';
    final body = jsonEncode({
      'AppId': _appId,
      'TitleId': _titleId,
      'RedirectUri': _redirectUri,
      'DeviceToken': deviceToken,
      'Sandbox': 'RETAIL',
      'TokenType': 'code',
      'Offers': ['service::user.auth.xboxlive.com::MBI_SSL'],
      'Query': {
        'display': 'android_phone',
        'code_challenge': challenge.value,
        'code_challenge_method': challenge.method,
        'state': state,
      },
    });
    final signature = signXboxRequest(
      keys: keys,
      path: path,
      authorizationToken: '',
      payload: body,
    );

    final resp = await _client.post(
      Uri.parse('https://sisu.xboxlive.com$path'),
      headers: {
        'Content-Type': 'application/json',
        'x-xbl-contract-version': '1',
        'Cache-Control': 'no-store, must-revalidate, no-cache',
        'Signature': signature,
      },
      body: body,
    );
    if (resp.statusCode != 200 && resp.statusCode != 201) {
      throw XboxAuthException('sisu_authenticate', 'Giriş adresi alınamadı',
          statusCode: resp.statusCode, body: resp.body);
    }
    final json = jsonDecode(resp.body) as Map<String, dynamic>;
    final redirect = (json['data'] as Map<String, dynamic>)['MsaOauthRedirect'] as String;

    return XboxLoginStart(
      msaOauthRedirect: redirect,
      state: state,
      codeVerifier: challenge.verifier,
    );
  }

  /// Adım 4–5: Kullanıcının yapıştırdığı yönlendirme adresinden `code`/`state`
  /// çıkarır, doğrular, userToken alır, ardından tam sisuToken'ı üretir.
  Future<void> completeLogin({
    required XboxTokenStore store,
    required String redirectUrlFromUser,
    required XboxLoginStart started,
  }) async {
    final uri = _parseRedirect(redirectUrlFromUser);
    final code = uri.queryParameters['code'];
    final state = uri.queryParameters['state'];
    if (code == null || state == null) {
      throw XboxAuthException('parse_redirect',
          'Yapıştırılan adreste code veya state alanı bulunamadı. '
          'Adresin "ms-xal-...://auth/?code=...&state=..." ile başladığından emin olun.');
    }
    if (state != started.state) {
      throw XboxAuthException('state_mismatch',
          'Güvenlik doğrulaması (state) eşleşmedi — giriş baştan tekrarlanmalı.');
    }

    final userToken = await _authenticateUserUsingCode(
      code: code,
      codeVerifier: started.codeVerifier,
    );
    store.userToken = userToken;
    await _refreshSisuToken(store);
    await store.save();
  }

  /// §1.8.1 + §1.8.2 + §1.8.3 — userToken süresi dolduysa yeniler, taze bir
  /// deviceToken alır ve SisuAuthorization ile tam sisuToken'ı günceller.
  /// completeLogin içinden ve periyodik yenilemeler için kullanılır.
  Future<void> _refreshSisuToken(XboxTokenStore store) async {
    final keys = store.jwtKeys!;
    var userToken = store.userToken!;

    if (userToken.isExpired) {
      userToken = await _refreshUserToken(userToken.refreshToken);
      store.userToken = userToken;
    }

    final deviceToken = await _requestDeviceToken(keys);

    const path = '/authorize';
    final body = jsonEncode({
      'AccessToken': 't=${userToken.accessToken}',
      'AppId': _appId,
      'DeviceToken': deviceToken,
      'Sandbox': 'RETAIL',
      'SiteName': 'user.auth.xboxlive.com',
      'UseModernGamertag': true,
      'ProofKey': {
        'use': 'sig',
        'alg': 'ES256',
        'kty': 'EC',
        'crv': 'P-256',
        'x': keys.x,
        'y': keys.y,
      },
    });
    final signature = signXboxRequest(
      keys: keys,
      path: path,
      authorizationToken: '',
      payload: body,
    );
    final resp = await _client.post(
      Uri.parse('https://sisu.xboxlive.com$path'),
      headers: {
        'Content-Type': 'application/json',
        'x-xbl-contract-version': '1',
        'Cache-Control': 'no-store, must-revalidate, no-cache',
        'Signature': signature,
      },
      body: body,
    );
    if (resp.statusCode != 200 && resp.statusCode != 201) {
      throw XboxAuthException('sisu_authorize', 'sisuToken alınamadı',
          statusCode: resp.statusCode, body: resp.body);
    }
    final json = resp.body.isEmpty ? <String, dynamic>{} : jsonDecode(resp.body) as Map<String, dynamic>;
    store.sisuToken = XboxSisuToken(
      deviceToken: json['DeviceToken'] as String,
      titleToken: (json['TitleToken'] as Map<String, dynamic>)['Token'] as String,
      userToken: (json['UserToken'] as Map<String, dynamic>)['Token'] as String,
    );
  }

  /// §1.10 — XSTS token. [relyingParty] `http://xboxlive.com` → webToken,
  /// `http://gssv.xboxlive.com/` → streamingToken. Dönen değer, 1.10
  /// yanıtındaki `Token` alanının kendisidir (xstsToken).
  Future<String> _requestXsts({
    required XboxTokenStore store,
    required String relyingParty,
  }) async {
    final keys = store.jwtKeys!;
    final sisu = store.sisuToken!;
    const path = '/xsts/authorize';
    final body = jsonEncode({
      'Properties': {
        'SandboxId': 'RETAIL',
        'DeviceToken': sisu.deviceToken,
        'TitleToken': sisu.titleToken,
        'UserTokens': [sisu.userToken],
      },
      'RelyingParty': relyingParty,
      'TokenType': 'JWT',
    });
    final signature = signXboxRequest(
      keys: keys,
      path: path,
      authorizationToken: '',
      payload: body,
    );
    final resp = await _client.post(
      Uri.parse('https://xsts.auth.xboxlive.com$path'),
      headers: {
        'Content-Type': 'application/json',
        'x-xbl-contract-version': '1',
        'Cache-Control': 'no-store, must-revalidate, no-cache',
        'Signature': signature,
      },
      body: body,
    );
    if (resp.statusCode != 200 && resp.statusCode != 201) {
      throw XboxAuthException('xsts_authorize', 'XSTS belirteci alınamadı ($relyingParty)',
          statusCode: resp.statusCode, body: resp.body);
    }
    final json = jsonDecode(resp.body) as Map<String, dynamic>;
    return json['Token'] as String;
  }

  /// "webToken" — konsol listesi/arkadaş listesi gibi web API'leri için.
  /// Ayrıca 2.1'de kullanılan `uhs` değeri de (DisplayClaims.xui[0].uhs)
  /// döndürülür.
  Future<(String token, String uhs)> getWebToken(XboxTokenStore store) async {
    final keys = store.jwtKeys!;
    final sisu = store.sisuToken!;
    const path = '/xsts/authorize';
    final body = jsonEncode({
      'Properties': {
        'SandboxId': 'RETAIL',
        'DeviceToken': sisu.deviceToken,
        'TitleToken': sisu.titleToken,
        'UserTokens': [sisu.userToken],
      },
      'RelyingParty': 'http://xboxlive.com',
      'TokenType': 'JWT',
    });
    final signature = signXboxRequest(
      keys: keys,
      path: path,
      authorizationToken: '',
      payload: body,
    );
    final resp = await _client.post(
      Uri.parse('https://xsts.auth.xboxlive.com$path'),
      headers: {
        'Content-Type': 'application/json',
        'x-xbl-contract-version': '1',
        'Cache-Control': 'no-store, must-revalidate, no-cache',
        'Signature': signature,
      },
      body: body,
    );
    if (resp.statusCode != 200 && resp.statusCode != 201) {
      throw XboxAuthException('xsts_authorize_web', 'webToken alınamadı',
          statusCode: resp.statusCode, body: resp.body);
    }
    final json = jsonDecode(resp.body) as Map<String, dynamic>;
    final token = json['Token'] as String;
    final uhs = ((json['DisplayClaims'] as Map<String, dynamic>)['xui'] as List)
        .first['uhs'] as String;
    return (token, uhs);
  }

  /// §1.11.1 — xhome (yerel konsol) akış belirteci: gsToken + bölgesel
  /// baseUri listesi. [streamingXstsToken], `getStreamingXstsToken()` ile
  /// (RelyingParty `http://gssv.xboxlive.com/`) alınan xstsToken'dır.
  Future<String> getStreamingXstsToken(XboxTokenStore store) =>
      _requestXsts(store: store, relyingParty: 'http://gssv.xboxlive.com/');

  Future<XboxHomeStreamCredential> getXHomeStreamCredential(String streamingXstsToken) async {
    final body = jsonEncode({
      'token': streamingXstsToken,
      'offeringId': 'xhome',
    });
    final resp = await _client.post(
      Uri.parse('https://xhome.gssv-play-prod.xboxlive.com'),
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, must-revalidate, no-cache',
        'x-gssv-client': 'XboxComBrowser',
      },
      body: body,
    );
    if (resp.statusCode != 200 && resp.statusCode != 201) {
      throw XboxAuthException('xhome_token', 'Yayın (streaming) belirteci alınamadı',
          statusCode: resp.statusCode, body: resp.body);
    }
    final json = jsonDecode(resp.body) as Map<String, dynamic>;
    final regions = (json['offeringSettings']['regions'] as List)
        .map((r) => (name: r['name'] as String, baseUri: r['baseUri'] as String))
        .toList();
    return XboxHomeStreamCredential(
      gsToken: json['gsToken'] as String,
      durationInSeconds: json['durationInSeconds'] as int,
      regions: regions,
    );
  }

  // --- 1.3 Cihaz belirteci ---------------------------------------------

  Future<String> _requestDeviceToken(XboxJwtKeys keys) async {
    const path = '/device/authenticate';
    final body = jsonEncode({
      'Properties': {
        'AuthMethod': 'ProofOfPossession',
        'Id': '{${generateUuidV4()}}',
        'DeviceType': 'Android',
        'SerialNumber': '{${generateUuidV4()}}',
        'Version': '15.0',
        'ProofKey': {
          'use': 'sig',
          'alg': 'ES256',
          'kty': 'EC',
          'crv': 'P-256',
          'x': keys.x,
          'y': keys.y,
        },
      },
      'RelyingParty': 'http://auth.xboxlive.com',
      'TokenType': 'JWT',
    });
    final signature = signXboxRequest(
      keys: keys,
      path: path,
      authorizationToken: '',
      payload: body,
    );
    final resp = await _client.post(
      Uri.parse('https://device.auth.xboxlive.com$path'),
      headers: {
        'Content-Type': 'application/json',
        'x-xbl-contract-version': '1',
        'Cache-Control': 'no-store, must-revalidate, no-cache',
        'Signature': signature,
      },
      body: body,
    );
    if (resp.statusCode != 200 && resp.statusCode != 201) {
      throw XboxAuthException('device_token', 'Cihaz belirteci alınamadı',
          statusCode: resp.statusCode, body: resp.body);
    }
    final json = jsonDecode(resp.body) as Map<String, dynamic>;
    return json['Token'] as String;
  }

  // --- 1.7 Kod → userToken ----------------------------------------------

  Future<XboxUserToken> _authenticateUserUsingCode({
    required String code,
    required String codeVerifier,
  }) async {
    final form = {
      'client_id': _appId,
      'code': code,
      'code_verifier': codeVerifier,
      'grant_type': 'authorization_code',
      'redirect_uri': _redirectUri,
      'scope': 'service::user.auth.xboxlive.com::MBI_SSL',
    };
    final resp = await _client.post(
      Uri.parse('https://login.live.com/oauth20_token.srf'),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-store, must-revalidate, no-cache',
      },
      body: form,
    );
    if (resp.statusCode != 200) {
      throw XboxAuthException('token_exchange', 'Giriş kodu belirtece çevrilemedi',
          statusCode: resp.statusCode, body: resp.body);
    }
    return _parseUserTokenResponse(resp.body);
  }

  // --- 1.8.1 refresh_token ile userToken yenileme ------------------------

  Future<XboxUserToken> _refreshUserToken(String refreshToken) async {
    final form = {
      'client_id': _appId,
      'grant_type': 'refresh_token',
      'refresh_token': refreshToken,
      'scope': 'service::user.auth.xboxlive.com::MBI_SSL',
    };
    final resp = await _client.post(
      Uri.parse('https://login.live.com/oauth20_token.srf'),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-store, must-revalidate, no-cache',
      },
      body: form,
    );
    if (resp.statusCode != 200) {
      throw XboxAuthException('token_refresh', 'Oturum yenilenemedi — yeniden giriş gerekebilir',
          statusCode: resp.statusCode, body: resp.body);
    }
    return _parseUserTokenResponse(resp.body);
  }

  XboxUserToken _parseUserTokenResponse(String body) {
    final json = jsonDecode(body) as Map<String, dynamic>;
    final expiresIn = json['expires_in'] as int;
    return XboxUserToken(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      expiresOn: DateTime.now().add(Duration(seconds: expiresIn)),
    );
  }

  Uri _parseRedirect(String raw) {
    // "ms-xal-...://auth/?code=...&state=..." — Dart'ın Uri.parse'ı özel
    // şemaları da ayrıştırabilir, queryParameters doğru çalışır.
    return Uri.parse(raw.trim());
  }

  void dispose() => _client.close();
}

/// §1.11.1 yanıtı.
class XboxHomeStreamCredential {
  XboxHomeStreamCredential({
    required this.gsToken,
    required this.durationInSeconds,
    required this.regions,
  });

  final String gsToken;
  final int durationInSeconds;
  final List<({String name, String baseUri})> regions;
}
