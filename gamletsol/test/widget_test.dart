import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:gamletsol/main.dart';

void main() {
  testWidgets('Uygulama açılışta GAMLETSOL başlığını ve başlat düğmesini gösterir',
      (WidgetTester tester) async {
    await tester.pumpWidget(const GamletsolApp());
    await tester.pump();

    expect(find.text('GAMLETSOL'), findsOneWidget);
    expect(find.text('Dinlemeyi Başlat'), findsOneWidget);
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
