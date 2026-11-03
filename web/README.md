# TD2 Loot Advisor — web sitesi

Tanıtım, haberler, premium ve hesap sayfalarından oluşan statik bir site (Cloudflare Pages). Hiçbir derleme adımı
yok — düz HTML/CSS/JS, doğrudan yayınlanabilir. Hesap sunucusuna (`server/`) çapraz-kaynak (CORS) ile bağlanır.

## Sayfalar

| Sayfa | Ne yapar |
|---|---|
| `index.html` | Tanıtım, özellik listesi, GitHub'ın son sürümünden otomatik indirme linkleri |
| `news/` | Oyun haberleri — uygulamanın kendi `news_cache.json`'ını (GitHub'dan ham) okur, aynı veri |
| `premium/` | Premium özellik listesi + Gumroad satın alma linki (ürün oluşturulunca `assets/js/config.js`'e eklenir) |
| `account/` | Discord ile giriş (web sürümü — masaüstüyle aynı hesap sistemi), lisans durumu, anahtar/davet kodu kullanma, hesap silme |

## Yerelde deneme

Herhangi bir statik dosya sunucusu yeterli, örn.:

```bat
cd web
python -m http.server 8080
```

Ama **hesap sayfası** gerçek sunucuya (`https://td2-stats.td2loot.workers.dev`) bağlanacağından Discord girişini
denemek için önce sunucuda `SITE_URL` değişkeninin sitenin gerçek adresine ayarlanmış ve yayınlanmış olması gerekir
(bkz. aşağıdaki "Kurulum" ve `server/README.md`). Sunucu tarafını uçtan uca (gerçek Discord'a çıkmadan) test etmek
için: `node web/test_web_account.mjs` — bu, `server/dev_server.mjs`'i arka planda başlatıp gerçek bir tarayıcıyla
(Playwright) tüm giriş/anahtar kullanma/çıkış/hesap silme akışını doğrular. Playwright kurulu değilse test sessizce
atlanır.

## Kurulum (bir kez, ~5 dakika)

Gerekenler: Node.js 18+ ve zaten kurulu olan Cloudflare hesabı (`server/` için kullanılan).

```bat
cd web
npx wrangler login                                    :: zaten giriş yaptıysan atla
npx wrangler pages project create td2-loot-advisor     :: adres: https://td2-loot-advisor.pages.dev
npx wrangler pages deploy . --project-name=td2-loot-advisor
```

Yayınlanan adres `server/wrangler.toml`'daki `SITE_URL` ile **birebir aynı** olmalı (farklıysa dosyada güncelleyip
`cd ../server && npx wrangler deploy` ile sunucuyu yeniden yayınla — yoksa web girişi "login not configured" hatası
verir).

Güncelleme (kod her değiştiğinde): `cd web && npx wrangler pages deploy .` yeterli — proje zaten var, yeniden
oluşturmaya gerek yok.

### Kendi alan adın varsa

Cloudflare Pages panelinden (Workers & Pages → td2-loot-advisor → Custom domains) alan adını bağla, sonra
`server/wrangler.toml`'daki `SITE_URL`'i o adrese güncelleyip sunucuyu yeniden yayınla.

## Premium satın alma (Gumroad)

1. [gumroad.com](https://gumroad.com) üzerinde bir ürün oluştur; **"Generate a unique license key per sale"**
   seçeneğini aç (Gumroad'un kendi "Licensing" özelliği — her satış için otomatik, doğrulanabilir bir anahtar
   üretir).
2. Ürünün **Product ID**'sini al (Gumroad panelinde ürün ayarlarında) → sunucuya gizli olmayan bir değişken
   olarak: `server/wrangler.toml` → `[vars]` → `GUMROAD_PRODUCT_ID = "..."`, sonra `npx wrangler deploy`.
   (Sunucu kodu zaten hazır — `server/accounts.js`'teki `/v1/license/redeem` ucu bu anahtarı otomatik doğrular.)
3. Ürünün satış sayfası linkini `web/assets/js/config.js` → `GUMROAD_URL`'e yapıştır, siteyi yeniden yayınla.
   Premium sayfası "yakında" yazısını otomatik olarak gerçek "Satın al" düğmesiyle değiştirir.

## Çok dillilik

Site şimdilik yalnız TR/EN (`assets/js/i18n.js`). Uygulamanın kendisi 10 dili destekliyor (`lang/*.json`) — siteye
yeni bir dil eklemek için `i18n.js`'teki `STRINGS` nesnesine aynı anahtarlarla bir dil daha eklemek ve
`index.html`/`news/index.html`/`premium/index.html`/`account/index.html`'deki dil düğmeleri satırına
`<button class="td2-lang-btn" data-lang="de">DE</button>` gibi bir düğme eklemek yeterli.

## Hesap sunucusuyla ilişki

Bu site, uygulamanın zaten kullandığı Cloudflare Worker'a (`server/`) bağlanır — **ayrı bir hesap sistemi değil**.
Web sitesinden giriş yapan biri, masaüstü uygulamasındaki hesabın AYNISINI görür (aynı Discord hesabı → aynı
`account_id`). Teknik ayrıntı ve önemli bir not (web girişi de bir "cihaz" sayılır) için: `server/README.md` →
"Hesap sistemi" bölümü.
