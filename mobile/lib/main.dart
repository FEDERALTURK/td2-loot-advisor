import 'dart:convert';
import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

const _bg = Color(0xFF090C12);
const _panel = Color(0xFF121722);
const _panel2 = Color(0xFF191F2B);
const _orange = Color(0xFFFF6D10);
const _soft = Color(0xFF9AA4B5);

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const TD2CompanionApp());
}

class TD2CompanionApp extends StatefulWidget {
  const TD2CompanionApp({super.key});

  @override
  State<TD2CompanionApp> createState() => _TD2CompanionAppState();
}

class _TD2CompanionAppState extends State<TD2CompanionApp> {
  late final CompanionModel model;

  @override
  void initState() {
    super.initState();
    model = CompanionModel()..load();
  }

  @override
  void dispose() {
    model.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(
      seedColor: _orange,
      brightness: Brightness.dark,
      surface: _panel,
    );
    return MaterialApp(
      title: 'TD2 Loot Advisor Companion',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: scheme,
        scaffoldBackgroundColor: _bg,
        cardColor: _panel,
        dividerColor: Colors.white12,
        appBarTheme: const AppBarTheme(
          backgroundColor: _bg,
          surfaceTintColor: Colors.transparent,
          elevation: 0,
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: const Color(0xFF0E121A),
          indicatorColor: _orange.withValues(alpha: .16),
          labelTextStyle: WidgetStateProperty.resolveWith(
            (states) => TextStyle(
              fontSize: 11,
              fontWeight: states.contains(WidgetState.selected)
                  ? FontWeight.w700
                  : FontWeight.w500,
              color: states.contains(WidgetState.selected) ? _orange : _soft,
            ),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: _panel2,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
        ),
      ),
      home: MainShell(model: model),
    );
  }
}

class CompanionModel extends ChangeNotifier {
  Map<String, dynamic> tasksFeed = {};
  Map<String, dynamic> newsFeed = {};
  Map<String, dynamic> metaBuilds = {};
  List<Map<String, dynamic>> savedBuilds = [];
  Set<String> completedTasks = {};
  bool loading = true;
  bool refreshing = false;
  String? refreshMessage;
  DateTime? lastRefresh;
  SharedPreferences? _prefs;
  Timer? _desktopPoll;
  String? _desktopToken;
  Uri? _desktopEndpoint;
  Map<String, dynamic>? desktopState;
  bool desktopConnecting = false;
  String? desktopError;

  bool get desktopConnected => desktopState != null && desktopError == null;

  String get season =>
      (tasksFeed['season'] ?? newsFeed['season'] ?? 'The Division 2')
          .toString();
  List<Map<String, dynamic>> get tasks => _maps(tasksFeed['tasks']);
  List<Map<String, dynamic>> get news => _maps(newsFeed['items']);
  List<Map<String, dynamic>> get builds => _maps(metaBuilds['builds']);
  int get activeNews => news.where((e) => _isCurrent(e)).length;
  int get doneCount => completedTasks.length;

  Future<void> load() async {
    try {
      final loaded = await Future.wait([
        _asset('assets/data/tasks_feed.json'),
        _asset('assets/data/news_feed.json'),
        _asset('assets/data/meta_builds.json'),
      ]);
      tasksFeed = loaded[0];
      newsFeed = loaded[1];
      metaBuilds = loaded[2];
      _prefs = await SharedPreferences.getInstance();
      completedTasks = (_prefs?.getStringList('completed_tasks') ?? <String>[])
          .toSet();
      final rawBuilds = _prefs?.getStringList('saved_builds') ?? <String>[];
      savedBuilds = rawBuilds
          .map((row) {
            try {
              final value = jsonDecode(row);
              return value is Map ? Map<String, dynamic>.from(value) : null;
            } catch (_) {
              return null;
            }
          })
          .whereType<Map<String, dynamic>>()
          .toList();
    } catch (e) {
      refreshMessage = 'Yerel oyun verisi açılamadı: $e';
    }
    loading = false;
    notifyListeners();
    await refresh(quiet: true);
  }

  Future<Map<String, dynamic>> _asset(String path) async {
    final text = await rootBundle.loadString(path);
    final decoded = jsonDecode(text);
    if (decoded is! Map) {
      throw FormatException('Beklenmeyen veri biçimi: $path');
    }
    return Map<String, dynamic>.from(decoded);
  }

  Future<Map<String, dynamic>?> _fetch(String file) async {
    final uri = Uri.https(
      'raw.githubusercontent.com',
      '/FEDERALTURK/td2-loot-advisor/main/meta/$file',
    );
    try {
      final response = await http
          .get(uri, headers: const {'User-Agent': 'TD2-Loot-Advisor-Companion'})
          .timeout(const Duration(seconds: 8));
      if (response.statusCode != 200) return null;
      final value = jsonDecode(utf8.decode(response.bodyBytes));
      if (value is! Map) return null;
      return Map<String, dynamic>.from(value);
    } catch (_) {
      return null;
    }
  }

