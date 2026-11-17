# Eşya okuma gecikmesi düzeltmesi

6.0.2 sonrasında yapılan bu çalışma 6.0.3 kaynak, kurulum ve taşınabilir sürümlerine dahil edilerek yayınlandı.

## Bulgu ve değişiklik

Otomatik taramanın küçük görüntü karşılaştırması ve ağır OCR işlemi aynı bekleme aralığını kullanıyordu. Dengeli profilde 900 ms, Oyun öncelikli profilde 1400 ms kontrol aralığı vardı; kartın sabit kaldığını doğrulamak için ikinci örnek bekleniyordu.

Görüntü kontrolü artık Dengeli profilde 200 ms, Oyun öncelikli profilde 300 ms aralık kullanıyor. İki sabit karşılaştırma isteniyor. Ağır OCR işlemleri arasında mevcut 900/1400 ms asgari bütçe korunuyor. Sabit kart tekrar işlenmiyor. OCR kilidi meşgulse otomatik döngü eski ekran görüntüsüyle sırada beklemiyor; sonraki kontrolde güncel görüntüyü alıyor.

Zaman kontrollü testte ilk sabit kartın algılama beklemesi Dengeli profilde 900 → 400 ms, Oyun öncelikli profilde 1400 → 600 ms. Bunlar ekran yakalama ve OCR süresi hariç, başlangıç döngü hizasına bağlı simülasyon değerleridir. Kullanıcının bilgisayarında uçtan uca hızlanma ölçümü değildir. Daha sık görüntü kontrolünün gerçek oyun içi yükü henüz ölçülmedi.

Ölçüm kayıtlarına kart bulma (`card_locate`), karar hesaplama (`evaluate`), her OCR geçişi (`ocr`) ve tüm kart OCR geçişleri toplamı (`ocr_total`) eklendi. Otomatik tarama da `scan_total` ölçümü üretir. Liste başlığından yapılan yardımcı isim okuması `ocr_total` kapsamına dahil değildir.

## Doğrulama

- 6 yeni otomatik tarama testi: başlangıç gecikmesi, değişmeyen kart, OCR hız sınırı, kilit meşgulken güncel yakalama, yükleme ekranı ve dünya beklemesi.
- Mevcut otomatik tarama, performans, uygulama entegrasyonu, eşya koruması ve OCR eşzamanlılık testleri geçti. Çıktılar ve sonuçlar bu klasördedir.
- İki gerçek kartın dört çözünürlükteki sekiz OCR kontrolü geçti. Bu kontrol OCR doğruluğu içindir; oyun içinde toplam tepki süresi ölçümü değildir.

## Hem elle hem otomatik okuma için seçili bölge yolu

Kullanıcı kart bölgesini açıkça seçmişse ve bölge 1600 pikselden darsa, ilk okuma doğrudan bu bölgeden yapılır. Geçerli kart bulunursa ayrıca kart konumunu bulmak için OCR yapılmaz. Sonuç geçersizse kart bulma yolu korunur. Tam ekran ve geniş bölgeler eski konum bulma yolunu kullanır. Altı yeni test bu davranışı ve geçersiz girdinin İNCELE sonucunda kalmasını denetler.

Tek gerçek silah kartında, CPU RapidOCR ile iki yol önceden ısıtılıp dört karşılaştırma yapıldı. Çalıştırma sırası dönüşümlü değiştirildi. Medyan süre eski yolda 2,085 saniye, doğrudan bölge yolunda 0,971 saniye oldu. Dört çalıştırmada da eşya adı, nitelikler ve karar aynıydı. Bu ölçüm tek kart, seçili bölge ve tek OCR geçişi içindir; ekran yakalama, gerçek oyun ve 8 GB bilgisayar dahil değildir. Tam ekran taraması için aynı hızlanmayı göstermez. Ham sonuç `region_benchmark.json`, tekrar çalıştırılabilir ölçüm `tests/bench_region_scan.py` dosyasındadır.

Elle taramadaki OCR deneme sayısı ve karar korumaları değiştirilmedi. Kişisel ayarlar değiştirilmedi. Kaynak sürümü `scripts/run.bat` ile çalıştırılabilir; 6.0.3 kurulum ve taşınabilir paketleri bu düzeltmeleri içerir.
