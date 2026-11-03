# Yol Haritası

Bu dosya her gün güncellenir (bkz. en alt — otomatik günlük görev). Ayrıntılı mobil plan: `docs/mobile_companion_roadmap.md`.

## Genel durum (özet)

| Bileşen | Durum |
|---|---|
| Windows masaüstü uygulaması | Canlı, `v9.1.5.19`. Fazlı bir yol haritası yok — sürekli Windows render/kararlılık/tanılama düzeltme döngüsü (bkz. `DEVELOPMENT_LOG.md`). |
| Mobil companion (Flutter) | **Faz 2 (bulut altyapısı) — bu turda ilerletildi.** Faz 1 tamamlandı, Faz 3 (Flutter MVP) kısmen yapıldı ama gerçek cihaz/Play doğrulaması bekliyor. |
| Topluluk sunucusu (Cloudflare Worker) | Canlı (düşüş istatistikleri, görevler, hesap/lisans). Bu turda mobil uçlar eklendi, henüz production'a deploy edilmedi. |
| Lisans/telif (mx-division-builds) | Açıklığa kavuşturma talebi hazırlandı, kullanıcı tarafından açılması bekleniyor. |

## Şu an aktif: Mobil companion Faz 2 — Bulut altyapısı

**Bugün (bu turda) yapıldı:**
- D1 şeması: `mobile_pairings`, `mobile_devices`, `desktop_inbox`, `desktop_status`, `push_tokens`, `mobile_builds`, `account_deletions`.
- `server/mobile.js`: eşleştirme, telefon oturumu, masaüstü komut kuyruğu/olayları, build senkronu (revizyon çakışma kontrolü), push-token saklama (gönderim YOK, bilerek stub), cihaz/hesap iptali, 24 saat bekleme sonrası gerçek hesap silme.
- `server/test_mobile.mjs`: 25 test, hepsi geçti. Mevcut 4 test dosyası da regresyonsuz geçti.
- `accounts.js`'e `DELETE /v1/me` (masaüstünden hesap silme talebi) eklendi.
- `server/README.md` ve `docs/mobile_companion_roadmap.md` güncellendi.

**Yapılmadı / sıradaki adımlar:**
1. **Production'a deploy henüz yapılmadı** — bu değişiklikler yerel test ortamında (`node:sqlite`) doğrulandı, canlı Cloudflare Worker'a (`npx wrangler deploy` + `d1 execute --remote --file schema.sql`) gönderilmedi. Bu, gerçek üretim veritabanını etkileyeceği için kullanıcı onayı/kendi yapması daha güvenli — ya da açıkça onay alınıp bu oturumda yapılabilir.
2. **Gerçek push bildirimi (APNs/FCM)** — kimlik bilgisi yok, `sendPush()` stub. Faz 4'te ele alınacak.
3. **Flutter tarafında bu yeni API'leri kullanan ekranlar yok** — `mobile/lib/` şu an yalnız eski LAN tabanlı `companion.py` QR eşleştirmesini kullanıyor (roadmap Faz 3 notu). Yeni bulut API'sine geçiş ayrı bir iş.
4. Gerçek Android/iOS cihazda test, Google Play imzalama/yükleme — hâlâ bekliyor (Faz 4).

## Diğer açık kalemler (BUGS.md/HANDOFF.md'den)

- `master` dalı hâlâ silinmedi — kullanıcı GitHub Settings'ten silmeli (ortam kısıtlaması, bkz. HANDOFF.md).
- mxswat/mx-division-builds lisans sorusu — issue taslağı hazır, kullanıcının GitHub'dan açması gerekiyor (üçüncü taraf repoya yazma, ortam kısıtlaması).
- Tanıtım videoları (private repo) yayınlanmadı — kullanıcı onayı bekliyor.
- SignPath durumu bilinmiyor.
- Gerçek Windows'ta 9.1.5.19 görsel doğrulaması — bağlı bilgisayarın ekranı kilitli/erişilemez olduğu için yapılamadı, kullanıcının ekranı açması gerekiyor.

## Güncelleme günlüğü

- **2026-11-03**: Mobil Faz 2 (bulut altyapısı) başlatıldı — D1 şeması + `server/mobile.js` + 25 test. Bu dosya oluşturuldu.
