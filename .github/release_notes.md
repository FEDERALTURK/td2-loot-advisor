## TD2 Loot Advisor — Windows

**9.1.5.13 — Windows canlı çeviri renderer güvenli modu ve CI WebSocket düzeltmesi**

- Windows'ta yerinde çeviri artık büyük saydam Canvas/Toplevel yüzeyi kullanmaz. Her Türkçe metin kendi küçük opak kutusunda çizilir; DX12/DWM saydamlık hatasının oluşturduğu boş siyah dikdörtgen ortadan kaldırılır.
- Yerinde çeviri kapanırken tüm küçük kutular birlikte kapatılır; ekranda bayat overlay kalmaz.
- HDR durumu `state.cfg` dosyasından her senkron ve tanılama isteğinde güncel olarak okunur; eski önbellek yanlış HDR uyarısı üretmez.
- Node.js WebSocket CI smoke testi sonuç aldıktan sonra süreci açıkça sonlandırır, zaman aşımı 30 saniyeye çıkarılır ve hata çıktısı workflow logunda korunur.

**9.1.5.12 — HDR durumunun güncel okunması**

- `state.cfg` içindeki `hdr = "Off"` değeri artık boşluk, `disabled` ve `no` varyantlarıyla birlikte güvenilir biçimde kapalı kabul edilir.
- Program açıkken oyun HDR ayarı değiştirildiğinde eski `_last_game_settings` önbelleği kullanılmaz; senkron ve tanılama ekranı dosyayı yeniden okur.
- HDR kapalı olduğu hâlde gösterilen yanlış HDR uyarıları giderildi.

**9.1.5.11 — Boş/siyah canlı çeviri penceresi düzeltmesi**

- Yerinde çeviri Toplevel arka planı Windows saydam renk anahtarıyla açıkça eşitlenir; saydamlık desteklenmediğinde siyah dikdörtgen oluşması engellenir.
- Çizilecek Türkçe satırı kalmayan overlay öğeleri gösterilmeden filtrelenir.
- Tüm yerleşim öğeleri elendiyse boş pencere açık bırakılmaz; güvenli ekran overlay’ine geri dönülür.
- Overlay, yerinde çeviri ve canlı çeviri regresyon testleri yeniden doğrulandı.

**9.1.5.10 — Windows OCR/CI güvenilirliği ve isteğe bağlı paketler**

- DirectML sağlayıcısı bulunmayan GitHub/Windows ortamlarında GPU testi artık yanlış yayın hatası üretmez; durum kontrollü biçimde `SKIP` olarak raporlanır. DirectML bulunan makinelerde gerçek sonuç benzerliği denetlenmeye devam eder.
- Windows senkronizasyon testi, uygulamanın Tesseract keşif akışını kullanır; standart Tesseract kurulumları ve kullanıcı tarafından seçilen yol testte de geçerlidir.
- Küçük/ölçeklenmiş oyun pencerelerinde Tesseract attribute satırlarını kaybederse senkron benchmark doğal çözünürlükte güvenli doğrulama yapar; süre ölçümü hedef pencere boyutunda korunur.
- Launcher, temel OCR/eşya okuma paketlerini ses, AI, sistem tepsisi ve QR gibi isteğe bağlı entegrasyonlardan ayırır. Eksik opsiyonel paketler artık programı durdurmak yerine hangi özelliğin kapalı olduğunu bildirir.
- Python 3.13–3.15 test aralığı launcher tarafından görünür hâle getirildi; desteklenmeyen sürümlerde açık uyarı gösterilir.
- OCR ve senkronizasyon testleri için Python çalışma sürümü workflow günlüğüne yazılır.

**9.1.5.6 — Canlı çeviri başlatma ve sonuç kararlılığı**

- İstatistik tarih seçicisinin konuşma çevirisi motoruyla aynı değişkeni kullanması düzeltildi. Canlı çeviriyi başlat düğmesi ve F6 artık istatistik ekranını ses motoru sanarak durdurmaya çalışmaz.
- Otomatik ekran taraması, devam eden veya sıradaki çeviriyi sürekli iptal etmez. Elle çevirme ve durdurma işlemleri önceliğini korur.
- Başlatma ve elle çevirme ön denetimi hataları tanılama günlüğüne yazılır.
- Beş regresyon testi eklendi. Yayın öncesi kurulu EXE üzerinde gerçek RapidOCR, OPUS-MT ve normal/yerinde kaplama testi zorunlu hale getirildi.
- Yerel modelin kullanıcı tarafından indirilmesi korunur; bu güncelleme kullanıcıya otomatik model indirme başlatmaz.

**9.1.5.7 — Kısayol görünürlüğü ve kısmi sonuç güvenliği**

- Canlı çeviri kısayolunun alındığı ve düğme durumunun değiştiği tanılama günlüğünde görünür hâle getirildi.
- Canlı çeviri durdurulurken sesli altyazı nesnesi yoksa oluşabilecek yan etki giderildi.
- Sayı veya özel isim doğrulaması başarısız olan tek OCR bloğu, aynı ekrandaki güvenli blokların gösterilmesini engellemez; hatalı blok gösterilmez ve uyarı yazılır.

**9.1.5.8 — Sürüm geri dönüşü, fabrika ayarı ve maskeli log raporu**

- Güncellemeler bölümüne GitHub sürüm geçmişinden seçerek eski Windows sürümüne dönme akışı korunarak görünür hâle getirildi.
- Aynı alana fabrika ayarları düğmesi eklendi. Ayarlar sıfırlanmadan önce otomatik yedeklenir; build, sandık, geçmiş ve log dosyaları silinmez.
- Log ekranına kullanıcı onaylı “Logu GitHub'a gönder” düğmesi eklendi. Son kayıtlar token, anahtar, e-posta, kullanıcı yolu, IP ve webhook bilgileri maskelenerek mevcut rapor paneline gönderilir; bağlantı yoksa güvenli kuyruğa alınır.

**9.1.5.9 — Boş/siyah çeviri kaplaması düzeltmesi**

- Yerinde çeviri kaplamasının ilk Tk çizimi zorlanıyor; metin çizilmeden siyah pencere kalmıyor.
- OCR kutuları geçersiz veya ekran dışında kaldığında boş pencere yerine normal okunabilir çeviri kutusuna otomatik düşülüyor.
- Kaplama modu, blok ve yerleşim sayıları tanılama günlüğüne yazılıyor.


**9.1.4 — Komuta Merkezi ve güvenli güncelleme**

- Ekipman → Sandık → Komuta Merkezi bağlantıları ve Türkçe/İngilizce menü etiketleri tamamlandı. Günlük hedef loot için eski günün görevleri önerilmez; doğrulanmış eşleşme yoksa açıkça belirtilir.
- Günlük hedef loot ve haftalık satıcı önbelleği için ayrı eskilik uyarıları eklendi.
- Komuta Merkezi üzerinden eşya/build araması ve bilinmeyen attribute anahtarı denetimi açılabilir. Arama yazarken kısa gecikmeyle çalışır.
- Sandık ve build'ler birlikte yedeklenir; geri yüklemeden önce doğrulanır ve mevcut veriler pre_restore_backup.json dosyasında saklanır. Kayıt hatasında önceki verilere dönülür.
- Görünüm efektlerinde Ajan saati, ISAC taraması ve Rogue sinyali seçilebilir. OCR performans ekranında medyan/p95 ölçümleri grafikle gösterilir.
- Agent logosu ve uygulama sahneleri Windows paketine dahil edildi; kaynak güncelleyici de bu görselleri alır. Kişisel videolar ve kullanıcı verileri korunur.
- Windows kurulum, paketlenmiş EXE ve güncelleme kontrolleri başarılı olmadan Release yayımlanmaz.