  Future<void> refresh({bool quiet = false}) async {
    if (refreshing) return;
    refreshing = true;
    if (!quiet) {
      refreshMessage = null;
      notifyListeners();
    }
    final results = await Future.wait([
      _fetch('tasks_feed.json'),
      _fetch('news_feed.json'),
      _fetch('meta_builds.json'),
    ]);
    var changed = false;
    if (results[0]?['tasks'] is List &&
        (results[0]!['tasks'] as List).isNotEmpty) {
      tasksFeed = results[0]!;
      changed = true;
    }
    if (results[1]?['items'] is List &&
        (results[1]!['items'] as List).isNotEmpty) {
      newsFeed = results[1]!;
      changed = true;
    }
    if (results[2]?['builds'] is List &&
        (results[2]!['builds'] as List).isNotEmpty) {
      metaBuilds = results[2]!;
      changed = true;
    }
    refreshing = false;
    lastRefresh = DateTime.now();
    if (!changed) refreshMessage = 'Çevrimdışı içerik gösteriliyor';
    notifyListeners();
  }

  Future<void> toggleTask(String id) async {
    if (completedTasks.contains(id)) {
      completedTasks.remove(id);
    } else {
      completedTasks.add(id);
    }
    await _prefs?.setStringList('completed_tasks', completedTasks.toList());
    notifyListeners();
  }

  Future<void> saveBuild(Map<String, dynamic> build) async {
    savedBuilds.insert(0, build);
    await _prefs?.setStringList(
      'saved_builds',
      savedBuilds.map(jsonEncode).toList(),
    );
    notifyListeners();
  }

  Future<void> deleteBuild(String id) async {
    savedBuilds.removeWhere((build) => build['id'] == id);
    await _prefs?.setStringList(
      'saved_builds',
      savedBuilds.map(jsonEncode).toList(),
    );
    notifyListeners();
  }

  Future<bool> connectDesktop(String rawUrl) async {
    final scanned = Uri.tryParse(rawUrl.trim());
    if (scanned == null ||
        scanned.scheme != 'http' ||
        (scanned.path != '/' && scanned.path != '/index.html')) {
      desktopError = 'Geçerli bir masaüstü Telefon Arkadaşı QR kodu değil.';
      notifyListeners();
      return false;
    }
    final address = InternetAddress.tryParse(scanned.host);
    if (address == null ||
        address.type != InternetAddressType.IPv4 ||
        !_isPrivateIpv4(address.address)) {
      desktopError =
          'Güvenlik için yalnızca yerel Wi-Fi IPv4 adresleri kabul edilir.';
      notifyListeners();
      return false;
    }
    final token = scanned.queryParameters['t'];
    if (token == null || token.length < 12 || token.length > 128) {
      desktopError = 'QR bağlantı anahtarı eksik veya geçersiz.';
      notifyListeners();
      return false;
    }
    _desktopPoll?.cancel();
    _desktopToken = token;
    _desktopEndpoint = scanned.replace(
      path: '/api/state',
      queryParameters: {'t': token},
      fragment: '',
    );
    desktopConnecting = true;
    desktopError = null;
    notifyListeners();
    final connected = await _pollDesktop();
    if (connected) {
      _desktopPoll = Timer.periodic(
        const Duration(seconds: 2),
        (_) => _pollDesktop(),
      );
    }
    desktopConnecting = false;
    notifyListeners();
    return connected;
  }

  Future<bool> _pollDesktop() async {
    final endpoint = _desktopEndpoint;
    if (endpoint == null || _desktopToken == null) return false;
    try {
      final response = await http
          .get(
            endpoint,
            headers: const {'User-Agent': 'TD2-Loot-Advisor-Companion/0.1.2'},
          )
          .timeout(const Duration(seconds: 4));
      if (response.statusCode != 200) {
        desktopError = response.statusCode == 403
            ? 'Bağlantı anahtarı reddedildi. Masaüstünden yeni QR kod okut.'
            : 'Masaüstü yanıt vermedi (${response.statusCode}).';
        desktopState = null;
      } else {
        final value = jsonDecode(utf8.decode(response.bodyBytes));
        if (value is! Map) {
          throw const FormatException('JSON nesnesi bekleniyordu');
        }
        desktopState = Map<String, dynamic>.from(value);
        desktopError = null;
      }
      notifyListeners();
      return desktopState != null;
    } catch (_) {
      desktopState = null;
      desktopError = 'Masaüstüne ulaşılamıyor. İki cihazın aynı Wi-Fi’da olduğunu ve Telefon Arkadaşı’nın açık olduğunu kontrol et.';
      notifyListeners();
      return false;
    }
  }

