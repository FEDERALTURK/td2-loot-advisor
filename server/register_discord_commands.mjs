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
const existingResponse = await fetch(url, { headers });
if (!existingResponse.ok) {
  console.error(`Guild komutları okunamadı: HTTP ${existingResponse.status}. Yanıt gövdesi yazdırılmadı.`);
  process.exit(1);
}
const existing = await existingResponse.json();
if (!Array.isArray(existing)) {
  console.error("Discord komut listesi beklenen biçimde değil; hiçbir komut değiştirilmedi.");
  process.exit(1);
}
for (const command of COMMANDS) {
  const previous = existing.find(item => item.name === command.name && (item.type || 1) === 1);
  const result = await fetch(previous ? `${url}/${previous.id}` : url, {
    method: previous ? "PATCH" : "POST", headers, body: JSON.stringify(command),
  });
  if (!result.ok) {
    console.error(`/${command.name} komutu kaydedilemedi: HTTP ${result.status}. Önceki guild komutları korunmuştur; yanıt gövdesi yazdırılmadı.`);
    process.exit(1);
  }
}
console.log(`Guild kapsamındaki ${COMMANDS.length} Discord komutu kaydedildi.`);
