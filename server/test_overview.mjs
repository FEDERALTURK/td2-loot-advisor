// Kullanım sayacı ve yönetici özeti testi.   node server/test_overview.mjs
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import worker from "./worker.js";
import { parseVersion } from "./overview.js";

const sql = new DatabaseSync(":memory:");
sql.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
const stmt = q => { let a = []; const s = {
  bind(...x) { a = x; return s; },
  async run() { return sql.prepare(q).run(...a); },
  async first() { return sql.prepare(q).get(...a) ?? null; },
  async all() { return { results: sql.prepare(q).all(...a) }; } }; return s; };
const ADMIN = "admin-token-0123456789abcdef-xyz";
globalThis.fetch = async () => new Response("nf", { status: 404 });
const env = { DB: { prepare: stmt }, HASH_SALT: "t", ADMIN_TOKEN: ADMIN };

let fails = 0;
const ok = (c, m) => { console.log((c ? "OK   " : "FAIL ") + m); if (!c) fails++; };
const waits = [];
async function call(method, path, headers = {}, body) {
  const r = await worker.fetch(new Request("http://x" + path, { method, headers: { "content-type": "application/json", "cf-connecting-ip": "1.1.1.1", ...headers },
    body: body ? JSON.stringify(body) : undefined }), env, { waitUntil(p) { waits.push(p); } });
  await Promise.all(waits.splice(0));
  return [r.status, await r.json().catch(() => null)];
}

ok(parseVersion("TD2LootAdvisor/6.0.1") === "6.0.1", "sürüm okunur");
ok(parseVersion("TD2LootAdvisor") === null && parseVersion("TD2LootAdvisor/6.0.1; DROP TABLE") === null
   && parseVersion("Mozilla/5.0") === null && parseVersion("TD2LootAdvisor/1.2.3.4") === null, "geçersiz / eski UA sayılmaz");

for (let i = 0; i < 3; i++) await call("GET", "/v1/tasks/live", { "user-agent": "TD2LootAdvisor/6.0.1", "x-td2-run": "start" });
for (let i = 0; i < 5; i++) await call("GET", "/v1/tasks/live", { "user-agent": "TD2LootAdvisor/6.0.1" });
await call("GET", "/v1/tasks/live", { "user-agent": "TD2LootAdvisor/6.0.2", "x-td2-run": "start" });
await call("GET", "/v1/tasks/live", { "user-agent": "TD2LootAdvisor" });                 // eski sürüm: sayılmaz
const rows = sql.prepare("SELECT * FROM usage_daily ORDER BY version").all();
ok(rows.length === 2 && rows[0].starts === 3 && rows[0].polls === 8 && rows[1].starts === 1, "günlük sayaç: " + JSON.stringify(rows));
ok(Object.keys(rows[0]).sort().join() === "day,polls,starts,version", "yalnız gün/sürüm/sayı saklanır (kimlik yok)");

let [st, j] = await call("GET", "/v1/admin/overview");
ok(st === 403, "belirteçsiz özet reddedilir");
[st, j] = await call("GET", "/v1/admin/overview", { authorization: "Admin yanlis-belirtec-0123456789abcdef" });
ok(st === 403, "yanlış belirteç reddedilir");

// biraz veri
const t = Math.floor(Date.now() / 1000);
sql.prepare("INSERT INTO accounts (discord_id, username, created, last_login) VALUES ('1','a',?,?)").run(t - 100, t - 100);
sql.prepare("INSERT INTO audit (t, actor, action, detail) VALUES (?, 'acc:1', 'redeem', '{}')").run(t - 50);
sql.prepare("INSERT INTO reports (created, client, payload, state) VALUES (?, 'c', '{}', 'queued')").run(t - 10);
await call("POST", "/v1/suggest", {}, { client: "player-A-1234", app: "6.0.1", en: "Head to the safe house.", old: "x", new: "Güvenli eve git." });

[st, j] = await call("GET", "/v1/admin/overview?since=" + (t - 3600), { authorization: "Admin " + ADMIN });
ok(st === 200, "özet döner");
ok(j.usage.versions_7d[0].version === "6.0.1" && j.usage.versions_7d[0].starts === 3, "sürüm dağılımı");
ok(j.usage.starts_today === 4 && j.usage.daily_30d.length === 1, "günlük açılış");
ok(j.accounts.total === 1 && j.events.accounts === 1 && j.events.redeems === 1 && j.events.reports === 1, "hesap ve olaylar: " + JSON.stringify(j.events));
ok(j.reports_queued === 1 && j.tasks && typeof j.tasks.public === "number", "rapor kuyruğu ve görev durumu");
ok(j.events.suggestions === 1 && j.suggestions_pending === 1, "öneri sayıları");
await worker.scheduled({}, env);
[st, j] = await call("GET", "/v1/admin/overview", { authorization: "Admin " + ADMIN });
ok(j.cron_last && Math.abs(j.cron_last - t) < 60, "zamanlanmış çalışma kaydı");

console.log("RESULT:", fails ? `FAIL (${fails})` : "PASS");
process.exit(fails ? 1 : 0);
