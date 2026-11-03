// TD2 Loot Advisor Companion — bulut eşleştirme ve build senkronu durumu.
//
// `cloud_api.dart` saf HTTP istemcisidir; burada telefonun cihaz
// oturumu (token), masaüstü gösterge paneli ve build senkronu durumu tutulur.
// LAN/QR tabanlı `CompanionModel.connectDesktop` akışından TAMAMEN ayrıdır:
// ikisi aynı anda, bağımsız olarak kullanılabilir.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'cloud_api.dart';

const _kDeviceIdKey = 'cloud_device_id';
const _kTokenKey = 'cloud_token';
const _kRevisionsKey = 'cloud_build_revisions';

class CloudLinkModel extends ChangeNotifier {
  CloudLinkModel({CloudApi? api}) : _api = api ?? CloudApi();
  final CloudApi _api;

  SharedPreferences? _prefs;
  Timer? _poll;

  String? _deviceId;
  String? _token;
  bool pairing = false;
  String? pairError;
  Map<String, dynamic>? dashboardState;
  bool dashboardLoading = false;

  bool syncing = false;
  String? syncError;
  DateTime? lastSync;

  bool get paired => _token != null;

  bool get desktopOnline => dashboardState?['desktop']?['online'] == true;

  Future<void> load() async {
    _prefs = await SharedPreferences.getInstance();
    _deviceId = _prefs?.getString(_kDeviceIdKey);
    _token = _prefs?.getString(_kTokenKey);
    if (_token != null) {
      _startPolling();
      unawaited(refreshDashboard());
    }
  }

  @override
  void dispose() {
    _poll?.cancel();
    super.dispose();
  }

  // ---------------------------------------------------------------- eşleştirme
  Future<bool> pair(String rawCode) async {
    final code = rawCode.trim().toUpperCase();
    if (code.length < 6) {
      pairError = 'Kod en az 6 karakter olmalı.';
      notifyListeners();
      return false;
    }
    pairing = true;
    pairError = null;
    notifyListeners();
    try {
      final result = await _api.claimPairing(code, isIos: Platform.isIOS);
      _deviceId = result.deviceId;
      _token = result.token;
      await _prefs?.setString(_kDeviceIdKey, result.deviceId);
      await _prefs?.setString(_kTokenKey, result.token);
      _startPolling();
      await refreshDashboard();
      return true;
    } on CloudApiException catch (e) {
      pairError = _describe(e);
      return false;
    } finally {
      pairing = false;
      notifyListeners();
    }
  }

  Future<void> unpair() async {
    _poll?.cancel();
    _poll = null;
    _deviceId = null;
    _token = null;
    dashboardState = null;
    pairError = null;
    await _prefs?.remove(_kDeviceIdKey);
    await _prefs?.remove(_kTokenKey);
    notifyListeners();
  }

  void _startPolling() {
    _poll?.cancel();
    _poll = Timer.periodic(const Duration(seconds: 8), (_) => refreshDashboard());
  }

  Future<void> refreshDashboard() async {
    final token = _token;
    if (token == null) return;
    dashboardLoading = true;
    notifyListeners();
    try {
      dashboardState = await _api.dashboard(token);
      pairError = null;
    } on CloudApiException catch (e) {
      if (e.statusCode == 401) await unpair();
      pairError = _describe(e);
    } finally {
      dashboardLoading = false;
      notifyListeners();
    }
  }

  // ---------------------------------------------------------------- build senkronu
  Future<Map<String, int>> _loadRevisions() async {
    final raw = _prefs?.getString(_kRevisionsKey);
    if (raw == null) return {};
    try {
      final value = jsonDecode(raw);
      if (value is Map) {
        return value.map((k, v) => MapEntry('$k', (v as num).toInt()));
      }
    } catch (_) {/* bozuk veri — sıfırdan başla */}
    return {};
  }

  Future<void> _saveRevisions(Map<String, int> revisions) async {
    await _prefs?.setString(_kRevisionsKey, jsonEncode(revisions));
  }

