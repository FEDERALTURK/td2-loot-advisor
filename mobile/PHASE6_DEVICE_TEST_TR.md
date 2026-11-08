# Faz 6 — Android Gerçek Cihaz Kabul Testi

Bu liste, Play Console'a herhangi bir dosya yüklemeden önce gerçek Android
cihazda yapılacak kabul testidir. Uygulama oyun belleğine erişmez; yalnız mobil
companion akışları denenir.

## Hazırlık

1. Telefonda **Geliştirici seçenekleri → USB hata ayıklama** açın.
2. Telefonu USB ile bağlayın ve ekrandaki RSA hata ayıklama iznini onaylayın.
3. PC'de cihazı kontrol edin:

   ```powershell
   C:\Users\PC\tools\android-sdk\platform-tools\adb.exe devices -l
   ```

   Durum `device` olmalıdır; `unauthorized` ise telefon ekranındaki izni
   onaylayın.
4. Depo kökünden ön-denetimi çalıştırın:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\mobile_preflight.ps1 -RequireDevice
   ```

   Firebase yapılandırması yalnız ana yerel çalışma kopyasında bulunuyorsa,
   bildirim testi için aynı komuta `-RequireFirebaseConfig` ekleyin. Bu komut
   dosyanın içeriğini okumaz ve Git'e eklemez.

## Kabul matrisi

| Alan | İşlem | Başarı ölçütü |
|---|---|---|
| Açılış | Debug APK'yı kurup açın | Uygulama kapanmadan açılış ekranından ana menüye geçer. |
| İçerik | Görevler, haberler ve build'leri yenileyin | Ağ yoksa yerel içerik kalır; ağ varsa güncel veri görünür. |
| Yerel QR | Windows Telefon Arkadaşı QR kodunu okutun | Yalnız özel Wi-Fi IPv4 kabul edilir; masaüstü durumu görünür. |
| Bulut eşleştirmesi | Masaüstünde kod üretip telefonda girin | Kod tek kullanımlık/5 dakika geçerli; bağlantı başarısızsa anlaşılır hata görünür. |
| Build senkronu | Build ekleyin, eşitleyin, silin, tekrar eşitleyin | Çift kayıt oluşmaz; silinen build geri gelmez. |
| Bildirim izni | Eşleştirmeden sonra uygulamayı yeniden açın | İzin penceresi **çıkmamalı**. |
| Bildirim opt-in | Bulut Eşleştirmesi → Masaüstü tarama bildirimleri anahtarını açın | İzin penceresi yalnız burada çıkar. Reddedilirse uygulama çalışmayı sürdürür. |
| Push | İzin verildiyse masaüstünde tarama sonucu üretin | Telefon tokenı kaydolur ve FCM bildirimi gelir. Firebase eksikse kullanıcıya anlaşılır hata görünür; uygulama çökmez. |
| Bildirim opt-out | Anahtarı kapatın | Yerel tercih kapanır; sunucudaki token silme isteği gönderilir. |
| Hesap silme | Hesabı sil düğmesine basın, ilk uyarıda vazgeçin | Onay olmadan hiçbir veri silme isteği gönderilmez. |
| Erişilebilirlik | Sistem yazı boyutunu büyütün, koyu tema ve ekran döndürmeyi deneyin | Temel düğmeler görünür, metin taşması kritik işlem düğmelerini gizlemez. |

## Kanıt kaydı

Her başarısız adım için şu bilgileri not edin; şifre, token veya Firebase dosyası
göndermeyin:

- Cihaz modeli ve Android sürümü
- Uygulama sürümü ve APK/AAB adı
- Tekrarlama adımları
- Ekran görüntüsü veya hata metni
- Bağlantı türü: Wi-Fi/mobil veri/çevrimdışı

## Yayın kapısı

Bu listedeki açılış, eşleştirme, build senkronu ve izin davranışı gerçek cihazda
başarılı olmadan Play internal testing veya üretim kanalına geçilmez. Mağazaya
yükleme ayrıca kullanıcı onayı, Play upload key ve tamamlanmış Data Safety
beyanını gerektirir.