**9.1.3 — Agent logosu ve kütüphane denetimi**

- Kullanıcının onayladığı Agent temalı logo masaüstü pencere/görev çubuğu simgesi ve marka varlığı olarak uygulandı.
- Kütüphane/build denetim raporu eklendi; mevcut 18 build’in attribute referanslarında doğrulanmış eksik bulunmadı.
- Bu sürüm GitHub Release asset’leri üzerinden uygulama içi güncelleme akışından alınabilir.

**9.1.2 — Komuta Merkezi, arama, yedekleme ve görsel yenileme**

- Komuta Merkezi’ne eksik build parçası için görev/hedef loot eşleştirmesi eklendi; hangi görevde hangi eşyanın aranacağı yerel build planı ve mevcut hedef loot önbelleği üzerinden açıklanır.
- Satıcı/hedef loot önbelleğinin yaşı hesaplanabilir hâle getirildi; eski veya çevrimdışı veri canlı veri gibi sunulmaz.
- Evrensel yerel arama motoru eklendi: eşya adı, marka, set, yuva, silah türü, attribute, yetenek ve build adı tek sorguda aranabilir.
- Sandık verisi için doğrulamalı tek adımlı yedekleme/geri yükleme altyapısı eklendi.
- Küçük pencere için mevcut responsive/kompakt menü davranışı korunarak toplu güncelleme kapsamına alındı.
- Yeni sürüm için güncel TD2 Loot Advisor logosu üretildi: `art/branding/td2-loot-advisor-9.1.2.png`.
- Windows kurulum ve paketlenmiş EXE testleri için sürüm 9.1.2 akışı hazırlandı; bu makinede yerel kaynak testleri çalıştırılabilir, GitHub Actions üzerindeki gerçek EXE doğrulaması yayın CI’sinde yapılmalıdır.

**9.1.1 — Toplu kararlılık, Komuta Merkezi ve yerel eşya yönetimi güncellemesi**

- Ekipman → Sandık altında **Komuta Merkezi** görünür hâle getirildi; eksik build parçaları, korumalı eşyalar, kopya grupları, kütüphane adayları ve farm öncelikleri tek ekranda özetlenir.
- Eşyalar için sandık/karakter konumu, koruma kilidi ve uzmanlık durumu yerel olarak tutulur. Kilitli Exotic, Named ve Prototype kayıtları yanlışlıkla söküm/audit sonucuna düşmez.
- Yeni eşya, mevcut sandık kayıtları ve aktif build ile karşılaştırılır; daha iyi veya zaten mevcut bir kopya varsa sonuç ekranında açık uyarı gösterilir.
- Yan yana eşya karşılaştırma görünümü eklendi; son OCR sonucu ile sandıktaki seçili kayıt karşılaştırılabilir.
- Komuta Merkezi artık satıcı/hedef loot verisiyle farm önceliği ve önerilen rotayı birleştirir; mevcut çevrimdışı önbellek korunur.
- Komut/menü etiketlerindeki ham çeviri anahtarları giderildi; Türkçe ve İngilizce Komuta Merkezi adları eklendi.
- Fare izi/ajan sahnesindeki geçersiz Tk widget çağrıları korumaya alındı; küçük pencere ve tema geçişlerinde tekrarlanan native-cursor hataları engellendi.
- `intelligence` ve sandık yönetimi için regresyon testleri eklendi. Kaynak kod açılışı, JSON sözlükleri ve 36 birim test doğrulandı.

**Sınır:** Bu klasör bir Git çalışma ağacı içermediği için bu değişiklikler yerel olarak hazırlanmıştır; GitHub release’i, gerçek depo remote’u bağlandıktan sonra CI iş akışıyla oluşturulmalıdır.

| Dosya | Ne |
|---|---|
| `TD2LootAdvisor_Setup_<sürüm>.exe` | **Kurulum dosyası** (önerilen). Yönetici izni gerekmez; kullanıcı klasörüne kurulur, Başlat menüsü ve masaüstü kısayolu, Programlar'dan kaldırma. |
| `TD2LootAdvisor_<sürüm>_portable.zip` | Kurulumsuz sürüm: bir klasöre çıkar, `TD2LootAdvisor.exe`'yi çalıştır. |
| Source code (zip / tar.gz) | Kaynak kod (Python). |

Windows "kişisel bilgisayarınızı korudu" derse: **Ek bilgi → Yine de çalıştır** (dosya henüz kod imzalı değil).

**9.0.7 — Canlı çeviride özel ad ve zamir doğruluğu**

- The Division 2 hikâyesi ve dünyasındaki karakter, grup, kurum, teknoloji, bölge ve başlık adları çeviride korunur. Doğrulanmış adlar ve kaynakları `meta/proper_names.json` dosyasında tutulur; ekipman ve yetenek adları mevcut oyun kütüphanesinden alınmaya devam eder.
- Zamirler özel ad gibi maskelenmez. Çeviri yönergesi kişi, gönderme, tekil/çoğul anlamı ve cümledeki rolün korunmasını ister; kaynakta doğrulanmış karakter zamirleri bağlam olarak verilir.
- Yerel çeviri motoruna zamir içeren çok cümleli satırlar birlikte gönderilir; önceki cümledeki kişi bilgisinin kaybolma riski azalır.
- Çeviri önbelleği yenilendi; önceki sürümde oluşmuş metinler yeni ad ve bağlam kurallarıyla tekrar çevrilir.
- OCR testinde RapidOCR/ONNX Runtime kurulu değilse zorunlu Tesseract hatası yerine açık bir `SKIP` nedeni gösterilir. RapidOCR kurulu CI ortamında asıl görüntü testi çalışır.

**9.0.6 — Daha kapsamlı oyun kütüphanesi ve doğru eşya tanıma**

- Div2Hub'ın sabitlenmiş CC BY 4.0 veri anlık görüntüsü mevcut kaynaklarla birleştirildi. Katalogda 898 ekipman/eşya kaydı, 379 silah indeksi kaydı, 224 ekipman yeteneği, 181 silah yeteneği, 255 silah modu, 17 ekipman modu, 43 skill varyantı ve 9 Prototype Augment bulunur.
- Health Damage eşleştirmesi artık Health ile çakışmaz. Beş ve daha fazla basamaklı sayılar, aksanlı ad normalizasyonu ve Perfect yetenek adlarının eşleştirilmesi düzeltildi.
- Named/Exotic silahların sabit yetenekleri tarama sonucuna eklenir. Prototype Augment'ler kütüphanede ve build hedeflerinde görünür; eşya puanlaması yeteneği yalnız uyumlu slot/tür ve Prototype eşyalarla karşılaştırır.
- Kütüphane Excel dosyası yetenek ilişkileri, mod uyumluluğu/etkileri ve skill varyantlarıyla yeniden üretildi. Div2Hub lisans/atıf ve senkronizasyon yönergesi eklendi.
- Ansiklopedi, yeni yetenek açıklamalarını kullanır ve her gear set için fiziksel yuva başına tek parça gösterir; kaynaklardaki eş adlar listeyi çoğaltmaz.
- **Kapsam sınırı:** kaynak anlık görüntüsü tam bir Skill Mod kataloğu içermiyor. Doğrulanamayan Skill Mod adları ve değerleri uydurulmadı.

