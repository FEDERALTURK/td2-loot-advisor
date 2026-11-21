// Signed Discord interaction endpoint tests. No Discord network calls are made.
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { generateKeyPairSync, sign, randomBytes } from "node:crypto";
import worker from "./worker.js";

const sql = new DatabaseSync(":memory:");
sql.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
sql.exec(readFileSync(new URL("./migrations/0001_discord_interactions.sql", import.meta.url), "utf8"));
function statement(query) {
  let args = [];
  const current = {
    bind(...values) { args = values; return current; },
    async run() { const result = sql.prepare(query).run(...args); return { meta: { changes: Number(result.changes) } }; },
    async first() { return sql.prepare(query).get(...args) ?? null; },
    async all() { return { results: sql.prepare(query).all(...args) }; },
  };
  return current;
}
const DB = { prepare: statement };
const pair = generateKeyPairSync("ed25519");
const publicRaw = pair.publicKey.export({ type: "spki", format: "der" }).subarray(-32).toString("hex");
const env = { DB, DISCORD_PUBLIC_KEY: publicRaw, DISCORD_CLIENT_ID: "111111111111", TD2_APP_VERSION: "9.1.5-test",
  PUBLIC_URL: "https://worker.test", DISCORD_FETCH: async () => new Response(JSON.stringify({ items: [] })) };
const checks = [];
const ok = (condition, label) => checks.push([Boolean(condition), label]);
const user = "222222222222";
const pendingJobs = [];
let sequence = 1;
function payload(name, extra = {}) {
  return { id: String(100000000000000000n + BigInt(sequence++)), application_id: env.DISCORD_CLIENT_ID, token: "test-interaction-token", type: 2, data: { name, ...extra }, user: { id: user } };
}
async function signedCall(body, { timestamp = String(Math.floor(Date.now() / 1000)), signatureBody = JSON.stringify(body), path = "/v1/discord/interactions" } = {}) {
  const signature = sign(null, Buffer.from(timestamp + signatureBody), pair.privateKey).toString("hex");
  return worker.fetch(new Request(`https://worker.test${path}`, { method: "POST", body: JSON.stringify(body), headers: {
    "content-type": "application/json", "x-signature-timestamp": timestamp, "x-signature-ed25519": signature,
  } }), env, { waitUntil(promise) { pendingJobs.push(promise); } });
}
async function result(response) {
  const body = await response.text();
  try { return JSON.parse(body); } catch { return { status: response.status, raw: body }; }
}
async function flushJobs() { await Promise.all(pendingJobs.splice(0)); }

