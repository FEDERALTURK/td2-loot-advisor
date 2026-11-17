# TD2 Loot Advisor - Proje haritası

Güncelleme notu (27 Ekim 2026, 17:48 İstanbul): Kullanıcının isteğiyle masaüstü ana klasörü GitHub main 74ffcc660bb9ad87860bf5eec63f7a5a82d86a00 ile eşitlendi. 17 dosya yenilendi, 544 dosya eklendi; 673 takipli dosya birebir doğrulandı. Kişisel builds.json ve sunucuya özel server/wrangler.toml korundu. Önceki dosyaların doğrulanmış yedeği C:\Users\PC\Desktop\Thedivision2program_backup_20261027_174819 içindedir. Aşağıdaki 5.0 yerel durum ve eski envanter sayıları ilk incelemenin tarihsel kaydıdır; ana klasör artık 6.0.1 kaynaklarını içerir. Güncel karşılaştırma LOCAL_VS_GITHUB_AFTER_UPDATE.csv ve işlem kaydı UPDATE_20261027_174819.json içindedir.

İnceleme tarihi: 27 Ekim 2026 (Europe/Istanbul).
Amaç: yerel dosyalar, güncel GitHub kaynakları ve Claude geçmişini karşılaştırıp geliştirmeye devam etmek için doğrulanabilir bir çalışma haritası oluşturmak.

## Başlangıçta bilinmesi gereken durum

- Masaüstü kökündeki app.py:50 kaynak sürümü 5.0; 5029 satır.
- GitHub main app.py:92 kaynak sürümü 6.0.1; 8033 satır.
- Yerel klasör bir Git checkout değil; eski uygulama kaynakları, daha yeni sunucu dosyaları, kişisel veriler ve farklı derleme çıktıları birlikte bulunuyor.
- Ana geliştirme kaynağı: FEDERALTURK/td2-loot-advisor, main 74ffcc660bb9ad87860bf5eec63f7a5a82d86a00.
- Son yayın v6.0.1; yayın kodu 1fc2553b8769f10d8aaeaf785cb4c79752e33914. Sonraki main commitleri feed/veri güncellemeleri içeriyor.
- Yönetim paneli ayrı özel depoda: FEDERALTURK/td2-loot-advisor-reports main fd393de7265f124113b9e6863bdbfd0e620e23ea, panel 1.5.0.
- Tanıtım kaynakları aynı özel depodaki promo 436394359e41fb53e595bb19e56666ae025dedf5 dalında.
- Çalışan/kurulu EXE sürümü dosyanın adından çıkarılmadı. Kurulu, dist ve panel EXE dosyalarının Windows sürüm alanları boş; içerikleri çalıştırılarak doğrulanmadı.

## İncelenen kapsam

Yerel kökte 247 dosya / 614625992 bayt envanterlendi. Kişisel private değerleri okunmadı; dosya adları ve boyutları envantere dahil.
Ana depo 675 takipli dosya; özel main 28, özel promo 83 takipli dosya.
Ana kaynak ve bütün varlıklar ayrı github/td2-loot-advisor klasörüne indirildi.
Özel main'in 27 metin/kaynak dosyası ve promo dalının 11 ek metin/kaynak dosyası alındı; özel ikili medya/yazı tipleri indirilmedi.
Yerel ve indirilen kopyalarda 139 Python kaynak dosyası AST ile ayrıştırıldı; sözdizimi ayrıştırma hatası bulunmadı.
Bu işlem uygulamayı başlatmaz, modülleri import etmez, bağımlılık veya davranış testi sayılmaz.
Bütün dosyalar envanterlendi; uygulama, sunucu, panel ve çeviri akışları kaynak üzerinden incelendi.
İkili EXE/model/video içerikleri çalıştırılmadı veya tersine mühendislikle incelenmedi.

## Ürün ve temel çalışma yolu

Ürün ekran kartındaki eşya metnini tanır, oyun kütüphanesiyle eşler, kullanıcının build koşullarına göre puanlar.
Karar motoru KEEP / CONSIDER / DISMANTLE / REVIEW üretir; sonuç panel, bindirme, ses, sandık ve ilerlemeye aktarılır.
Oyunun belleğini okumaya/yazmaya yönelik bir akış saptanmadı. gameinfo.py sınırlı süreç sorgusuyla EXE yolunu alıyor; bu yüzden "oyun sürecini hiç açmaz" ifadesi kaynakla uyumlu değil.