  /// Yerel build listesini buluttakiyle eşitler: değişen/yeni yerel build'leri
  /// gönderir, buluttaki silme (tombstone) ve güncellemeleri yerele uygular.
  /// Sonucu [persistLocal] ile kalıcı hâle getirmek çağıranın sorumluluğundadır.
  Future<String?> syncBuilds({
    required List<Map<String, dynamic>> local,
    required Future<void> Function(List<Map<String, dynamic>>) persistLocal,
  }) async {
    final token = _token;
    if (token == null) return 'Telefon henüz buluta eşleştirilmedi.';
    syncing = true;
    syncError = null;
    notifyListeners();
    try {
      final revisions = await _loadRevisions();
      for (final build in local) {
        final id = '${build['id'] ?? ''}';
        if (id.length < 16 || id.length > 64) continue; // bulutun client_id biçimine uymuyor
        final base = revisions[id] ?? 0;
        final name = '${build['name'] ?? ''}'.trim().isEmpty ? 'Build' : '${build['name']}';
        try {
          revisions[id] = await _api.putBuild(
            token,
            clientId: id,
            name: name,
            payload: build,
            baseRevision: base,
          );
        } on RevisionConflict {
          // Sunucu farklı bir revizyonda: bu turda atla, aşağıdaki çekme adımı
          // buluttaki hâli uygulayacak — basit "bulut kazanır" çözümü.
        }
      }
      final cloudBuilds = await _api.listBuilds(token);
      final merged = [...local];
      for (final cb in cloudBuilds) {
        final id = '${cb['client_id'] ?? ''}';
        final idx = merged.indexWhere((b) => '${b['id']}' == id);
        if (cb['deleted'] == true) {
          if (idx != -1) merged.removeAt(idx);
          revisions.remove(id);
        } else {
          final payload = cb['payload'] is Map
              ? Map<String, dynamic>.from(cb['payload'] as Map)
              : <String, dynamic>{};
          payload['id'] = id;
          if (idx != -1) {
            merged[idx] = payload;
          } else {
            merged.add(payload);
          }
          revisions[id] = (cb['revision'] as num?)?.toInt() ?? revisions[id] ?? 0;
        }
      }
      await persistLocal(merged);
      await _saveRevisions(revisions);
      lastSync = DateTime.now();
      return null;
    } on CloudApiException catch (e) {
      syncError = _describe(e);
      return syncError;
    } finally {
      syncing = false;
      notifyListeners();
    }
  }

  /// Tek bir build'i hemen buluta gönderir (örn. yeni build kaydedildiğinde).
  /// En iyi gayret: başarısız olursa sessizce yutar, bir sonraki tam senkron
  /// zaten yeniden deneyecektir.
  Future<void> pushBuildQuietly(Map<String, dynamic> build) async {
    final token = _token;
    final id = '${build['id'] ?? ''}';
    if (token == null || id.length < 16 || id.length > 64) return;
    try {
      final revisions = await _loadRevisions();
      final rev = await _api.putBuild(
        token,
        clientId: id,
        name: '${build['name'] ?? ''}'.trim().isEmpty ? 'Build' : '${build['name']}',
        payload: build,
        baseRevision: revisions[id] ?? 0,
      );
      revisions[id] = rev;
      await _saveRevisions(revisions);
    } catch (_) {/* sessizce yut — bir sonraki tam senkron devreye girer */}
  }

  /// Bir build silindiğinde buluttaki karşılığını da tombstone'lar.
  Future<void> deleteBuildQuietly(String id) async {
    final token = _token;
    if (token == null || id.length < 16 || id.length > 64) return;
    try {
      await _api.deleteBuild(token, id);
      final revisions = await _loadRevisions();
      revisions.remove(id);
      await _saveRevisions(revisions);
    } catch (_) {/* sessizce yut */}
  }

  // ---------------------------------------------------------------- hesap silme
  /// DİKKAT: Bu, yalnızca bu telefonu değil, masaüstünün bağlı olduğu TÜM
  /// hesabı (lisans dahil) 24 saatlik bekleme sonrası kalıcı olarak siler.
  Future<String?> deleteAccount() async {
    final token = _token;
    if (token == null) return 'Telefon buluta eşleştirilmemiş.';
    try {
      await _api.deleteAccount(token);
      await unpair();
      return null;
    } on CloudApiException catch (e) {
      return _describe(e);
    }
  }

  String _describe(CloudApiException e) {
    switch (e.code) {
      case 'network':
        return 'Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.';
      case 'timeout':
        return 'Sunucu yanıt vermedi. Tekrar dene.';
      case 'unauthorized':
        return 'Eşleştirme süresi doldu veya iptal edildi. Telefonu yeniden eşleştir.';
      case 'rate limited':
        return 'Çok fazla istek gönderildi. Birazdan tekrar dene.';
      case 'invalid or expired code':
        return 'Kod geçersiz veya süresi dolmuş.';
      case 'code already used':
        return 'Bu kod zaten kullanılmış. Masaüstünden yeni bir kod al.';
      default:
        return 'Sunucu hatası (${e.statusCode}): ${e.code}';
    }
  }
}
