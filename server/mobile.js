// Mobil companion — bulut altyapısı (Faz 2, bkz. docs/mobile_companion_roadmap.md).
//
// Tasarım ilkeleri (roadmap'teki "Target architecture" ile aynı):
//  - Telefon asla masaüstüne doğrudan bağlanmaz; her şey bu Worker üzerinden gider.
//  - Eşleştirme: masaüstü kısa ömürlü bir kod üretir (desktop hesabı, Bearer oturumuyla), telefon bu kodu
//    bir kerede "claim" eder ve kendi taşınabilir cihaz oturumunu alır. Kod tek kullanımlıktır.
//  - Masaüstüne giden komutlar yalnız ALLOWED_COMMANDS listesindeki, önceden izin verilmiş komutlardır;
//    telefon keyfi bir komut gönderemez. Masaüstü komutları kendi documented scan kontrolleriyle yorumlar
//    (bu Worker hiçbir komutu doğrudan çalıştırmaz, sadece kuyruğa koyar/okur).
//  - Masaüstünden bulut'a giden "event" içinde ekran görüntüsü, oyun belleği veya dosya içeriği YOKTUR;
//    yalnız küçük bir durum JSON'u (örn. {type:"scan_result", slot:"Mask", decision:"keep"}).
//  - Push belirteçleri (APNs/FCM) burada saklanır ama bu Faz 2 artımında gerçek bir push GÖNDERİMİ henüz
//    yok (APNs/FCM kimlik bilgisi yok) — bkz. ROADMAP.md "Faz 2" notu. sendPush() bilerek bir iskelet/stub'dır.
//
// Ortam: aynı D1 (env.DB), accounts.js ile aynı HASH_SALT.

import { session as desktopSession } from "./accounts.js";

