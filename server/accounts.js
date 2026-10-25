// Hesaplar, Discord ile giriş, lisans anahtarları, davet kodları, satış (Gumroad) ve yönetici uçları.
//
// Güvenlik ilkeleri
//  - Şifre yok: giriş Discord OAuth2. İstemci "verifier" üretir, sunucuya yalnız SHA-256'sını verir (PKCE benzeri);
//    Discord dönüşü tek kullanımlık bir "grant" ile kullanıcının KENDİ bilgisayarındaki programa (127.0.0.1) yönlenir
//    (RFC 8252). Oturum için verifier + grant birlikte gerekir: bağlantıyı başkasına tıklatmak oturum vermez.
//  - Oturum belirteçleri, lisans anahtarları ve davet kodları veritabanında YALNIZ SHA-256 özetleriyle durur.
//  - Cihaz kimliği istemcide özetlenir, sunucuda tuzla bir kez daha özetlenir.
//  - Yetki belgesi (entitlement) Ed25519 ile imzalanır (gizli ENT_SIGNING_KEY), cihaza bağlıdır ve 7 gün geçerlidir;
//    program internetsiz doğrular. Yayıncının eski TD2P anahtarları ayrıca geçerli kalır.
//  - Anahtar/davet denemeleri hesap + IP başına sınırlı (kaba kuvvet), girişler IP başına sınırlı.
//  - Yönetici uçları ayrı bir gizli belirteçle (ADMIN_TOKEN) korunur; her yönetici işlemi denetim kaydına yazılır.
//
// Ortam: DISCORD_CLIENT_ID (değişken), DISCORD_CLIENT_SECRET (gizli), ENT_SIGNING_KEY (gizli, PKCS8 base64),
//        ENT_PUBLIC_KEY (değişken, hex), ADMIN_TOKEN (gizli), GUMROAD_PRODUCT_ID (değişken, isteğe bağlı),
//        HASH_SALT (gizli), PUBLIC_URL (değişken, ör. https://td2-stats.td2loot.workers.dev)

const enc = new TextEncoder();
const DAY = 86400;
const ENT_DAYS = 7;
const TIERS = new Set(["premium"]);
const B64U = /^[A-Za-z0-9_\-]{32,128}$/;

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra },
  });
}
const now = () => Math.floor(Date.now() / 1000);

