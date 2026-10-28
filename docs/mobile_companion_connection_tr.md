# Telefon uygulamasını Windows programına bağlama

Bu kılavuz `TD2 Loot Advisor Companion 0.1.1-beta` içindir. Telefon uygulaması ile Windows masaüstü programı şu anda **aynı yerel Wi-Fi ağı** üzerinden, masaüstündeki Telefon Arkadaşı sunucusuna bağlanır. Eşleşme QR kodla yapılır. Bağlantı salt okunurdur: telefon son eşya kararını, aktif build ilerlemesini ve varsa satıcı eşleşmelerini gösterir; bilgisayarda tarama başlatamaz, ayar değiştiremez ve oyunla etkileşime girmez.

## Gerekli olanlar

- Windows programı `9.0.8` veya üstü.
- Android beta uygulaması `0.1.1`.
- Bilgisayar ve telefon aynı güvenilir ev Wi-Fi ağına bağlı olmalı. Misafir Wi-Fi, cihaz yalıtımı açık ağlar, VPN'ler ve mobil veri üzerinden bağlantı kurulamıyor.
- Masaüstündeki Telefon Arkadaşı özelliği hesap/lisans tarafından kilitliyse, uygulamada bu özelliğe erişim veren lisans etkin olmalı.

## İlk bağlantı

1. Bilgisayarda TD2 Loot Advisor'ı açın. Telefonu ve bilgisayarı aynı ev Wi-Fi ağına bağlayın.
2. **Ayarlar → Senkronizasyon → Telefon Arkadaşı** bölümüne gidin. Telefon Arkadaşı **Başlat** düğmesine basın.
3. Programın oluşturduğu QR kod ekranda görünür halde kalsın. Windows Güvenlik Duvarı izin sorarsa yalnızca **Özel ağlar** için erişime izin verin; ortak ağlar seçeneğini açmayın.
4. Android'de **TD2 Loot Advisor Companion** uygulamasını açıp **Özet → Masaüstü eşleştirmesi** kartına dokunun.
5. Kamera iznini verin ve bilgisayar ekranındaki QR kodu okutun. Uygulamada son eşya kararı ve build bilgisi görünüyorsa bağlantı kurulmuştur.
6. Eşleştirme penceresini kapatabilirsiniz. Uygulama açıkken masaüstü bilgisayardan yaklaşık iki saniyede bir güncel salt-okunur durum alır.

## Kullanım ve bağlantıyı kesme

- Windows programında Telefon Arkadaşı **Durdur** düğmesine basınca sunucu kapanır ve telefondaki canlı durum güncellemesi kesilir.
- Telefonda eşleştirme kartının bağlantıyı kes simgesine basınca telefon token'ı bellekten siler.
- Uygulama yeniden açıldığında QR kodu tekrar okutun. Eşleştirme kimlik bilgisi cihazda kalıcı olarak saklanmaz.
- Bilgisayar uykuya geçerse, Wi-Fi değişirse veya program kapanırsa telefon bağlantı hatası gösterir. Sunucuyu yeniden başlatıp yeni QR kodu okutun.

## Bağlanmıyorsa

1. Her iki cihazın aynı Wi-Fi ağı adını kullandığını ve VPN'in kapalı olduğunu kontrol edin.
2. Windows programında Telefon Arkadaşı'nın **Başlat** durumunda olduğuna ve yeni QR kodun ekranda olduğuna bakın.
3. Windows Güvenlik Duvarı'nda uygulamaya yalnızca **Özel ağ** izni verildiğini kontrol edin. Güvenlik duvarını tümden kapatmayın.
4. Telefonun Wi-Fi ayarında "cihazlar arası iletişimi engelle" veya misafir ağı yalıtımı varsa kapalı olmalı.
5. QR kod eskiyse, masaüstü sunucusunu durdurup tekrar başlatın ve yeni kodu okutun.
6. Kurumsal/kampüs Wi-Fi ağları cihazlar arası bağlantıyı engelleyebilir. Böyle bir ağda bu yerel eşleştirme çalışmaz.

## Ağ ve gizlilik bilgisi

- QR kod özel ağdaki bilgisayar adresini ve o sunucu çalışırken geçerli rastgele bağlantı anahtarını taşır. Kodu yalnızca kendi telefonunuzla okutun; ekran görüntüsünü, QR adresini veya bağlantı anahtarını paylaşmayın.
- Telefon uygulaması taranan adresin özel IPv4 yerel ağ aralıklarından birinde olmasını zorunlu tutar. Bu sürüm genel internet adreslerine veya özel olmayan alan adlarına bağlanmaz.
- Masaüstü Telefon Arkadaşı `http` kullanır ve anahtarı yerel ağ içinde taşır. Bu nedenle yalnızca güvendiğiniz ev ağında kullanın. Modem/router üzerinde port yönlendirme açmayın, bilgisayarı internete açmayın ve ortak Wi-Fi'da başlatmayın.
- Masaüstü programı QR sunucusunu başlatırken yeni bir anahtar üretir. Sunucuyu durdurup yeniden başlatmak önceki QR anahtarını geçersiz kılar.
- Uygulamadaki görev/haber/build içerikleri ve masaüstü eşleştirmesi farklı kaynaklardır. Eşleştirme masaüstü verisini telefon hesabına yüklemez; telefonun kendi görev işaretleri ve kullanıcı build'leri cihazda kalır.

## Bu beta sürümünün sınırları

- Masaüstü eşleştirmesi Android telefonda uygulama içinden QR tarayarak çalışır.
- Eşleştirme aynı yerel ağla sınırlıdır; internet üzerinden uzaktan bağlantı, bildirim, bulut senkronizasyonu veya telefon uygulamasından masaüstü kontrolü yoktur.
- APK yan yükleme beta paketidir. Android mağaza yayını imzası kullanılmamıştır. iOS kodu projede bulunur, ancak iOS derlemesi ve cihaz testi macOS/Xcode gerektirir.
- Beta APK'ları mağaza anahtarı yerine CI debug anahtarıyla imzalanır. Android bir önceki APK ile imza uyuşmazlığı bildirirse, eskisini kaldırıp yenisini kurmak gerekir; uygulamayı kaldırmak telefondaki yerel görev işaretlerini ve kaydedilmiş build'leri siler.
- Ağdaki istemcilerle masaüstü arasında HTTP kullanıldığı için bu beta hassas veya ortak ağlarda kullanılmamalıdır. Daha sonraki internet/uzaktan eşleştirme için HTTPS, kısa ömürlü tek kullanımlık kod ve cihaz iptali olan ayrı bir aktarım katmanı gerekir.