const enc = new TextEncoder();
const now = () => Math.floor(Date.now() / 1000);
const DAY = 86400;
const PAIR_TTL = 300;                 // eşleştirme kodu 5 dakika geçerli
const DEVICE_TTL = 180 * DAY;         // telefon oturumu 180 gün (sessizce pairing ile uzatılabilir)
const ALLOWED_COMMANDS = new Set(["scan_start", "scan_stop"]);
const DELETE_GRACE_SECONDS = 24 * 3600;   // hesap silme talebinden sonra bekleme süresi

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra },
  });
}
async function sha256(text) {
  const d = await crypto.subtle.digest("SHA-256", enc.encode(text));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("");
}
function b64uEnc(bytes) { let s = ""; for (const b of bytes) s += String.fromCharCode(b); return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
function randomToken(n = 32) { return b64uEnc(crypto.getRandomValues(new Uint8Array(n))); }
const salt = env => env.HASH_SALT || "dev-salt";
const ipOf = req => req.headers.get("cf-connecting-ip") || "local";
const ID = /^[A-Za-z0-9_\-]{16,64}$/;

async function rate(env, bucket, max, windowSec = 3600) {
  const slot = Math.floor(Date.now() / 1000 / windowSec);
  const row = await env.DB.prepare(
    "INSERT INTO rate (bucket, hour, n) VALUES (?1, ?2, 1) ON CONFLICT(bucket, hour) DO UPDATE SET n = n + 1 RETURNING n"
  ).bind("m:" + bucket, slot).first();
  return (row?.n ?? 1) <= max;
}

// ------------------------------------------------------------ telefonun kendi oturumu
async function phoneSession(req, env) {
  const m = /^Bearer\s+([A-Za-z0-9_\-]{32,128})$/.exec(req.headers.get("authorization") || "");
  if (!m) return null;
  const th = await sha256(m[1]);
  const d = await env.DB.prepare(
    "SELECT device_id, account_id, platform, expires FROM mobile_devices WHERE token_hash = ?1 AND revoked = 0").bind(th).first();
  if (!d || d.expires < now()) return null;
  await env.DB.prepare("UPDATE mobile_devices SET last_seen = ?1 WHERE device_id = ?2").bind(now(), d.device_id).run();
  return d;
}

// ------------------------------------------------------------ eşleştirme (masaüstü → kod, telefon → claim)
async function createPairing(req, env) {
  const s = await desktopSession(req, env);
  if (!s) return json({ error: "unauthorized" }, 401);
  if (!(await rate(env, "pair:acc:" + s.account_id, 20))) return json({ error: "rate limited" }, 429);
  await env.DB.prepare("DELETE FROM mobile_pairings WHERE expires < ?1").bind(now() - DAY).run();
  const code = randomToken(6).replace(/[^A-Za-z0-9]/g, "").slice(0, 8).toUpperCase() || "PAIR0000";
  await env.DB.prepare("INSERT INTO mobile_pairings (code_hash, account_id, created, expires) VALUES (?1, ?2, ?3, ?4)")
    .bind(await sha256(salt(env) + ":pair:" + code), s.account_id, now(), now() + PAIR_TTL).run();
  return json({ code, expires_in: PAIR_TTL });
}

async function claimPairing(req, env) {
  let b; try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const code = String(b?.code || "").toUpperCase().trim();
  const platform = b?.platform === "ios" ? "ios" : b?.platform === "android" ? "android" : null;
  if (!code || !platform) return json({ error: "bad request" }, 400);
  const ipb = (await sha256(salt(env) + ipOf(req))).slice(0, 24);
  if (!(await rate(env, "claim:ip:" + ipb, 30))) return json({ error: "rate limited" }, 429);
  const ch = await sha256(salt(env) + ":pair:" + code);
  const p = await env.DB.prepare("SELECT * FROM mobile_pairings WHERE code_hash = ?1").bind(ch).first();
  if (!p || p.claimed || p.expires < now()) return json({ error: "invalid or expired code" }, 410);
  const r = await env.DB.prepare("UPDATE mobile_pairings SET claimed = 1 WHERE code_hash = ?1 AND claimed = 0").bind(ch).run();
  if (!r.meta?.changes) return json({ error: "code already used" }, 409);   // yarış durumunda tek kazanan
  const deviceId = randomToken(16), token = randomToken(32);
  await env.DB.prepare(
    "INSERT INTO mobile_devices (device_id, account_id, token_hash, platform, created, last_seen, expires) VALUES (?1, ?2, ?3, ?4, ?5, ?5, ?6)")
    .bind(deviceId, p.account_id, await sha256(token), platform, now(), now() + DEVICE_TTL).run();
  return json({ device_id: deviceId, token, expires_in: DEVICE_TTL });
}

// ------------------------------------------------------------ gösterge paneli (telefon)
async function dashboard(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json({ error: "unauthorized" }, 401);
  const st = await env.DB.prepare("SELECT online, last_event, last_seen FROM desktop_status WHERE account_id = ?1").bind(d.account_id).first();
  const online = !!st && st.online && (now() - st.last_seen) < 120;   // 2 dakikadan uzun sessizlik = çevrimdışı say
  let lastEvent = null;
  try { lastEvent = st?.last_event ? JSON.parse(st.last_event) : null; } catch { lastEvent = null; }
  return json({ desktop: { online, last_seen: st?.last_seen || null, last_event: lastEvent } });
}

// ------------------------------------------------------------ masaüstü kuyruğu (komut gönder/al) ve olaylar
async function sendCommand(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json({ error: "unauthorized" }, 401);
  let b; try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  if (!ALLOWED_COMMANDS.has(b?.command)) return json({ error: "command not allowed" }, 400);
  if (!(await rate(env, "cmd:dev:" + d.device_id, 60))) return json({ error: "rate limited" }, 429);
  await env.DB.prepare("INSERT INTO desktop_inbox (account_id, command, created) VALUES (?1, ?2, ?3)")
    .bind(d.account_id, b.command, now()).run();
  return json({ ok: true });
}

async function desktopInbox(req, env) {
  const s = await desktopSession(req, env);
  if (!s) return json({ error: "unauthorized" }, 401);
  const rows = (await env.DB.prepare(
    "SELECT id, command, created FROM desktop_inbox WHERE account_id = ?1 AND delivered = 0 ORDER BY id LIMIT 20")
    .bind(s.account_id).all()).results || [];
  if (rows.length) {
    const ids = rows.map(r => r.id);
    await env.DB.batch(ids.map(id => env.DB.prepare("UPDATE desktop_inbox SET delivered = 1 WHERE id = ?1").bind(id)));
  }
  return json({ commands: rows.map(r => ({ command: r.command, created: r.created })) });
}

async function desktopEvent(req, env) {
  const s = await desktopSession(req, env);
  if (!s) return json({ error: "unauthorized" }, 401);
  let b; try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  if (!b || typeof b.type !== "string" || !/^[a-z_]{2,32}$/.test(b.type)) return json({ error: "bad event" }, 400);
  const safe = {}; for (const [k, v] of Object.entries(b).slice(0, 12))
    if (/^[a-z_]{1,24}$/.test(k) && ["string", "number", "boolean"].includes(typeof v)) safe[k] = typeof v === "string" ? v.slice(0, 160) : v;
  await env.DB.prepare(
    "INSERT INTO desktop_status (account_id, online, last_event, last_seen) VALUES (?1, 1, ?2, ?3) " +
    "ON CONFLICT(account_id) DO UPDATE SET online = 1, last_event = ?2, last_seen = ?3")
    .bind(s.account_id, JSON.stringify(safe), now()).run();
  return json({ ok: true });
}

// ------------------------------------------------------------ build senkronu (telefonun kendi build kütüphanesi)
async function listBuilds(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json({ error: "unauthorized" }, 401);
  const rows = (await env.DB.prepare(
    "SELECT client_id, name, payload, revision, updated, deleted FROM mobile_builds WHERE account_id = ?1 ORDER BY updated DESC LIMIT 500")
    .bind(d.account_id).all()).results || [];
  return json({ builds: rows.map(r => ({ client_id: r.client_id, name: r.name, payload: JSON.parse(r.payload),
                                          revision: r.revision, updated: r.updated, deleted: !!r.deleted })) });
}

async function putBuild(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json({ error: "unauthorized" }, 401);
  let b; try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const clientId = String(b?.client_id || "");
  if (!ID.test(clientId)) return json({ error: "bad client_id" }, 400);
  const name = String(b?.name || "").slice(0, 80).trim();
  if (!name) return json({ error: "name required" }, 400);
  let payload; try { payload = JSON.stringify(b.payload ?? {}); } catch { return json({ error: "bad payload" }, 400); }
  if (payload.length > 20000) return json({ error: "payload too large" }, 413);
  const baseRev = Number.isFinite(b.base_revision) ? b.base_revision : 0;
  const cur = await env.DB.prepare("SELECT revision FROM mobile_builds WHERE account_id = ?1 AND client_id = ?2")
    .bind(d.account_id, clientId).first();
  if (cur && cur.revision !== baseRev) return json({ error: "revision conflict", revision: cur.revision }, 409);
  const nextRev = (cur?.revision || 0) + 1;
  await env.DB.prepare(
    "INSERT INTO mobile_builds (account_id, client_id, name, payload, revision, updated, deleted) VALUES (?1, ?2, ?3, ?4, ?5, ?6, 0) " +
    "ON CONFLICT(account_id, client_id) DO UPDATE SET name = ?3, payload = ?4, revision = ?5, updated = ?6, deleted = 0")
    .bind(d.account_id, clientId, name, payload, nextRev, now()).run();
  return json({ ok: true, revision: nextRev });
}

// ------------------------------------------------------------ push belirteçleri (iskelet — gerçek gönderim yok)
async function sendPush(_env, _accountId, _payload) {
  // TODO(Faz 4): APNs (HTTP/2 + JWT) ve FCM (HTTP v1) kimlik bilgileri eklenince burada gerçek gönderim
  // yapılacak. Şu an sadece belirteç saklanıyor; hiçbir bildirim fiilen gönderilmiyor. Bunu "çalışıyor" gibi
  // raporlamak proje talimatlarının 5. maddesine (sahte başarı göstermeme) aykırı olur — bilerek stub.
  return false;
}

async function putPushToken(req, env, deviceId) {
  const d = await phoneSession(req, env);
  if (!d || d.device_id !== deviceId) return json({ error: "unauthorized" }, 401);
  let b; try { b = await req.json(); } catch { return json({ error: "bad json" }, 400); }
  const token = String(b?.token || "");
  if (!token || token.length > 512) return json({ error: "bad token" }, 400);
  await env.DB.prepare(
    "INSERT INTO push_tokens (device_id, token, platform, created) VALUES (?1, ?2, ?3, ?4) " +
    "ON CONFLICT(device_id) DO UPDATE SET token = ?2, created = ?4")
    .bind(deviceId, token, d.platform, now()).run();
  return json({ ok: true, delivery: "not_yet_implemented" });
}

async function deletePushToken(req, env, deviceId) {
  const d = await phoneSession(req, env);
  if (!d || d.device_id !== deviceId) return json({ error: "unauthorized" }, 401);
  await env.DB.prepare("DELETE FROM push_tokens WHERE device_id = ?1").bind(deviceId).run();
  return json({ ok: true });
}

// ------------------------------------------------------------ cihaz/hesap iptali
async function revokeDevice(req, env, deviceId) {
  const s = await desktopSession(req, env);           // masaüstü kendi hesabındaki bir telefonu iptal eder
  if (!s) return json({ error: "unauthorized" }, 401);
  const r = await env.DB.prepare("UPDATE mobile_devices SET revoked = 1 WHERE device_id = ?1 AND account_id = ?2")
    .bind(deviceId, s.account_id).run();
  if (!r.meta?.changes) return json({ error: "not found" }, 404);
  await env.DB.prepare("DELETE FROM push_tokens WHERE device_id = ?1").bind(deviceId).run();
  return json({ ok: true });
}

// Telefon tarafından tetiklenen hesap silme talebi (accounts.js'teki DELETE /v1/me masaüstü içindir — aynı
// account_deletions tablosuna yazar, hangi uygulamadan geldiği önemli değildir).
async function deleteMeFromPhone(req, env) {
  const d = await phoneSession(req, env);
  if (!d) return json({ error: "unauthorized" }, 401);
  await env.DB.prepare("INSERT INTO account_deletions (account_id, requested) VALUES (?1, ?2) ON CONFLICT(account_id) DO NOTHING")
    .bind(d.account_id, now()).run();
  await env.DB.prepare("UPDATE sessions SET revoked = 1 WHERE account_id = ?1").bind(d.account_id).run();
  await env.DB.prepare("UPDATE mobile_devices SET revoked = 1 WHERE account_id = ?1").bind(d.account_id).run();
  return json({ ok: true, deletion_requested: true });
}

// ------------------------------------------------------------ periyodik temizlik (worker.js scheduled() çağırır)
export async function cleanup(env) {
  const t = now();
  await env.DB.prepare("DELETE FROM mobile_pairings WHERE expires < ?1").bind(t - DAY).run();
  await env.DB.prepare("DELETE FROM desktop_inbox WHERE delivered = 1 AND created < ?1").bind(t - 7 * DAY).run();
  await env.DB.prepare("DELETE FROM mobile_devices WHERE revoked = 1 AND last_seen < ?1").bind(t - 30 * DAY).run();
  // Hesap silme: bekleme süresini doldurmuş talepleri gerçekten (geri alınamaz şekilde) sil.
  const due = (await env.DB.prepare("SELECT account_id FROM account_deletions WHERE requested < ?1")
    .bind(t - DELETE_GRACE_SECONDS).all()).results || [];
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
      env.DB.prepare("DELETE FROM account_deletions WHERE account_id = ?1").bind(id),
    ]);
  }
  return { deleted_accounts: due.length };
}