**9.0.5 — Daha düzenli menüler, merkezi kısayollar ve Division 3 haber alanı**

- Ana menüdeki 14 sayfa altı ana grupta toplandı; Ayarlar sayfaları Temel, Tarama, Görünüm ve Hizmetler olarak düzenlendi.
- Eşya tarama, tek seferlik çeviri, canlı çeviriyi durdurma/sürdürme, görev önerisi, sesli asistan ve iptal kısayolları Ayarlar → Temel → Kısayollar alanında birleştirildi. Klavye ile tuş yakalama ve çakışma denetimi eklendi.
- The Division 3 için yeni İstihbarat sayfası eklendi. Ubisoft’un doğrulanmış duyuruları ve kaynakları gösterilir; son resmî haber akışı Division 3 haberlerini buldukça sayfayı günceller. Ubisoft’un açıklamadığı çıkış tarihi veya oynanış bilgisi iddia edilmez.
- Görev eşitleme alanına Ubisoft’un resmî haberleri ve topluluk görev rehberleri için kaynak bağlantıları eklendi. Mevcut görev akışı, Wiki rehberleri ve doğrulanmış topluluk bildirimleri korunur.
- Kaynak ağacı ve varlık klasörleri denetlendi; uygulama/kurulum yolları sabit tutularak proje yerleşimi belgelendi.
- Yayın iş akışına yeni menü yapısını oluşturan Windows widget kontrolü eklendi.

**9.0.4 — Oyun içi sesli AI asistanı ve çeviri kontrolü**

- **F6: çeviriyi durdur / devam et.** Canlı ekran ve konuşma çevirisi tek tuşla durdurulup önceki kaynaklarla yeniden başlatılır. Durdurma, kısayol dinleyicisini kapatmaz. Eski kaynak ve gecikmiş ekran yakalama işleri iptal sonrasında kaplamayı yeniden açamaz.
- **F9: oyun içinden soru sor.** İlk basış mikrofonu açar; tekrar basış kaydı gönderir. En fazla 20 saniye kayıt alınır. Yerel çok dilli Whisper soruyu metne çevirir; seçili sağlayıcı yanıtlar ve yanıt sesli okunur. Genel sohbet seslendirmesi kapalı olsa da sesli sorunun yanıtı okunur.
- **F12: isteği ve sesi iptal et.** Eski soru/yanıt çıktıları sonradan uygulanmaz. Kullanıcı konuşurken programın kendi çeviri ve eşya sesleri bekler. Daha önce gönderilmiş bulut isteği geri alınmayabilir.
- **Asistan sekmesi yenilendi.** Kısayol açıklamaları, konuşma modelini hazırlama düğmesi, sağlayıcı/veri aktarımı açıklamaları ve oyun üstü durum/yanıt penceresi eklendi. AI sağlayıcısı ayrıca yapılandırılmalıdır; yerleşik yardımcı sınırlı kurallarla çalışır.
- **Tarama bağımsız kısayollar.** F6/F7/F9/F12 uygulama açıkken eşya taraması durdurulmuş olsa da çalışır. Boş veya çakışan atamalar reddedilir. F7 tek seferlik çeviri, F8 eşya taraması, F10 görev getirme işlevlerini korur.
- **Paketlenmiş konuşma altyapısı.** Mikrofon ve yerel Whisper çalışma zamanı pakette; model ilk hazırlamada indirilir. Yeni ayarlarda base/CPU/int8, iki CPU iş parçacığı; mevcut model ve sağlayıcı seçimi korunur. Boştaki konuşma modeli bellekten bırakılabilir. PyAV uyumluluğu sabitlendi.
- **Veri aktarımı açık.** Mikrofon sesi yerelde metne dönüşür. Soru ve build/eşya bağlamı seçili AI sağlayıcısına gider; çevrimiçi doğal ses açıksa yanıt metni Microsoft ses hizmetine de gönderilir. Sağlayıcı hatasında yerleşik yardımcıya dönülmesi sesli olarak açıklanır.
- **Yayın öncesi kontroller.** Kısayol, kayıt, iptal, eski zamanlayıcı/yanıt korumaları ve yerel HTTP sağlayıcı akışı test edilir; kurulan EXE'de asistan çalışma zamanı ve gerçek Türkçe ses tanıma ayrıca sınanır. Gerçek oyun + kullanıcı mikrofonu + bulut hesabıyla uçtan uca kullanım henüz doğrulanmadı.

**6.0.3 — Daha hızlı eşya okuma, yerinde çeviri ve doğal ses**

- **Daha çabuk otomatik algılama:** hafif görüntü kontrolü OCR bekleme aralığından ayrıldı. Dengeli profilde 200 ms, Oyun öncelikli profilde 300 ms kontrol yapılır; ağır OCR işlemlerinin hız sınırı korunur. OCR meşgulse eski yakalama sırada beklemez.
- **Seçili kart bölgesinde daha az OCR:** dar bir kart bölgesi seçildiğinde doğrudan okunur; geçerli sonuçta konum bulmak için ek OCR yapılmaz. Eksik sonuçta mevcut arama yoluna dönülür. Kazanç seçilen bölgeye ve karta bağlıdır; oyun içi genel hızlanma yüzdesi iddiası yoktur.
- **Yerinde çeviri konumları:** ayrı satırlar büyük bir paragraf kutusunda birleştirilmez. Kutular komşu yazıları aşağı kaydırmaz. Ölçüm ve çizim aynı fontla yapılır; uzun adlar bölünebilir. Çok dar alanda üç nokta kullanılır, tam çeviri geçmişte kalır.
- **Eski çeviriler temizlenir:** aynı metin başka yere taşınırsa kaplama yeniden konumlanır; boş ekran okumasında önceki kutular kaldırılır.
- **İki doğal bildirim paketi:** Türkçe Emel Neural ve İngilizce Aria Neural. Toplam 20 hazır kayıt çevrimdışı çalar ve telsiz bozulması uygulanmaz. Hazır kayıtlarda değişken build adı/yüzdesi yerine genel bildirim kullanılır; tam değerler ekranda kalır.
- **İsteğe bağlı çevrimiçi doğal ses:** Asistan ve Canlı Çeviri sekmelerinden açılır. Okunacak metin Microsoft Edge ses hizmetine gönderilir; ses yerelde sınırlı önbelleğe alınır. Yeni ayarlarda kapalıdır. Kapalıyken veya hizmet çalışmazsa değişken metin Windows sesiyle okunur. Hazır bildirimler çevrimdışı kalır.
- **Doğrulama ve paketleme:** yerleşim, konum değişikliği, ses önbelleği, çevrimdışı davranış ve hata dönüşleri için testler eklendi. Kurulan EXE'de 20 ses kaydı ve çevrimiçi ses bağımlılıkları ayrıca denetlenir. Gerçek oyunda tüm ekran düzenleri ve 8 GB bilgisayarda performans henüz doğrulanmadı.

**6.0.2 — OCR, çeviri ve performans kararlılığı**