(async () => {
  const ping = { application_id: env.DISCORD_CLIENT_ID, type: 1 };
  let r = await signedCall(ping);
  ok(r.status === 200 && (await result(r)).type === 1, "valid Discord PING returns PONG");

  r = await signedCall(payload("help"));
  let data = await result(r);
  ok(r.status === 200 && data.type === 4 && data.data.flags === 64 && data.data.content.includes("/buildler") &&
    data.data.embeds[0].title === "TD2 LOOT ADVISOR // SHD" && data.data.embeds[0].color === 0xff5500,
    "help command returns a branded private SHD response");
  r = await signedCall(payload("yardim")); data = await result(r);
  ok(data.data.content.includes("/haberler") && data.data.embeds[0].footer.text.includes("Kaivolt"), "Turkish help alias returns branded command list");
  r = await signedCall(payload("surum")); data = await result(r);
  ok(data.data.content.includes("9.1.5-test"), "Turkish version alias shares the existing version behavior");
  env.DISCORD_FETCH = async (url, init) => {
    ok(String(url) === "https://api.github.com/repos/FEDERALTURK/td2-loot-advisor/releases/latest" && init.headers["user-agent"].includes("TD2"),
      "GitHub command uses the fixed public project release endpoint");
    return new Response(JSON.stringify({ tag_name: "v-test", published_at: "2026-11-21T00:00:00Z",
      html_url: "https://github.com/FEDERALTURK/td2-loot-advisor/releases/tag/v-test" }));
  };
  let githubUser = "666666666666";
  let latestRelease = payload("github"); latestRelease.user.id = githubUser;
  r = await signedCall(latestRelease); data = await result(r);
  ok(data.data.content.includes("v-test") && data.data.content.includes("github.com/FEDERALTURK/td2-loot-advisor/releases/tag/v-test"),
    "GitHub command privately reports the latest release");
  env.DISCORD_FETCH = async () => new Response(JSON.stringify({ tag_name: "v-bad", html_url: "https://evil.example/releases/tag/v-bad" }));
  let unsafeRelease = payload("github"); unsafeRelease.user.id = githubUser;
  r = await signedCall(unsafeRelease); data = await result(r);
  ok(data.data.content.includes("alınamadı") && !data.data.content.includes("evil.example"), "GitHub command rejects a release link outside the fixed repository");
  env.DISCORD_FETCH = async () => new Response(JSON.stringify({ items: [] }));
  let unconfiguredAsk = payload("sor", { options: [{ name: "soru", type: 3, value: "Build nasıl kaydedilir?" }] });
  unconfiguredAsk.user.id = "777777777777";
  r = await signedCall(unconfiguredAsk); data = await result(r);
  ok(data.data.flags === 64 && data.data.content.includes("henüz yapılandırılmamış"), "AI command fails closed when its binding is absent");
  r = await signedCall(payload("haberler")); data = await result(r);
  ok(data.data.content.includes("Son 30 gün") && data.data.flags === 64, "news command gives a private empty state");
  env.DISCORD_FETCH = async url => {
    if (String(url) !== "https://worker.test/v1/tasks/live") throw new Error("unexpected tasks URL");
    return new Response(JSON.stringify({ version: "20261121.1", tasks: [
      { title: "Weekly Project", objective: "Complete missions", reporters: 3, expires_at: null },
    ] }));
  };
  r = await signedCall(payload("gorevler")); data = await result(r);
  ok(data.data.content.includes("Weekly Project") && data.data.content.toLowerCase().includes("topluluk") && data.data.flags === 64,
    "tasks command displays the current community feed privately");
  env.DISCORD_FETCH = async () => { throw new Error("offline"); };
  r = await signedCall(payload("gorevler")); data = await result(r);
  ok(data.data.content.includes("alınamadı"), "tasks command handles Worker failures without throwing");
  env.DISCORD_FETCH = async () => new Response(JSON.stringify({ items: [
    { date: new Date().toISOString(), url: "https://x.com/TheDivisionGame/status/123", title: { tr: "Güvenilir haber" }, text: { tr: "Kısa açıklama" } },
    { date: new Date().toISOString(), url: "https://evil.example/", title: { tr: "Harici adres" } },
  ] }));
  r = await signedCall(payload("haberler")); data = await result(r);
  ok(data.data.content.includes("Güvenilir haber") && !data.data.content.includes("evil.example"),
    "news command localizes trusted links and rejects untrusted hosts");
  env.DISCORD_FETCH = async () => new Response("not json", { status: 503 });
  r = await signedCall(payload("haberler")); data = await result(r);
  ok(data.data.content.includes("alınamadı"), "news command handles feed errors safely");
  env.DISCORD_FETCH = async () => new Response(JSON.stringify({ items: [] }));

  let aiCalls = 0;
  const question = "Striker build için genel öneri nedir?";
  let callbackBody;
  env.AI = { run: async (model, input) => {
    aiCalls++;
    ok(model === "@cf/zai-org/glm-4.7-flash" && input.max_tokens === 350 && input.messages[1].content === question,
      "AI uses a bounded model request with only the explicit user question");
    return { response: "Genel olarak hasar seti ve kritik istatistik dengesini hedefle." };
  } };
  env.DISCORD_FETCH = async (url, init) => {
    ok(String(url).endsWith("/webhooks/111111111111/test-interaction-token/messages/@original") && init.method === "PATCH",
      "AI result edits the private deferred Discord response without exposing the token");
    callbackBody = JSON.parse(init.body);
    return new Response(null, { status: 204 });
  };
  const ask = () => payload("sor", { options: [{ name: "soru", type: 3, value: question }] });
  let aiUser = "555555555555";
  const firstAsk = ask(); firstAsk.user.id = aiUser;
  r = await signedCall(firstAsk); data = await result(r);
  ok(data.type === 5 && data.data.flags === 64, "AI command acknowledges privately before inference");
  await flushJobs();
  ok(callbackBody?.content.includes("kritik istatistik") && callbackBody.allowed_mentions.parse.length === 0,
    "AI completion is returned privately with mentions disabled");
  for (let i = 0; i < 5; i++) {
    const item = ask(); item.user.id = aiUser;
    r = await signedCall(item); data = await result(r);
    if (i < 4) await flushJobs();
  }
  ok(data.data.content.toLowerCase().includes("saatte en fazla 5") && aiCalls === 5, "AI has a separate five-requests-per-hour user limit");
  delete env.AI;
  env.DISCORD_FETCH = async () => new Response(JSON.stringify({ items: [] }));

  const replay = payload("help");
  r = await signedCall(replay);
  ok(r.status === 200, "first signed interaction accepted");
  r = await signedCall(replay);
  data = await result(r);
  ok(r.status === 200 && data.data.content.includes("daha önce"), "duplicate interaction ID acknowledged without reprocessing");

  r = await signedCall(payload("help"), { timestamp: String(Math.floor(Date.now() / 1000) - 301) });
  ok(r.status === 401, "stale signature timestamp rejected");
  r = await signedCall(payload("help"), { signatureBody: "tampered" });
  ok(r.status === 401, "tampered body rejected");
  const wrongApp = payload("help"); wrongApp.application_id = "999999999999";
  r = await signedCall(wrongApp);
  ok(r.status === 401, "wrong application ID rejected");

  sql.prepare("INSERT INTO accounts (discord_id, username, avatar, created, last_login) VALUES (?, ?, NULL, 1, 1)").run(user, "Test Agent");
  const accountId = sql.prepare("SELECT id FROM accounts WHERE discord_id = ?").get(user).id;
  const foreignId = "333333333333";
  sql.prepare("INSERT INTO accounts (discord_id, username, avatar, created, last_login) VALUES (?, ?, NULL, 1, 1)").run(foreignId, "Other Agent");
  const foreignAccountId = sql.prepare("SELECT id FROM accounts WHERE discord_id = ?").get(foreignId).id;
  sql.prepare("INSERT INTO mobile_builds (account_id, client_id, name, payload, updated) VALUES (?, ?, ?, ?, 1)")
    .run(accountId, "my-build-1", "Striker DPS", JSON.stringify({ playstyle: "DPS", gear: "Mask: Coyote's Mask\nChest: Striker" }));
  sql.prepare("INSERT INTO mobile_builds (account_id, client_id, name, payload, updated) VALUES (?, ?, ?, ?, 1)")
    .run(foreignAccountId, "other-build", "Private Other Build", JSON.stringify({ gear: "secret" }));

  r = await signedCall(payload("account")); data = await result(r);
  ok(data.data.content.includes("Test Agent") && data.data.content.includes("free"), "account command shows only caller account tier");
  r = await signedCall(payload("builds")); data = await result(r);
  ok(data.data.content.includes("Striker DPS") && !data.data.content.includes("Private Other Build"), "build list is limited to linked Discord account");

  const share = isPublic => payload("build-share", { options: [
    { name: "build_id", type: 3, value: "my-build-1" }, { name: "public", type: 5, value: isPublic },
  ] });
  r = await signedCall(share(false)); data = await result(r);
  ok(data.data.flags === 64 && data.data.content.includes("Coyote's Mask"), "build share defaults to private summary");
  r = await signedCall(share(true)); data = await result(r);
  ok(!data.data.flags && data.data.allowed_mentions.parse.length === 0, "public share requires explicit option and disables mentions");

  const crossAccount = payload("build-share", { options: [{ name: "build_id", type: 3, value: "other-build" }] });
  r = await signedCall(crossAccount); data = await result(r);
  ok(data.data.content.includes("bulunamadı") && !data.data.content.includes("secret"), "cannot share another Discord account build");
  r = await signedCall(payload("notifications")); data = await result(r);
  ok(data.data.flags === 64 && data.data.content.includes("webhook"), "notification command explains opt-in desktop setup without requesting secrets");
  r = await signedCall(payload("bildirimler")); data = await result(r);
  ok(data.data.flags === 64 && data.data.content.includes("DM"), "Turkish notification alias preserves the honest DM limitation");
  r = await signedCall(payload("hesap")); data = await result(r);
  ok(data.data.content.includes("Test Agent") && data.data.content.includes("free"), "Turkish account alias remains scoped to the caller");
  r = await signedCall(payload("buildler")); data = await result(r);
  ok(data.data.content.includes("Striker DPS") && !data.data.content.includes("Private Other Build"), "Turkish build alias remains account-scoped");

  const rateUser = "444444444444";
  for (let i = 0; i < 21; i++) {
    const item = payload("help"); item.user.id = rateUser;
    r = await signedCall(item);
  }
  data = await result(r);
  ok(r.status === 200 && data.data.content.includes("sınırına ulaştın"), "per-user command rate limit is enforced");

  for (const [passed, label] of checks) console.log(`${passed ? "OK   " : "FAIL "}${label}`);
  if (checks.some(([passed]) => !passed)) process.exitCode = 1;
})().finally(() => sql.close());
