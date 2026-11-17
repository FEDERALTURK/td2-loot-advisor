# TD2 Loot Advisor: kararlılık ve performans çalışması

27 Ekim 2026. Kaynak değişiklikleri 6.0.2 olarak GitHub'a gönderildi, temiz Windows ortamında derlendi ve kararlı sürüm olarak yayınlandı. Yayın: https://github.com/FEDERALTURK/td2-loot-advisor/releases/tag/v6.0.2

## Uygulanan davranış

- Dengeli varsayılan profil ve tek tıkla Oyun öncelikli profil. Otomatik taramada daha az OCR denemesi ve daha seyrek kontrol; elle tarama kalitesi korunur.
- Ortak eşya doğrulaması: geçersiz OCR incelemeye gider. Exotic, Named ve Prototype değerlendirme, ilerleme ve depo denetiminde KIR sonucuna düşmez.
- Çeviri ve hata ayıklama işleri sınırlı kuyruk kullanır. Çeviride eski sonuçlar uygulanmaz; sayı/oyun terimi kaybı ve bozuk sonuçlar önbelleğe alınmaz. Başarısız çeviri aynı ekran için tekrar denenebilir.
- Yeni ayarlarda yerel çeviri, kapalı metin günlüğü ve kapalı hata ayıklama görüntüsü. Mevcut kullanıcı ayarları korunur. Çevrimiçi AI seçiminde veri aktarımı açıklanır.
- Oyun öndeyken veya pencere küçültüldüğünde arka plan animasyonları bekler. Görsel önbellekler ve süre ölçümleri sınırlıdır. Boşta kalan yerel çeviri modeli serbest bırakılabilir.
- RapidOCR ısınma ve tarama işlemleri aynı model üzerinde eşzamanlı çalışmaz. Yavaş yerel API istemcisi arayüz yayınını bekletmez.
- Kaynak başlatıcısı normal açılışta gereksiz pip çalıştırmaz ve büyük modelleri bağımlılık kontrolü için içeri aktarmaz. İsteğe bağlı paketler `--extras`, onarım `--repair`, kurmadan kontrol `--check` ile kullanılabilir.

## Doğrulama

Son çalıştırmanın makine tarafından okunabilir sonucu `stability_checks/final_results.json`, her grubun çıktısı aynı klasördeki `test_*.log` dosyalarındadır. Yeni birim/entegrasyon testleri eşya politikası, sınırlı kuyruk, performans politikası, animasyon bekletme, uygulama bağlantıları, çeviri bütünlüğü, yerel API basıncı, başlatıcı ve OCR eşzamanlılık korumasını kapsar. Mevcut çekirdek, yerel API, çeviri, otomatik tarama, ekran durumu, servis, overlay ve görev testleri de çalıştırılmıştır.

Gerçek RapidOCR denemesinde iki örnek kartın 1440p, 1080p, 720p ve 480p sürümleri olmak üzere sekiz kontrol geçti. Bu örnek kümesi tüm eşyalarda veya tüm ekran düzenlerinde yüzde yüz doğruluk kanıtı değildir. Yerel çeviri modeli de mevcut çeviri testinde çalıştırıldı.

`test_stability_widgets.py`, geçici ayarlar ve verilerle gerçek Tk bileşenlerini oluşturur; profil düğmesini, çeviri gizlilik metnini ve zamanlama penceresini denetler. Dış servisler, model ısınması ve efektler kapalıdır. Bu test görsel yerleşim, oyun içi çalışma veya tam uygulama RAM ölçümü değildir.

Kişisel `builds.json`, `tasks.json`, `stash.json`, `progress.json` ve `server/wrangler.toml` dosyalarının önce/sonra SHA-256 karşılaştırması `stability_checks/preserved_after.json` dosyasındadır. Değişiklik listesi `stability_checks/changed_files.json`, kaynak yaması `stability_changes.patch` dosyasındadır.

## Kalan ölçümler

Gerçek 8 GB RAM ve harici GPU bulunmayan bilgisayarda çalışma; oyun açıkken CPU/RAM/GPU/FPS etkisi; görünür arayüzün yerleşimi; gerçek oyun ekranı, mikrofon ve çevrimiçi sağlayıcıyla uçtan uca deneme henüz doğrulanmadı. Bu aşamada yüzde hızlanma veya FPS artışı iddiası yoktur. GPU sağlayıcısı otomatik değiştirilmedi.

Kaynak sürümü başlatmak için proje kökündeki `scripts/run.bat` kullanılabilir. 6.0.2 kurulum ve taşınabilir paketleri bu değişiklikleri içerir. Önceden mevcut eski EXE dosyaları kendiliğinden değiştirilmedi.
