# Devir Notu (bir sonraki oturum/geliştirici/AI için)

Son güncelleme: 2026-11-14 — bu oturum (cloud sandbox, session `019puJcpmi1mPj3qdczCYr6K`), Xbox
Companion CI'yi yeşile çekti, bir özellik yol haritası teslim etti ve **kritik bir senkronizasyon
sorunu** buldu (aşağıya bakın — bir sonraki oturumun/geliştiricinin ilk okuması gereken kısım bu).

## ⚠️ En önemli açık konu: iki ayrı, senkronize olmayan çalışma kolu var

Bu depo (`FEDERALTURK/td2-loot-advisor`, bu oturumun çalıştığı **bulut** klonu) ile kullanıcının
kendi Windows bilgisayarındaki **yerel** `C:\Users\PC\Desktop\Thedivision2program` klasörü artık
aynı şey değil:

- Kullanıcı bu oturuma bir "Claude Code → Codex" devir belgesi (`claude_to_codex_handoff.md`)
  paylaştı. O belge, yerel klasörde Android Companion imzalama/FCM/overlay işi yapan **başka bir
  AI oturumunun**, işi "Codex" adlı bir ajana devrettiğini anlatıyor.
- O belgedeki son yerel commit (`6fea365 fix: restrict companion installer paths`) **bu bulut
  deposunun git geçmişinde hiç yok** (doğrulandı: `git log --oneline --all | grep 6fea365` → 0
  sonuç).
- Android GitHub-beta imzalama için yerel kolun kullandığı secret isimleri (`ANDROID_KEYSTORE_BASE64`/
  `ANDROID_KEYSTORE_PASSWORD`/`ANDROID_KEY_ALIAS`/`ANDROID_KEY_PASSWORD`, yerel betik
  `scripts/build_signed_companion.ps1`) bu depoda kurulu olan şemadan (`TD2_BETA_KEYSTORE_BASE64`/
  `TD2_BETA_KEYSTORE_PASSWORD`/`TD2_BETA_KEY_ALIAS`, bkz. `docs/mobile_beta_signing_tr.md`,
  `.github/workflows/build-mobile.yml`) **farklı**. Aynı fiziksel keystore (`td2-companion-beta.jks`,
  aynı alias `td2-companion-beta`, aynı SHA256 fingerprint `B1:FD:54:C8:...:BA`) olması çok muhtemel
  ama hangi `build-mobile.yml`/secret şemasının kalıcı kabul edileceği **kullanıcı kararı bekliyor**.
- **Hiçbir AI oturumu bu iki kolu henüz birleştirmedi.** Bu depoda kod/secret değişikliği yapmadan
  önce kullanıcıya sorulmalı: hangi yerel değişiklikler hâlâ sadece
  `C:\Users\PC\Desktop\Thedivision2program`'da duruyor, bu depoya (bulut klonuna) push edilmiş mi,
  yoksa bu depo o yerel klasörün üstüne mi kopyalanmalı? Bu netleşmeden Android imzalama/mobile
  companion üzerinde yeni iş yapmak, iki kolun birbirini ezmesi riskini taşır.
- Ayrıntı ve bulgunun tam kaydı: `ROADMAP.md` → "Şu an aktif" bölümü ve "Diğer açık kalemler".

## Bu oturumda tamamlanan iş

