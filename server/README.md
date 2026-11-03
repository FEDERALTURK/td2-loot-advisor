# Topluluk istatistik sunucusu / Community stats server

Cloudflare Workers + D1 (ücretsiz katman yeterli). Uygulama düşüşleri buraya gönderir; premium kullanıcılar
"hangi aktivitede ne düşüyor" istatistiğini buradan okur. Sunucu IP saklamaz, istemci kimliğini tuzlu özetle tutar.

## Yayındaki sunucu

`https://td2-stats.td2loot.workers.dev` (Cloudflare panelinden kuruldu: D1 `td2stats`, bağlama `DB`,
değişkenler `LICENSE_PUBKEY` ve gizli `HASH_SALT`). Uygulamanın varsayılan adresi budur (`dropstats.DEFAULT_URL`).
Kod güncellemesi (2026-11-03'ten beri): Worker, Cloudflare Workers Builds ile GitHub'a bağlı — `main` dalındaki
`server/` dizinine giden her push, `npx wrangler deploy`'u otomatik tetikler (Root directory: `server`). Elle
"Edit code" ile yapıştırma artık gerekmiyor; yalnızca manuel/acil bir düzeltme gerekiyorsa Cloudflare panelinden
Quick Edit hâlâ kullanılabilir ama normal akış artık `git push`.

## Kurulum (bir kez, ~10 dakika)

Gerekenler: Node.js 18+ ve ücretsiz bir Cloudflare hesabı.

```bat
cd server
npx wrangler login                                   :: tarayıcıda Cloudflare hesabına izin ver
npx wrangler d1 create td2stats                      :: çıktıdaki database_id'yi wrangler.toml'a yaz
npx wrangler d1 execute td2stats --remote --file schema.sql
npx wrangler secret put HASH_SALT                    :: uzun, rastgele bir metin yapıştır (kimseyle paylaşma)
npx wrangler deploy                                  :: adres: https://td2-stats.<hesabın>.workers.dev
```

Sonra adresi uygulamaya ver:
- herkes için varsayılan: `dropstats.py` içinde `DEFAULT_URL = "https://td2-stats.<hesabın>.workers.dev"`, ya da
- yalnız kendin için: İstatistik → Topluluk → Sunucu.

Lisans açık anahtarı `wrangler.toml` içindeki `LICENSE_PUBKEY`'dir; `scripts/license_tool.py init` ile anahtar çiftini
değiştirirsen burayı da güncelle.

## Yerelde deneme

```bat
npx wrangler d1 execute td2stats --local --file schema.sql
npx wrangler dev --local --port 8787
python test_local.py TD2P-...                        :: ayrı pencerede; lisans anahtarı isteğe bağlı
```

## Uç noktalar

| Yol | Ne | Erişim |
|---|---|---|
| `POST /v1/drops` | `{"client": "...", "drops": [...]}` en çok 50 kayıt | herkese açık, saatte 600 kayıt / istemci ve IP |
| `GET /v1/summary` | toplam düşüş, katkıcı sayısı | herkese açık |
| `GET /v1/stats?activity=&q=&weeks=` | aktivite başına en çok düşenler, eşyanın nerede düştüğü | `Authorization: TD2 <lisans>` |
| `GET /v1/health` | çalışıyor mu | herkese açık |
| `POST /v1/tasks` | topluluk görevi: `{"client", "app", "task": {title, subtitle, desc, objective, total, rewards, category, period, expires_at}, "tr": {...}}` | herkese açık, saatte 60 / istemci |
| `GET /v1/tasks/live` | en az 2 oyuncudan gelen güncel görevler (+ Türkçe) | herkese açık, 5 dk önbellek |
| `GET /v1/admin/tasks`, `POST /v1/admin/tasks/hide`, `POST /v1/admin/tasks/override` | tüm görevler, gizle, Türkçe düzelt | `Authorization: Admin <ADMIN_TOKEN>` |

Kayıt biçimi ve doğrulama: `worker.js` (`cleanDrop`). Attribute değerleri alınmaz, yalnız türleri.

## Maliyet

Workers ücretsiz katmanı günde 100.000 istek, D1 ücretsiz katmanı 5 GB depolama ve günde 5 milyon satır okuma verir.
Uygulama düşüşleri 10 dakikada bir toplu gönderir; binlerce oyuncu için bile ücretsiz katman yeterlidir.

## Hesap sistemi (Discord ile giriş, anahtar / davet / satış, 1 bilgisayar)

Giriş isteğe bağlıdır; program hesapsız da ücretsiz çalışır. Kurulum (bir kez, kendi bilgisayarında):

1. https://discord.com/developers/applications → **New Application** → ad: `TD2 Loot Advisor`.
   OAuth2 sayfası → **Redirects**: `https://td2-stats.td2loot.workers.dev/v1/auth/callback` → Save.
   Client ID ve **Reset Secret** ile Client Secret'ı al. (Rich Presence → Art Assets: `logo` adında bir görsel yüklersen
   Discord durumunda simge görünür.)
