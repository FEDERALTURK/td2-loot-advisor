import 'dart:math' as math;

const buildSlots = [
  'Mask',
  'Backpack',
  'Chest',
  'Gloves',
  'Holster',
  'Kneepads',
  'Primary',
  'Secondary',
  'SideArm',
  'Specialization',
  'Skill1',
  'Skill2',
];
const statKeys = [
  'weapon_damage',
  'headshot_damage',
  'crit_chance',
  'crit_damage',
  'reload_speed',
  'stability',
  'accuracy',
  'ammo_capacity',
  'armor',
  'explosive_resistance',
  'hazard_protection',
  'health',
  'skill_haste',
  'skill_damage',
  'skill_duration',
  'repair_skills',
  'skill_tier',
];
Map<String, dynamic> objectMap(dynamic value) =>
    value is Map ? Map<String, dynamic>.from(value) : {};
double number(dynamic value, [double fallback = 0]) {
  final parsed = double.tryParse('$value'.replaceAll(',', '.'));
  return parsed != null && parsed.isFinite ? parsed : fallback;
}

String _attribute(String slug, Map<String, dynamic> attributes) {
  final normalized = slug.toLowerCase().replaceAll(RegExp('[^a-z0-9]+'), '_');
  var found = '', length = 0;
  for (final entry in attributes.entries) {
    final meta = objectMap(entry.value);
    for (final alias in [
      entry.key.replaceAll('_', ' '),
      ...?meta['aliases'] as List?,
    ]) {
      final candidate = '$alias'.toLowerCase().replaceAll(
        RegExp('[^a-z0-9]+'),
        '_',
      );
      if (candidate.length > length &&
          (normalized == candidate || normalized.startsWith('${candidate}_'))) {
        found = entry.key;
        length = candidate.length;
      }
    }
  }
  return found;
}

