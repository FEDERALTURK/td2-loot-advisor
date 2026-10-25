# TD2 Raporlama Sistemi — Kurulum Rehberi

Kullanıcılar, programdan doğrudan hata raporu ve istekleri gönderebilecekler. Bu sistem:
- **Uygulama içi geri bildirim penceresi** (app.py'de `open_feedback`)
- **Cloudflare Worker relay** (sunucuda `worker.js`)
- **Özel GitHub deposu** (`td2-loot-advisor-reports`)
- **Admin paneli** (rapor yönetimi için)

## Adım 1: GitHub Yapısı

### 1.1 Özel Depo

```bash
gh repo create td2-loot-advisor-reports --private --description "TD2 raporları (dahili)"
```

### 1.2 Fine-Grained Token

https://github.com/settings/personal-access-tokens/new

- **Token name:** TD2 Reports
- **Expiration:** 90 days
- **Resource owner:** Your account
- **Repository access:** Only select repositories → `td2-loot-advisor-reports`
- **Permissions:**
  - `Issues`: Read and write
  - `Commit statuses`: Read-only (isteğe bağlı)

Token'ı kopyala ve yerel bir yerde sakla (henüz projede yok).

## Adım 2: Cloudflare Worker

Eğer Cloudflare + D1 kullanıyorsan:

```bash
# Depo klonla (varsa)
# cd td2-dropstats-worker  (veya worker repo'nun yolu)

# 1. Veritabanını hazırla
wrangler d1 create reports  # veya adını `reports` yap

# 2. Schema'yı uygula
wrangler d1 execute reports --file=../td2-loot-advisor/server/schema.sql

# 3. wrangler.toml'de environment variables:
# [env.production]
# vars = {
#   GITHUB_TOKEN = "ghp_...",
#   REPORTS_REPO = "owner/td2-loot-advisor-reports",
#   ADMIN_LOGIN = "senin_github_adın",
#   HASH_SALT = "random_string"
# }

# 4. Redeploy
wrangler deploy --env production
```

**URL not:** `/v1/reports` endpoint'ine ulaşabileceğin URL'i not et (örn. `https://td2-reports.example.workers.dev`).

## Adım 3: Uygulamada Ayarı

`app.py`'de `_fb_url()` fonksiyonu, rapor sunucusunu bulur:

```python
def _fb_url():
    return (os.environ.get("TD2_REPORT_URL") or
            self.app_settings.get("report_server") or
            self.app_settings.get("drop_server") or
            dropstats.DEFAULT_URL)
```

Ayarla:
1. **Windows:** Ortam değişkeni `TD2_REPORT_URL=https://...`
   ```batch
   setx TD2_REPORT_URL https://td2-reports.example.workers.dev
   ```

2. **veya** Uygulamada: Ayarlar → Report sunucusu → `https://...`

3. **veya** `dropstats.DEFAULT_URL`'yi güncelle (varsayılan fallback)

## Adım 4: Admin Paneli

```bash
# Git repo'nda
python panel/panel.py
# veya Windows'ta: panel\panel.bat
```

Panelde ayarlar:
- **Repo:** `senin_adın/td2-loot-advisor-reports`
- **Token:** yukarıda oluşturduğun fine-grained token
- **API Base:** (boş bırak, varsayılan kullan)
- **Admin login:** senin GitHub login'in

## Adım 5: Test Et

### Test Modu (gerçek GitHub olmadan)

```bash
# Sahte sunucu başlat (başka terminal)
python tests/fake_github.py

# Uygulamada
# TD2_REPORT_URL=http://127.0.0.1:8888 python app.py

# Geri bildirim penceresini aç ve bir rapor gönder
# Panel'de raporu gör (aynı terminal'de)
```

### Canlı Test

1. Uygulamayı çalıştır (Cloudflare URL'i ayarlanmış)
2. Geri bildirim penceresini aç (`🐞 Geri Bildirim` düğmesi)
3. Rapor gönder
4. Panel'i aç ve "Yenile" tuşuna bas
5. Rapor görünmeli
6. **Yanıt Ekle** ile bir cevap yaz
7. Uygulamada "Raporlarım" sekmesine git ve yanıtı gör

## Yapılandırma Dosyaları

### Uygulamada saklanacak ayarlar

`~/.td2/settings.json` (veya `%APPDATA%\TD2\settings.json`):
```json
{
  "report_server": "https://...",
  "fb_contact": "discord_adı"
}
```

### Admin Panelinde

`~/.td2_admin_panel.json` (veya `%APPDATA%\td2_admin_panel.json`):
```json
{
  "repo": "senin_adın/td2-loot-advisor-reports",
  "token": "ghp_...",
  "api": "https://api.github.com",
  "admin_login": "senin_adın"
}
```

## Kararlaştırma: Rapor Durumları

Panel'deki etiketler:
- `status:new` — yeni rapor (varsayılan)
- `status:triaged` — okundu, triage edildi
- `status:in-progress` — üzerinde çalışılıyor
- `status:done` — tamamlandı
- `status:wontfix` — yapılmayacak
- `status:duplicate` — mükerrer
- `status:closed` — kapatıldı (issue state = closed)

## Sorun Giderme

**Panel'de rapor görünmüyor:**
- Token'ı kontrol et (Settings sekmesinde yazılı mı?)
- GitHub'da özel depo var mı?
- Token'da `Issues: Read and write` izni var mı?

**Uygulamada yanıt görünmüyor:**
- Report URL'i doğru mü? (`TD2_REPORT_URL` env var'ını kontrol et)
- Worker endpoint'i çalışıyor mı? (URL'i tarayıcıda aç: `https://.../v1/reports/status?client=test&ids=1`)

