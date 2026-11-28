# TD2 Loot Advisor — GitHub Actions Hata Kök Neden Analizi

Tarih: 2026-11-28  
Aday dal: `codex/release-9.1.5.56`  
Son doğrulanan commit: `2b64170`

## Sonuç

Ekran görüntülerindeki kırmızı koşuların tamamı aynı anda aktif üretim hatası değildir. GitHub Actions geçmişi her manuel denemeyi sakladığı için, düzeltilmeden önceki denemeler de listede kalır. Son aday commit için aşağıdaki temel kapılar başarılıdır:

| Kapı | Çalışma | Sonuç |
|---|---:|---|
| Account server + Windows UI | `46117507355` | PASS |
| Stability and workload policy | `46118579001` | PASS |
| Windows installer/package smoke | `46117717282` | PASS |
| Translate check / live UI | `46117745463` | PASS |
| Cloudflare Pages | PR check | PASS |
| Workers Builds: td2-stats | PR check | PASS |

PR #17 üzerinde görünen tek devam eden durum, GitHub dışı Graphify ve Cubic incelemeleridir; bunlar uygulama test hatası değildir.

## Hata sınıfları ve kök nedenler

### 1. Account UI: `_acc_btn` yok / pencere henüz hazır değil

İlk kırılmalarda test, ertelenmiş UI sayfaları ve CustomTkinter pencere kurulumu tamamlanmadan `_acc_btn.invoke()` çağırıyordu. Sonuçlar:

```text
AttributeError: 'App' object has no attribute '_acc_btn'
Tk callback hatası: application has been destroyed
```

Kök neden ürün hesabının kaybolması değil, testin widget referansını yaşam döngüsü tamamlanmadan kullanması ve hata sonrasında Tk kökünü kapatmasıydı. Kapanıştan sonra hâlâ kuyrukta bulunan `after`, bind ve CustomTkinter title-bar callback’leri ikincil `TclError` üretiyordu.

Kalıcı çözüm:

- Account smoke testi gerçek başlangıçtaki deferred UI hazır olma akışını bekliyor.
- Aynı-process rebuild simülasyonu ile gerçek yeni-process restart birbirinden ayrıldı.
- Yeniden açılış kontrolü, rebuilt root üzerinde kontrollü şekilde yapılıyor.
- Premium geçişinden sonra pencere oluşturma ile entitlement kontrolü birbirine karıştırılmıyor.
- İptal/yenileme kontrolü aynı-process restart yarışına sokulmadan izole ediliyor.
- Tk teardown hataları, test başarısızlığını maskeleyen ikincil gürültü olmaktan çıkarıldı.

Kanıt: Account check `46117507355` server ve Windows UI olarak başarılıdır.

### 2. Paketli translation probe: `app.capture is None`

Installer koşularındaki ana gerçek hata şuydu:

```text
AttributeError: 'NoneType' object has no attribute 'Grabber'
```

Kök neden: Ağır modüller normal `App()` başlatılırken daemon thread ile yükleniyordu. `translation_probe` ise `App()` oluşturmadan çalışan CLI yolu olduğundan bu thread hiç başlamıyor, `capture` placeholder değeri `None` kalıyordu.

Kalıcı çözüm:

- Deferred modül yükleyicisine kilit eklendi.
- `_ensure_deferred()` yalnızca event beklemiyor; eksik placeholder varsa senkron tamamlıyor.
- Çift import yarışını önlemek için mevcut modül atanmışsa tekrar yüklenmiyor.
- Beş deferred modül yerel probe ile doğrulandı.

Kanıt: Son installer koşusu `46117717282` başarılıdır.

### 3. Installer eksik modülleri

Önceki paket koşularında şu hatalar görüldü:

```text
ModuleNotFoundError: No module named 'capture'
ModuleNotFoundError: No module named 'meta_sync'
ModuleNotFoundError: No module named 'build_tool_ui'
```

Kök neden PyInstaller hidden-import kapsamının deferred modülleri tam içermemesi ve probe’un `None` placeholder ile devam etmesiydi.

Kalıcı çözüm:

- Installer hidden-import listesi güncellendi.
- Deferred yükleme fallback’i eklendi.
- Sessiz kurulumdan sonra gerçek kurulu EXE üzerinde translation probe çalıştırıldı.
- `app.log` içinde traceback aranarak paket smoke kapısı korunuyor.