  void disconnectDesktop() {
    _desktopPoll?.cancel();
    _desktopPoll = null;
    _desktopToken = null;
    _desktopEndpoint = null;
    desktopState = null;
    desktopError = null;
    desktopConnecting = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _desktopPoll?.cancel();
    super.dispose();
  }
}

bool _isPrivateIpv4(String value) {
  final octets = value.split('.').map(int.tryParse).toList();
  if (octets.length != 4 ||
      octets.any((part) => part == null || part < 0 || part > 255)) {
    return false;
  }
  final a = octets[0]!, b = octets[1]!;
  return a == 10 || a == 192 && b == 168 || a == 172 && b >= 16 && b <= 31;
}

class MainShell extends StatefulWidget {
  const MainShell({super.key, required this.model});
  final CompanionModel model;

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int selected = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      OverviewPage(model: widget.model),
      TasksPage(model: widget.model),
      BuildsPage(model: widget.model),
      NewsPage(model: widget.model),
    ];
    return AnimatedBuilder(
      animation: widget.model,
      builder: (context, _) => Scaffold(
        appBar: AppBar(
          titleSpacing: 20,
          title: Row(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: _orange.withValues(alpha: .14),
                  borderRadius: BorderRadius.circular(11),
                  border: Border.all(color: _orange.withValues(alpha: .6)),
                ),
                child: const Icon(
                  Icons.hexagon_outlined,
                  color: _orange,
                  size: 22,
                ),
              ),
              const SizedBox(width: 10),
              const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'TD2 LOOT ADVISOR',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                      letterSpacing: .8,
                    ),
                  ),
                  Text(
                    'COMPANION  ·  BETA 0.1.2',
                    style: TextStyle(
                      fontSize: 9,
                      color: _soft,
                      letterSpacing: 1.2,
                    ),
                  ),
                ],
              ),
            ],
          ),
          actions: [
            IconButton(
              tooltip: widget.model.refreshing
                  ? 'Güncelleniyor'
                  : 'İçeriği güncelle',
              onPressed: widget.model.refreshing
                  ? null
                  : () => widget.model.refresh(),
              icon: widget.model.refreshing
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.sync_rounded),
            ),
            IconButton(
              tooltip: 'Beta hakkında',
              onPressed: () => _about(context),
              icon: const Icon(Icons.info_outline_rounded),
            ),
            const SizedBox(width: 8),
          ],
        ),
        body: IndexedStack(index: selected, children: pages),
        floatingActionButton: selected == 2
            ? FloatingActionButton.extended(
                onPressed: () => _newBuild(context, widget.model),
                backgroundColor: _orange,
                foregroundColor: Colors.white,
                icon: const Icon(Icons.add_rounded),
                label: const Text('Build oluştur'),
              )
            : null,
        bottomNavigationBar: NavigationBar(
          selectedIndex: selected,
          onDestinationSelected: (index) => setState(() => selected = index),
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.grid_view_rounded),
              label: 'Özet',
            ),
            NavigationDestination(
              icon: Icon(Icons.checklist_rounded),
              label: 'Görevler',
            ),
            NavigationDestination(
              icon: Icon(Icons.bolt_rounded),
              label: 'Buildler',
            ),
            NavigationDestination(
              icon: Icon(Icons.newspaper_rounded),
              label: 'Haberler',
            ),
          ],
        ),
      ),
    );
  }
}

class OverviewPage extends StatelessWidget {
  const OverviewPage({super.key, required this.model});
  final CompanionModel model;

