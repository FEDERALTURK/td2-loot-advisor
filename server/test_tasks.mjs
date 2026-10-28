// Topluluk görevleri testi: D1 → node:sqlite, GitHub → sahte fetch.   node server/test_tasks.mjs
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import worker from "./worker.js";

const sql = new DatabaseSync(":memory:");
sql.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
const stmt = q => { let a = []; const s = {
  bind(...x) { a = x; return s; },
  async run() { return sql.prepare(q).run(...a); },
  async first() { return sql.prepare(q).get(...a) ?? null; },
  async all() { return { results: sql.prepare(q).all(...a) }; } }; return s; };
const ADMIN = "admin-token-0123456789abcdef-xyz";
const puts = [];
globalThis.fetch = async (url, opts = {}) => {
  if (opts.method === "PUT" && url.includes("/contents/tasks/")) { puts.push([url, JSON.parse(opts.body)]); return Response.json({ ok: 1 }, { status: 201 }); }
  return new Response("nf", { status: 404 });
};
const env = { DB: { prepare: stmt }, HASH_SALT: "t", ADMIN_TOKEN: ADMIN, GITHUB_TOKEN: "x", REPORTS_REPO: "o/r" };

let fails = 0;
const ok = (c, m) => { console.log((c ? "OK   " : "FAIL ") + m); if (!c) fails++; };
async function call(method, path, body, headers = {}, ip = "1.1.1.1") {
  const r = await worker.fetch(new Request("http://x" + path, { method, headers: { "content-type": "application/json", "cf-connecting-ip": ip, ...headers },
    body: body ? JSON.stringify(body) : undefined }), env, { waitUntil() {} });
  return [r.status, await r.json().catch(() => null)];
}

const now = Math.floor(Date.now() / 1000);
const task = {
  title: "Weekly Legendary Mission", subtitle: "Legendary Roosevelt Island",
  desc: "We've got a special item for any agent who can defeat the special forces who have moved into Roosevelt Island.",
  objective: "Complete the Roosevelt Island mission on Legendary difficulty", total: 1,
  rewards: ["Exotic Cache", "Recalibration Cache", "Gear Crafting Cache"], category: "project", period: "weekly",
  expires_at: now + 3 * 86400 + 1234 };
const tr = { title: "Haftalık Legendary Görevi", subtitle: "Legendary Roosevelt Adası",
  desc: "Roosevelt Adası'na taşınan özel kuvvetleri yenebilecek her ajan için özel bir eşyamız var.",
  objective: "Legendary zorlukta Roosevelt Adası görevini tamamlayın" };

let [st, j] = await call("POST", "/v1/tasks", { client: "player-A-1234", app: "5.1.8", task, tr });
ok(st === 200 && j.ok && /^[0-9a-f]{16}$/.test(j.key) && j.reporters === 1, "ilk gönderim kabul");
const key = j.key;
[st, j] = await call("GET", "/v1/tasks/live");
ok(st === 200 && j.tasks.length === 0, "tek oyuncunun görevi listede değil (eşik 2)");
[st, j] = await call("POST", "/v1/tasks", { client: "player-A-1234", app: "5.1.8", task, tr });
ok(j.reporters === 1, "aynı oyuncu ikinci kez sayılmaz");
[st, j] = await call("POST", "/v1/tasks", { client: "player-B-5678", app: "5.1.8", task: { ...task, expires_at: now + 3 * 86400 + 900 }, tr }, {}, "2.2.2.2");
ok(j.reporters === 2 && j.key === key, "ikinci oyuncu (sunucu aynı kimliği hesapladı)");
[st, j] = await call("GET", "/v1/tasks/live");
const t = j.tasks[0];
ok(j.tasks.length === 1 && t.reporters === 2 && t.title === task.title && t.rewards.length === 3, "iki oyuncudan sonra listede");
ok(t.tr && t.tr.objective === tr.objective && t.tr_source === "community", "Türkçe çeviri (2 oyuncudan aynı) yayınlandı");
ok(t.expires_at && t.expires_at % 3600 === 0, "bitiş saati saate yuvarlandı (aynı sıfırlama)");
ok(!JSON.stringify(j).includes("player-") && !("client" in t), "gönderen kimliği listede yok");

