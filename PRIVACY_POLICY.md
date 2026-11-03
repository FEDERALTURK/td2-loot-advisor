# TD2 Loot Advisor — Gizlilik Politikası

Son güncelleme: 3 Kasım 2026

Bu, TD2 Loot Advisor'ın tamamı için geçerli gizlilik politikasıdır: Windows masaüstü uygulaması, isteğe bağlı
topluluk/hesap sunucusu (Cloudflare Worker) ve Android/iOS Companion mobil uygulaması. Bağımsız, kâr amacı
gütmeyen bir topluluk projesidir; Ubisoft veya Massive Entertainment tarafından yayımlanmaz ya da desteklenmez.
(Companion mobil uygulamasının daha ayrıntılı önceki sürümü: [`mobile/PRIVACY_POLICY_TR.md`](mobile/PRIVACY_POLICY_TR.md).)

## Oyunun kendisiyle ilgili: hiçbir zaman

Program oyunun işlemine veya belleğine hiçbir zaman dokunmaz (okuma, yazma veya enjeksiyon yok), oyuna girdi
göndermez ve oyun dosyalarını değiştirmez. Yalnızca ekranı (OCR ile) ve oyunun kendi ayar dosyasını okur.

## Masaüstü uygulaması (varsayılan — hesapsız)

- **Hesapsız kullanım tamamen yereldir.** Taranan eşyalar, build'ler, ayarlar ve günlükler yalnızca kendi
  bilgisayarınızda (`%LOCALAPPDATA%`/uygulama klasörü) tutulur; hiçbir yere gönderilmez.
- **Düşüş istatistikleri (isteğe bağlı, topluluk özelliği açıksa):** Hangi eşyanın hangi aktivitede düştüğü,
  kimliği tuzlanmış-özetlenmiş bir istemci kodu ile sunucuya gönderilir. **IP adresi saklanmaz.** Eşya
  özellik (attribute) *değerleri* değil, yalnızca *türleri* gönderilir.
- **Topluluk görevleri (isteğe bağlı):** Kullanıcı izin verdiyse, ekranda görülen görev metni ve Türkçe çevirisi
  sunucuya gönderilir; kişisel bilgi içermez.

## Hesap sistemi (isteğe bağlı — Discord ile giriş)

Giriş tamamen isteğe bağlıdır; program hesapsız da tam olarak ücretsiz çalışır.

- Giriş, Discord OAuth2 ile yapılır; program Discord şifrenizi hiçbir zaman görmez.
- Sunucuda saklanan: oturum belirteçleri, lisans/davet anahtarları yalnızca **SHA-256 özeti** olarak tutulur —
  düz metin yalnızca üretildiği an bir kez gösterilir.
- Bir lisans tek bilgisayara bağlanır (cihaz parmak izi); panelden "Cihazı sıfırla" ile değiştirilebilir.
- **Hesap silme:** `DELETE /v1/me` (veya telefon tarafında `DELETE /v1/mobile/me`) ile talep edilir; oturumlar
  anında iptal edilir, asıl veri 24 saatlik bekleme süresinden sonra kalıcı olarak silinir.

## Mobil Companion — bulut eşleştirmesi (isteğe bağlı)

Telefon, masaüstü hesabınızla kısa ömürlü (5 dakika geçerli) bir kodla eşleştirilir. Telefon **asla doğrudan
masaüstüne bağlanmaz**; her şey Cloudflare Worker üzerinden, uçtan uca TLS ile geçer.

