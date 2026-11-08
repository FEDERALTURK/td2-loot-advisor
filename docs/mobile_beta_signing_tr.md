# Mobil Companion — GitHub Beta Kanalı İmza Düzeltmesi (P0)

## Sorun neydi?

`.github/workflows/build-mobile.yml` her `companion-v*` etiketinde
`flutter build apk --release` çalıştırıyordu, ve `mobile/android/app/build.gradle.kts`
bu durumda **Gradle'ın "debug" imza anahtarını** kullanıyordu (yalnızca Play
yayınında `playRelease=true` verilirse kalıcı bir anahtar devreye giriyordu).

`ubuntu-latest` GitHub Actions runner'larında kalıcı bir `~/.android/debug.keystore`
**yoktur** — her job ilk ihtiyaç anında kendi geçici debug anahtarını üretir.
Yani her CI çalışması farklı bir anahtarla imzalıyordu. Android, bir APK'yı
aynı paket adı (`com.federalturk.td2companion`) üzerine ancak **imza
sertifikası eşleşirse** güncelliyor; eşleşmezse kurulumu reddediyor. Bu da
kullanıcıların "yeni sürüm indi ama kurulum başarısız/eski sürüm görünüyor"
şikâyetinin kök nedeniydi (Codex'in devir raporunda P0 olarak işaretlenmişti).

## Ne değişti?

1. `mobile/android/app/build.gradle.kts`'e, Play yükleme anahtarından
   (`key.properties`/`playRelease`) tamamen ayrı, kalıcı bir
   **"GitHub beta" imza yapılandırması** eklendi: `beta-key.properties` +
   `githubBetaRelease=true` Gradle özelliği.
2. `.github/workflows/build-mobile.yml`, build'den önce bir GitHub Actions
   secret'ından (base64 kodlu keystore) `android/td2-companion-beta.jks` ve
   `android/beta-key.properties` dosyalarını üretip derlemeyi
   `--android-project-arg=githubBetaRelease=true` ile çalıştırıyor.
3. Secret yoksa (örn. henüz kurulmadıysa) build **kırılmıyor**, sadece bir
   uyarı basıp eski (debug) davranışa düşüyor — bu yüzden secret'lar
   eklenmeden önce de CI bozulmaz, ama sorun da düzelmiş olmaz.
4. Bu oturumda **gerçekten üretilmiş, kalıcı bir keystore** hazırlandı
   (`keytool -genkeypair -alias td2-companion-beta -keysize 4096 -validity 36500`,
   geçerlilik 100 yıl). Dosya ve parolalar bu repoya **commit edilmedi**
   (`.gitignore`'da `beta-key.properties` ve `**/*.jks` zaten vardı) — sana
   ayrı olarak gönderildi.

## Senin yapman gerekenler (GitHub repo ayarları — ben buradan yapamıyorum)

Bu oturumun GitHub Actions secret'larını ayarlama izni yok (proxy engelliyor),
bu yüzden şu adımları **senin** tamamlaman gerekiyor:

1. GitHub'da repo → **Settings → Secrets and variables → Actions → New repository secret**.
2. Üç secret ekle (sana ayrıca gönderilen `td2-companion-beta.jks` dosyası ve
   parolayla):
   - `TD2_BETA_KEYSTORE_BASE64` — keystore dosyasının base64 hâli (sana
     gönderilen `.b64` dosyasının içeriği, tek satır).
   - `TD2_BETA_KEYSTORE_PASSWORD` — keystore/anahtar parolası (sana ayrıca
     gönderildi; bu modern PKCS12 formatında store ve key parolası aynıdır).
   - `TD2_BETA_KEY_ALIAS` — değeri: `td2-companion-beta`.
3. **Keystore dosyasını ve parolasını güvenli bir yerde (parola yöneticisi
   vb.) ayrıca yedekle.** Bu dosya kaybolursa bir daha hiçbir güncelleme eski
   kurulumların üstüne gitmez — herkesin tekrar elle kaldırıp kurması gerekir.
   Repoya asla commit etme, issue/mesaja asla yapıştırma.

## Geriye dönük etki — ÖNEMLİ

Önceki tüm GitHub beta APK'ları (muhtemelen `companion-v0.1.x` serisinin
tamamı) birbirinden farklı, geçici debug anahtarlarıyla imzalanmıştı. Bu
demek oluyor ki:

- **Telefolarında şu an kurulu olan sürüm, bu düzeltmeden sonraki ilk yeni
  sürümü "üstüne" kuramayacak** — imza uyuşmazlığı hatası alacaklar (ya da
  app sessizce indirip kurulum adımında başarısız olacak).
- **Tek seferlik çözüm:** kullanıcılar eski APK'yı kaldırıp yeni sürümü
  (bu düzeltmeden SONRA yayınlanan ilk sürüm) temiz kursun. Bu, uygulama içi
  yerel verilerini (görev ilerlemesi, kaydedilen build'ler) siler — kullanıcıya
  açıkça bildirilmeli.
- Bu kaldır-kur işleminden SONRA, artık her sürüm aynı kalıcı anahtarla
  imzalanacağı için gelecekteki tüm güncellemeler sorunsuz üstüne kurulacak.

## Doğrulama durumu

- [Doğrulandı] `build.gradle.kts` değişikliği, mevcut `playRelease` desenine
  birebir simetrik şekilde yazıldı — aynı `require(...)` güvenlik kontrolleri var.
- [Doğrulandı — 2026-11-08] Secret'lar GitHub'a eklendikten sonra
  `workflow_dispatch` ile gerçek bir CI çalışması tetiklendi
  (run 42502909839): "Decode beta signing keystore" adımı `USE_BETA_SIGNING=true`
  üretti, `flutter build apk --release --android-project-arg=githubBetaRelease=true`
  başarıyla tamamlandı. Üretilen APK indirilip `androguard` ile v2 imza
  sertifikası çıkarıldı — SHA256 parmak izi
  `B1:FD:54:C8:72:76:E9:75:3F:CB:AF:4B:6D:93:F0:01:0A:D9:D3:FD:D9:38:06:E0:46:2C:78:67:A5:EA:0F:BA`,
  bu da aynı oturumda `keytool` ile keystore üretilirken alınan fingerprint'le
  birebir eşleşiyor. **Yani CI artık her çalışmada aynı kalıcı anahtarla
  imzalıyor — P0 giderildi.** (Not: bu test çalışması bir tag push değil
  `workflow_dispatch` olduğu için "Publish companion release" adımı koşullu
  olarak atlandı, hiçbir public release/tag oluşmadı.)
- [Doğrulanmadı] Gerçek bir telefonda "eski APK kaldır → yeni kur → bir sonraki
  sürümü üstüne güncelle" senaryosu denenmedi — bu, Codex'in raporundaki en
  riskli, test edilmemiş adımla aynı, sadece imza artık kalıcı.
