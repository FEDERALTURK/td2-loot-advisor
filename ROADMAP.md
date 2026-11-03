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

**Bugün ayrıca yapıldı (PC üzerinden, kullanıcı onayıyla):**
- ✅ **Production'a deploy edildi.** PC'de Cloudflare zaten oturum açıktı (`gokmensoner1888@gmail.com`, D1+Workers yazma izni). `npx wrangler d1 execute td2stats --remote --file schema.sql` (27 sorgu, 23 tablo — eklemeler `IF NOT EXISTS`, mevcut veriye dokunmadı) ve `npx wrangler deploy` (Version ID `278f119d-6683-4fc7-b8a4-c2d0a26e6a23`) çalıştırıldı. Canlı adres: `https://td2-stats.td2loot.workers.dev` — `GET /v1/health` doğrulandı (`{"ok":true,...}`).
- ✅ **Windows'ta v9.1.5.19 görsel testi tamamlandı.** PC'de git PATH'te değilmiş (GitHub Desktop'ın gömülü git'i kullanıldı); repo `rollback/claude-last` dalındaydı ve kaydedilmemiş yerel değişiklikler vardı — bunlar silinmeden `git stash` ile korunup (`git stash list`'te duruyor) repo `main`'e (`6b5aa69`) güncellendi. `app.py` yeniden başlatıldı, süreç "Running" durumda, arka plan görev/haber senkronu normal çalışıyor — çökme yok.

**Yapılmadı / sıradaki adımlar:**
1. **Gerçek push bildirimi (APNs/FCM)** — kimlik bilgisi yok, `sendPush()` stub. Faz 4'te ele alınacak.
2. **Flutter tarafında bu yeni API'leri kullanan ekranlar yok** — `mobile/lib/` şu an yalnız eski LAN tabanlı `companion.py` QR eşleştirmesini kullanıyor (roadmap Faz 3 notu). Yeni bulut API'sine geçiş ayrı bir iş.
3. Gerçek Android/iOS cihazda test, Google Play imzalama/yükleme — hâlâ bekliyor (Faz 4).
4. PC'deki eski `git stash` girişi (`rollback/claude-last` dalındaki yerel değişiklikler) incelenip gerekirse ayrı bir dala alınmalı — veri kaybı yok ama kullanıcı kontrol etmeli.

## Diğer açık kalemler (BUGS.md/HANDOFF.md'den)

- `master` dalı hâlâ silinmedi — kullanıcı GitHub Settings'ten silmeli (ortam kısıtlaması, bkz. HANDOFF.md).
- mxswat/mx-division-builds lisans sorusu — [issue #153](https://github.com/mxswat/mx-division-builds/issues/153) açıldı (2026-11-03, kullanıcının PC'sinde kendi GitHub oturumuyla), yanıt bekleniyor.
- Tanıtım videoları (private repo) yayınlanmadı — kullanıcı onayı bekliyor.
- SignPath durumu bilinmiyor.

## Güncelleme günlüğü

- **2026-11-03**: Mobil Faz 2 (bulut altyapısı) başlatıldı — D1 şeması + `server/mobile.js` + 25 test. **Aynı gün production'a deploy edildi** (PC üzerinden, kullanıcı onayıyla) ve Windows'ta v9.1.5.19 görsel testi tamamlandı.
