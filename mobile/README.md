# TD2 Loot Advisor Companion

Flutter companion app for the TD2 Loot Advisor Windows application.

## Beta 0.1.1

- Current game tasks, news and meta-build feeds with bundled offline data.
- Local task progress and user-created build storage.
- Android QR pairing with the Windows app's existing read-only Phone Companion server on the same private Wi-Fi.
- No remote desktop commands, game memory access, mobile OCR, account system or cloud sync.

See [`../docs/mobile_companion_connection_tr.md`](../docs/mobile_companion_connection_tr.md) for the Turkish pairing and network guide.

## Build locally

Requires Flutter/Dart, a supported JDK and Android SDK for Android APK builds. iOS builds require macOS and Xcode.

```sh
flutter pub get
flutter analyze
flutter build apk --release --build-name=0.1.1 --build-number=2
```

The Android APK output is `build/app/outputs/flutter-apk/app-release.apk`.