- **Ortak eşya koruması:** eksik/geçersiz OCR incelemeye yönlendirilir. Exotic, Named ve Prototype eşyalar değerlendirme, ilerleme takibi ve depo denetiminde KIR sonucuna düşmez.
- **Dengeli / Oyun öncelikli:** başlıktan tek tıkla profil değiştirilebilir. Oyun öncelikli profil otomatik OCR denemelerini ve tarama sıklığını azaltır; elle tarama ayarlarını korur. GPU sağlayıcısı otomatik değiştirilmez.
- **Sınırlı iş kuyrukları:** çeviride eski isteklerin sonuçları uygulanmaz; bekleyen işler birikmez. OCR modelinin ısınmasıyla taraması aynı anda çalışmaz. Yavaş yerel API istemcileri yayını bekletmez.
- **Çeviri doğrulaması:** sayıların ve oyun terimlerinin korunması denetlenir; eksik/bozuk çıktı önbelleğe alınmaz. Başarısız çeviri aynı ekran için tekrar denenebilir.
- **Yerel çeviri ve açık veri aktarımı:** yeni ayarlarda yerel çeviri varsayılandır. Çevrimiçi AI seçiminde veri aktarımı açıklanır. Çeviri metni günlüğü ve OCR görüntüsü kaydı yeni ayarlarda kapalıdır; mevcut kullanıcı ayarları korunur.
- **Daha kontrollü kaynak kullanımı:** oyun öndeyken veya pencere küçültülmüşken arka plan animasyonları bekler; görsel önbellekler sınırlıdır. Ölçüm düğmesi son işlem sürelerini ve kuyruk durumunu gösterir.
- **Kaynak sürümünü başlatma:** normal açılışta gereksiz pip çalıştırılmaz. `--check`, `--repair` ve `--extras` seçenekleri eklendi.
- **Doğrulama:** yerel çalıştırmada 18 test grubu geçti. İki gerçek kartın dört çözünürlükteki sekiz OCR kontrolü geçti. Gerçek 8 GB bilgisayarda ve oyun açıkken FPS/GPU etkisi henüz ölçülmedi; yüzde hızlanma iddiası yoktur.

**6.0.1 — Sürüm sayacı**

- Program topluluk görev listesini indirirken artık kendi sürüm numarasını da bildirir (açılıştaki ilk istekte ayrıca "açılış" işareti). Sunucu bunları yalnız günlük toplam olarak tutar: hangi sürüm kaç kez açıldı. Kimlik, IP, hesap ya da cihaz bilgisi gönderilmez ve saklanmaz; tek tek kullanıcılar ayırt edilemez. Böylece eski sürümlerin ne zaman bırakılabileceği görülebilir. Ayarlar'da topluluk görevleri kapatılırsa sayaç da kapanır.

**6.0.0 — Nihai sürüm: güvenlik, kararlılık ve uyumluluk**

Bu sürüm yeni özellikten çok sağlamlık içindir: programın tamamı güvenlik, veri sızıntısı, eşzamanlılık, donanım uyumu ve performans açısından gözden geçirildi.

- **Güvenli güncelleme:** otomatik güncelleme artık yalnız bu projenin GitHub sürümünden gelen, adı ve SHA-256 özeti doğrulanan kurulum dosyasını kurar; özet bulunamazsa **kurmaz** (önceden doğrulamasız devam edebiliyordu). İndirilen dosya her seferinde yalnız sana ait yeni bir geçici klasöre iner.
- **Gizli ayarlar şifreli:** yapay zekâ API anahtarları, Discord webhook'u, ntfy konusu, lisans anahtarı ve yerel bağlantı belirteçleri diskte Windows'un kullanıcıya bağlı şifrelemesiyle (DPAPI) saklanır. builds.json'u biriyle paylaşsan bile bu bilgiler okunamaz. (Başka bir bilgisayara taşırsan anahtarları bir kez yeniden girmen gerekir.)
- **Ayarlar ve build'ler artık bozulmaz:** kayıtlar önce geçici dosyaya yazılıp tek adımda değiştirilir; aynı anda birden çok yerden kaydedilse ya da program kayıt sırasında kapansa bile dosya sağlam kalır. Günlük yedek (.bak) tutulur; dosya bir şekilde bozulursa program build'lerini yedekten geri yükler. Sandık ve ilerleme dosyaları için de aynısı.
- **Veri sızıntısına karşı:**
  - Geri bildirim raporlarında temizlenenler genişletildi: API anahtarları, Discord webhook'ları, lisans / davet kodları, yerel bağlantı belirteçleri, ev ağı IP adresleri, kullanıcı klasörü yolları, e-postalar (hem programda hem sunucuda).
  - Ubisoft Connect / Steam / Discord bildirimleri (arkadaş adları içerir) canlı çeviriye, görev paylaşımına ve çeviri günlüğüne hiç girmez.
  - Düzeltme önerileri gönderilmeden önce aynı temizlikten geçer.
  - Rapor Paneli de GitHub ve yönetici belirteçlerini diskte şifreli saklar.
- **Yerel sunucular (OBS/Stream Deck, telefon ekranı, telefon arkadaşı):** yarım bırakılan bağlantılar 15 sn'de kapanır (ev ağından gelen yüzlerce boş bağlantı programı kilitleyemez); başka bir program aynı portu ele geçiremez; topluluk sunucusu çok büyük istekleri reddeder.
- **Türkçe kullanıcı adları:** Windows kullanıcı klasöründe ş, ğ, ı, ü gibi harfler varsa (C:\Users\Şükrü) çeviri ve konuşma modelleri yüklenemeyebiliyordu; artık güvenli bir yoldan açılıyor.
- **Daha az bellek:** canlı çeviri 10 dakika kullanılmazsa çeviri modeli bellekten çıkarılır (~300 MB geri verilir), gerekince saniyeler içinde yeniden yüklenir.
- **Özel tam ekran uyarısı:** oyun özel tam ekrandayken canlı çeviri açılırsa program bunu oyunun ayar dosyasından anlar ve kenarlıksız moda geçmeni ya da telefon / ikinci ekranı kullanmanı söyler.
- Diğer: Windows konuşma tanıma komutu tam yolla ve güvenli kaçışla çalışır; model arşivlerinde her türlü yol kaçışı (.., sürücü harfi, ters eğik çizgi) reddedilir.

**5.1.9 — 🌐 Çeviri artık oyunun bir parçası: yerinde çeviri, konuşma çevirisi, telefon ekranı ve tema paketleri**
- **📍 Yerinde çeviri (yeni mod):** Türkçe metin İngilizce yazının **tam üstünde, kendi yerinde** görünür — harita, envanter, menüler. Her yazının altına oyunun panel rengine yakın **opak bir fon** konur, iki yazı üst üste binmez. Türkçe uzunsa önce yazı küçülür, yine sığmazsa kutu aşağı uzar. Menü satırları tek tek, paragraflar blok olarak çevrilir. Aynı kalan adlar (Exotic Cache…) örtülmez.
- **🎧 Konuşma çevirisi (altyazısız sesler):**
  - **Windows 11:** Windows'un Canlı Altyazı özelliği oyunun sesini yazıya döker, program çevirip altyazı olarak gösterir. Ek indirme yok, yük çok düşük.
  - **Windows 10 (ve 11):** isteğe bağlı yerel **Whisper** modeli (~146 MB, bir kez). Programdaki çeviri altyapısıyla çalışır; yalnız konuşma algılanınca devreye girer. Oyun adları düzeltilir (Capitol, Black Tusk, ISAC…).
  - En kararlısı hâlâ oyunda altyazıyı açıp "Altyazılar" modunu kullanmak.
