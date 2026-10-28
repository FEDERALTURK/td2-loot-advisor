// Hesap sistemi kurulumu — KENDİ bilgisayarında, server klasöründe bir kez çalıştır:
//
//     cd server
//     node account_setup.mjs
//
// Ne yapar
//   1) Yetki belgesi imza anahtarını (Ed25519) BU bilgisayarda üretir; özel yarısını doğrudan Cloudflare gizlisine
//      (ENT_SIGNING_KEY) yollar — diske yazılmaz, ekrana basılmaz.
//   2) Yönetici belirtecini (ADMIN_TOKEN) üretir, Cloudflare gizlisine yollar ve ../private/admin_token.txt dosyasına
//      kaydeder (panel ayarlarına bunu yapıştıracaksın; private/ klasörü depoya girmez).
//   3) Discord uygulamasının gizli anahtarını (DISCORD_CLIENT_SECRET) sorar → doğrudan Cloudflare gizlisine.
//   4) wrangler.toml [vars]: DISCORD_CLIENT_ID, ENT_PUBLIC_KEY, PUBLIC_URL (ve isteğe bağlı GUMROAD_PRODUCT_ID).
//   5) Veritabanı tablolarını ekler (mevcut veriye dokunmaz) ve worker'ı yayınlar.
//   6) Açık anahtarı ../private/ent_public_key.txt dosyasına yazar (gizli değildir; programa eklenecek).
import { generateKeyPairSync, randomBytes } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";

const here = new URL(".", import.meta.url);
const priv = new URL("../private/", here);
const tomlPath = new URL("wrangler.toml", here);
const rl = createInterface({ input, output });
const WIN = process.platform === "win32";

function wrangler(args, stdinText) {
  const r = spawnSync(WIN ? "npx.cmd" : "npx", ["wrangler", ...args], {
    cwd: here, shell: WIN, encoding: "utf8",
    input: stdinText, stdio: stdinText === undefined ? "inherit" : ["pipe", "inherit", "inherit"] });
  if (r.status !== 0) { console.error(`\n✖ wrangler ${args.join(" ")} başarısız (kod ${r.status}).`); process.exit(1); }
}
function setVar(toml, name, value) {
  const line = `${name} = "${value}"`;
  const re = new RegExp(`^${name}\\s*=.*$`, "m");
  if (re.test(toml)) return toml.replace(re, line);
  return toml.replace(/^\[vars\]\s*$/m, `[vars]\n${line}`);
}

console.log("\n=== TD2 Loot Advisor — hesap sistemi kurulumu ===\n");
console.log("Gerekenler: discord.com/developers/applications → uygulaman → OAuth2 sayfası:");
console.log("  • Client ID ve Client Secret");
console.log("  • Redirects'e şunu ekle:  https://td2-stats.td2loot.workers.dev/v1/auth/callback\n");

let toml = readFileSync(tomlPath, "utf8");
const publicUrl = ((await rl.question("Worker adresi [https://td2-stats.td2loot.workers.dev]: ")).trim() || "https://td2-stats.td2loot.workers.dev").replace(/\/$/, "");
let clientId = "";
while (!/^\d{15,25}$/.test(clientId)) clientId = (await rl.question("Discord Client ID (yalnız rakam): ")).trim();
const gumroad = (await rl.question("Gumroad ürün kimliği (product_id) — satış yoksa boş bırak: ")).trim();

mkdirSync(priv, { recursive: true });
let regen = true;
if (existsSync(new URL("ent_public_key.txt", priv))) {
  const a = (await rl.question("İmza anahtarı zaten var. Yeniden üretilsin mi? (e/H — yeniden üretirsen program güncellemesi gerekir): ")).trim().toLowerCase();
  regen = a === "e" || a === "y";
}
rl.close();

if (regen) {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  const pkcs8 = privateKey.export({ format: "der", type: "pkcs8" }).toString("base64");
  const pubHex = publicKey.export({ format: "der", type: "spki" }).subarray(-32).toString("hex");
  console.log("\n→ İmza anahtarı Cloudflare'e gönderiliyor (ENT_SIGNING_KEY)…");
  wrangler(["secret", "put", "ENT_SIGNING_KEY"], pkcs8 + "\n");
  writeFileSync(new URL("ent_public_key.txt", priv), pubHex + "\n");
  toml = setVar(toml, "ENT_PUBLIC_KEY", pubHex);
}
if (!existsSync(new URL("admin_token.txt", priv))) {
  const admin = randomBytes(32).toString("base64url");
  console.log("→ Yönetici belirteci Cloudflare'e gönderiliyor (ADMIN_TOKEN)…");
  wrangler(["secret", "put", "ADMIN_TOKEN"], admin + "\n");
  writeFileSync(new URL("admin_token.txt", priv), admin + "\n");
}
console.log("→ Şimdi Discord Client Secret'ı yapıştır (ekranda görünmez) ve Enter'a bas:");
wrangler(["secret", "put", "DISCORD_CLIENT_SECRET"]);

toml = setVar(toml, "DISCORD_CLIENT_ID", clientId);
toml = setVar(toml, "PUBLIC_URL", publicUrl);
if (gumroad) toml = setVar(toml, "GUMROAD_PRODUCT_ID", gumroad);
writeFileSync(tomlPath, toml);

console.log("→ Veritabanı tabloları ekleniyor (mevcut veriler korunur)…");
wrangler(["d1", "execute", "td2stats", "--remote", "--file=schema.sql"]);
console.log("→ Worker yayınlanıyor…");
wrangler(["deploy"]);

const pub = readFileSync(new URL("ent_public_key.txt", priv), "utf8").trim();
console.log("\n✔ Kurulum tamam.");
console.log("  • Panel → Ayarlar → 'Yönetici belirteci': private\\admin_token.txt içindeki metin (kimseyle paylaşma).");
console.log("  • Açık anahtar (gizli değil, programa eklenecek):  " + pub);
console.log("  • Deneme: " + publicUrl + "/v1/health  →  \"login\": true görünmeli.\n");