2. `cd server` → `node account_setup.mjs` — imza anahtarını ve yönetici belirtecini burada üretir, gizlileri doğrudan
   Cloudflare'e yollar, tabloları ekler ve yayınlar. Hiçbir gizli bilgi depoya ya da ekrana yazılmaz.
3. `private\ent_public_key.txt` içindeki açık anahtar programın `features.py` → `ENT_PUBLIC_KEY_HEX` değerine yazılır
   (gizli değildir). `private\admin_token.txt` → Rapor Paneli → Ayarlar → *Yönetici belirteci*.

| Yol | Ne | Erişim |
|---|---|---|
| `POST /v1/auth/start` · `GET /v1/auth/callback` · `POST /v1/auth/token` | Discord girişi (PKCE + 127.0.0.1 dönüşü, ya da `"platform":"web"` ile `SITE_URL`'e dönüş) | herkese açık, oran sınırlı |
| `GET /v1/me` | hesap, lisans, 7 günlük imzalı yetki belgesi (TD2E) | `Authorization: Bearer <oturum>` |
| `POST /v1/license/redeem` | `TD2K-…` anahtar, `TD2I-…` davet, Gumroad anahtarı | oturum; saatte 10 deneme |
| `POST /v1/auth/logout` | oturumu kapat | oturum |
| `/v1/admin/*` | hesaplar, lisanslar, davetler, denetim, istatistik | `Authorization: Admin <ADMIN_TOKEN>` |

Güvenlik: oturum belirteçleri, anahtarlar ve davet kodları veritabanında yalnız SHA-256 özetleriyle durur; düz anahtar
yalnız üretildiği an panelde görünür. Bir lisans tek bilgisayara bağlanır (panelden "Cihazı sıfırla"). Yetki belgesi
bilgisayara bağlıdır ve 7 gün internetsiz geçerlidir. Testler: `node test_accounts.mjs`, `python ../tests/test_account.py`.

**Not: web sitesinden giriş de bu hesaba bağlanır.** `web/account/` sayfası aynı Discord hesabıyla giriş yapar ve
`/v1/me`'yi çağırır — bu da (masaüstü gibi) bir "cihaz" sayılır. Lisansın `max_devices` değeri 1 ise (varsayılan),
bir kullanıcı önce masaüstünde giriş yapıp sonra siteye girerse site "cihaz sınırına ulaşıldı" görebilir (hesap/tier
bilgisi yine görünür, yalnız yetki belgesi verilmez — sitenin zaten ihtiyacı olmayan bir alan). Bunu bir sorun olarak
görürseniz admin panelinden o lisansın `max_devices`'ını artırabilir ya da "Cihazı sıfırla" diyebilirsiniz.

## Topluluk görevleri (5.1.8)

Oyuncular canlı çeviriyi açıkken bir görev paneline (harita → Projeler, Ödül avları, Görevlendirmeler) bakınca program
görevi tanır ve oyuncu izin verdiyse yalnız görev yazısını ve Türkçe çevirisini `POST /v1/tasks`'a gönderir (`server/tasks.js`).

- Görev kimliği sunucuda hesaplanır (başlık + hedef). Aynı oyuncu bir görevi bir kez sayılır.
- **Eşik:** bir görev en az `TASKS_MIN_REPORTERS` (varsayılan 2) farklı oyuncudan gelince `GET /v1/tasks/live`'a girer;
  Türkçe çeviri de en az 2 oyuncudan aynı geldiyse ya da yönetici düzelttiyse yayınlanır. Süresi dolan (günlük/haftalık
  sıfırlama) görevler listeden düşer; ham kayıtlar 90 gün sonra silinir.
- **Yalnız sen görürsün:** Rapor Paneli → 👥 Topluluk görevleri sekmesi (aynı yönetici belirteci): tüm görevler, kaç
  oyuncudan geldiği, farklı metin/çeviri hâlleri; gizle ve Türkçe düzelt. Sunucu ayrıca her gün özel depoya
  (`REPORTS_REPO`) `tasks/<gün>.json` dökümü yazar — bunun için `GITHUB_TOKEN`'ın o depoda **Contents: Read and write**
  izni olmalı (yoksa döküm atlanır, panel yine çalışır).
- **Herkese açık liste:** `.github/workflows/tasks-live.yml` saatte bir `meta/tasks_live.json`'u günceller; program önce
  sunucudan, olmazsa bu dosyadan okur.
- Tablolar ilk istekte kendiliğinden oluşur; güncellemek için yalnız `npx wrangler deploy` yeterli.
- İsteğe bağlı değişkenler: `TASKS_MIN_REPORTERS` (2), `TASKS_PER_HOUR` (60), `TASKS_KEEP_DAYS` (8).

## Mobil companion bulut altyapısı (Faz 2 — devam ediyor, bkz. `../docs/mobile_companion_roadmap.md`)

Masaüstü hesabı (yukarıdaki Discord girişi, `Authorization: Bearer <oturum>`) ile telefon arasında kısa ömürlü bir
kodla eşleştirme; telefon asla masaüstüne doğrudan bağlanmaz, her şey bu Worker üzerinden gider.

| Yol | Ne | Erişim |
|---|---|---|
| `POST /v1/mobile/pairings` | 5 dakika geçerli, tek kullanımlık eşleştirme kodu üretir | masaüstü oturumu |
| `POST /v1/mobile/pairings/claim` | `{code, platform}` → telefonun kendi `device_id`/`token`'ı | herkese açık, oran sınırlı |
| `GET /v1/mobile/dashboard` | masaüstü çevrimiçi mi, son durum olayı | telefon oturumu (`Bearer <token>`) |
| `GET /v1/mobile/desktop/inbox` | kuyruktaki izin verilen komutları alır (teslim edildikten sonra bir daha gelmez) | masaüstü oturumu |
| `POST /v1/mobile/desktop/events` | `{type, ...}` küçük durum JSON'u (ekran görüntüsü/dosya YOK) | masaüstü oturumu |
| `POST /v1/mobile/desktop/commands` | `{command}` — yalnız `scan_start`/`scan_stop` (allow-list) | telefon oturumu |
| `GET/PUT /v1/mobile/builds` | telefonun kendi build kütüphanesi, `base_revision` ile çakışma kontrolü | telefon oturumu |
| `PUT/DELETE /v1/mobile/push-tokens/{device_id}` | APNs/FCM belirteci kaydet/sil | telefon oturumu |
| `GET /v1/mobile/devices` | masaüstünün kendi eşleştirdiği telefonları listeler (iptal için gereken `device_id`'ler) | masaüstü oturumu |
| `DELETE /v1/mobile/devices/{device_id}` | bir telefonu iptal et | masaüstü oturumu |
| `DELETE /v1/mobile/builds/{client_id}` | bir build'i siler (tombstone: `deleted:true`, diğer cihazlar senkronda görür) | telefon oturumu |
| `DELETE /v1/mobile/me`, `DELETE /v1/me` | hesap silme talebi (telefon/masaüstü) — oturumlar hemen iptal, asıl veri 24 saat bekleme sonrası `scheduled()` görevinde gerçekten silinir | ilgili oturum |

**Push bildirimi (Faz 4):** Hem Android hem iOS için gerçek gönderim var (`mobile.js` → `sendPush()`).
- **Android:** FCM HTTP v1, Firebase Admin SDK servis hesabı JWT'siyle (`fcmAccessToken()`). Secret:
  `npx wrangler secret put FCM_SERVICE_ACCOUNT_JSON` (indirilen servis hesabı JSON dosyasının TAMAMI). **Production'a deploy edildi (2026-11-03).**
- **iOS:** APNs HTTP/2 + JWT (token tabanlı kimlik doğrulama), `.p8` Auth Key ile ES256 imzalı provider token
  (`apnsProviderJwt()`). Secret'lar: `npx wrangler secret put APNS_AUTH_KEY_P8` (indirilen `.p8` dosyasının
  TAMAMI), `APNS_KEY_ID`, `APNS_TEAM_ID` (Apple Developer Program hesabından); `APNS_BUNDLE_ID` gizli değil,
  `wrangler.toml`'daki `[vars]` içinde zaten tanımlı. **Henüz deploy edilmedi** — Apple Developer Program kaydı
  (kullanıcının kendisinin yapması gereken, ücretli bir adım) henüz tamamlanmadı; adımlar için
  `docs/mobile_companion_roadmap.md`'ye bakın.

Her iki platform da kendi secret/değişken seti tanımlı değilse BAĞIMSIZ olarak sessizce no-op'tur ("çalışıyor"
gibi göstermez); `PUT /push-tokens` yanıtı bunu `delivery: "available"` / `"not_yet_implemented"` ile açıkça söyler.

