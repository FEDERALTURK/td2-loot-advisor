// Hesap / lisans uçlarının testi: D1 → node:sqlite, Discord ve Gumroad → sahte fetch.   node server/test_accounts.mjs
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { createHash, generateKeyPairSync, randomBytes } from "node:crypto";
import worker from "./worker.js";

const sql = new DatabaseSync(":memory:");
sql.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
function stmt(q) {
  let args = [];
  const s = {
    bind(...a) { args = a; return s; },
    async run() { const r = sql.prepare(q).run(...args); return { meta: { changes: Number(r.changes) } }; },
    async first() { return sql.prepare(q).get(...args) ?? null; },
    async all() { return { results: sql.prepare(q).all(...args) }; },
  };
  return s;
}
const DB = { prepare: stmt };

const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const pkcs8 = privateKey.export({ format: "der", type: "pkcs8" }).toString("base64");
const pubHex = publicKey.export({ format: "der", type: "spki" }).subarray(-32).toString("hex");
const env = { DB, HASH_SALT: "t", DISCORD_CLIENT_ID: "123", DISCORD_CLIENT_SECRET: "sec", ENT_SIGNING_KEY: pkcs8,
              ENT_PUBLIC_KEY: pubHex, ADMIN_TOKEN: "admin-token-very-long-random-xyz-123", GUMROAD_PRODUCT_ID: "prod",
              PUBLIC_URL: "https://w", LICENSE_PUBKEY: "00".repeat(32) };

// --- sahte Discord / Gumroad
let discordUser = { id: "111111111111", username: "soner", global_name: "Soner" };
const gumroad = { "AAAAAAAA-BBBBBBBB-CCCCCCCC-DDDDDDDD": { success: true, purchase: { sale_id: "S1", email: "buyer@x.com" } },
                  "EEEEEEEE-FFFFFFFF-00000000-11111111": { success: true, purchase: { sale_id: "S2", refunded: true } } };
globalThis.fetch = async (url, opts = {}) => {
  if (url.startsWith("https://discord.com/api/oauth2/token")) {
    const b = new URLSearchParams(opts.body);
    if (b.get("client_secret") !== "sec" || b.get("redirect_uri") !== "https://w/v1/auth/callback") return new Response("no", { status: 401 });
    return Response.json({ access_token: "at-" + b.get("code") });
  }
  if (url === "https://discord.com/api/users/@me") return Response.json(discordUser);
  if (url.startsWith("https://api.gumroad.com/")) {
    const k = new URLSearchParams(opts.body).get("license_key");
    return Response.json(gumroad[k] || { success: false });
  }
  return new Response("nf", { status: 404 });
};

let fails = 0;
const ok = (c, msg) => { console.log((c ? "OK   " : "FAIL ") + msg); if (!c) fails++; };
const b64u = b => Buffer.from(b).toString("base64url");
const call = (path, { method = "GET", body, auth, ip = "9.9.9.9" } = {}) => worker.fetch(new Request("https://w" + path, {
  method, body: body ? JSON.stringify(body) : undefined,
  headers: { "cf-connecting-ip": ip, ...(auth ? { authorization: auth } : {}) } }), env);
const A = { auth: "Admin " + env.ADMIN_TOKEN };

async function login(device, user) {
  if (user) discordUser = user;
  const state = b64u(randomBytes(24)), verifier = b64u(randomBytes(32));
  const challenge = b64u(createHash("sha256").update(verifier).digest());
  ok((await call("/v1/auth/start", { method: "POST", body: { state, challenge, port: 80 } })).status === 400, "ayrıcalıklı port reddedildi");
  let r = await call("/v1/auth/start", { method: "POST", body: { state, challenge, port: 53682 } });
  const j = await r.json();
  ok(r.status === 200 && j.url.includes("client_id=123") && j.url.includes("state=" + state), "giriş bağlantısı");
  r = await call("/v1/auth/token", { method: "POST", body: { state, verifier, grant: b64u(randomBytes(24)), device } });
  ok(r.status === 410, "Discord onayından önce oturum yok");
  r = await call(`/v1/auth/callback?state=${state}&code=c1`);
  const loc = r.headers.get("location") || "";
  ok(r.status === 302 && loc.startsWith("http://127.0.0.1:53682/callback?state=" + state + "&grant="), "dönüş yalnız yerel programa gider");
  const grant = new URL(loc).searchParams.get("grant");
  r = await call("/v1/auth/token", { method: "POST", body: { state, verifier, grant, device } });
  const p = await r.json();
  ok(p.status === "ok" && p.token && p.tier === "free", "oturum alındı, ücretsiz katman");
  r = await call("/v1/auth/token", { method: "POST", body: { state, verifier, grant, device } });
  ok(r.status === 410, "aynı giriş ikinci kez kullanılamaz");
  return p.token;
}

