# Play Console Data safety formu — inceleme taslağı

Bu dosya uygulama kaynaklarının mevcut incelemesine göre hazırlanmıştır. Play Console'da gönderilecek son beyan, yayımlanacak AAB'nin izinleri ve tüm bağımlılıkları tekrar incelendikten sonra uygulama sahibi tarafından onaylanmalıdır. Google, verilerin nasıl kullanıldığını geliştiricinin doğru beyan etmesini bekler.

## Kodda görülen akışlar

- Hesap, reklam, reklam kimliği, analitik, crash reporting veya geliştiriciye veri yükleme uç noktası bulunmuyor.
- Görevlerin tamamlandı durumu ve yerel build'ler `shared_preferences` ile bu cihazda saklanıyor.
- Kamera izni QR tarayıcı eklentisinden geliyor; tarayıcı kullanıcı tarafından açılınca çalışıyor. QR içeriği cihazda çözülüyor.
- Görev/haber/build JSON verileri HTTPS ile GitHub'dan indiriliyor. İstekler normal bağlantı metaverisini GitHub altyapısına gösterir; uygulama IP adresini konum çıkarmak veya kullanıcı profili oluşturmak için okumuyor/kullanmıyor.
- QR eşleştirmesi açılırsa geçici token ve masaüstü durumu kullanıcının aynı yerel ağındaki kendi Windows uygulamasına HTTP üzerinden gider. Bu içerik geliştirici sunucusuna gitmez; taşıma şifreli değildir.
- Haber/kaynak bağlantıları kullanıcı dokunduğunda ayrı tarayıcıda açılır.

## Formdaki sorular için önerilen cevaplar

1. **Uygulama veri topluyor veya paylaşıyor mu?** Mevcut kodda kullanıcının kişisel verisini geliştiriciye ya da başka bir uygulamaya gönderen bir özellik yoktur. Son seçimi yapmadan önce Play Console'un gösterdiği izinleri ve AAB'deki üçüncü taraf kütüphaneleri kontrol edin. GitHub içerik isteklerinin ağ metaverisi ayrıca bu belgede açıklanmıştır.
2. **Reklam var mı?** Hayır.
3. **Hesap oluşturma veya hesap silme gerekiyor mu?** Hayır; uygulama hesabı yoktur.
4. **Kullanıcı verileri silme talebi var mı?** Uygulama hesabı veya geliştirici sunucusunda tutulan kullanıcı verisi yok. Yerel görev/build verileri uygulama verisini temizleyerek ya da uygulamayı kaldırarak silinir.
5. **Şifreleme aktarımda uygulanıyor mu?** Uygulamanın internet içerik isteği HTTPS kullanır. İsteğe bağlı masaüstü eşleştirmesi HTTP'dir. Form, uygulamanın topladığı tüm kullanıcı verisi aktarımda şifrelenmiyorsa tüm veri türleri için “şifreleniyor” cevabını seçmemelidir.

## Beyanı kilitlemeden önce tekrar kontrol et

- Play Console App content sayfasındaki her izin ve SDK sorusunu, tam olarak yüklenecek AAB'ye göre yanıtla.
- Android manifestinde internet ve kamera izinleri görünüyor; kamera yalnız QR ekranı için isteğe bağlıdır.
- Yeni bir analitik, reklam, hata raporlama veya bulut yedekleme SDK'sı eklersen bu belge ve gizlilik politikası güncellenmeli.
- Bu taslak, ağ servislerinin kendi sunucu loglarını uygulamanın kontrol ettiği kullanıcı profiliyle karıştırmaz. IP adresinin nasıl sınıflandırılacağı konusunda Play Console formu ve Google'ın [Data safety açıklaması](https://support.google.com/googleplay/android-developer/answer/10787469) esas alınmalıdır.
