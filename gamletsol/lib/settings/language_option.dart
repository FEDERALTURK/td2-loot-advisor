/// Ana TD2 Loot Advisor projesindeki 10 dille aynı küme (bkz. lang/*.json) —
/// hedef (çeviri) dili için kullanılır. Kaynak (konuşulan) dil için de aynı
/// küme kullanılabilir; TV/konsolda hangi dil konuşuluyorsa o seçilir.
class LanguageOption {
  const LanguageOption(this.code, this.nativeName);

  final String code;
  final String nativeName;

  static const List<LanguageOption> all = [
    LanguageOption('tr', 'Türkçe'),
    LanguageOption('en', 'English'),
    LanguageOption('de', 'Deutsch'),
    LanguageOption('fr', 'Français'),
    LanguageOption('es', 'Español'),
    LanguageOption('it', 'Italiano'),
    LanguageOption('pt', 'Português'),
    LanguageOption('ru', 'Русский'),
    LanguageOption('pl', 'Polski'),
    LanguageOption('nl', 'Nederlands'),
  ];

  static LanguageOption byCode(String code) {
    return all.firstWhere(
      (o) => o.code == code,
      orElse: () => all.first,
    );
  }
}