// bağlantıyı çalan / yanlış kanıt: tek denemede giriş yanar
{
  const state = b64u(randomBytes(24)), verifier = b64u(randomBytes(32));
  const challenge = b64u(createHash("sha256").update(verifier).digest());
  await call("/v1/auth/start", { method: "POST", body: { state, challenge, port: 50000 } });
  const loc = (await call(`/v1/auth/callback?state=${state}&code=c1`)).headers.get("location");
  const grant = new URL(loc).searchParams.get("grant");
  let r = await call("/v1/auth/token", { method: "POST", body: { state, verifier: b64u(randomBytes(32)), grant, device: b64u(randomBytes(32)) } });
  ok(r.status === 403, "verifier'ı bilmeyen grant ile oturum alamaz");
  r = await call("/v1/auth/token", { method: "POST", body: { state, verifier, grant, device: b64u(randomBytes(32)) } });
  ok(r.status === 410, "başarısız denemeden sonra giriş geçersiz");
  r = await call(`/v1/auth/callback?state=${state}&code=c1`);
  ok(r.status === 400, "dönüş bağlantısı tekrar kullanılamaz");
}

const DEV1 = b64u(randomBytes(32)), DEV2 = b64u(randomBytes(32));
const tok = await login(DEV1);
ok(!sql.prepare("SELECT * FROM sessions").all().some(s => s.token_hash === tok), "oturum belirteci düz saklanmıyor");
let r = await call("/v1/me", { auth: "Bearer " + tok }); let j = await r.json();
ok(j.account.username === "Soner" && j.entitlement === null, "/v1/me hesap bilgisi");
ok((await call("/v1/me", { auth: "Bearer " + "x".repeat(43) })).status === 401, "geçersiz oturum reddedildi");

// yönetici
ok((await call("/v1/admin/stats", { auth: "Admin wrong-token-wrong-token-wrong" })).status === 403, "yanlış yönetici belirteci reddedildi");
ok((await call("/v1/admin/stats")).status === 403, "yetkisiz yönetici isteği reddedildi");
r = await call("/v1/admin/licenses", { ...A, method: "POST", body: { count: 3, days: 30, note: "test" } });
const keys = (await r.json()).keys;
ok(keys.length === 3 && keys.every(k => /^TD2K(-[0-9A-Z]{4}){4}$/.test(k)), "3 anahtar üretildi: " + keys[0]);
ok(!sql.prepare("SELECT key_hash FROM licenses").all().some(x => keys.some(k => x.key_hash.includes(k))), "anahtarlar düz saklanmıyor");

// anahtar kullan
r = await call("/v1/license/redeem", { method: "POST", auth: "Bearer " + tok, body: { code: keys[0].toLowerCase().replace(/-/g, " ") } });
j = await r.json();
ok(r.status === 200 && j.tier === "premium" && j.entitlement?.startsWith("TD2E-"), "anahtar kullanıldı → premium + yetki belgesi");
ok(j.license.expires > Date.now() / 1000 + 29 * 86400, "süre kullanımda başladı (30 gün)");
// yetki belgesi worker'ın premium kontrolünden geçer
r = await call("/v1/stats", { auth: "TD2 " + j.entitlement });
ok(r.status === 200, "TD2E ile premium istatistik uç noktası açık");
const bad = j.entitlement.slice(0, -3) + (j.entitlement.endsWith("A") ? "BBB" : "AAA");
ok((await call("/v1/stats", { auth: "TD2 " + bad })).status === 401, "değiştirilmiş yetki belgesi reddedildi");
const ent = JSON.parse(Buffer.from(j.entitlement.slice(5).split(".")[0], "base64url"));
ok(ent.exp - ent.iat <= 7 * 86400 && ent.dev === createHash("sha256").update("td2e:" + DEV1).digest("hex").slice(0, 32) && ent.tier === "premium", "belge 7 gün, cihaza bağlı");
console.log("ENT_SAMPLE " + JSON.stringify({ ent: j.entitlement, pub: pubHex, device: DEV1 }));

