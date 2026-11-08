# Faz 7 — Play Internal Testing Yayın Kapısı

Bu faz, uygulamayı Google Play'e **yüklemeden önce** imzalı Android App Bundle
hazırlığını ve mağaza beyanlarını denetlenebilir hâle getirir. Bu belge bir
mağaza yükleme veya üretim yayını izni değildir.

## Fazın hedefi

- Gerçek cihaz kabul testinin kanıtını toplamak.
- Kullanıcının yerel upload key'i ile imzalı AAB üretebildiğini doğrulamak.
- Play Console'daki Data safety, gizlilik politikası ve mağaza varlıklarının
  uygulamanın gerçek davranışıyla tutarlı olmasını sağlamak.
- İlk yüklemeyi yalnızca **Internal testing** kanalına sınırlamak.

## Kesin yayın kapıları

| Kapı | Gerekli kanıt | Durum |
|---|---|---|
| Gerçek cihaz | Faz 6 açılış, eşleştirme, build senkronu ve izin kontrolleri | Bekliyor |
| Upload key | `key.properties` ve keystore yerelde var, Git tarafından yok sayılıyor | Bekliyor |
| İmzalı AAB | `-BuildSignedAab` ile AAB oluşturuluyor | Bekliyor |
| Firebase | Bildirim vaat edilecekse yapılandırma ve opt-in gerçek cihazda çalışıyor | Bekliyor |
| Gizlilik URL'si | Herkese açık, uygulama içindeki bağlantıyla aynı politika | Bekliyor |
| Data safety | Yerel QR, isteğe bağlı bulut eşleştirmesi/build senkronu ve opt-in token doğru beyan edildi | Bekliyor |
| Mağaza varlıkları | Simge, özellik görseli, gerçek cihaz ekran görüntüleri, destek e-postası | Bekliyor |

## Güvenli yerel komut

Depo kökünde aşağıdaki komut yalnız denetim ve yerel AAB üretimi yapar;
Play Console'a dosya yüklemez, keystore parolalarını yazdırmaz ve hiçbir sırrı
Git'e eklemez:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\play_store_preflight.ps1 -RequireDevice -RequireUploadKey -BuildSignedAab
```

Telefon ya da upload key henüz hazır değilse parametreleri çıkarıp önce temel
denetimi çalıştırabilirsiniz:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\play_store_preflight.ps1
```

## Play Console sırası

1. Kullanıcı kendi Play Console hesabında uygulama kaydını açar.
2. Play App Signing etkinleştirilir; yerel upload key yalnız bilgisayarda
   saklanır ve güvenli şekilde yedeklenir.
3. İmzalı AAB yalnız **Internal testing** kanalına yüklenir.
4. Davetli testçiler gerçek cihazda temel akışları doğrular.
5. Herhangi bir üretim/kapalı test yayını için yeniden açık kullanıcı onayı
   alınır. İlk üretim erişimi için Google'ın güncel testçi ve süre şartları
   Play Console'dan ayrıca teyit edilir.

## Sınırlar

- Bu uygulama oyun belleği okumaz, DLL enjekte etmez, anti-cheat aşmaz ve oyun
  verisini değiştirmez.
- QR eşleştirmesi yalnız yerel ağ içindir; güvenilmeyen ağda kullanılmamalıdır.
- Play Console, geliştirici hesabı, ödeme yöntemi, upload key parolası veya
  Firebase sırları kullanıcı tarafından yönetilir; bunlar mesajlara veya Git'e
  gönderilmez.
