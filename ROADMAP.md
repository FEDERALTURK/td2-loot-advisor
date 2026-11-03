# Yol Haritası

Bu dosya her gün güncellenir (bkz. en alt — otomatik günlük görev). Ayrıntılı mobil plan: `docs/mobile_companion_roadmap.md`.

## Genel durum (özet)

| Bileşen | Durum |
|---|---|
| Windows masaüstü uygulaması | Canlı, `v9.1.5.19`. Fazlı bir yol haritası yok — sürekli Windows render/kararlılık/tanılama düzeltme döngüsü (bkz. `DEVELOPMENT_LOG.md`). |
| Mobil companion (Flutter) | **Faz 2 tamamlandı ve canlı; Faz 3'te bulut eşleştirmesi/build senkronu bu turda eklendi.** Gerçek cihaz/Play doğrulaması hâlâ bekliyor. |
| Topluluk sunucusu (Cloudflare Worker) | Canlı. Mobil uçlar (eşleştirme, build senkronu, cihaz listesi/iptali, hesap silme) production'da. |
| Lisans/telif (mx-division-builds) | [issue #153](https://github.com/mxswat/mx-division-builds/issues/153) açıldı, yanıt bekleniyor. |

## Şu an aktif: Mobil companion — bulut eşleştirmesi Flutter'a bağlandı

**Bu turda yapıldı — masaüstü (Python):**
- `account.py`: `create_mobile_pairing()`, `list_mobile_devices()`, `revoke_mobile_device(id)` eklendi (var olan `Account._req` Bearer-oturum yardımcısını kullanıyor).
- `app.py`: Hesap panelinde "📱 Telefon eşleştir" düğmesi — `_acc_pair_phone()` kodu üretir, 5 dakika geçerli kodu bir mesaj kutusunda gösterir. `lang/en.json` + `lang/tr.json`'a `acc.mobile_hint/mobile_pair/mobile_code` eklendi (diğer 8 dil İngilizce'ye düşüyor, `i18n.py`'ın tasarımı bu).
- `tests/test_account.py`: gerçek `server/dev_server.mjs`'e karşı eşleştirme kodu üretme → telefon tarafından claim etme (ham HTTP ile simüle edildi) → cihaz listesi → iptal akışının uçtan uca testi eklendi. **`python3 tests/test_account.py` → 28/28 PASS**, regresyon yok.

**Bu turda yapıldı — mobil (Flutter):**
- `mobile/lib/services/cloud_api.dart` (yeni): `server/mobile.js`'in tüm telefon-tarafı uçları için saf HTTP istemcisi (claim/dashboard/builds GET-PUT-DELETE/hesap silme), tipli hata (`CloudApiException`, `RevisionConflict`).
- `mobile/lib/services/cloud_link.dart` (yeni): `CloudLinkModel` — eşleştirme durumu (cihaz id/token `shared_preferences`'ta), 8 saniyede bir gösterge paneli yoklaması, build senkronu (yerelde değişeni gönder → buluttakini çek → tombstone'ları yereldeki build'lerden kaldır → revizyonları sakla), hesap silme.
- `mobile/lib/main.dart`: var olan LAN/QR eşleştirmesine **DOKUNULMADI** (ayrı, bağımsız özellik) — yanına yeni, bağımsız "Bulut eşleştirmesi" kartı/sayfası eklendi: 8 haneli kod girişi, çevrimiçi/çevrimdışı durumu, buildler sekmesinde "bulutla eşitle" düğmesi, yeni build kaydedince/silince otomatik (sessiz, en-iyi-gayret) bulut senkronu, ve mağaza kurallarının gerektirdiği "Hesabı ve tüm verilerimi sil" akışı (güçlü uyarı diyaloğuyla — bunun SADECE bu telefonu değil, masaüstünün bağlı TÜM hesabını sildiğini açıkça belirtiyor).
- ⚠️ **Doğrulanamadı**: bu kum havuzunda Flutter/Dart SDK'sı yok, dolayısıyla `flutter analyze`/`flutter test`/derleme çalıştırılamadı. Değişiklikler elle satır satır gözden geçirildi (parantez dengesi, tip uyumu, sınıf sınırları) ama **Windows PC'de (`Flutter 3.47.8` kurulu) `flutter analyze` ve bir derleme/çalıştırma ile doğrulanması gerekiyor** — bu yapılmadan "çalışıyor" sayılmamalı.

**Yapılmadı / sıradaki adımlar:**
1. **Windows PC'de doğrulama** — `flutter analyze` + `flutter run` (veya APK build), ardından gerçek akış: masaüstünde kod üret → telefonda gir → eşleşsin → build oluştur/sil → bulutla eşitle düğmesini dene.
2. **Gerçek push bildirimi (APNs/FCM)** — kimlik bilgisi yok, `sendPush()` hâlâ stub. Faz 4.
3. Gerçek Android/iOS cihazda test, Google Play imzalama/yükleme — hâlâ bekliyor (Faz 4).
4. PC'deki eski `git stash` girişi (`rollback/claude-last` dalındaki yerel değişiklikler) incelenip gerekirse ayrı bir dala alınmalı — veri kaybı yok ama kullanıcı kontrol etmeli.

## Diğer açık kalemler (BUGS.md/HANDOFF.md'den)

- `master` dalı hâlâ silinmedi — kullanıcı GitHub Settings'ten silmeli (ortam kısıtlaması, bkz. HANDOFF.md).
- mxswat/mx-division-builds lisans sorusu — [issue #153](https://github.com/mxswat/mx-division-builds/issues/153) açıldı (2026-11-03, kullanıcının PC'sinde kendi GitHub oturumuyla), yanıt bekleniyor.
- Tanıtım videoları (private repo) yayınlanmadı — kullanıcı onayı bekliyor.
- SignPath durumu bilinmiyor.

## Güncelleme günlüğü

- **2026-11-03**: Mobil Faz 2 (bulut altyapısı) başlatıldı, aynı gün production'a deploy edildi, Windows'ta v9.1.5.19 görsel testi tamamlandı. İki boşluk (cihaz listesi, build soft-delete) bulunup kapatıldı ve ikinci kez deploy edildi (Version ID `f75d2807-1da2-4f8d-a01d-12c7e1b6cbbb`). **Aynı gün: masaüstüne eşleştirme-kodu üretme eklendi (`account.py`/`app.py`) ve Flutter uygulaması yeni bulut API'sine bağlandı** (`cloud_api.dart`, `cloud_link.dart`, eski LAN/QR akışına dokunulmadan) — Flutter/Dart SDK'sı bu ortamda yok, Windows PC'de `flutter analyze` ile doğrulama bekliyor.