async function sha256(text) {
  const d = await crypto.subtle.digest("SHA-256", enc.encode(text));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("");
}
async function shaB64u(text) {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(text)));
  return b64uEnc(d);
}
function b64uEnc(bytes) {
  let s = ""; for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function b64uDec(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/"); s += "=".repeat((4 - s.length % 4) % 4);
  return Uint8Array.from(atob(s), c => c.charCodeAt(0));
}
function randomToken(n = 32) { return b64uEnc(crypto.getRandomValues(new Uint8Array(n))); }
function safeEqual(a, b) {                           // sabit süreli karşılaştırma (eşit uzunluklu özetler)
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let r = 0; for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}
const salt = env => env.HASH_SALT || "dev-salt";
const ipOf = req => req.headers.get("cf-connecting-ip") || "local";

// Anahtar biçimi: TD2K-XXXX-XXXX-XXXX-XXXX (Crockford base32: karışan harfler yok), davet: TD2I-XXXX-XXXX-XXXX
const ALPH = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
function humanCode(prefix, groups) {
  const b = crypto.getRandomValues(new Uint8Array(groups * 4));
  const g = []; for (let i = 0; i < groups; i++) g.push([...b.slice(i * 4, i * 4 + 4)].map(x => ALPH[x % 32]).join(""));
  return prefix + "-" + g.join("-");
}
function normCode(s) {                               // büyük harf, ayırıcısız; önekten sonra O→0, I/L→1 (karışan harfler)
  const c = String(s || "").toUpperCase().replace(/[^0-9A-Z]/g, "");
  const m = /^(TD2[KI])(.*)$/.exec(c);
  return m ? m[1] + m[2].replace(/O/g, "0").replace(/[IL]/g, "1") : c;
}

async function rate(env, bucket, max, windowSec = 3600) {
  const slot = Math.floor(Date.now() / 1000 / windowSec);
  const row = await env.DB.prepare(
    "INSERT INTO rate (bucket, hour, n) VALUES (?1, ?2, 1) ON CONFLICT(bucket, hour) DO UPDATE SET n = n + 1 RETURNING n"
  ).bind("a:" + bucket, slot).first();
  return (row?.n ?? 1) <= max;
}

async function audit(env, actor, action, detail) {
  await env.DB.prepare("INSERT INTO audit (t, actor, action, detail) VALUES (?1, ?2, ?3, ?4)")
    .bind(now(), actor, action, JSON.stringify(detail || {}).slice(0, 2000)).run();
}

// ------------------------------------------------------------ yetki belgesi (Ed25519)
let _signKey = null;
async function signKey(env) {
  if (!_signKey) _signKey = await crypto.subtle.importKey("pkcs8", b64uDec(env.ENT_SIGNING_KEY.replace(/\s/g, "")),
                                                          { name: "Ed25519" }, false, ["sign"]);
  return _signKey;
}
async function signEntitlement(env, payload) {
  const raw = enc.encode(JSON.stringify(payload));
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, await signKey(env), raw));
  return "TD2E-" + b64uEnc(raw) + "." + b64uEnc(sig);
}
export async function verifyEntitlement(env, token) {
  const m = /^TD2E-([A-Za-z0-9_\-]+)\.([A-Za-z0-9_\-]+)$/.exec(token || "");
  if (!m || !env.ENT_PUBLIC_KEY) return null;
  try {
    const raw = b64uDec(m[1]);
    const pub = Uint8Array.from(env.ENT_PUBLIC_KEY.match(/../g).map(h => parseInt(h, 16)));
    const key = await crypto.subtle.importKey("raw", pub, { name: "Ed25519" }, false, ["verify"]);
    if (!(await crypto.subtle.verify({ name: "Ed25519" }, key, b64uDec(m[2]), raw))) return null;
    const p = JSON.parse(new TextDecoder().decode(raw));
    return p.exp && now() <= p.exp ? p : null;
  } catch { return null; }
}

// ------------------------------------------------------------ oturum
async function session(req, env) {
  const m = /^Bearer\s+([A-Za-z0-9_\-]{32,128})$/.exec(req.headers.get("authorization") || "");
  if (!m) return null;
  const th = await sha256(m[1]);
  const s = await env.DB.prepare(
    "SELECT s.token_hash, s.account_id, s.device_hash, s.device_pub, s.expires, a.username, a.avatar, a.discord_id, a.banned " +
    "FROM sessions s JOIN accounts a ON a.id = s.account_id WHERE s.token_hash = ?1 AND s.revoked = 0").bind(th).first();
  if (!s || s.expires < now() || s.banned) return null;
  await env.DB.prepare("UPDATE sessions SET last_seen = ?1 WHERE token_hash = ?2").bind(now(), th).run();
  return s;
}
async function devicePub(raw) { return (await sha256("td2e:" + raw)).slice(0, 32); }   // belgede; program kendisi doğrular
async function deviceHash(env, raw) {
  if (typeof raw !== "string" || !B64U.test(raw)) return null;
  return (await sha256(salt(env) + ":d:" + raw)).slice(0, 40);
}

// ------------------------------------------------------------ Discord ile giriş
async function authStart(req, env) {
  let b; try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const port = parseInt(b?.port, 10);
  if (!B64U.test(b?.state || "") || !B64U.test(b?.challenge || "") || !(port >= 1024 && port <= 65535))
    return json({ error: "bad request" }, 400);
  if (!env.DISCORD_CLIENT_ID) return json({ error: "login not configured" }, 503);
  if (!(await rate(env, "start:" + (await sha256(salt(env) + ipOf(req))).slice(0, 24), 30))) return json({ error: "rate limited" }, 429);
  await env.DB.prepare("DELETE FROM auth_pending WHERE created < ?1").bind(now() - 900).run();
  await env.DB.prepare("INSERT INTO auth_pending (state, challenge, created, port) VALUES (?1, ?2, ?3, ?4)")
    .bind(b.state, b.challenge, now(), port).run();
  const q = new URLSearchParams({ client_id: env.DISCORD_CLIENT_ID, response_type: "code", scope: "identify",
                                  redirect_uri: redirectUri(env, req), state: b.state, prompt: "consent" });
  return json({ url: "https://discord.com/oauth2/authorize?" + q.toString(), expires_in: 600 });
}
function redirectUri(env, req) { return (env.PUBLIC_URL || new URL(req.url).origin).replace(/\/$/, "") + "/v1/auth/callback"; }

