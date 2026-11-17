# Kaynak incelemesi bulguları

Güncelleme notu (27 Ekim 2026, 17:48 İstanbul): Aşağıdaki 1. madde kullanıcı isteğiyle giderildi; ana kaynak klasörü güncel GitHub main ile eşitlendi. Kullanıcı verileri ve yerel sunucu yapılandırması korundu, yedek ve dosya doğrulama kaydı oluşturuldu. Diğer kod bulgularına bu kaynak eşitlemesinde düzeltme uygulanmadı.

Tarih: 27 Ekim 2026.
Güncel public ref: 74ffcc660bb9ad87860bf5eec63f7a5a82d86a00 (uygulama 6.0.1).
Kaynak atıfları github/td2-loot-advisor kopyasına göredir.
Bulgular statik inceleme sonuçlarıdır; davranış/GUI testleriyle yeniden üretilmedi. Bu dosya öneri ve takip kaydıdır; düzeltme uygulanmadı.

## Öncelikli

1. **Yerel geliştirme tabanı eski ve karışık.** Kökteki app.py:50 5.0; GitHub app.py:92 6.0.1. Yerel kaynakta hesap, F7 canlı çeviri ve tek kopya modülleri yok. Daha yeni server/ ve panel EXE'si bu eski istemciyle yan yana. Kod değiştirmeden önce tabanı belirlemek gerekiyor.

2. **Konuşma gizlilik metni çevrimiçi AI yolunu kapsamıyor.** lang/tr.json:1485 sp.hint bütün ses için "her şey bu bilgisayarda kalır" diyor. app.py:1700 _sp_text -> 1704 lt_translator().translate; lt_translator:1495 AI seçilince ai_complete:1465 sağlayıcısına gider. Claude/OpenAI/Claude Code veya uzaktaki Ollama seçilirse tanınan metin dışarı gönderilebilir. Ham sesin yerelde işlenmesi, çeviri metninin de yerelde kaldığını kanıtlamaz. Ayrıca varsayılan sistem çıkışı diğer konuşmaları da içerebilir. Metin/onay davranışı seçilen motorla uyumlu yapılmalı.

3. **Geçersiz OCR bütün girişlerde merkezi doğrulanmıyor.** app.py:556 valid_item var; evaluate:597 bunu ortak ön koşul yapmıyor. Otomatik mod kontrolü scan_image:4064 civarında; manuel ve vision yolları aynı kontrolü zorunlu kullanmıyor. Modern engine boş/partial kartı REVIEW yapıyor (engine.py:297-300), ancak evaluate_legacy:607 yolu kütüphane yokken geçersiz metin için KIR üretebilir. Yeni bir değişiklik, bütün girişleri ve yedek motoru kapsamalı.

4. **Prototype karar politikası tutarsız.** app.py legacy bütün Prototype'ları REVIEW yapıyor; engine.py:315 sadece eşik üstündekini KEEP yapıyor, daha düşük puan :321 DISMANTLE'a düşüyor. stash.py denetimi egzotik korur, Named/Prototype için evrensel koruma yok. Ürün politikasının tek noktada belirlenmesi gerekiyor.

## Veri, gizlilik ve eşzamanlılık

5. app.py:7235 ayar eşiklerini sayıya çeviriyor ama 0-100 ve KEEP >= CONSIDER koşulu yok.
6. app.py:5099 import_builds yalnız üst listenin türünü denetliyor; :5110 öğe sözlük varsayılıyor. Alan tipleri/sayısal değerler için şema doğrulama gerekli.
7. app.py:1091 bütün paralel Claude çağrıları için aynı system_prompt.txt dosyasını kullanıyor; istemlerin birbirinin üstüne yazılma olasılığı var.
8. safeio.py:91-94 Windows şifreleme hatasında özgün düz değeri döndürüyor. README'deki şifreli saklama beklentisi hata yolunda sağlanmıyor. Windows dışındaki düz saklama da açıkça belgelenmeli.
9. Çeviri metinleri logs/live_translate.log'a yazılıyor (app.py _lt_log). Metin kaydı ve isteğe bağlı LAN telefon yayını gizlilik açıklamalarında motor seçiminden ayrı anlatılmalı.
10. Hesap ve rapor kuyruğu kayıtları bazı yerlerde ayrı temp/replace yöntemini kullanıyor; safeio'nun kilit/yedek davranışı bütün dosyalara yayılmış değil. Eşzamanlı yazma ve bozuk kayıt kurtarma hedefli kontrol gerektirir.