// başka hesap aynı anahtarı kullanamaz
const tok2 = await login(DEV2, { id: "222222222222", username: "other" });
r = await call("/v1/license/redeem", { method: "POST", auth: "Bearer " + tok2, body: { code: keys[0] } });
ok(r.status === 409, "kullanılmış anahtar başka hesapta reddedildi");
// aynı hesap ikinci bilgisayar → cihaz sınırı
const tok1b = await login(DEV2, { id: "111111111111", username: "soner", global_name: "Soner" });
j = await (await call("/v1/me", { auth: "Bearer " + tok1b })).json();
ok(j.device_limit === true && j.entitlement === null && j.tier === "free", "1 bilgisayar sınırı: ikinci cihaz premium alamaz");
const licId = sql.prepare("SELECT id FROM licenses WHERE account_id IS NOT NULL").get().id;
await call(`/v1/admin/licenses/${licId}/reset_devices`, { ...A, method: "POST" });
j = await (await call("/v1/me", { auth: "Bearer " + tok1b })).json();
ok(j.tier === "premium" && j.entitlement, "yönetici cihazı sıfırlayınca yeni bilgisayar çalışır");
j = await (await call("/v1/me", { auth: "Bearer " + tok })).json();
ok(j.device_limit === true, "eski bilgisayar artık sınırda");

// iptal
await call(`/v1/admin/licenses/${licId}/revoke`, { ...A, method: "POST" });
j = await (await call("/v1/me", { auth: "Bearer " + tok1b })).json();
ok(j.tier === "free" && !j.entitlement, "iptal edilen lisans premium vermez");

// davet kodu
r = await call("/v1/admin/invites", { ...A, method: "POST", body: { uses: 1, days: 7, note: "yayıncı" } });
const inv = (await r.json()).code;
ok(/^TD2I(-[0-9A-Z]{4}){3}$/.test(inv), "davet kodu: " + inv);
r = await call("/v1/license/redeem", { method: "POST", auth: "Bearer " + tok2, body: { code: inv } });
j = await r.json(); ok(r.status === 200 && j.how === "invite" && j.tier === "premium", "davet kodu → 7 gün premium");
r = await call("/v1/license/redeem", { method: "POST", auth: "Bearer " + tok1b, body: { code: inv } });
ok(r.status === 410, "tek kullanımlık davet bitti");

// Gumroad
r = await call("/v1/license/redeem", { method: "POST", auth: "Bearer " + tok1b, body: { code: "AAAAAAAA-BBBBBBBB-CCCCCCCC-DDDDDDDD" } });
j = await r.json(); ok(r.status === 200 && j.how === "gumroad" && j.tier === "premium", "Gumroad satışı → süresiz premium");
r = await call("/v1/license/redeem", { method: "POST", auth: "Bearer " + tok2, body: { code: "AAAAAAAA-BBBBBBBB-CCCCCCCC-DDDDDDDD" } });
ok(r.status === 409, "aynı satış başka hesaba geçmez");
r = await call("/v1/license/redeem", { method: "POST", auth: "Bearer " + tok2, body: { code: "EEEEEEEE-FFFFFFFF-00000000-11111111" } });
ok(r.status === 402, "iade edilmiş satış reddedildi");
ok(!JSON.stringify(sql.prepare("SELECT note FROM licenses").all()).includes("buyer@x.com"), "alıcı e-postası maskelendi");

// kaba kuvvet sınırı
let last;
for (let i = 0; i < 12; i++) last = await call("/v1/license/redeem", { method: "POST", auth: "Bearer " + tok2, body: { code: "TD2K-0000-0000-0000-000" + (i % 10) } });
ok(last.status === 429, "anahtar tahmini sınırlandı (saatte 10)");

// engelleme
const acc2 = sql.prepare("SELECT id FROM accounts WHERE discord_id = '222222222222'").get().id;
await call(`/v1/admin/accounts/${acc2}/ban`, { ...A, method: "POST", body: { banned: true } });
ok((await call("/v1/me", { auth: "Bearer " + tok2 })).status === 401, "engellenen hesabın oturumu kapandı");

// liste + denetim
j = await (await call("/v1/admin/licenses", A)).json();
ok(j.licenses.length >= 5 && !JSON.stringify(j).includes("key_hash"), "lisans listesi (özetler dışarı verilmez)");
j = await (await call("/v1/admin/audit", A)).json();
ok(j.audit.some(a => a.action === "ban") && j.audit.some(a => a.action === "redeem"), "denetim kaydı tutuluyor");
j = await (await call("/v1/admin/stats", A)).json();
ok(j.accounts === 2, "istatistik: " + JSON.stringify(j));

// çıkış
await call("/v1/auth/logout", { method: "POST", auth: "Bearer " + tok1b });
ok((await call("/v1/me", { auth: "Bearer " + tok1b })).status === 401, "çıkıştan sonra oturum geçersiz");
// callback: süresi dolmuş/rastgele state
ok((await call("/v1/auth/callback?state=" + "z".repeat(40) + "&code=x")).status === 400, "bilinmeyen state reddedildi");

console.log(fails ? `RESULT: FAIL (${fails})` : "RESULT: PASS");
process.exit(fails ? 1 : 0);