- **📱 Telefon / ikinci ekran:** çeviriler aynı ağdaki telefonda ya da ikinci monitörde bir sayfada akar — **oyun özel tam ekranda olsa bile.** QR kodla aç; yazı boyutu, İngilizce aç/kapa, telefonda sesli okuma, ekran açık kalır. Yalnız yazı gönderilir, yük yok denecek kadar az. Ücretsiz.
- **🔊 Sesli okuma:** çeviriler ajan sesi paketiyle (telsiz efekti dahil) okunur — kapalı / yalnız altyazılar / her çeviri.
- **📖 Terim açıklamaları:** çeviride geçen oyun terimleri (egzotik, adlı eşya, set, marka, yetenek ve Exotic Cache, Dark Zone, SHD gibi genel terimler) çeviri geçmişinde ve telefon sayfasında işaretli; dokununca kısa açıklama, tek tıkla Ansiklopedi.
- **✍️ Topluluk düzeltme önerisi:** çeviri geçmişinde her satırın yanında "Daha iyi çeviri öner". Öneriler onaylanınca herkesin canlı çevirisinde o satır düzeltilmiş hâliyle görünür.
- **⚡ Hızlı OCR:** Windows'un kendi OCR'ı da kullanılabiliyor (Windows 10 ve 11, işlemcide, ekran kartını oyuna bırakır). Program ilk çeviride ikisini ölçüp bilgisayarına hafif geleni seçer.
- **🎮 Kumanda tuşu:** "Şimdi çevir" bir kumanda bileşimine atanabilir (varsayılan Back + RB). Kumanda yalnız okunur, oyuna hiçbir şey gönderilmez.
- **🎨 Oyun atmosferinde tema paketleri:** SHD Turuncu, **Dark Zone, Black Tusk, Hunter, Kış New York, Gece Operasyonu, Kenly.** Ayarlar'da renk kartlarından tek tıkla; arayüz, çeviri kutuları ve telefon sayfası birlikte değişir.
- Çeviri kutularında yazı tipi seçimi (okunaklı yazı tipleri dahil) ve kenar çizgisi; çeviri geçmişinde arama ve CSV dışa aktarma.

**5.1.8 — 👥 Topluluk görevleri: canlı çeviri ile görevler birbirine bağlandı**
- **Oyuncular görevleri birlikte topluyor.** Canlı çeviri açıkken haritada bir görev paneline (Projeler, Ödül avları, Görevlendirmeler) bakınca program görevi tanır: başlık, alt başlık, açıklama, hedef ve sayaç, ödüller, günlük / haftalık / sezon ve bitiş zamanı. İzin verdiysen görevin **yalnız yazısı** ve Türkçe çevirisi topluluk listesine gönderilir. Oyuncu adı, ekran görüntüsü ya da bilgisayar bilgisi gönderilmez. İzin canlı çeviriyi ilk açtığında bir kez sorulur, Canlı çeviri sekmesinden her zaman değiştirilebilir.
- **Uydurma göreve karşı:** bir görev ancak **en az 2 farklı oyuncudan** aynı şekilde gelince herkese açılır; Türkçesi de en az 2 oyuncudan aynı gelmeli. Süresi dolan günlük ve haftalık görevler listeden kendiliğinden düşer.
- **Herkes faydalanıyor:**
  - **Görevler sekmesi:** oyunculardan toplanan güncel görevler 👥 işaretiyle, Türkçesi, açıklaması ve ödülleriyle listeleniyor. Liste açılışta ve 30 dakikada bir yenilenir.
  - **Canlı çeviri:** ekrandaki görev listede varsa çeviri modeli hiç çalışmadan **anında ve doğrulanmış Türkçesiyle** gösterilir. Çeviri ne kadar çok kullanılırsa o kadar hızlı ve tutarlı oluyor.
- **Tam ekran çevirisinde yan yana paneller artık karışmıyor:** OCR sütunları ayırıyor; harita gibi çok sütunlu ekranlarda soldaki panelin yazısı sağdaki kartların yazısıyla aynı satıra birleşmiyor.

**5.1.7 — ⚡ Performans ve daha iyi çeviri**
- **Program artık tek kopya çalışır.** Masaüstü kısayoluna ya da Başlat menüsüne ikinci kez tıklamak yeni bir kopya açmıyor; açık olan pencere (tarama sırasında küçültülmüş olsa, oyun tam ekranda olsa bile) öne geliyor. Önceden her tıklama arka planda yeni bir kopya başlatıyordu; kopyaların hepsi ekranı okuyup ekran kartını ve işlemciyi birlikte yoruyordu ve F7 kısayolunu birbirinden kapıyordu.
- **Oyun sırasında daha az yük:**
  - Ekranda eşya kartı yokken (sahada, haritada, başka menülerde) ekranın tamamı artık tam çözünürlükte okunmuyor ve diske resim yazılmıyor; kart aramasının küçük ön okuması yeterli. Kartsız ekranlarda okuma başına iş yaklaşık yarıya iniyor.
  - Sahadayken kart çıkmadıkça okuma aralığı kendiliğinden uzar (4 → 8 → 16 → 30 sn); envanter ya da bir menü açılınca hemen eski hızına döner.
  - Oyun penceresi ve monitör bilgisi önbellekten okunuyor (önceden saniyede birkaç kez tüm pencereler taranıyordu).
  - Oyun açıkken programın işlemci önceliği "normalin altı" olur, oyun kare hızı önce gelir; oyun kapanınca normale döner.
  - Yerel çeviri modeli işlemci çekirdeklerinin en fazla yarısını kullanır.
- **Canlı çeviri daha doğru:**
  - Başlıklar ve listeler ayrı satırda: "Objective / Rewards" gibi başlıklar metne yapışmıyor ve **Hedef / Ödüller** olarak gösteriliyor; ödül listesi satır satır.
  - İlerleme sayaçları (00/01) cümlenin ortasına girmiyor, sona ekleniyor.
  - Ödül sandıkları oyundaki adlarıyla kalıyor (Exotic Cache, Recalibration Cache…); "önbellek" gibi yanlış çeviriler yok.
  - "Misyon" yerine oyundaki **görev**, "Legendary zorluğu üzerinde" yerine **Legendary zorlukta**.
  - Simgelerden okunan tek harfler (ör. "X") ayıklanıyor.
  - Her çeviri `logs\live_translate.log` dosyasına da yazılıyor (İngilizcesi ve Türkçesiyle), çeviri kutusunu kaçırırsan sonradan bakabilirsin.
- Yerel API (OBS/Stream Deck) Windows'ta aynı portu iki kez açamaz; çakışma artık görünür bir hata veriyor.