### 4. Translate UI: model/OCR sonucu gelmeden assertion

Eski translate koşularında şu belirtiler birlikte görüldü:

```text
FAIL altyazı okundu ve çevrildi
FAIL çeviri kaplaması oyunun üstünde
FAIL yerinde çeviri
telefon sayfası: NoneType ... timeout
```

Kök neden sentetik pencere, OCR, yerel model ve overlay callback’lerinin sabit bekleme süresinden uzun sürmesiydi. Telefon kontrolü de güvenlik nedeniyle kapatılmış LAN HTTP paylaşımını eski davranışla PASS bekliyordu.

Kalıcı çözüm:

- Sabit `sleep` yerine bounded polling kullanıldı.
- OCR/çeviri/overlay için sonuç gelmeden assertion yapılmıyor.
- Güvenli HTTP LAN reddi bilinçli ve beklenen sonuç olarak test ediliyor.
- Gerçek HTTPS pairing olmadan telefon/ikinci ekran özelliği yanlışlıkla başarılı sayılmıyor.

Kanıt: Translate check `46117745463` başarılıdır.

### 5. Info/UI testlerinde CTk widget uyumsuzluğu

Eski Info koşularında `None.invoke` hataları ve notebook sayfa hazır olmadan yapılan widget kontrolleri vardı.

Kök neden testlerin klasik Tk widget davranışını CustomTkinter uyumluluk katmanına doğrudan uygulaması ve deferred notebook sayfalarını beklememesiydi.

Kalıcı çözüm:

- CTk widget sınırlarına uygun assertions kullanıldı.
- Deferred notebook/page hazır olma durumu bekleniyor.
- Widget bulunamadığında hemen root destroy edilerek ikinci bir TclError zinciri oluşturulmuyor.

## Kırmızı görünen ama farklı sınıfta olan kayıtlar

- PyInstaller’ın `tensorrt` ve `onnx` alt modülü uyarıları, kullanılmayan opsiyonel alt modüller için toplama uyarılarıdır; son installer koşusunu bozmadı.
- `application has been destroyed` kayıtlarının büyük kısmı ilk assertion başarısızlığından sonra testin root’u kapatmasıyla oluşan ikincil teardown hatalarıdır.
- Aynı commit üzerindeki art arda manuel koşuların kırmızı olması, eski run kayıtlarını geriye dönük yeşile çevirmez. Güncel commit’in check rollup’u esas alınmalıdır.
- Graphify ve Cubic, GitHub Actions test job’ları değil, PR üzerinde çalışan harici inceleme sağlayıcılarıdır.

## GitHub’da hata tekrarını azaltmak için uygulanan politika

1. Önceki kırmızı koşuları silmek yerine geçmiş kanıtı koruyoruz.
2. Yayın kararı yalnızca son commit SHA’sının check rollup’una göre veriliyor.
3. Installer workflow’u `release=false` ile çalıştırılıyor; public release koşulu ayrı tutuluyor.
4. UI testlerinde sabit bekleme yerine sınırlı polling ve yaşam döngüsü kontrolü kullanılıyor.
5. Deferred import kullanan her CLI/probe yolu `App()` olmadan da çalışabilir durumda tutuluyor.
6. Güvenlik nedeniyle LAN HTTP token/telefon paylaşımı PASS olarak maskelenmiyor; HTTPS olmadan açıkça reddediliyor.
7. Her kök neden için regression test veya CI smoke kontrolü korunuyor.

## Mevcut yayın kararı

Teknik aday dalı, son temel GitHub kapıları açısından başarılıdır. Buna rağmen public release/tag/installer yayını bu raporla otomatik yapılmaz; proje kuralları gereği kullanıcıdan açık yayın onayı gerekir.

Gerekli onay metni:

```text
Yeni Güncellemeyi Yayınlamak İster misiniz? (v9.1.5.56) — Evet / Hayır
```

## Sınırlar

Bu rapor GitHub Actions, yerel testler ve kurulu paket smoke kanıtına dayanır. Gerçek oyun/DX12 oturumu, fiziksel DPI/mouse pass-through kombinasyonları ve gerçek telefon–LAN HTTPS cihaz pairing’i bu koşuların dışında kalır.
