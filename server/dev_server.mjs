// Yerel test sunucusu: worker.js + bellek içi SQLite + sahte Discord/Gumroad. Yalnız testler içindir.
//   node server/dev_server.mjs [port]     → "READY <port> <ADMIN_TOKEN> <ENT_PUBLIC_KEY>"
// Sahte Discord: /v1/auth/start'ın verdiği discord.com bağlantısı yerine bu sunucunun /fake/discord adresi kullanılır;
// o adres doğrudan /v1/auth/callback?code=... ya yönlendirir (kullanıcı adı ?user= ile seçilir).
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { createServer } from "node:http";
import { generateKeyPairSync } from "node:crypto";
import worker from "./worker.js";

const sql = new DatabaseSync(":memory:");
sql.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
const stmt = q => { let a = []; const s = {
  bind(...x) { a = x; return s; },
  async run() { const r = sql.prepare(q).run(...a); return { meta: { changes: Number(r.changes) } }; },
  async first() { return sql.prepare(q).get(...a) ?? null; },
  async all() { return { results: sql.prepare(q).all(...a) }; } }; return s; };

const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const port = parseInt(process.argv[2] || "8799", 10);
const env = { DB: { prepare: stmt }, HASH_SALT: "dev", DISCORD_CLIENT_ID: "dev-client", DISCORD_CLIENT_SECRET: "dev-secret",
  ENT_SIGNING_KEY: privateKey.export({ format: "der", type: "pkcs8" }).toString("base64"),
  ENT_PUBLIC_KEY: publicKey.export({ format: "der", type: "spki" }).subarray(-32).toString("hex"),
  ADMIN_TOKEN: process.env.DEV_ADMIN_TOKEN || "dev-admin-token-0123456789abcdef", GUMROAD_PRODUCT_ID: "dev-product",
  PUBLIC_URL: `http://127.0.0.1:${port}`, LICENSE_PUBKEY: "00".repeat(32) };

const realFetch = globalThis.fetch;
globalThis.fetch = async (url, opts = {}) => {
  if (url.startsWith("https://discord.com/api/oauth2/token")) return Response.json({ access_token: new URLSearchParams(opts.body).get("code") });
  if (url === "https://discord.com/api/users/@me") {
    const who = (opts.headers.authorization || "").replace("Bearer ", "") || "agent";
    return Response.json({ id: String(100000000000 + [...who].reduce((a, c) => a * 31 + c.charCodeAt(0), 7) % 899999999999), username: who, global_name: who });
  }
  if (url.startsWith("https://api.gumroad.com/")) {
    const k = new URLSearchParams(opts.body).get("license_key");
    return Response.json(k.startsWith("GOOD") ? { success: true, purchase: { sale_id: k, email: "x@y.z" } } : { success: false });
  }
  return realFetch(url, opts);
};

createServer(async (rq, rs) => {
  const chunks = []; for await (const c of rq) chunks.push(c);
  const url = `http://127.0.0.1:${port}${rq.url}`;
  let res;
  const u = new URL(url);
  if (u.pathname === "/fake/discord") {          // tarayıcıdaki Discord onayı yerine
    res = new Response(null, { status: 302, headers: { location: `/v1/auth/callback?state=${u.searchParams.get("state")}&code=${u.searchParams.get("user") || "agent"}` } });
  } else {
    const req = new Request(url, { method: rq.method, headers: { ...rq.headers, "cf-connecting-ip": "127.0.0.1" },
                                   body: ["GET", "HEAD"].includes(rq.method) ? undefined : Buffer.concat(chunks) });
    res = await worker.fetch(req, env);
    if (u.pathname === "/v1/auth/start" && res.status === 200) {   // discord.com → sahte onay sayfası
      const j = await res.json(); const st = new URL(j.url).searchParams.get("state");
      res = Response.json({ ...j, url: `https://discord.com/oauth2/authorize?state=${st}`, dev_url: `http://127.0.0.1:${port}/fake/discord?state=${st}` });
    }
  }
  rs.writeHead(res.status, Object.fromEntries(res.headers)); rs.end(Buffer.from(await res.arrayBuffer()));
}).listen(port, "127.0.0.1", () => console.log(`READY ${port} ${env.ADMIN_TOKEN} ${env.ENT_PUBLIC_KEY}`));
