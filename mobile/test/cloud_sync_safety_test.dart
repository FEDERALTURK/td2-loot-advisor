import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:td2_companion/services/cloud_api.dart';
import 'package:td2_companion/services/cloud_link.dart';

const id = 'fixture-build-0001';

class FakeApi extends CloudApi {
  bool conflict = false;
  bool deleteFails = false;
  int puts = 0;
  int deletes = 0;
  int dashboards = 0;
  Completer<Map<String, dynamic>>? pendingDashboard;
  Completer<List<Map<String, dynamic>>>? pendingList;

  @override
  Future<Map<String, dynamic>> dashboard(String token) {
    dashboards++;
    return pendingDashboard?.future ?? Future.value({});
  }

  @override
  Future<int> putBuild(
    String token, {
    required String clientId,
    required String name,
    required Map<String, dynamic> payload,
    required int baseRevision,
  }) async {
    puts++;
    if (conflict) throw RevisionConflict(4);
    return 2;
  }

  @override
  Future<List<Map<String, dynamic>>> listBuilds(String token) async =>
      pendingList?.future ??
      [
        {
          'client_id': id,
          'revision': 4,
          'payload': {'name': 'cloud build'},
        },
      ];

  @override
  Future<int> deleteBuild(String token, String clientId) async {
    deletes++;
    if (deleteFails) throw CloudApiException(0, 'network');
    return 5;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({
      'cloud_device_id': 'fixture-device',
      'cloud_token': 'fixture-token',
    });
  });

  test(
    'revision conflicts preserve local data and stay conflicts on retry',
    () async {
      final api = FakeApi()..conflict = true;
      final model = CloudLinkModel(api: api);
      await model.load();
      addTearDown(model.dispose);
      var saved = <Map<String, dynamic>>[];
      final local = [
        {'id': id, 'name': 'local build'},
      ];
      for (var i = 0; i < 2; i++) {
        expect(
          await model.syncBuilds(
            local: local,
            persistLocal: (rows) async {
              saved = rows;
            },
          ),
          contains('çakıştı'),
        );
        expect(saved.single['name'], 'local build');
      }
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('cloud_build_revisions'), '{}');
    },
  );

  test(
    'offline delete persists across restart and is not resurrected',
    () async {
      final api = FakeApi()..deleteFails = true;
      final first = CloudLinkModel(api: api);
      await first.load();
      await first.deleteBuildQuietly(id);
      expect(first.pendingDeleteCount, 1);
      first.dispose();
      api.deleteFails = false;
      final second = CloudLinkModel(api: api);
      await second.load();
      addTearDown(second.dispose);
      expect(second.pendingDeleteCount, 1);
      var saved = <Map<String, dynamic>>[];
      await second.syncBuilds(
        local: [
          {'id': id, 'name': 'stale local'},
        ],
        persistLocal: (rows) async => saved = rows,
      );
      expect(saved, isEmpty);
      expect(api.puts, 0);
      expect(api.deletes, 2);
      expect(second.pendingDeleteCount, 0);
    },
  );

  test(
    'overlapping dashboard and build sync requests are suppressed',
    () async {
      final api = FakeApi()..pendingDashboard = Completer();
      final model = CloudLinkModel(api: api);
      await model.load();
      addTearDown(model.dispose);
      await model.refreshDashboard();
      expect(api.dashboards, 1);
      api.pendingDashboard!.complete({});
      api.pendingList = Completer();
      final first = model.syncBuilds(local: [], persistLocal: (_) async {});
      expect(
        await model.syncBuilds(local: [], persistLocal: (_) async {}),
        contains('zaten'),
      );
      api.pendingList!.complete([]);
      await first;
    },
  );
}
