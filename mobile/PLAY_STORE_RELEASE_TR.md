# Google Play hazırlık ve imzalama

Bu belge Google Play üretim yayını için yerel AAB hazırlama adımlarını içerir. Geliştirici hesabı, Play Console beyanları ve mağaza yayını proje dosyalarından yönetilmez.

## Mevcut uygulama durumu

- Uygulama kimliği: `com.federalturk.td2companion`
- Android hedefi: API 36
- Companion sürümü: `0.1.2+3`
- Play Console'a APK değil Android App Bundle (`.aab`) yüklenir.
- GitHub beta APK'ları debug anahtarıyla imzalanır. Bu imzalı APK'lar Play Console'a üretim sürümü olarak yüklenmemelidir.
- Play App Signing'e katılın ve yalnızca yükleme anahtarını (upload key) yerel makinede saklayın. Keystore ve `key.properties` dosyasını Git'e, issue'lara veya mesajlara eklemeyin.

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
- Gizlilik politikası URL'sini mağaza kaydına ekleyin. Uygulamanın Hakkında penceresindeki bağlantı aynı dosyaya gider.
- Data safety, reklam, hedef kitle ve içerik derecelendirmesi formlarını uygulamanın gerçek davranışına göre doldurun.
- Mağaza başlığı, kısa/tam açıklama, 512×512 simge, 1024×500 özellik görseli ve telefon ekran görüntülerini hazırlayın.
- Play Console geliştirici iletişim e-postasını sağlayın; mağaza iletişim bilgileri ve gizlilik politikasındaki destek kanalı birbiriyle tutarlı olmalı.
- HONOR Magic8 Lite / Android 16 dahil gerçek cihaz testinde açılış ve temel akışlar doğrulanmadan üretim kanalına geçmeyin.
- Kişisel geliştirici hesabı 13 Kasım 2023'ten sonra açıldıysa, üretim erişiminden önce 12 kullanıcılı ve 14 gün kesintisiz kapalı test şartı uygulanabilir.

## Bu projede açık kalan yayın engelleri

- `0.1.2` düzeltilmiş APK'nın HONOR Android 16 cihazında açıldığı doğrulanmalı.
- Upload key sahibi/parolaları kullanıcı tarafından kurulmalı ve yedeklenmeli.
- Play Console geliştirici hesabı ve uygulama kaydı kullanıcı tarafında tamamlanmalı.
- Mağaza görselleri ve gerekli iletişim bilgileri tamamlanmalı.
