var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// accounts.js
var enc = new TextEncoder();
var DAY = 86400;
var ENT_DAYS = 7;
var TIERS = /* @__PURE__ */ new Set(["premium"]);
var B64U = /^[A-Za-z0-9_\-]{32,128}$/;
function json(data, status = 200, extra = {}) {
  const noBody = status === 204 || status === 205 || status === 304;
  return new Response(noBody ? null : JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      ...extra
    }
  });
}
__name(json, "json");
var now = /* @__PURE__ */ __name(() => Math.floor(Date.now() / 1e3), "now");
async function sha256(text) {
  const d = await crypto.subtle.digest("SHA-256", enc.encode(text));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
__name(sha256, "sha256");
async function shaB64u(text) {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(text)));
  return b64uEnc(d);
}
__name(shaB64u, "shaB64u");
function b64uEnc(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
__name(b64uEnc, "b64uEnc");
function b64uDec(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  s += "=".repeat((4 - s.length % 4) % 4);
  return Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
}
__name(b64uDec, "b64uDec");
function randomToken(n = 32) {
  return b64uEnc(crypto.getRandomValues(new Uint8Array(n)));
}
__name(randomToken, "randomToken");
function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}
__name(safeEqual, "safeEqual");
var salt = /* @__PURE__ */ __name((env) => env.HASH_SALT || "dev-salt", "salt");
var ipOf = /* @__PURE__ */ __name((req) => req.headers.get("cf-connecting-ip") || "local", "ipOf");
var ALPH = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
function humanCode(prefix, groups) {
  const b = crypto.getRandomValues(new Uint8Array(groups * 4));
  const g = [];
  for (let i = 0; i < groups; i++) g.push([...b.slice(i * 4, i * 4 + 4)].map((x) => ALPH[x % 32]).join(""));
  return prefix + "-" + g.join("-");
}
__name(humanCode, "humanCode");
function normCode(s) {
  const c = String(s || "").toUpperCase().replace(/[^0-9A-Z]/g, "");
  const m = /^(TD2[KI])(.*)$/.exec(c);
  return m ? m[1] + m[2].replace(/O/g, "0").replace(/[IL]/g, "1") : c;
}
__name(normCode, "normCode");
async function rate(env, bucket, max, windowSec = 3600) {
  const slot = Math.floor(Date.now() / 1e3 / windowSec);
  const row = await env.DB.prepare(
    "INSERT INTO rate (bucket, hour, n) VALUES (?1, ?2, 1) ON CONFLICT(bucket, hour) DO UPDATE SET n = n + 1 RETURNING n"
  ).bind("a:" + bucket, slot).first();
  return (row?.n ?? 1) <= max;
}
__name(rate, "rate");
async function audit(env, actor, action, detail) {
  await env.DB.prepare("INSERT INTO audit (t, actor, action, detail) VALUES (?1, ?2, ?3, ?4)").bind(now(), actor, action, JSON.stringify(detail || {}).slice(0, 2e3)).run();
}
__name(audit, "audit");
var _signKey = null;
async function signKey(env) {
  if (!_signKey) _signKey = await crypto.subtle.importKey(
    "pkcs8",
    b64uDec(env.ENT_SIGNING_KEY.replace(/\s/g, "")),
    { name: "Ed25519" },
    false,
    ["sign"]
  );
  return _signKey;
}
__name(signKey, "signKey");
async function signEntitlement(env, payload) {
  const raw = enc.encode(JSON.stringify(payload));
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, await signKey(env), raw));
  return "TD2E-" + b64uEnc(raw) + "." + b64uEnc(sig);
}
__name(signEntitlement, "signEntitlement");
async function verifyEntitlement(env, token) {
  const m = /^TD2E-([A-Za-z0-9_\-]+)\.([A-Za-z0-9_\-]+)$/.exec(token || "");
  if (!m || !env.ENT_PUBLIC_KEY) return null;
  try {
    const raw = b64uDec(m[1]);
    const pub = Uint8Array.from(env.ENT_PUBLIC_KEY.match(/../g).map((h) => parseInt(h, 16)));
    const key = await crypto.subtle.importKey("raw", pub, { name: "Ed25519" }, false, ["verify"]);
    if (!await crypto.subtle.verify({ name: "Ed25519" }, key, b64uDec(m[2]), raw)) return null;
    const p = JSON.parse(new TextDecoder().decode(raw));
    return p.exp && now() <= p.exp ? p : null;
  } catch {
    return null;
  }
}
__name(verifyEntitlement, "verifyEntitlement");
async function session(req, env) {
  const m = /^Bearer\s+([A-Za-z0-9_\-]{32,128})$/.exec(req.headers.get("authorization") || "");
  if (!m) return null;
  const th = await sha256(m[1]);
  const s = await env.DB.prepare(
    "SELECT s.token_hash, s.account_id, s.device_hash, s.device_pub, s.expires, a.username, a.avatar, a.discord_id, a.banned FROM sessions s JOIN accounts a ON a.id = s.account_id WHERE s.token_hash = ?1 AND s.revoked = 0"
  ).bind(th).first();
  if (!s || s.expires < now() || s.banned) return null;
  await env.DB.prepare("UPDATE sessions SET last_seen = ?1 WHERE token_hash = ?2").bind(now(), th).run();
  return s;
}
__name(session, "session");
async function devicePub(raw) {
  return (await sha256("td2e:" + raw)).slice(0, 32);
}
__name(devicePub, "devicePub");
async function deviceHash(env, raw) {
  if (typeof raw !== "string" || !B64U.test(raw)) return null;
  return (await sha256(salt(env) + ":d:" + raw)).slice(0, 40);
}
__name(deviceHash, "deviceHash");
async function authStart(req, env) {
  let b;
  try {
    b = await req.json();
  } catch {
    return json({ error: "bad json" }, 400);
  }
  const isWeb = b?.platform === "web";
  const port = isWeb ? 0 : parseInt(b?.port, 10);
  if (!B64U.test(b?.state || "") || !B64U.test(b?.challenge || "") || !isWeb && !(port >= 1024 && port <= 65535))
    return json({ error: "bad request" }, 400);
  if (!env.DISCORD_CLIENT_ID) return json({ error: "login not configured" }, 503);
  if (isWeb && !env.SITE_URL) return json({ error: "web login not configured" }, 503);
  if (!await rate(env, "start:" + (await sha256(salt(env) + ipOf(req))).slice(0, 24), 30)) return json({ error: "rate limited" }, 429);
  await env.DB.prepare("DELETE FROM auth_pending WHERE created < ?1").bind(now() - 900).run();
  await env.DB.prepare("INSERT INTO auth_pending (state, challenge, created, port) VALUES (?1, ?2, ?3, ?4)").bind(b.state, b.challenge, now(), port).run();
  const q = new URLSearchParams({
    client_id: env.DISCORD_CLIENT_ID,
    response_type: "code",
    scope: "identify",
    redirect_uri: redirectUri(env, req),
    state: b.state,
    prompt: "consent"
  });
  return json({ url: "https://discord.com/oauth2/authorize?" + q.toString(), expires_in: 600 });
}
__name(authStart, "authStart");
function redirectUri(env, req) {
  return (env.PUBLIC_URL || new URL(req.url).origin).replace(/\/$/, "") + "/v1/auth/callback";
}
__name(redirectUri, "redirectUri");
function page(title, msg, ok) {
  const c = ok ? "#22c55e" : "#ef4444";
  return new Response(
    `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${title}</title>
<body style="background:#0f1116;color:#e7e9ee;font-family:Segoe UI,system-ui,sans-serif;display:grid;place-items:center;height:100vh;margin:0">
<div style="text-align:center;max-width:460px;padding:24px"><div style="font-size:48px;color:${c}">${ok ? "\u2714" : "\u2716"}</div>
<h2 style="margin:8px 0">${title}</h2><p style="color:#9aa1ae">${msg}</p></div>`,
    { status: ok ? 200 : 400, headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
      "content-security-policy": "default-src 'none'; style-src 'unsafe-inline'",
      "x-frame-options": "DENY"
    } }
  );
}
__name(page, "page");
async function authCallback(req, env) {
  const u = new URL(req.url);
  const state = u.searchParams.get("state") || "", code = u.searchParams.get("code") || "";
  const p = B64U.test(state) ? await env.DB.prepare("SELECT * FROM auth_pending WHERE state = ?1").bind(state).first() : null;
  if (!p || p.created < now() - 600 || p.done) return page("Giri\u015F ba\u015Far\u0131s\u0131z / Login failed", "Ba\u011Flant\u0131n\u0131n s\xFCresi doldu. Programdan yeniden deneyin. / Link expired \u2014 try again from the app.", false);
  if (!code) {
    await env.DB.prepare("DELETE FROM auth_pending WHERE state = ?1").bind(state).run();
    return page("Giri\u015F iptal edildi / Login cancelled", "Programa d\xF6nebilirsiniz. / You can return to the app.", false);
  }
  const tr = await fetch("https://discord.com/api/oauth2/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: env.DISCORD_CLIENT_ID,
      client_secret: env.DISCORD_CLIENT_SECRET,
      grant_type: "authorization_code",
      code,
      redirect_uri: redirectUri(env, req)
    })
  });
  if (!tr.ok) return page("Giri\u015F ba\u015Far\u0131s\u0131z / Login failed", "Discord yan\u0131t vermedi. / Discord did not respond.", false);
  const tok = await tr.json();
  const ur = await fetch("https://discord.com/api/users/@me", { headers: { authorization: "Bearer " + tok.access_token } });
  if (!ur.ok) return page("Giri\u015F ba\u015Far\u0131s\u0131z / Login failed", "Discord hesab\u0131 okunamad\u0131. / Could not read the Discord account.", false);
  const du = await ur.json();
  if (!/^\d{5,25}$/.test(du.id || "")) return page("Giri\u015F ba\u015Far\u0131s\u0131z / Login failed", "Ge\xE7ersiz hesap. / Invalid account.", false);
  const name = String(du.global_name || du.username || "agent").slice(0, 40);
  const acc = await env.DB.prepare(
    "INSERT INTO accounts (discord_id, username, avatar, created, last_login) VALUES (?1, ?2, ?3, ?4, ?4) ON CONFLICT(discord_id) DO UPDATE SET username = ?2, avatar = ?3, last_login = ?4 RETURNING id, banned"
  ).bind(du.id, name, du.avatar || null, now()).first();
  if (acc.banned) {
    await env.DB.prepare("DELETE FROM auth_pending WHERE state = ?1").bind(state).run();
    return page("Hesap engelli / Account blocked", "Bu hesap kullan\u0131lam\u0131yor. / This account is blocked.", false);
  }
  const grant = randomToken(24);
  await env.DB.prepare("UPDATE auth_pending SET done = 1, account_id = ?1, grant_hash = ?2 WHERE state = ?3").bind(acc.id, await sha256(grant), state).run();
  const dest = p.port === 0 ? `${String(env.SITE_URL).replace(/\/$/, "")}/account/#state=${state}&grant=${grant}` : `http://127.0.0.1:${p.port}/callback?state=${state}&grant=${grant}`;
  return new Response(null, { status: 302, headers: {
    "cache-control": "no-store",
    "referrer-policy": "no-referrer",
    location: dest
  } });
}
__name(authCallback, "authCallback");
async function authToken(req, env) {
  let b;
  try {
    b = await req.json();
  } catch {
    return json({ error: "bad json" }, 400);
  }
  if (!B64U.test(b?.state || "") || !B64U.test(b?.verifier || "") || !B64U.test(b?.grant || "")) return json({ error: "bad request" }, 400);
  if (!await rate(env, "tok:" + (await sha256(salt(env) + ipOf(req))).slice(0, 24), 60)) return json({ error: "rate limited" }, 429);
  const p = await env.DB.prepare("SELECT * FROM auth_pending WHERE state = ?1").bind(b.state).first();
  if (!p || p.created < now() - 600 || !p.done || !p.account_id) return json({ error: "expired" }, 410);
  const vOk = safeEqual(await shaB64u(b.verifier), p.challenge), gOk = safeEqual(await sha256(b.grant), p.grant_hash || "");
  await env.DB.prepare("DELETE FROM auth_pending WHERE state = ?1").bind(b.state).run();
  if (!vOk || !gOk) return json({ error: "proof mismatch" }, 403);
  const dh = await deviceHash(env, b.device);
  if (!dh) return json({ error: "device required" }, 400);
  const token = randomToken(32);
  const dp = await devicePub(b.device);
  await env.DB.prepare("INSERT INTO sessions (token_hash, account_id, device_hash, device_pub, created, expires, last_seen) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?5)").bind(await sha256(token), p.account_id, dh, dp, now(), now() + 30 * DAY).run();
  await audit(env, "acc:" + p.account_id, "login", {});
  return json({ status: "ok", token, ...await meData(env, p.account_id, dh, dp) });
}
__name(authToken, "authToken");
async function logout(req, env) {
  const s = await session(req, env);
  if (s) await env.DB.prepare("UPDATE sessions SET revoked = 1 WHERE token_hash = ?1").bind(s.token_hash).run();
  return json({ ok: true });
}
__name(logout, "logout");
async function deleteMe(req, env) {
  const s = await session(req, env);
  if (!s) return json({ error: "unauthorized" }, 401);
  await env.DB.prepare("INSERT INTO account_deletions (account_id, requested) VALUES (?1, ?2) ON CONFLICT(account_id) DO NOTHING").bind(s.account_id, now()).run();
  await env.DB.prepare("UPDATE sessions SET revoked = 1 WHERE account_id = ?1").bind(s.account_id).run();
  await env.DB.prepare("UPDATE mobile_devices SET revoked = 1 WHERE account_id = ?1").bind(s.account_id).run();
  await audit(env, "acc:" + s.account_id, "delete_requested", {});
  return json({ ok: true, deletion_requested: true });
}
__name(deleteMe, "deleteMe");
async function activeLicense(env, accountId) {
  const rows = (await env.DB.prepare(
    "SELECT * FROM licenses WHERE account_id = ?1 AND revoked = 0 AND (expires IS NULL OR expires > ?2) ORDER BY expires IS NULL DESC, expires DESC"
  ).bind(accountId, now()).all()).results || [];
  return rows[0] || null;
}
__name(activeLicense, "activeLicense");
async function bindDevice(env, lic, dh) {
  const has = await env.DB.prepare("SELECT 1 FROM devices WHERE license_id = ?1 AND device_hash = ?2").bind(lic.id, dh).first();
  if (has) {
    await env.DB.prepare("UPDATE devices SET last_seen = ?1 WHERE license_id = ?2 AND device_hash = ?3").bind(now(), lic.id, dh).run();
    return true;
  }
  const n = (await env.DB.prepare("SELECT COUNT(*) AS n FROM devices WHERE license_id = ?1").bind(lic.id).first()).n;
  if (n >= (lic.max_devices || 1)) return false;
  await env.DB.prepare("INSERT INTO devices (license_id, device_hash, first_seen, last_seen) VALUES (?1, ?2, ?3, ?3)").bind(lic.id, dh, now()).run();
  return true;
}
__name(bindDevice, "bindDevice");
async function meData(env, accountId, dh, dp) {
  const a = await env.DB.prepare("SELECT id, username, avatar, discord_id, created FROM accounts WHERE id = ?1").bind(accountId).first();
  const lic = await activeLicense(env, accountId);
  const out = {
    account: { username: a.username, avatar: a.avatar, discord_id: a.discord_id, since: a.created },
    tier: "free",
    license: null,
    entitlement: null
  };
  if (!lic) return out;
  out.license = { hint: lic.key_hint, tier: lic.tier, expires: lic.expires, source: lic.source, max_devices: lic.max_devices };
  if (!await bindDevice(env, lic, dh)) {
    out.device_limit = true;
    return out;
  }
  const exp = Math.min(lic.expires || Infinity, now() + ENT_DAYS * DAY);
  out.tier = lic.tier;
  out.entitlement = await signEntitlement(env, {
    v: 1,
    acc: String(a.id),
    name: a.username,
    tier: lic.tier,
    dev: dp,
    lic_exp: lic.expires || null,
    exp,
    iat: now()
  });
  return out;
}
__name(meData, "meData");
async function me(req, env) {
  const s = await session(req, env);
  if (!s) return json({ error: "unauthorized" }, 401);
  return json(await meData(env, s.account_id, s.device_hash, s.device_pub));
}
__name(me, "me");
async function redeem(req, env) {
  const s = await session(req, env);
  if (!s) return json({ error: "unauthorized" }, 401);
  let b;
  try {
    b = await req.json();
  } catch {
    return json({ error: "bad json" }, 400);
  }
  const ipb = (await sha256(salt(env) + ipOf(req))).slice(0, 24);
  if (!await rate(env, "redeem:acc:" + s.account_id, 10) || !await rate(env, "redeem:ip:" + ipb, 20))
    return json({ error: "too many attempts", retry_after: 3600 }, 429);
  const code = normCode(b?.code);
  let lic = null, how = null;
  if (/^TD2K[0-9A-Z]{16}$/.test(code)) {
    const kh = await sha256("k:" + code);
    lic = await env.DB.prepare("SELECT * FROM licenses WHERE key_hash = ?1").bind(kh).first();
    if (!lic || lic.revoked) return json({ error: "invalid key" }, 404);
    if (lic.account_id && lic.account_id !== s.account_id) return json({ error: "key already used" }, 409);
    if (!lic.account_id) {
      const exp = lic.duration_days ? now() + lic.duration_days * DAY : lic.expires;
      const r = await env.DB.prepare("UPDATE licenses SET account_id = ?1, redeemed = ?2, expires = ?3 WHERE id = ?4 AND account_id IS NULL").bind(s.account_id, now(), exp, lic.id).run();
      if (!r.meta?.changes) return json({ error: "key already used" }, 409);
    }
    how = "key";
  } else if (/^TD2I[0-9A-Z]{12}$/.test(code)) {
    const ch = await sha256("i:" + code);
    const inv = await env.DB.prepare("SELECT * FROM invites WHERE code_hash = ?1").bind(ch).first();
    if (!inv || inv.revoked || inv.expires && inv.expires < now()) return json({ error: "invalid code" }, 404);
    const used = await env.DB.prepare("SELECT 1 FROM licenses WHERE source = 'invite' AND source_ref = ?1 AND account_id = ?2").bind(String(inv.id), s.account_id).first();
    if (used) return json({ error: "code already used by this account" }, 409);
    const r = await env.DB.prepare("UPDATE invites SET uses_left = uses_left - 1 WHERE id = ?1 AND uses_left > 0").bind(inv.id).run();
    if (!r.meta?.changes) return json({ error: "code used up" }, 410);
    await env.DB.prepare("INSERT INTO licenses (key_hash, key_hint, tier, created, expires, account_id, redeemed, max_devices, source, source_ref, note) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?4, 1, 'invite', ?7, ?8)").bind(
      await sha256("inv:" + inv.id + ":" + s.account_id),
      "INV" + inv.id,
      inv.tier,
      now(),
      inv.duration_days ? now() + inv.duration_days * DAY : null,
      s.account_id,
      String(inv.id),
      inv.note || null
    ).run();
    how = "invite";
  } else if (env.GUMROAD_PRODUCT_ID && /^[0-9A-Z]{32}$/.test(code)) {
    const gr = await fetch("https://api.gumroad.com/v2/licenses/verify", {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ product_id: env.GUMROAD_PRODUCT_ID, license_key: String(b.code).trim(), increment_uses_count: "false" })
    });
    const g = await gr.json().catch(() => ({}));
    const pu = g.purchase || {};
    if (!g.success || pu.refunded || pu.chargebacked || pu.disputed || pu.subscription_cancelled_at || pu.subscription_failed_at)
      return json({ error: "purchase not valid" }, 402);
    const ref = String(pu.sale_id || pu.id || code);
    const exist = await env.DB.prepare("SELECT account_id FROM licenses WHERE source = 'gumroad' AND source_ref = ?1").bind(ref).first();
    if (exist && exist.account_id !== s.account_id) return json({ error: "key already used" }, 409);
    if (!exist)
      await env.DB.prepare("INSERT INTO licenses (key_hash, key_hint, tier, created, expires, account_id, redeemed, max_devices, source, source_ref, note) VALUES (?1, ?2, 'premium', ?3, NULL, ?4, ?3, 1, 'gumroad', ?5, ?6)").bind(await sha256("g:" + code), code.slice(-4), now(), s.account_id, ref, String(pu.email || "").replace(/(^.).*(@.*$)/, "$1***$2")).run();
    how = "gumroad";
  } else {
    return json({ error: "unrecognised code" }, 400);
  }
  await audit(env, "acc:" + s.account_id, "redeem", { how });
  const out = await meData(env, s.account_id, s.device_hash, s.device_pub);
  return json({ ok: true, how, ...out });
}
__name(redeem, "redeem");
async function isAdmin(req, env) {
  const m = /^Admin\s+(\S{24,200})$/.exec(req.headers.get("authorization") || "");
  if (!m || !env.ADMIN_TOKEN) return false;
  return safeEqual(await sha256(m[1]), await sha256(env.ADMIN_TOKEN));
}
__name(isAdmin, "isAdmin");
async function admin(req, env, path) {
  const ipb = (await sha256(salt(env) + ipOf(req))).slice(0, 24);
  if (!await isAdmin(req, env)) {
    await rate(env, "adminfail:" + ipb, 1e3);
    return json({ error: "forbidden" }, 403);
  }
  const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};
  const u = new URL(req.url);
  const q = (u.searchParams.get("q") || "").slice(0, 60);
  let m;
  if (path === "accounts" && req.method === "GET") {
    const rows = (await env.DB.prepare(
      "SELECT a.id, a.discord_id, a.username, a.created, a.last_login, a.banned, (SELECT COUNT(*) FROM licenses l WHERE l.account_id = a.id AND l.revoked = 0 AND (l.expires IS NULL OR l.expires > ?2)) AS active FROM accounts a WHERE a.username LIKE ?1 OR a.discord_id = ?3 ORDER BY a.last_login DESC LIMIT 500"
    ).bind("%" + q + "%", now(), q).all()).results;
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
      "SELECT l.id, l.key_hint, l.tier, l.created, l.expires, l.duration_days, l.redeemed, l.max_devices, l.source, l.note, l.revoked, a.username, a.id AS account_id, (SELECT COUNT(*) FROM devices d WHERE d.license_id = l.id) AS devices FROM licenses l LEFT JOIN accounts a ON a.id = l.account_id WHERE ?1 = '' OR a.username LIKE ?2 OR l.key_hint = ?1 OR l.note LIKE ?2 ORDER BY l.created DESC LIMIT 1000"
    ).bind(q, "%" + q + "%").all()).results;
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
      await env.DB.prepare("INSERT INTO licenses (key_hash, key_hint, tier, created, duration_days, max_devices, source, note) VALUES (?1, ?2, ?3, ?4, ?5, ?6, 'admin', ?7)").bind(await sha256("k:" + nk), nk.slice(-4), tier, now(), days, Math.max(1, Math.min(5, parseInt(body.max_devices || 1, 10))), note).run();
      keys.push(key);
    }
    await audit(env, "admin", "create_keys", { n, tier, days, note });
    return json({ keys });
  }
  if ((m = /^licenses\/(\d+)\/(revoke|unrevoke|reset_devices|extend)$/.exec(path)) && req.method === "POST") {
    const id = +m[1];
    if (m[2] === "revoke" || m[2] === "unrevoke") await env.DB.prepare("UPDATE licenses SET revoked = ?1 WHERE id = ?2").bind(m[2] === "revoke" ? 1 : 0, id).run();
    if (m[2] === "reset_devices") await env.DB.prepare("DELETE FROM devices WHERE license_id = ?1").bind(id).run();
    if (m[2] === "extend") {
      const d = Math.max(1, Math.min(3650, parseInt(body.days || 30, 10)));
      await env.DB.prepare("UPDATE licenses SET expires = CASE WHEN expires IS NULL THEN NULL ELSE MAX(expires, ?1) + ?2 END, duration_days = CASE WHEN account_id IS NULL AND duration_days IS NOT NULL THEN duration_days + ?3 ELSE duration_days END WHERE id = ?4").bind(now(), d * DAY, d, id).run();
    }
    await audit(env, "admin", m[2], { license: id, days: body.days });
    return json({ ok: true });
  }
  if (path === "invites" && req.method === "GET") {
    return json({ invites: (await env.DB.prepare("SELECT id, code_hint, tier, duration_days, uses_left, expires, created, note, revoked FROM invites ORDER BY created DESC LIMIT 500").all()).results });
  }
  if (path === "invites" && req.method === "POST") {
    const code = humanCode("TD2I", 3), nc = normCode(code);
    const uses = Math.max(1, Math.min(1e4, parseInt(body.uses || 1, 10)));
    const days = body.days ? Math.max(1, Math.min(3650, parseInt(body.days, 10))) : null;
    const exp = body.valid_days ? now() + Math.max(1, Math.min(365, parseInt(body.valid_days, 10))) * DAY : null;
    await env.DB.prepare("INSERT INTO invites (code_hash, code_hint, tier, duration_days, uses_left, expires, created, note) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)").bind(await sha256("i:" + nc), nc.slice(-4), TIERS.has(body.tier) ? body.tier : "premium", days, uses, exp, now(), String(body.note || "").slice(0, 120)).run();
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
    const one = /* @__PURE__ */ __name(async (sqlq) => (await env.DB.prepare(sqlq).bind(now()).first()).n, "one");
    return json({
      accounts: await one("SELECT COUNT(*) AS n FROM accounts WHERE ?1 > 0"),
      active_licenses: await one("SELECT COUNT(*) AS n FROM licenses WHERE revoked = 0 AND account_id IS NOT NULL AND (expires IS NULL OR expires > ?1)"),
      unused_keys: await one("SELECT COUNT(*) AS n FROM licenses WHERE account_id IS NULL AND revoked = 0 AND ?1 > 0"),
      logins_24h: await one("SELECT COUNT(*) AS n FROM accounts WHERE last_login > ?1 - 86400")
    });
  }
  return json({ error: "not found" }, 404);
}
__name(admin, "admin");
async function route(req, env, path) {
  if (path === "/v1/auth/start" && req.method === "POST") return authStart(req, env);
  if (path === "/v1/auth/callback" && req.method === "GET") return authCallback(req, env);
  if (path === "/v1/auth/token" && req.method === "POST") return authToken(req, env);
  if (path === "/v1/auth/logout" && req.method === "POST") return logout(req, env);
  if (path === "/v1/me" && req.method === "GET") return me(req, env);
  if (path === "/v1/me" && req.method === "DELETE") return deleteMe(req, env);
  if (path === "/v1/license/redeem" && req.method === "POST") return redeem(req, env);
  if (path.startsWith("/v1/admin/")) return admin(req, env, path.slice(10));
  return null;
}
__name(route, "route");

