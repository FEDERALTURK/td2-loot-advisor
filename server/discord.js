// Discord interactions use the signed HTTP endpoint; no Gateway connection or message intents are needed.
const ENDPOINT = "/v1/discord/interactions";
const MAX_BODY = 64 * 1024;
const MAX_PER_MINUTE = 20;
const encoder = new TextEncoder();

export const COMMANDS = [
  { name: "help", description: "TD2 Loot Advisor komutlarını göster" },
  { name: "version", description: "Program sürüm bilgisini göster" },
  { name: "account", description: "Bağlı Discord hesabı ve lisans durumunu göster" },
  { name: "builds", description: "Hesabına bağlı build adlarını listele" },
  { name: "build-share", description: "Kendi build'ini güvenli biçimde paylaş" , options: [
    { name: "build_id", description: "Paylaşılacak build kimliği", type: 3, required: true, max_length: 80 },
    { name: "public", description: "Build özetini kanalda herkese açık paylaş", type: 5, required: false },
  ] },
  { name: "notifications", description: "Masaüstü Discord bildirimlerini yapılandırma yardımını göster" },
];

function response(content, ephemeral = true) {
  return new Response(JSON.stringify({ type: 4, data: {
    content: String(content).slice(0, 2000),
    ...(ephemeral ? { flags: 64 } : {}),
    allowed_mentions: { parse: [] },
  } }), { status: 200, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
}

function hexBytes(value) {
  if (!/^[0-9a-f]{64}$/i.test(value || "")) return null;
  return Uint8Array.from(value.match(/../g), byte => parseInt(byte, 16));
}

async function validSignature(env, request, body) {
  const publicKey = hexBytes(env.DISCORD_PUBLIC_KEY || "");
  const timestamp = request.headers.get("x-signature-timestamp") || "";
  const signature = request.headers.get("x-signature-ed25519") || "";
  if (!publicKey || !/^\d{10,16}$/.test(timestamp) || !/^[0-9a-f]{128}$/i.test(signature)) return false;
  if (Math.abs(Math.floor(Date.now() / 1000) - Number(timestamp)) > 300) return false;
  try {
    const key = await crypto.subtle.importKey("raw", publicKey, { name: "Ed25519" }, false, ["verify"]);
    const sig = Uint8Array.from(signature.match(/../g), byte => parseInt(byte, 16));
    return await crypto.subtle.verify({ name: "Ed25519" }, key, sig, encoder.encode(timestamp + body));
  } catch {
    return false;
  }
}

function userId(interaction) {
  const id = interaction.member?.user?.id || interaction.user?.id;
  return typeof id === "string" && /^\d{5,25}$/.test(id) ? id : null;
}

function option(interaction, name) {
  return interaction.data?.options?.find(item => item.name === name)?.value;
}

function safeText(value, limit = 160) {
  return String(value || "").replace(/[\u0000-\u001f\u007f]/g, " ").replace(/[`*_~|<>]/g, "")
    .replace(/\s+/g, " ").trim().slice(0, limit);
}

async function linkedAccount(env, id) {
  return env.DB.prepare(
    "SELECT id, username, banned FROM accounts WHERE discord_id = ?1 LIMIT 1"
  ).bind(id).first();
}

async function executeCommand(env, interaction, actor) {
  const name = interaction.data?.name;
  if (name === "help") return response("TD2 Loot Advisor komutları: `/version`, `/account`, `/builds`, `/build-share`, `/notifications`. Hesap ve build komutları yalnız bağlı Discord hesabının verisini gösterir.");
  if (name === "version") return response(env.TD2_APP_VERSION
    ? `TD2 Loot Advisor sürümü: ${safeText(env.TD2_APP_VERSION, 40)}`
    : "Program sürümü Worker ortamında yapılandırılmamış.");
  if (name === "notifications") return response("Masaüstü uygulamasında Ayarlar → Hizmetler bölümünden Discord webhook bildirimlerini isteğe bağlı olarak yapılandır. Bu komut webhook veya gizli anahtar istemez; bot DM bildirimi etkin değildir.");
  if (name === "account") {
    const account = await linkedAccount(env, actor);
    if (!account || account.banned) return response("Bu Discord hesabına TD2 Loot Advisor hesabı bağlı değil. Masaüstü uygulamasında Discord ile giriş yapıp tekrar dene.");
    const license = await env.DB.prepare(
      "SELECT tier, expires FROM licenses WHERE account_id = ?1 AND revoked = 0 AND (expires IS NULL OR expires > ?2) ORDER BY expires IS NULL DESC, expires DESC LIMIT 1"
    ).bind(account.id, Math.floor(Date.now() / 1000)).first();
    const tier = safeText(license?.tier || "free", 24);
    const expiry = license?.expires ? ` · bitiş: ${new Date(license.expires * 1000).toISOString().slice(0, 10)}` : "";
    return response(`Hesap: ${safeText(account.username, 40)} · plan: ${tier}${expiry}`);
  }
  if (name === "builds" || name === "build-share") {
    const account = await linkedAccount(env, actor);
    if (!account || account.banned) return response("Bu Discord hesabına TD2 Loot Advisor hesabı bağlı değil.");
    if (name === "builds") {
      const rows = (await env.DB.prepare(
        "SELECT client_id, name FROM mobile_builds WHERE account_id = ?1 AND deleted = 0 ORDER BY updated DESC LIMIT 10"
      ).bind(account.id).all()).results || [];
      return response(rows.length
        ? `Kayıtlı build'lerin:\n${rows.map(row => `• ${safeText(row.name, 80)} — \`${safeText(row.client_id, 40)}\``).join("\n")}`
        : "Hesabında eşitlenmiş build bulunamadı.");
    }
    const buildId = option(interaction, "build_id");
    if (typeof buildId !== "string" || !/^[A-Za-z0-9_\-]{1,80}$/.test(buildId)) return response("Build kimliği geçersiz.");
    const row = await env.DB.prepare(
      "SELECT name, payload FROM mobile_builds WHERE account_id = ?1 AND client_id = ?2 AND deleted = 0 LIMIT 1"
    ).bind(account.id, buildId).first();
    if (!row) return response("Bu build bulunamadı veya bu hesaba ait değil.");
    let payload;
    try { payload = JSON.parse(row.payload); } catch { return response("Build verisi okunamadı; hiçbir içerik paylaşılmadı."); }
    const details = typeof payload.gear === "string" ? payload.gear
      : Object.entries(payload.slots || {}).map(([slot, item]) => `${slot}: ${item?.name || item}`).join("\n");
    const summary = safeText(details, 900);
    const content = `Build: ${safeText(row.name, 80)}${payload.playstyle ? ` · ${safeText(payload.playstyle, 80)}` : ""}${summary ? `\n${summary}` : ""}`;
    return response(content, option(interaction, "public") !== true);
  }
  return response("Bilinmeyen komut. `/help` komutunu kullan.");
}

export async function route(request, env, path) {
  if (path !== ENDPOINT) return null;
  if (request.method !== "POST") return new Response(null, { status: 405, headers: { allow: "POST" } });
  if (!env.DISCORD_PUBLIC_KEY || !env.DISCORD_CLIENT_ID) return new Response(null, { status: 503 });
  const declaredLength = Number(request.headers.get("content-length") || 0);
  if (declaredLength > MAX_BODY) return new Response(null, { status: 413 });
  const raw = await request.text();
  if (encoder.encode(raw).byteLength > MAX_BODY) return new Response(null, { status: 413 });
  if (!(await validSignature(env, request, raw))) return new Response(null, { status: 401 });
  let interaction;
  try { interaction = JSON.parse(raw); } catch { return new Response(null, { status: 400 }); }
  if (interaction.application_id !== env.DISCORD_CLIENT_ID) return new Response(null, { status: 401 });
  if (interaction.type === 1) return new Response(JSON.stringify({ type: 1 }), { headers: { "content-type": "application/json" } });
  if (interaction.type !== 2 || !/^\d{5,25}$/.test(interaction.id || "")) return new Response(null, { status: 400 });
  const actor = userId(interaction);
  if (!actor) return response("Discord kullanıcı bilgisi alınamadı.");
  const created = Math.floor(Date.now() / 1000);
  try {
    const inserted = await env.DB.prepare(
      "INSERT INTO discord_interactions (interaction_id, user_id, created) VALUES (?1, ?2, ?3) ON CONFLICT(interaction_id) DO NOTHING"
    ).bind(interaction.id, actor, created).run();
    if (!inserted.meta?.changes) return response("Bu Discord isteği daha önce işlendi.");
    const windowStart = Math.floor(created / 60) * 60;
    const rate = await env.DB.prepare(
      "INSERT INTO discord_rate_limits (user_id, window_start, requests) VALUES (?1, ?2, 1) " +
      "ON CONFLICT(user_id, window_start) DO UPDATE SET requests = requests + 1 RETURNING requests"
    ).bind(actor, windowStart).first();
    if (rate?.requests > MAX_PER_MINUTE) return response("Komut kullanım sınırına ulaştın. Bir dakika sonra tekrar dene.");
    return await executeCommand(env, interaction, actor);
  } catch {
    return new Response(null, { status: 503 });
  }
}

export async function cleanup(env) {
  const cutoff = Math.floor(Date.now() / 1000);
  await env.DB.prepare("DELETE FROM discord_interactions WHERE created < ?1").bind(cutoff - 48 * 3600).run();
  await env.DB.prepare("DELETE FROM discord_rate_limits WHERE window_start < ?1").bind(cutoff - 3600).run();
}
