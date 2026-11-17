// TD2 Loot Advisor — web sitesi ortak ayarları.
// Bu site Cloudflare Pages üzerinde, uygulamanın Cloudflare Worker sunucusuna (server/) bağlanır.
"use strict";
window.TD2_CONFIG = {
  // Topluluk/hesap sunucusu — server/wrangler.toml → PUBLIC_URL ile aynı olmalı.
  API_BASE: "https://td2-stats.td2loot.workers.dev",

  // GitHub deposu — indirme linkleri ve haber verisi buradan okunur.
  REPO: "FEDERALTURK/td2-loot-advisor",

  // Gumroad ürün linki. Ürün henüz oluşturulmadıysa boş bırak ("") — Premium sayfası
  // otomatik olarak "yakında" durumunu gösterir. Ürün oluşturulunca buraya tam linki yapıştır,
  // örn. "https://gumroad.com/l/td2-loot-advisor-premium".
  GUMROAD_URL: "",
};