// tasks.js
var CATS = /* @__PURE__ */ new Set(["project", "bounty", "assignment", "other"]);
var PERIODS = /* @__PURE__ */ new Set(["daily", "weekly", "season", "other"]);
var EN_FIELDS = { title: 80, subtitle: 80, desc: 420, objective: 220 };
var enc2 = new TextEncoder();
var READY = false;
function json2(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      ...extra
    }
  });
}
__name(json2, "json");
async function sha(text) {
  const d = await crypto.subtle.digest("SHA-256", enc2.encode(text));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
__name(sha, "sha");
function norm(s) {
  return String(s || "").toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9' ]+/g, " ").replace(/\s+/g, " ").trim();
}
__name(norm, "norm");
async function taskKey(title, objective) {
  return (await sha("task|" + norm(title) + "|" + norm(objective))).slice(0, 16);
}
__name(taskKey, "taskKey");
async function ensure(env) {
  if (READY) return;
  const ddl = [
    `CREATE TABLE IF NOT EXISTS task_reports (key TEXT NOT NULL, client TEXT NOT NULL, created INTEGER NOT NULL,
       updated INTEGER NOT NULL, category TEXT NOT NULL, period TEXT NOT NULL, expires_at INTEGER, en_hash TEXT NOT NULL,
       en TEXT NOT NULL, tr_hash TEXT, tr TEXT, app TEXT, PRIMARY KEY (key, client))`,
    `CREATE INDEX IF NOT EXISTS idx_task_reports_updated ON task_reports (updated)`,
    `CREATE TABLE IF NOT EXISTS task_admin (key TEXT PRIMARY KEY, hidden INTEGER NOT NULL DEFAULT 0, tr TEXT, updated INTEGER)`,
    `CREATE TABLE IF NOT EXISTS task_state (k TEXT PRIMARY KEY, v TEXT)`,
    `CREATE TABLE IF NOT EXISTS tr_suggest (id INTEGER PRIMARY KEY AUTOINCREMENT, en_key TEXT NOT NULL, en TEXT NOT NULL,
       old TEXT, new TEXT NOT NULL, new_hash TEXT NOT NULL, client TEXT NOT NULL, created INTEGER NOT NULL, app TEXT,
       status TEXT NOT NULL DEFAULT 'pending', UNIQUE (en_key, client))`,
    `CREATE INDEX IF NOT EXISTS idx_tr_suggest_status ON tr_suggest (status)`,
    `CREATE TABLE IF NOT EXISTS tr_lines (en_key TEXT PRIMARY KEY, en TEXT NOT NULL, tr TEXT NOT NULL, updated INTEGER NOT NULL)`
  ];
  for (const q of ddl) await env.DB.prepare(q).run();
  READY = true;
}
__name(ensure, "ensure");
function cleanText(v, max, english) {
  if (typeof v !== "string") return "";
  let s = v.replace(/[\u0000-\u0009\u000b-\u001f\u007f]/g, "").replace(/[ \t]+/g, " ").trim();
  if (!s) return "";
  if (s.length > max) return null;
  if (/https?:|www\.|@|<|>|\{|\}/i.test(s)) return null;
  if (english) {
    const letters = s.match(/\p{L}/gu) || [];
    if (letters.length < 3 || letters.filter((c) => /[A-Za-z]/.test(c)).length / letters.length < 0.9) return null;
  }
  return s;
}
__name(cleanText, "cleanText");
function cleanTask(b) {
  if (!b || typeof b !== "object") return null;
  const t = b.task || {};
  const en = {};
  for (const [k, max] of Object.entries(EN_FIELDS)) {
    const v = cleanText(t[k], max, true);
    if (v === null) return null;
    if (v) en[k] = v;
  }
  if (!en.title || !en.objective) return null;
  const total = Number.isInteger(t.total) && t.total > 0 && t.total <= 999 ? t.total : null;
  if (total) en.total = total;
  const rewards = Array.isArray(t.rewards) ? t.rewards.slice(0, 8).map((r) => cleanText(r, 60, true)) : [];
  if (rewards.some((r) => r === null)) return null;
  if (rewards.length) en.rewards = rewards.filter(Boolean);
  const category = CATS.has(t.category) ? t.category : "other";
  const period = PERIODS.has(t.period) ? t.period : "other";
  const now4 = Math.floor(Date.now() / 1e3);
  let expires_at = Number.isInteger(t.expires_at) ? t.expires_at : null;
  if (expires_at && (expires_at < now4 || expires_at > now4 + 100 * 86400)) expires_at = null;
  if (expires_at) expires_at = Math.round(expires_at / 3600) * 3600;
  let tr = null;
  if (b.tr && typeof b.tr === "object") {
    tr = {};
    for (const [k, max] of Object.entries(EN_FIELDS)) {
      if (!en[k]) continue;
      const v = cleanText(b.tr[k], max * 2, false);
      if (v === null) {
        tr = null;
        break;
      }
      if (v) tr[k] = v;
    }
    if (tr && !tr.title && !tr.objective) tr = null;
  }
  const app = typeof b.app === "string" && /^\d+\.\d+\.\d+$/.test(b.app) ? b.app : null;
  return { en, tr, category, period, expires_at, app };
}
__name(cleanTask, "cleanTask");
async function rateCheck(env, bucket, max, hours) {
  const hour = Math.floor(Date.now() / 36e5);
  const r = await env.DB.prepare("SELECT COALESCE(SUM(n),0) AS n FROM rate WHERE bucket = ?1 AND hour > ?2").bind(bucket, hour - hours).first();
  return (r ? r.n : 0) < max;
}
__name(rateCheck, "rateCheck");
async function rateAdd(env, bucket) {
  const hour = Math.floor(Date.now() / 36e5);
  await env.DB.prepare("INSERT INTO rate (bucket, hour, n) VALUES (?1, ?2, 1) ON CONFLICT(bucket, hour) DO UPDATE SET n = n + 1").bind(bucket, hour).run();
}
__name(rateAdd, "rateAdd");
async function postTask(req, env) {
  let b;
  try {
    b = await req.json();
  } catch {
    return json2({ error: "bad json" }, 400);
  }
  const c = cleanTask(b);
  if (!c) return json2({ error: "invalid task" }, 400);
  const salt3 = env.HASH_SALT || "dev-salt";
  const rawClient = String(b.client || "").slice(0, 64);
  if (rawClient.length < 8) return json2({ error: "invalid client" }, 400);
  const client = await sha(salt3 + "|task|" + rawClient);
  const ip = await sha(salt3 + "|ip|" + (req.headers.get("cf-connecting-ip") || ""));
  const maxC = parseInt(env.TASKS_PER_HOUR || "60", 10);
  if (!await rateCheck(env, "tc:" + client, maxC, 1) || !await rateCheck(env, "ti:" + ip, maxC * 3, 1))
    return json2({ error: "rate limited" }, 429);
  await rateAdd(env, "tc:" + client);
  await rateAdd(env, "ti:" + ip);
  const key = await taskKey(c.en.title, c.en.objective);
  const enS = JSON.stringify(c.en), trS = c.tr ? JSON.stringify(c.tr) : null;
  const enH = (await sha(enS)).slice(0, 16), trH = trS ? (await sha(trS)).slice(0, 16) : null;
  const now4 = Math.floor(Date.now() / 1e3);
  await env.DB.prepare(
    `INSERT INTO task_reports (key, client, created, updated, category, period, expires_at, en_hash, en, tr_hash, tr, app)
     VALUES (?1, ?2, ?3, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)
     ON CONFLICT(key, client) DO UPDATE SET updated = ?3, category = ?4, period = ?5, expires_at = ?6, en_hash = ?7, en = ?8,
       tr_hash = COALESCE(?9, tr_hash), tr = COALESCE(?10, tr), app = ?11`
  ).bind(key, client, now4, c.category, c.period, c.expires_at, enH, enS, trH, trS, c.app).run();
  const n = await env.DB.prepare("SELECT COUNT(*) AS n FROM task_reports WHERE key = ?1").bind(key).first();
  return json2({ ok: true, key, reporters: n ? n.n : 1 });
}
__name(postTask, "postTask");
async function postSuggest(req, env) {
  let b;
  try {
    b = await req.json();
  } catch {
    return json2({ error: "bad json" }, 400);
  }
  const en = cleanText(b.en, 420, true), nw = cleanText(b.new, 840, false), old = cleanText(b.old, 840, false);
  if (!en || !nw || en === null || nw === null || old === null || nw === old) return json2({ error: "invalid suggestion" }, 400);
  const rawClient = String(b.client || "").slice(0, 64);
  if (rawClient.length < 8) return json2({ error: "invalid client" }, 400);
  const salt3 = env.HASH_SALT || "dev-salt";
  const client = await sha(salt3 + "|task|" + rawClient);
  const ip = await sha(salt3 + "|ip|" + (req.headers.get("cf-connecting-ip") || ""));
  if (!await rateCheck(env, "sc:" + client, 30, 24) || !await rateCheck(env, "si:" + ip, 90, 24)) return json2({ error: "rate limited" }, 429);
  await rateAdd(env, "sc:" + client);
  await rateAdd(env, "si:" + ip);
  const en_key = (await sha("line|" + norm(en))).slice(0, 16);
  const app = typeof b.app === "string" && /^\d+\.\d+\.\d+$/.test(b.app) ? b.app : null;
  await env.DB.prepare(
    `INSERT INTO tr_suggest (en_key, en, old, new, new_hash, client, created, app) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
     ON CONFLICT(en_key, client) DO UPDATE SET new = ?4, new_hash = ?5, old = ?3, created = ?7, app = ?8, status = 'pending'`
  ).bind(en_key, en, old || null, nw, (await sha(norm(nw))).slice(0, 16), client, Math.floor(Date.now() / 1e3), app).run();
  return json2({ ok: true });
}
__name(postSuggest, "postSuggest");
async function approvedLines(env) {
  return (await env.DB.prepare("SELECT en, tr FROM tr_lines ORDER BY updated DESC LIMIT 2000").all()).results || [];
}
__name(approvedLines, "approvedLines");
async function topVariant(env, key, col, hashCol) {
  const r = await env.DB.prepare(
    `SELECT ${col} AS v, COUNT(*) AS c FROM task_reports WHERE key = ?1 AND ${hashCol} IS NOT NULL
     GROUP BY ${hashCol} ORDER BY c DESC, MAX(updated) DESC LIMIT 1`
  ).bind(key).first();
  return r ? { v: JSON.parse(r.v), c: r.c } : null;
}
__name(topVariant, "topVariant");
async function mostCommon(env, key, col) {
  const r = await env.DB.prepare(
    `SELECT ${col} AS v, COUNT(*) AS c FROM task_reports WHERE key = ?1 GROUP BY ${col} ORDER BY c DESC LIMIT 1`
  ).bind(key).first();
  return r ? r.v : null;
}
__name(mostCommon, "mostCommon");
async function liveTasks(env, { includeHidden = false, minReporters = null, admin: admin2 = false } = {}) {
  await ensure(env);
  const now4 = Math.floor(Date.now() / 1e3);
  const minR = minReporters ?? parseInt(env.TASKS_MIN_REPORTERS || "2", 10);
  const days = parseInt(env.TASKS_KEEP_DAYS || "8", 10);
  const rows = (await env.DB.prepare(
    `SELECT r.key, COUNT(*) AS n, MIN(r.created) AS first_seen, MAX(r.updated) AS last_seen,
            a.hidden AS hidden, a.tr AS tr_override
     FROM task_reports r LEFT JOIN task_admin a ON a.key = r.key
     WHERE r.updated > ?1 GROUP BY r.key HAVING COUNT(*) >= ?2 ORDER BY last_seen DESC LIMIT 300`
  ).bind(now4 - (admin2 ? 60 : days) * 86400, minR).all()).results || [];
  const out = [];
  for (const r of rows) {
    if (r.hidden && !includeHidden) continue;
    const exp = await mostCommon(env, r.key, "expires_at");
    if (!admin2 && exp && exp < now4) continue;
    const en = await topVariant(env, r.key, "en", "en_hash");
    if (!en) continue;
    const trv = await topVariant(env, r.key, "tr", "tr_hash");
    let tr = null, trSrc = null;
    if (r.tr_override) {
      tr = JSON.parse(r.tr_override);
      trSrc = "admin";
    } else if (trv && trv.c >= Math.min(2, minR)) {
      tr = trv.v;
      trSrc = "community";
    }
    const t = {
      key: r.key,
      category: await mostCommon(env, r.key, "category"),
      period: await mostCommon(env, r.key, "period"),
      ...en.v,
      expires_at: exp || null,
      first_seen: r.first_seen,
      last_seen: r.last_seen,
      reporters: r.n
    };
    if (tr) {
      t.tr = tr;
      t.tr_source = trSrc;
    }
    if (admin2) {
      t.hidden = !!r.hidden;
      t.variants = {
        en: ((await env.DB.prepare("SELECT en AS v, COUNT(*) AS c FROM task_reports WHERE key = ?1 GROUP BY en_hash ORDER BY c DESC LIMIT 5").bind(r.key).all()).results || []).map((x) => ({ n: x.c, ...JSON.parse(x.v) })),
        tr: ((await env.DB.prepare("SELECT tr AS v, COUNT(*) AS c FROM task_reports WHERE key = ?1 AND tr IS NOT NULL GROUP BY tr_hash ORDER BY c DESC LIMIT 5").bind(r.key).all()).results || []).map((x) => ({ n: x.c, ...JSON.parse(x.v) }))
      };
      t.apps = ((await env.DB.prepare("SELECT app, COUNT(*) AS c FROM task_reports WHERE key = ?1 GROUP BY app").bind(r.key).all()).results || []).map((x) => `${x.app || "?"}\xD7${x.c}`);
    }
    out.push(t);
  }
  const lines = await approvedLines(env);
  return {
    version: new Date(now4 * 1e3).toISOString().slice(0, 16).replace(/[-:T]/g, "") + "." + lines.length,
    generated: now4,
    min_reporters: parseInt(env.TASKS_MIN_REPORTERS || "2", 10),
    tasks: out,
    lines
  };
}
__name(liveTasks, "liveTasks");
async function snapshotToRepo(env, gh2) {
  if (!env.GITHUB_TOKEN || !env.REPORTS_REPO) return "no-token";
  await ensure(env);
  const day = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
  const last = await env.DB.prepare("SELECT v FROM task_state WHERE k = 'snapshot_day'").first();
  if (last && last.v === day) return "done-today";
  const data = await liveTasks(env, { includeHidden: true, minReporters: 1, admin: true });
  const body = JSON.stringify(data, null, 1);
  const path = `tasks/${day}.json`;
  try {
    await gh2(env, `/repos/${env.REPORTS_REPO}/contents/${path}`, { method: "PUT", body: JSON.stringify({
      message: `G\xF6rev d\xF6k\xFCm\xFC ${day} (${data.tasks.length} g\xF6rev)`,
      content: btoa(String.fromCharCode(...enc2.encode(body)))
    }) });
  } catch (e) {
    return "github-failed";
  }
  await env.DB.prepare("INSERT INTO task_state (k, v) VALUES ('snapshot_day', ?1) ON CONFLICT(k) DO UPDATE SET v = ?1").bind(day).run();
  return "ok";
}
__name(snapshotToRepo, "snapshotToRepo");
async function cleanup(env) {
  await ensure(env);
  const now4 = Math.floor(Date.now() / 1e3);
  await env.DB.prepare("DELETE FROM task_reports WHERE updated < ?1").bind(now4 - 90 * 86400).run();
}
__name(cleanup, "cleanup");
async function route2(req, env, path, isAdmin2, ctx) {
  if (path === "/v1/tasks" && req.method === "POST") {
    await ensure(env);
    return await postTask(req, env);
  }
  if (path === "/v1/suggest" && req.method === "POST") {
    await ensure(env);
    return await postSuggest(req, env);
  }
  if (path.startsWith("/v1/admin/suggestions")) {
    if (!await isAdmin2(req, env)) return json2({ error: "forbidden" }, 403);
    await ensure(env);
    if (path === "/v1/admin/suggestions" && req.method === "GET") {
      const st = new URL(req.url).searchParams.get("status") || "pending";
      const rows = (await env.DB.prepare(
        `SELECT MIN(s.id) AS id, s.en_key, s.en, s.old, s.new, COUNT(*) AS n, MAX(s.created) AS last, s.status, l.tr AS current
         FROM tr_suggest s LEFT JOIN tr_lines l ON l.en_key = s.en_key WHERE s.status = ?1
         GROUP BY s.en_key, s.new_hash ORDER BY n DESC, last DESC LIMIT 300`
      ).bind(st).all()).results || [];
      return json2({ suggestions: rows });
    }
    if (path === "/v1/admin/suggestions/decide" && req.method === "POST") {
      const b = await req.json().catch(() => ({}));
      const row = Number.isInteger(b.id) ? await env.DB.prepare("SELECT * FROM tr_suggest WHERE id = ?1").bind(b.id).first() : null;
      if (!row) return json2({ error: "not found" }, 404);
      const now4 = Math.floor(Date.now() / 1e3);
      if (b.approve) {
        const text = b.text === void 0 ? row.new : cleanText(b.text, 840, false);
        if (!text) return json2({ error: "bad text" }, 400);
        await env.DB.prepare("INSERT INTO tr_lines (en_key, en, tr, updated) VALUES (?1, ?2, ?3, ?4) ON CONFLICT(en_key) DO UPDATE SET tr = ?3, updated = ?4").bind(row.en_key, row.en, text, now4).run();
        await env.DB.prepare("UPDATE tr_suggest SET status = CASE WHEN new_hash = ?2 THEN 'approved' ELSE 'rejected' END WHERE en_key = ?1 AND status = 'pending'").bind(row.en_key, row.new_hash).run();
      } else {
        await env.DB.prepare("UPDATE tr_suggest SET status = 'rejected' WHERE en_key = ?1 AND new_hash = ?2").bind(row.en_key, row.new_hash).run();
      }
      return json2({ ok: true });
    }
    if (path === "/v1/admin/suggestions/line" && req.method === "POST") {
      const b = await req.json().catch(() => ({}));
      if (typeof b.en_key !== "string") return json2({ error: "bad key" }, 400);
      await env.DB.prepare("DELETE FROM tr_lines WHERE en_key = ?1").bind(b.en_key).run();
      return json2({ ok: true });
    }
    return json2({ error: "not found" }, 404);
  }
  if (path === "/v1/tasks/live" && req.method === "GET") {
    const cache = typeof caches !== "undefined" ? caches.default : null;
    const ck = new Request(new URL(req.url).origin + "/v1/tasks/live");
    if (cache) {
      const hit = await cache.match(ck);
      if (hit) return hit;
    }
    const res = json2(await liveTasks(env), 200, { "cache-control": "public, max-age=300" });
    if (cache && ctx) ctx.waitUntil(cache.put(ck, res.clone()));
    return res;
  }
  if (path.startsWith("/v1/admin/tasks")) {
    if (!await isAdmin2(req, env)) return json2({ error: "forbidden" }, 403);
    await ensure(env);
    if (path === "/v1/admin/tasks" && req.method === "GET") {
      return json2(await liveTasks(env, { includeHidden: true, minReporters: 1, admin: true }));
    }
    const b = req.method === "POST" ? await req.json().catch(() => ({})) : {};
    const key = typeof b.key === "string" && /^[0-9a-f]{16}$/.test(b.key) ? b.key : null;
    if (!key) return json2({ error: "bad key" }, 400);
    const now4 = Math.floor(Date.now() / 1e3);
    if (path === "/v1/admin/tasks/hide" && req.method === "POST") {
      await env.DB.prepare("INSERT INTO task_admin (key, hidden, updated) VALUES (?1, ?2, ?3) ON CONFLICT(key) DO UPDATE SET hidden = ?2, updated = ?3").bind(key, b.hidden === false ? 0 : 1, now4).run();
      return json2({ ok: true });
    }
    if (path === "/v1/admin/tasks/override" && req.method === "POST") {
      let tr = null;
      if (b.tr && typeof b.tr === "object") {
        tr = {};
        for (const [k, max] of Object.entries(EN_FIELDS)) {
          const v = cleanText(b.tr[k], max * 2, false);
          if (v === null) return json2({ error: "bad tr" }, 400);
          if (v) tr[k] = v;
        }
      }
      await env.DB.prepare("INSERT INTO task_admin (key, tr, updated) VALUES (?1, ?2, ?3) ON CONFLICT(key) DO UPDATE SET tr = ?2, updated = ?3").bind(key, tr ? JSON.stringify(tr) : null, now4).run();
      return json2({ ok: true });
    }
    return json2({ error: "not found" }, 404);
  }
  return null;
}
__name(route2, "route");

// overview.js
var VERSION_RE = /^TD2LootAdvisor\/(\d{1,2}\.\d{1,2}\.\d{1,3})(?:\s|$)/;
var READY2 = false;
function json3(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
  });
}
__name(json3, "json");
var now2 = /* @__PURE__ */ __name(() => Math.floor(Date.now() / 1e3), "now");
var dayOf = /* @__PURE__ */ __name((t) => new Date(t * 1e3).toISOString().slice(0, 10), "dayOf");
async function ensure2(env) {
  if (READY2) return;
  await env.DB.prepare(`CREATE TABLE IF NOT EXISTS usage_daily (day TEXT NOT NULL, version TEXT NOT NULL,
    starts INTEGER NOT NULL DEFAULT 0, polls INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, version))`).run();
  await env.DB.prepare(`CREATE TABLE IF NOT EXISTS task_state (k TEXT PRIMARY KEY, v TEXT)`).run();
  READY2 = true;
}
__name(ensure2, "ensure");
function parseVersion(ua) {
  const m = VERSION_RE.exec(String(ua || ""));
  return m ? m[1] : null;
}
__name(parseVersion, "parseVersion");
async function countUsage(req, env) {
  const v = parseVersion(req.headers.get("user-agent"));
  if (!v) return;
  const start = (req.headers.get("x-td2-run") || "") === "start" ? 1 : 0;
  try {
    await ensure2(env);
    await env.DB.prepare(`INSERT INTO usage_daily (day, version, starts, polls) VALUES (?1, ?2, ?3, 1)
      ON CONFLICT(day, version) DO UPDATE SET starts = starts + ?3, polls = polls + 1`).bind(dayOf(now2()), v, start).run();
  } catch (e) {
  }
}
__name(countUsage, "countUsage");
async function markCron(env) {
  try {
    await ensure2(env);
    await env.DB.prepare("INSERT INTO task_state (k, v) VALUES ('cron_last', ?1) ON CONFLICT(k) DO UPDATE SET v = ?1").bind(String(now2())).run();
    await env.DB.prepare("DELETE FROM usage_daily WHERE day < ?1").bind(dayOf(now2() - 400 * 86400)).run();
  } catch (e) {
  }
}
__name(markCron, "markCron");
async function safeAll(env, sql, ...args) {
  try {
    return (await env.DB.prepare(sql).bind(...args).all()).results || [];
  } catch (e) {
    return [];
  }
}
__name(safeAll, "safeAll");
async function safeN(env, sql, ...args) {
  try {
    const r = await env.DB.prepare(sql).bind(...args).first();
    return r ? r.n ?? 0 : 0;
  } catch (e) {
    return null;
  }
}
__name(safeN, "safeN");
async function overview(req, env) {
  await ensure2(env);
  const t = now2();
  const u = new URL(req.url);
  let since = parseInt(u.searchParams.get("since") || "0", 10);
  if (!Number.isFinite(since) || since < t - 30 * 86400) since = t - 86400;
  const d7 = dayOf(t - 6 * 86400), d30 = dayOf(t - 29 * 86400);
  const minR = parseInt(env.TASKS_MIN_REPORTERS || "2", 10);
  const keep = parseInt(env.TASKS_KEEP_DAYS || "8", 10);
  const versions7 = await safeAll(env, `SELECT version, SUM(starts) AS starts, SUM(polls) AS polls FROM usage_daily
    WHERE day >= ?1 GROUP BY version ORDER BY starts DESC, polls DESC LIMIT 30`, d7);
  const daily = await safeAll(env, `SELECT day, SUM(starts) AS starts, SUM(polls) AS polls FROM usage_daily
    WHERE day >= ?1 GROUP BY day ORDER BY day`, d30);
  const taskRows = await safeAll(env, `SELECT r.key, COUNT(*) AS n, COALESCE(a.hidden, 0) AS hidden FROM task_reports r
    LEFT JOIN task_admin a ON a.key = r.key WHERE r.updated > ?1 GROUP BY r.key`, t - keep * 86400);
  const tasks = { public: 0, waiting: 0, hidden: 0, min_reporters: minR };
  for (const r of taskRows) {
    if (r.hidden) tasks.hidden++;
    else if (r.n >= minR) tasks.public++;
    else tasks.waiting++;
  }
  const cron = await env.DB.prepare("SELECT v FROM task_state WHERE k = 'cron_last'").first().catch(() => null);
  const events = {
    suggestions: await safeN(env, "SELECT COUNT(*) AS n FROM tr_suggest WHERE created > ?1", since),
    task_reports: await safeN(env, "SELECT COUNT(*) AS n FROM task_reports WHERE created > ?1", since),
    accounts: await safeN(env, "SELECT COUNT(*) AS n FROM accounts WHERE created > ?1", since),
    redeems: await safeN(env, "SELECT COUNT(*) AS n FROM audit WHERE action = 'redeem' AND t > ?1", since),
    reports: await safeN(env, "SELECT COUNT(*) AS n FROM reports WHERE created > ?1", since)
  };
  return json3({
    now: t,
    since,
    usage: {
      versions_7d: versions7,
      daily_30d: daily,
      starts_today: daily.length && daily[daily.length - 1].day === dayOf(t) ? daily[daily.length - 1].starts : 0
    },
    accounts: {
      total: await safeN(env, "SELECT COUNT(*) AS n FROM accounts WHERE ?1 > 0", t),
      logins_7d: await safeN(env, "SELECT COUNT(*) AS n FROM accounts WHERE last_login > ?1", t - 7 * 86400),
      active_licenses: await safeN(env, "SELECT COUNT(*) AS n FROM licenses WHERE revoked = 0 AND account_id IS NOT NULL AND (expires IS NULL OR expires > ?1)", t),
      expiring_14d: await safeN(env, "SELECT COUNT(*) AS n FROM licenses WHERE revoked = 0 AND account_id IS NOT NULL AND expires IS NOT NULL AND expires > ?1 AND expires < ?2", t, t + 14 * 86400),
      unused_keys: await safeN(env, "SELECT COUNT(*) AS n FROM licenses WHERE account_id IS NULL AND revoked = 0 AND ?1 > 0", t)
    },
    suggestions_pending: await safeN(env, "SELECT COUNT(*) AS n FROM (SELECT 1 FROM tr_suggest WHERE status = 'pending' AND ?1 > 0 GROUP BY en_key, new_hash)", t),
    lines_approved: await safeN(env, "SELECT COUNT(*) AS n FROM tr_lines WHERE ?1 > 0", t),
    tasks,
    reports_queued: await safeN(env, "SELECT COUNT(*) AS n FROM reports WHERE state = 'queued' AND ?1 > 0", t),
    cron_last: cron && cron.v ? parseInt(cron.v, 10) : null,
    events
  });
}
__name(overview, "overview");
async function route3(req, env, path, isAdmin2) {
  if (path === "/v1/admin/overview" && req.method === "GET") {
    if (!await isAdmin2(req, env)) return json3({ error: "forbidden" }, 403);
    return overview(req, env);
  }
  return null;
}
__name(route3, "route");

