# GAMLETSOL — Devir Özeti (yeni sohbet/proje için)

**Repo:** https://github.com/FEDERALTURK/gamletsol (public, bağımsız — `td2-loot-advisor` ile hiçbir kod/yayın bağımlılığı yok)

## Ne bu uygulama
TV/konsoldan çıkan sesi telefonun **mikrofonuyla** dinleyip canlı altyazıya çeviren, **yalnızca Android** hedefleyen bir Flutter uygulaması.

**Akış:** Mikrofon (`record` paketi, ham LINEAR16/PCM16/16kHz akışı) → ~4 saniyelik parçalar hâlinde Google Cloud Speech-to-Text REST API → Google Cloud Translation API v2 → ekranda orijinal + çevrilmiş metin.

API anahtarı kullanıcı tarafından Ayarlar ekranından girilir, `flutter_secure_storage` ile cihazda (Android Keystore) saklanır — koda/loga asla yazılmaz.

## Mevcut durum (dürüstlük notu)
- İlk commit: `1fe0243`. CI (`.github/workflows/build.yml`, `flutter analyze` + `flutter test` + `flutter build apk --debug`, ubuntu-latest) tetiklendi, sonucu bu özetten sonra kontrol edilmeli.
- Google Speech-to-Text ve Translation API'lerinin istek/yanıt şeması resmi dokümantasyondan doğrulandı (tahmin edilmedi), ama **gerçek bir Google Cloud API anahtarıyla uçtan uca hiç denenmedi**.
- Gerçek zamanlı değil — ~4-8 saniye gecikmeli, parçalı (chunked) bir ilk sürüm.
- iOS yok, bilinçli olarak yalnızca Android.
- Beta/Play Store imzalama düzeni henüz yok (sadece debug anahtarıyla CI derleme doğrulaması).

## Kalan işler
- CI'nın gerçekten yeşile geçtiğini doğrula (ilk denemede geçmeme ihtimali var — hiçbir dış paket/API bu ortamda fiilen çalıştırılamadı, sadece dokümantasyonla doğrulandı).
- Gerçek bir Android cihazda, gerçek bir Google Cloud API anahtarıyla uçtan uca test.
- İsteğe bağlı: gerçek düşük-gecikmeli streaming STT'ye geçiş (şu an senkron `speech:recognize`, gRPC streaming değil).
- İsteğe bağlı: Play Store yayın hazırlığı (imzalama anahtarı, mağaza girişi).

## Dosya haritası
- `lib/audio/mic_capture_service.dart` — mikrofon yakalama
- `lib/stt/speech_to_text_service.dart` — Google STT istemcisi
- `lib/translate/translate_service.dart` — Google Translate istemcisi
- `lib/caption/` — oturum orkestrasyonu + ana ekran
- `lib/settings/` — API anahtarı güvenli depo + ayarlar ekranı
- `README.md` — tam kapsam, sınırlamalar, kurulum adımları
