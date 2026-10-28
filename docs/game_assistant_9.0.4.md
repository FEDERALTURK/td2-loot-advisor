# 9.0.4 — Oyun içi sesli asistan ve bağımsız kısayollar

## Kullanım

| Varsayılan kısayol | İşlev |
|---|---|
| F6 | Canlı ekran/konuşma çevirisini durdurur; aynı tuşla önceki kaynakları yeniden başlatır. |
| F7 | Ekranı bir kez çevirir. |
| F8 | Eşya taraması başlatılmışsa bir eşya okur. |
| F9 | Mikrofonu açar; tekrar basıldığında kaydı bitirip soruyu gönderir. |
| F10 | Mevcut Claude görev getirme işlevi. |
| F12 | Mikrofon isteğini, bekleyen asistan yanıtını ve ses çıkışını iptal eder. |

Uygulama açık kaldığı sürece kısayollar eşya taramasından bağımsızdır. Çeviriyi durdurmak, onu yeniden başlatan kısayolu kapatmaz. Kısayollar Asistan, Canlı Çeviri ve mevcut eşya/görev ayarlarından değiştirilebilir; boş veya çakışan atamalar reddedilir. Bir tuşu değiştirmek diğer işlemlerin atamasını sessizce ezmez.

Asistan sekmesindeki **Konuşma modelini hazırla** düğmesiyle modeli oyun sırasında soru sormadan önce hazırlamak önerilir. İlk kullanımda model dosyaları indirilir. Yeni kurulumlarda çok dilli Whisper `base`, CPU int8 ve iki işlemci iş parçacığı kullanılır. Mevcut kullanıcıların model ve sağlayıcı seçimi korunur. Model beş dakika kullanılmadığında bellekten bırakılabilir; sonraki soruda yeniden yüklenir.

F9'a bas, sorunu söyle ve F9'a tekrar bas. Kayıt en fazla 20 saniyedir; süre dolduğunda otomatik gönderilir. Soru ve ilerleme durumu Asistan sekmesinde, oyun penceresi bulunabiliyorsa tıklamaları geçiren küçük bir oyun üstü pencerede görünür. Yanıt sesli okunur; bunun için genel sohbet seslendirmesinin açık olması gerekmez. Özel tam ekranda Windows kaplaması görünmeyebilir; kenarlıksız pencere modu kullanılabilir.

## Gerekli kurulum

- Yerel ses tanıma çalışma zamanı pakete dahildir. Model dosyaları ilk hazırlamada ayrıca indirilir; mikrofon kaydı açılmadan model hazırlanabilir. Konuşma dili arayüz dilini izler.
- AI yanıtı için seçili sağlayıcı çalışır durumda olmalıdır. Ollama'da servis ve seçilen model; Claude Code'da resmi CLI ve oturum; Claude/OpenAI'da geçerli API ayarı gerekir. Uygulama bunların hesabını veya API anahtarını sağlamaz.
- Yerleşik yardımcı genel amaçlı bir dil modeli değildir; mevcut eşya, istatistik ve build bilgilerine sınırlı kurallarla yanıt verir. Sağlayıcı hatasında bu yardımcıya dönülürse sesli yanıtta da bu açıkça belirtilir.
- Doğal çevrimiçi okuma isteğe bağlıdır. Kapalıyken kurulu Windows sesi kullanılır. Hazır Türkçe/İngilizce bildirim paketleri çevrimdışıdır.

## İşleyiş ve veri aktarımı

Mikrofon yalnız F9 veya Asistan'daki konuşma düğmesiyle açılır. Kayıt bellekte en fazla 20 saniyeyle sınırlandırılır; yeni bir kayıt için eski zamanlayıcı geçersizdir. Kullanıcı konuşurken programın kendi çeviri/eşya sesleri bekler. F12 eski sorunun sonradan görünmesini veya okunmasını engeller. Zaten gönderilmiş bir sağlayıcı isteği veya başlamış model indirmesi zorla sonlandırılmayabilir; iptal edilmiş çıktı kullanıcıya uygulanmaz.

Ses yerel Whisper ile metne dönüştürülür. Soru metni ve mevcut eşya/build/ilerleme bağlamı seçili AI sağlayıcısına gönderilir; bulut sağlayıcıda bu metin bilgisayardan çıkar. Mikrofon sesi AI sohbet sağlayıcısına gönderilmez. Çevrimiçi doğal ses açıksa yanıt metni ayrıca Microsoft ses hizmetine gönderilir. Bu özellik oyunun belleğini veya süreç verilerini okumaz; oyunda tuş basmaz ve oyun eylemi gerçekleştirmez.

AI işleri ve mikrofon tanıma işleri sınırlı işçilerde yürür. UI ve klavye dinleyicisi ağ/model işlemini beklemez. Klavye callback'leri Tk'ya dokunmadan olay kuyruğuna yazar; pencere güncellemeleri ana iş parçacığındadır. Durdurulmuş çeviri kaynaklarının gecikmiş callback'leri ve eski ekran yakalama işleri yeni çeviri başlatamaz.

## Doğrulama ve sınırlar

- Yeni testler kısayol bağımsızlığını, çakışma denetimini, tuş tekrarlarını, 20 saniye sınırını, eski zamanlayıcıları, mikrofon hatasından dönüşü, iptali ve gecikmiş çıktıların reddini kapsar.
- Gerçek yerel HTTP test sağlayıcısı üzerinden soru/yanıt protokolü ve seslendirme çağrısı sınanır. Bu, kullanıcının bulut hesabıyla yapılmış bir AI görüşmesi değildir.
- Gerçek Türkçe Neural ses örneği çok dilli Whisper base/CPU modeliyle metne dönüştürülmüştür. Bu test canlı mikrofon veya fiziksel hoparlör testi değildir.
- Yayın akışı, kurulan EXE içinden asistan çalışma zamanlarını ve gerçek Türkçe ses dosyası tanımayı da denetler. PyAV 19 ile faster-whisper 1.2.x arasındaki dosya okuma uyumsuzluğu nedeniyle `av>=14,<19` kullanılır.
- Gerçek oyun açıkken kullanıcı mikrofonu, ses aygıtı, seçili bulut hesabı ve fiziksel kısayol kullanımının birlikte denenmesi henüz yapılmamıştır. Yanıt süresi modele, donanıma ve sağlayıcı bağlantısına bağlıdır; sabit tepki süresi/FPS kazancı vaat edilmez.

Bu sürüm numarası kullanıcının isteği doğrultusunda **9.0.4** olarak belirlenmiştir; önceki yayın 6.0.3'tür. Mevcut kurulum kimliği ve kullanıcı verilerinin korunması sürdürülür.
