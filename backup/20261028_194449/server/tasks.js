// Topluluk görevleri: oyuncuların canlı çeviri sırasında gördüğü görev ekranları (Projeler, Ödül avları, Görevlendirmeler)
//
//   POST /v1/tasks          bir görev (İngilizce metin + programın Türkçe çevirisi)   herkese açık, gönüllü, oran sınırlı
//   GET  /v1/tasks/live     birleştirilmiş güncel görev listesi                         herkese açık (5 dk önbellek)
//   GET  /v1/admin/tasks    tüm görevler, çeşitleri ve gönderen sayıları                yönetici (Authorization: Admin …)
//   POST /v1/admin/tasks/hide      {key, hidden}       görevi listeden çıkar / geri al
//   POST /v1/admin/tasks/override  {key, tr|null}      Türkçe çeviriyi elle düzelt (null: kaldır)
//   POST /v1/suggest        çeviri satırı için daha iyi Türkçe önerisi                  herkese açık, oran sınırlı
//   GET  /v1/admin/suggestions?status=pending    öneriler (aynı öneriyi kaç oyuncu yaptı)  yönetici
//   POST /v1/admin/suggestions/decide  {id, approve, text?}   onayla (isteğe bağlı düzenleyerek) / reddet
//   Onaylanan satırlar /v1/tasks/live yanıtında "lines" olarak gelir → herkesin çeviri hafızası.
//
// Kurallar
//  - Görev kimliği sunucuda hesaplanır (başlık + hedef metni); istemcinin gönderdiği kimliğe güvenilmez.
//  - Bir görev herkese açık listeye ancak MIN_REPORTERS (varsayılan 2) farklı oyuncudan geldiyse girer; metnin en çok
//    gönderilen hâli seçilir. Türkçe çeviri de en az 2 oyuncudan aynı geldiyse (ya da yönetici düzelttiyse) yayınlanır.
//  - Yalnız oyunun görev yazısı alınır; oyuncu adı, ekran görüntüsü, IP saklanmaz. İstemci kimliği tuzlu SHA-256 özetidir.
//  - Tablolar ilk kullanımda kendiliğinden oluşturulur (ayrı bir veritabanı adımı gerekmez).

const CATS = new Set(["project", "bounty", "assignment", "other"]);
const PERIODS = new Set(["daily", "weekly", "season", "other"]);
const EN_FIELDS = { title: 80, subtitle: 80, desc: 420, objective: 220 };
const enc = new TextEncoder();
let READY = false;

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store",
                       "access-control-allow-origin": "*", ...extra } });
}

async function sha(text) {
  const d = await crypto.subtle.digest("SHA-256", enc.encode(text));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("");
}

export function norm(s) {
  return String(s || "").toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9' ]+/g, " ").replace(/\s+/g, " ").trim();
}

export async function taskKey(title, objective) {
  return (await sha("task|" + norm(title) + "|" + norm(objective))).slice(0, 16);
}

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
    `CREATE TABLE IF NOT EXISTS tr_lines (en_key TEXT PRIMARY KEY, en TEXT NOT NULL, tr TEXT NOT NULL, updated INTEGER NOT NULL)`,
  ];
  for (const q of ddl) await env.DB.prepare(q).run();
  READY = true;
}

// ------------------------------------------------------------ doğrulama
function cleanText(v, max, english) {
  if (typeof v !== "string") return "";
  let s = v.replace(/[\u0000-\u0009\u000b-\u001f\u007f]/g, "").replace(/[ \t]+/g, " ").trim();
  if (!s) return "";
  if (s.length > max) return null;
  if (/https?:|www\.|@|<|>|\{|\}/i.test(s)) return null;                      // bağlantı / etiket / e-posta yok
  if (english) {
    const letters = s.match(/\p{L}/gu) || [];
    if (letters.length < 3 || letters.filter(c => /[A-Za-z]/.test(c)).length / letters.length < 0.9) return null;
  }
  return s;
}

