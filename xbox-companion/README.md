# TD2 Loot Advisor — Xbox Companion (DENEYSEL, statik referans uygulaması)

## Bu nedir, ne değildir

Bu, Konsol Modu'nun (`mobile/lib/console/`) telefon-kamerası yaklaşımından
**tamamen ayrı**, Xbox One/Series konsolunda **doğrudan çalışan** bir UWP
(Universal Windows Platform) uygulamasıdır. Kullanıcının Microsoft Partner
Center'a kayıtlı olması ve Xbox Live Creators Program üzerinden kendi
uygulamasını yayınlayabilmesi üzerine başlatıldı (2026-11-08).

**Ne yapar:** Pakete gömülü JSON verisinden (bkz. `XboxCompanion/Assets/data/`)
10 dilde görev çevirilerini ve popüler build özetlerini gösterir. Kullanıcı
Xbox'ta uygulamayı açar, dil seçer, görev/build listesine bakar.

**Ne YAPMAZ (kritik, kasıtlı sınır):**
- **Canlı ekran okuma veya overlay YOK.** Araştırma (2026-11-08) gösterdi ki
  Xbox, üçüncü taraf bir UWP/GDK uygulamasının başka bir çalışan oyunun
  ekranını okumasına veya üstüne gerçek bir overlay koymasına izin veren
  **hiçbir resmi API sunmuyor** — bu bir eksiklik değil, platformun bilinçli
  bir güvenlik/içerik-koruma kısıtı. Xbox, bir oyun açıldığında diğer
  uygulamaları askıya alıyor (Spotify/Discord gibi istisnalar yalnız sesle
  sınırlı). Yani gamecaptionapp'ın yaptığı "oyunun üstüne canlı çeviri
  bindirme" işini bu uygulama **yapamaz**.
- Veri **statik** — sürüm güncellemesiyle yenilenir, canlı senkronizasyon yok.
- Xbox Live servisi (başarımlar, arkadaş listesi vb.) **kullanmıyor** — Store
  Policy 10.13.1'e göre Creators Program başlıkları bunu gerektirmiyor, bu da
  ID@Xbox onayı beklemeden yayınlanabilmesini sağlıyor (araştırmaya göre; bkz.
  aşağıdaki "doğrulanmamış alanlar").

## Mimari

- **Dil:** C# / klasik UWP (Windows.UI.Xaml) — **WinUI 3 / Windows App SDK
  DEĞİL**. Xbox konsolları şu an için yalnız klasik UWP uygulamalarını
  çalıştırıyor.
- **JSON ayrıştırma:** WinRT'nin yerleşik `Windows.Data.Json` API'si — ek bir
  NuGet paketi (System.Text.Json vb.) gerektirmiyor, restore riskini azaltır.
- **Veri kaynağı:** `meta/tasks_feed.json` ve `meta/meta_builds.json`'un bir
  anlık görüntüsü, `Assets/data/` altına kopyalandı. Ana Python projesindeki
  bu dosyalar güncellendiğinde, bu kopyalar da elle/script ile yenilenmeli
  (otomatik senkronizasyon bu ilk sürümde YOK).

## Doğrulama durumu (dürüstlük ilkesi — bkz. AGENTS.md)

Bu proje, Flutter mobil companion'dan farklı olarak, **hiçbir Windows/UWP
araç zinciri olmayan bir Linux kum havuzunda** yazıldı — ne Visual Studio ne
de `dotnet`/MSBuild yerel olarak mevcut. Tek doğrulama yolu
`.github/workflows/build-xbox.yml` üzerinden `windows-latest` GitHub Actions
koşucusunda gerçek MSBuild ile derlemedir.

- [ ] CI'da derleme doğrulandı mı? (Bu dosyanın en son güncellendiği commit'e
      bakın — `DEVELOPMENT_LOG.md`'de ilgili CI run numarası kayıtlı olmalı.)
- [ ] Gerçek bir Xbox konsoluna (Developer Mode açık) yüklenip çalıştırıldı mı?
      **HAYIR** — kullanıcının eline Developer Mode'a alınmış bir konsol
      geçmeden bu adım atılamaz.
- [ ] Partner Center'a gerçek bir gönderim yapıldı mı? **HAYIR** — bu, kodun
      derlenmesinden tamamen ayrı, elle yapılması gereken bir süreç (bkz.
      aşağıdaki "Yayına hazırlık" bölümü).

## Doğrulanmamış / belirsiz alanlar (bunları ben doğrulayamadım)

- Xbox Live Creators Program'ın 2026 sonundaki tam kuralları — Microsoft'un
  kendi geliştirici forumlarında (2023-2025 arası) çelişkili/değişken
  bilgiler var; resmi, güncel bir duyuru bulunamadı. **Gerçek gönderim
  öncesi Partner Center'daki güncel koşulları kendin kontrol etmelisin.**
- `Package.appxmanifest`'teki `Identity/Name` ve `Publisher` alanları **yer
  tutucudur** — gerçek bir Store gönderimi için Visual Studio'nun "Associate
  App with the Store" sihirbazıyla Partner Center'daki gerçek rezervasyon
  bilgilerinle değiştirilmeli.
- `XboxCompanion_TemporaryKey.pfx`, bu depoda yalnızca **yerel/CI derleme
  testi** için üretilmiş kendi kendine imzalı bir sertifikadır — gerçek
  mağaza gönderiminde KULLANILMAMALI (Partner Center kendi imzalama
  sürecini uygular).

## Yayına hazırlık (kullanıcının kendisi yapmalı)

1. Partner Center'da uygulama adını rezerve et.
2. Visual Studio'da projeyi aç, Project → Publish → Associate App with the
   Store ile gerçek Identity/Publisher bilgilerini otomatik yazdır.
3. Developer Mode'a alınmış bir Xbox'ta yerel olarak dağıt ve dene (bkz.
   "Ne YAPMAZ" bölümündeki kısıtları akılda tutarak — sürpriz bekleme).
4. Sorunsuzsa, Partner Center üzerinden normal mağaza gönderim sürecini
   izle (bkz. AGENTS.md madde 6 — yayın onayı ana Python/mobil proje için
   geçerli kural, ama aynı dürüstlük ilkesi burada da uygulanmalı: gerçek
   bir Store gönderimi kullanıcının açık "Evet"i olmadan yapılmaz; zaten bu
   adım Claude'un erişemediği Partner Center arayüzünde, elle yapılıyor).
