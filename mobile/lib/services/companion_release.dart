import 'dart:convert';

import 'package:http/http.dart' as http;

/// GitHub beta etiketi dört bileşene izin verir (ör. 0.1.4.1). Android'in
/// package sürümü ise pubspec içinde üç bileşen + artan build numarasıdır.
const companionVersion = '0.1.7';
const updateCheckInterval = Duration(hours: 6);

class CompanionRelease {
  const CompanionRelease({
    required this.version,
    required this.url,
    this.apkUrl,
    this.sha256Url,
  });

  final String version;
  final String url;

  /// GitHub release içindeki imzalı Android APK'ya doğrudan HTTPS bağlantısı.
  /// Varlık yoksa uygulama güvenle release sayfasına geri dönebilir.
  final String? apkUrl;
  final String? sha256Url;
}

/// GitHub'daki yalnız Companion ön-yayınlarını okur. Masaüstü `v9.x` yayınları
/// bu kontrolün kapsamına girmez.
Future<CompanionRelease?> fetchLatestCompanionRelease(
  http.Client client,
) async {
  final uri = Uri.https(
    'api.github.com',
    '/repos/FEDERALTURK/td2-loot-advisor/releases',
    {'per_page': '20'},
  );
  final response = await client
      .get(
        uri,
        headers: const {
          'Accept': 'application/vnd.github+json',
          'User-Agent': 'TD2-Loot-Advisor-Companion/$companionVersion',
        },
      )
      .timeout(const Duration(seconds: 8));
  if (response.statusCode != 200) return null;
  return parseLatestCompanionRelease(
    jsonDecode(utf8.decode(response.bodyBytes)),
  );
}

/// Ağ katmanından ayrılmış sürüm seçimi. Böylece hem hatalı GitHub verisi hem
/// doğrudan APK bağlantısı tekil testlerde doğrulanabilir.
CompanionRelease? parseLatestCompanionRelease(dynamic decoded) {
  if (decoded is! List) return null;
  CompanionRelease? latest;
  for (final item in decoded) {
    if (item is! Map) continue;
    final tag = '${item['tag_name'] ?? ''}';
    if (!tag.startsWith('companion-v')) continue;
    final version = tag.substring('companion-v'.length).split('-').first;
    if (!_validVersion(version)) continue;
    final url = '${item['html_url'] ?? ''}';
    if (!_isSafeHttpsUrl(url)) continue;
    final candidate = CompanionRelease(
      version: version,
      url: url,
      apkUrl: _findApkUrl(item['assets']),
      sha256Url: _findSha256Url(item['assets']),
    );
    if (latest == null || isNewerVersion(candidate.version, latest.version)) {
      latest = candidate;
    }
  }
  return latest;
}

String? _findApkUrl(dynamic assets) {
  if (assets is! List) return null;
  for (final asset in assets) {
    if (asset is! Map) continue;
    final name = '${asset['name'] ?? ''}';
    final url = '${asset['browser_download_url'] ?? ''}';
    if (!name.startsWith('TD2LootAdvisor_Companion_') ||
        !name.toLowerCase().endsWith('.apk') ||
        !_isSafeHttpsUrl(url)) {
      continue;
    }
    return url;
  }
  return null;
}

String? _findSha256Url(dynamic assets) {
  if (assets is! List) return null;
  for (final asset in assets) {
    if (asset is! Map) continue;
    final name = '${asset['name'] ?? ''}'.toLowerCase();
    final url = '${asset['browser_download_url'] ?? ''}';
    if (name == 'sha256sums.sha256' && _isSafeHttpsUrl(url)) return url;
  }
  return null;
}

bool _isSafeHttpsUrl(String value) {
  final uri = Uri.tryParse(value);
  return uri != null && uri.scheme == 'https' && uri.host.isNotEmpty;
}

bool isNewerVersion(String candidate, String installed) {
  final a = _parts(candidate);
  final b = _parts(installed);
  if (a == null || b == null) return false;
  for (var index = 0; index < 4; index++) {
    if (a[index] != b[index]) return a[index] > b[index];
  }
  return false;
}

bool isUpdateCheckDue(DateTime? lastCheck, {DateTime? now}) {
  if (lastCheck == null) return true;
  final current = now ?? DateTime.now();
  return current.difference(lastCheck) >= updateCheckInterval;
}

bool _validVersion(String value) => _parts(value) != null;

List<int>? _parts(String value) {
  final match = RegExp(r'^(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?$').firstMatch(value);
  if (match == null) return null;
  return [
    int.parse(match.group(1)!),
    int.parse(match.group(2)!),
    int.parse(match.group(3)!),
    int.tryParse(match.group(4) ?? '') ?? 0,
  ];
}
