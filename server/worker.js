// TD2 Loot Advisor — topluluk düşüş istatistikleri (Cloudflare Worker + D1)
//
//   POST /v1/drops     anonim düşüş kayıtları (gönüllü)           herkese açık, oran sınırlı
//   GET  /v1/summary   toplam düşüş / katkıcı sayısı               herkese açık
//   GET  /v1/stats     aktivite başına en çok düşenler, eşya arama  premium (Authorization: TD2 <lisans>)
//   GET  /v1/health
//
// Gizlilik: IP saklanmaz; istemci kimliği tuzlu SHA-256 ile özetlenir; attribute DEĞERLERİ değil yalnız türleri alınır.

const ACTIVITIES = new Set(["open_world", "mission", "legendary", "countdown", "summit", "incursion", "raid", "dark_zone",
  "conflict", "descent", "manhunt", "control_point", "bounty", "season", "vendor", "caches", "crafting", "unknown"]);
const KINDS = new Set(["gear", "weapon", "gear_mod", "weapon_mod", "skill_mod"]);
const SLOTS = new Set(["Mask", "Chest", "Backpack", "Gloves", "Holster", "Kneepads", "Weapon", "Sidearm"]);
const RARITIES = new Set(["EXOTIC", "NAMED", "GEAR SET", "HIGH-END", "SUPERIOR", "PROTOTYPE"]);
const TEXT = /^[\p{L}\p{N} '.&:\-()/,]{1,60}$/u;
const KEY = /^[a-z_]{2,30}$/;
const HEX = /^[0-9a-f]{8,64}$/;

const enc = new TextEncoder();

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store",
               "access-control-allow-origin": "*", ...extra },
  });
}

async function sha(text) {
  const d = await crypto.subtle.digest("SHA-256", enc.encode(text));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("");
}

function weekOf(d) {                       // haftalık sıfırlama Salı: o haftanın Salı günü
  const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const back = (t.getUTCDay() - 2 + 7) % 7;
  t.setUTCDate(t.getUTCDate() - back);
  return t.toISOString().slice(0, 10);
}

function str(v) { return typeof v === "string" && TEXT.test(v.trim()) ? v.trim() : null; }

function cleanDrop(x) {
  if (!x || typeof x !== "object") return null;
  const activity = ACTIVITIES.has(x.activity) ? x.activity : "unknown";
  if (!KINDS.has(x.kind)) return null;
  const slot = SLOTS.has(x.slot) ? x.slot : null;
  const rarity = Array.isArray(x.rarity) ? x.rarity.filter(r => RARITIES.has(r)).slice(0, 3).join("/") : null;
  const attrs = Array.isArray(x.attrs) ? x.attrs.filter(a => typeof a === "string" && KEY.test(a)).slice(0, 6).sort().join(",") : "";
  const q = Number.isFinite(x.best_q) ? Math.max(0, Math.min(100, Math.round(x.best_q))) : null;
  const name = str(x.name), brand = str(x.brand), gear_set = str(x.gear_set);
  if (!name && !brand && !gear_set) return null;
  const sig = typeof x.sig === "string" && HEX.test(x.sig) ? x.sig : null;
  if (!sig) return null;
  return { activity, kind: x.kind, slot, name, brand, gear_set, rarity, attrs, best_q: q, sig };
}

async function rateOk(env, bucket, add) {
  const hour = Math.floor(Date.now() / 3600000);
  const max = parseInt(env.MAX_PER_HOUR || "600", 10);
  const row = await env.DB.prepare(
    "INSERT INTO rate (bucket, hour, n) VALUES (?1, ?2, ?3) ON CONFLICT(bucket, hour) DO UPDATE SET n = n + ?3 RETURNING n"
  ).bind(bucket, hour, add).first();
  return (row?.n ?? add) <= max;
}

// ------------------------------------------------------------ lisans (Ed25519, uygulamadaki features.py ile aynı biçim)
function b64url(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/"); s += "=".repeat((4 - s.length % 4) % 4);
  return Uint8Array.from(atob(s), c => c.charCodeAt(0));
}