  @override
  Widget build(BuildContext context) {
    final active = model.news.where(_isCurrent).toList();
    final featured = model.builds.isNotEmpty ? model.builds.first : null;
    return RefreshIndicator(
      onRefresh: () => model.refresh(),
      color: _orange,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
        children: [
          Text('SAHA ÖZETİ', style: _eyebrow),
          const SizedBox(height: 5),
          Text(
            model.season,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(22),
              gradient: const LinearGradient(
                colors: [
                  Color(0xFF3A2118),
                  Color(0xFF191820),
                  Color(0xFF121722),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              border: Border.all(color: _orange.withValues(alpha: .3)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.radar_rounded, color: _orange),
                    const SizedBox(width: 9),
                    const Text(
                      'GÜNCEL DURUM',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.1,
                      ),
                    ),
                    const Spacer(),
                    if (model.refreshing)
                      const SizedBox(
                        width: 15,
                        height: 15,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                  ],
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: _Metric(
                        value: '${model.tasks.length}',
                        label: 'görev',
                      ),
                    ),
                    Expanded(
                      child: _Metric(
                        value: '${active.length}',
                        label: 'aktif içerik',
                      ),
                    ),
                    Expanded(
                      child: _Metric(
                        value: '${model.savedBuilds.length}',
                        label: 'kayıtlı build',
                      ),
                    ),
                  ],
                ),
                if (model.refreshMessage != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    model.refreshMessage!,
                    style: const TextStyle(color: _soft, fontSize: 12),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 22),
          const SectionTitle(
            title: 'MASAÜSTÜ EŞLEŞTİRMESİ',
            trailing: 'SONRAKİ AŞAMA',
          ),
          const SizedBox(height: 10),
          _DesktopStatusCard(model: model),
          const SizedBox(height: 22),
          SectionTitle(
            title: 'AKTİF ETKİNLİKLER',
            trailing: '${active.length} KAYIT',
          ),
          const SizedBox(height: 10),
          if (active.isEmpty)
            const _EmptyCard(
              icon: Icons.event_busy_rounded,
              text: 'Şu anda aktif etkinlik görünmüyor.',
            )
          else
            ...active
                .take(3)
                .map((item) => NewsCard(item: item, compact: true)),
          const SizedBox(height: 22),
          SectionTitle(title: 'ÖNE ÇIKAN BUILD', trailing: 'META KÜTÜPHANESİ'),
          const SizedBox(height: 10),
          if (featured == null)
            const _EmptyCard(
              icon: Icons.bolt_rounded,
              text: 'Build önerileri yüklenemedi.',
            )
          else
            MetaBuildCard(data: featured),
          if (model.lastRefresh != null) ...[
            const SizedBox(height: 18),
            Text(
              'Son kontrol: ${_dateTime(model.lastRefresh!)}',
              style: const TextStyle(color: _soft, fontSize: 11),
            ),
          ],
        ],
      ),
    );
  }
}

class TasksPage extends StatefulWidget {
  const TasksPage({super.key, required this.model});
  final CompanionModel model;

  @override
  State<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends State<TasksPage> {
  String category = 'all';

  @override
  Widget build(BuildContext context) {
    final all = widget.model.tasks;
    final filtered = category == 'all'
        ? all
        : all.where((task) => task['cat'] == category).toList();
    final done = all
        .where((task) => widget.model.completedTasks.contains('${task['id']}'))
        .length;
    return RefreshIndicator(
      onRefresh: () => widget.model.refresh(),
      color: _orange,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
        children: [
          Text('GÖREV TAKİBİ', style: _eyebrow),
          const SizedBox(height: 4),
          const Text(
            'Bu sezon',
            style: TextStyle(fontSize: 25, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 14),
          _ProgressCard(
            done: done,
            total: all.length,
            season: widget.model.season,
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            children: [
              _filter('all', 'Tümü'),
              _filter('manhunt', 'Manhunt'),
              _filter('projects', 'Projeler'),
              _filter('journey', 'Journey'),
            ],
          ),
          const SizedBox(height: 12),
          if (filtered.isEmpty)
            const _EmptyCard(
              icon: Icons.assignment_turned_in_outlined,
              text: 'Görev verisi yok. Yenilemeyi deneyin.',
            )
          else
            ...filtered.map(
              (task) => TaskCard(
                task: task,
                done: widget.model.completedTasks.contains('${task['id']}'),
                onChanged: () => widget.model.toggleTask('${task['id']}'),
              ),
            ),
          const SizedBox(height: 10),
          const Text(
            'Görevler cihazında saklanan şekilde işaretlenir; oyun hesabından otomatik doğrulanmaz.',
            style: TextStyle(color: _soft, fontSize: 11),
          ),
        ],
      ),
    );
  }

  Widget _filter(String value, String label) => FilterChip(
    label: Text(label),
    selected: category == value,
    showCheckmark: false,
    selectedColor: _orange.withValues(alpha: .22),
    side: BorderSide(color: category == value ? _orange : Colors.white12),
    onSelected: (_) => setState(() => category = value),
  );
}

class BuildsPage extends StatefulWidget {
  const BuildsPage({super.key, required this.model});
  final CompanionModel model;

  @override
  State<BuildsPage> createState() => _BuildsPageState();
}

class _BuildsPageState extends State<BuildsPage> {
  int tab = 0;
  String query = '';