function page(title, msg, ok) {
  const c = ok ? "#22c55e" : "#ef4444";
  return new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${title}</title>
<body style="background:#0f1116;color:#e7e9ee;font-family:Segoe UI,system-ui,sans-serif;display:grid;place-items:center;height:100vh;margin:0">
<div style="text-align:center;max-width:460px;padding:24px"><div style="font-size:48px;color:${c}">${ok ? "✔" : "✖"}</div>
<h2 style="margin:8px 0">${title}</h2><p style="color:#9aa1ae">${msg}</p></div>`,
    { status: ok ? 200 : 400, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store",
      "content-security-policy": "default-src 'none'; style-src 'unsafe-inline'", "x-frame-options": "DENY" } });
}

async function authCallback(req, env) {
  const u = new URL(req.url);
  const state = u.searchParams.get("state") || "", code = u.searchParams.get("code") || "";
  const p = B64U.test(state) ? await env.DB.prepare("SELECT * FROM auth_pending WHERE state = ?1").bind(state).first() : null;
  if (!p || p.created < now() - 600 || p.done) return page("Giriş başarısız / Login failed", "Bağlantının süresi doldu. Programdan yeniden deneyin. / Link expired — try again from the app.", false);
  if (!code) {
    await env.DB.prepare("DELETE FROM auth_pending WHERE state = ?1").bind(state).run();
    return page("Giriş iptal edildi / Login cancelled", "Programa dönebilirsiniz. / You can return to the app.", false);
  }
  const tr = await fetch("https://discord.com/api/oauth2/token", {
    method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_id: env.DISCORD_CLIENT_ID, client_secret: env.DISCORD_CLIENT_SECRET,
                                grant_type: "authorization_code", code, redirect_uri: redirectUri(env, req) }) });
  if (!tr.ok) return page("Giriş başarısız / Login failed", "Discord yanıt vermedi. / Discord did not respond.", false);
  const tok = await tr.json();
  const ur = await fetch("https://discord.com/api/users/@me", { headers: { authorization: "Bearer " + tok.access_token } });
  if (!ur.ok) return page("Giriş başarısız / Login failed", "Discord hesabı okunamadı. / Could not read the Discord account.", false);
  const du = await ur.json();
  if (!/^\d{5,25}$/.test(du.id || "")) return page("Giriş başarısız / Login failed", "Geçersiz hesap. / Invalid account.", false);
  const name = String(du.global_name || du.username || "agent").slice(0, 40);
  const acc = await env.DB.prepare(
    "INSERT INTO accounts (discord_id, username, avatar, created, last_login) VALUES (?1, ?2, ?3, ?4, ?4) " +
    "ON CONFLICT(discord_id) DO UPDATE SET username = ?2, avatar = ?3, last_login = ?4 RETURNING id, banned")
    .bind(du.id, name, du.avatar || null, now()).first();
  if (acc.banned) {
    await env.DB.prepare("DELETE FROM auth_pending WHERE state = ?1").bind(state).run();
    return page("Hesap engelli / Account blocked", "Bu hesap kullanılamıyor. / This account is blocked.", false);
  }
  // Tek kullanımlık "grant" yalnız bu tarayıcının kendi bilgisayarındaki programa (127.0.0.1) gider (RFC 8252).
  // Giriş bağlantısını başkasına tıklatan biri grant'i alamaz: yönlendirme kurbanın kendi bilgisayarına düşer.
  const grant = randomToken(24);
  await env.DB.prepare("UPDATE auth_pending SET done = 1, account_id = ?1, grant_hash = ?2 WHERE state = ?3")
    .bind(acc.id, await sha256(grant), state).run();
  return new Response(null, { status: 302, headers: { "cache-control": "no-store", "referrer-policy": "no-referrer",
    location: `http://127.0.0.1:${p.port}/callback?state=${state}&grant=${grant}` } });
}

