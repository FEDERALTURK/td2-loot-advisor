// Kimliksiz kullanım sayacı ve Rapor Paneli için yönetici özeti.
//
// Kullanım sayacı: program /v1/tasks/live adresini açılışta ve 30 dakikada bir okur. Program kendi sürümünü
// User-Agent'ta bildirir ("TD2LootAdvisor/6.0.1"), açılıştaki ilk istekte ayrıca "x-td2-run: start" gönderir.
// Sunucu YALNIZ günlük sayaç tutar: (gün, sürüm) -> açılış sayısı, yoklama sayısı. IP, hesap, cihaz ya da herhangi bir
// kimlik saklanmaz; tek tek kullanıcılar ayırt edilemez. Sayaçlar 400 gün sonra silinir.
//
// GET /v1/admin/overview[?since=<unix>]  (Admin belirteci)
//   Gösterge sekmesinin tek çağrısı: sürüm dağılımı, günlük açılışlar, hesap/lisans sayıları, bekleyen öneriler,
//   görev durumu, kuyruktaki raporlar, son zamanlanmış çalışma ve "since" sonrası olaylar (bildirimler için).

const VERSION_RE = /^TD2LootAdvisor\/(\d{1,2}\.\d{1,2}\.\d{1,3})(?:\s|$)/;
let READY = false;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}
const now = () => Math.floor(Date.now() / 1000);
const dayOf = t => new Date(t * 1000).toISOString().slice(0, 10);

async function ensure(env) {
  if (READY) return;
  await env.DB.prepare(`CREATE TABLE IF NOT EXISTS usage_daily (day TEXT NOT NULL, version TEXT NOT NULL,
    starts INTEGER NOT NULL DEFAULT 0, polls INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, version))`).run();
  await env.DB.prepare(`CREATE TABLE IF NOT EXISTS task_state (k TEXT PRIMARY KEY, v TEXT)`).run();
  READY = true;
}

export function parseVersion(ua) {
  const m = VERSION_RE.exec(String(ua || ""));
  return m ? m[1] : null;
}

/** /v1/tasks/live isteklerinde çağrılır (önbellekten dönse bile). Hata yanıtı etkilemez. */
export async function countUsage(req, env) {
  const v = parseVersion(req.headers.get("user-agent"));
  if (!v) return;
  const start = (req.headers.get("x-td2-run") || "") === "start" ? 1 : 0;
  try {
    await ensure(env);
    await env.DB.prepare(`INSERT INTO usage_daily (day, version, starts, polls) VALUES (?1, ?2, ?3, 1)
      ON CONFLICT(day, version) DO UPDATE SET starts = starts + ?3, polls = polls + 1`).bind(dayOf(now()), v, start).run();
  } catch (e) { /* sayaç isteğe bağlı */ }
}

export async function markCron(env) {
  try {
    await ensure(env);
    await env.DB.prepare("INSERT INTO task_state (k, v) VALUES ('cron_last', ?1) ON CONFLICT(k) DO UPDATE SET v = ?1").bind(String(now())).run();
    await env.DB.prepare("DELETE FROM usage_daily WHERE day < ?1").bind(dayOf(now() - 400 * 86400)).run();
  } catch (e) { /* bir sonraki saat */ }
}

async function safeAll(env, sql, ...args) {
  try { return (await env.DB.prepare(sql).bind(...args).all()).results || []; } catch (e) { return []; }
}
async function safeN(env, sql, ...args) {
  try { const r = await env.DB.prepare(sql).bind(...args).first(); return r ? (r.n ?? 0) : 0; } catch (e) { return null; }
}

export async function overview(req, env) {
  await ensure(env);
  const t = now();
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
    if (r.hidden) tasks.hidden++; else if (r.n >= minR) tasks.public++; else tasks.waiting++;
  }

  const cron = await env.DB.prepare("SELECT v FROM task_state WHERE k = 'cron_last'").first().catch(() => null);
  const events = {
    suggestions: await safeN(env, "SELECT COUNT(*) AS n FROM tr_suggest WHERE created > ?1", since),
    task_reports: await safeN(env, "SELECT COUNT(*) AS n FROM task_reports WHERE created > ?1", since),
    accounts: await safeN(env, "SELECT COUNT(*) AS n FROM accounts WHERE created > ?1", since),
    redeems: await safeN(env, "SELECT COUNT(*) AS n FROM audit WHERE action = 'redeem' AND t > ?1", since),
    reports: await safeN(env, "SELECT COUNT(*) AS n FROM reports WHERE created > ?1", since),
  };
  return json({
    now: t, since,
    usage: { versions_7d: versions7, daily_30d: daily,
             starts_today: daily.length && daily[daily.length - 1].day === dayOf(t) ? daily[daily.length - 1].starts : 0 },
    accounts: {
      total: await safeN(env, "SELECT COUNT(*) AS n FROM accounts WHERE ?1 > 0", t),
      logins_7d: await safeN(env, "SELECT COUNT(*) AS n FROM accounts WHERE last_login > ?1", t - 7 * 86400),
      active_licenses: await safeN(env, "SELECT COUNT(*) AS n FROM licenses WHERE revoked = 0 AND account_id IS NOT NULL AND (expires IS NULL OR expires > ?1)", t),
      expiring_14d: await safeN(env, "SELECT COUNT(*) AS n FROM licenses WHERE revoked = 0 AND account_id IS NOT NULL AND expires IS NOT NULL AND expires > ?1 AND expires < ?2", t, t + 14 * 86400),
      unused_keys: await safeN(env, "SELECT COUNT(*) AS n FROM licenses WHERE account_id IS NULL AND revoked = 0 AND ?1 > 0", t),
    },
    suggestions_pending: await safeN(env, "SELECT COUNT(*) AS n FROM (SELECT 1 FROM tr_suggest WHERE status = 'pending' AND ?1 > 0 GROUP BY en_key, new_hash)", t),
    lines_approved: await safeN(env, "SELECT COUNT(*) AS n FROM tr_lines WHERE ?1 > 0", t),
    tasks,
    reports_queued: await safeN(env, "SELECT COUNT(*) AS n FROM reports WHERE state = 'queued' AND ?1 > 0", t),
    cron_last: cron && cron.v ? parseInt(cron.v, 10) : null,
    events,
  });
}

export async function route(req, env, path, isAdmin) {
  if (path === "/v1/admin/overview" && req.method === "GET") {
    if (!(await isAdmin(req, env))) return json({ error: "forbidden" }, 403);
    return overview(req, env);
  }
  return null;
}
