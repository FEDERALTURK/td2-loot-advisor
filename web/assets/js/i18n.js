// TD2 Loot Advisor — web sitesi için çok küçük bir çeviri katmanı (yalnız TR/EN).
// Not: uygulamanın kendisi 10 dili destekliyor (lang/*.json) ve herkes kendi dilini ekleyebiliyor;
// bu site şimdilik TR/EN ile başlıyor — aynı desene uyan yeni bir dosya (ör. de.js) eklenip
// STRINGS'e kaydedilerek genişletilebilir.
"use strict";

const STRINGS = {
  tr: {
    nav_home: "Ana Sayfa", nav_news: "Haberler", nav_premium: "Premium", nav_account: "Hesabım",
    nav_download: "İndir", nav_github: "GitHub",

    hero_title: "Envanterde zaman kaybetme.",
    hero_sub: "The Division 2'de bir eşyanın üzerine gel, F8'e bas: TD2 Loot Advisor ekranı okur, kendi build kurallarınla karşılaştırır ve saniyeler içinde sakla / düşün / kır kararını verir. Oyunun belleğine hiç dokunmaz.",
    hero_cta_download: "Windows için indir",
    hero_cta_source: "Kaynak kodu (GitHub)",
    hero_note: "Ücretsiz ve açık kaynak (MIT). Hesap gerektirmez.",

    feat_title: "Ne yapıyor?",
    feat_scan_t: "Ekran okuma ile anında karar",
    feat_scan_d: "RapidOCR motoru eşya kartını okur, aktif build'inle karşılaştırır ve sakla / düşün / kır der — gerçek kartlarda 1440p/1080p/720p/480p çözünürlüklerde test edildi.",
    feat_build_t: "Build takibi",
    feat_build_d: "Aktif build'in hangi parçasının eksik olduğunu, hangi set/marka/isimli eşyayı aradığını gösterir; tamamlanan build'ler bildirilir.",
    feat_stash_t: "Envanter analizi (Stash)",
    feat_stash_d: "Taranan her eşya saklanır; build'ine göre en iyi parçalarını bulur, neyi kırabileceğini (hiçbir zaman yakın build'lerinde kullandıklarını değil) söyler.",
    feat_task_t: "Görev çevirisi",
    feat_task_d: "Ekrandaki güncel oyun görevlerini kendi arayüz dilinde gösterir, adımları ve wiki görsellerini sunar.",
    feat_mem_t: "Belleğe asla dokunmaz",
    feat_mem_d: "Yalnızca ekranı (OCR ile) ve oyunun kendi ayar dosyasını okur — işlem belleğine okuma/yazma/enjeksiyon yok.",
    feat_lang_t: "10 dil, herkes kendi dilini ekleyebilir",
    feat_lang_d: "Arayüz TR, EN, DE, FR, ES, IT, PT, PL, RU, NL dillerinde; yeni bir dil dosyası eklemek yeterli.",
    feat_more: "Tüm özellikler → GitHub README",

    free_title: "Ücretsiz ve Premium",
    free_lede: "Tarama, build takibi, görevler, envanter (stash) ve aktif-build optimizasyonu tamamen ücretsiz ve her zaman öyle kalacak.",
    free_cta: "Premium'u gör",

    down_title: "İndir",
    down_installer: "Kurulum dosyası (önerilen)",
    down_portable: "Taşınabilir (zip)",
    down_mobile: "Android companion (beta)",
    down_source: "Kaynak kodundan çalıştır",
    down_loading: "Son sürüm bilgisi alınıyor…",
    down_error: "Sürüm bilgisi şu an alınamadı — doğrudan Releases sayfasından indirebilirsin.",
    down_version: "Sürüm",
    down_unsigned_note: "Henüz Windows kod imzalama sertifikası yok (küçük açık kaynak bir proje — ücretsiz SignPath Foundation programına başvurdu, henüz onaylanmadı). İlk çalıştırmada SmartScreen \"Bilinmeyen yayımcı\" uyarısı gösterebilir — \"Daha fazla bilgi\" → \"Yine de çalıştır\" ile devam edebilirsin. Her sürümle birlikte bir SHA256SUMS dosyası da yayımlanır; indirdiğin dosyayı çalıştırmadan önce karşılaştırabilirsin (Windows'ta: certutil -hashfile dosya.exe SHA256).",

    news_title: "The Division 2 Haberleri",
    news_sub: "TD2 Loot Advisor'ın kendi oyun-içi haber akışından — aynı veri, uygulamadaki Bilgi sekmesinde de görünür.",
    news_season: "Mevcut sezon",
    news_updated: "Güncellendi",
    news_loading: "Haberler yükleniyor…",
    news_error: "Haberler şu an yüklenemedi. Doğrudan kaynağa bakabilirsin:",
    news_source: "Kaynak",
    d3_title: "The Division 3",
    d3_checked: "Son kontrol",
    d3_status_fallback: "Ubisoft, The Division 3'ün Massive Entertainment tarafından geliştirildiğini doğruladı. Henüz oynanış, platform veya çıkış tarihi açıklanmadı.",
    d3_sources: "Kaynaklar",

    prem_title: "Premium",
    prem_sub: "Ücretsiz sürüm tam ve sınırsız kalır. Premium, ekstra zaman kazandıran özellikler ekler.",
    prem_list_t: "Premium ile gelenler",
    prem_recal_t: "Kalibrasyon danışmanı",
    prem_recal_d: "Hangi attribute'un hangi eşyadan geldiğine dair önerilerle en iyi donör eşyayı bulur.",
    prem_opt_t: "Tüm build'ler için optimize",
    prem_opt_d: "Envanterindeki eşyaları her build'ine göre ayrı ayrı puanlar, en iyi kombinasyonu önerir.",
    prem_export_t: "CSV dışa aktarma",
    prem_export_d: "Envanterini ve build analizini tablo olarak dışa aktar.",
    prem_vendor_t: "Satıcı takibi",
    prem_vendor_d: "Haftalık satıcıları ve hedefli düşüşleri kendi build'lerinle eşleştirir.",
    prem_phone_t: "Telefon companion",
    prem_phone_d: "Son karar, aktif build ve satıcı eşleşmeleri — telefonunda, aynı Wi-Fi üzerinden ya da bulut eşleştirmesiyle.",
    prem_api_t: "Yerel API ve bildirimler",
    prem_api_d: "OBS overlay, Stream Deck, WebSocket entegrasyonu ve telefon bildirimleri (ntfy / Discord webhook).",
    prem_stats_t: "Topluluk düşüş istatistikleri",
    prem_stats_d: "Hangi eşya hangi aktivitede ne sıklıkla düşüyor — binlerce oyuncunun anonim katkısıyla.",
    prem_buy_t: "Premium satın al",
    prem_buy_soon: "Satın alma yakında açılıyor — şu an için hesabından davet kodu veya anahtar girebilirsin.",
    prem_buy_cta: "Gumroad'da satın al",
    prem_redeem_t: "Zaten bir anahtarın/kodun mu var?",
    prem_redeem_cta: "Hesabım sayfasından kullan →",
    prem_license_note: "Bir lisans tek bilgisayara bağlanır; hesabından istediğin zaman cihazı sıfırlayabilirsin.",

    acc_title: "Hesabım",
    acc_sub: "Programdaki hesabınla aynı — Discord ile giriş yap, lisans durumunu gör, anahtar/davet kodunu kullan.",
    acc_login_cta: "Discord ile giriş yap",
    acc_login_note: "Şifre yok; giriş tamamen Discord OAuth2 ile. Bu site Discord şifreni hiçbir zaman görmez.",
    acc_logout: "Çıkış yap",
    acc_tier_free: "Ücretsiz katman",
    acc_tier_premium: "Premium",
    acc_since: "Katılım",
    acc_device_limit: "Bu lisansın cihaz sınırına ulaşıldı (masaüstü uygulaman muhtemelen zaten bağlı) — hesap bilgin yine de doğru, yalnız bu tarayıcıya yeni bir yetki belgesi verilmiyor. Gerekirse hesap panelinden cihazı sıfırlayabilirsin.",
    acc_redeem_t: "Anahtar / davet kodu kullan",
    acc_redeem_ph: "TD2K-…, TD2I-… ya da Gumroad lisans anahtarı",
    acc_redeem_cta: "Kullan",
    acc_redeem_ok: "Kod kullanıldı, hesabın güncellendi.",
    acc_delete_t: "Hesabı sil",
    acc_delete_cta: "Hesabımı ve tüm verilerimi sil",
    acc_delete_note: "Bu, masaüstündeki ve telefondaki TÜM bağlı hesabı siler (yalnızca bu tarayıcıyı değil). 24 saat bekleme süresinden sonra kalıcı olur.",
    acc_delete_confirm: "Emin misin? Bu, hesabının tamamını (masaüstü ve telefon dahil) silme talebi başlatır.",
    acc_delete_ok: "Silme talebi alındı. Oturumların hemen kapatıldı; veriler 24 saat sonra kalıcı olarak silinecek.",
    acc_err_generic: "Bir şeyler ters gitti, birazdan tekrar dene.",
    acc_logging_in: "Discord'a yönlendiriliyor…",
    acc_completing: "Giriş tamamlanıyor…",

    footer_privacy: "Gizlilik Politikası",
    footer_license: "Lisans (MIT)",
    footer_disclaimer: "Bağımsız bir topluluk projesidir; Ubisoft veya Massive Entertainment tarafından yayımlanmaz ya da desteklenmez.",
  },
  en: {
    nav_home: "Home", nav_news: "News", nav_premium: "Premium", nav_account: "My account",
    nav_download: "Download", nav_github: "GitHub",

    hero_title: "Stop wasting time in your stash.",
    hero_sub: "Hover an item in The Division 2, press F8: TD2 Loot Advisor reads the screen, checks it against your own build rules, and gives a keep / consider / dismantle verdict in seconds. It never touches game memory.",
    hero_cta_download: "Download for Windows",
    hero_cta_source: "Source code (GitHub)",
    hero_note: "Free and open source (MIT). No account required.",

    feat_title: "What it does",
    feat_scan_t: "Instant decisions from the screen",
    feat_scan_d: "The RapidOCR engine reads the item card and compares it with your active build — tested on real cards at 1440p, 1080p, 720p and 480p.",
    feat_build_t: "Build tracking",
    feat_build_d: "Shows exactly which piece of your active build is missing, and which set/brand/named item to look for; completed builds are announced.",
    feat_stash_t: "Stash analysis",
    feat_stash_d: "Every scanned item is saved; it finds your best pieces per build and what's safe to dismantle (never pieces your nearby builds use).",
    feat_task_t: "Task translation",
    feat_task_d: "Shows current in-game tasks in your own interface language, with steps and wiki pictures.",
    feat_mem_t: "Never touches memory",
    feat_mem_d: "Reads only the screen (via OCR) and the game's own settings file — no process memory reading, writing or injection.",
    feat_lang_t: "10 languages, add your own",
    feat_lang_d: "Interface in TR, EN, DE, FR, ES, IT, PT, PL, RU, NL; adding a new language is a single file.",
    feat_more: "Full feature list → GitHub README",

    free_title: "Free and Premium",
    free_lede: "Scanning, build tracking, tasks, stash and the active-build optimizer are completely free, and always will be.",
    free_cta: "See Premium",

    down_title: "Download",
    down_installer: "Installer (recommended)",
    down_portable: "Portable (zip)",
    down_mobile: "Android companion (beta)",
    down_source: "Run from source",
    down_loading: "Fetching the latest release…",
    down_error: "Couldn't fetch the latest release right now — download directly from the Releases page.",
    down_version: "Version",
    down_unsigned_note: "No Windows code-signing certificate yet (small open-source project — applied to the free SignPath Foundation program, not yet approved). On first run, SmartScreen may show an \"Unknown publisher\" warning — click \"More info\" → \"Run anyway\" to continue. Every release also ships a SHA256SUMS file so you can verify your download before running it (on Windows: certutil -hashfile file.exe SHA256).",

    news_title: "The Division 2 News",
    news_sub: "From TD2 Loot Advisor's own in-game news feed — the same data shown in the app's Knowledge tab.",
    news_season: "Current season",
    news_updated: "Updated",
    news_loading: "Loading news…",
    news_error: "Couldn't load news right now. You can check the source directly:",
    news_source: "Source",
    d3_title: "The Division 3",
    d3_checked: "Last checked",
    d3_status_fallback: "Ubisoft has confirmed The Division 3 is in development at Massive Entertainment. No gameplay, platforms, or release date have been announced yet.",
    d3_sources: "Sources",

    prem_title: "Premium",
    prem_sub: "The free version stays full and unlimited. Premium adds extra time-saving features.",
    prem_list_t: "What Premium adds",
    prem_recal_t: "Recalibration advisor",
    prem_recal_d: "Finds the best donor item with suggestions on which attribute comes from which item.",
    prem_opt_t: "Optimize for every build",
    prem_opt_d: "Scores your stash against each of your builds separately and suggests the best combination.",
    prem_export_t: "CSV export",
    prem_export_d: "Export your stash and build analysis as a table.",
    prem_vendor_t: "Vendor tracking",
    prem_vendor_d: "Matches weekly vendors and targeted loot against your builds.",
    prem_phone_t: "Phone companion",
    prem_phone_d: "Latest verdict, active build and vendor matches — on your phone, over your own Wi-Fi or cloud pairing.",
    prem_api_t: "Local API and notifications",
    prem_api_d: "OBS overlay, Stream Deck, WebSocket integration and phone notifications (ntfy / Discord webhook).",
    prem_stats_t: "Community drop statistics",
    prem_stats_d: "What drops where, and how often — from thousands of players' anonymous contributions.",
    prem_buy_t: "Buy Premium",
    prem_buy_soon: "Purchasing opens soon — for now you can redeem an invite code or key from your account.",
    prem_buy_cta: "Buy on Gumroad",
    prem_redeem_t: "Already have a key or code?",
    prem_redeem_cta: "Redeem it on My Account →",
    prem_license_note: "A license is bound to one computer; you can reset the device from your account at any time.",

    acc_title: "My Account",
    acc_sub: "The same account as in the app — sign in with Discord, see your license status, redeem a key or invite code.",
    acc_login_cta: "Sign in with Discord",
    acc_login_note: "No password; sign-in is entirely Discord OAuth2. This site never sees your Discord password.",
    acc_logout: "Sign out",
    acc_tier_free: "Free tier",
    acc_tier_premium: "Premium",
    acc_since: "Member since",
    acc_device_limit: "This license has reached its device limit (your desktop app is probably already using it) — your account info is still correct, this browser just isn't issued a new entitlement. You can reset the device from your account panel if needed.",
    acc_redeem_t: "Redeem a key / invite code",
    acc_redeem_ph: "TD2K-…, TD2I-… or a Gumroad license key",
    acc_redeem_cta: "Redeem",
    acc_redeem_ok: "Code redeemed, your account is updated.",
    acc_delete_t: "Delete account",
    acc_delete_cta: "Delete my account and all my data",
    acc_delete_note: "This deletes the ENTIRE linked account on desktop and phone (not just this browser). It becomes permanent after a 24-hour grace period.",
    acc_delete_confirm: "Are you sure? This starts a request to delete your whole account (desktop and phone included).",
    acc_delete_ok: "Deletion requested. Your sessions were revoked immediately; the data will be permanently deleted after 24 hours.",
    acc_err_generic: "Something went wrong, please try again shortly.",
    acc_logging_in: "Redirecting to Discord…",
    acc_completing: "Finishing sign-in…",

    footer_privacy: "Privacy Policy",
    footer_license: "License (MIT)",
    footer_disclaimer: "An independent community project; not published, endorsed, or supported by Ubisoft or Massive Entertainment.",
  },
};

function td2Lang() {
  try {
    const saved = localStorage.getItem("td2_site_lang");
    if (saved === "tr" || saved === "en") return saved;
  } catch (e) { /* özel pencere / engellenmiş depolama */ }
  return (navigator.language || "en").toLowerCase().startsWith("tr") ? "tr" : "en";
}
function td2SetLang(lang) {
  try { localStorage.setItem("td2_site_lang", lang); } catch (e) { /* yoksay */ }
  td2ApplyI18n(lang);
}
function td2T(key, lang) {
  const l = lang || td2Lang();
  return (STRINGS[l] && STRINGS[l][key]) || STRINGS.en[key] || key;
}
function td2ApplyI18n(lang) {
  const l = lang || td2Lang();
  document.documentElement.lang = l;
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = td2T(el.getAttribute("data-i18n"), l); });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = td2T(el.getAttribute("data-i18n-ph"), l); });
  document.querySelectorAll(".td2-lang-btn").forEach(b => b.classList.toggle("active", b.dataset.lang === l));
}
document.addEventListener("DOMContentLoaded", () => {
  td2ApplyI18n();
  document.querySelectorAll(".td2-lang-btn").forEach(b => b.addEventListener("click", () => td2SetLang(b.dataset.lang)));
});
