# Konsol Modu (bkz. docs/console_game_caption_roadmap.md) — google_mlkit_text_recognition
# yalnızca Latin script ile kullanılıyor (console_translate_service.dart,
# TextRecognitionScript.latin). Eklenti kodu desteklediği TÜM scriptlerin
# (Çince/Devanagari/Japonca/Korece) seçenek sınıflarına koşulsuz referans veriyor,
# ama bu scriptlerin ayrı native ML Kit kütüphaneleri bağımlılık olarak
# eklenmedi (gerek yok, yalnız Latin alfabe okunuyor) — R8 bu sınıfları
# bulamayınca "Missing class" hatasıyla derleme patlıyor. Bu dört satır,
# google_ml_kit_flutter eklentisinin bu tip opsiyonel/kullanılmayan referanslar
# için önerdiği standart R8 çözümüdür (gerçek derleme hatasıyla doğrulandı,
# bkz. CI run 42513566679).
-dontwarn com.google.mlkit.vision.text.chinese.**
-dontwarn com.google.mlkit.vision.text.devanagari.**
-dontwarn com.google.mlkit.vision.text.japanese.**
-dontwarn com.google.mlkit.vision.text.korean.**
