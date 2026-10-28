# Google Play hazırlık ve imzalama

Bu belge Google Play üretim yayını için yerel AAB hazırlama adımlarını içerir. Geliştirici hesabı, Play Console beyanları ve mağaza yayını proje dosyalarından yönetilmez.

## Mevcut uygulama durumu

- Uygulama kimliği: `com.federalturk.td2companion`
- Android hedefi: API 36
- Companion sürümü: `0.1.2+3`
- Paket adı: `com.federalturk.td2companion`
- Play Console'a APK değil Android App Bundle (`.aab`) yüklenir.
- GitHub beta APK'ları debug anahtarıyla imzalanır. Bu imzalı APK'lar Play Console'a üretim sürümü olarak yüklenmemelidir.
- Play App Signing'e katılın ve yalnızca yükleme anahtarını (upload key) yerel makinede saklayın. Keystore ve `key.properties` dosyasını Git'e, issue'lara veya mesajlara eklemeyin.
- Yeni Play uygulama gönderimleri en az Android 16 / API 36 hedeflemelidir; bu uygulama API 36 hedefliyor.
- Uygulama `mobile_scanner` üzerinden kamera izni ve Android plugin'lerinden native kod kullanır. Google Play teknik kalite şartı 64-bit ve 16 KB sayfa uyumluluğudur; AAB yüklemeden önce App Bundle Explorer ve 16 KB test ortamıyla teyit edin.

## Yerel upload key oluşturma

1. JDK `keytool` ile `mobile/android` klasöründe bir upload keystore üretin:

   ```powershell
   cd mobile/android
   keytool -genkeypair -v -keystore upload-keystore.jks -keyalg RSA -keysize 4096 -validity 10000 -alias upload
   ```

2. `mobile/android/key.properties.example` dosyasını `mobile/android/key.properties` adıyla kopyalayın. Keystore yolu, store parolası, alias ve key parolasını yerel dosyaya girin. Bu dosya `.gitignore` kapsamındadır.

3. Flutter bağımlılıklarını alıp analiz edin. Ardından AAB'yi Play imzasıyla oluşturun:

   ```powershell
   cd mobile
   flutter pub get
   flutter analyze
   flutter build appbundle --release --build-name=0.1.2 --build-number=3 --android-project-arg=playRelease=true
   ```

Çıktı: `mobile/build/app/outputs/bundle/release/app-release.aab`.

`playRelease=true` seçeneği olmadan oluşturulan paketler beta/test içindir ve debug imzalı kalır. Play imzası istenip `key.properties` yoksa derleme açık bir hata ile durur.

## Play Console tamamlanacaklar

- Play App Signing'i etkinleştirin ve ilk AAB'yi internal testing'e yükleyin.
- Geliştirici kimliğinin doğrulandığını ve `com.federalturk.td2companion` paket adının hesaba kayıtlı olduğunu kontrol edin.
- 30 Eylül 2026'da yürürlüğe giren Android geliştirici doğrulama sürecinde kimlik doğrulamasını ve paket adı kaydını kontrol edin; Play Console'da paket adı durumunu doğrulayın.
- Gizlilik politikası URL'sini mağaza kaydına ekleyin. Uygulamanın Hakkında penceresindeki bağlantı aynı dosyaya gider.
- Data safety, reklam, hedef kitle ve içerik derecelendirmesi formlarını uygulamanın gerçek davranışına göre doldurun.
- Mağaza başlığı, kısa/tam açıklama, 512×512 simge ve 1024×500 özellik görseli hazırlandı (`PLAY_STORE_LISTING_TR.md`, `PLAY_STORE_LISTING_EN.md`, `store-assets/`). Gerçek uygulamadan telefon ekran görüntüleri hâlâ alınmalı.
- Play Console geliştirici iletişim e-postasını sağlayın; mağaza iletişim bilgileri ve gizlilik politikasındaki destek kanalı birbiriyle tutarlı olmalı.
- HONOR Magic8 Lite / Android 16 üzerinde açılış doğrulandı. Üretimden önce görevler, build kaydetme, kamera/QR izinleri ve masaüstü eşleştirmesi son AAB ile tekrar kontrol edilmeli.
- 12 kullanıcı / 14 gün kapalı test şartı yeni kişisel hesaplar için geçerlidir; kuruluş hesabının Play Console kurallarını kendi hesabında doğrula.

## Bu projede açık kalan yayın engelleri

- Gerçek uygulama ekran görüntüleri mağaza gereksinimlerine göre alınmalı.
- Upload key sahibi/parolaları kullanıcı tarafından kurulmalı ve yedeklenmeli.
- Play Console geliştirici hesabı ve uygulama kaydı kullanıcı tarafında tamamlanmalı.
- Destek e-postası seçilmeli; gizlilik metni ve Play Console geliştirici iletişim adresi eşleştirilmeli.
- AAB'nin 64-bit ve 16 KB uyumluluğu doğrulanmalı; 64-bit native kodlu uygulamalarda Google Play bu teknik gerekliliği uygular.
- Ekran görüntüsü ölçüleri ve özel veriyi gizleme adımları için `PLAY_STORE_SCREENSHOTS_TR.md` kılavuzunu kullan.