// zehirleme: üçüncü oyuncu farklı çeviri yollar → en çok gönderilen kalır; tek kişilik çeviri yayınlanmaz
await call("POST", "/v1/tasks", { client: "player-C-9999", task, tr: { ...tr, objective: "SAHTE METİN" } }, {}, "3.3.3.3");
[st, j] = await call("GET", "/v1/tasks/live");
ok(j.tasks[0].tr.objective === tr.objective && j.tasks[0].reporters === 3, "tek kişinin farklı çevirisi yayına girmedi");

// tek oyunculu başka görev + çeviri tek kişiden → görev yok
await call("POST", "/v1/tasks", { client: "player-A-1234", task: { ...task, title: "Daily Project", objective: "Kill 50 Black Tusk enemies", period: "daily" }, tr });
[st, j] = await call("GET", "/v1/tasks/live");
ok(j.tasks.length === 1, "tek kişinin gönderdiği görev herkese açık değil");

// kötü veriler
for (const [bad, name] of [
  [{ client: "player-Z-0000", task: { ...task, title: "" } }, "başlıksız"],
  [{ client: "player-Z-0000", task: { ...task, desc: "x".repeat(500) } }, "çok uzun"],
  [{ client: "player-Z-0000", task: { ...task, objective: "visit https://evil.example now" } }, "bağlantı"],
  [{ client: "player-Z-0000", task: { ...task, title: "Здравствуйте друзья" } }, "İngilizce olmayan başlık"],
  [{ client: "x", task }, "kısa istemci kimliği"],
  [{ client: "player-Z-0000", task: { ...task, rewards: ["<script>"] } }, "etiketli ödül"],
]) { [st] = await call("POST", "/v1/tasks", bad); ok(st === 400, "reddedildi: " + name); }

// oran sınırı
let limited = false;
for (let i = 0; i < 70; i++) {
  [st] = await call("POST", "/v1/tasks", { client: "spammer-0000", task: { ...task, title: "Spam " + "abcdefghij"[i % 10] + i } }, {}, "9.9.9.9");
  if (st === 429) { limited = true; break; }
}
ok(limited, "saatlik sınır (60)");

// yönetici
[st] = await call("GET", "/v1/admin/tasks");
ok(st === 403, "yönetici belirteci olmadan 403");
[st, j] = await call("GET", "/v1/admin/tasks", null, { authorization: "Admin " + ADMIN });
const at = j.tasks.find(x => x.key === key);
ok(st === 200 && j.tasks.length >= 2 && at.variants.tr.length === 2 && at.variants.tr[0].n === 2, "yönetici: tüm görevler ve çeşitleri");
ok(j.min_reporters === 2, "yönetici listesi herkese açık eşiğini bildiriyor (2)");
[st] = await call("POST", "/v1/admin/tasks/override", { key, tr: { ...tr, title: "Haftalık Efsanevi Görev" } }, { authorization: "Admin " + ADMIN });
[st, j] = await call("GET", "/v1/tasks/live");
ok(j.tasks[0].tr.title === "Haftalık Efsanevi Görev" && j.tasks[0].tr_source === "admin", "yönetici çeviriyi düzeltti");
await call("POST", "/v1/admin/tasks/hide", { key }, { authorization: "Admin " + ADMIN });
[st, j] = await call("GET", "/v1/tasks/live");
ok(j.tasks.length === 0, "yönetici gizledi");
await call("POST", "/v1/admin/tasks/hide", { key, hidden: false }, { authorization: "Admin " + ADMIN });
[st, j] = await call("GET", "/v1/tasks/live");
ok(j.tasks.length === 1, "geri açıldı");