Akış:
F8/otomatik tarama -> capture + display -> kart bulma + OCR -> gamedata -> engine -> Tk sonuç kuyruğu -> UI / stash / progress / log / isteğe bağlı paylaşım.

## Güncel uygulama modülleri

| Modül | Sorumluluk ve ilişkiler |
|---|---|
| app.py | Tkinter uygulaması, 13 sekme, ayarlar, giriş ve arka plan işlerinin koordinasyonu. Bilgi ve Çeviri yeni sekmeler. Ana App sınıfı halen çok büyük. |
| capture.py | İş parçacığına özel kalıcı MSS yakalama, düşük maliyetli thumbnail örnekleme. |
| display.py / syncer.py | Pencere/DPI/çözünürlük, state.cfg yalnız okuma, donanım ve OCR ölçümü, uygulama ayarı önerileri. |
| ocr_backend.py / winocr.py | RapidOCR, Tesseract ve çeviri için Windows OCR. CPU/DirectML karşılaştırması, OCR kutuları ve renk ipuçları. |
| gamedata.py | Eşya türü, yuva, isim, set/marka, attribute/talent tanıma; learned_library.json ile yerel öğrenme. |
| engine.py | Gear/weapon/mod skoru, karar, build planı ve yuva koşulları, envanter listesi ipucu. |
| stash.py | Sandık kaydı, kopya ve kırma denetimi, build optimizasyonu, kalibrasyon önerisi. |
| vendor.py | Açık satıcı/targeted-loot verisi ve build/sandık eşleştirme. |
| share.py | TD2B build kodu; yerel sıkıştırma ve doğrulama. |
| dropstats.py | Gönüllü anonim düşüş kuyruğu, sunucuya toplu gönderme, premium istatistik okuma. |
| meta_sync.py / wiki_sync.py | Meta build, görev, rehber, haber ve oyun kütüphanesi eşitleme; Wiki metin/görsel okuma. |
| tasks_live.py | Canlı OCR'dan görev ayıklama, ortak görev/çeviri belleği, gönderim ve düzeltme önerileri. |
| livetranslate.py | İngilizce -> Türkçe yerel OPUS-MT veya seçili AI motoru; özel adları koruma, bloklama, çeviri önbelleği. |
| overlay.py | Çeviriyi arka fonlu kutularla OCR konumlarına yerleştirme; yazı boyutu/taşma/çakışma düzeni. |
| speech.py | W11 Live Captions veya W10/W11 sistem ses çıkışı + yerel Whisper; ardından aynı çeviri motoru. |
| trscreen.py / terms.py | Telefonda EN/TR çeviri görünümü ve oyun terimi açıklamaları. |
| knowledge.py | Ansiklopedi, meta vitrin, haberler, quiz/XP. |
| account.py / features.py | Discord giriş istemcisi, TD2P eski lisans ve TD2E cihaz bağlı hesap yetkisi, ücretsiz/premium kapıları. |
| reports.py | İsteğe bağlı hata/istek kaydı, sistem/log temizliği, kalıcı gönderim kuyruğu, rapor yanıtları. |
| safeio.py | Kilitli/atomik JSON, günlük yedek, Windows DPAPI ile gizli ayarlar. |
| service.py / screenstate.py | Oyun pencere/odak gözlemi, akıllı tarama, işlem önceliği, tepsi, autostart ve oturum özeti. |
| single.py | Windows tek kopya mutex/event yönetimi. |
| gameinfo.py / updates.py / updater.py | Oyun sürüm/dosya kimliği, birleşik güncelleme görünümü, program kaynak/EXE güncelleme. |
| localapi.py / companion.py | Token'lı yerel HTTP/WebSocket, OBS/Stream Deck ve telefon görünümü; oyun girdisi yerine uygulama işlemleri. |
| gamepad.py | XInput düğmelerini okuyup uygulama kısayolunu tetikler. |
| notify.py / presence.py | İsteğe bağlı ntfy/Discord webhook ve Discord Rich Presence. |
| i18n.py / lang/ | On arayüz dili; seçili dil -> İngilizce -> anahtar yedeği. Arayüz dil sayısı yerel makine çevirisinin dil kapsamıyla aynı değildir. |
| voicepack.py / ui_art.py / ui_theme.py / fx.py / bgvideo.py / view3d.py | Ses paketleri, temalar, efektler, özgün görseller/video, Tk ve önceden render edilmiş ajan görünümü. |
| winpath.py | Modeller için ASCII veya kısa yol/ortak klasör uyumluluğu. |

## Canlı çeviri ve konuşma

