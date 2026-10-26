// TD2 Loot Advisor — topluluk düşüş istatistikleri (Cloudflare Worker + D1)
//
//   POST /v1/drops     anonim düşüş kayıtları (gönüllü)           herkese açık, oran sınırlı
//   GET  /v1/summary   toplam düşüş / katkıcı sayısı               herkese açık
//   GET  /v1/stats     aktivite başına en çok düşenler, eşya arama  premium (Authorization: TD2 <lisans>)
//   GET  /v1/health
//   POST /v1/reports   hata raporu / istek (programdan)             herkese açık, istemci+IP başına sınırlı
//   GET  /v1/reports/status?client=..&n=12,15   gönderenin kendi raporlarının durumu ve yanıt
//
// Raporlar özel bir GitHub deposunda "issue" olarak açılır (REPORTS_REPO, gizli GITHUB_TOKEN). Token yoksa ya da
// GitHub ulaşılamazsa rapor D1'de bekletilir ve saatlik görevde iletilir. Kişisel veriler (kullanıcı klasörü
// yolları, lisans anahtarları, e-postalar) temizlenir.
//
//   Topluluk görevleri (tasks.js): POST /v1/tasks, GET /v1/tasks/live, /v1/admin/tasks*
//   Hesap / lisans (accounts.js): /v1/auth/start|callback|token|logout, /v1/me, /v1/license/redeem, /v1/admin/*
//
// Gizlilik: IP saklanmaz; istemci kimliği tuzlu SHA-256 ile özetlenir; attribute DEĞERLERİ değil yalnız türleri alınır.

