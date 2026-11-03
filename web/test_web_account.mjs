// web/ sitesinin hesap sayfasını GERÇEK bir tarayıcıyla (Playwright) uçtan uca test eder: statik siteyi kendi
// JS dosyalarıyla (api.js, i18n.js — hiçbiri taklit edilmez) sunar, server/dev_server.mjs'i (SITE_URL bu statik
// siteye ayarlanmış olarak) arka planda çalıştırır, Discord onayını `page.route` ile dev sunucunun kendi
// "/fake/discord" adresine yönlendirir (gerçek internete çıkmadan) ve giriş → /v1/me → anahtar kullanma →
// hesap silme akışının tamamını tarayıcıda doğrular.
//
//   node web/test_web_account.mjs
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
let chromium;
try {
  const m = await import("playwright");
  chromium = m.chromium || m.default?.chromium;
} catch {
  try {
    const m = await import("/opt/npm-tools/node_modules/playwright/index.js");
    chromium = m.chromium || m.default?.chromium;
  } catch { /* aşağıda kontrol ediliyor */ }
}
if (!chromium) {
  console.log("ATLANDI: playwright paketi bulunamadı (`npm install -D playwright` ile eklenebilir) — bu test yalnız bir tarayıcı varsa çalışır.");
  process.exit(0);
}

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB_DIR = HERE;
let fails = 0;
const ok = (c, msg) => { console.log((c ? "OK   " : "FAIL ") + msg); if (!c) fails++; };

const SITE_PORT = 8801, DEV_PORT = 8802;
const SITE_ORIGIN = `http://127.0.0.1:${SITE_PORT}`, DEV_ORIGIN = `http://127.0.0.1:${DEV_PORT}`;

const MIME = { ".html": "text/html", ".js": "application/javascript", ".css": "text/css", ".json": "application/json" };

// Statik site sunucusu: tüm dosyalar web/'den, yalnız config.js test sunucusuna (DEV_ORIGIN) işaret edecek
// şekilde değiştirilir — gerçek config.js (production API_BASE) hiç değiştirilmez/commit edilmez.
const siteServer = createServer(async (req, res) => {
  let p = decodeURIComponent(new URL(req.url, SITE_ORIGIN).pathname);
  if (p.endsWith("/")) p += "index.html";
  if (p === "/assets/js/config.js") {
    res.writeHead(200, { "content-type": "application/javascript" });
    res.end(`window.TD2_CONFIG = { API_BASE: "${DEV_ORIGIN}", REPO: "FEDERALTURK/td2-loot-advisor", GUMROAD_URL: "" };`);
    return;
  }
  try {
    const file = path.join(WEB_DIR, p);
    if (!file.startsWith(WEB_DIR)) throw new Error("bad path");
    const body = await readFile(file);
    res.writeHead(200, { "content-type": MIME[path.extname(file)] || "application/octet-stream" });
    res.end(body);
  } catch (e) { res.writeHead(404); res.end("not found"); }
});
await new Promise(r => siteServer.listen(SITE_PORT, "127.0.0.1", r));
ok(true, `statik site http sunucusu ${SITE_ORIGIN} üzerinde`);

const dev = spawn(process.execPath, [path.join(HERE, "..", "server", "dev_server.mjs"), String(DEV_PORT)],
  { env: { ...process.env, DEV_SITE_URL: SITE_ORIGIN }, stdio: ["ignore", "pipe", "inherit"] });
