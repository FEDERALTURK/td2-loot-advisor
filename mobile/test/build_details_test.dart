import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:td2_companion/main.dart';

void main() {
  testWidgets('saved build opens its slot attributes and fixed details', (
    tester,
  ) async {
    final build = <String, dynamic>{
      'name': 'St Elmo test',
      'specialization': 'Technician',
      'slots': {
        'Primary': {
          'name': "St. Elmo's Engine",
          'talent': 'Actum Est',
          'attrs': {'health_damage': 10},
          'attachments': [
            {'slot': 'Optics', 'name': 'Conductor Rail', 'stats': 'CHC +5%'},
          ],
        },
      },
    };
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SavedBuildCard(data: build, onDelete: () {}),
        ),
      ),
    );

    await tester.tap(find.byTooltip('Build ayrıntılarını gör'));
    await tester.pumpAndSettle();

    expect(find.text('St Elmo test'), findsNWidgets(2));
    expect(find.text("Primary · St. Elmo's Engine"), findsOneWidget);
    expect(find.textContaining('Yetenek: Actum Est'), findsOneWidget);
    expect(find.textContaining('health damage: 10'), findsOneWidget);
    expect(
      find.textContaining('Optics: Conductor Rail CHC +5%'),
      findsOneWidget,
    );
  });
}