async function authToken(req, env) {
  let b; try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  if (!B64U.test(b?.state || "") || !B64U.test(b?.verifier || "") || !B64U.test(b?.grant || "")) return json({ error: "bad request" }, 400);
  if (!(await rate(env, "tok:" + (await sha256(salt(env) + ipOf(req))).slice(0, 24), 60))) return json({ error: "rate limited" }, 429);
  const p = await env.DB.prepare("SELECT * FROM auth_pending WHERE state = ?1").bind(b.state).first();
  if (!p || p.created < now() - 600 || !p.done || !p.account_id) return json({ error: "expired" }, 410);
  const vOk = safeEqual(await shaB64u(b.verifier), p.challenge), gOk = safeEqual(await sha256(b.grant), p.grant_hash || "");
  await env.DB.prepare("DELETE FROM auth_pending WHERE state = ?1").bind(b.state).run();     // tek deneme hakkı
  if (!vOk || !gOk) return json({ error: "proof mismatch" }, 403);
  const dh = await deviceHash(env, b.device);
  if (!dh) return json({ error: "device required" }, 400);
  const token = randomToken(32);
  const dp = await devicePub(b.device);
  await env.DB.prepare("INSERT INTO sessions (token_hash, account_id, device_hash, device_pub, created, expires, last_seen) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?5)")
    .bind(await sha256(token), p.account_id, dh, dp, now(), now() + 30 * DAY).run();
  await audit(env, "acc:" + p.account_id, "login", {});
  return json({ status: "ok", token, ...(await meData(env, p.account_id, dh, dp)) });
}

async function logout(req, env) {
  const s = await session(req, env);
  if (s) await env.DB.prepare("UPDATE sessions SET revoked = 1 WHERE token_hash = ?1").bind(s.token_hash).run();
  return json({ ok: true });
}

// ------------------------------------------------------------ hesap durumu + yetki belgesi
async function activeLicense(env, accountId) {
  const rows = (await env.DB.prepare(
    "SELECT * FROM licenses WHERE account_id = ?1 AND revoked = 0 AND (expires IS NULL OR expires > ?2) ORDER BY expires IS NULL DESC, expires DESC")
    .bind(accountId, now()).all()).results || [];
  return rows[0] || null;
}

async function bindDevice(env, lic, dh) {
  const has = await env.DB.prepare("SELECT 1 FROM devices WHERE license_id = ?1 AND device_hash = ?2").bind(lic.id, dh).first();
  if (has) { await env.DB.prepare("UPDATE devices SET last_seen = ?1 WHERE license_id = ?2 AND device_hash = ?3").bind(now(), lic.id, dh).run(); return true; }
  const n = (await env.DB.prepare("SELECT COUNT(*) AS n FROM devices WHERE license_id = ?1").bind(lic.id).first()).n;
  if (n >= (lic.max_devices || 1)) return false;
  await env.DB.prepare("INSERT INTO devices (license_id, device_hash, first_seen, last_seen) VALUES (?1, ?2, ?3, ?3)").bind(lic.id, dh, now()).run();
  return true;
}

async function meData(env, accountId, dh, dp) {
  const a = await env.DB.prepare("SELECT id, username, avatar, discord_id, created FROM accounts WHERE id = ?1").bind(accountId).first();
  const lic = await activeLicense(env, accountId);
  const out = { account: { username: a.username, avatar: a.avatar, discord_id: a.discord_id, since: a.created }, tier: "free",
                license: null, entitlement: null };
  if (!lic) return out;
  out.license = { hint: lic.key_hint, tier: lic.tier, expires: lic.expires, source: lic.source, max_devices: lic.max_devices };
  if (!(await bindDevice(env, lic, dh))) { out.device_limit = true; return out; }
  const exp = Math.min(lic.expires || Infinity, now() + ENT_DAYS * DAY);
  out.tier = lic.tier;
  out.entitlement = await signEntitlement(env, { v: 1, acc: String(a.id), name: a.username, tier: lic.tier, dev: dp,
                                                 lic_exp: lic.expires || null, exp, iat: now() });
  return out;
}

async function me(req, env) {
  const s = await session(req, env);
  if (!s) return json({ error: "unauthorized" }, 401);
  return json(await meData(env, s.account_id, s.device_hash, s.device_pub));
}

