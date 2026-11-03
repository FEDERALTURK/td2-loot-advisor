# Bağımlılıklar ve Lisanslar

Bu dosya, projenin gerçek bağımlılıklarını ve lisans kaynaklarını listeler.
Proje talimatlarının 17. maddesi (DEPENDENCIES.md) ve 12. maddesi (bağımlılık/sürüm yönetimi) kapsamında tutulur.

## Ana program (Windows masaüstü, `requirements.txt`)

Oyuncu çalışma zamanında gerekli, zorunlu paketler:

| Paket | Sürüm kısıtı | Amaç |
|---|---|---|
| mss | — | Ekran görüntüsü yakalama (OCR için) |
| pillow | — | Görüntü işleme |
| pytesseract | — | Tesseract OCR bağlayıcısı |
| pynput | — | Klavye/fare dinleme (ör. kısayollar) |
| pystray | — | Sistem tepsisi simgesi |
| ctranslate2 | >=4.8.4,<5 | Çeviri motoru (yerinde çeviri) |
| sentencepiece | — | Çeviri modeli tokenizasyonu |
| soundcard | — | Ses cihazı tespiti |
| edge-tts | >=7.3.1,<8 | Metin-konuşma (TTS) |
| sounddevice | — | Ses I/O |
| faster-whisper | >=1.2.1,<2 | Konuşma tanıma (STT) |
| av | >=14,<19 | PyAV; faster-whisper 1.2.x ile uyumluluk üst sınırı not edilmiş (metadata_errors PyAV 19'da kaldırıldı) |
| pyttsx3 | — | Yerel TTS yedek motoru |
| qrcode | — | Lisans/paylaşım QR kodu üretimi |

## Opsiyonel ses/görüntü paketleri (`requirements-voice.txt`)

Kurulamazsa **uygulama yine çalışır**, yalnızca ilgili özellik kapanır: `pyttsx3`, `sounddevice`, `numpy`, `faster-whisper`, `av` (arka plan videosu), `onnxruntime`+`rapidocr` (yeni OCR motoru, önerilen), `qrcode`.

## Geliştirici/bakım araçları (`requirements-dev.txt`)

| Paket | Amaç |
|---|---|
| openpyxl | `scripts/library_excel.py` ve `scripts/import_library_excel.py` (Excel ↔ `meta/game_data.json` senkron kontrolü, `tests/test_core.py::test_excel_library_in_sync`) için. **Oyuncu çalışma zamanında gerekmez.** |

Bu oturumda doğrulandı: `openpyxl` kurulu değilken `test_excel_library_in_sync` `ModuleNotFoundError` ile başarısız oluyor (bu bir kod hatası değil — dev-only bağımlılığın test ortamında kurulu olmaması). `requirements-dev.txt` kurulunca test geçiyor.

## Sunucu (`server/`, Cloudflare Workers + D1, Node.js)

`server/worker.js`, `server/*.js`, `server/*.mjs` — bağımlılıkları `server/package.json` yerine doğrudan Cloudflare Workers runtime API'leri ve `wrangler` CLI üzerinden çalışıyor (`server/wrangler.toml`). Kurulum adımları `server/README.md`'de.

## Mobil companion (`mobile/`) — Flutter/Dart, Kotlin/Gradle değil

Önceki bir devir özetinde bu bileşen "Kotlin/Gradle" olarak tanımlanmıştı; bu **hatalıydı**. `mobile/pubspec.yaml` içeriği doğrulandı: proje adı `td2_companion`, **Flutter** (Dart SDK `^3.13.7`) ile yazılmış. `mobile/android/` ve `mobile/ios/` klasörleri Flutter'ın otomatik ürettiği platform sarmalayıcıları (Gradle/Xcode projeleri), elle yazılmış native kod değil. `mobile/lib/` gerçek Dart kaynak kodunu içerir.

## Üçüncü taraf oyun verisi (lisans)

Ayrıntılar `LICENSE_NOTES.md`'de:
- **The Division Wiki** (thedivision.fandom.com) — CC BY-SA.
- **mx-division-builds** (github.com/mxswat/mx-division-builds) — CC BY-NC-SA 4.0 (ticari olmayan). `recal_advisor` (premium) özelliğiyle ilişkisi hâlâ açıklığa kavuşturulmamış bir gri alan — bkz. LICENSE_NOTES.md "Önerilen adım".

## Programın kendi lisansı

`LICENSE` — MIT License, Copyright (c) 2026 FEDERALTURK.
