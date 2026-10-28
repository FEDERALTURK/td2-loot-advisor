import 'package:flutter_test/flutter_test.dart';
import 'package:td2_companion/main.dart';

void main() {
  testWidgets('companion renders its first Flutter frame', (tester) async {
    await tester.pumpWidget(const TD2CompanionApp());
    await tester.pump();

    expect(find.text('TD2 LOOT ADVISOR'), findsOneWidget);
    expect(find.text('COMPANION  ·  BETA 0.1.2'), findsOneWidget);
  });
}