// ------------------------------------------------------------ anahtar / davet / satış
async function redeem(req, env) {
  const s = await session(req, env);
  if (!s) return json({ error: "unauthorized" }, 401);
  let b; try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const ipb = (await sha256(salt(env) + ipOf(req))).slice(0, 24);
  if (!(await rate(env, "redeem:acc:" + s.account_id, 10)) || !(await rate(env, "redeem:ip:" + ipb, 20)))
    return json({ error: "too many attempts", retry_after: 3600 }, 429);
  const code = normCode(b?.code);
  let lic = null, how = null;
  if (/^TD2K[0-9A-Z]{16}$/.test(code)) {                                   // yönetici anahtarı
    const kh = await sha256("k:" + code);
    lic = await env.DB.prepare("SELECT * FROM licenses WHERE key_hash = ?1").bind(kh).first();
    if (!lic || lic.revoked) return json({ error: "invalid key" }, 404);
    if (lic.account_id && lic.account_id !== s.account_id) return json({ error: "key already used" }, 409);
    if (!lic.account_id) {
      const exp = lic.duration_days ? now() + lic.duration_days * DAY : lic.expires;
      const r = await env.DB.prepare("UPDATE licenses SET account_id = ?1, redeemed = ?2, expires = ?3 WHERE id = ?4 AND account_id IS NULL")
        .bind(s.account_id, now(), exp, lic.id).run();
      if (!r.meta?.changes) return json({ error: "key already used" }, 409);
    }
    how = "key";
  } else if (/^TD2I[0-9A-Z]{12}$/.test(code)) {                            // davet / hediye kodu
    const ch = await sha256("i:" + code);
    const inv = await env.DB.prepare("SELECT * FROM invites WHERE code_hash = ?1").bind(ch).first();
    if (!inv || inv.revoked || (inv.expires && inv.expires < now())) return json({ error: "invalid code" }, 404);
    const used = await env.DB.prepare("SELECT 1 FROM licenses WHERE source = 'invite' AND source_ref = ?1 AND account_id = ?2")
      .bind(String(inv.id), s.account_id).first();
    if (used) return json({ error: "code already used by this account" }, 409);
    const r = await env.DB.prepare("UPDATE invites SET uses_left = uses_left - 1 WHERE id = ?1 AND uses_left > 0").bind(inv.id).run();
    if (!r.meta?.changes) return json({ error: "code used up" }, 410);
    await env.DB.prepare("INSERT INTO licenses (key_hash, key_hint, tier, created, expires, account_id, redeemed, max_devices, source, source_ref, note) " +
                         "VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?4, 1, 'invite', ?7, ?8)")
      .bind(await sha256("inv:" + inv.id + ":" + s.account_id), "INV" + inv.id, inv.tier, now(),
            inv.duration_days ? now() + inv.duration_days * DAY : null, s.account_id, String(inv.id), inv.note || null).run();
    how = "invite";
  } else if (env.GUMROAD_PRODUCT_ID && /^[0-9A-Z]{32}$/.test(code)) {      // Gumroad lisans anahtarı (8-8-8-8)
    const gr = await fetch("https://api.gumroad.com/v2/licenses/verify", {
      method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ product_id: env.GUMROAD_PRODUCT_ID, license_key: String(b.code).trim(), increment_uses_count: "false" }) });
    const g = await gr.json().catch(() => ({}));
    const pu = g.purchase || {};
    if (!g.success || pu.refunded || pu.chargebacked || pu.disputed || pu.subscription_cancelled_at || pu.subscription_failed_at)
      return json({ error: "purchase not valid" }, 402);
    const ref = String(pu.sale_id || pu.id || code);
    const exist = await env.DB.prepare("SELECT account_id FROM licenses WHERE source = 'gumroad' AND source_ref = ?1").bind(ref).first();
    if (exist && exist.account_id !== s.account_id) return json({ error: "key already used" }, 409);
    if (!exist)
      await env.DB.prepare("INSERT INTO licenses (key_hash, key_hint, tier, created, expires, account_id, redeemed, max_devices, source, source_ref, note) " +
                           "VALUES (?1, ?2, 'premium', ?3, NULL, ?4, ?3, 1, 'gumroad', ?5, ?6)")
        .bind(await sha256("g:" + code), code.slice(-4), now(), s.account_id, ref, String(pu.email || "").replace(/(^.).*(@.*$)/, "$1***$2")).run();
    how = "gumroad";
  } else {
    return json({ error: "unrecognised code" }, 400);
  }
  await audit(env, "acc:" + s.account_id, "redeem", { how });
  const out = await meData(env, s.account_id, s.device_hash, s.device_pub);
  return json({ ok: true, how, ...out });
}