export function cleanTask(b) {
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
  const rewards = Array.isArray(t.rewards) ? t.rewards.slice(0, 8).map(r => cleanText(r, 60, true)) : [];
  if (rewards.some(r => r === null)) return null;
  if (rewards.length) en.rewards = rewards.filter(Boolean);
  const category = CATS.has(t.category) ? t.category : "other";
  const period = PERIODS.has(t.period) ? t.period : "other";
  const now = Math.floor(Date.now() / 1000);
  let expires_at = Number.isInteger(t.expires_at) ? t.expires_at : null;
  if (expires_at && (expires_at < now || expires_at > now + 100 * 86400)) expires_at = null;
  if (expires_at) expires_at = Math.round(expires_at / 3600) * 3600;           // aynı sıfırlama → aynı değer
  let tr = null;
  if (b.tr && typeof b.tr === "object") {
    tr = {};
    for (const [k, max] of Object.entries(EN_FIELDS)) {
      if (!en[k]) continue;
      const v = cleanText(b.tr[k], max * 2, false);
      if (v === null) { tr = null; break; }
      if (v) tr[k] = v;
    }
    if (tr && !tr.title && !tr.objective) tr = null;
  }
  const app = typeof b.app === "string" && /^\d+\.\d+\.\d+$/.test(b.app) ? b.app : null;
  return { en, tr, category, period, expires_at, app };
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

// ------------------------------------------------------------ gönderim
async function postTask(req, env) {
  let b;
  try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const c = cleanTask(b);
  if (!c) return json({ error: "invalid task" }, 400);
  const salt = env.HASH_SALT || "dev-salt";
  const rawClient = String(b.client || "").slice(0, 64);
  if (rawClient.length < 8) return json({ error: "invalid client" }, 400);
  const client = await sha(salt + "|task|" + rawClient);
  const ip = await sha(salt + "|ip|" + (req.headers.get("cf-connecting-ip") || ""));
  const maxC = parseInt(env.TASKS_PER_HOUR || "60", 10);
  if (!(await rateCheck(env, "tc:" + client, maxC, 1)) || !(await rateCheck(env, "ti:" + ip, maxC * 3, 1)))
    return json({ error: "rate limited" }, 429);
  await rateAdd(env, "tc:" + client); await rateAdd(env, "ti:" + ip);
  const key = await taskKey(c.en.title, c.en.objective);
  const enS = JSON.stringify(c.en), trS = c.tr ? JSON.stringify(c.tr) : null;
  const enH = (await sha(enS)).slice(0, 16), trH = trS ? (await sha(trS)).slice(0, 16) : null;
  const now = Math.floor(Date.now() / 1000);
  await env.DB.prepare(
    `INSERT INTO task_reports (key, client, created, updated, category, period, expires_at, en_hash, en, tr_hash, tr, app)
     VALUES (?1, ?2, ?3, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)
     ON CONFLICT(key, client) DO UPDATE SET updated = ?3, category = ?4, period = ?5, expires_at = ?6, en_hash = ?7, en = ?8,
       tr_hash = COALESCE(?9, tr_hash), tr = COALESCE(?10, tr), app = ?11`)
    .bind(key, client, now, c.category, c.period, c.expires_at, enH, enS, trH, trS, c.app).run();
  const n = await env.DB.prepare("SELECT COUNT(*) AS n FROM task_reports WHERE key = ?1").bind(key).first();
  return json({ ok: true, key, reporters: n ? n.n : 1 });
}

// ------------------------------------------------------------ çeviri önerileri
async function postSuggest(req, env) {
  let b;
  try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const en = cleanText(b.en, 420, true), nw = cleanText(b.new, 840, false), old = cleanText(b.old, 840, false);
  if (!en || !nw || en === null || nw === null || old === null || nw === old) return json({ error: "invalid suggestion" }, 400);
  const rawClient = String(b.client || "").slice(0, 64);
  if (rawClient.length < 8) return json({ error: "invalid client" }, 400);
  const salt = env.HASH_SALT || "dev-salt";
  const client = await sha(salt + "|task|" + rawClient);
  const ip = await sha(salt + "|ip|" + (req.headers.get("cf-connecting-ip") || ""));
  if (!(await rateCheck(env, "sc:" + client, 30, 24)) || !(await rateCheck(env, "si:" + ip, 90, 24))) return json({ error: "rate limited" }, 429);
  await rateAdd(env, "sc:" + client); await rateAdd(env, "si:" + ip);
  const en_key = (await sha("line|" + norm(en))).slice(0, 16);
  const app = typeof b.app === "string" && /^\d+\.\d+\.\d+$/.test(b.app) ? b.app : null;
  await env.DB.prepare(
    `INSERT INTO tr_suggest (en_key, en, old, new, new_hash, client, created, app) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
     ON CONFLICT(en_key, client) DO UPDATE SET new = ?4, new_hash = ?5, old = ?3, created = ?7, app = ?8, status = 'pending'`)
    .bind(en_key, en, old || null, nw, (await sha(norm(nw))).slice(0, 16), client, Math.floor(Date.now() / 1000), app).run();
  return json({ ok: true });
}

async function approvedLines(env) {
  return ((await env.DB.prepare("SELECT en, tr FROM tr_lines ORDER BY updated DESC LIMIT 2000").all()).results || []);
}

// ------------------------------------------------------------ birleştirme
async function topVariant(env, key, col, hashCol) {
  const r = await env.DB.prepare(
    `SELECT ${col} AS v, COUNT(*) AS c FROM task_reports WHERE key = ?1 AND ${hashCol} IS NOT NULL
     GROUP BY ${hashCol} ORDER BY c DESC, MAX(updated) DESC LIMIT 1`).bind(key).first();
  return r ? { v: JSON.parse(r.v), c: r.c } : null;
}

async function mostCommon(env, key, col) {
  const r = await env.DB.prepare(
    `SELECT ${col} AS v, COUNT(*) AS c FROM task_reports WHERE key = ?1 GROUP BY ${col} ORDER BY c DESC LIMIT 1`).bind(key).first();
  return r ? r.v : null;
}

export async function liveTasks(env, { includeHidden = false, minReporters = null, admin = false } = {}) {
  await ensure(env);
  const now = Math.floor(Date.now() / 1000);
  const minR = minReporters ?? parseInt(env.TASKS_MIN_REPORTERS || "2", 10);
  const days = parseInt(env.TASKS_KEEP_DAYS || "8", 10);
  const rows = (await env.DB.prepare(
    `SELECT r.key, COUNT(*) AS n, MIN(r.created) AS first_seen, MAX(r.updated) AS last_seen,
            a.hidden AS hidden, a.tr AS tr_override
     FROM task_reports r LEFT JOIN task_admin a ON a.key = r.key
     WHERE r.updated > ?1 GROUP BY r.key HAVING COUNT(*) >= ?2 ORDER BY last_seen DESC LIMIT 300`)
    .bind(now - (admin ? 60 : days) * 86400, minR).all()).results || [];
  const out = [];
  for (const r of rows) {
    if (r.hidden && !includeHidden) continue;
    const exp = await mostCommon(env, r.key, "expires_at");
    if (!admin && exp && exp < now) continue;                                   // süresi dolmuş görev
    const en = await topVariant(env, r.key, "en", "en_hash");
    if (!en) continue;
    const trv = await topVariant(env, r.key, "tr", "tr_hash");
    let tr = null, trSrc = null;
    if (r.tr_override) { tr = JSON.parse(r.tr_override); trSrc = "admin"; }
    else if (trv && trv.c >= Math.min(2, minR)) { tr = trv.v; trSrc = "community"; }
    const t = { key: r.key, category: await mostCommon(env, r.key, "category"), period: await mostCommon(env, r.key, "period"),
                ...en.v, expires_at: exp || null, first_seen: r.first_seen, last_seen: r.last_seen, reporters: r.n };
    if (tr) { t.tr = tr; t.tr_source = trSrc; }
    if (admin) {
      t.hidden = !!r.hidden;
      t.variants = {
        en: ((await env.DB.prepare("SELECT en AS v, COUNT(*) AS c FROM task_reports WHERE key = ?1 GROUP BY en_hash ORDER BY c DESC LIMIT 5")
          .bind(r.key).all()).results || []).map(x => ({ n: x.c, ...JSON.parse(x.v) })),
        tr: ((await env.DB.prepare("SELECT tr AS v, COUNT(*) AS c FROM task_reports WHERE key = ?1 AND tr IS NOT NULL GROUP BY tr_hash ORDER BY c DESC LIMIT 5")
          .bind(r.key).all()).results || []).map(x => ({ n: x.c, ...JSON.parse(x.v) })),
      };
      t.apps = ((await env.DB.prepare("SELECT app, COUNT(*) AS c FROM task_reports WHERE key = ?1 GROUP BY app").bind(r.key).all()).results || [])
        .map(x => `${x.app || "?"}×${x.c}`);
    }
    out.push(t);
  }
  const lines = await approvedLines(env);
  return { version: new Date(now * 1000).toISOString().slice(0, 16).replace(/[-:T]/g, "") + "." + lines.length, generated: now,
           min_reporters: parseInt(env.TASKS_MIN_REPORTERS || "2", 10), tasks: out, lines };   // herkese açık olma eşiği
}

// ------------------------------------------------------------ özel depoya günlük döküm (isteğe bağlı)
export async function snapshotToRepo(env, gh) {
  if (!env.GITHUB_TOKEN || !env.REPORTS_REPO) return "no-token";
  await ensure(env);
  const day = new Date().toISOString().slice(0, 10);
  const last = await env.DB.prepare("SELECT v FROM task_state WHERE k = 'snapshot_day'").first();
  if (last && last.v === day) return "done-today";
  const data = await liveTasks(env, { includeHidden: true, minReporters: 1, admin: true });
  const body = JSON.stringify(data, null, 1);
  const path = `tasks/${day}.json`;
  try {
    await gh(env, `/repos/${env.REPORTS_REPO}/contents/${path}`, { method: "PUT", body: JSON.stringify({
      message: `Görev dökümü ${day} (${data.tasks.length} görev)`,
      content: btoa(String.fromCharCode(...enc.encode(body))) }) });
  } catch (e) {
    return "github-failed";                       // belirtecin içerik izni yoksa: döküm atlanır, yönetici uçları yine çalışır
  }
  await env.DB.prepare("INSERT INTO task_state (k, v) VALUES ('snapshot_day', ?1) ON CONFLICT(k) DO UPDATE SET v = ?1").bind(day).run();
  return "ok";
}

export async function cleanup(env) {
  await ensure(env);
  const now = Math.floor(Date.now() / 1000);
  await env.DB.prepare("DELETE FROM task_reports WHERE updated < ?1").bind(now - 90 * 86400).run();
}

// ------------------------------------------------------------ yönlendirme
export async function route(req, env, path, isAdmin, ctx) {
  if (path === "/v1/tasks" && req.method === "POST") { await ensure(env); return await postTask(req, env); }
  if (path === "/v1/suggest" && req.method === "POST") { await ensure(env); return await postSuggest(req, env); }
  if (path.startsWith("/v1/admin/suggestions")) {
    if (!(await isAdmin(req, env))) return json({ error: "forbidden" }, 403);
    await ensure(env);
    if (path === "/v1/admin/suggestions" && req.method === "GET") {
      const st = new URL(req.url).searchParams.get("status") || "pending";
      const rows = (await env.DB.prepare(
        `SELECT MIN(s.id) AS id, s.en_key, s.en, s.old, s.new, COUNT(*) AS n, MAX(s.created) AS last, s.status, l.tr AS current
         FROM tr_suggest s LEFT JOIN tr_lines l ON l.en_key = s.en_key WHERE s.status = ?1
         GROUP BY s.en_key, s.new_hash ORDER BY n DESC, last DESC LIMIT 300`).bind(st).all()).results || [];
      return json({ suggestions: rows });
    }
    if (path === "/v1/admin/suggestions/decide" && req.method === "POST") {
      const b = await req.json().catch(() => ({}));
      const row = Number.isInteger(b.id) ? await env.DB.prepare("SELECT * FROM tr_suggest WHERE id = ?1").bind(b.id).first() : null;
      if (!row) return json({ error: "not found" }, 404);
      const now = Math.floor(Date.now() / 1000);
      if (b.approve) {
        const text = b.text === undefined ? row.new : cleanText(b.text, 840, false);
        if (!text) return json({ error: "bad text" }, 400);
        await env.DB.prepare("INSERT INTO tr_lines (en_key, en, tr, updated) VALUES (?1, ?2, ?3, ?4) ON CONFLICT(en_key) DO UPDATE SET tr = ?3, updated = ?4")
          .bind(row.en_key, row.en, text, now).run();
        await env.DB.prepare("UPDATE tr_suggest SET status = CASE WHEN new_hash = ?2 THEN 'approved' ELSE 'rejected' END WHERE en_key = ?1 AND status = 'pending'")
          .bind(row.en_key, row.new_hash).run();
      } else {
        await env.DB.prepare("UPDATE tr_suggest SET status = 'rejected' WHERE en_key = ?1 AND new_hash = ?2").bind(row.en_key, row.new_hash).run();
      }
      return json({ ok: true });
    }
    if (path === "/v1/admin/suggestions/line" && req.method === "POST") {         // onaylı satırı kaldır
      const b = await req.json().catch(() => ({}));
      if (typeof b.en_key !== "string") return json({ error: "bad key" }, 400);
      await env.DB.prepare("DELETE FROM tr_lines WHERE en_key = ?1").bind(b.en_key).run();
      return json({ ok: true });
    }
    return json({ error: "not found" }, 404);
  }
  if (path === "/v1/tasks/live" && req.method === "GET") {
    const cache = typeof caches !== "undefined" ? caches.default : null;
    const ck = new Request(new URL(req.url).origin + "/v1/tasks/live");
    if (cache) { const hit = await cache.match(ck); if (hit) return hit; }
    const res = json(await liveTasks(env), 200, { "cache-control": "public, max-age=300" });
    if (cache && ctx) ctx.waitUntil(cache.put(ck, res.clone()));
    return res;
  }
  if (path.startsWith("/v1/admin/tasks")) {
    if (!(await isAdmin(req, env))) return json({ error: "forbidden" }, 403);
    await ensure(env);
    if (path === "/v1/admin/tasks" && req.method === "GET") {
      return json(await liveTasks(env, { includeHidden: true, minReporters: 1, admin: true }));
    }
    const b = req.method === "POST" ? await req.json().catch(() => ({})) : {};
    const key = typeof b.key === "string" && /^[0-9a-f]{16}$/.test(b.key) ? b.key : null;
    if (!key) return json({ error: "bad key" }, 400);
    const now = Math.floor(Date.now() / 1000);
    if (path === "/v1/admin/tasks/hide" && req.method === "POST") {
      await env.DB.prepare("INSERT INTO task_admin (key, hidden, updated) VALUES (?1, ?2, ?3) ON CONFLICT(key) DO UPDATE SET hidden = ?2, updated = ?3")
        .bind(key, b.hidden === false ? 0 : 1, now).run();
      return json({ ok: true });
    }
    if (path === "/v1/admin/tasks/override" && req.method === "POST") {
      let tr = null;
      if (b.tr && typeof b.tr === "object") {
        tr = {};
        for (const [k, max] of Object.entries(EN_FIELDS)) {
          const v = cleanText(b.tr[k], max * 2, false);
          if (v === null) return json({ error: "bad tr" }, 400);
          if (v) tr[k] = v;
        }
      }
      await env.DB.prepare("INSERT INTO task_admin (key, tr, updated) VALUES (?1, ?2, ?3) ON CONFLICT(key) DO UPDATE SET tr = ?2, updated = ?3")
        .bind(key, tr ? JSON.stringify(tr) : null, now).run();
      return json({ ok: true });
    }
    return json({ error: "not found" }, 404);
  }
  return null;
}
