// Xbox doğrudan bağlantı (deneysel) — hesaba kayıtlı konsol listesi.
// KAYNAK: docs/2.Web.md §2.1 (GiGanTe71/XStreaming, MIT) — satır satır alındı.
import 'dart:convert';

import 'package:http/http.dart' as http;

class XboxConsole {
  XboxConsole({
    required this.id,
    required this.name,
    required this.powerState,
    required this.consoleType,
  });

  /// Yayın oturumu başlatırken `serverId` olarak kullanılan asıl kimlik.
  final String id;
  final String name;
  final String powerState;
  final String consoleType;

  factory XboxConsole.fromJson(Map<String, dynamic> j) => XboxConsole(
        id: j['id'] as String,
        name: j['name'] as String? ?? 'Xbox',
        powerState: j['powerState'] as String? ?? 'Unknown',
        consoleType: j['consoleType'] as String? ?? 'Unknown',
      );
}

class XboxConsoleService {
  final http.Client _client = http.Client();

  /// [webToken]/[uhs]: `XboxAuthService.getWebToken()`'dan.
  Future<List<XboxConsole>> listConsoles({
    required String webToken,
    required String uhs,
  }) async {
    final uri = Uri.parse(
      'https://xccs.xboxlive.com/lists/devices?queryCurrentDevice=false&includeStorageDevices=true',
    );
    final resp = await _client.get(uri, headers: {
      'Authorization': 'XBL3.0 x=$uhs;$webToken',
      'Accept-Language': 'en-US',
      'x-xbl-contract-version': '2',
      'x-xbl-client-name': 'XboxApp',
      'x-xbl-client-type': 'UWA',
      'x-xbl-client-version': '39.39.22001.0',
    });
    if (resp.statusCode != 200) {
      throw Exception('Konsol listesi alınamadı (HTTP ${resp.statusCode}): ${resp.body}');
    }
    final json = jsonDecode(resp.body) as Map<String, dynamic>;
    final status = json['status'] as Map<String, dynamic>?;
    if (status != null && status['errorCode'] != 'OK') {
      throw Exception('Konsol listesi hata döndürdü: ${status['errorMessage']}');
    }
    final result = (json['result'] as List?) ?? const [];
    return result.map((r) => XboxConsole.fromJson(r as Map<String, dynamic>)).toList();
  }

  void dispose() => _client.close();
}
