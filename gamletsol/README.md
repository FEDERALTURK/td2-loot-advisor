# GAMLETSOL — TV/Konsol Sesi Canlı Çeviri (DENEYSEL)

"Game Translate Console" kısaltması. TD2 Loot Advisor'ın mobil companion'ından
(`mobile/`) **tamamen ayrı**, bağımsız bir Flutter uygulaması (2026-11-09'da
kullanıcı isteğiyle başlatıldı — ayrı paket/mağaza girişi olarak).

## Ne yapar

Telefonun **mikrofonuyla** TV/konsoldan çıkan sesi (oda sesi olarak) dinler,
konuşmayı buluta gönderip metne çevirir (Google Cloud Speech-to-Text), sonra
seçilen hedef dile çevirir (Google Cloud Translation API) ve ekranda hem
orijinal hem çevrilmiş metni canlı altyazı olarak gösterir.

Bu, mevcut "Konsol Modu" (mobile/lib/console/) ile **karıştırılmamalı**:
Konsol Modu kamerayla ekrandaki YAZIYI okur (OCR, cihaz-üstü, ücretsiz,
internet gerektirmez). GAMLETSOL ise mikrofonla SESİ dinler (ASR, bulut API,
ücretli, internet gerektirir) — konuşma/diyalog sesli ama ekranda yazı olarak
görünmeyen içerikler için (örn. seslendirilmiş ara sahneler, canlı yayın,
fiziksel bir TV/konsol).

## Mimari

- **Dil/platform:** Flutter (Android hedefli bu ilk sürümde; iOS scaffold'u
  henüz yok).
- **Ses yakalama:** `record` paketi, `startStream` ile ham LINEAR16 (PCM16,
  16kHz, mono) akışı — WAV başlığı gerekmiyor, Google STT'ye doğrudan
  gönderiliyor.
- **STT:** Google Cloud Speech-to-Text REST API (`v1/speech:recognize`) —
  gerçek sürekli/düşük-gecikmeli "streaming recognize" DEĞİL; ~4 saniyelik
  parçalar ayrı ayrı REST isteğiyle gönderiliyor (bkz. "Bilinen sınırlamalar").
- **Çeviri:** Google Cloud Translation API v2 (`language/translate/v2`).
- **API anahtarı:** Kullanıcı kendi Google Cloud API anahtarını Ayarlar
  ekranından girer; `flutter_secure_storage` ile cihazda güvenli depoda
  tutulur (Android Keystore) — asla koda, loga veya herhangi bir sunucuya
  yazılmaz/gönderilmez.

## Bilinen sınırlamalar (ilk sürüm, dürüstlük ilkesi)

- **Gerçek zamanlı akış değil, parçalı (chunked) işleme.** Her ~4 saniyede
  bir ayrı bir STT isteği gönderiliyor — bu, Google'ın gerçek "streaming
  recognize" (gRPC, kelime kelime canlı) API'sinden daha basit ama daha
  yüksek gecikmeli. İleri sürümde gerçek streaming'e geçilebilir.
  Not: Google'ın `v1/speech:recognize` (senkron, kısa ses) uç noktası resmî
  dokümantasyondan doğrulandı; `v1p1beta1`/`v2` streaming gRPC API'si
  henüz İNCELENMEDİ.
- **Maliyetli.** Hem Speech-to-Text hem Translation API çağrı başına
  ücretlidir (Google Cloud fiyatlandırması). Kullanıcı kendi API anahtarını
  kullanır, kendi faturalandırmasından sorumludur.
- **Gecikme yaklaşık 4-8 saniye** (parça süresi + ağ + API işleme) —
  canlı bir konuşmayı gerçek zamanlı altyazılamaz, birkaç saniye arkadan
  gelir.
- **Arka plan gürültüsü/yankı** TV hoparlöründen mikrofona giden sesin
  kalitesini düşürebilir; `autoGain`/`noiseSuppress` açık ama tam izolasyon
  garanti edilmez.
- **Uzun çalışma / pil tüketimi** test edilmedi.

## Doğrulama durumu (dürüstlük ilkesi — bkz. AGENTS.md)

- [ ] `flutter analyze` / `flutter test` / `flutter build apk --debug` CI'da
      geçti mi? (Bkz. DEVELOPMENT_LOG.md'deki ilgili CI run numarası.)
- [ ] Gerçek bir Google Cloud API anahtarıyla uçtan uca denendi mi?
      **HAYIR.** Bu kum havuzunda gerçek bir anahtar yok ve olmamalı —
      kullanıcı kendi anahtarıyla gerçek bir cihazda denemelidir.
- [ ] Gerçek bir TV/konsol sesiyle mikrofon testi yapıldı mı? **HAYIR.**
- STT/Translate REST API'lerinin istek/yanıt şeması resmi Google Cloud
  dokümantasyonundan doğrulandı (URL, alan adları) — ama gerçek bir ağ
  çağrısıyla hiç denenmedi.

## Kurulum (kullanıcının yapması gereken)

1. [Google Cloud Console](https://console.cloud.google.com/)'da bir proje aç
   (veya mevcut birini kullan).
2. **Cloud Speech-to-Text API** ve **Cloud Translation API**'yi etkinleştir.
3. Kimlik Bilgileri → API Anahtarı Oluştur. Güvenlik için anahtarı sadece bu
   iki API'yle sınırlamanı öneririz.
4. GAMLETSOL'u aç → Ayarlar → API anahtarını yapıştır → Kaydet.
5. Ana ekranda TV/konsol sesinin dilini ve görmek istediğin dili seç,
   "Dinlemeyi Başlat"a bas, mikrofon iznini ver.

## Henüz yapılmayanlar

- Gerçek düşük-gecikmeli streaming STT.
- Whisper/Azure gibi alternatif STT sağlayıcıları (kullanıcı ileride
  Google dışında bir seçenek isteyebilir).
- iOS derlemesi/paketleme.
- Play Store / beta imzalama (mobile/ projesindeki kalıcı anahtar düzeni
  burada henüz yok — bkz. android/app/build.gradle.kts'teki not).