**5.1.6 — 🌐 Canlı oyun çevirisi ve canlı haber akışı**
- **Yeni sekme: 🌐 Canlı çeviri (İngilizce → Türkçe).** Program ekrandaki İngilizce yazıyı eşya kartı okur gibi okur ve Türkçe çevirisini oyunun üstünde gösterir: altyazılar ve telsiz konuşmaları, istihbarat ve görev metinleri, menüler.
  - **Ne çevrilsin:** Altyazılar (oyun penceresinin alt kısmı), Seçili alan (bir kez seçersin) ya da Tüm oyun penceresi (yan panelde).
  - **Yazı değişince kendiliğinden çevirir**; ayrıca **F7** ile anında çeviri. Yazı boyutu, saydamlık ve gizlenme süresi ayarlanabilir.
  - **Motorlar:** *Yerel sinir ağı modeli* — OPUS-MT (Helsinki-NLP, CC-BY 4.0), bilgisayarında internetsiz ve ücretsiz çalışır, cümle başına ~0,1–0,3 sn; bir kerelik ~210 MB indirme. *Gelişmiş yapay zekâ* — Asistan'da seçtiğin Claude / OpenAI / Ollama ile, oyun bağlamını bilerek.
  - Oyun içi adlar (Black Tusk, Eagle Bearer, Striker's Battlegear, Dark Zone…) çevrilmez, Türkçe eklerle korunur ("Black Tusk'ı").
  - Yalnız ekran okunur; oyuna dokunulmaz. Kaplamanın görünmesi için oyunu kenarlıksız ya da pencere modunda oyna.
- **Canlı haber akışı:** program açıkken 30 dakikada bir yeni haber var mı diye bakar, sayfayı yeniden başlatmadan günceller; Bilgi sekmesinde okunmamış haber sayısı (●3) görünür. Yeni sezon, bakım, yeni içerik ve etkinliklerde tepside bildirim; telefon bildirimlerinde yeni "Haberler ve etkinlikler" seçeneği. Haber akışı artık günde 4 kez güncelleniyor.
- **Ansiklopedi açıklamaları Türkçe:** 300 açıklamanın Türkçesi eklendi (ilk sürüm makine çevirisi; günlük görev gözden geçirip diğer dilleri de ekleyecek). Altında İngilizce özgün metin de görünür.
- **Programa eklenen diğer diller için:** Asistan'da bir yapay zekâ seçiliyse haberler ve açıklamalar o dile bilgisayarında çevrilip saklanır.

**5.1.5 — 📚 Bilgi sekmesi ve ajan sesi**
- **Yeni sekme: 📚 Bilgi.** Dört bölüm:
  - **Ansiklopedi:** 80 egzotik, 170 adlı eşya, 29 gear set, 39 marka ve 240'tan fazla yetenek tek yerde, aranabilir. Set bonusları, parçalar, yetenek açıklamaları ve ilgili girişler; tek tıkla **build'e ekle** (gear set/marka → yeni build, egzotik/yetenek → etkin build). Premium: "Nerede düşer?" topluluk istatistiğinden.
  - **Meta build vitrini:** günlük güncellenen popüler build'ler kartlar halinde — PvE/PvP/solo/grup/son oyun ve rol etiketleri, popülerlik çubuğu, ▲ yükselişte / ▼ düşüşte / ✦ yeni işaretleri, favoriler, "build'lerimde göster / gizle", kaynak bağlantıları.
  - **Haberler ve sezon:** günlük ve haftalık sıfırlamaya geri sayım, açık görev sayısı, canlı / yakında etkinlikler ve yama notları (kalan süreyle, kaynak bağlantılı, 10 dilde). Her gün otomatik güncellenir.
  - **Bilgi yarışması:** oyun kütüphanesinden üretilen sorular (egzotiğin yuvası, marka bonusu, set yeteneği, silah türü, yetenek açıklaması…), XP, seviye ve seri. İsteğe bağlı olarak yükleme ekranlarında küçük bir soru penceresi.
- **Ajan sesi:** kararlar artık özgün "taktik asistan" cümleleriyle söyleniyor ("Egzotik tespit edildi. Saklaman önerilir."). Üç paket (Taktik asistan, Sakin operatör, Kısa ve net) + Klasik, 10 dilde; isteğe bağlı **telsiz efekti**. Asistan → ayarlar → Ses paketi.

**5.1.4 — güncelleme düzeltmesi**
- Otomatik güncellemede program artık sistem tepsisine küçülmüyor, tamamen kapanıyor; kurulum dosyaları değiştirip programı yeniden açabiliyor. Kurulum da başlamadan önce tepside açık kalmış bir programı kapatıyor (kaldırırken de).

**5.1.3 — düzeltme**
- Discord ile giriş yapınca (ya da premium açılıp kapanınca) program kendiliğinden yeniden başlıyor ve aynı sekmeye, hesap penceresiyle dönüyor. Önceden girişten sonra menüler ve pencere boyutu bozuk kalabiliyordu; kapatıp açmak gerekmiyor.

**5.1.2 — hesap, oyunla entegre hizmet**
- **Yeni: isteğe bağlı hesap — Discord ile giriş.** Program girişsiz de tamamen ücretsiz çalışır. Hesap; premium anahtarını, davet / hediye kodunu ya da satın alımı bilgisayarına bağlar. Şifre yok: kim olduğunu Discord doğrular, oturum bilgisayarında Windows'un kendi şifrelemesiyle (DPAPI) saklanır. İlk açılışta karşılama penceresi çıkar ("Girişsiz devam et" ile geçilebilir); üst banttaki **👤 Giriş yap** her zaman orada.
- **Kod kullan:** `TD2K-…` lisans anahtarı, `TD2I-…` davet kodu ya da satın alma anahtarı tek kutuya yazılır. Bir lisans bir bilgisayarda çalışır; premium 7 gün internetsiz geçerlidir ve kendiliğinden yenilenir. Eski `TD2P-` anahtarlar çalışmaya devam eder.
- **Yeni: 🛰 Hizmet (Ayarlar).** Oyun açılınca tarama kendiliğinden başlar, kapanınca durur; oturum özeti (okunan, saklanan, kırılan, egzotik) kaydedilir. Sistem tepsisi simgesi, "pencereyi kapatınca tepside kalsın", **Windows ile başlat**.
- **Akıllı tarama:** program menü / sahada / yükleme ekranlarını tanır; sahadayken ve yükleme ekranında boşuna okuma yapmaz. Sabit metin aramaz — bir kart her başarıyla okunduğunda o ekranı kendisi öğrenir, her dilde ve çözünürlükte çalışır. Üst bantta oyunun durumu görünür (🎮 Menüde).
- **Discord durumu:** isteğe bağlı olarak Discord'da "TD2 Loot Advisor — Envanteri düzenliyor · 23 eşya · 2 egzotik" gösterir (bilgisayardaki Discord uygulamasıyla; sunucumuza bir şey gitmez).
- **Premium — yerel API:** OBS için şeffaf canlı karar kartı (Tarayıcı Kaynağı), Stream Deck düğmeleri (başlat / durdur / tara) ve WebSocket. Varsayılan yalnız bu bilgisayar; her adres gizli bir anahtar içerir.
- **Premium — telefon bildirimleri:** egzotik / adlı "SAKLA", build yükseltmesi, satıcı eşleşmesi ve oturum özeti telefona gelir — ücretsiz **ntfy** uygulaması (QR ile abone ol) ya da kendi Discord sunucuna webhook.
- Hiçbiri oyunun belleğine, dosyalarına ya da ağ trafiğine dokunmaz; oyun yalnız pencere adından tanınır, durum yalnız ekrandan okunur.

**5.1.0 — ekran kartıyla okuma**
- **Yeni: ekran kartıyla OCR (DirectML).** Kart okuma artık ekran kartında çalışabiliyor (DirectX 12 destekleyen her ekran kartı: NVIDIA, AMD, Intel). İlk açılışta program bunu ayrı bir süreçte güvenle dener: sonuç işlemciyle aynıysa ve daha hızlıysa açar, değilse işlemcide kalır. Sürücü sorunu olsa bile program etkilenmez.
- Ayarlar → OCR'da yeni satır: **Ekran kartıyla hızlandır** (Otomatik / Açık / Kapalı) ve bu bilgisayardaki ölçüm ("işlemci 1350 ms → ekran kartı 400 ms" gibi).
- **Ondalık onarımı:** OCR noktayı kaçırdığında ("+60%" Kritik Şans) değer atılmıyor, oyunun sınırlarına göre onarılıyor (6.0%). Onarılan değerler "şüpheli" sayılır ve kart bir kez daha okunur.

**5.0.9 — hız**
- **Eşya tanıma 2–15 kat hızlı:** okunan yazıyı eşya kütüphanesiyle eşleştirme, ilk okumada yaklaşık 2 kat, aynı taramadaki tekrarlarda 13–15 kat hızlandı (Windows ölçümü: kart başına 360–630 ms → 27–47 ms). Sonuçlar eskisiyle birebir aynı (200.000 karşılaştırmada fark yok).
- **Gereksiz okumalar kaldırıldı:** hızlı bilgisayarlarda her kart 3 kez okunuyordu. İlk okuma eşyayı tam güvenle tanıdıysa ve rakamlar net okunduysa ek okuma yapılmıyor; kart başına 1,5–4,5 sn tasarruf. Kaydırılmış/eksik kartlarda eskisi gibi çoklu okuma yapılır.
- **Otomatik taramada daha az işlemci:** "ekran değişti mi?" denetimi tam görüntü üretmeden ham piksellerden yapılıyor ve yakalayıcı her seferinde yeniden açılmıyor (3440×1440'ta tur başına 64 ms → 8 ms; 1024×768'de 32 → 16 ms).
- Son okunan kartın görüntüsü diske arka planda yazılıyor (tarama beklemiyor).
- Açılış: yedek OCR motoru (Tesseract) yalnız kuruluysa yükleniyor, RapidOCR'ın varlığı yüklenmeden denetleniyor — özellikle bilgisayar yeni açıldığında daha hızlı başlangıç.

**5.0.8 — gerçekçi 3D ajanlar**
- **Eksik Parçalar sekmesindeki 3D ajan yenilendi:** beş özgün, gerçekçi ajan — Operatör, Keşifçi, Ağır Zırh, Şehir, Kutup. Her biri stüdyo ışığında render edilmiş 360° görüntülerden oluşuyor; fareyle sürükleyince döner, ◀ ▶ ile ajan değişir, seçimin kaydedilir.
- Eksik parçalar ajanın üzerinde kırmızı nabız gibi parlar, sahip olunanlar yeşil görünür; bir parçaya tıklayınca o yuva seçilir. Yuva adları ajanın iki yanında hizalı durur.
- Tasarımların tamamı özgündür (oyundan hiçbir model ya da doku kullanılmaz); insan bedeni MakeHuman'ın serbest (CC0) temel modelinden.
- Gerçekçi görüntüler bulunamazsa önceki çizim tabanlı ajan (5 model, kıyafet renkleri, ten seçimi) kullanılır.

**5.0.7 — hata bildirme ve istek menüsü**
- **Yeni: 🐞 Geri bildirim** (üst bant ve Yardım sekmesi). Hata, istek ya da soru doğrudan geliştiriciye gönderilir; GitHub hesabı gerekmez. İsteğe bağlı olarak sistem bilgisi, program kaydının son satırları ve son okunan eşya kartı eklenebilir; **Önizle** ile tam olarak ne gideceği görülür.
- Göndermeden önce kişisel bilgiler silinir: dosya yollarındaki Windows kullanıcı adı, lisans anahtarı, e-posta adresleri.
- **Raporlarım** sekmesi: gönderdiğin raporların durumu (Yeni, İncelendi, Üzerinde çalışılıyor, Tamamlandı…) ve geliştiricinin yanıtı burada görünür.
- İnternet yoksa rapor saklanır ve bağlantı gelince kendiliğinden gönderilir.
- "Yanlış okundu" düğmesi artık bu pencereyi kartın bilgileriyle doldurulmuş olarak açıyor.

**5.0.6 — menü geçişi ve kaydırılmış kartlar**
- Menü geçiş efekti yenilendi: seçili sekmenin altında kalıcı turuncu bir gösterge; sekme değişince eski sekmeden yenisine ~0,25 sn'de akıcı biçimde kayar. Sekmenin verisi animasyon bittikten sonra yenilendiği için geçiş takılmaz (eskiden pencere karartılıp açılıyor, arka plan saatiyle çakışıp titriyordu).
- Kart aşağı kaydırılınca eşyanın adı görünmüyordu: ad ve set/marka artık envanter listesindeki seçili (vurgulu) satırdan okunuyor (ör. "Striker's Pack · Striker's Battlegear"). Kaydırılan kart başka bir eşyayla birleştirilmiyor.
- Kartın başlığı ekranın en üstündeyse (uzun set açıklamasında) artık kırpılmıyor.
- Harita, projeler gibi eşya kartı olmayan ekranlardaki yazılar artık eşya sanılmıyor.

**5.0.5 — akıcılık ve fare düzeltmeleri**
- Menülere ve düğmelere tıklamak bazen algılanmıyordu (arka plandaki ajan saati görünsün diye şeffaf yapılan zemine düşen tıklamalar arka plana gidiyordu): artık bu tıklamalar programa iletiliyor; kaydırma ve sağ tıklama da.
- Pencere boşluklarında imleç Windows'un beyaz okuna dönüyordu: artık her yerde programın imleci.
- Kasma azaltıldı: arka plan saati şekilleri yeniden kullanıyor, program arka plandayken / fare hareketsizken yavaş çiziliyor, pencere sırası her karede değil saniyede bir eşitleniyor, fare izi hafifletildi.
- Oyun güncellemesi algılama: oyunun exe'si her yamada aynı sürüm numarasını (1.0.0.0) taşıdığı için yama artık dosyanın tarihi ve boyutundan da algılanıyor.

**5.0.4 — her bilgisayarda oyunla senkron**
- **Yeni: her açılışta güncelleme denetimi.** Program sürümü, eşya kütüphanesi ve oyunun kendi sürümü her açılışta denetlenir. Yenilik varsa tek pencerede gösterilir (ör. "Kütüphane: 3 yeni eşya — Fafnir, Iron Will …", "The Division 2 güncellendi 1.41 → 1.42"); seçilenler tek tıkla yüklenir, reddedilirse bir sonraki açılışta yine sorulur. Oyun bir yamayla güncellendiğinde program bunu fark edip yeni eşyaların kütüphanesini denetler (oyun yamasının kendisini Ubisoft Connect / Steam yükler).
- **Yeni: PC ve oyun senkronizasyon aracı** (üst banttaki 🔄 *PC senkron* düğmesi ya da Ayarlar → Ekran ve oyun). Bilgisayarı (monitörler, Windows ölçeklendirmesi, işlemci, bellek, ekran kartı) ve oyunun ayarlarını tarar, bu PC'de bir eşya kartını okuma hızını ve doğruluğunu ölçer, programın ayarlarını bu PC'ye göre kurar ve bir rapor gösterir (HDR açık, özel tam ekran gibi oyun ayarı önerileriyle). Program yeni bir bilgisayarda, monitör düzeni ya da oyun çözünürlüğü değiştiğinde açılırsa senkronizasyonu kendisi önerir. Oyunun dosyalarına ve belleğine dokunulmaz.
- Program artık ana monitörü değil, oyunun penceresini okuyor: oyun hangi monitörde, hangi modda (tam ekran / kenarlıksız / pencere) ve boyutta olursa olsun yalnız oyunun alanı okunur. Pencerenin yeri Windows'tan sorulur; oyunun belleğine dokunulmaz.
- Okuma ayarları oyunun gerçek boyutundan hesaplanır: hazır listede olmayan her çözünürlük ve en-boy oranı (1680×1050, 2560×1600, dizüstü ekranlar …) desteklenir. Oyunun boyutu değişince program kendini uyarlar.
- Başka bilgisayardan kalmış ya da monitöre uymayan profil ve sabit okuma eşiği artık okumayı bozmaz: otomatiğe dönülür.
- Okuma sayısı bilgisayarın hızına göre ayarlanır (Ayarlar → OCR → Geçiş: otomatik): yavaş işlemcide kararlar gecikmez.
- Kalibrasyon ve görev bölgesi seçimi oyunun bulunduğu monitörde yapılır.

**5.0.3 — kendi kendine öğrenen eşya kütüphanesi**
- Program artık kendi uyarı penceresini okumuyor (önceki kararın yazıları yeni kartın adını kapatıyordu).
- Öğrenen kütüphane: kütüphanede olmayan marka / gear set / parça adı bir kez okununca kaydedilir (`learned_library.json`) ve hep tanınır. Örn. "Unmatched Backpack → Sırt çantası, Unit Alloys".
- "Brand Set / Gear Set" satırından marka ve set her zaman okunur; zırh kartları artık silah sanılmıyor.
- Tam eşya kütüphanesi: 39 markanın ve 29 gear set'in tüm parça adları (Unmatched Backpack, Umbra Plate Carrier, Burdenless Pack …) — ekipman kaydı 92 → 521. Silah varyantları (Black Market, Classic, Replica …) artık doğru adıyla tanınıyor.
- Son sezonların eşyaları: Red Horizon (Fafnir, Iron Will, Loaded for Bear, Ember Engine, Trick Shot, Rushdown, Melon Baller, Keeper, Teapot, Steamer), Into the Dark ve Rise Up (Caduceus, Underboss, Nurse's Kneepads, Agitator, Investor, Whiplash, Interchange, Insult to Injury …), yeni talent'ler.
- Kütüphane düzeltmeleri: ilk oyuna (TD1) ait 14 exotic çıkarıldı; Fafnir (pompalı), Whiplash (tabanca), Bulldog (holster), Royal Works bonusları düzeltildi. Aynı adı taşıyan ekipman ve silah ("Robin") karttan ayırt edilir.
- Tüm kütüphane Excel'de: `meta/TD2_Kutuphane.xlsx` (markalar, setler, exotic, named, silahlar, talent'ler, modlar, sezon yenilikleri). Excel'deki düzeltmeler `scripts/import_library_excel.py` ile programa işlenir.
- M16A2 / LVOA-C gibi tüfekler artık sniper build'leriyle eşleşmiyor.

**5.0.2 — kararlılık düzeltmeleri**
- Set parçaları yanlış yuvaya yazılıyordu (dizlik / holster / sırt çantası "eldiven" görünüyordu): düzeltildi.
- Kaydırılmış kart birleştirme artık farklı eşyaları (ör. maske + silah, eldiven + dizlik) birleştirmiyor.
- Skill build'leri "Assault Turret" yüzünden tüfeklerle eşleşiyordu: düzeltildi.
- Tanı için son 200 kart okuması `logs/ocr_history/` altında tutulur (yalnız kart metni).

**Öne çıkanlar:** yeni OCR motoru (RapidOCR; 480p'ye kadar doğru okuma, Tesseract gerekmez) · Sandık: envanter, build optimize edici,
denetim raporu, satıcı eşleştirme · telefon arkadaşı · build paylaşım kodları · gönüllü ve anonim topluluk düşüş istatistikleri ·
Asistana sor / Claude ile oku · 10 dil. Oyunun belleğine dokunmaz, yalnızca ekranı okur.

Bu dosyalar GitHub Actions'ta otomatik derlendi; kurulum dosyası Windows'ta sessizce kurulup program açılarak test edildi.
## 9.1.5 — Sürüm geçmişi, güvenli geri dönüş ve beta kanalına kontrollü geçiş

- 9.1.4 kullanıcılarının uygulama içinden doğrudan 9.1.5 kararlı güncellemesini alabilmesi sağlandı.
- RapidOCR 3.10, ONNX Runtime 1.31 ve DirectML için kararlı Python 3.13 paketleme kapıları korundu.
- CTranslate2 4.8.4, faster-whisper 1.2.1 ve SentencePiece sürüm sınırları sabitlendi.
- Ayarlar → Güncellemeler altında sürüm geçmişi ve kullanıcı onaylı eski sürüme dönüş eklendi.
- Beta kanalı isteğe bağlıdır; kullanıcı onayı olmadan beta kurulmaz.
- Python 3.14 uyumluluk betası ayrı `v9.1.5-beta.*` etiketlerinde tutulur.
- Beta installer adındaki `-beta.N` etiketi uygulama içi SHA-256 güncelleme doğrulamasında kabul edilir.
- Sürüm geçmişi artık installer/source arşivi olmayan teknik kayıtları gizler, 100 sürüme kadar listeler ve seçim yüklenmeden geri dönüş butonunu kapalı tutar.

## 9.1.5.2

- Sürüm geçmişi artık GitHub Releases listesini 100 kayda kadar güvenli biçimde tarar.
- Teknik/yardımcı sürümler geçmiş ekranından filtrelenir; yalnızca kurulabilir veya kaynak arşivi olan sürümler gösterilir.
- Geçmiş ekranı yüklenmeden geri yükleme düğmesi devre dışı kalır; çift tıklama ile eski sürüme dönme desteklenir.
- Uygulama sürüm numarası ile yayın etiketi eşitlendi.

## 9.1.5.3

- Canlı çeviri modeli artık kullanıcı tarafından, Canlı Çeviri sekmesindeki “Modeli indir” düğmesiyle isteğe bağlı indirilir.
- Başlatma ve `F6`/`F7` kısayolları model eksikliğini sessizce yutmak yerine kullanıcıya açık durum bildirir; otomatik indirme yapılmaz.

## 9.1.5.4

- OCR sonucu geçerli bir eşya kartı değilse artık boş/siyah oyun üstü penceresi açılmaz.
- Menü, harita veya okunamayan ekranlar için kullanıcıya açık “Bu bir eşya kartı değil” bildirimi verilir.
- Eşya overlay’inin dış çerçevesi siyah dikdörtgen yerine kart arka planıyla uyumlu çizilir.

## 9.1.5.5

- Kurulu EXE’de yerel çeviri modeli artık yazma izni olmayan Program Files yerine kullanıcıya ait `LOCALAPPDATA\TD2LootAdvisor\models` klasöründe tutulur.
- Kaynak/run.bat kullananlarda proje içindeki `models/en-tr` davranışı değişmez.
- Model indirme ve sonraki açılışta model bulma yolu aynılaştırıldı.

