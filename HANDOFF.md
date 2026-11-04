# Devir Notu (bir sonraki oturum/geliştirici/AI için)

Son güncelleme: bu dosyayı güncelleyen oturumun yaptığı iş — 9.1.5.19 yayını sonrası ek sağlamlaştırma turu.

## Şu an nerede kalındı

- **Yayınlanmış, canlı sürüm**: `v9.1.5.19` (GitHub Releases, `main` dalından, installer `.exe` + taşınabilir `.zip` + `SHA256SUMS`).
- **Dal durumu**: `main` güncel ve tek doğru kaynak; `master` içerik olarak `main`'e tamamen merge edildi ama GitHub'da hâlâ siliniyor değil (aşağıdaki "kullanıcı işlemi gerekli" kısmına bak).
- **Bu turda eklenenler**: `tests/test_regression_crash_patterns.py` (9.1.5.19'daki iki çökme hatasının statik-analiz koruması), `DEVELOPMENT_LOG.md`, `BUGS.md`, `TESTING.md`, `DEPENDENCIES.md`, bu dosya.

## Kullanıcıdan (Soner/DJVORLIX) beklenen işlemler

1. ✅ **`master` dalı silindi (2026-11-04, kullanıcı tarafından).** Doğrulandı. İsteğe bağlı küçük temizlik: `archive/master-superseded-2026-11-03` (aynı eski commit'e işaret eden yedek dal) ve `deploy/worker-bundle-temp` (kendi commit mesajında "will be removed" diyen geçici dal) hâlâ repoda duruyor, hiçbir aktif işe bağımlılıkları yok.
2. ✅ **mxswat lisans gri alanı — çözüldü (2026-11-04, kullanıcı kararı).** `recal_advisor` `free` yapılarak sorun kökünden çözüldü (bkz. `LICENSE_NOTES.md`, `BUGS.md` #2). [mxswat/mx-division-builds#153](https://github.com/mxswat/mx-division-builds/issues/153) nezaketen açık bırakıldı ama artık bekleyen bir karar yok; yanıt gelirse yalnızca bilgi amaçlı not düşülür.
3. ✅ **Tanıtım videoları — GitHub Release'e yayınlandı (2026-11-04, kullanıcı tarafından).** `td2_promo_en_1080p.mp4` ve `td2_promo_tr_1080p.mp4` v9.1.5.20 (latest) release notlarına eklendi. Dikey (Shorts/Reels) versiyonları ve YouTube paylaşımı hâlâ isteğe bağlı.
4. **SignPath Foundation — reddedildi (2026-11-03).** Gerekçe kamuya görünürlük eşiği (GitHub star/fork, dış
   referans, sürekli aktivite) — proje kalitesiyle ilgisiz. Kullanıcıdan karar bekleniyor: yeniden başvuru
   (görünürlük arttıktan sonra, ücretsiz) mu, ücretli bir sağlayıcıya (SignPath ücretli abonelik / Azure Trusted
   Signing / geleneksel OV sertifika) mı geçilsin, yoksa şimdilik imzasız mı devam edilsin. Ayrıntı: `ROADMAP.md`.

## Bir sonraki oturumun yapabileceği, teknik olarak hazır işler

- ✅ **Gerçek Windows testi yapıldı (2026-11-04).** Bağlı Windows bilgisayarında (win32, `mcp__remote-devices__get_device_info` ile doğrulandı, `device_bash`/shell yok ama computer-use var) uygulama v9.1.5.20 olarak açıldı ve üç senaryo tıklanarak doğrulandı: Ansiklopedi "Wiki'de aç" düğmesi, Ayarlar → Sürüm geçmişi, Tanılama Merkezi → "Sorunları tara" (hata bildirimi yolu). Üçünde de çökme olmadı. Ayrıntı: `DEVELOPMENT_LOG.md`, `BUGS.md` #5 (artık ✅). Küçük, ayrı bir gözlem: Sürüm geçmişi penceresinin içerik listesi boş kaldı — çökmeyle ilgisiz, kök nedeni henüz araştırılmadı.
- **mobile/ (Flutter) ve server/ (Node.js/Cloudflare Workers) testleri hiç çalıştırılmadı** — ikisi de bu depoda mevcut, ayrı bir oturumda ele alınabilir.

## Güvenlik/kısıt hatırlatmaları (tüm oturumlar için geçerli)

- Oyunun process/belleğine asla dokunulmaz (ReadProcessMemory/injection/packet sniffing/input automation yok) — her oturumda `git grep` ile yeniden doğrulanmalı.
- Gerçek sır/token asla koda/commit'e girmez.
- Panel PIN kilidi Windows'un kendi şifresine asla bağımlı olmamalı.
- Belirsiz/geri alınamaz/public GitHub işlemlerinden önce kullanıcıya sor.
- Test etmeden "çalışıyor" denmez; sahte test sonucu raporlanmaz.
