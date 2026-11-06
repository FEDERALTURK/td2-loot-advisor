# TD2 Loot Advisor Companion Gizlilik Politikası

Son güncelleme: 6 Kasım 2026

Bu politika Android Companion uygulamasının hangi bilgileri kullandığını açıklar. Uygulama bağımsız bir topluluk projesidir; Ubisoft veya Massive Entertainment tarafından yayımlanmaz ya da desteklenmez.

## Uygulamanın kullandığı bilgiler

- **Kamera:** Yalnızca kullanıcı Telefon Arkadaşı eşleştirme ekranında QR tarayıcıyı açtığında kullanılır. Kamera görüntüsü QR kodunu cihaz üzerinde çözümlemek için işlenir; uygulama tarafından kaydedilmez veya geliştirici sunucusuna gönderilmez.
- **Cihazda saklanan tercihler:** Tamamlandı olarak işaretlenen görevler, kullanıcının kaydettiği build'ler ve senkron revizyonları Android uygulama depolamasında saklanır. Bulut eşleştirmesi seçilirse cihaz kimliği ile oturum belirteci Android Keystore/iOS Keychain tabanlı güvenli depoda saklanır. Bunlar uygulama verisini temizleyince, eşleştirme kaldırılınca veya uygulama kaldırılınca silinir.
- **Herkese açık oyun içerikleri:** Güncel görev, haber ve build JSON dosyalarını almak için `raw.githubusercontent.com` adresine istek gönderilir. İnternet bağlantısı yoksa APK ile gelen yerel içerik kullanılır. GitHub bağlantısı standart ağ isteği bilgilerini (ör. IP adresi ve istemci yazılımı) kendi hizmet kuralları kapsamında görebilir.
- **İsteğe bağlı masaüstü eşleştirmesi:** Kullanıcı Windows uygulamasındaki QR kodu tararsa telefon, aynı yerel ağdaki özel IPv4 adresine ve QR kodundaki geçici belirtece istek gönderir. Belirteç uygulama belleğinde tutulur ve uygulama kapatılınca kaybolur. Bu bağlantı salt okunurdur; oyun taraması veya masaüstü ayar komutu göndermez. İstek ve yanıtlar geliştiriciye aktarılmaz.
- **İsteğe bağlı bulut eşleştirmesi ve build senkronu:** Kullanıcı Windows uygulamasında üretilen kısa ömürlü eşleştirme kodunu girerse telefon, TLS üzerinden TD2 Loot Advisor bulut hizmetine bağlanır. Hizmet; rastgele cihaz kimliği, oturum belirteci, masaüstünün çevrimiçi/çevrimdışı durumu ve son olay özeti ile kullanıcının özellikle eşitlemeyi seçtiği build adlarını/içeriklerini işler. Bu özellik isteğe bağlıdır; genel görev ve haber ekranları için gerekli değildir. Eşleştirilmiş cihaz masaüstü uygulamasından iptal edilebilir.
- **İsteğe bağlı bildirimler:** Kullanıcı Bulut eşleştirmesi ekranında bildirim anahtarını açıkça etkinleştirirse işletim sistemi izin penceresi gösterilir. İzin verilirse cihazın FCM/APNs bildirim belirteci, masaüstü tarama sonucu gibi seçilen bildirimleri göndermek için bulut hizmetine kaydedilir. Anahtar kapatılırsa uygulama kayıtlı belirteci silmek için hizmete istek gönderir. Uygulama açılışında veya eşleştirme sırasında otomatik bildirim izni istenmez.
- **Dış bağlantılar:** Kullanıcı haber veya kaynak bağlantısına dokunduğunda sayfa cihazın harici tarayıcısında açılır ve ilgili sitenin gizlilik politikası geçerli olur.

## Toplama, paylaşma ve reklam

Uygulamada reklam, reklam kimliği veya davranış analitiği yoktur. Yerel kullanımda görev/build tercihleri cihazda kalır. Bulut eşleştirmesi seçilirse yukarıda açıklanan cihaz oturumu, durum ve eşitlenmiş build verileri yalnızca bu hizmetin çalışması için işlenir; satılmaz veya reklam amacıyla paylaşılmaz. İnternet içerik isteği için GitHub'ın, isteğe bağlı bulut eşleştirmesi için TD2 Loot Advisor bulut hizmetinin sunucularına bağlantı yapılır. Push bildirimi etkinse Firebase/Apple bildirim altyapısı da cihaz belirtecini iletmek için kullanılır.

