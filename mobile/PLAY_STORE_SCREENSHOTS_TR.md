# Google Play ekran görüntülerini hazırlama

Mağazaya yüklenecek ekran görüntüleri son uygulamanın gerçek ekranından alınmalıdır. Tanıtım grafiğindeki çizimler ekran görüntüsü yerine kullanılamaz.

## HONOR telefondan yakalama

1. Telefona Google Play için son AAB'den üretilmiş test sürümünü kur; şu an çalışan 0.1.2 beta da ilk taslak görüntüleri almak için kullanılabilir.
2. Durum çubuğunda bildirimleri kapat, kişisel bilgi veya özel ağ adı görünmediğini kontrol et.
3. Uygulamayı aç ve şu ekranları ayrı ayrı yakala: ana özet, görev listesi/ilerleme, build listesi veya kaydedilmiş build, QR eşleştirme ekranı.
4. QR eşleştirme ekranında gerçek masaüstü token'ı/QR kodunu mağaza görseline koyma. QR ekranı görüntüsü alacaksan yeni token üretmeden boş tarayıcı ekranını veya kamera izin istemini kullan.
5. Hacim, okunabilirlik ve uygulamanın gerçek görünümü değişmeden PNG olarak telefondan dışa aktar.

## Yükleme kontrolü

- Telefon ekran görüntülerinde uygulamanın gerçek arayüzü görünmeli; mockup, çerçeve, özellik iddiası veya oynanmamış bir durum ekleme.
- Dosyaları `mobile/store-assets/screenshots/` klasörüne `phone-01-home.png`, `phone-02-tasks.png` gibi anlaşılır adlarla koy.
- Temel mağaza girişi için en az iki ekran görüntüsü hazırla. Google Play yönlendirme alanlarında görünürlük için en az dört gerçek ekran görüntüsü, her biri en az 1080 px olacak şekilde öneriliyor: dikey görseller 1080×1920, yatay görseller 1920×1080.\n- Yükleme anında Play Console'daki geçerli boyut ve biçim kurallarını yeniden kontrol et. Telefon ekranı görüntüleri 9:16 veya 16:9 oranında olmalı; farklı cihaz türleri için Console ayrı varlık alanları gösterirse her cihazı ayrıca gerçek cihazda doğrula.
- Gizlilik için canlı QR kod, eşleştirme token'ı, Wi-Fi SSID'si ve kullanıcıya özel verileri hiçbir görüntüde bırakma.