async function licenseOk(env, header) {
  const m = /^TD2\s+(TD2P-[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)$/.exec(header || "");
  if (!m) return { ok: false, why: "missing" };
  const [body, sig] = m[1].slice(5).split(".");
  let payload;
  try {
    const raw = b64url(body);
    payload = JSON.parse(new TextDecoder().decode(raw));
    const pub = Uint8Array.from(env.LICENSE_PUBKEY.match(/../g).map(h => parseInt(h, 16)));
    const key = await crypto.subtle.importKey("raw", pub, { name: "Ed25519" }, false, ["verify"]);
    const valid = await crypto.subtle.verify({ name: "Ed25519" }, key, b64url(sig), raw);
    if (!valid) return { ok: false, why: "signature" };
  } catch (e) {
    return { ok: false, why: "format" };
  }
  if (payload.exp && Date.now() / 1000 > payload.exp) return { ok: false, why: "expired" };
  if ((payload.tier || "premium") !== "premium") return { ok: false, why: "tier" };
  return { ok: true, payload };
}

// ------------------------------------------------------------ uç noktalar
async function postDrops(req, env) {
  let body;
  try { body = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const client = typeof body?.client === "string" && /^[A-Za-z0-9_\-]{16,64}$/.test(body.client) ? body.client : null;
  if (!client) return json({ error: "client id required" }, 400);
  const list = Array.isArray(body.drops) ? body.drops.slice(0, parseInt(env.MAX_BATCH || "50", 10)) : [];
  const drops = list.map(cleanDrop).filter(Boolean);
  if (!drops.length) return json({ accepted: 0 });
  const salt = env.HASH_SALT || "dev-salt";
  const ch = (await sha(salt + ":c:" + client)).slice(0, 32);
  const ip = req.headers.get("cf-connecting-ip") || "local";
  const ih = (await sha(salt + ":i:" + ip)).slice(0, 32);
  if (!(await rateOk(env, "c:" + ch, drops.length)) || !(await rateOk(env, "i:" + ih, drops.length)))
    return json({ error: "rate limited" }, 429, { "retry-after": "3600" });
  const now = new Date(), day = now.toISOString().slice(0, 10), week = weekOf(now), ts = Math.floor(now.getTime() / 1000);
  const stmt = env.DB.prepare(
    "INSERT OR IGNORE INTO drops (day, week, activity, kind, slot, name, brand, gear_set, rarity, attrs, best_q, client, sig, created) " +
    "VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14)");
  const res = await env.DB.batch(drops.map(d => stmt.bind(day, week, d.activity, d.kind, d.slot, d.name, d.brand, d.gear_set,
                                                           d.rarity, d.attrs, d.best_q, ch, d.sig, ts)));
  const accepted = res.reduce((n, r) => n + (r.meta?.changes || 0), 0);
  return json({ accepted, received: list.length });
}

async function summary(env) {
  const r = await env.DB.prepare(
    "SELECT COUNT(*) AS drops, COUNT(DISTINCT client) AS contributors, MAX(week) AS week FROM drops").first();
  return json({ drops: r?.drops || 0, contributors: r?.contributors || 0, week: r?.week || null },
              200, { "cache-control": "public, max-age=300" });
}

async function stats(req, env) {
  const lic = await licenseOk(env, req.headers.get("authorization"));
  if (!lic.ok) return json({ error: "premium license required", why: lic.why }, 401);
  const u = new URL(req.url);
  const weeks = Math.max(1, Math.min(12, parseInt(u.searchParams.get("weeks") || "4", 10)));
  const since = new Date(Date.now() - weeks * 7 * 86400000).toISOString().slice(0, 10);
  const act = u.searchParams.get("activity");
  const q = str(u.searchParams.get("q") || "");
  const out = { weeks, since };
  out.activities = (await env.DB.prepare(
    "SELECT activity, COUNT(*) AS drops, SUM(rarity LIKE '%EXOTIC%') AS exotic, SUM(rarity LIKE '%NAMED%') AS named, " +
    "COUNT(DISTINCT client) AS players FROM drops WHERE week >= ?1 GROUP BY activity ORDER BY drops DESC").bind(since).all()).results;
  if (act && ACTIVITIES.has(act)) {
    out.activity = act;
    out.top = (await env.DB.prepare(
      "SELECT COALESCE(name, gear_set, brand) AS item, kind, slot, rarity, COUNT(*) AS n FROM drops " +
      "WHERE week >= ?1 AND activity = ?2 GROUP BY item, kind, slot, rarity ORDER BY n DESC LIMIT 40").bind(since, act).all()).results;
  }
  if (q) {
    out.q = q;
    out.where = (await env.DB.prepare(
      "SELECT d.activity, COUNT(*) AS n, ROUND(1000.0 * COUNT(*) / t.total, 1) AS per1000 FROM drops d " +
      "JOIN (SELECT activity, COUNT(*) AS total FROM drops WHERE week >= ?1 GROUP BY activity) t ON t.activity = d.activity " +
      "WHERE d.week >= ?1 AND (d.name = ?2 OR d.gear_set = ?2 OR d.brand = ?2) GROUP BY d.activity ORDER BY per1000 DESC")
      .bind(since, q).all()).results;
  }
  return json(out);
}

export default {
  async fetch(req, env) {
    const u = new URL(req.url);
    try {
      if (req.method === "OPTIONS") return json({}, 204, { "access-control-allow-methods": "GET, POST",
                                                           "access-control-allow-headers": "content-type, authorization" });
      if (u.pathname === "/v1/health") return json({ ok: true });
      if (u.pathname === "/v1/drops" && req.method === "POST") return await postDrops(req, env);
      if (u.pathname === "/v1/summary" && req.method === "GET") return await summary(env);
      if (u.pathname === "/v1/stats" && req.method === "GET") return await stats(req, env);
      return json({ error: "not found" }, 404);
    } catch (e) {
      return json({ error: "server error" }, 500);
    }
  },
  async scheduled(_event, env) {                       // eski oran kayıtlarını sil (48 saatten eski)
    const hour = Math.floor(Date.now() / 3600000) - 48;
    await env.DB.prepare("DELETE FROM rate WHERE hour < ?1").bind(hour).run();
  },
};