## Güvenlik ve saklama

Masaüstü QR eşleştirmesi özel yerel ağdaki HTTP bağlantısını kullanır ve uçtan uca şifreli değildir. Yalnızca güvendiğiniz özel Wi-Fi ağında kullanın; modemde internetten erişim için port açmayın. Bulut eşleştirmesi TLS kullanır ve telefonun kalıcı oturum belirteci işletim sistemi güvenli deposunda tutulur. Yerel eşleştirmeyi kaldırabilir, masaüstünden cihazı iptal edebilir veya uygulama içinden hesap ve ilişkili bulut verileri için silme talebi oluşturabilirsiniz; silme işlemi 24 saatlik bekleme süresinden sonra tamamlanır.

## Çocuklar

Uygulama çocuklara yönelik olarak tasarlanmamıştır ve çocuklardan bilerek kişisel bilgi toplamaz.

## İletişim ve değişiklikler

Gizlilik soruları veya talepleri için [proje GitHub Issues sayfasını](https://github.com/FEDERALTURK/td2-loot-advisor/issues) kullanın. Bu politika değişirse güncelleme tarihi bu sayfada değiştirilir.

---

# TD2 Loot Advisor Companion Privacy Policy

Last updated: November 6, 2026

This policy describes how the Android Companion app uses information. This is an independent community project and is not published, endorsed, or supported by Ubisoft or Massive Entertainment.

## Information the app uses

- **Camera:** Used only after the user opens the QR scanner from the Phone Companion pairing screen. The camera image is processed on-device to decode the QR code and is not stored or sent to a developer server by the app.
- **Preferences stored on the device:** Completed-task selections, user-saved builds, and sync revisions are stored in app storage. When cloud pairing is chosen, the device ID and session token are stored in Android Keystore/iOS Keychain-backed secure storage. They are removed when app data is cleared, the pairing is removed, or the app is uninstalled.
- **Public game content:** The app requests current task, news, and build JSON files from `raw.githubusercontent.com`. Bundled offline content is used without an internet connection. GitHub may receive standard network request information (for example, an IP address and client software) under its service terms.
- **Optional desktop pairing:** When the user scans the Windows app's QR code, the phone sends requests to a private IPv4 address on the same local network using the temporary token in the QR code. The token is held in app memory and is discarded when the app closes. This connection is read-only; it does not send scan or desktop settings commands. Pairing requests and responses are not sent to the developer.
- **Optional cloud pairing and build sync:** When the user enters a short-lived pairing code created in the Windows app, the phone connects over TLS to the TD2 Loot Advisor cloud service. The service processes a random device ID, session token, desktop online/offline status and last-event summary, plus names/content of builds the user chooses to sync. This is optional and not needed for public task or news screens. A paired device can be revoked from the desktop app.
- **Optional notifications:** The operating-system permission prompt is shown only after the user explicitly enables notifications in the Cloud Pairing screen. If permission is granted, the device's FCM/APNs notification token is stored by the cloud service to deliver selected notifications, such as a desktop scan result. Turning the switch off requests deletion of the stored token. The app does not request notification permission at launch or merely because a device is paired.
- **External links:** When a user opens a news or source link, the page opens in the device's external browser and the linked site's privacy policy applies.

## Collection, sharing, and advertising

The app has no ads, advertising ID, or behavioural analytics. In local-only use, task and build preferences remain on the device. If cloud pairing is chosen, the session, status and synced build data described above are processed only to provide that feature; they are not sold or shared for advertising. GitHub receives public-content requests. The TD2 Loot Advisor cloud service receives optional cloud-pairing requests, and Firebase/Apple notification infrastructure receives a device token only when notifications are enabled.

## Security and retention

Desktop QR pairing uses HTTP on a private local network and is not end-to-end encrypted. Use it only on a trusted private Wi-Fi network and do not open an internet-facing router port. Cloud pairing uses TLS and the phone's persistent session token is held in secure operating-system storage. You can remove local pairing, revoke a device from the desktop app, or request deletion of the account and associated cloud data in the app; deletion completes after a 24-hour grace period. Local task and build data remain until the user clears app data or uninstalls the app.

## Children

The app is not designed for children and does not knowingly collect personal information from children.

## Contact and changes

For privacy questions or requests, use the [project GitHub Issues page](https://github.com/FEDERALTURK/td2-loot-advisor/issues). The last-updated date on this page will be changed when this policy changes.
