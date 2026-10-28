// Rapor uç noktalarının testi: D1 → node:sqlite, GitHub → sahte fetch.   node server/test_reports.mjs
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import worker from "./worker.js";

const sql = new DatabaseSync(":memory:");
sql.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
function stmt(q) {
  let args = [];
  const s = {
    bind(...a) { args = a; return s; },
    async run() { return sql.prepare(q).run(...args); },
    async first() { return sql.prepare(q).get(...args) ?? null; },
    async all() { return { results: sql.prepare(q).all(...args) }; },
  };
  return s;
}
const DB = { prepare: stmt, async batch(list) { return Promise.all(list.map(x => x.run())); } };

// --- sahte GitHub
const issues = new Map(); let next = 1; let ghDown = false; const calls = [];
globalThis.fetch = async (url, opts = {}) => {
  calls.push([opts.method || "GET", url]);
  if (ghDown) return new Response("down", { status: 503 });
  const u = new URL(url); const m = u.pathname.match(/^\/repos\/([^/]+\/[^/]+)\/issues(?:\/(\d+))?(\/comments)?$/);
  if (!m) return new Response("nf", { status: 404 });
  if (!m[2] && opts.method === "POST") {
    const b = JSON.parse(opts.body); const n = next++;
    issues.set(n, { number: n, state: "open", title: b.title, body: b.body, labels: b.labels.map(name => ({ name })), comments: 0, updated_at: "now", _c: [] });
    return Response.json(issues.get(n), { status: 201 });
  }
  const it = issues.get(+m[2]);
  if (!it) return new Response("nf", { status: 404 });
  if (m[3]) return Response.json(it._c);
  return Response.json(it);
};

const env = { DB, HASH_SALT: "test", GITHUB_TOKEN: "ghp_test", REPORTS_REPO: "o/reports", ADMIN_LOGIN: "admin",
              GITHUB_API: "https://gh.test" };
const post = (b, ip = "1.2.3.4") => worker.fetch(new Request("https://w/v1/reports", { method: "POST", body: JSON.stringify(b),
                                                    headers: { "cf-connecting-ip": ip } }), env);
let fails = 0;
const ok = (c, msg) => { console.log((c ? "OK   " : "FAIL ") + msg); if (!c) fails++; };

const good = { client: "abc123", type: "bug", title: "Kart okunmuyor", app_version: "5.0.6", lang: "tr",
  body: "Striker dizliği eldiven görünüyor. C:\\Users\\Soner\\AppData\\x.log, mail: a@b.com, lisans TD2P-AAAA.BBBB",
  contact: "soner#1234", system: { os: "Windows 11", res: "3440x1440", evil_KEY: "x" },
  log: "File \"C:\\Users\\Soner\\Desktop\\app.py\", token ghp_abcdefghijklmnopqrstuvwxyz123456", card: "Striker's Kneepads" };

let r = await post(good); let j = await r.json();
ok(r.status === 200 && j.number === 1, "rapor GitHub issue olarak açıldı (#" + j.number + ")");
const iss = issues.get(1);
ok(iss.title === "[Hata] Kart okunmuyor", "başlık: " + iss.title);
ok(iss.labels.map(l => l.name).join(",") === "report,type:bug,status:new,v5.0.6,lang:tr", "etiketler: " + iss.labels.map(l => l.name));
ok(!/Soner|a@b\.com|AAAA|ghp_abc/.test(iss.body), "kişisel veriler temizlendi");
ok(iss.body.includes("C:\\Users\\<user>") && iss.body.includes("<email>") && iss.body.includes("TD2P-<license>") && iss.body.includes("<token>"), "yer tutucular yazıldı");
ok(iss.body.includes("<!-- td2-report ") && !iss.body.includes("evil_KEY"), "panel için meta veri; geçersiz alan atıldı");

r = await post({ ...good, type: "hack" }); ok(r.status === 400, "geçersiz tür reddedildi");
r = await post({ ...good, title: "x" }); ok(r.status === 400, "çok kısa başlık reddedildi");

// hız sınırı: aynı istemci saatte 5
for (let i = 0; i < 4; i++) await post({ ...good, title: "Rapor " + i }, "9.9.9." + i);
r = await post({ ...good, title: "Altıncı" }, "8.8.8.8"); ok(r.status === 429, "istemci başına saatlik sınır (6. rapor 429)");

// GitHub kapalı: kuyruk, sonra saatlik görev iletir
ghDown = true;
r = await post({ ...good, client: "other", title: "Kuyruk testi" }, "7.7.7.7"); j = await r.json();
ok(j.ok && j.queued && j.number === null, "GitHub ulaşılamaz: rapor kuyruğa alındı (id " + j.id + ")");
ghDown = false;
await worker.scheduled({}, env);
const row = sql.prepare("SELECT state, number FROM reports WHERE id = ?").get(j.id);
ok(row.state === "sent" && row.number > 0, "saatlik görev kuyruktakini iletti (#" + row.number + ")");

// durum sorgusu: yalnız kendi raporu; yönetici yanıtı
issues.get(1).labels.push({ name: "status:in-progress" }); issues.get(1).labels = issues.get(1).labels.filter(l => l.name !== "status:new");
issues.get(1).comments = 2; issues.get(1)._c = [{ user: { login: "someone" }, body: "+1" }, { user: { login: "admin" }, body: "5.0.7'de düzeldi" }];
r = await worker.fetch(new Request("https://w/v1/reports/status?client=abc123&ids=1"), env); j = await r.json();
ok(j.reports.length === 1 && j.reports[0].status === "in-progress" && j.reports[0].reply === "5.0.7'de düzeldi", "durum + yönetici yanıtı: " + JSON.stringify(j.reports[0]));
r = await worker.fetch(new Request("https://w/v1/reports/status?client=baskasi&ids=1"), env); j = await r.json();
ok(j.reports.length === 0, "başkasının raporu görünmez");

console.log(fails ? `RESULT: FAIL (${fails})` : "RESULT: PASS");
process.exit(fails ? 1 : 0);
