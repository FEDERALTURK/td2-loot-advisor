// Kaivolt lacivert/turuncu HUD estetiği — ana TD2 Loot Advisor projesi ve
// mobile/ companion ile görsel tutarlılık için aynı renk paleti kullanılıyor.
import 'package:flutter/material.dart';

class GamletsolColors {
  GamletsolColors._();

  static const background = Color(0xFF090C12);
  static const panel = Color(0xFF121722);
  static const panelAlt = Color(0xFF1A2130);
  static const orange = Color(0xFFFF6D10);
  static const soft = Color(0xFF9AA4B5);
  static const green = Color(0xFF3DDC84);
  static const red = Color(0xFFE5484D);
}

ThemeData buildGamletsolTheme() {
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: GamletsolColors.background,
    colorScheme: ColorScheme.fromSeed(
      seedColor: GamletsolColors.orange,
      brightness: Brightness.dark,
      surface: GamletsolColors.panel,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: GamletsolColors.background,
      foregroundColor: Colors.white,
      elevation: 0,
    ),
    cardTheme: CardThemeData(
      color: GamletsolColors.panel,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: GamletsolColors.orange,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      ),
    ),
  );
}