1. **Xbox Companion (UWP) CI, 13 denemenin sonunda tamamen yeşile çekildi** (`run 43622873860`,
   `success`, commit `377b441`→`origin/main`). Kök neden zinciri: `setup.exe modify`'de zorunlu
   `--channelId` eksikliği → PowerShell `Start-Process -ArgumentList`'in boşluklu `--installPath`
   değerini otomatik tırnaklamaması (asıl kök neden) → `setup.exe`'nin tanımadığı `--log` bayrağı →
   Windows10SDK.19041'in runner'da sessizce kurulamaması (→ `TargetPlatformVersion` zaten kurulu
   `10.0.26100.0`'a çekildi) → `AppContainerExe`'nin otomatik APPX imzalama tetiklemesi (→
   `/p:AppxPackageSigningEnabled=false`). Son çalıştırmada gerçek `.msix` üretildi, sıfır hata.
   Bu workflow hâlâ sadece derleme doğrulaması yapıyor (paketleme/gerçek Xbox dağıtımı kapsam dışı).
   Ayrıntı: `.github/workflows/build-xbox.yml` içindeki Türkçe yorumlar, `ROADMAP.md`.
2. **Özellik taraması + geliştirme yol haritası teslim edildi**: `docs/feature_roadmap_2026-11-14.md`.
   Ekran okuma (F8 eşya tarama) / tanımlama (gamedata eşleştirme) / çeviri (i18n + görev çevirisi +
   canlı çeviri F6 — üç ayrı alt-sistem) kod düzeyinde tanımlandı; doğrudan "gereksiz" kanıtlanmış
   bir özellik yok, ama üç örtüşen Xbox/konsol girişiminin (statik UWP ref app, mobil Xbox
   doğrudan-bağlantı, capture-card çevirisi) kullanıcı tarafından önceliklendirilmesi gerektiği
   not edildi. 5 fazlı bir sıra önerildi (temizlik → konsol stratejisi → mobil tamamlama →
   OCR/çeviri derinleştirme → topluluk veri → yayın altyapısı). Kod değişikliği yok.
3. **`td2-companion-beta.jks` parolası doğrulandı ve kullanıcıya bildirildi** (kullanıcının açık
   talebi üzerine). `docs/mobile_beta_signing_tr.md`'deki "store ve key parolası aynıdır" iddiası
   bu keystore için **yanlış** çıktı — `keytool -list -v -storepass` ile sadece bir dosyadaki
   (`store_password.txt`) değer gerçekten açıyor, diğeri (`key_password.txt`) açmıyor. Doküman
   düzeltilmedi (sadece kullanıcıya bildirildi) — bir sonraki oturum isterse `docs/mobile_beta_signing_tr.md`
   satır 48'i düzeltebilir.

## Kullanıcıdan (Soner/DJVORLIX) beklenen kararlar

1. **Codex devir kolunun bu depoyla senkronizasyonu** — yukarıdaki "⚠️" bölümüne bakın. Hangi
   secret şeması (`TD2_BETA_*` vs `ANDROID_*`) kalıcı olacak, yerel değişiklikler bu depoya nasıl
   taşınacak?
2. **Üç örtüşen Xbox/konsol girişiminden hangisine öncelik verilsin** — `docs/feature_roadmap_2026-11-14.md`
   §3.1/§4 Faz 1.
3. **Kod imzalama** (SignPath yeniden başvuru / Azure Trusted Signing / imzasız devam) — `ROADMAP.md`'de
   bekliyor, değişmedi.
4. **`tests/test_knowledge.py` KeyError fixture'ı** — düşük risk, tek dosya, test kodu; kullanıcı
   onayı gerektirmiyor ama henüz hiçbir oturum düzeltmedi (bkz. `ROADMAP.md` "Diğer açık kalemler").
   Bir sonraki oturum bunu doğrudan düzeltebilir.
5. **PR #3** (`fix/desc-offline-fallback`) hâlâ `dirty` — rebase veya kapatma kararı bekliyor.

## Bir sonraki oturumun yapabileceği, teknik olarak hazır işler

- `tests/test_knowledge.py` fixture düzeltmesi (kök neden `ROADMAP.md`'de belgeli) — onay gerektirmez.
- Xbox Companion CI yeşile çekildiğine göre, istenirse gerçek bir Xbox konsolunda/uzak masaüstünde
  paket testi (hâlâ hiç denenmedi).
- Mobil companion push bildirimi uçtan uca gerçek cihaz testi (Android canlı, iOS kod hazır/APNs
  secret bekliyor) — **ama önce madde 1'deki senkronizasyon netleşmeli**, aksi halde hangi
  `build-mobile.yml`/secret üzerinde test edileceği belirsiz.

## Güvenlik/kısıt hatırlatmaları (tüm oturumlar için geçerli)

- Oyunun process/belleğine asla dokunulmaz (ReadProcessMemory/injection/packet sniffing/input
  automation yok).
- Gerçek sır/token/parola asla koda, commit mesajına veya bu türden devir belgelerine açık metin
  yazılmaz (`td2-companion-beta.jks` parolası bu kurala uyularak sadece doğrudan kullanıcı
  talebiyle, chat içinde, bir kerelik bildirildi — bu dosyaya veya başka bir belgeye yazılmadı).
- Public GitHub Release/tag/installer-APK yayını için AGENTS.md'deki onay sorusu zorunlu
  (`"Yeni Güncellemeyi Yayınlamak İster misiniz? (vX.Y.Z) — Evet / Hayır"`); kod/commit/push
  otonom yapılabilir.
- Belirsiz/geri alınamaz işlemlerden önce kullanıcıya sor; test etmeden "çalışıyor" denmez.
