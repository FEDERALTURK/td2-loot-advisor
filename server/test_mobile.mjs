// Mobil companion bulut uçlarının testi (Faz 2): eşleştirme, telefon oturumu, masaüstü kuyruğu/olayları,
// build senkronu, push belirteci, cihaz/hesap iptali, periyodik temizlik.   node server/test_mobile.mjs
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { createHash, generateKeyPairSync, randomBytes } from "node:crypto";
import worker from "./worker.js";
import { cleanup as mobileCleanup } from "./mobile.js";

const sql = new DatabaseSync(":memory:");
sql.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
function stmt(q) {
  let args = [];
  const s = {
    bind(...a) { args = a; return s; },
    async run() { const r = sql.prepare(q).run(...args); return { meta: { changes: Number(r.changes) } }; },
    async first() { return sql.prepare(q).get(...args) ?? null; },
    async all() { return { results: sql.prepare(q).all(...args) }; },
    async batch(stmts) { return stmts; },
  };
  return s;
}
const DB = { prepare: stmt, async batch(list) { return Promise.all(list.map(s => s.run())); } };

const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const env = { DB, HASH_SALT: "t", DISCORD_CLIENT_ID: "123", DISCORD_CLIENT_SECRET: "sec",
  ENT_SIGNING_KEY: privateKey.export({ format: "der", type: "pkcs8" }).toString("base64"),
  ENT_PUBLIC_KEY: publicKey.export({ format: "der", type: "spki" }).subarray(-32).toString("hex"),
  ADMIN_TOKEN: "admin-token-very-long-random-xyz-123", GUMROAD_PRODUCT_ID: "prod",
  PUBLIC_URL: "https://w", LICENSE_PUBKEY: "00".repeat(32) };

let discordUser = { id: "222222222222", username: "soner", global_name: "Soner" };
globalThis.fetch = async (url, opts = {}) => {
  if (url.startsWith("https://discord.com/api/oauth2/token")) return Response.json({ access_token: "at" });
  if (url === "https://discord.com/api/users/@me") return Response.json(discordUser);
  return new Response("nf", { status: 404 });
};

let fails = 0;
const ok = (c, msg) => { console.log((c ? "OK   " : "FAIL ") + msg); if (!c) fails++; };
const b64u = b => Buffer.from(b).toString("base64url");
const call = (path, { method = "GET", body, auth } = {}) => worker.fetch(new Request("https://w" + path, {
  method, body: body ? JSON.stringify(body) : undefined,
  headers: { "cf-connecting-ip": "9.9.9.9", ...(auth ? { authorization: auth } : {}) } }), env);

async function desktopLogin(device) {
  const state = b64u(randomBytes(24)), verifier = b64u(randomBytes(32));
  const challenge = b64u(createHash("sha256").update(verifier).digest());
  await call("/v1/auth/start", { method: "POST", body: { state, challenge, port: 53682 } });
  const r = await call(`/v1/auth/callback?state=${state}&code=c1`);
  const grant = new URL(r.headers.get("location")).searchParams.get("grant");
  const p = await (await call("/v1/auth/token", { method: "POST", body: { state, verifier, grant, device } })).json();
  return p.token;
}

