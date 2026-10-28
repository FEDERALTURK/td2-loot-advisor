# Yerinde çeviri ve doğal ses — 6.0.3

28 Ekim 2026. Bu özellikler 6.0.3 kaynak, kurulum ve taşınabilir sürümlerine dahildir.

## Yerinde çeviri

- Yerinde mod, OCR satırlarını ayrı kaynak dikdörtgenlerinde tutar. Altyazı ve diğer modlarda mevcut paragraf birleştirme davranışı korunur.
- Büyük logo yazıları ile küçük menü metinlerinin tek OCR satırında birleşmesi engellenir.
- Uzayan bir kutu, altındaki çeviriyi aşağı kaydırmaz. Metin kaynak konumuna bağlı kalır; yalnız boş alana uzar.
- Yazı ölçümünde ve çiziminde aynı font kullanılır. Uzun boşluksuz adlar da satıra bölünür. Çok dar alanda yazı küçülür; yine sığmıyorsa üç nokta kullanılır. Tam çeviri geçmişte kalır.
- Aynı metin farklı koordinata taşınırsa kaplama yeniden konumlanır. Boş ekran okumasında eski kaplama temizlenir.

Kaynak OCR'nin yazıyı kaçırması veya kutuyu yanlış belirlemesi bu değişikliklerle tamamen çözülmez. Gerçek oyunda, kullanıcının ekranı ve görüntü ölçeğiyle son görsel kontrol hâlâ gereklidir.

## İki ses paketi

| Paket | Gerçekte kullanılan ses | Kullanım |
|---|---|---|
| Türkçe — Doğal | Microsoft `tr-TR-EmelNeural` | Türkçe bildirimler ve çevrimiçi Türkçe okuma |
| English — Natural | Microsoft `en-US-AriaNeural` | İngilizce bildirimler ve çevrimiçi İngilizce okuma |

Her pakette 10 kayıt bulunur: sakla, değerlendir, parçala, incele, egzotik, adlı eşya, build uyumu, eksik yuva, yükseltme ve tanıtım. Toplam 20 kayıt yaklaşık 4,07 MB'dır. WAV dosyaları mono, 24 kHz, 16 bit PCM biçimindedir. Kayıtlar özgün bildirim metinlerinden Neural hizmetiyle üretildi; oyun sesleri kullanılmadı. Manifest, metinler, süreler ve SHA-256 değerleri `meta/voice_packs.json` dosyasındadır.

Hazır bildirimler çevrimdışı çalar. Seçilen paket, bildirim dilini belirler. Sohbet seslendirmesi arayüz dilini, canlı çeviri seslendirmesi Türkçeyi izler. Hazır kayıtlarda build adı ve yüzdesi gibi değişken değerler okunmaz; tam değerler uygulama ekranında kalır. Önceki cümle paketleri uyumluluk için korunmuştur.

## Çevrimiçi değişken ses

Asistan sekmesinde ve Canlı Çeviri sekmesindeki sesli okuma bölümünde **Sohbet ve çeviride çevrimiçi doğal ses** seçeneği vardır. İki kontrol aynı ayarı yönetir. Yeni ayarlarda bu seçenek kapalıdır; açılmasıyla okunacak metin Microsoft Edge ses hizmetine `edge-tts` üzerinden gönderilir. Bu, yerel model veya Azure API aboneliği değildir. Bu ses özelliği ekran görüntüsü ya da mikrofon kaydı göndermez.

Kapalıyken değişken metin Windows sistemiyle okunur. Açıksa Emel/Aria Neural kullanılır. Hizmet çalışmazsa sistem sesine dönülür ve günlükte hata türü belirtilir. Ses işçisi arayüzü bekletmez; kuyruk en fazla dört iş tutar, daha yeni istek gelince eski bekleyen istekler bırakılır. Eski çevrimiçi isteğin üretimi tamamlandığında sonucu artık güncel değilse çalınmaz. Çalmaya başlamış sesin anında kesileceği garanti edilmez.

Ses önbelleği `cache/voice` altındadır. Dosya adları metnin kendisini içermez; üretilen MP3 dosyaları konuşulan içeriği barındırır. En fazla 128 kayıt ve yaklaşık 32 MiB tutulur. Aynı ses tekrar gerektiğinde hizmet çağrılmadan kullanılabilir. `requirements.txt` ve paketleme betikleri çevrimiçi ses bağımlılıklarını içerir; sesler çalışma sırasında yeniden üretilmeden EXE içine alınabilir.

## Doğrulama

- Proje ekranı OCR örneği: 38 ayrı kaynak parçası; yerleşimde sıfır kutu çakışması.
- Gerçek Tk font ve Canvas ölçümü: çizilen metinler maskelerinin içinde kaldı. Test pencereleri gizli oluşturuldu; gerçek oyun ekranı otomasyonu yapılmadı.
- Kaynak koordinatının değişmesi ve boş ekranda eski kaplamanın temizlenmesi uygulama testleriyle doğrulandı.
- 20 WAV dosyasının boyutu, süresi, PCM biçimi, sessiz olmaması ve SHA-256 özeti doğrulandı.
- Çevrimdışı modda hizmet çağrılmaması, bağlantı hatasında sistem sesine dönüş, eski işin çalınmaması, sınırlı kuyruk ve geçersiz sesin önbelleğe alınmaması test edildi.
- Gerçek çevrimiçi Emel ve Aria çağrılarıyla MP3 üretildi ve çözümlenerek süreleri doğrulandı. Hoparlör çıkışının insan tarafından dinlenmesi ve oyunla birlikte sesli kullanım henüz doğrulanmadı.
- İlgili test grupları ve gerçek OCR örnekleri tekrar çalıştırıldı. Yayın derlemesinin sonuçları GitHub Actions içindeki Build Windows installer ve Stability and workload policy kayıtlarındadır.

Kaynak sürümünü başlatmak için `scripts/run.bat` kullanılır. Hazır ses örnekleri `meta/voices/natural_tr/demo.wav` ve `meta/voices/natural_en/demo.wav` dosyalarıdır.