  @override
  Widget build(BuildContext context) {
    final meta = widget.model.builds.where((build) {
      final text = '${build['name']} ${build['mode']} ${build['role']}'
          .toLowerCase();
      return text.contains(query.toLowerCase());
    }).toList();
    final saved = widget.model.savedBuilds.where((build) {
      return '${build['name']} ${build['playstyle']}'.toLowerCase().contains(
        query.toLowerCase(),
      );
    }).toList();
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
      children: [
        Text('BUILD KÜTÜPHANESİ', style: _eyebrow),
        const SizedBox(height: 4),
        const Text(
          'Ajanını hazırla',
          style: TextStyle(fontSize: 25, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 15),
        TextField(
          decoration: const InputDecoration(
            prefixIcon: Icon(Icons.search),
            hintText: 'Build veya rol ara',
          ),
          onChanged: (value) => setState(() => query = value),
        ),
        const SizedBox(height: 12),
        SegmentedButton<int>(
          segments: const [
            ButtonSegment(
              value: 0,
              label: Text('Önerilen'),
              icon: Icon(Icons.auto_awesome),
            ),
            ButtonSegment(
              value: 1,
              label: Text('Kaydettiklerim'),
              icon: Icon(Icons.bookmark_outline),
            ),
          ],
          selected: {tab},
          onSelectionChanged: (values) => setState(() => tab = values.first),
        ),
        const SizedBox(height: 14),
        if (tab == 0)
          if (meta.isEmpty)
            const _EmptyCard(
              icon: Icons.search_off_rounded,
              text: 'Aramaya uygun öneri bulunamadı.',
            )
          else
            ...meta.map((build) => MetaBuildCard(data: build))
        else if (saved.isEmpty)
          const _EmptyCard(
            icon: Icons.bookmark_add_outlined,
            text:
                'Henüz build kaydetmedin. + düğmesiyle ilk build’ini oluştur.',
          )
        else
          ...saved.map(
            (build) => SavedBuildCard(
              data: build,
              onDelete: () => widget.model.deleteBuild('${build['id']}'),
            ),
          ),
      ],
    );
  }
}

class NewsPage extends StatelessWidget {
  const NewsPage({super.key, required this.model});
  final CompanionModel model;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: () => model.refresh(),
    color: _orange,
    child: ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
      children: [
        Text('SAHA HABERLERİ', style: _eyebrow),
        const SizedBox(height: 4),
        const Text(
          'Güncel gelişmeler',
          style: TextStyle(fontSize: 25, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 6),
        Text(
          'Kaynak ve yayın bağlantıları her içerikte gösterilir.',
          style: TextStyle(color: _soft, fontSize: 13),
        ),
        const SizedBox(height: 16),
        if (model.news.isEmpty)
          const _EmptyCard(
            icon: Icons.newspaper_rounded,
            text: 'Haber akışı bulunamadı.',
          )
        else
          ...model.news.map((item) => NewsCard(item: item)),
      ],
    ),
  );
}

