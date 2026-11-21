import { COMMANDS } from "./discord.js";

const clientId = process.env.DISCORD_CLIENT_ID;
const guildId = process.env.DISCORD_GUILD_ID;
const token = process.env.DISCORD_BOT_TOKEN;
if (!/^\d{5,25}$/.test(clientId || "") || !/^\d{5,25}$/.test(guildId || "")) {
  console.error("DISCORD_CLIENT_ID ve DISCORD_GUILD_ID geçerli Discord ID'leri olmalı.");
  process.exit(1);
}

if (!process.argv.includes("--apply")) {
  console.log(JSON.stringify({ application_id: clientId, guild_id: guildId, scope: "guild-only", commands: COMMANDS }, null, 2));
  console.log("Uygulamak için DISCORD_BOT_TOKEN tanımlayıp --apply parametresiyle tekrar çalıştır.");
  process.exit(0);
}
if (!token) {
  console.error("--apply için DISCORD_BOT_TOKEN gerekli. Token'ı dosyaya veya sohbete yazma.");
  process.exit(1);
}

const url = `https://discord.com/api/v10/applications/${clientId}/guilds/${guildId}/commands`;
const headers = { authorization: `Bot ${token}`, "content-type": "application/json" };
async function discordRequest(target, options) {
  for (let attempt = 0; attempt <= 5; attempt += 1) {
    const response = await fetch(target, options);
    if (response.status !== 429 || attempt === 5) return response;

    const retryHeader = response.headers.get("retry-after");
    let retryAfter = retryHeader ? Number(retryHeader) : Number.NaN;
    if (!Number.isFinite(retryAfter) || retryAfter < 0) {
      const payload = await response.clone().json().catch(() => ({}));
      retryAfter = Number(payload.retry_after);
    }
    if (!Number.isFinite(retryAfter) || retryAfter < 0) return response;

    const waitMs = Math.ceil(retryAfter * 1000) + 250;
    console.warn(`Discord rate limit: ${Math.ceil(waitMs / 1000)} sn beklenecek; tekrar ${attempt + 1}/5.`);
    await new Promise(resolve => setTimeout(resolve, waitMs));
  }
}

const existingResponse = await discordRequest(url, { headers });
if (!existingResponse.ok) {
  console.error(`Guild komutları okunamadı: HTTP ${existingResponse.status}. Yanıt gövdesi yazdırılmadı.`);
  process.exit(1);
}
const existing = await existingResponse.json();
if (!Array.isArray(existing)) {
  console.error("Discord komut listesi beklenen biçimde değil; hiçbir komut değiştirilmedi.");
  process.exit(1);
}
let completed = 0;
for (const command of COMMANDS) {
  const previous = existing.find(item => item.name === command.name && (item.type || 1) === 1);
  const result = await discordRequest(previous ? `${url}/${previous.id}` : url, {
    method: previous ? "PATCH" : "POST", headers, body: JSON.stringify(command),
  });
  if (!result.ok) {
    console.error(`/${command.name} komutu kaydedilemedi: HTTP ${result.status}. Bu çalıştırmada ${completed}/${COMMANDS.length} komut kaydedildi; kısmi başarılar geri alınmadı. Güvenle devam etmek için komutu tekrar çalıştırın. Yanıt gövdesi yazdırılmadı.`);
    process.exit(1);
  }
  completed += 1;
}
console.log(`Guild kapsamındaki ${COMMANDS.length} Discord komutu kaydedildi.`);