// ------------------------------------------------------------ yönetici
async function isAdmin(req, env) {
  const m = /^Admin\s+(\S{24,200})$/.exec(req.headers.get("authorization") || "");
  if (!m || !env.ADMIN_TOKEN) return false;
  return safeEqual(await sha256(m[1]), await sha256(env.ADMIN_TOKEN));
}

async function admin(req, env, path) {
  const ipb = (await sha256(salt(env) + ipOf(req))).slice(0, 24);
  if (!(await isAdmin(req, env))) {
    await rate(env, "adminfail:" + ipb, 1000);
    return json({ error: "forbidden" }, 403);
  }
  const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};
  const u = new URL(req.url); const q = (u.searchParams.get("q") || "").slice(0, 60);
  let m;
  if (path === "accounts" && req.method === "GET") {
    const rows = (await env.DB.prepare(
      "SELECT a.id, a.discord_id, a.username, a.created, a.last_login, a.banned, " +
      "(SELECT COUNT(*) FROM licenses l WHERE l.account_id = a.id AND l.revoked = 0 AND (l.expires IS NULL OR l.expires > ?2)) AS active " +
      "FROM accounts a WHERE a.username LIKE ?1 OR a.discord_id = ?3 ORDER BY a.last_login DESC LIMIT 500")
      .bind("%" + q + "%", now(), q).all()).results;
    return json({ accounts: rows });
  }
  if ((m = /^accounts\/(\d+)\/ban$/.exec(path)) && req.method === "POST") {
    await env.DB.prepare("UPDATE accounts SET banned = ?1 WHERE id = ?2").bind(body.banned ? 1 : 0, +m[1]).run();
    if (body.banned) await env.DB.prepare("UPDATE sessions SET revoked = 1 WHERE account_id = ?1").bind(+m[1]).run();
    await audit(env, "admin", body.banned ? "ban" : "unban", { account: +m[1] });
    return json({ ok: true });
  }
  if (path === "licenses" && req.method === "GET") {
    const rows = (await env.DB.prepare(
      "SELECT l.id, l.key_hint, l.tier, l.created, l.expires, l.duration_days, l.redeemed, l.max_devices, l.source, l.note, l.revoked, " +
      "a.username, a.id AS account_id, (SELECT COUNT(*) FROM devices d WHERE d.license_id = l.id) AS devices " +
      "FROM licenses l LEFT JOIN accounts a ON a.id = l.account_id WHERE ?1 = '' OR a.username LIKE ?2 OR l.key_hint = ?1 OR l.note LIKE ?2 " +
      "ORDER BY l.created DESC LIMIT 1000").bind(q, "%" + q + "%").all()).results;
    return json({ licenses: rows });
  }
  if (path === "licenses" && req.method === "POST") {
    const n = Math.max(1, Math.min(100, parseInt(body.count || 1, 10)));
    const tier = TIERS.has(body.tier) ? body.tier : "premium";
    const days = body.days ? Math.max(1, Math.min(3650, parseInt(body.days, 10))) : null;
    const note = String(body.note || "").slice(0, 120);
    const keys = [];
    for (let i = 0; i < n; i++) {
      const key = humanCode("TD2K", 4), nk = normCode(key);
      await env.DB.prepare("INSERT INTO licenses (key_hash, key_hint, tier, created, duration_days, max_devices, source, note) VALUES (?1, ?2, ?3, ?4, ?5, ?6, 'admin', ?7)")
        .bind(await sha256("k:" + nk), nk.slice(-4), tier, now(), days, Math.max(1, Math.min(5, parseInt(body.max_devices || 1, 10))), note).run();
      keys.push(key);
    }
    await audit(env, "admin", "create_keys", { n, tier, days, note });
    return json({ keys });                                    // düz anahtarlar YALNIZ bu yanıtta görünür
  }
  if ((m = /^licenses\/(\d+)\/(revoke|unrevoke|reset_devices|extend)$/.exec(path)) && req.method === "POST") {
    const id = +m[1];
    if (m[2] === "revoke" || m[2] === "unrevoke") await env.DB.prepare("UPDATE licenses SET revoked = ?1 WHERE id = ?2").bind(m[2] === "revoke" ? 1 : 0, id).run();
    if (m[2] === "reset_devices") await env.DB.prepare("DELETE FROM devices WHERE license_id = ?1").bind(id).run();
    if (m[2] === "extend") {
      const d = Math.max(1, Math.min(3650, parseInt(body.days || 30, 10)));
      await env.DB.prepare("UPDATE licenses SET expires = CASE WHEN expires IS NULL THEN NULL ELSE MAX(expires, ?1) + ?2 END, " +
                           "duration_days = CASE WHEN account_id IS NULL AND duration_days IS NOT NULL THEN duration_days + ?3 ELSE duration_days END WHERE id = ?4")
        .bind(now(), d * DAY, d, id).run();
    }
    await audit(env, "admin", m[2], { license: id, days: body.days });
    return json({ ok: true });
  }
  if (path === "invites" && req.method === "GET") {
    return json({ invites: (await env.DB.prepare("SELECT id, code_hint, tier, duration_days, uses_left, expires, created, note, revoked FROM invites ORDER BY created DESC LIMIT 500").all()).results });
  }
  if (path === "invites" && req.method === "POST") {
    const code = humanCode("TD2I", 3), nc = normCode(code);
    const uses = Math.max(1, Math.min(10000, parseInt(body.uses || 1, 10)));
    const days = body.days ? Math.max(1, Math.min(3650, parseInt(body.days, 10))) : null;
    const exp = body.valid_days ? now() + Math.max(1, Math.min(365, parseInt(body.valid_days, 10))) * DAY : null;
    await env.DB.prepare("INSERT INTO invites (code_hash, code_hint, tier, duration_days, uses_left, expires, created, note) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)")
      .bind(await sha256("i:" + nc), nc.slice(-4), TIERS.has(body.tier) ? body.tier : "premium", days, uses, exp, now(), String(body.note || "").slice(0, 120)).run();
    await audit(env, "admin", "create_invite", { uses, days, note: body.note });
    return json({ code });
  }
  if ((m = /^invites\/(\d+)\/revoke$/.exec(path)) && req.method === "POST") {
    await env.DB.prepare("UPDATE invites SET revoked = 1 WHERE id = ?1").bind(+m[1]).run();
    await audit(env, "admin", "revoke_invite", { invite: +m[1] });
    return json({ ok: true });
  }
  if (path === "audit" && req.method === "GET") {
    return json({ audit: (await env.DB.prepare("SELECT t, actor, action, detail FROM audit ORDER BY id DESC LIMIT 300").all()).results });
  }
  if (path === "stats" && req.method === "GET") {
    const one = async sqlq => (await env.DB.prepare(sqlq).bind(now()).first()).n;
    return json({ accounts: await one("SELECT COUNT(*) AS n FROM accounts WHERE ?1 > 0"),
                  active_licenses: await one("SELECT COUNT(*) AS n FROM licenses WHERE revoked = 0 AND account_id IS NOT NULL AND (expires IS NULL OR expires > ?1)"),
                  unused_keys: await one("SELECT COUNT(*) AS n FROM licenses WHERE account_id IS NULL AND revoked = 0 AND ?1 > 0"),
                  logins_24h: await one("SELECT COUNT(*) AS n FROM accounts WHERE last_login > ?1 - 86400") });
  }
  return json({ error: "not found" }, 404);
}

// ------------------------------------------------------------ yönlendirme
export async function route(req, env, path) {
  if (path === "/v1/auth/start" && req.method === "POST") return authStart(req, env);
  if (path === "/v1/auth/callback" && req.method === "GET") return authCallback(req, env);
  if (path === "/v1/auth/token" && req.method === "POST") return authToken(req, env);
  if (path === "/v1/auth/logout" && req.method === "POST") return logout(req, env);
  if (path === "/v1/me" && req.method === "GET") return me(req, env);
  if (path === "/v1/license/redeem" && req.method === "POST") return redeem(req, env);
  if (path.startsWith("/v1/admin/")) return admin(req, env, path.slice(10));
  return null;
}