import { route as accountRoute, verifyEntitlement, isAdmin } from "./accounts.js";
import { route as tasksRoute, snapshotToRepo, cleanup as tasksCleanup } from "./tasks.js";

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
  const e = /^TD2\s+(TD2E-\S+)$/.exec(header || "");
  if (e) {                                               // hesap yetki belgesi (Discord girişi + anahtar)
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

// ------------------------------------------------------------------ raporlar
const RTYPES = { bug: "Hata", feature: "İstek", question: "Soru" };
const STATUS = ["new", "triaged", "in-progress", "done", "wontfix", "duplicate"];

function scrub(t) {
  if (typeof t !== "string") return "";
  return t
    .replace(/TD2P-[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+/g, "TD2P-<license>")
    .replace(/([A-Za-z]:\\(?:Users|Documents and Settings)\\)[^\\\/\r\n"']+/gi, "$1<user>")
    .replace(/(\/(?:home|Users)\/)[^\/\s"']+/g, "$1<user>")
    .replace(/[\w.+-]+@[\w-]+\.[\w.-]+/g, "<email>")
    .replace(/\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b/g, "<token>")
    .replace(/([A-Za-z]:\/(?:Users|Documents and Settings)\/)[^\/\r\n"']+/gi, "$1<user>")
    .replace(/\bsk-ant-[A-Za-z0-9_\-]{16,}/gi, "<api-key>").replace(/\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}/gi, "<api-key>")
    .replace(/https?:\/\/(?:canary\.|ptb\.)?discord(?:app)?\.com\/api\/webhooks\/\d+\/[\w\-]+/gi, "<webhook>")
    .replace(/\bTD2[KIE]-[A-Za-z0-9_\-.]{6,}/gi, "TD2-<key>").replace(/\bdpapi:[A-Za-z0-9+\/=]+/gi, "<secret>")
    .replace(/([?&](?:t|token|key|access_token)=)[^&\s"']+/gi, "$1<token>")
    .replace(/\b(Bearer|Admin|TD2)\s+[A-Za-z0-9._~+\/=\-]{12,}/g, "$1 <token>")
    .replace(/(ntfy\.sh\/)[A-Za-z0-9_\-]+/gi, "$1<topic>")
    .replace(/\b(?:10|127)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|\b192\.168\.\d{1,3}\.\d{1,3}\b|\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b/g, "<lan-ip>");
}
export { scrub };

function clip(v, n) { return typeof v === "string" ? v.replace(/\u0000/g, "").slice(0, n) : ""; }

function cleanReport(b) {
  if (!b || typeof b !== "object") return null;
  const type = RTYPES[b.type] ? b.type : null;
  const title = clip(b.title, 120).trim();
  const body = clip(b.body, 6000).trim();
  if (!type || title.length < 4 || body.length < 10) return null;
  const sys = {};
  if (b.system && typeof b.system === "object")
    for (const [k, v] of Object.entries(b.system).slice(0, 24))
      if (/^[a-z_]{2,24}$/.test(k) && ["string", "number", "boolean"].includes(typeof v)) sys[k] = typeof v === "string" ? clip(v, 160) : v;
  const ver = /^\d+\.\d+(\.\d+)?$/.test(b.app_version || "") ? b.app_version : "?";
  const lang = /^[a-z]{2}$/.test(b.lang || "") ? b.lang : "?";
  return { type, title: scrub(title), body: scrub(body), contact: scrub(clip(b.contact, 80).trim()), app_version: ver, lang,
           system: JSON.parse(scrub(JSON.stringify(sys))), log: scrub(clip(b.log, 12000)), card: scrub(clip(b.card, 3000)) };
}

function issueOf(r, clientShort) {
  const meta = { v: 1, type: r.type, app_version: r.app_version, lang: r.lang, client: clientShort, system: r.system };
  const sysLines = Object.entries(r.system).map(([k, v]) => `| ${k} | ${String(v).replace(/\|/g, "/")} |`).join("\n");
  const parts = [r.body, "", "---", `**Tür:** ${RTYPES[r.type]} · **Sürüm:** ${r.app_version} · **Dil:** ${r.lang}` +
                 (r.contact ? ` · **İletişim:** ${r.contact}` : "")];
  if (sysLines) parts.push("", "<details><summary>Sistem</summary>\n\n| | |\n|---|---|\n" + sysLines + "\n</details>");
  if (r.card) parts.push("", "<details><summary>Okunan kart</summary>\n\n```\n" + r.card + "\n```\n</details>");
  if (r.log) parts.push("", "<details><summary>Kayıt (son satırlar)</summary>\n\n```\n" + r.log + "\n```\n</details>");
  parts.push("", `<!-- td2-report ${JSON.stringify(meta)} -->`);
  return { title: `[${RTYPES[r.type]}] ${r.title}`, body: parts.join("\n"),
           labels: ["report", "type:" + r.type, "status:new", "v" + r.app_version, "lang:" + r.lang] };
}

async function gh(env, path, opts = {}) {
  const base = env.GITHUB_API || "https://api.github.com";
  const res = await fetch(base + path, { ...opts, headers: { "authorization": "Bearer " + env.GITHUB_TOKEN,
    "accept": "application/vnd.github+json", "user-agent": "td2-loot-advisor-reports", "content-type": "application/json",
    "x-github-api-version": "2022-11-28", ...(opts.headers || {}) } });
  if (!res.ok) throw new Error("github " + res.status);
  return res.json();
}

async function rateCheck(env, bucket, max, hours) {
  const hour = Math.floor(Date.now() / 3600000);
  const r = await env.DB.prepare("SELECT COALESCE(SUM(n),0) AS n FROM rate WHERE bucket = ?1 AND hour > ?2")
    .bind(bucket, hour - hours).first();
  return (r ? r.n : 0) < max;
}

async function rateAdd(env, bucket) {
  const hour = Math.floor(Date.now() / 3600000);
  await env.DB.prepare("INSERT INTO rate (bucket, hour, n) VALUES (?1, ?2, 1) ON CONFLICT(bucket, hour) DO UPDATE SET n = n + 1")
    .bind(bucket, hour).run();
}

async function forward(env, rowId, payload) {
  const iss = await gh(env, `/repos/${env.REPORTS_REPO}/issues`, { method: "POST", body: JSON.stringify(payload) });
  await env.DB.prepare("UPDATE reports SET number = ?1, state = 'sent' WHERE id = ?2").bind(iss.number, rowId).run();
  return iss.number;
}

async function postReport(req, env) {
  let b;
  try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const r = cleanReport(b);
  if (!r) return json({ error: "invalid report" }, 400);
  const salt = env.HASH_SALT || "dev-salt";
  const client = await sha(salt + "|" + String(b.client || "").slice(0, 64));
  const ip = await sha(salt + "|ip|" + (req.headers.get("cf-connecting-ip") || ""));
  const maxH = parseInt(env.REPORTS_PER_HOUR || "5", 10), maxD = parseInt(env.REPORTS_PER_DAY || "20", 10);
  for (const bk of ["rc:" + client, "ri:" + ip]) {
    if (!(await rateCheck(env, bk, maxH, 1)) || !(await rateCheck(env, bk, maxD, 24))) return json({ error: "rate limited" }, 429);
  }
  await rateAdd(env, "rc:" + client); await rateAdd(env, "ri:" + ip);
  const payload = issueOf(r, client.slice(0, 10));
  const ins = await env.DB.prepare("INSERT INTO reports (created, client, payload, state) VALUES (?1, ?2, ?3, 'queued') RETURNING id")
    .bind(Date.now(), client, JSON.stringify(payload)).first();
  if (env.GITHUB_TOKEN && env.REPORTS_REPO) {
    try {
      const number = await forward(env, ins.id, payload);
      return json({ ok: true, id: ins.id, number });
    } catch (e) { /* GitHub ulaşılamadı: kuyrukta kalır, saatlik görev iletir */ }
  }
  return json({ ok: true, id: ins.id, number: null, queued: true });
}

async function reportStatus(req, env) {
  const u = new URL(req.url);
  const salt = env.HASH_SALT || "dev-salt";
  const client = await sha(salt + "|" + String(u.searchParams.get("client") || "").slice(0, 64));
  const ids = (u.searchParams.get("ids") || "").split(",").map(x => parseInt(x, 10)).filter(Number.isFinite).slice(0, 20);
  const out = [];
  for (const id of ids) {
    const row = await env.DB.prepare("SELECT id, number, state FROM reports WHERE id = ?1 AND client = ?2").bind(id, client).first();
    if (!row) continue;                                     // yalnız kendi raporları
    const item = { id: row.id, number: row.number, state: row.state };
    if (row.number && env.GITHUB_TOKEN) {
      try {
        const iss = await gh(env, `/repos/${env.REPORTS_REPO}/issues/${row.number}`);
        item.state = iss.state;
        const st = (iss.labels || []).map(l => l.name || l).find(n => n.startsWith("status:"));
        item.status = st ? st.slice(7) : "new";
        item.updated = iss.updated_at;
        if (iss.comments && env.ADMIN_LOGIN) {
          const cs = await gh(env, `/repos/${env.REPORTS_REPO}/issues/${row.number}/comments?per_page=50`);
          const mine = cs.filter(c => c.user && c.user.login === env.ADMIN_LOGIN);
          if (mine.length) item.reply = clip(mine[mine.length - 1].body, 1500);
        }
      } catch (e) { item.error = "github"; }
    }
    out.push(item);
  }
  return json({ reports: out });
}

async function flushQueue(env) {
  if (!env.GITHUB_TOKEN || !env.REPORTS_REPO) return 0;
  const rows = (await env.DB.prepare("SELECT id, payload FROM reports WHERE state = 'queued' ORDER BY id LIMIT 20").all()).results || [];
  let n = 0;
  for (const row of rows) {
    try { await forward(env, row.id, JSON.parse(row.payload)); n++; } catch (e) { break; }
  }
  return n;
}

export default {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    try {
      if (req.method === "OPTIONS") return json({}, 204, { "access-control-allow-methods": "GET, POST",
                                                           "access-control-allow-headers": "content-type, authorization" });
      if (u.pathname === "/v1/health") return json({ ok: true, login: !!env.DISCORD_CLIENT_ID, discord_app: env.DISCORD_CLIENT_ID || null });
      if (req.method === "POST" && parseInt(req.headers.get("content-length") || "0", 10) > 262144)   // büyük gövde: reddet
        return json({ error: "payload too large" }, 413);
      const tk = await tasksRoute(req, env, u.pathname, isAdmin, ctx);
      if (tk) return tk;
      const acc = await accountRoute(req, env, u.pathname);
      if (acc) return acc;
      if (u.pathname === "/v1/drops" && req.method === "POST") return await postDrops(req, env);
      if (u.pathname === "/v1/summary" && req.method === "GET") return await summary(env);
      if (u.pathname === "/v1/stats" && req.method === "GET") return await stats(req, env);
      if (u.pathname === "/v1/reports" && req.method === "POST") return await postReport(req, env);
      if (u.pathname === "/v1/reports/status" && req.method === "GET") return await reportStatus(req, env);
      return json({ error: "not found" }, 404);
    } catch (e) {
      return json({ error: "server error" }, 500);
    }
  },
  async scheduled(_event, env) {                       // eski oran kayıtlarını sil (48 saatten eski)
    const hour = Math.floor(Date.now() / 3600000) - 48;
    await env.DB.prepare("DELETE FROM rate WHERE hour < ?1").bind(hour).run();
    const t = Math.floor(Date.now() / 1000);
    await env.DB.prepare("DELETE FROM auth_pending WHERE created < ?1").bind(t - 900).run();
    await env.DB.prepare("DELETE FROM sessions WHERE expires < ?1 OR (revoked = 1 AND last_seen < ?2)").bind(t, t - 7 * 86400).run();
    await flushQueue(env);                             // GitHub'a iletilemeyen raporlar
    try { await tasksCleanup(env); await snapshotToRepo(env, gh); } catch (e) { /* görev dökümü bir sonraki saate */ }
  },
};