(async () => {
  const desktopToken = await desktopLogin(b64u(randomBytes(32)));
  ok(!!desktopToken, "masaüstü oturumu alındı (ön koşul)");
  const dAuth = "Bearer " + desktopToken;

  // --- eşleştirme
  let r = await call("/v1/mobile/pairings", { method: "POST" });
  ok(r.status === 401, "oturumsuz eşleştirme kodu alınamaz");
  r = await call("/v1/mobile/pairings", { method: "POST", auth: dAuth });
  const pair = await r.json();
  ok(r.status === 200 && /^[A-Z0-9]{1,8}$/.test(pair.code) && pair.expires_in === 300, "masaüstü eşleştirme kodu üretti");

  r = await call("/v1/mobile/pairings/claim", { method: "POST", body: { code: "WRONGCODE", platform: "android" } });
  ok(r.status === 410, "geçersiz kod reddedildi");

  r = await call("/v1/mobile/pairings/claim", { method: "POST", body: { code: pair.code, platform: "android" } });
  const claim = await r.json();
  ok(r.status === 200 && claim.device_id && claim.token, "telefon kodu claim etti, cihaz oturumu aldı");
  const pAuth = "Bearer " + claim.token;

  r = await call("/v1/mobile/pairings/claim", { method: "POST", body: { code: pair.code, platform: "android" } });
  ok(r.status === 410, "aynı eşleştirme kodu ikinci kez kullanılamaz (zaten claimed=1 işaretli)");

  // --- gösterge paneli: masaüstü henüz olay göndermeden
  r = await call("/v1/mobile/dashboard", { auth: pAuth });
  let dash = await r.json();
  ok(r.status === 200 && dash.desktop.online === false, "masaüstü olay göndermeden önce çevrimdışı görünür");

  // --- masaüstü olay gönderir → telefon panelde görür
  r = await call("/v1/mobile/desktop/events", { method: "POST", auth: dAuth,
    body: { type: "scan_result", slot: "Mask", decision: "keep" } });
  ok(r.status === 200, "masaüstü olay gönderdi");
  r = await call("/v1/mobile/dashboard", { auth: pAuth });
  dash = await r.json();
  ok(dash.desktop.online === true && dash.desktop.last_event.decision === "keep", "telefon panelde güncel olayı görüyor");

  // --- telefon → masaüstü komut kuyruğu
  r = await call("/v1/mobile/desktop/commands", { method: "POST", auth: pAuth, body: { command: "launch_nuke" } });
  ok(r.status === 400, "izin verilmeyen komut reddedildi");
  r = await call("/v1/mobile/desktop/commands", { method: "POST", auth: pAuth, body: { command: "scan_start" } });
  ok(r.status === 200, "izin verilen komut kuyruğa alındı");
  r = await call("/v1/mobile/desktop/inbox", { auth: dAuth });
  let inbox = await r.json();
  ok(inbox.commands.length === 1 && inbox.commands[0].command === "scan_start", "masaüstü kuyruktaki komutu aldı");
  r = await call("/v1/mobile/desktop/inbox", { auth: dAuth });
  inbox = await r.json();
  ok(inbox.commands.length === 0, "teslim edilen komut ikinci kez gelmiyor");

  // --- build senkronu
  const clientId = b64u(randomBytes(16));
  r = await call("/v1/mobile/builds", { method: "PUT", auth: pAuth,
    body: { client_id: clientId, name: "Tank build", payload: { slots: {} }, base_revision: 0 } });
  let put = await r.json();
  ok(r.status === 200 && put.revision === 1, "ilk build yazımı rev=1");
  r = await call("/v1/mobile/builds", { method: "PUT", auth: pAuth,
    body: { client_id: clientId, name: "Tank build v2", payload: { slots: { Mask: "x" } }, base_revision: 0 } });
  ok(r.status === 409, "bayat revizyonla yazım çakışması yakalandı");
  r = await call("/v1/mobile/builds", { method: "PUT", auth: pAuth,
    body: { client_id: clientId, name: "Tank build v2", payload: { slots: { Mask: "x" } }, base_revision: 1 } });
  put = await r.json();
  ok(r.status === 200 && put.revision === 2, "doğru revizyonla build güncellendi, rev=2");
  r = await call("/v1/mobile/builds", { auth: pAuth });
  const list = await r.json();
  ok(list.builds.length === 1 && list.builds[0].name === "Tank build v2", "build listesi güncel");

  // --- build silme (soft-delete, tombstone senkron için dönüyor)
  r = await call(`/v1/mobile/builds/${clientId}`, { method: "DELETE", auth: pAuth });
  const delBuild = await r.json();
  ok(r.status === 200 && delBuild.revision === 3, "build silindi, revizyon arttı");
  r = await call("/v1/mobile/builds", { auth: pAuth });
  const list2 = await r.json();
  ok(list2.builds.length === 1 && list2.builds[0].deleted === true, "silinen build tombstone olarak listede görünüyor");
  r = await call(`/v1/mobile/builds/${clientId}`, { method: "DELETE", auth: pAuth });
  ok(r.status === 200, "zaten silinmiş build tekrar silinebilir (idempotent)");
  r = await call(`/v1/mobile/builds/doesnotexist1234567890`, { method: "DELETE", auth: pAuth });
  ok(r.status === 404, "var olmayan build silme isteği 404 döner");

  // --- eşleştirilmiş cihazları listeleme (masaüstü)
  r = await call("/v1/mobile/devices", { auth: dAuth });
  const devs = await r.json();
  ok(r.status === 200 && devs.devices.length === 1 && devs.devices[0].device_id === claim.device_id,
     "masaüstü eşleştirilmiş telefonu listede görüyor");
  r = await call("/v1/mobile/devices");
  ok(r.status === 401, "oturumsuz cihaz listesi alınamaz");

  // --- push belirteci (gönderim yok, sadece saklama — bilerek)
  r = await call(`/v1/mobile/push-tokens/${claim.device_id}`, { method: "PUT", auth: pAuth, body: { token: "fcm-abc" } });
  const pushRes = await r.json();
  ok(r.status === 200 && pushRes.delivery === "not_yet_implemented", "push belirteci saklandı, gönderim henüz yok (dürüst durum)");
  r = await call(`/v1/mobile/push-tokens/${claim.device_id}`, { method: "DELETE", auth: pAuth });
  ok(r.status === 200, "push belirteci silindi");

  // --- cihaz iptali (masaüstünden)
  r = await call(`/v1/mobile/devices/${claim.device_id}`, { method: "DELETE", auth: dAuth });
  ok(r.status === 200, "masaüstü telefon cihazını iptal etti");
  r = await call("/v1/mobile/dashboard", { auth: pAuth });
  ok(r.status === 401, "iptal edilen telefon oturumu artık geçersiz");
  r = await call("/v1/mobile/devices", { auth: dAuth });
  const devsAfter = await r.json();
  ok(devsAfter.devices.length === 0, "iptal edilen cihaz artık listede görünmüyor");

  // --- yeniden eşleştir, sonra hesap silme talebi + bekleme süresi + gerçek silme
  r = await call("/v1/mobile/pairings", { method: "POST", auth: dAuth });
  const pair2 = await (await call("/v1/mobile/pairings", { method: "POST", auth: dAuth })).json();
  const claim2 = await (await call("/v1/mobile/pairings/claim", { method: "POST", body: { code: pair2.code, platform: "ios" } })).json();
  r = await call("/v1/mobile/me", { method: "DELETE", auth: "Bearer " + claim2.token });
  ok(r.status === 200, "telefon hesap silme talebinde bulundu");
  r = await call("/v1/mobile/dashboard", { auth: "Bearer " + claim2.token });
  ok(r.status === 401, "silme talebinden sonra telefon oturumu hemen iptal edilir");
  let row = sql.prepare("SELECT * FROM account_deletions").get();
  ok(!!row, "silme talebi kayda geçti (bekleme süresi başladı)");
  sql.prepare("UPDATE account_deletions SET requested = requested - 100000").run();   // bekleme süresini geçmiş say
  const cl = await mobileCleanup(env);
  ok(cl.deleted_accounts === 1, "bekleme süresi dolan hesap gerçekten silindi");
  row = sql.prepare("SELECT * FROM accounts WHERE id = ?").get(row.account_id);
  ok(!row, "accounts satırı kalıcı olarak silindi");

  console.log(fails ? `\n${fails} FAIL` : "\nAll mobile tests passed");
  process.exit(fails ? 1 : 0);
})();