/// Mirrors build_tool.calculate. Conditional talents, SHD and bonus text are
/// deliberately not applied: the PC calculator does not simulate them either.
Map<String, dynamic> calculateBuild(
  Map<String, dynamic> build,
  Map<String, dynamic> catalog,
) {
  final stats = {for (final key in statKeys) key: 0.0};
  final cores = {'offensive': 0, 'defensive': 0, 'utility': 0};
  final brands = <String, int>{}, sets = <String, int>{};
  final slots = objectMap(build['slots']);
  for (final slot in buildSlots) {
    final item = objectMap(slots[slot]);
    if (item.isEmpty) continue;
    final core = '${item['core'] ?? ''}'.toLowerCase();
    if (buildSlots.take(6).contains(slot)) {
      if (core.contains('weapon') || core.contains('offensive')) {
        cores['offensive'] = cores['offensive']! + 1;
      } else if (core.contains('armor') || core.contains('defensive')) {
        cores['defensive'] = cores['defensive']! + 1;
      } else if (core.contains('skill') || core.contains('utility')) {
        cores['utility'] = cores['utility']! + 1;
      }
      for (final entry in {'brand': brands, 'gear_set': sets}.entries) {
        final name = '${item[entry.key] ?? ''}';
        if (name.isNotEmpty) entry.value[name] = (entry.value[name] ?? 0) + 1;
      }
    }
    if (!['Primary', 'Secondary', 'SideArm'].contains(slot)) {
      for (final entry in objectMap(item['attrs']).entries) {
        if (stats.containsKey(entry.key)) {
          stats[entry.key] =
              stats[entry.key]! + number(entry.value).clamp(-1000000, 1000000);
        }
      }
      if (core.contains('skill') || core.contains('utility')) {
        stats['skill_tier'] = stats['skill_tier']! + 1;
      }
    }
  }
  final weapons = <Map<String, dynamic>>[];
  final enemyHp = number(build['enemy_hp'], 2000000).clamp(1, 100000000);
  for (final slot in ['Primary', 'Secondary', 'SideArm']) {
    final item = objectMap(slots[slot]);
    if (item.isEmpty) continue;
    final attrs = objectMap(item['attrs']);
    final index = objectMap(catalog['weapon_index']);
    final meta = objectMap(
      index.entries
          .where((e) => e.key.toLowerCase() == '${item['name']}'.toLowerCase())
          .firstOrNull
          ?.value,
    );
    final base = objectMap(meta['base_stats']),
        ws = objectMap(item['weapon_stats']);
    final damage = number(attrs['base_damage'] ?? base['base_damage']);
    var rpm = number(attrs['rpm'] ?? base['base_rpm']);
    var magazine =
        number(base['base_mag_size'] ?? attrs['magazine_size']) +
        number(ws['magazine_bonus']);
    magazine *= 1 + number(ws['magazine_percent']) / 100;
    var reload = number(attrs['reload_time'] ?? base['base_reload_time']);
    final mods = <String, double>{};
    var magazinePercent = 0.0;
    for (final raw
        in (item['attachments'] is List ? item['attachments'] : []) as List) {
      for (final part in '${objectMap(raw)['stats'] ?? ''}'.split('|')) {
        final match = RegExp(
          r'^\s*([a-z0-9-]+)\s*:\s*([+-]?\d+(?:[.,]\d+)?)\s*(%)?\s*$',
          caseSensitive: false,
        ).firstMatch(part);
        if (match == null) continue;
        final key = _attribute(match[1]!, objectMap(catalog['attributes']));
        if (key.isEmpty) continue;
        mods[key] = (mods[key] ?? 0) + number(match[2]);
        if (key == 'magazine_size' && match[3] != null) {
          magazinePercent += number(match[2]);
        }
      }
    }
    if (damage <= 0 || rpm <= 0) continue;
    final wd =
        stats['weapon_damage']! +
        number(attrs['weapon_damage']) +
        number(attrs['weapon_type_damage']) +
        (mods['weapon_damage'] ?? 0) +
        (mods['weapon_type_damage'] ?? 0);
    final cc = math.min(
      60,
      stats['crit_chance']! +
          number(attrs['crit_chance']) +
          (mods['crit_chance'] ?? 0),
    );
    final cd =
        stats['crit_damage']! +
        number(attrs['crit_damage']) +
        (mods['crit_damage'] ?? 0);
    rpm *=
        1 + (number(attrs['rate_of_fire']) + (mods['rate_of_fire'] ?? 0)) / 100;
    final reloadFactor =
        1 +
        (stats['reload_speed']! +
                number(attrs['reload_speed']) +
                (mods['reload_speed'] ?? 0)) /
            100;
    if (rpm <= 0 || reloadFactor <= 0) continue;
    reload /= reloadFactor;
    magazine *= 1 + magazinePercent / 100;
    final shot =
        damage *
        (1 + cores['offensive']! * .15 + wd / 100) *
        (1 + cc / 100 * cd / 100);
    final dps = shot * rpm / 60;
    final shots = (enemyHp / math.max(shot, 1)).ceil();
    final ttk = magazine > 0 && reload > 0
        ? math.max(0, shots - 1) * 60 / rpm +
              math.max(0, (shots / magazine).ceil() - 1) * reload
        : (dps > 0 ? enemyHp / dps : 0);
    weapons.add({
      'slot': slot,
      'name': item['name'],
      'dps': dps,
      'ttk': ttk,
      'damage': damage,
      'rpm': rpm,
      'magazine': magazine,
      'reload': reload,
    });
  }
  final bonuses = <String, List<Map<String, dynamic>>>{
    'brands': [],
    'gear_sets': [],
  };
  for (final pair in [
    ('brands', brands, 'brand_bonuses', 1),
    ('gear_sets', sets, 'gear_set_bonuses', 2),
  ]) {
    for (final entry in pair.$2.entries) {
      final raw = objectMap(catalog[pair.$3])[entry.key];
      final tiers = raw is List ? raw : [];
      for (
        var i = 0;
        i < math.min(tiers.length, entry.value - pair.$4 + 1);
        i++
      ) {
        bonuses[pair.$1]!.add({
          'name': entry.key,
          'tier': i + pair.$4,
          'text': '${tiers[i]}',
        });
      }
    }
  }
  return {
    'stats': stats,
    'cores': cores,
    'armor': 660014 + cores['defensive']! * 170000 + stats['armor']!,
    'brands': brands,
    'gear_sets': sets,
    'bonuses': bonuses,
    'weapons': weapons,
    'enemy_hp': enemyHp,
  };
}