class TaskCard extends StatelessWidget {
  const TaskCard({
    super.key,
    required this.task,
    required this.done,
    required this.onChanged,
  });
  final Map<String, dynamic> task;
  final bool done;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    final title = _localized(task['text']);
    final how = _localized(task['how']);
    final source = task['source'] is Map
        ? (task['source']['url'] ?? '').toString()
        : '';
    return Card(
      margin: const EdgeInsets.only(bottom: 9),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        child: Column(
          children: [
            CheckboxListTile(
              value: done,
              onChanged: (_) => onChanged(),
              controlAffinity: ListTileControlAffinity.leading,
              title: Text(
                title,
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  decoration: done ? TextDecoration.lineThrough : null,
                ),
              ),
              subtitle: Padding(
                padding: const EdgeInsets.only(top: 5),
                child: Row(
                  children: [
                    _Tag(_categoryLabel(task['cat'])),
                    const SizedBox(width: 8),
                    if (task['kind'] != null)
                      Text(
                        '${task['kind']}',
                        style: const TextStyle(color: _soft, fontSize: 11),
                      ),
                  ],
                ),
              ),
            ),
            if (how.isNotEmpty || source.isNotEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 13),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (how.isNotEmpty)
                      Expanded(
                        child: Text(
                          how,
                          style: const TextStyle(
                            color: _soft,
                            fontSize: 12,
                            height: 1.4,
                          ),
                        ),
                      ),
                    if (source.isNotEmpty)
                      IconButton(
                        tooltip: 'Kaynağı aç',
                        visualDensity: VisualDensity.compact,
                        onPressed: () => _open(source),
                        icon: const Icon(
                          Icons.open_in_new_rounded,
                          size: 18,
                          color: _orange,
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class MetaBuildCard extends StatelessWidget {
  const MetaBuildCard({super.key, required this.data});
  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final sets = data['sets_or_brands'] is List
        ? (data['sets_or_brands'] as List).map((e) => e.toString()).join(' · ')
        : '';
    final sources = data['sources'] is List
        ? (data['sources'] as List)
        : const [];
    final sourceUrl = sources.isNotEmpty && sources.first is Map
        ? '${sources.first['url'] ?? ''}'
        : '';
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(17)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: _orange.withValues(alpha: .13),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.bolt_rounded, color: _orange),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${data['name'] ?? 'Önerilen build'}',
                        style: const TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${data['mode'] ?? 'PvE'}  ·  ${_roleLabel(data['role'])}',
                        style: const TextStyle(color: _soft, fontSize: 11),
                      ),
                    ],
                  ),
                ),
                if (data['popularity'] != null)
                  _Tag('META ${data['popularity']}'),
              ],
            ),
            if (sets.isNotEmpty) ...[
              const SizedBox(height: 13),
              Text(
                sets,
                style: const TextStyle(
                  color: Color(0xFFFFB274),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
            if (_localized(data['summary']).isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                _localized(data['summary']),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: _soft,
                  fontSize: 12,
                  height: 1.35,
                ),
              ),
            ],
            if (sourceUrl.isNotEmpty) ...[
              const SizedBox(height: 6),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: () => _open(sourceUrl),
                  icon: const Icon(Icons.source_outlined, size: 17),
                  label: const Text('Kaynakları gör'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class SavedBuildCard extends StatelessWidget {
  const SavedBuildCard({super.key, required this.data, required this.onDelete});
  final Map<String, dynamic> data;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 10),
    child: ListTile(
      leading: const CircleAvatar(
        backgroundColor: Color(0xFF302015),
        child: Icon(Icons.shield_outlined, color: _orange),
      ),
      title: Text(
        '${data['name'] ?? ''}',
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
      subtitle: Text(
        '${data['playstyle'] ?? ''}\n${data['gear'] ?? ''}',
        maxLines: 3,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(color: _soft, height: 1.4),
      ),
      isThreeLine: true,
      trailing: IconButton(
        tooltip: 'Build’i sil',
        onPressed: onDelete,
        icon: const Icon(Icons.delete_outline),
      ),
    ),
  );
}

class NewsCard extends StatelessWidget {
  const NewsCard({super.key, required this.item, this.compact = false});
  final Map<String, dynamic> item;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final title = _localized(item['title']);
    final body = _localized(item['text']);
    final url = '${item['url'] ?? ''}';
    final active = _isCurrent(item);
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(17)),
      child: InkWell(
        onTap: url.isEmpty ? null : () => _open(url),
        child: Padding(
          padding: const EdgeInsets.all(15),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  _Tag(active ? 'AKTİF' : _kindLabel(item['kind'])),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${item['source'] ?? 'Kaynak'}',
                      style: const TextStyle(color: _soft, fontSize: 11),
                    ),
                  ),
                  if (url.isNotEmpty)
                    const Icon(
                      Icons.open_in_new_rounded,
                      color: _soft,
                      size: 16,
                    ),
                ],
              ),
              const SizedBox(height: 9),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
                ),
              ),
              if (body.isNotEmpty && !compact) ...[
                const SizedBox(height: 7),
                Text(
                  body,
                  maxLines: 4,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: _soft,
                    fontSize: 12,
                    height: 1.4,
                  ),
                ),
              ],
              if (item['start'] != null || item['end'] != null) ...[
                const SizedBox(height: 8),
                Text(
                  '${_shortDate(item['start'])}  —  ${_shortDate(item['end'])}',
                  style: const TextStyle(
                    color: Color(0xFF748093),
                    fontSize: 10,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ProgressCard extends StatelessWidget {
  const _ProgressCard({
    required this.done,
    required this.total,
    required this.season,
  });
  final int done;
  final int total;
  final String season;

  @override
  Widget build(BuildContext context) {
    final progress = total == 0 ? 0.0 : (done / total).clamp(0.0, 1.0);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            season,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: _soft, fontSize: 12),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(99),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 8,
                    backgroundColor: Colors.white10,
                    color: _orange,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text(
                '$done / $total',
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DesktopStatusCard extends StatelessWidget {
  const _DesktopStatusCard({required this.model});
  final CompanionModel model;

  @override
  Widget build(BuildContext context) => InkWell(
    borderRadius: BorderRadius.circular(17),
    onTap: model.desktopConnected || model.desktopConnecting
        ? null
        : () => Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => DesktopPairPage(model: model),
            ),
          ),
    child: Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(17),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .06),
              borderRadius: BorderRadius.circular(13),
            ),
            child: const Icon(Icons.desktop_windows_outlined, color: _soft),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Windows Loot Advisor',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                ),
                SizedBox(height: 4),
                Text(
                  model.desktopConnecting
                      ? 'Masaüstü doğrulanıyor…'
                      : model.desktopConnected
                      ? '${model.desktopState?['verdict_label'] ?? 'Bağlandı'} · ${model.desktopState?['item']?['name'] ?? 'Canlı eşleşme'}'
                      : model.desktopError ??
                            'QR kodu okut ve aynı Wi-Fi üzerinden eşleştir',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: _soft, fontSize: 11),
                ),
              ],
            ),
          ),
          if (model.desktopConnected)
            IconButton(
              tooltip: 'Masaüstü bağlantısını kes',
              onPressed: model.disconnectDesktop,
              icon: const Icon(
                Icons.link_off_rounded,
                color: _orange,
                size: 19,
              ),
            )
          else
            Icon(
              model.desktopConnecting
                  ? Icons.sync_rounded
                  : Icons.qr_code_scanner_rounded,
              color: _soft,
              size: 20,
            ),
        ],
      ),
    ),
  );
}

