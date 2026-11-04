# Mobil push bildirimi — kalan kurulum adımı

Bağlam: `server/mobile.js` push gönderimi tamamen hazır (Android/FCM canlı,
iOS/APNs kodu hazır — bkz. `mobile_companion_roadmap.md`). Flutter uygulaması
artık `PUT /v1/mobile/push-tokens/{id}` ucunu çağırıyor (eşleştirme sonrası ve
her açılışta, zaten eşleşmişse) — bkz. `mobile/lib/services/push_registration.dart`
ve `mobile/lib/services/cloud_link.dart`. **Tek eksik parça**: Android projesine
gerçek bir Firebase yapılandırma dosyası (`google-services.json`) eklenmesi.
Bu dosya olmadan `Firebase.initializeApp()` sessizce başarısız olur (uygulama
çökmez, push bildirimi kaydı atlanır — bkz. `push_registration.dart`'taki
en-iyi-gayret tasarımı) — yani bu adım tamamlanana kadar push bildirimi
telefonda hiç çalışmaz, ama programın geri kalanı etkilenmez.

## Durum: 1-3 arası tamamlandı (2026-11-04), kalan adımlar aşağıda

Firebase konsolunda Android uygulaması (`com.federalturk.td2companion`) eklendi ve
`google-services.json` indirilip doğrudan kullanıcının PC'sindeki depo kopyasına
(`C:\Users\PC\Desktop\Thedivision2program\mobile\android\app\google-services.json`)
yazıldı — bu dosya `.gitignore`'da olduğu için git'e hiç girmedi, yalnızca o PC'de var.
**Kalan**: o PC'de `git pull` (bu oturumun push-token kodunu çekmek için) + 4. maddedeki
tek satırın yorumunu kaldırmak + 5. maddedeki doğrulama.

## Yapılacaklar (tek seferlik, Firebase konsolunda)

1. https://console.firebase.google.com → mevcut proje **`td2-loot-advisor`**
   (sunucu tarafı Admin SDK anahtarı bu projeden üretilmişti).
2. Proje ayarları → "Uygulama ekle" → **Android**.
   - Android paket adı: **`com.federalturk.td2companion`** (bkz.
     `mobile/android/app/build.gradle.kts` → `applicationId`).
   - İsteğe bağlı takma ad: "TD2 Loot Advisor Companion".
   - Debug imza sertifikası SHA-1: bu adımda atlanabilir (push bildirimi için
     gerekli değil; yalnızca Dynamic Links/App Check gibi gerekmeyen
     özellikler için istenir).
3. **`google-services.json`**'ı indir, depodaki `mobile/android/app/google-services.json`
   konumuna koy (bu dosya `.gitignore`'da olmalı — proje kimlik bilgisi, depoya
   girmemeli; `mobile/android/app/.gitignore`'u kontrol et, yoksa ekle).
4. İki satırın yorumunu kaldır:
   - `mobile/android/app/build.gradle.kts` → `plugins {}` içindeki
     `// id("com.google.gms.google-services")` satırının başındaki `//`'yi sil.
   - (`mobile/android/settings.gradle.kts`'teki `apply false` satırı zaten
     hazır, dokunmana gerek yok.)
5. `flutter pub get` (yeni eklenen `firebase_core`/`firebase_messaging`
   paketlerini çeker), sonra `flutter build apk --debug` (veya `flutter run`)
   ile gerçek cihazda/emülatörde dene — "Bildirime izin ver" istemi çıkmalı,
   ardından uygulama arka planda sunucuya kaydolmalı (log yok; sessiz).
6. Doğrulama: telefon eşleştir → masaüstünde bir `scan_result` olayı tetikle
   (örn. bir eşya tara) → telefona FCM bildirimi gelmeli. Sunucu tarafında
   `PUT /push-tokens` yanıtındaki `delivery` alanı `"available"` dönüyorsa
   (kodda zaten kontrol ediliyor) kayıt başarılı demektir.

## iOS/APNs (ayrı, ertelendi)

iOS tarafı bu işin kapsamında değil — kullanıcı önce Apple Developer Program'a
(~$99/yıl) kaydolmalı (bkz. `mobile_companion_roadmap.md` → "iOS push setup").
`google-services.json`'a ek olarak `GoogleService-Info.plist` ve
`ios/Runner/Info.plist`'e arka plan modu (`remote-notification`) eklenmesi
gerekecek — o adım geldiğinde bu dosyaya eklenecek.

## Neden şimdi tam otomatik yapılmadı

Bu depoyla çalışan oturum (bu dosyayı yazan) Firebase konsoluna/hesabına
erişemiyor (kullanıcının kendi Google oturumu gerekiyor) ve bu ortamda
Flutter SDK'sı kurulu değil (`flutter analyze`/`build` çalıştırılamadı) —
yani kod yazıldı ve mantık/sözdizimi incelemesiyle doğrulandı, ama gerçek
derleme + cihaz testi kullanıcının Windows PC'sinde (Flutter zaten kurulu,
bkz. `DEVELOPMENT_LOG.md`) yapılmalı.