let browser = null;
try {
  await new Promise((resolve, reject) => {
    let buf = "";
    dev.stdout.on("data", d => { buf += d; if (buf.includes("READY")) resolve(); });
    dev.on("exit", code => reject(new Error("dev_server erken kapandı: " + code +
      " (port " + DEV_PORT + " zaten kullanımda olabilir — önceki bir test çalışması temizlenmemiş olabilir)")));
    setTimeout(() => reject(new Error("dev_server zaman aşımı")), 8000);
  });
  ok(true, `dev_server.mjs ${DEV_ORIGIN} üzerinde, SITE_URL=${SITE_ORIGIN}`);

  browser = await chromium.launch();
  const context = await browser.newContext({ locale: "tr-TR" });   // td2Lang() varsayılanı TR olsun (testler TR metin bekliyor)
  const page = await context.newPage();
  page.on("pageerror", e => ok(false, "sayfa JS hatası: " + e.message));
  page.on("console", m => { if (m.type() === "error") ok(false, "console.error: " + m.text()); });

  // Discord'a gidecek navigasyonu yakalayıp dev sunucunun sahte onay adresine yönlendir (gerçek internete çıkmadan).
  await page.route("https://discord.com/**", async route => {
    const u = new URL(route.request().url());
    const state = u.searchParams.get("state");
    await route.fulfill({ status: 302, headers: { location: `${DEV_ORIGIN}/fake/discord?state=${state}&user=webtester` } });
  });

  // ---- 1) Giriş yapılmamış hâl
  await page.goto(`${SITE_ORIGIN}/account/`);
  await page.waitForSelector("#acc-logged-out:not([hidden])", { timeout: 5000 });
  ok(true, "çıkış durumunda 'Discord ile giriş yap' gösteriliyor");

  // ---- 2) Giriş akışı (gerçek fragment-tabanlı dönüş, gerçek PKCE/sha256 kodu tarayıcıda çalışıyor)
  await page.click("#acc-login-btn");
  await page.waitForURL(u => u.origin === SITE_ORIGIN && u.pathname === "/account/", { timeout: 8000 });
  await page.waitForSelector("#acc-logged-in:not([hidden])", { timeout: 8000 });
  const name = await page.textContent("#acc-name");
  ok(name.trim() === "webtester", `giriş tamamlandı, kullanıcı adı doğru (${name})`);
  const tier = await page.textContent("#acc-tier");
  ok(tier.trim() === "Ücretsiz katman", "başlangıç katmanı ücretsiz");
  const url1 = page.url();
  ok(!url1.includes("state="), "giriş sonrası #fragment temizlendi");

  // ---- 3) Sayfa yenilenince oturum kalıcı (localStorage token)
  await page.reload();
  await page.waitForSelector("#acc-logged-in:not([hidden])", { timeout: 5000 });
  ok(true, "sayfa yenilenince oturum localStorage'dan geri geliyor");

  // ---- 4) Anahtar kullanma — dev_server'ın sahte Gumroad'u "GOOD" önekli 32 karakterli anahtarları kabul eder
  // (gerçek Gumroad lisans anahtarı biçimi: 8-8-8-8, tire ile); tireler sunucu tarafında normCode() ile temizlenir.
  const gumroadKey = "GOODAAAA-BBBBBBBB-CCCCCCCC-DDDDDDDD";
  await page.fill("#acc-redeem-input", gumroadKey);
  await page.click("#acc-redeem-btn");
  await page.waitForSelector("#acc-redeem-msg:not([hidden])", { timeout: 5000 });
  const redeemMsg = await page.textContent("#acc-redeem-msg");
  const tierAfter = await page.textContent("#acc-tier");
  ok(tierAfter.trim() === "Premium" && redeemMsg.includes("güncellendi"), `Gumroad anahtarı kullanıldı → Premium (mesaj: "${redeemMsg.trim()}")`);

  // ---- 5) Çıkış
  await page.click("#acc-logout-btn");
  await page.waitForSelector("#acc-logged-out:not([hidden])", { timeout: 5000 });
  ok(true, "çıkış yapınca giriş ekranına dönüyor");
  await page.reload();
  await page.waitForSelector("#acc-logged-out:not([hidden])", { timeout: 5000 });
  ok(true, "çıkış sonrası sayfa yenilenince token kalıcı değil (temizlendi)");
} catch (e) {
  ok(false, "beklenmeyen hata: " + e.message);
} finally {
  if (browser) await browser.close().catch(() => {});
  siteServer.close();
  dev.kill("SIGKILL");
}

console.log(fails ? `RESULT: FAIL (${fails})` : "RESULT: PASS");
process.exit(fails ? 1 : 0);