// ------------------------------------------------------------ yönlendirme
export async function route(req, env, path) {
  let m;
  if (path === "/v1/mobile/pairings" && req.method === "POST") return createPairing(req, env);
  if (path === "/v1/mobile/pairings/claim" && req.method === "POST") return claimPairing(req, env);
  if (path === "/v1/mobile/dashboard" && req.method === "GET") return dashboard(req, env);
  if (path === "/v1/mobile/desktop/inbox" && req.method === "GET") return desktopInbox(req, env);
  if (path === "/v1/mobile/desktop/events" && req.method === "POST") return desktopEvent(req, env);
  if (path === "/v1/mobile/desktop/commands" && req.method === "POST") return sendCommand(req, env);
  if (path === "/v1/mobile/builds" && req.method === "GET") return listBuilds(req, env);
  if (path === "/v1/mobile/builds" && req.method === "PUT") return putBuild(req, env);
  if (path === "/v1/mobile/me" && req.method === "DELETE") return deleteMeFromPhone(req, env);
  if ((m = /^\/v1\/mobile\/push-tokens\/([A-Za-z0-9_\-]{16,64})$/.exec(path)) && req.method === "PUT") return putPushToken(req, env, m[1]);
  if ((m = /^\/v1\/mobile\/push-tokens\/([A-Za-z0-9_\-]{16,64})$/.exec(path)) && req.method === "DELETE") return deletePushToken(req, env, m[1]);
  if ((m = /^\/v1\/mobile\/devices\/([A-Za-z0-9_\-]{16,64})$/.exec(path)) && req.method === "DELETE") return revokeDevice(req, env, m[1]);
  return null;
}