**"Bağlantı yok" mesajı:**
- Rapor sonra otomatik gönderilecek, `reports_queue.json`'da bekleme durumunda
- Bağlantı gelince panel **Yenile** tuşunda **Gönderilmeyi Bekliyor (n)** diye yazacak

## Güvenlik Notları

- Token'ı asla git'e commit etme, `.gitignore`'a ekle
- Panel ayarları lokal bilgisayarda saklanıyor (uygulama klasörüne değil)
- Raporlar, kullanıcının Windows adı / lisans anahtarı / e-postası temizlenmiş olarak GitHub'a gidiyor
- Sistem bilgisi ve log dosyası yalnız kullanıcı seçerse ekleniyor

## Yapı Özeti

```
td2-loot-advisor/
├── app.py                 # Geri bildirim penceresi eklendi
├── reports.py             # Rapor oluştur / gönder / depo
├── panel/
│   ├── panel.py           # Admin GUI
│   ├── github_api.py      # GitHub istemcisi
│   ├── panel.bat          # Windows launcher
│   ├── README.md          # Panel kullanımı
│   └── SETUP.md           # (bu dosya)
├── server/
│   ├── worker.js          # Cloudflare Worker (rapor relay)
│   ├── schema.sql         # D1 veritabanı şeması
│   └── test_reports.mjs   # Worker testleri
├── tests/
│   ├── fake_github.py     # Sahte sunucu (test için)
│   └── test_reports_panel.py  # Rapor sistemi testleri
└── meta/
    └── (rapor verileri GitHub'da, lokal repo'da değil)
```

## Sonraki Adımlar

1. ✅ Rapor sistemi ve panel kodları hazır
2. **TODO:** Windows CI'da video kaydı: geri bildirim → rapor gönder → panel'de göster → yanıt ver
3. **TODO:** Uygulamayı 5.0.7 olarak yayınla (feedback sistemi ve panel dahil)

---

**Sorun veya soru?** admin_login'de issue açabilirsin veya GitHub'dan `@senin_adın` etiketleyin.
