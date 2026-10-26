# Topluluk istatistik sunucusu / Community stats server

Cloudflare Workers + D1 (ücretsiz katman yeterli). Uygulama düşüşleri buraya gönderir; premium kullanıcılar
"hangi aktivitede ne düşüyor" istatistiğini buradan okur. Sunucu IP saklamaz, istemci kimliğini tuzlu özetle tutar.

## Yayındaki sunucu

`https://td2-stats.td2loot.workers.dev` (Cloudflare panelinden kuruldu: D1 `td2stats`, bağlama `DB`,
değişkenler `LICENSE_PUBKEY` ve gizli `HASH_SALT`). Uygulamanın varsayılan adresi budur (`dropstats.DEFAULT_URL`).
Kod güncellemesi: Workers & Pages → td2-stats → Edit code → `worker.js` içeriğini yapıştır → Deploy.

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
| `POST /v1/auth/start` · `GET /v1/auth/callback` · `POST /v1/auth/token` | Discord girişi (PKCE + 127.0.0.1 dönüşü) | herkese açık, oran sınırlı |
| `GET /v1/me` | hesap, lisans, 7 günlük imzalı yetki belgesi (TD2E) | `Authorization: Bearer <oturum>` |
| `POST /v1/license/redeem` | `TD2K-…` anahtar, `TD2I-…` davet, Gumroad anahtarı | oturum; saatte 10 deneme |
| `POST /v1/auth/logout` | oturumu kapat | oturum |
| `/v1/admin/*` | hesaplar, lisanslar, davetler, denetim, istatistik | `Authorization: Admin <ADMIN_TOKEN>` |

Güvenlik: oturum belirteçleri, anahtarlar ve davet kodları veritabanında yalnız SHA-256 özetleriyle durur; düz anahtar
yalnız üretildiği an panelde görünür. Bir lisans tek bilgisayara bağlanır (panelden "Cihazı sıfırla"). Yetki belgesi
bilgisayara bağlıdır ve 7 gün internetsiz geçerlidir. Testler: `node test_accounts.mjs`, `python ../tests/test_account.py`.

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

## Sürüm sayacı ve yönetici özeti (6.0.1)
- Program `/v1/tasks/live` isteğinde sürümünü User-Agent'ta bildirir (`TD2LootAdvisor/6.0.1`); açılıştaki ilk istekte
  `x-td2-run: start` başlığı da gelir. Sunucu yalnız `usage_daily (gün, sürüm, açılış, yoklama)` sayaçlarını tutar —
  IP, hesap, cihaz ya da kimlik yok. 400 günden eski sayaçlar saatlik bakımda silinir. Daha eski sürümler sayılmaz.
- `GET /v1/admin/overview[?since=<unix>]` (Admin belirteci): Rapor Paneli'nin Gösterge sekmesi ve bildirimleri için tek
  çağrı — sürüm dağılımı (7 gün), günlük açılış (30 gün), hesap/lisans sayıları, bekleyen öneriler, görev durumu, kuyruktaki
  raporlar, saatlik bakımın son çalışması (`cron_last`) ve `since` sonrası olay sayıları.
- Test: `node server/test_overview.mjs`