// mobile.js
var enc3 = new TextEncoder();
var now3 = /* @__PURE__ */ __name(() => Math.floor(Date.now() / 1e3), "now");
var DAY2 = 86400;
var PAIR_TTL = 300;
var DEVICE_TTL = 180 * DAY2;
var ALLOWED_COMMANDS = /* @__PURE__ */ new Set(["scan_start", "scan_stop"]);
var DELETE_GRACE_SECONDS = 24 * 3600;
var FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging";
var _fcmTokenCache = null;
var _apnsJwtCache = null;
function json4(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra }
  });
}
__name(json4, "json");
async function sha2562(text) {
  const d = await crypto.subtle.digest("SHA-256", enc3.encode(text));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
__name(sha2562, "sha256");
function b64uEnc2(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
__name(b64uEnc2, "b64uEnc");
function randomToken2(n = 32) {
  return b64uEnc2(crypto.getRandomValues(new Uint8Array(n)));
}
__name(randomToken2, "randomToken");
var salt2 = /* @__PURE__ */ __name((env) => env.HASH_SALT || "dev-salt", "salt");
var ipOf2 = /* @__PURE__ */ __name((req) => req.headers.get("cf-connecting-ip") || "local", "ipOf");
var ID = /^[A-Za-z0-9_\-]{16,64}$/;
async function rate2(env, bucket, max, windowSec = 3600) {
  const slot = Math.floor(Date.now() / 1e3 / windowSec);
  const row = await env.DB.prepare(
    "INSERT INTO rate (bucket, hour, n) VALUES (?1, ?2, 1) ON CONFLICT(bucket, hour) DO UPDATE SET n = n + 1 RETURNING n"
  ).bind("m:" + bucket, slot).first();
  return (row?.n ?? 1) <= max;
}
__name(rate2, "rate");
async function phoneSession(req, env) {
  const m = /^Bearer\s+([A-Za-z0-9_\-]{32,128})$/.exec(req.headers.get("authorization") || "");
  if (!m) return null;
  const th = await sha2562(m[1]);
  const d = await env.DB.prepare(
    "SELECT device_id, account_id, platform, expires FROM mobile_devices WHERE token_hash = ?1 AND revoked = 0"
  ).bind(th).first();
  if (!d || d.expires < now3()) return null;
  await env.DB.prepare("UPDATE mobile_devices SET last_seen = ?1 WHERE device_id = ?2").bind(now3(), d.device_id).run();
  return d;
}
__name(phoneSession, "phoneSession");
async function createPairing(req, env) {
  const s = await session(req, env);
  if (!s) return json4({ error: "unauthorized" }, 401);
  if (!await rate2(env, "pair:acc:" + s.account_id, 20)) return json4({ error: "rate limited" }, 429);
  await env.DB.prepare("DELETE FROM mobile_pairings WHERE expires < ?1").bind(now3() - DAY2).run();
  const code = randomToken2(6).replace(/[^A-Za-z0-9]/g, "").slice(0, 8).toUpperCase() || "PAIR0000";
  await env.DB.prepare("INSERT INTO mobile_pairings (code_hash, account_id, created, expires) VALUES (?1, ?2, ?3, ?4)").bind(await sha2562(salt2(env) + ":pair:" + code), s.account_id, now3(), now3() + PAIR_TTL).run();
  return json4({ code, expires_in: PAIR_TTL });
}
__name(createPairing, "createPairing");
async function claimPairing(req, env) {
  let b;
  try {
    b = await req.json();
  } catch {
    return json4({ error: "bad json" }, 400);
  }
  const code = String(b?.code || "").toUpperCase().trim();
  const platform = b?.platform === "ios" ? "ios" : b?.platform === "android" ? "android" : null;
  if (!code || !platform) return json4({ error: "bad request" }, 400);
  const ipb = (await sha2562(salt2(env) + ipOf2(req))).slice(0, 24);
  if (!await rate2(env, "claim:ip:" + ipb, 30)) return json4({ error: "rate limited" }, 429);
  const ch = await sha2562(salt2(env) + ":pair:" + code);
  const p = await env.DB.prepare("SELECT * FROM mobile_pairings WHERE code_hash = ?1").bind(ch).first();
  if (!p || p.claimed || p.expires < now3()) return json4({ error: "invalid or expired code" }, 410);
  const r = await env.DB.prepare("UPDATE mobile_pairings SET claimed = 1 WHERE code_hash = ?1 AND claimed = 0").bind(ch).run();
  if (!r.meta?.changes) return json4({ error: "code already used" }, 409);
  const deviceId = randomToken2(16), token = randomToken2(32);
  await env.DB.prepare(
    "INSERT INTO mobile_devices (device_id, account_id, token_hash, platform, created, last_seen, expires) VALUES (?1, ?2, ?3, ?4, ?5, ?5, ?6)"
  ).bind(deviceId, p.account_id, await sha2562(token), platform, now3(), now3() + DEVICE_TTL).run();
  return json4({ device_id: deviceId, token, expires_in: DEVICE_TTL });
}
__name(claimPairing, "claimPairing");
async function dashboard(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json4({ error: "unauthorized" }, 401);
  const st = await env.DB.prepare("SELECT online, last_event, last_seen FROM desktop_status WHERE account_id = ?1").bind(d.account_id).first();
  const online = !!st && st.online && now3() - st.last_seen < 120;
  let lastEvent = null;
  try {
    lastEvent = st?.last_event ? JSON.parse(st.last_event) : null;
  } catch {
    lastEvent = null;
  }
  return json4({ desktop: { online, last_seen: st?.last_seen || null, last_event: lastEvent } });
}
__name(dashboard, "dashboard");
async function sendCommand(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json4({ error: "unauthorized" }, 401);
  let b;
  try {
    b = await req.json();
  } catch {
    return json4({ error: "bad json" }, 400);
  }
  if (!ALLOWED_COMMANDS.has(b?.command)) return json4({ error: "command not allowed" }, 400);
  if (!await rate2(env, "cmd:dev:" + d.device_id, 60)) return json4({ error: "rate limited" }, 429);
  await env.DB.prepare("INSERT INTO desktop_inbox (account_id, command, created) VALUES (?1, ?2, ?3)").bind(d.account_id, b.command, now3()).run();
  return json4({ ok: true });
}
__name(sendCommand, "sendCommand");
async function desktopInbox(req, env) {
  const s = await session(req, env);
  if (!s) return json4({ error: "unauthorized" }, 401);
  const rows = (await env.DB.prepare(
    "SELECT id, command, created FROM desktop_inbox WHERE account_id = ?1 AND delivered = 0 ORDER BY id LIMIT 20"
  ).bind(s.account_id).all()).results || [];
  if (rows.length) {
    const ids = rows.map((r) => r.id);
    await env.DB.batch(ids.map((id) => env.DB.prepare("UPDATE desktop_inbox SET delivered = 1 WHERE id = ?1").bind(id)));
  }
  return json4({ commands: rows.map((r) => ({ command: r.command, created: r.created })) });
}
__name(desktopInbox, "desktopInbox");
async function desktopEvent(req, env, ctx) {
  const s = await session(req, env);
  if (!s) return json4({ error: "unauthorized" }, 401);
  let b;
  try {
    b = await req.json();
  } catch {
    return json4({ error: "bad json" }, 400);
  }
  if (!b || typeof b.type !== "string" || !/^[a-z_]{2,32}$/.test(b.type)) return json4({ error: "bad event" }, 400);
  const safe = {};
  for (const [k, v] of Object.entries(b).slice(0, 12))
    if (/^[a-z_]{1,24}$/.test(k) && ["string", "number", "boolean"].includes(typeof v)) safe[k] = typeof v === "string" ? v.slice(0, 160) : v;
  await env.DB.prepare(
    "INSERT INTO desktop_status (account_id, online, last_event, last_seen) VALUES (?1, 1, ?2, ?3) ON CONFLICT(account_id) DO UPDATE SET online = 1, last_event = ?2, last_seen = ?3"
  ).bind(s.account_id, JSON.stringify(safe), now3()).run();
  if (b.type === "scan_result") {
    const slot = typeof safe.slot === "string" ? safe.slot : "";
    const decisionRaw = typeof safe.decision === "string" ? safe.decision : "";
    const decision = decisionRaw === "keep" ? "Sakla" : decisionRaw === "dismantle" ? "K\u0131r" : decisionRaw;
    const body = slot ? decision ? `${slot}: ${decision}` : slot : "Yeni tarama sonucu";
    const p = sendPush(env, s.account_id, { title: "TD2 Loot Advisor", body, data: { type: "scan_result" } }).catch(() => {
    });
    if (ctx && ctx.waitUntil) ctx.waitUntil(p);
    else await p;
  }
  return json4({ ok: true });
}
__name(desktopEvent, "desktopEvent");
async function listBuilds(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json4({ error: "unauthorized" }, 401);
  const rows = (await env.DB.prepare(
    "SELECT client_id, name, payload, revision, updated, deleted FROM mobile_builds WHERE account_id = ?1 ORDER BY updated DESC LIMIT 500"
  ).bind(d.account_id).all()).results || [];
  return json4({ builds: rows.map((r) => ({
    client_id: r.client_id,
    name: r.name,
    payload: JSON.parse(r.payload),
    revision: r.revision,
    updated: r.updated,
    deleted: !!r.deleted
  })) });
}
__name(listBuilds, "listBuilds");
async function putBuild(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json4({ error: "unauthorized" }, 401);
  let b;
  try {
    b = await req.json();
  } catch {
    return json4({ error: "bad json" }, 400);
  }
  const clientId = String(b?.client_id || "");
  if (!ID.test(clientId)) return json4({ error: "bad client_id" }, 400);
  const name = String(b?.name || "").slice(0, 80).trim();
  if (!name) return json4({ error: "name required" }, 400);
  let payload;
  try {
    payload = JSON.stringify(b.payload ?? {});
  } catch {
    return json4({ error: "bad payload" }, 400);
  }
  if (payload.length > 2e4) return json4({ error: "payload too large" }, 413);
  const baseRev = Number.isFinite(b.base_revision) ? b.base_revision : 0;
  const cur = await env.DB.prepare("SELECT revision FROM mobile_builds WHERE account_id = ?1 AND client_id = ?2").bind(d.account_id, clientId).first();
  if (cur && cur.revision !== baseRev) return json4({ error: "revision conflict", revision: cur.revision }, 409);
  const nextRev = (cur?.revision || 0) + 1;
  await env.DB.prepare(
    "INSERT INTO mobile_builds (account_id, client_id, name, payload, revision, updated, deleted) VALUES (?1, ?2, ?3, ?4, ?5, ?6, 0) ON CONFLICT(account_id, client_id) DO UPDATE SET name = ?3, payload = ?4, revision = ?5, updated = ?6, deleted = 0"
  ).bind(d.account_id, clientId, name, payload, nextRev, now3()).run();
  return json4({ ok: true, revision: nextRev });
}
__name(putBuild, "putBuild");
async function deleteBuild(req, env, clientId) {
  const d = await phoneSession(req, env);
  if (!d) return json4({ error: "unauthorized" }, 401);
  if (!ID.test(clientId)) return json4({ error: "bad client_id" }, 400);
  const cur = await env.DB.prepare("SELECT revision FROM mobile_builds WHERE account_id = ?1 AND client_id = ?2").bind(d.account_id, clientId).first();
  if (!cur) return json4({ error: "not found" }, 404);
  await env.DB.prepare("UPDATE mobile_builds SET deleted = 1, revision = revision + 1, updated = ?1 WHERE account_id = ?2 AND client_id = ?3").bind(now3(), d.account_id, clientId).run();
  return json4({ ok: true, revision: cur.revision + 1 });
}
__name(deleteBuild, "deleteBuild");
function pemToArrayBuffer(pem) {
  const b64 = String(pem || "").replace(/-----BEGIN [^-]+-----/, "").replace(/-----END [^-]+-----/, "").replace(/\s+/g, "");
  const raw = atob(b64);
  const buf = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) buf[i] = raw.charCodeAt(i);
  return buf.buffer;
}
__name(pemToArrayBuffer, "pemToArrayBuffer");
async function fcmAccessToken(env) {
  if (_fcmTokenCache && _fcmTokenCache.expiresAt > now3() + 60) return _fcmTokenCache;
  let sa;
  try {
    sa = JSON.parse(env.FCM_SERVICE_ACCOUNT_JSON || "");
  } catch {
    return null;
  }
  if (!sa?.client_email || !sa?.private_key || !sa?.project_id) return null;
  const iat = now3(), exp = iat + 3600;
  const unsigned = b64uEnc2(enc3.encode(JSON.stringify({ alg: "RS256", typ: "JWT" }))) + "." + b64uEnc2(enc3.encode(JSON.stringify({
    iss: sa.client_email,
    scope: FCM_SCOPE,
    aud: "https://oauth2.googleapis.com/token",
    iat,
    exp
  })));
  let key, sig;
  try {
    key = await crypto.subtle.importKey(
      "pkcs8",
      pemToArrayBuffer(sa.private_key),
      { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
      false,
      ["sign"]
    );
    sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, enc3.encode(unsigned));
  } catch {
    return null;
  }
  const jwt = unsigned + "." + b64uEnc2(new Uint8Array(sig));
  let resp;
  try {
    resp = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: "grant_type=" + encodeURIComponent("urn:ietf:params:oauth:grant-type:jwt-bearer") + "&assertion=" + jwt
    });
  } catch {
    return null;
  }
  if (!resp.ok) return null;
  const tok = await resp.json().catch(() => null);
  if (!tok?.access_token) return null;
  _fcmTokenCache = { accessToken: tok.access_token, expiresAt: iat + (Number(tok.expires_in) || 3600), projectId: sa.project_id };
  return _fcmTokenCache;
}
__name(fcmAccessToken, "fcmAccessToken");
async function apnsProviderJwt(env) {
  if (_apnsJwtCache && _apnsJwtCache.expiresAt > now3() + 60) return _apnsJwtCache;
  const p8 = env.APNS_AUTH_KEY_P8, keyId = env.APNS_KEY_ID, teamId = env.APNS_TEAM_ID;
  if (!p8 || !keyId || !teamId) return null;
  const iat = now3();
  const unsigned = b64uEnc2(enc3.encode(JSON.stringify({ alg: "ES256", kid: keyId }))) + "." + b64uEnc2(enc3.encode(JSON.stringify({ iss: teamId, iat })));
  let key, sig;
  try {
    key = await crypto.subtle.importKey("pkcs8", pemToArrayBuffer(p8), { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
    sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, enc3.encode(unsigned));
  } catch {
    return null;
  }
  _apnsJwtCache = { jwt: unsigned + "." + b64uEnc2(new Uint8Array(sig)), expiresAt: iat + 55 * 60 };
  return _apnsJwtCache;
}
__name(apnsProviderJwt, "apnsProviderJwt");
async function sendPush(env, accountId, payload) {
  const title = String(payload?.title || "TD2 Loot Advisor").slice(0, 120);
  const body = String(payload?.body || "").slice(0, 200);
  const data = payload?.data && typeof payload.data === "object" ? payload.data : {};
  let sent = 0, failed = 0, skipped = [];
  if (env.FCM_SERVICE_ACCOUNT_JSON) {
    const rows = (await env.DB.prepare(
      "SELECT pt.device_id AS device_id, pt.token AS token FROM push_tokens pt JOIN mobile_devices md ON md.device_id = pt.device_id WHERE md.account_id = ?1 AND md.revoked = 0 AND md.platform = 'android'"
    ).bind(accountId).all()).results || [];
    const auth = rows.length ? await fcmAccessToken(env) : null;
    if (rows.length && !auth) {
      failed += rows.length;
    } else {
      for (const row of rows) {
        try {
          const resp = await fetch(`https://fcm.googleapis.com/v1/projects/${auth.projectId}/messages:send`, {
            method: "POST",
            headers: { authorization: "Bearer " + auth.accessToken, "content-type": "application/json" },
            body: JSON.stringify({ message: { token: row.token, notification: { title, body }, data } })
          });
          if (resp.ok) {
            sent++;
            continue;
          }
          failed++;
          const errBody = await resp.json().catch(() => null);
          const status = errBody?.error?.status;
          if (status === "UNREGISTERED" || status === "NOT_FOUND" || status === "INVALID_ARGUMENT")
            await env.DB.prepare("DELETE FROM push_tokens WHERE device_id = ?1").bind(row.device_id).run();
        } catch {
          failed++;
        }
      }
    }
  } else skipped.push("android:no_credentials");
  if (env.APNS_AUTH_KEY_P8 && env.APNS_BUNDLE_ID) {
    const rows = (await env.DB.prepare(
      "SELECT pt.device_id AS device_id, pt.token AS token FROM push_tokens pt JOIN mobile_devices md ON md.device_id = pt.device_id WHERE md.account_id = ?1 AND md.revoked = 0 AND md.platform = 'ios'"
    ).bind(accountId).all()).results || [];
    const prov = rows.length ? await apnsProviderJwt(env) : null;
    if (rows.length && !prov) {
      failed += rows.length;
    } else {
      const apnsHost = env.APNS_ENV === "sandbox" ? "api.sandbox.push.apple.com" : "api.push.apple.com";
      for (const row of rows) {
        try {
          const resp = await fetch(`https://${apnsHost}/3/device/${row.token}`, {
            method: "POST",
            headers: { authorization: "bearer " + prov.jwt, "apns-topic": env.APNS_BUNDLE_ID, "apns-push-type": "alert", "apns-priority": "10" },
            body: JSON.stringify({ aps: { alert: { title, body }, sound: "default" }, ...data })
          });
          if (resp.ok) {
            sent++;
            continue;
          }
          failed++;
          const errBody = await resp.json().catch(() => null);
          if (resp.status === 410 || errBody?.reason === "BadDeviceToken" || errBody?.reason === "Unregistered")
            await env.DB.prepare("DELETE FROM push_tokens WHERE device_id = ?1").bind(row.device_id).run();
        } catch {
          failed++;
        }
      }
    }
  } else skipped.push("ios:no_credentials");
  return { sent, failed, ...skipped.length ? { skipped } : {} };
}
__name(sendPush, "sendPush");
async function putPushToken(req, env, deviceId) {
  const d = await phoneSession(req, env);
  if (!d || d.device_id !== deviceId) return json4({ error: "unauthorized" }, 401);
  let b;
  try {
    b = await req.json();
  } catch {
    return json4({ error: "bad json" }, 400);
  }
  const token = String(b?.token || "");
  if (!token || token.length > 512) return json4({ error: "bad token" }, 400);
  await env.DB.prepare(
    "INSERT INTO push_tokens (device_id, token, platform, created) VALUES (?1, ?2, ?3, ?4) ON CONFLICT(device_id) DO UPDATE SET token = ?2, created = ?4"
  ).bind(deviceId, token, d.platform, now3()).run();
  const delivery = d.platform === "android" && env.FCM_SERVICE_ACCOUNT_JSON || d.platform === "ios" && env.APNS_AUTH_KEY_P8 && env.APNS_BUNDLE_ID ? "available" : "not_yet_implemented";
  return json4({ ok: true, delivery });
}
__name(putPushToken, "putPushToken");
async function deletePushToken(req, env, deviceId) {
  const d = await phoneSession(req, env);
  if (!d || d.device_id !== deviceId) return json4({ error: "unauthorized" }, 401);
  await env.DB.prepare("DELETE FROM push_tokens WHERE device_id = ?1").bind(deviceId).run();
  return json4({ ok: true });
}
__name(deletePushToken, "deletePushToken");
async function listDevices(req, env) {
  const s = await session(req, env);
  if (!s) return json4({ error: "unauthorized" }, 401);
  const rows = (await env.DB.prepare(
    "SELECT device_id, platform, created, last_seen, expires FROM mobile_devices WHERE account_id = ?1 AND revoked = 0 AND expires > ?2 ORDER BY last_seen DESC"
  ).bind(s.account_id, now3()).all()).results || [];
  return json4({ devices: rows });
}
__name(listDevices, "listDevices");
async function revokeDevice(req, env, deviceId) {
  const s = await session(req, env);
  if (!s) return json4({ error: "unauthorized" }, 401);
  const r = await env.DB.prepare("UPDATE mobile_devices SET revoked = 1 WHERE device_id = ?1 AND account_id = ?2").bind(deviceId, s.account_id).run();
  if (!r.meta?.changes) return json4({ error: "not found" }, 404);
  await env.DB.prepare("DELETE FROM push_tokens WHERE device_id = ?1").bind(deviceId).run();
  return json4({ ok: true });
}
__name(revokeDevice, "revokeDevice");
async function deleteMeFromPhone(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json4({ error: "unauthorized" }, 401);
  await env.DB.prepare("INSERT INTO account_deletions (account_id, requested) VALUES (?1, ?2) ON CONFLICT(account_id) DO NOTHING").bind(d.account_id, now3()).run();
  await env.DB.prepare("UPDATE sessions SET revoked = 1 WHERE account_id = ?1").bind(d.account_id).run();
  await env.DB.prepare("UPDATE mobile_devices SET revoked = 1 WHERE account_id = ?1").bind(d.account_id).run();
  return json4({ ok: true, deletion_requested: true });
}
__name(deleteMeFromPhone, "deleteMeFromPhone");
async function cleanup2(env) {
  const t = now3();
  await env.DB.prepare("DELETE FROM mobile_pairings WHERE expires < ?1").bind(t - DAY2).run();
  await env.DB.prepare("DELETE FROM desktop_inbox WHERE delivered = 1 AND created < ?1").bind(t - 7 * DAY2).run();
  await env.DB.prepare("DELETE FROM mobile_devices WHERE revoked = 1 AND last_seen < ?1").bind(t - 30 * DAY2).run();
  const expiredDevices = (await env.DB.prepare(
    "SELECT device_id FROM mobile_devices WHERE revoked = 0 AND expires < ?1"
  ).bind(t - 7 * DAY2).all()).results || [];
  if (expiredDevices.length) {
    const ids = expiredDevices.map((r) => r.device_id);
    await env.DB.batch(ids.map((id) => env.DB.prepare("DELETE FROM push_tokens WHERE device_id = ?1").bind(id)));
    await env.DB.batch(ids.map((id) => env.DB.prepare("DELETE FROM mobile_devices WHERE device_id = ?1").bind(id)));
  }
  const due = (await env.DB.prepare("SELECT account_id FROM account_deletions WHERE requested < ?1").bind(t - DELETE_GRACE_SECONDS).all()).results || [];
  for (const row of due) {
    const id = row.account_id;
    await env.DB.batch([
      env.DB.prepare("DELETE FROM mobile_builds WHERE account_id = ?1").bind(id),
      env.DB.prepare("DELETE FROM desktop_inbox WHERE account_id = ?1").bind(id),
      env.DB.prepare("DELETE FROM desktop_status WHERE account_id = ?1").bind(id),
      env.DB.prepare("DELETE FROM push_tokens WHERE device_id IN (SELECT device_id FROM mobile_devices WHERE account_id = ?1)").bind(id),
      env.DB.prepare("DELETE FROM mobile_devices WHERE account_id = ?1").bind(id),
      env.DB.prepare("DELETE FROM sessions WHERE account_id = ?1").bind(id),
      env.DB.prepare("DELETE FROM devices WHERE license_id IN (SELECT id FROM licenses WHERE account_id = ?1)").bind(id),
      env.DB.prepare("DELETE FROM licenses WHERE account_id = ?1").bind(id),
      env.DB.prepare("DELETE FROM accounts WHERE id = ?1").bind(id),
      env.DB.prepare("DELETE FROM account_deletions WHERE account_id = ?1").bind(id)
    ]);
  }
  return { deleted_accounts: due.length, expired_devices: expiredDevices.length };
}
__name(cleanup2, "cleanup");
async function route4(req, env, path, ctx) {
  let m;
  if (path === "/v1/mobile/pairings" && req.method === "POST") return createPairing(req, env);
  if (path === "/v1/mobile/pairings/claim" && req.method === "POST") return claimPairing(req, env);
  if (path === "/v1/mobile/dashboard" && req.method === "GET") return dashboard(req, env);
  if (path === "/v1/mobile/desktop/inbox" && req.method === "GET") return desktopInbox(req, env);
  if (path === "/v1/mobile/desktop/events" && req.method === "POST") return desktopEvent(req, env, ctx);
  if (path === "/v1/mobile/desktop/commands" && req.method === "POST") return sendCommand(req, env);
  if (path === "/v1/mobile/builds" && req.method === "GET") return listBuilds(req, env);
  if (path === "/v1/mobile/builds" && req.method === "PUT") return putBuild(req, env);
  if ((m = /^\/v1\/mobile\/builds\/([A-Za-z0-9_\-]{16,64})$/.exec(path)) && req.method === "DELETE") return deleteBuild(req, env, m[1]);
  if (path === "/v1/mobile/me" && req.method === "DELETE") return deleteMeFromPhone(req, env);
  if ((m = /^\/v1\/mobile\/push-tokens\/([A-Za-z0-9_\-]{16,64})$/.exec(path)) && req.method === "PUT") return putPushToken(req, env, m[1]);
  if ((m = /^\/v1\/mobile\/push-tokens\/([A-Za-z0-9_\-]{16,64})$/.exec(path)) && req.method === "DELETE") return deletePushToken(req, env, m[1]);
  if (path === "/v1/mobile/devices" && req.method === "GET") return listDevices(req, env);
  if ((m = /^\/v1\/mobile\/devices\/([A-Za-z0-9_\-]{16,64})$/.exec(path)) && req.method === "DELETE") return revokeDevice(req, env, m[1]);
  return null;
}
__name(route4, "route");

// worker.js
var ACTIVITIES = /* @__PURE__ */ new Set([
  "open_world",
  "mission",
  "legendary",
  "countdown",
  "summit",
  "incursion",
  "raid",
  "dark_zone",
  "conflict",
  "descent",
  "manhunt",
  "control_point",
  "bounty",
  "season",
  "vendor",
  "caches",
  "crafting",
  "unknown"
]);
var KINDS = /* @__PURE__ */ new Set(["gear", "weapon", "gear_mod", "weapon_mod", "skill_mod"]);
var SLOTS = /* @__PURE__ */ new Set(["Mask", "Chest", "Backpack", "Gloves", "Holster", "Kneepads", "Weapon", "Sidearm"]);
var RARITIES = /* @__PURE__ */ new Set(["EXOTIC", "NAMED", "GEAR SET", "HIGH-END", "SUPERIOR", "PROTOTYPE"]);
var TEXT = /^[\p{L}\p{N} '.&:\-()/,]{1,60}$/u;
var KEY = /^[a-z_]{2,30}$/;
var HEX = /^[0-9a-f]{8,64}$/;
var enc4 = new TextEncoder();
function json5(data, status = 200, extra = {}) {
  const noBody = status === 204 || status === 205 || status === 304;
  return new Response(noBody ? null : JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      ...extra
    }
  });
}
__name(json5, "json");
async function sha2(text) {
  const d = await crypto.subtle.digest("SHA-256", enc4.encode(text));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
__name(sha2, "sha");
function weekOf(d) {
  const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const back = (t.getUTCDay() - 2 + 7) % 7;
  t.setUTCDate(t.getUTCDate() - back);
  return t.toISOString().slice(0, 10);
}
__name(weekOf, "weekOf");
function str(v) {
  return typeof v === "string" && TEXT.test(v.trim()) ? v.trim() : null;
}
__name(str, "str");
function cleanDrop(x) {
  if (!x || typeof x !== "object") return null;
  const activity = ACTIVITIES.has(x.activity) ? x.activity : "unknown";
  if (!KINDS.has(x.kind)) return null;
  const slot = SLOTS.has(x.slot) ? x.slot : null;
  const rarity = Array.isArray(x.rarity) ? x.rarity.filter((r) => RARITIES.has(r)).slice(0, 3).join("/") : null;
  const attrs = Array.isArray(x.attrs) ? x.attrs.filter((a) => typeof a === "string" && KEY.test(a)).slice(0, 6).sort().join(",") : "";
  const q = Number.isFinite(x.best_q) ? Math.max(0, Math.min(100, Math.round(x.best_q))) : null;
  const name = str(x.name), brand = str(x.brand), gear_set = str(x.gear_set);
  if (!name && !brand && !gear_set) return null;
  const sig = typeof x.sig === "string" && HEX.test(x.sig) ? x.sig : null;
  if (!sig) return null;
  return { activity, kind: x.kind, slot, name, brand, gear_set, rarity, attrs, best_q: q, sig };
}
__name(cleanDrop, "cleanDrop");
async function rateOk(env, bucket, add) {
  const hour = Math.floor(Date.now() / 36e5);
  const max = parseInt(env.MAX_PER_HOUR || "600", 10);
  const row = await env.DB.prepare(
    "INSERT INTO rate (bucket, hour, n) VALUES (?1, ?2, ?3) ON CONFLICT(bucket, hour) DO UPDATE SET n = n + ?3 RETURNING n"
  ).bind(bucket, hour, add).first();
  return (row?.n ?? add) <= max;
}
__name(rateOk, "rateOk");
function b64url(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  s += "=".repeat((4 - s.length % 4) % 4);
  return Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
}
__name(b64url, "b64url");
async function licenseOk(env, header) {
  const e = /^TD2\s+(TD2E-\S+)$/.exec(header || "");
  if (e) {
    const p = await verifyEntitlement(env, e[1]);
    return p && p.tier === "premium" ? { ok: true, payload: p } : { ok: false, why: "entitlement" };
  }
  const m = /^TD2\s+(TD2P-[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)$/.exec(header || "");
  if (!m) return { ok: false, why: "missing" };
  const [body, sig] = m[1].slice(5).split(".");
  let payload;
  try {
    const raw = b64url(body);
    payload = JSON.parse(new TextDecoder().decode(raw));
    const pub = Uint8Array.from(env.LICENSE_PUBKEY.match(/../g).map((h) => parseInt(h, 16)));
    const key = await crypto.subtle.importKey("raw", pub, { name: "Ed25519" }, false, ["verify"]);
    const valid = await crypto.subtle.verify({ name: "Ed25519" }, key, b64url(sig), raw);
    if (!valid) return { ok: false, why: "signature" };
  } catch (e2) {
    return { ok: false, why: "format" };
  }
  if (payload.exp && Date.now() / 1e3 > payload.exp) return { ok: false, why: "expired" };
  if ((payload.tier || "premium") !== "premium") return { ok: false, why: "tier" };
  return { ok: true, payload };
}
__name(licenseOk, "licenseOk");
async function postDrops(req, env) {
  let body;
  try {
    body = await req.json();
  } catch {
    return json5({ error: "bad json" }, 400);
  }
  const client = typeof body?.client === "string" && /^[A-Za-z0-9_\-]{16,64}$/.test(body.client) ? body.client : null;
  if (!client) return json5({ error: "client id required" }, 400);
  const list = Array.isArray(body.drops) ? body.drops.slice(0, parseInt(env.MAX_BATCH || "50", 10)) : [];
  const drops = list.map(cleanDrop).filter(Boolean);
  if (!drops.length) return json5({ accepted: 0 });
  const salt3 = env.HASH_SALT || "dev-salt";
  const ch = (await sha2(salt3 + ":c:" + client)).slice(0, 32);
  const ip = req.headers.get("cf-connecting-ip") || "local";
  const ih = (await sha2(salt3 + ":i:" + ip)).slice(0, 32);
  if (!await rateOk(env, "c:" + ch, drops.length) || !await rateOk(env, "i:" + ih, drops.length))
    return json5({ error: "rate limited" }, 429, { "retry-after": "3600" });
  const now4 = /* @__PURE__ */ new Date(), day = now4.toISOString().slice(0, 10), week = weekOf(now4), ts = Math.floor(now4.getTime() / 1e3);
  const stmt = env.DB.prepare(
    "INSERT OR IGNORE INTO drops (day, week, activity, kind, slot, name, brand, gear_set, rarity, attrs, best_q, client, sig, created) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14)"
  );
  const res = await env.DB.batch(drops.map((d) => stmt.bind(
    day,
    week,
    d.activity,
    d.kind,
    d.slot,
    d.name,
    d.brand,
    d.gear_set,
    d.rarity,
    d.attrs,
    d.best_q,
    ch,
    d.sig,
    ts
  )));
  const accepted = res.reduce((n, r) => n + (r.meta?.changes || 0), 0);
  return json5({ accepted, received: list.length });
}
__name(postDrops, "postDrops");
async function summary(env) {
  const r = await env.DB.prepare(
    "SELECT COUNT(*) AS drops, COUNT(DISTINCT client) AS contributors, MAX(week) AS week FROM drops"
  ).first();
  return json5(
    { drops: r?.drops || 0, contributors: r?.contributors || 0, week: r?.week || null },
    200,
    { "cache-control": "public, max-age=300" }
  );
}
__name(summary, "summary");
async function stats(req, env) {
  const lic = await licenseOk(env, req.headers.get("authorization"));
  if (!lic.ok) return json5({ error: "premium license required", why: lic.why }, 401);
  const u = new URL(req.url);
  const weeks = Math.max(1, Math.min(12, parseInt(u.searchParams.get("weeks") || "4", 10)));
  const since = new Date(Date.now() - weeks * 7 * 864e5).toISOString().slice(0, 10);
  const act = u.searchParams.get("activity");
  const q = str(u.searchParams.get("q") || "");
  const out = { weeks, since };
  out.activities = (await env.DB.prepare(
    "SELECT activity, COUNT(*) AS drops, SUM(rarity LIKE '%EXOTIC%') AS exotic, SUM(rarity LIKE '%NAMED%') AS named, COUNT(DISTINCT client) AS players FROM drops WHERE week >= ?1 GROUP BY activity ORDER BY drops DESC"
  ).bind(since).all()).results;
  if (act && ACTIVITIES.has(act)) {
    out.activity = act;
    out.top = (await env.DB.prepare(
      "SELECT COALESCE(name, gear_set, brand) AS item, kind, slot, rarity, COUNT(*) AS n FROM drops WHERE week >= ?1 AND activity = ?2 GROUP BY item, kind, slot, rarity ORDER BY n DESC LIMIT 40"
    ).bind(since, act).all()).results;
  }
  if (q) {
    out.q = q;
    out.where = (await env.DB.prepare(
      "SELECT d.activity, COUNT(*) AS n, ROUND(1000.0 * COUNT(*) / t.total, 1) AS per1000 FROM drops d JOIN (SELECT activity, COUNT(*) AS total FROM drops WHERE week >= ?1 GROUP BY activity) t ON t.activity = d.activity WHERE d.week >= ?1 AND (d.name = ?2 OR d.gear_set = ?2 OR d.brand = ?2) GROUP BY d.activity ORDER BY per1000 DESC"
    ).bind(since, q).all()).results;
  }
  return json5(out);
}
__name(stats, "stats");
var RTYPES = { bug: "Hata", feature: "\u0130stek", question: "Soru" };
function scrub(t) {
  if (typeof t !== "string") return "";
  return t.replace(/TD2P-[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+/g, "TD2P-<license>").replace(/([A-Za-z]:\\(?:Users|Documents and Settings)\\)[^\\\/\r\n"']+/gi, "$1<user>").replace(/(\/(?:home|Users)\/)[^\/\s"']+/g, "$1<user>").replace(/[\w.+-]+@[\w-]+\.[\w.-]+/g, "<email>").replace(/\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b/g, "<token>").replace(/([A-Za-z]:\/(?:Users|Documents and Settings)\/)[^\/\r\n"']+/gi, "$1<user>").replace(/\bsk-ant-[A-Za-z0-9_\-]{16,}/gi, "<api-key>").replace(/\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}/gi, "<api-key>").replace(/https?:\/\/(?:canary\.|ptb\.)?discord(?:app)?\.com\/api\/webhooks\/\d+\/[\w\-]+/gi, "<webhook>").replace(/\bTD2[KIE]-[A-Za-z0-9_\-.]{6,}/gi, "TD2-<key>").replace(/\bdpapi:[A-Za-z0-9+\/=]+/gi, "<secret>").replace(/([?&](?:t|token|key|access_token)=)[^&\s"']+/gi, "$1<token>").replace(/\b(Bearer|Admin|TD2)\s+[A-Za-z0-9._~+\/=\-]{12,}/g, "$1 <token>").replace(/(ntfy\.sh\/)[A-Za-z0-9_\-]+/gi, "$1<topic>").replace(/\b(?:10|127)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|\b192\.168\.\d{1,3}\.\d{1,3}\b|\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b/g, "<lan-ip>");
}
__name(scrub, "scrub");
function clip(v, n) {
  return typeof v === "string" ? v.replace(/\u0000/g, "").slice(0, n) : "";
}
__name(clip, "clip");
function cleanReport(b) {
  if (!b || typeof b !== "object") return null;
  const type = RTYPES[b.type] ? b.type : null;
  const title = clip(b.title, 120).trim();
  const body = clip(b.body, 6e3).trim();
  if (!type || title.length < 4 || body.length < 10) return null;
  const sys = {};
  if (b.system && typeof b.system === "object") {
    for (const [k, v] of Object.entries(b.system).slice(0, 24))
      if (/^[a-z_]{2,24}$/.test(k) && ["string", "number", "boolean"].includes(typeof v)) sys[k] = typeof v === "string" ? clip(v, 160) : v;
  }
  const ver = /^\d+\.\d+(\.\d+)?$/.test(b.app_version || "") ? b.app_version : "?";
  const lang = /^[a-z]{2}$/.test(b.lang || "") ? b.lang : "?";
  return {
    type,
    title: scrub(title),
    body: scrub(body),
    contact: scrub(clip(b.contact, 80).trim()),
    app_version: ver,
    lang,
    system: JSON.parse(scrub(JSON.stringify(sys))),
    log: scrub(clip(b.log, 12e3)),
    card: scrub(clip(b.card, 3e3))
  };
}
__name(cleanReport, "cleanReport");
function issueOf(r, clientShort) {
  const meta = { v: 1, type: r.type, app_version: r.app_version, lang: r.lang, client: clientShort, system: r.system };
  const sysLines = Object.entries(r.system).map(([k, v]) => `| ${k} | ${String(v).replace(/\|/g, "/")} |`).join("\n");
  const parts = [r.body, "", "---", `**T\xFCr:** ${RTYPES[r.type]} \xB7 **S\xFCr\xFCm:** ${r.app_version} \xB7 **Dil:** ${r.lang}` + (r.contact ? ` \xB7 **\u0130leti\u015Fim:** ${r.contact}` : "")];
  if (sysLines) parts.push("", "<details><summary>Sistem</summary>\n\n| | |\n|---|---|\n" + sysLines + "\n</details>");
  if (r.card) parts.push("", "<details><summary>Okunan kart</summary>\n\n```\n" + r.card + "\n```\n</details>");
  if (r.log) parts.push("", "<details><summary>Kay\u0131t (son sat\u0131rlar)</summary>\n\n```\n" + r.log + "\n```\n</details>");
  parts.push("", `<!-- td2-report ${JSON.stringify(meta)} -->`);
  return {
    title: `[${RTYPES[r.type]}] ${r.title}`,
    body: parts.join("\n"),
    labels: ["report", "type:" + r.type, "status:new", "v" + r.app_version, "lang:" + r.lang]
  };
}
__name(issueOf, "issueOf");
async function gh(env, path, opts = {}) {
  const base = env.GITHUB_API || "https://api.github.com";
  const res = await fetch(base + path, { ...opts, headers: {
    "authorization": "Bearer " + env.GITHUB_TOKEN,
    "accept": "application/vnd.github+json",
    "user-agent": "td2-loot-advisor-reports",
    "content-type": "application/json",
    "x-github-api-version": "2022-11-28",
    ...opts.headers || {}
  } });
  if (!res.ok) throw new Error("github " + res.status);
  return res.json();
}
__name(gh, "gh");
async function rateCheck2(env, bucket, max, hours) {
  const hour = Math.floor(Date.now() / 36e5);
  const r = await env.DB.prepare("SELECT COALESCE(SUM(n),0) AS n FROM rate WHERE bucket = ?1 AND hour > ?2").bind(bucket, hour - hours).first();
  return (r ? r.n : 0) < max;
}
__name(rateCheck2, "rateCheck");
async function rateAdd2(env, bucket) {
  const hour = Math.floor(Date.now() / 36e5);
  await env.DB.prepare("INSERT INTO rate (bucket, hour, n) VALUES (?1, ?2, 1) ON CONFLICT(bucket, hour) DO UPDATE SET n = n + 1").bind(bucket, hour).run();
}
__name(rateAdd2, "rateAdd");
async function forward(env, rowId, payload) {
  const iss = await gh(env, `/repos/${env.REPORTS_REPO}/issues`, { method: "POST", body: JSON.stringify(payload) });
  await env.DB.prepare("UPDATE reports SET number = ?1, state = 'sent' WHERE id = ?2").bind(iss.number, rowId).run();
  return iss.number;
}
__name(forward, "forward");
async function postReport(req, env) {
  let b;
  try {
    b = await req.json();
  } catch {
    return json5({ error: "bad json" }, 400);
  }
  const r = cleanReport(b);
  if (!r) return json5({ error: "invalid report" }, 400);
  const salt3 = env.HASH_SALT || "dev-salt";
  const client = await sha2(salt3 + "|" + String(b.client || "").slice(0, 64));
  const ip = await sha2(salt3 + "|ip|" + (req.headers.get("cf-connecting-ip") || ""));
  const maxH = parseInt(env.REPORTS_PER_HOUR || "5", 10), maxD = parseInt(env.REPORTS_PER_DAY || "20", 10);
  for (const bk of ["rc:" + client, "ri:" + ip]) {
    if (!await rateCheck2(env, bk, maxH, 1) || !await rateCheck2(env, bk, maxD, 24)) return json5({ error: "rate limited" }, 429);
  }
  await rateAdd2(env, "rc:" + client);
  await rateAdd2(env, "ri:" + ip);
  const payload = issueOf(r, client.slice(0, 10));
  const ins = await env.DB.prepare("INSERT INTO reports (created, client, payload, state) VALUES (?1, ?2, ?3, 'queued') RETURNING id").bind(Date.now(), client, JSON.stringify(payload)).first();
  if (env.GITHUB_TOKEN && env.REPORTS_REPO) {
    try {
      const number = await forward(env, ins.id, payload);
      return json5({ ok: true, id: ins.id, number });
    } catch (e) {
    }
  }
  return json5({ ok: true, id: ins.id, number: null, queued: true });
}
__name(postReport, "postReport");
async function reportStatus(req, env) {
  const u = new URL(req.url);
  const salt3 = env.HASH_SALT || "dev-salt";
  const client = await sha2(salt3 + "|" + String(u.searchParams.get("client") || "").slice(0, 64));
  const ids = (u.searchParams.get("ids") || "").split(",").map((x) => parseInt(x, 10)).filter(Number.isFinite).slice(0, 20);
  const out = [];
  for (const id of ids) {
    const row = await env.DB.prepare("SELECT id, number, state FROM reports WHERE id = ?1 AND client = ?2").bind(id, client).first();
    if (!row) continue;
    const item = { id: row.id, number: row.number, state: row.state };
    if (row.number && env.GITHUB_TOKEN) {
      try {
        const iss = await gh(env, `/repos/${env.REPORTS_REPO}/issues/${row.number}`);
        item.state = iss.state;
        const st = (iss.labels || []).map((l) => l.name || l).find((n) => n.startsWith("status:"));
        item.status = st ? st.slice(7) : "new";
        item.updated = iss.updated_at;
        if (iss.comments && env.ADMIN_LOGIN) {
          const cs = await gh(env, `/repos/${env.REPORTS_REPO}/issues/${row.number}/comments?per_page=50`);
          const mine = cs.filter((c) => c.user && c.user.login === env.ADMIN_LOGIN);
          if (mine.length) item.reply = clip(mine[mine.length - 1].body, 1500);
        }
      } catch (e) {
        item.error = "github";
      }
    }
    out.push(item);
  }
  return json5({ reports: out });
}
__name(reportStatus, "reportStatus");
async function flushQueue(env) {
  if (!env.GITHUB_TOKEN || !env.REPORTS_REPO) return 0;
  const rows = (await env.DB.prepare("SELECT id, payload FROM reports WHERE state = 'queued' ORDER BY id LIMIT 20").all()).results || [];
  let n = 0;
  for (const row of rows) {
    try {
      await forward(env, row.id, JSON.parse(row.payload));
      n++;
    } catch (e) {
      break;
    }
  }
  return n;
}
__name(flushQueue, "flushQueue");
var worker_default = {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    try {
      if (req.method === "OPTIONS") return json5({}, 204, {
        "access-control-allow-methods": "GET, POST, PUT, DELETE",
        "access-control-allow-headers": "content-type, authorization"
      });
      if (u.pathname === "/v1/health") return json5({ ok: true, login: !!env.DISCORD_CLIENT_ID, discord_app: env.DISCORD_CLIENT_ID || null });
      if (req.method === "POST" && parseInt(req.headers.get("content-length") || "0", 10) > 262144)
        return json5({ error: "payload too large" }, 413);
      if (u.pathname === "/v1/tasks/live" && req.method === "GET") {
        const c = countUsage(req, env);
        if (ctx && ctx.waitUntil) ctx.waitUntil(c);
        else await c;
      }
      const ov = await route3(req, env, u.pathname, isAdmin);
      if (ov) return ov;
      const tk = await route2(req, env, u.pathname, isAdmin, ctx);
      if (tk) return tk;
      const acc = await route(req, env, u.pathname);
      if (acc) return acc;
      const mob = await route4(req, env, u.pathname, ctx);
      if (mob) return mob;
      if (u.pathname === "/v1/drops" && req.method === "POST") return await postDrops(req, env);
      if (u.pathname === "/v1/summary" && req.method === "GET") return await summary(env);
      if (u.pathname === "/v1/stats" && req.method === "GET") return await stats(req, env);
      if (u.pathname === "/v1/reports" && req.method === "POST") return await postReport(req, env);
      if (u.pathname === "/v1/reports/status" && req.method === "GET") return await reportStatus(req, env);
      return json5({ error: "not found" }, 404);
    } catch (e) {
      return json5({ error: "server error" }, 500);
    }
  },
  async scheduled(_event, env) {
    const hour = Math.floor(Date.now() / 36e5) - 48;
    await env.DB.prepare("DELETE FROM rate WHERE hour < ?1").bind(hour).run();
    const t = Math.floor(Date.now() / 1e3);
    await env.DB.prepare("DELETE FROM auth_pending WHERE created < ?1").bind(t - 900).run();
    await env.DB.prepare("DELETE FROM sessions WHERE expires < ?1 OR (revoked = 1 AND last_seen < ?2)").bind(t, t - 7 * 86400).run();
    await flushQueue(env);
    try {
      await cleanup(env);
      await snapshotToRepo(env, gh);
    } catch (e) {
    }
    try {
      await cleanup2(env);
    } catch (e) {
    }
    await markCron(env);
  }
};
export {
  worker_default as default,
  scrub
};