- F7/otomatik görüntü değişimi -> OCR -> sütunlara göre metin blokları -> terim koruma -> ortak çeviri belleği -> yerel/AI çeviri -> bindirme.
- Yerel motor İngilizce-Türkçe OPUS-MT/CTranslate2; arayüzün 10 dili, bu modelin 10 dile çeviri yaptığı anlamına gelmiyor.
- AI motoru Asistan'daki Claude Code / Claude API / OpenAI / Ollama sağlayıcısını kullanır.
- Windows OCR/RapidOCR tercihi hız ve metin benzerliğiyle ölçülür; gerçek doğru cevaba karşı kalite ölçümü değildir.
- Windows 10 konuşma yolu varsayılan ses çıkışını loopback ile dinler; sadece oyun sesini ayırmaz.
- Ham ses diske yazılmıyor; EN/TR çeviri metni logs/live_translate.log'a kaydediliyor.
- Kullanıcı açarsa ücretsiz telefon çeviri görünümü yerel ağda sunulur.
- Çevrimiçi AI seçilince tanınmış konuşma metni de sağlayıcıya gidebilir. Mevcut ses gizlilik açıklaması bunu yeterince anlatmıyor; BULGULAR.md'ye bakın.

## Kalıcı veri ayrımı

| Alan | Veri |
|---|---|
| Kullanıcı | builds.json (ayar/build), progress.json, tasks.json, stash.json, loot_log.csv; kaynak ve kullanıcı verisi ayrılmadan kopyalanmamalı. |
| Yerel türetilen | learned_library.json, oyun/meta/görev/satıcı önbellekleri, çeviri önbelleği, screenstate imzaları, session log. |
| Gizli/yayıncı | private/; değerleri incelenmedi. Public depoya veya tanıtım/devir paketine eklenmemeli. |
| Paket verisi | lang/, meta/game_data.json, meta/meta_builds.json, görev/haber/terim/voice feed'leri, icon/, agent kareleri. |
| Çıktı | build/, dist/, installer/, logs/ ve son kart görüntüleri; sürümleri kaynakla aynı varsayılmaz. |

## Sunucu ve panel ilişkisi

Cloudflare Workers + D1 sunucusunun ana yönlendiricisi server/worker.js.
accounts.js, tasks.js ve overview.js ayrı modüller; worker.js dosyasını tek başına kopyalamak bütün sunucu projesini yayınlamaz.