- Saklanan veri: cihaz kimliği/belirteci, eşleştirilen hesapla bağlantısı, senkronize edilen build verisi
  (sadece kullanıcının kendi build'leri — kimlik/hesap bilgisi içermez), ve varsa push bildirimi cihaz tokenı
  (FCM/APNs).
- Masaüstü yalnızca küçük durum olayları gönderir (örn. "tarama tamamlandı") — **ekran görüntüsü veya dosya
  asla gönderilmez.**
- Telefon, masaüstüne yalnızca izinli-liste'deki iki komuttan birini gönderebilir (`scan_start`/`scan_stop`) —
  başka hiçbir uzaktan komut yok.
- **Push bildirimi:** Yalnızca cihazınızın kendi FCM (Android) veya APNs (iOS) tokenı kullanılır; bu token
  üçüncü bir tarafla paylaşılmaz, yalnızca Google/Apple'ın kendi bildirim altyapısına iletim için kullanılır.
- Cihaz eşleştirmesi masaüstü panelinden ("Telefon eşleştir" → cihaz listesi) tek tek iptal edilebilir.
- Hesap silme isteği (telefon veya masaüstünden) **bağlı TÜM hesabı** siler — sadece o telefonu değil.

## Mobil Companion — yerel ağ (LAN/QR) eşleştirmesi

Bulut eşleştirmesinden tamamen ayrı, isteğe bağlı bir özelliktir: telefon, aynı yerel ağdaki masaüstüne QR
koddaki geçici bir belirteçle salt-okunur bağlanır. Uçtan uca şifreli değildir — yalnızca güvendiğiniz özel
Wi-Fi ağında kullanın. Ayrıntılar: [`mobile/PRIVACY_POLICY_TR.md`](mobile/PRIVACY_POLICY_TR.md).

## Reklam, analitik, üçüncü taraf takibi

Uygulamada reklam, reklam kimliği veya üçüncü taraf analitik SDK'sı **yoktur**. Veri hiçbir zaman satılmaz veya
pazarlama amacıyla paylaşılmaz.

## Çocuklar

Uygulama çocuklara yönelik olarak tasarlanmamıştır ve çocuklardan bilerek kişisel bilgi toplamaz.

## İletişim ve değişiklikler

Gizlilik soruları veya silme talepleri için [proje GitHub Issues sayfasını](https://github.com/FEDERALTURK/td2-loot-advisor/issues)
kullanın. Bu politika değişirse yukarıdaki tarih güncellenir.

---

# TD2 Loot Advisor — Privacy Policy

Last updated: November 3, 2026

This is the privacy policy for all of TD2 Loot Advisor: the Windows desktop app, the optional
community/account server (Cloudflare Worker), and the Android/iOS Companion mobile app. It is an independent,
non-commercial community project and is not published, endorsed, or supported by Ubisoft or Massive
Entertainment. (A more detailed, earlier version scoped to the mobile app:
[`mobile/PRIVACY_POLICY_TR.md`](mobile/PRIVACY_POLICY_TR.md).)

## The game itself: never

The app never touches the game's process or memory (no reading, writing, or injection), never sends input to
the game, and never modifies game files. It only reads the screen (via OCR) and the game's own settings file.

## Desktop app (default — no account)

- **Without an account, everything is local.** Scanned items, builds, settings, and logs stay on your own
  computer only; nothing is sent anywhere.
- **Drop statistics (optional, community feature):** if enabled, which item dropped from which activity is
  sent with a salted-hashed client id. **No IP address is stored.** Only attribute *types* are sent, never
  attribute *values*.
- **Community tasks (optional):** if the user opts in, the on-screen task text and its Turkish translation are
  sent to the server; it contains no personal information.

## Account system (optional — Discord sign-in)

Sign-in is entirely optional; the app is fully free and functional without an account.

- Sign-in uses Discord OAuth2; the app never sees your Discord password.
- What the server stores: session tokens and license/invite keys are stored only as **SHA-256 hashes** — the
  plaintext is shown once, at creation time, only.
- A license is bound to one computer (a device fingerprint); it can be reset from the panel ("Reset device").
- **Account deletion:** requested via `DELETE /v1/me` (or `DELETE /v1/mobile/me` from the phone); sessions are
  revoked immediately, and the underlying data is permanently deleted after a 24-hour grace period.

## Mobile Companion — cloud pairing (optional)

The phone is paired to your desktop account with a short-lived (5-minute) code. The phone **never connects
directly to the desktop**; everything goes through the Cloudflare Worker, over end-to-end TLS.

- Data stored: a device id/token, its link to the paired account, synced build data (only the user's own
  builds — no identity/account data embedded), and, if enabled, a push-notification device token
  (FCM/APNs).
- The desktop only sends small status events (e.g. "scan finished") — **screenshots or files are never
  sent.**
- The phone may send only one of two allow-listed commands to the desktop (`scan_start`/`scan_stop`) — no
  other remote command exists.
- **Push notifications:** only your own device's FCM (Android) or APNs (iOS) token is used; it is never shared
  with a third party, only used to deliver the notification through Google's/Apple's own push
  infrastructure.
- Paired devices can be revoked individually from the desktop panel ("Pair a phone" → device list).
- An account-deletion request (from either the phone or the desktop) deletes the **entire linked account** —
  not just that one phone.

## Mobile Companion — local network (LAN/QR) pairing

A separate, optional feature from cloud pairing: the phone connects read-only to the desktop on the same local
network using a temporary token from a QR code. It is not end-to-end encrypted — use it only on a trusted
private Wi-Fi network. Details: [`mobile/PRIVACY_POLICY_TR.md`](mobile/PRIVACY_POLICY_TR.md).

## Advertising, analytics, third-party tracking

The app has **no** ads, advertising ID, or third-party analytics SDK. Data is never sold or shared for
marketing purposes.

## Children

The app is not designed for children and does not knowingly collect personal information from children.

## Contact and changes

For privacy questions or deletion requests, use the
[project's GitHub Issues page](https://github.com/FEDERALTURK/td2-loot-advisor/issues). If this policy
changes, the date above will be updated.
