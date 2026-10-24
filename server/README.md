# Topluluk istatistik sunucusu / Community stats server

Cloudflare Workers + D1 (ücretsiz katman yeterli). Uygulama düşüşleri buraya gönderir; premium kullanıcılar
"hangi aktivitede ne düşüyor" istatistiğini buradan okur. Sunucu IP saklamaz, istemci kimliğini tuzlu özetle tutar.

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

Kayıt biçimi ve doğrulama: `worker.js` (`cleanDrop`). Attribute değerleri alınmaz, yalnız türleri.

## Maliyet

Workers ücretsiz katmanı günde 100.000 istek, D1 ücretsiz katmanı 5 GB depolama ve günde 5 milyon satır okuma verir.
Uygulama düşüşleri 10 dakikada bir toplu gönderir; binlerce oyuncu için bile ücretsiz katman yeterlidir.
