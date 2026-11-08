/// ISO 639-1 kod (örn. "en") → Google Speech-to-Text'in beklediği BCP-47
/// konuşma-tanıma yerel ayarı (örn. "en-US"). Her dilin en yaygın/varsayılan
/// bölgesi seçildi; ileride kullanıcıya bölge seçimi de eklenebilir.
const Map<String, String> bcp47SpeechLocale = {
  'tr': 'tr-TR',
  'en': 'en-US',
  'de': 'de-DE',
  'fr': 'fr-FR',
  'es': 'es-ES',
  'it': 'it-IT',
  'pt': 'pt-PT',
  'ru': 'ru-RU',
  'pl': 'pl-PL',
  'nl': 'nl-NL',
};

String speechLocaleFor(String iso639) => bcp47SpeechLocale[iso639] ?? 'en-US';
