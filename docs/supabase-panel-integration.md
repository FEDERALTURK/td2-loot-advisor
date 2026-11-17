# Supabase panel entegrasyonu — başlangıç durumu

## Oluşturulan proje

- Proje: `td2-loot-advisor-panel`
- Bölge: `eu-central-1`
- URL: `https://ukbbwubktohifdomhcks.supabase.co`
- Supabase MCP ile oluşturulma durumu: aktif/sağlıklı

Gerçek anahtarlar bu dosyaya yazılmaz. `SUPABASE_SERVICE_ROLE_KEY` yalnızca
sunucu tarafında, secret olarak tutulmalıdır.

## İlk migration'lar

1. `panel_observability_foundation`
   - `panel_error_reports`
   - `panel_usage_daily`
   - `panel_audit_logs`
2. `panel_observability_rls_guardrails`
   - RLS etkinleştirildi.
   - `anon` ve `authenticated` istemci rollerine varsayılan kapalı politikalar
     eklendi.
3. `panel_usage_daily_index_cleanup`
   - Çakışan unique/primary indeks düzeltildi.

Mevcut Cloudflare D1 şeması silinmedi ve D1 rapor kuyruğu kaynak sistem olarak
korundu. Worker'a isteğe bağlı, kapatılabilir bir Supabase aynalama katmanı
eklendi: `POST /v1/reports` başarılı biçimde D1'e yazıldıktan sonra yalnızca
maskelenmiş hata özeti `panel_error_reports` tablosuna en iyi çaba modeliyle
gönderilir. Supabase erişim hatası rapor yanıtını veya GitHub kuyruğunu bozmaz.

Yerel birim doğrulaması `server/test_supabase.mjs` içindedir. Gerçek service-role
anahtarı test fixture'ına veya istemciye eklenmez.

## Sonraki güvenli adım

Cloudflare'da secret tanımlandıktan sonra feature flag kontrollü canlı aynalama
etkinleştirilebilir. Kullanım sayaçları şimdilik D1'de kalır; eşzamanlı sayaç
üzerine yazma riskini önlemek için ayrı event/aggregate tasarımı yapılmadan
Supabase'e aktarılmaz.

## Canlı etkinleştirme durumu

Cloudflare hesabı yerelde doğrulandı ve `SUPABASE_SECRET_KEY` secret'ı güvenli
secret store'a tanımlandı. `SUPABASE_PANEL_ENABLED=true` ile Worker deploy edildi
ve canlı runtime testi başarıyla tamamlandı.

```powershell
cd server
npx wrangler secret put SUPABASE_SECRET_KEY
```

Girilecek değer Dashboard → Project Settings → API Keys → Secret keys
bölümündeki `sb_secret_...` değeridir. Eski `service_role` anahtarı varsa
geçici olarak `SUPABASE_SERVICE_ROLE_KEY` adıyla da çalışır.

Secret değeri sohbet, Git veya istemci paketlerine yazılmamalıdır. Canlı testte
`panel_mirror=enabled` görüldü, maskelenmiş test raporu Supabase'e yazıldı ve
doğrulama sonrası test satırı temizlendi.

- Tarayıcı paneli Supabase service-role anahtarını görmemeli.
- OCR görüntüleri ve ham ekran görüntüleri varsayılan olarak Supabase'e
  yüklenmemeli.
- Hata metinleri gönderilmeden önce maskeleme ve boyut sınırı uygulanmalı.
- RLS politikaları gerçek kullanıcı/admin kimlik modeli netleştirilmeden
  genişletilmemeli.