class DesktopPairPage extends StatefulWidget {
  const DesktopPairPage({super.key, required this.model});
  final CompanionModel model;

  @override
  State<DesktopPairPage> createState() => _DesktopPairPageState();
}

class _DesktopPairPageState extends State<DesktopPairPage> {
  bool handled = false;
  String? message;

  Future<void> _handle(String raw) async {
    if (handled) return;
    handled = true;
    final connected = await widget.model.connectDesktop(raw);
    if (!mounted) return;
    if (connected) {
      Navigator.of(context).pop();
    } else {
      setState(() {
        message = widget.model.desktopError;
        handled = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Masaüstü eşleştir')),
    body: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text('QR KODU OKUT', style: _eyebrow),
        const SizedBox(height: 8),
        const Text(
          'Windows programında Ayarlar → Senkronizasyon → Telefon Arkadaşı bölümünden sunucuyu başlat. Ekrandaki QR kodu bu kameraya göster.',
          style: TextStyle(color: _soft, height: 1.45),
        ),
        const SizedBox(height: 18),
        ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: SizedBox(
            height: 330,
            child: MobileScanner(
              onDetect: (capture) {
                final raw = capture.barcodes.firstOrNull?.rawValue;
                if (raw != null) _handle(raw);
              },
            ),
          ),
        ),
        if (message != null) ...[
          const SizedBox(height: 14),
          Text(message!, style: const TextStyle(color: Color(0xFFFF8A80))),
        ],
        const SizedBox(height: 16),
        const _EmptyCard(
          icon: Icons.wifi_rounded,
          text: 'Telefon ve bilgisayar aynı güvenilir Wi-Fi ağına bağlı olmalı. Bağlantı yalnızca görüntüleme içindir; uygulama bilgisayara komut göndermez.',
        ),
      ],
    ),
  );
}

class _Metric extends StatelessWidget {
  const _Metric({required this.value, required this.label});
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        value,
        style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w900),
      ),
      const SizedBox(height: 2),
      Text(label, style: const TextStyle(color: _soft, fontSize: 11)),
    ],
  );
}

class SectionTitle extends StatelessWidget {
  const SectionTitle({super.key, required this.title, this.trailing});
  final String title;
  final String? trailing;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Expanded(child: Text(title, style: _eyebrow)),
      if (trailing != null)
        Text(
          trailing!,
          style: const TextStyle(color: _soft, fontSize: 9, letterSpacing: .8),
        ),
    ],
  );
}

class _Tag extends StatelessWidget {
  const _Tag(this.label);
  final String label;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
    decoration: BoxDecoration(
      color: _orange.withValues(alpha: .12),
      borderRadius: BorderRadius.circular(99),
    ),
    child: Text(
      label.toUpperCase(),
      style: const TextStyle(
        color: Color(0xFFFFA563),
        fontSize: 9,
        fontWeight: FontWeight.w800,
      ),
    ),
  );
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: _panel,
      borderRadius: BorderRadius.circular(17),
    ),
    child: Row(
      children: [
        Icon(icon, color: _soft),
        const SizedBox(width: 12),
        Expanded(
          child: Text(text, style: const TextStyle(color: _soft)),
        ),
      ],
    ),
  );
}

