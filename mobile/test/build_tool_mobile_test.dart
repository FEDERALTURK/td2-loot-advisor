import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:td2_companion/builds/build_calculator.dart';

void main() {
  test(
    'catalog fixed item data resolves St Elmo and calculates a weapon estimate',
    () async {
      final catalog = jsonDecode(
        await File('assets/data/build_catalog.json').readAsString(),
      ) as Map<String, dynamic>;
      final elmo = (catalog['choices']['Primary'] as List)
          .cast<Map>()
          .firstWhere((e) => e['name'] == "St. Elmo's Engine");
      expect(elmo['talent'], 'Actum Est');
      expect((elmo['attachments'] as List), hasLength(4));
      final result = calculateBuild({
        'slots': {'Primary': elmo},
      }, catalog);
      expect((result['weapons'] as List).single['dps'], greaterThan(0));
    },
  );

  test(
    'fixed exotic gear attributes are surfaced in the same calculation schema',
    () async {
      final catalog = jsonDecode(
        await File('assets/data/build_catalog.json').readAsString(),
      ) as Map<String, dynamic>;
      final coyote = (catalog['choices']['Mask'] as List)
          .cast<Map>()
          .firstWhere((e) => e['name'] == "Coyote's Mask");
      expect(coyote['talent'], 'Pack Instincts');
      expect(
        calculateBuild({
          'slots': {'Mask': coyote},
        }, catalog)['cores']['offensive'],
        1,
      );
    },
  );
}
