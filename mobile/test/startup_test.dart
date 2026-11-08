import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:td2_companion/main.dart';

void main() {
  testWidgets('companion renders its first Flutter frame', (tester) async {
    await tester.pumpWidget(const TD2CompanionApp());
    await tester.pump();

    // Yerel içerik ve ağ yenilemesi tamamlanmadan önce uygulamanın güvenilir
    // ilk karesi splash ekranıdır. Önceki test, asenkron yükleme bitmiş gibi
    // davranıp ana kabuktaki başlığı aradığı için yanlış negatif üretiyordu.
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