## Dayanıklılık ve performans

11. app.py:1855 _lt_last_sig çeviri başarılı olmadan atanıyor. Ağ/model hatasından sonra değişmeyen ekran otomatik akışta tekrar denenmeyebilir.
12. app.py:1833 lt_once her çağrıda iş parçacığı açıyor; manuel tuş tekrarları için tek iş/kuyruk kısıtı görünmüyor. Eski sonuçların daha yeni ekranın üstüne gelmesi incelenmeli.
13. localapi.py:94 WebSocket sendall senkron, :221 bağlantı timeout'u None. UI callback'lerinden yayınlanan sonuç, yavaş LAN istemcisi yüzünden bekleyebilir; worker/kuyruk ve zaman aşımı değerlendirilmeli.
14. gameinfo.py running_exe sınırlı OpenProcess/QueryFullProcessImageNameW çağrılarında 64 bit ctypes imzaları tanımlanmamış; başarısız yol sessiz olabilir.
15. Debug görüntü seçeneği açıksa son ekran app.py:3977-3978'de kart bulunmadan önce yazılıyor. Kart yokken OCR azaltılmış olsa da "hiç disk yazımı yok" iddiası koşulsuz doğru değil.
16. winpath ortak klasöre kopyada ad/boyut karşılaştırıyor; aynı boyutlu değişmiş model dosyası için güncellik ölçütü zayıf.

## Tamamlanmamış veya kapsamı karıştırılmaması gerekenler

17. features.py:41 cloud_sync COMING; çalışan bulut sandık/build eşitlemesi bulunmuş gibi anlatılmamalı.
18. meta/tasks_live.json görev listesi bu snapshot'ta boş. Onay eşiğine ulaşmış gerçek katkı yokluğu veya yayın süreci ayrıca kontrol edilmeli; tek dosyadan sebep çıkarılamaz.
19. W11 Live Captions gerçek işletim sistemi/dil/erişim gereksinimlerinde yeniden denenmedi. Yerel model/Whisper/OCR hızları kaynak belgesindeki iddialardan bu incelemeye taşınmadı.
20. Generic pull_request CI yok; çoğu otomatik kontrol dosya yolu filtreli push, bazı Windows kontrolleri yalnız manuel. Son main için bütün test grupları birlikte çalışmış değil.
21. server/README.md tek worker.js yapıştırma talimatı modüllü sunucuyla uyumsuz; tüm Wrangler projesi üzerinden yayın yolu belgelenmeli. Testler Node 22 kullanıyor, kurulum metni 18+ diyor.
22. Kaynak güncelleyici izinli dosyaları ekler/değiştirir; eski dosyaları silmez veya bütün güncellemeyi tek işlem olarak geri almaz. Panel ayrı depodan güncellenir.
23. Uygulama app.py 8033 satır ve işlerin çoğu App sınıfında. Davranış sabitlendikten sonra UI, tarama, çeviri ve hesap koordinasyonu ayrı modüllere alınabilir; bunu eski yerel kaynağı klasörlere taşımayla karıştırmamak gerekir.

## Çözüldüğü güncel kaynakta görülen eski sorunlar

- Hesap/rapor istemcileri ve test dosyalarının yerelde eksik olması GitHub'da düzelmiş.
- EXE güncelleyici SHA-256 ve kaynak/ad denetimini zorunlu yapıyor.
- Tek kopya mutex/event desteği, oyun odak/durum izleme, adaptif tarama mevcut.
- Ayar/progress/task/stash için atomik/yedekli yazma ve normal Windows gizli ayar şifrelemesi mevcut.
- Otomatik kart bulunmayan geniş ekranda tam ekran OCR'a gitmeden dönüş mevcut.
- Modern motor boş/partial kartları REVIEW yapıyor; bütün giriş yollarının güvenli olması için yine merkezi politika gerekli.

## Kanıt sınırı

Yerel ve GitHub kaynakları statik okundu, dosya/commit/CI metaverisi doğrulandı. Uygulama, test, installer, model veya sunucu yayını çalıştırılmadı. GitHub'ın geçmiş başarılı kontrol kayıtları yeni yerel test sonucu olarak sunulmadı. Gizli değerler ve canlı hesap/veritabanı içeriği okunmadı.

