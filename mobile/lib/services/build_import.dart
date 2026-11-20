import 'dart:convert';

const _maxImportBytes = 2 * 1024 * 1024;
const _slots = {
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
};
const _itemFields = {
  'name',
  'core',
  'brand',
  'gear_set',
  'talent',
  'quality',
  'attrs',
  'fixed_attributes',
  'attachments',
  'mod_slots',
  'weapon_stats',
};

List<Map<String, dynamic>> parseDesktopBuildExport(String raw) {
  if (utf8.encode(raw).length > _maxImportBytes) {
    throw const FormatException('Dışa aktarma dosyası 2 MB sınırını aşıyor.');
  }
  final decoded = jsonDecode(raw);
  if (decoded is! Map || decoded['builds'] is! List) {
    throw const FormatException(
      'Geçerli bir masaüstü Build Tool JSON dosyası değil.',
    );
  }
  final rows = (decoded['builds'] as List).whereType<Map>().toList();
  if (rows.isEmpty || rows.length > 200) {
    throw const FormatException(
      'Dosyada içe aktarılabilir build yok veya 200 build sınırı aşılıyor.',
    );
  }
  return [
    for (var index = 0; index < rows.length; index++)
      _convert(rows[index], index),
  ];
}

Map<String, dynamic> _convert(Map row, int index) {
  final name = row['name'];
  if (name is! String || name.trim().isEmpty) {
    throw const FormatException('Build adı eksik veya geçersiz.');
  }
  final sourceSlots = row['slots'];
  final slots = <String, dynamic>{};
  if (sourceSlots is Map) {
    for (final entry in sourceSlots.entries) {
      final slot = '${entry.key}';
      if (!_slots.contains(slot) || entry.value is! Map) continue;
      final item = <String, dynamic>{};
      for (final field in _itemFields) {
        final value = entry.value[field];
        if (value == null) continue;
        if (field == 'attrs' || field == 'weapon_stats') {
          if (value is Map) item[field] = Map<String, dynamic>.from(value);
        } else if (field == 'attachments' ||
            field == 'fixed_attributes' ||
            field == 'mod_slots') {
          if (value is List) item[field] = value;
        } else if (value is String || value is num || value is bool) {
          item[field] = _limit('$value', 120);
        }
      }
      slots[slot] = item;
    }
  }
  final specialization = row['specialization'] is String
      ? row['specialization'] as String
      : '';
  final gear = slots.values
      .whereType<Map>()
      .map((item) => item['name'])
      .whereType<String>()
      .where((item) => item.isNotEmpty)
      .join(', ');
  return {
    'id': '${DateTime.now().microsecondsSinceEpoch}-$index',
    'name': _limit(name.trim(), 80),
    'playstyle': specialization,
    'specialization': specialization,
    'gear': gear,
    'slots': slots,
    'shd_levels': row['shd_levels'] is Map
        ? row['shd_levels']
        : <String, dynamic>{},
    'created': DateTime.now().toIso8601String(),
  };
}

String _limit(String value, int limit) =>
    value.length > limit ? value.substring(0, limit) : value;
