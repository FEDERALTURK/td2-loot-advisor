# TD2 Loot Advisor Companion Gizlilik Politikası

Son güncelleme: 28 Ekim 2026

Bu politika Android Companion uygulamasının hangi bilgileri kullandığını açıklar. Uygulama bağımsız bir topluluk projesidir; Ubisoft veya Massive Entertainment tarafından yayımlanmaz ya da desteklenmez.

## Uygulamanın kullandığı bilgiler

- **Kamera:** Yalnızca kullanıcı Telefon Arkadaşı eşleştirme ekranında QR tarayıcıyı açtığında kullanılır. Kamera görüntüsü QR kodunu cihaz üzerinde çözümlemek için işlenir; uygulama tarafından kaydedilmez veya geliştirici sunucusuna gönderilmez.
- **Cihazda saklanan tercihler:** Tamamlandı olarak işaretlenen görevler ve kullanıcının kaydettiği build'ler Android uygulama depolamasında saklanır. Bunlar uygulama verisini temizleyince veya uygulamayı kaldırınca silinir.
- **Herkese açık oyun içerikleri:** Güncel görev, haber ve build JSON dosyalarını almak için `raw.githubusercontent.com` adresine istek gönderilir. İnternet bağlantısı yoksa APK ile gelen yerel içerik kullanılır. GitHub bağlantısı standart ağ isteği bilgilerini (ör. IP adresi ve istemci yazılımı) kendi hizmet kuralları kapsamında görebilir.
- **İsteğe bağlı masaüstü eşleştirmesi:** Kullanıcı Windows uygulamasındaki QR kodu tararsa telefon, aynı yerel ağdaki özel IPv4 adresine ve QR kodundaki geçici belirtece istek gönderir. Belirteç uygulama belleğinde tutulur ve uygulama kapatılınca kaybolur. Bu bağlantı salt okunurdur; oyun taraması veya masaüstü ayar komutu göndermez. İstek ve yanıtlar geliştiriciye aktarılmaz.
- **Dış bağlantılar:** Kullanıcı haber veya kaynak bağlantısına dokunduğunda sayfa cihazın harici tarayıcısında açılır ve ilgili sitenin gizlilik politikası geçerli olur.

## Toplama, paylaşma ve reklam

Uygulamada hesap, reklam, reklam kimliği, analitik veya geliştiriciye veri gönderen bir kullanıcı profili yoktur. Görev/build tercihleri cihazda kalır. Masaüstü eşleştirme verisi sadece kullanıcının aynı yerel ağdaki Windows uygulamasına gider. İnternet içerik isteği için GitHub'ın sunucularına bağlantı yapılır.

## Güvenlik ve saklama

Masaüstü eşleştirmesi özel yerel ağdaki HTTP bağlantısını kullanır ve uçtan uca şifreli değildir. Yalnızca güvendiğiniz özel Wi-Fi ağında kullanın; modemde internetten erişim için port açmayın. Eşleştirme belirteci yalnızca oturum süresince bellekte tutulur. Uygulama, cihazdaki görev ve build kayıtlarını kullanıcı uygulama verisini temizleyene veya uygulamayı kaldırana kadar saklar.

## Çocuklar

Uygulama çocuklara yönelik olarak tasarlanmamıştır ve çocuklardan bilerek kişisel bilgi toplamaz.

## İletişim ve değişiklikler

Gizlilik soruları veya talepleri için [proje GitHub Issues sayfasını](https://github.com/FEDERALTURK/td2-loot-advisor/issues) kullanın. Bu politika değişirse güncelleme tarihi bu sayfada değiştirilir.

---

# TD2 Loot Advisor Companion Privacy Policy

Last updated: October 28, 2026

This policy describes how the Android Companion app uses information. This is an independent community project and is not published, endorsed, or supported by Ubisoft or Massive Entertainment.

## Information the app uses

- **Camera:** Used only after the user opens the QR scanner from the Phone Companion pairing screen. The camera image is processed on-device to decode the QR code and is not stored or sent to a developer server by the app.
- **Preferences stored on the device:** Completed-task selections and user-saved builds are stored in Android app storage. They are removed when app data is cleared or the app is uninstalled.
- **Public game content:** The app requests current task, news, and build JSON files from `raw.githubusercontent.com`. Bundled offline content is used without an internet connection. GitHub may receive standard network request information (for example, an IP address and client software) under its service terms.
- **Optional desktop pairing:** When the user scans the Windows app's QR code, the phone sends requests to a private IPv4 address on the same local network using the temporary token in the QR code. The token is held in app memory and is discarded when the app closes. This connection is read-only; it does not send scan or desktop settings commands. Pairing requests and responses are not sent to the developer.
- **External links:** When a user opens a news or source link, the page opens in the device's external browser and the linked site's privacy policy applies.

## Collection, sharing, and advertising

The app has no account, ads, advertising ID, analytics, or user profile that sends data to the developer. Task and build preferences remain on the device. Desktop pairing data goes only to the user's Windows app on the same local network. GitHub receives the app's public-content requests.

## Security and retention

Desktop pairing uses HTTP on a private local network and is not end-to-end encrypted. Use it only on a trusted private Wi-Fi network and do not open an internet-facing router port. The pairing token is held in memory for the session only. Task and build data remain on the device until the user clears app data or uninstalls the app.

## Children

The app is not designed for children and does not knowingly collect personal information from children.

## Contact and changes

For privacy questions or requests, use the [project GitHub Issues page](https://github.com/FEDERALTURK/td2-loot-advisor/issues). The last-updated date on this page will be changed when this policy changes.
