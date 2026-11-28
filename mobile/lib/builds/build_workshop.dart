import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'build_calculator.dart';

const _orange = Color(0xFFFF6D10);
const _slots = buildSlots;

Future<Map<String, dynamic>?> openBuildWorkshop(BuildContext context) async {
  final raw = await rootBundle.loadString('assets/data/build_catalog.json');
  final catalog = Map<String, dynamic>.from(jsonDecode(raw) as Map);
  if (!context.mounted) return null;
  return showModalBottomSheet<Map<String, dynamic>>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    backgroundColor: const Color(0xFF121722),
    builder: (_) => _Workshop(catalog: catalog),
  );
}

class _Workshop extends StatefulWidget {
  const _Workshop({required this.catalog});
  final Map<String, dynamic> catalog;
  @override
  State<_Workshop> createState() => _WorkshopState();
}

class _WorkshopState extends State<_Workshop> {
  final _name = TextEditingController();
  final _selected = <String, Map<String, dynamic>>{};
  late final Map<String, List<Map<String, dynamic>>> _choices;
  late Map<String, dynamic> _calculated;

  @override
  void initState() {
    super.initState();
    final raw = objectMap(widget.catalog['choices']);
    _choices = {
      for (final slot in _slots)
        slot: (raw[slot] as List? ?? [])
            .whereType<Map>()
            .map(Map<String, dynamic>.from)
            .toList(),
    };
    _calculated = calculateBuild({'slots': _selected}, widget.catalog);
  }