Future<void> _newBuild(BuildContext context, CompanionModel model) async {
  final name = TextEditingController();
  final playstyle = TextEditingController(text: 'PvE / DPS');
  final gear = TextEditingController();
  final notes = TextEditingController();
  final formKey = GlobalKey<FormState>();
  await showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: _panel,
    showDragHandle: true,
    builder: (sheetContext) => Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        8,
        20,
        MediaQuery.of(sheetContext).viewInsets.bottom + 24,
      ),
      child: Form(
        key: formKey,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Yeni build',
                style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 6),
              const Text(
                'Build cihazında saklanır; masaüstüyle eşitleme henüz etkin değil.',
                style: TextStyle(color: _soft, fontSize: 12),
              ),
              const SizedBox(height: 18),
              TextFormField(
                controller: name,
                autofocus: true,
                maxLength: 50,
                decoration: const InputDecoration(labelText: 'Build adı'),
                validator: (value) => value == null || value.trim().isEmpty
                    ? 'Bir ad gir.'
                    : null,
              ),
              const SizedBox(height: 10),
              TextField(
                controller: playstyle,
                maxLength: 40,
                decoration: const InputDecoration(labelText: 'İçerik / rol'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: gear,
                maxLines: 3,
                maxLength: 240,
                decoration: const InputDecoration(
                  labelText: 'Set ve markalar',
                  hintText: 'Striker, Grupo Sombra…',
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: notes,
                maxLines: 3,
                maxLength: 300,
                decoration: const InputDecoration(
                  labelText: 'Notlar',
                  hintText: 'Silah, yetenek veya oynanış notu',
                ),
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: () async {
                  if (formKey.currentState?.validate() != true) return;
                  await model.saveBuild({
                    'id': DateTime.now().microsecondsSinceEpoch.toString(),
                    'name': name.text.trim(),
                    'playstyle': playstyle.text.trim(),
                    'gear': gear.text.trim(),
                    'notes': notes.text.trim(),
                    'created': DateTime.now().toIso8601String(),
                  });
                  if (sheetContext.mounted) Navigator.pop(sheetContext);
                },
                icon: const Icon(Icons.save_outlined),
                label: const Text('Build’i kaydet'),
              ),
            ],
          ),
        ),
      ),
    ),
  );
  name.dispose();
  playstyle.dispose();
  gear.dispose();
  notes.dispose();
}

void _about(BuildContext context) => showAboutDialog(
  context: context,
  applicationName: 'TD2 Loot Advisor Companion',
  applicationVersion: '0.1.2-beta',
  applicationIcon: const Icon(Icons.hexagon_outlined, color: _orange, size: 34),
  children: [
    const Text(
      'Görev, haber ve yerel build takibine ek olarak aynı Wi-Fi ağındaki Windows programına QR kodla salt-okunur bağlanır.',
    ),
    const SizedBox(height: 10),
    const Text(
      'The Division 2, Ubisoft’un ticari markasıdır. Bu bağımsız yardımcı uygulama Ubisoft ile bağlantılı veya Ubisoft tarafından desteklenen bir ürün değildir.',
    ),
    const SizedBox(height: 8),
    TextButton.icon(
      onPressed: () => _open(
        'https://github.com/FEDERALTURK/td2-loot-advisor/blob/main/mobile/PRIVACY_POLICY_TR.md',
      ),
      icon: Icon(Icons.privacy_tip_outlined),
      label: Text('Gizlilik politikası'),
    ),
  ],
);

Future<void> _open(String raw) async {
  final uri = Uri.tryParse(raw);
  if (uri == null || (uri.scheme != 'https' && uri.scheme != 'http')) return;
  await launchUrl(uri, mode: LaunchMode.externalApplication);
}

List<Map<String, dynamic>> _maps(dynamic value) => value is List
    ? value
          .whereType<Map>()
          .map((row) => Map<String, dynamic>.from(row))
          .toList()
    : <Map<String, dynamic>>[];

String _localized(dynamic value) {
  if (value is Map) return '${value['tr'] ?? value['en'] ?? ''}';
  return value?.toString() ?? '';
}

bool _isCurrent(Map<String, dynamic> item) {
  final now = DateTime.now().toUtc();
  final start = DateTime.tryParse('${item['start'] ?? ''}')?.toUtc();
  final end = DateTime.tryParse('${item['end'] ?? ''}')?.toUtc();
  if (start != null && now.isBefore(start)) return false;
  if (end != null && now.isAfter(end)) return false;
  return item['kind'] == 'event' ||
      item['kind'] == 'season' ||
      (end != null && now.isBefore(end));
}

String _dateTime(DateTime value) =>
    '${value.day.toString().padLeft(2, '0')}.${value.month.toString().padLeft(2, '0')} ${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';

String _shortDate(dynamic raw) {
  final date = DateTime.tryParse('${raw ?? ''}')?.toLocal();
  if (date == null) return '—';
  return '${date.day.toString().padLeft(2, '0')}.${date.month.toString().padLeft(2, '0')}.${date.year}';
}

String _categoryLabel(dynamic value) => switch ('$value') {
  'manhunt' => 'Manhunt',
  'projects' => 'Projeler',
  'journey' => 'Journey',
  _ => '$value'.isEmpty || value == null ? 'Görev' : '$value',
};

String _kindLabel(dynamic value) => switch ('$value') {
  'news' => 'HABER',
  'patch' => 'GÜNCELLEME',
  'season' => 'SEZON',
  _ => 'BİLGİ',
};

String _roleLabel(dynamic value) => switch ('$value') {
  'dps' => 'Hasar',
  'tank' => 'Tank',
  'skill' => 'Yetenek',
  'heal' => 'İyileştirme',
  _ => value == null ? 'Genel' : '$value',
};

const _eyebrow = TextStyle(
  color: _orange,
  fontSize: 10,
  fontWeight: FontWeight.w800,
  letterSpacing: 1.2,
);