Tablolar `schema.sql`'de (`mobile_pairings`, `mobile_devices`, `desktop_inbox`, `desktop_status`, `push_tokens`,
`mobile_builds`, `account_deletions`); `npx wrangler d1 execute td2stats --remote --file schema.sql` ile var olan
veritabanına eklenir (CREATE TABLE IF NOT EXISTS — mevcut tabloları etkilemez). Test: `node server/test_mobile.mjs`
(44 test — FCM/RS256 ve APNs/ES256 imzaları gerçek test anahtar çiftleriyle doğrulanarak test edilir, ağa hiç çıkılmaz).

## Sürüm sayacı ve yönetici özeti (6.0.1)
- Program `/v1/tasks/live` isteğinde sürümünü User-Agent'ta bildirir (`TD2LootAdvisor/6.0.1`); açılıştaki ilk istekte
  `x-td2-run: start` başlığı da gelir. Sunucu yalnız `usage_daily (gün, sürüm, açılış, yoklama)` sayaçlarını tutar —
  IP, hesap, cihaz ya da kimlik yok. 400 günden eski sayaçlar saatlik bakımda silinir. Daha eski sürümler sayılmaz.
- `GET /v1/admin/overview[?since=<unix>]` (Admin belirteci): Rapor Paneli'nin Gösterge sekmesi ve bildirimleri için tek
  çağrı — sürüm dağılımı (7 gün), günlük açılış (30 gün), hesap/lisans sayıları, bekleyen öneriler, görev durumu, kuyruktaki
  raporlar, saatlik bakımın son çalışması (`cron_last`) ve `since` sonrası olay sayıları.
- Test: `node server/test_overview.mjs`