// süresi dolmuş görev
sql.prepare("UPDATE task_reports SET expires_at = ?1 WHERE key = ?2").run(now - 3600, key);
[st, j] = await call("GET", "/v1/tasks/live");
ok(j.tasks.length === 0, "süresi dolan görev listeden düştü");

// günlük döküm (özel depo)
await worker.scheduled({}, env);
ok(puts.length === 1 && puts[0][0].includes("/repos/o/r/contents/tasks/") && JSON.parse(Buffer.from(puts[0][1].content, "base64").toString()).tasks.length >= 2, "özel depoya günlük döküm");
await worker.scheduled({}, env);
ok(puts.length === 1, "aynı gün ikinci döküm yok");

// --- çeviri önerileri
const line = "Head to the White House and talk to Manny.";
for (const [who, ip, txt] of [["sug-aaaa-1111", "5.5.5.1", "White House'a git ve Manny ile konuş."], ["sug-bbbb-2222", "5.5.5.2", "White House'a git ve Manny ile konuş."],
                               ["sug-cccc-3333", "5.5.5.3", "Beyaz Saray'a git."]]) {
  [st] = await call("POST", "/v1/suggest", { client: who, en: line, old: "Beyaz Saray'a gidin ve Manny ile konuşun.", new: txt, app: "5.1.9" }, {}, ip);
  ok(st === 200, "öneri alındı: " + who);
}
[st] = await call("POST", "/v1/suggest", { client: "sug-dddd-4444", en: line, old: "x", new: "x" }, {}, "5.5.5.4");
ok(st === 400, "aynı metin öneri sayılmaz");
[st] = await call("POST", "/v1/suggest", { client: "sug-eeee-5555", en: "Привет", old: "a", new: "b" }, {}, "5.5.5.5");
ok(st === 400, "İngilizce olmayan satır reddedildi");
[st] = await call("GET", "/v1/admin/suggestions");
ok(st === 403, "öneriler yalnız yönetici");
[st, j] = await call("GET", "/v1/admin/suggestions", null, { authorization: "Admin " + ADMIN });
ok(j.suggestions.length === 2 && j.suggestions[0].n === 2 && j.suggestions[0].new.startsWith("White House'a git"), "aynı öneri gruplanıp sayıldı (2 oyuncu)");
[st, j] = await call("GET", "/v1/tasks/live");
ok(Array.isArray(j.lines) && j.lines.length === 0, "onaysız öneri herkese gitmez");
const top = (await call("GET", "/v1/admin/suggestions", null, { authorization: "Admin " + ADMIN }))[1].suggestions[0];
[st] = await call("POST", "/v1/admin/suggestions/decide", { id: top.id, approve: true }, { authorization: "Admin " + ADMIN });
[st, j] = await call("GET", "/v1/tasks/live");
ok(j.lines.length === 1 && j.lines[0].tr === "White House'a git ve Manny ile konuş." && j.lines[0].en === line, "onaylanan öneri herkesin listesinde");
[st, j] = await call("GET", "/v1/admin/suggestions", null, { authorization: "Admin " + ADMIN });
ok(j.suggestions.length === 0, "aynı satırın diğer önerileri kapandı");
[st, j] = await call("GET", "/v1/admin/suggestions?status=rejected", null, { authorization: "Admin " + ADMIN });
ok(j.suggestions.length === 1 && j.suggestions[0].new === "Beyaz Saray'a git.", "diğer öneri reddedildi olarak duruyor");
await call("POST", "/v1/admin/suggestions/line", { en_key: top.en_key }, { authorization: "Admin " + ADMIN });
[st, j] = await call("GET", "/v1/tasks/live");
ok(j.lines.length === 0, "onaylı satır kaldırılabildi");

console.log("RESULT:", fails ? `FAIL (${fails})` : "PASS");
process.exit(fails ? 1 : 0);