| Yol/alan | İşlev |
|---|---|
| POST /v1/drops, GET /v1/summary, /v1/stats | Düşüş doğrulama/tekilleştirme, özet ve premium istatistik. |
| /v1/auth/start, callback, token, logout; /v1/me | Discord OAuth, loopback grant/verifier, oturum ve imzalı yetki. |
| /v1/license/redeem | Anahtar, davet ve Gumroad lisansı. |
| /v1/reports, /v1/reports/status | Kuyruk/temizleme -> özel GitHub issue; kullanıcıya yönetici yanıtı. |
| /v1/tasks, /v1/tasks/live, /v1/suggest | Topluluk görevleri, ortak çeviri belleği, öneri. |
| /v1/admin/* | Hesap/lisans/davet/cihaz, görev/çeviri moderasyonu, overview. |

Topluluk görevi varsayılan iki farklı bildirici eşiğiyle yayımlanır. Sunucuya özel ham görev anlık görüntüsü günlük; bakım cron'u ve public feed iş akışı saatliktir.
meta/tasks_live.json bu main snapshot'ında boş (tasks=[]); sistem kodunun bulunması gerçek katkı verisinin dolu olduğunu göstermez.
Sürüm sayacı gün/sürüm toplamı olarak açılış ve poll sayılarını tutar; 6.0.1 öncesi istemcileri kapsamaz.
Cloud sync features.py içinde COMING; çalışan bulut kayıt eşitlemesi olarak anlatılmamalı.

Özel panel 1.5.0:
- panel.py + github_api.py: raporlar, filtre/durum/yanıt ve GitHub issue ilişkisi.
- license_tab.py: hesap/lisans/davet/cihaz yönetimi, AdminAPI.
- tasks_tab.py: görev gizleme/Türkçe düzeltme ve çeviri önerisi moderasyonu.
- dashboard_tab.py: overview ve sürüm/indirme grafikleri.
- lock.py: PIN türetme/şifreleme, deneme gecikmesi; panel.py ayrıca Windows DPAPI.
- tray.py: tepsi/bildirim; selfupdate.py: özel panel release ve zorunlu SHA denetimi.
Yerel eski panel/panel.py bu kaynakların yerine kullanılamaz.

## Varlık, kütüphane ve üretim yolu

- Oyun kütüphanesi v2026-10-25.5: 29 set, 39 marka, 80 exotic, 170 named, 521 item, 359 weapon-index kaydı. Bunlar dosya sayımları; oyun içeriğinin güncellik kanıtı değildir.
- Meta build v2026-10-27.1: 13 build; görev feed'i 17 görev + 17 rehber; haber feed'i 8 kayıt.
- scripts/build_library.py Wiki/önbellek verisini derler; library_excel.py ve import_library_excel.py meta/TD2_Kutuphane.xlsx ile veri düzenleme döngüsü sağlar.
- scripts/agents* Blender/MakeHuman tabanlı modelleme, 48 açı render, parça maskesi ve anchor üretir. Runtime Tkinter önceden üretilmiş kareleri kullanır; Blender gerekmez.
- Kaynakta beş kıyafet için WebP kare ve PNG maskeler var; düzenlenebilir model kaynak bağımlılıklarının tamamı dağıtım varlığı değildir.
- Yazılım LICENSE dosyası MIT. Oyun veri kaynakları README'de CC BY-NC-SA/CC BY-SA, model ve font kaynakları kendi lisanslarıyla açıklanıyor; bunlar ayrı bağımlılıklardır.

## Derleme, test, yayın

- Python 3.13 öneriliyor; scripts/run.bat 3.13 sonra 3.12 seçiyor.
- requirements.txt: mss, pillow, pytesseract, pynput, pystray, ctranslate2, sentencepiece, soundcard.
- RapidOCR/ONNX, Whisper/TTS/video/QR ek bağımlılıklar; kurulum paketi ve eski tek-EXE derleme yollarının içerikleri aynı değil.
- PyInstaller + Inno Setup kullanıcı dizinine kurulum; model release'i mt-models uygulama sürümünden ayrıdır.
- tests/ altında 31 Python dosyası: 19 test_*, 9 ui_*, 3 yardımcı/ölçüm dosyası. Server'da 4 test_*.mjs.
- 14 mevcut public workflow hesap, çeviri, hizmet, bilgi, OCR, UI, senkron, performans, model, ajan varlıkları, kurulum, görev feed'i ve eski yayın temizliğini kapsıyor.
- Son workflow sonuçları GITHUB_DURUMU.md'de; her kontrol aynı commit'te çalışmamış. Installer başarısı bütün testlerin son main'de geçtiği anlamına gelmez.
- Bu inceleme yeni test çalıştırması değildir. Gerçek oyun/GUI/mikrofon/W11 Captions/kurulum ve dış hesap akışları yeniden denenmedi.

## Geliştirmeye devam etme ilkesi

1. Kod tabanı olarak güncel GitHub main snapshot'ını kullan; kökteki 5.0 dosyalarını rastgele yeni dosyalarla birleştirme.
2. Kullanıcı verileri ve yayıncı anahtarları ayrı korunmalı; panel özel depoda kalmalı.
3. Önce BULGULAR.md'deki karar doğrulaması ve gizlilik metni/akışı sorunlarını somut testlerle ele al.
4. Bir değişiklikte ilgili iş akışını/test grubunu seç; eski CI yeşil sonucunu yeni commit için doğrulama sayma.
5. Sezon/görev/metayı mevcut feed yolu ve kaynakları üzerinden doğrula; tarihli veriyi kalıcı oyun gerçeği kabul etme.

## İnceleme çıktıları

- GITHUB_DURUMU.md: depolar, dallar, release/Actions/medya durumu.
- BULGULAR.md: kaynakla desteklenen açık noktalar ve doğrulama sınırı.
- FILE_INVENTORY.csv: yerel + indirilen snapshot dosya envanteri.
- GITHUB_FILE_INVENTORY.csv: üç GitHub ref'inin tam blob listesi/kimlikleri.
- LOCAL_VS_GITHUB.csv: 675 ana repo dosyasının yerel karşılaştırması (25 aynı, 40 farklı, 610 yok).
- SOURCE_MAP.json: modül, satır, import, sınıf ve üst düzey fonksiyon dizini.
- GITHUB_SNAPSHOT.json: commit/release/branch/issue/Actions/video kayıtları.
- SCAN_SUMMARY.json: sayısal kapsam ve statik ayrıştırma sonucu.

Kaynakların sabit kopyaları github/ altında. project_review inceleme klasörüdür; aktif uygulama dosyaları güncellenmedi ve GitHub'da yazma/yayın işlemi yapılmadı.

