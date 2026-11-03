# Devir Notu (bir sonraki oturum/geliştirici/AI için)

Son güncelleme: bu dosyayı güncelleyen oturumun yaptığı iş — 9.1.5.19 yayını sonrası ek sağlamlaştırma turu.

## Şu an nerede kalındı

- **Yayınlanmış, canlı sürüm**: `v9.1.5.19` (GitHub Releases, `main` dalından, installer `.exe` + taşınabilir `.zip` + `SHA256SUMS`).
- **Dal durumu**: `main` güncel ve tek doğru kaynak; `master` içerik olarak `main`'e tamamen merge edildi ama GitHub'da hâlâ siliniyor değil (aşağıdaki "kullanıcı işlemi gerekli" kısmına bak).
- **Bu turda eklenenler**: `tests/test_regression_crash_patterns.py` (9.1.5.19'daki iki çökme hatasının statik-analiz koruması), `DEVELOPMENT_LOG.md`, `BUGS.md`, `TESTING.md`, `DEPENDENCIES.md`, bu dosya.

## Kullanıcıdan (Soner/DJVORLIX) beklenen işlemler

1. **`master` dalını sil.** AI oturumunun ortam politikası, hem `git push --delete master` hem GitHub API `DELETE /git/refs/heads/master` çağrısını "proxy üzerinden yazma erişimine izin verilmiyor" diyerek engelliyor — bu, kullanıcı onayıyla bile aşılamayan sabit bir kısıtlama (iki farklı AI oturumunda iki farklı yöntemle doğrulandı). Kullanıcı GitHub Settings → Branches'tan, ya da kendi makinesinden `git push origin --delete master` ile, ya da Actions → `retire-releases.yml`'i `branches: master` girdisiyle manuel tetikleyerek silebilir.
2. **mxswat'a lisans sorusu — açıldı, yanıt bekleniyor.** [mxswat/mx-division-builds#153](https://github.com/mxswat/mx-division-builds/issues/153) (2026-11-03, kullanıcının kendi GitHub oturumuyla, PC üzerinden tarayıcı otomasyonuyla gönderildi — bkz. `LICENSE_NOTES.md`). Yanıt gelince `LICENSE_NOTES.md`'deki "Durum" bölümü ve `recal_advisor`'ın kapsamı buna göre güncellenmeli.
3. **Tanıtım videoları — render edildi (2026-11-04), teslim edildi.** Private `td2-loot-advisor-reports`'taki `promo` pipeline'ı çalıştırıldı, 4 video (EN/TR × yatay 1920×1080/dikey 1080×1920, ~60-66sn) üretildi ve sohbet üzerinden kullanıcıya gönderildi. Kullanıcı: videoları izle, uygun bulursan README'ye göm / GitHub Release'e ekle / YouTube'a yükle — hangisini istersen sen karar ver.
4. **SignPath Foundation — reddedildi (2026-11-03).** Gerekçe kamuya görünürlük eşiği (GitHub star/fork, dış
   referans, sürekli aktivite) — proje kalitesiyle ilgisiz. Kullanıcıdan karar bekleniyor: yeniden başvuru
   (görünürlük arttıktan sonra, ücretsiz) mu, ücretli bir sağlayıcıya (SignPath ücretli abonelik / Azure Trusted
   Signing / geleneksel OV sertifika) mı geçilsin, yoksa şimdilik imzasız mı devam edilsin. Ayrıntı: `ROADMAP.md`.

## Bir sonraki oturumun yapabileceği, teknik olarak hazır işler

- **Gerçek Windows testi artık mümkün**: Bu oturumda `C:\Users\PC\Desktop\Thedivision2program` klasörünün bağlı bir Windows bilgisayarına (win32, `mcp__remote-devices__get_device_info` ile doğrulandı) erişim olduğu görüldü. O makinede `device_bash` yok (shell erişimi yok), ama **computer-use** (ekran görüntüsü + tıklama/klavye) ile uygulama gerçekten açılıp Tanılama Merkezi, Ansiklopedi "Kaynağı aç" düğmeleri ve Sürüm Geçmişi ekranı manuel olarak tıklanarak 9.1.5.19 düzeltmeleri gerçek Windows'ta görsel olarak doğrulanabilir. Bu, "Linux+Xvfb testi geçti ama gerçek Windows'ta doğrulanmadı" boşluğunu kapatır (bkz. BUGS.md #5).
- **mobile/ (Flutter) ve server/ (Node.js/Cloudflare Workers) testleri hiç çalıştırılmadı** — ikisi de bu depoda mevcut, ayrı bir oturumda ele alınabilir.

## Güvenlik/kısıt hatırlatmaları (tüm oturumlar için geçerli)

- Oyunun process/belleğine asla dokunulmaz (ReadProcessMemory/injection/packet sniffing/input automation yok) — her oturumda `git grep` ile yeniden doğrulanmalı.
- Gerçek sır/token asla koda/commit'e girmez.
- Panel PIN kilidi Windows'un kendi şifresine asla bağımlı olmamalı.
- Belirsiz/geri alınamaz/public GitHub işlemlerinden önce kullanıcıya sor.
- Test etmeden "çalışıyor" denmez; sahte test sonucu raporlanmaz.
