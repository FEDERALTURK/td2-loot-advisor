# TD2 Raporları — Admin Paneli

Kullanıcıların gönderdikleri hata raporları ve istekleri GitHub issue'ları olarak görmek ve yönetmek için.

## Kurulum

### GitHub Ayarı

1. **Özel depo oluştur** (td2-loot-advisor-reports):
   ```bash
   gh repo create td2-loot-advisor-reports --private
   ```

2. **Fine-grained token oluştur** (Personal Access Tokens → Fine-grained):
   - Resource owner: your account
   - Repository access: Only select repositories → td2-loot-advisor-reports
   - Permissions:
     - Issues: Read and write
   - Token'ı kopyala (git credentials'a kaydet veya panel ayarlarında kullan)

3. **Cloudflare Worker ayarı** (varsa):
   - Worker environment variables:
     - `GITHUB_TOKEN`: yukarıdaki token
     - `REPORTS_REPO`: td2-loot-advisor-reports (owner/repo)
     - `ADMIN_LOGIN`: senin GitHub login'in (yanıtları göstermek için)

4. **Veritabanı migration** (node.js + D1):
   ```bash
   sqlite3 reports.db < server/schema.sql
   # veya D1'de `wrangler d1 execute reports < server/schema.sql`
   ```

5. **Worker'ı redeploy et**:
   ```bash
   wrangler deploy
   ```

### Paneli Çalıştır

```bash
python panel/panel.py
# veya Windows'ta: panel\panel.bat
```

Açılan pencerede:
- **Ayarlar** sekmesine git
- Repo: `owner/td2-loot-advisor-reports`
- Token: yukarıda oluşturduğun token
- API Base: (boş bırak) `https://api.github.com`
- Admin login: senin GitHub login'in
- **Raporlar** sekmesine geç, **Yenile** tuşuna bas

## Kullanım

**Raporlar** sekmesinde:
- Tür, durum ve açıklık filtresi ile raporları listele
- Raporu seç ve **Detay** sekmesinde oku
- **Yanıt Ekle**: geliştiricinin cevabını yaz (kullanıcının uygulamada görüneceği)
- **Etiket Ayarla**: `status:triaged`, `status:in-progress`, `status:done` vb. ekle
- **Kapat/Aç**: işlemi bitirince kapat
- **GitHub'da Aç**: tarayıcıda gerçek issue'yu gör

## Demo Modu (test)

Eğer test etmek istersen `tests/fake_github.py` var:

```bash
python tests/fake_github.py
```

Bu, gerçek GitHub'a bağlanmadan işleri simüle eder.