  void _update(String slot, Map<String, dynamic>? item) {
    setState(() {
      if (item == null) {
        _selected.remove(slot);
      } else {
        _selected[slot] = item;
      }
      _calculated = calculateBuild({'slots': _selected}, widget.catalog);
    });
  }

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FractionallySizedBox(
    heightFactor: .94,
    child: Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 6),
          child: Row(
            children: [
              const Expanded(
                child: Text(
                  'BUILD WORKSHOP',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                ),
              ),
              IconButton(
                tooltip: 'Kapat',
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              TextField(
                controller: _name,
                maxLength: 50,
                decoration: const InputDecoration(labelText: 'Build adı'),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 10),
              ..._slots.map((slot) => _slotCard(slot)),
              const SizedBox(height: 16),
              _summary(),
              const SizedBox(height: 14),
              FilledButton.icon(
                onPressed: _selected.isEmpty || _name.text.trim().isEmpty
                    ? null
                    : () {
                        Navigator.pop(context, {
                          'id': DateTime.now().microsecondsSinceEpoch
                              .toString(),
                          'name': _name.text.trim(),
                          'playstyle': 'Özel build',
                          'gear': _selected.entries
                              .map((e) => '${e.key}: ${e.value['name']}')
                              .join('\n'),
                          'slots': _selected,
                          'calculation': _calculated,
                          'created': DateTime.now().toIso8601String(),
                        });
                      },
                icon: const Icon(Icons.save_outlined),
                label: const Text('Build’i kaydet'),
              ),
            ],
          ),
        ),
      ],
    ),
  );

  Widget _slotCard(String slot) {
    final selected = _selected[slot];
    final items = _choices[slot] ?? const [];
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              slot.toUpperCase(),
              style: const TextStyle(
                color: _orange,
                fontWeight: FontWeight.w800,
                fontSize: 11,
              ),
            ),
            Autocomplete<Map<String, dynamic>>(
              initialValue: TextEditingValue(
                text: '${selected?['name'] ?? ''}',
              ),
              displayStringForOption: (item) => '${item['name']}',
              optionsBuilder: (value) {
                final query = value.text.trim().toLowerCase();
                return items
                    .where(
                      (item) =>
                          query.isEmpty ||
                          '${item['name']}'.toLowerCase().contains(query),
                    )
                    .take(30);
              },
              onSelected: (item) => _update(slot, item),
              fieldViewBuilder: (context, controller, focusNode, onSubmit) =>
                  TextField(
                    controller: controller,
                    focusNode: focusNode,
                    decoration: const InputDecoration(
                      labelText: 'Eşya ara ve seç',
                    ),
                  ),
            ),
            if (selected != null) ...[
              const SizedBox(height: 8),
              Text(
                'Talent: ${selected['talent']?.toString().isNotEmpty == true ? selected['talent'] : '—'}',
              ),
              if ((selected['fixed_attributes'] as List? ?? []).isNotEmpty)
                ...((selected['fixed_attributes'] as List).whereType<Map>().map(
                  (a) => Text(
                    '${a['name']}: ${a['value']}${a['unit']}',
                    style: const TextStyle(
                      color: Color(0xFFB7C3D4),
                      fontSize: 12,
                    ),
                  ),
                ))
              else
                const Text(
                  'Sabit attribute verisi kaynak kaydında yok.',
                  style: TextStyle(color: Color(0xFF9AA4B5), fontSize: 12),
                ),
              if ((selected['attachments'] as List? ?? []).isNotEmpty)
                Text(
                  'Modlar: ${(selected['attachments'] as List).whereType<Map>().map((a) => a['name']).join(' · ')}',
                  style: const TextStyle(
                    color: Color(0xFFB7C3D4),
                    fontSize: 12,
                  ),
                ),
              if ((selected['fixed_attributes'] as List? ?? []).isEmpty &&
                  (slot == 'Mask' ||
                      slot == 'Backpack' ||
                      slot == 'Chest' ||
                      slot == 'Gloves' ||
                      slot == 'Holster' ||
                      slot == 'Kneepads'))
                _gearRolls(slot, selected),
            ],
          ],
        ),
      ),
    );
  }

  Widget _gearRolls(String slot, Map<String, dynamic> item) {
    final attributes = objectMap(widget.catalog['attributes']);
    final attrs = objectMap(item['attrs']);
    final core = '${item['core'] ?? ''}';
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: const Text('Çekirdek ve attribute roll’leri'),
      children: [
        DropdownButtonFormField<String?>(
          key: ValueKey('core:$slot:$core'),
          initialValue: core.isEmpty ? null : core,
          decoration: const InputDecoration(labelText: 'Çekirdek'),
          items: const [
            DropdownMenuItem<String?>(value: null, child: Text('Seçilmedi')),
            DropdownMenuItem<String?>(
              value: 'Weapon Damage',
              child: Text('Silah hasarı'),
            ),
            DropdownMenuItem<String?>(value: 'Armor', child: Text('Zırh')),
            DropdownMenuItem<String?>(
              value: 'Skill Tier',
              child: Text('Skill tier'),
            ),
          ],
          onChanged: (value) => _editItem(slot, item, core: value ?? ''),
        ),
        for (var index = 0; index < 2; index++)
          _attributeRoll(slot, index, item, attrs, attributes),
      ],
    );
  }

  Widget _attributeRoll(
    String slot,
    int index,
    Map<String, dynamic> item,
    Map<String, dynamic> attrs,
    Map<String, dynamic> catalogAttributes,
  ) {
    final selectedKey = attrs.keys
        .where(
          (key) => ![
            'base_damage',
            'rpm',
            'magazine_size',
            'reload_time',
          ].contains(key),
        )
        .skip(index)
        .firstOrNull;
    final meta = objectMap(catalogAttributes[selectedKey]);
    final aliases = meta['aliases'] as List? ?? const [];
    final title = aliases.isEmpty
        ? selectedKey ?? 'Attribute'
        : '${aliases.first}';
    return Row(
      children: [
        Expanded(
          flex: 3,
          child: DropdownButtonFormField<String?>(
            key: ValueKey('attr:$slot:$index:$selectedKey'),
            initialValue: selectedKey,
            isExpanded: true,
            decoration: InputDecoration(labelText: 'Attribute ${index + 1}'),
            items: [
              const DropdownMenuItem<String?>(
                value: null,
                child: Text('Seçilmedi'),
              ),
              ...statKeys
                  .where((key) => !key.endsWith('_tier') || key == 'skill_tier')
                  .map(
                    (key) => DropdownMenuItem<String?>(
                      value: key,
                      child: Text(key.replaceAll('_', ' ')),
                    ),
                  ),
            ],
            onChanged: (key) {
              final next = Map<String, dynamic>.from(attrs);
              if (selectedKey != null) next.remove(selectedKey);
              if (key != null) {
                next[key] = number(objectMap(catalogAttributes[key])['max']);
              }
              _editItem(slot, item, attrs: next);
            },
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          flex: 2,
          child: TextFormField(
            key: ValueKey('value:$slot:$selectedKey:$title'),
            initialValue: selectedKey == null ? '' : '${attrs[selectedKey]}',
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(
              labelText: title,
              suffixText:
                  '${objectMap(catalogAttributes[selectedKey])['unit'] ?? ''}',
            ),
            onChanged: (value) {
              if (selectedKey == null) return;
              final next = Map<String, dynamic>.from(attrs)
                ..[selectedKey] = number(value);
              _editItem(slot, item, attrs: next);
            },
          ),
        ),
      ],
    );
  }

  void _editItem(
    String slot,
    Map<String, dynamic> item, {
    String? core,
    Map<String, dynamic>? attrs,
  }) {
    final next = Map<String, dynamic>.from(item);
    if (core != null) next['core'] = core;
    if (attrs != null) next['attrs'] = attrs;
    _update(slot, next);
  }

  Widget _summary() {
    final stats = objectMap(_calculated['stats']);
    final weapons = (_calculated['weapons'] as List).whereType<Map>();
    return Card(
      color: const Color(0xFF191F2B),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'BUILD ÖZETİ',
              style: TextStyle(color: _orange, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text(
              'Zırh tahmini: ${number(_calculated['armor']).round()}  ·  Çekirdekler: ${jsonEncode(_calculated['cores'])}',
            ),
            ...weapons.map(
              (w) => Text(
                '${w['name']}: ${number(w['dps']).round()} DPS · ${number(w['ttk']).toStringAsFixed(1)} sn TTK',
              ),
            ),
            Text(
              'Kritik şans: ${number(stats['crit_chance']).toStringAsFixed(1)}%  ·  Kritik hasar: ${number(stats['crit_damage']).toStringAsFixed(1)}%',
              style: const TextStyle(color: Color(0xFFB7C3D4)),
            ),
            const SizedBox(height: 5),
            const Text(
              'Tahmini hesap; seçilmeyen rastgele attribute ve koşullu talent etkileri uygulanmaz.',
              style: TextStyle(color: Color(0xFF9AA4B5), fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }
}
