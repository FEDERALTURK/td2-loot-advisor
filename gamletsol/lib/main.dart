import 'package:flutter/material.dart';

import 'caption/caption_page.dart';
import 'ui/theme.dart';

void main() {
  runApp(const GamletsolApp());
}

class GamletsolApp extends StatelessWidget {
  const GamletsolApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GAMLETSOL',
      debugShowCheckedModeBanner: false,
      theme: buildGamletsolTheme(),
      home: const CaptionPage(),
    );
  }
}
