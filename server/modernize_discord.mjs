// Idempotent Discord server setup. Dry-run by default; never logs the bot token.
const API = "https://discord.com/api/v10";
const guildId = process.env.DISCORD_GUILD_ID;
const token = process.env.DISCORD_BOT_TOKEN;
const apply = process.argv.includes("--apply");

const channelPlan = [
  { name: "rules", type: 0, category: null },
  { name: "karşılama-ve-kurallar", type: 0, category: "Bilgi" },
  { name: "duyurular", type: 0, category: "Bilgi" },
  { name: "kaynaklar", type: 0, category: "Bilgi" },
  { name: "uygulama-tanitim", type: 0, category: "Bilgi" },
  { name: "genel", type: 0, category: "Metin Kanalları" },
  { name: "toplantı-planları", type: 0, category: "Metin Kanalları" },
  { name: "konu-dışı", type: 0, category: "Metin Kanalları" },
  { name: "build-paylasim", type: 0, category: "Metin Kanalları" },
  { name: "yardim-destek", type: 0, category: "Metin Kanalları" },
  { name: "hata-bildirimi", type: 0, category: "Metin Kanalları" },
  { name: "surum-notlari", type: 0, category: "Metin Kanalları" },
  { name: "Salon", type: 2, category: "Ses Kanalları" },
  { name: "Toplantı Odası", type: 2, category: "Ses Kanalları" },
];

const rolePlan = ["Üye", "Moderasyon", "Destek", "Geliştirici"];
const defaultChannelNames = new Set([
  "rules", "karşılama-ve-kurallar", "duyurular", "uygulama-tanitim", "yardim-destek",
]);

if (!/^\d{5,25}$/.test(guildId || "")) {
  console.error("DISCORD_GUILD_ID geçerli bir Discord sunucu ID'si olmalı.");
  process.exit(1);
}
if (apply && !token) {
  console.error("--apply için DISCORD_BOT_TOKEN gerekli; token'ı dosyaya veya sohbete yazma.");
  process.exit(1);
}
if (!token) {
  console.error("Discord API önizlemesi için de DISCORD_BOT_TOKEN gerekli; araç sunucuyu okuyarak plan üretir.");
  process.exit(1);
}

const headers = { authorization: `Bot ${token || "dry-run"}`, "content-type": "application/json" };
async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { ...options, headers: { ...headers, ...(options.headers || {}) } });
  if (response.ok) return response.status === 204 ? null : response.json();
  const body = await response.text();
  throw new Error(`${options.method || "GET"} ${path}: HTTP ${response.status} ${body.slice(0, 240)}`);
}

async function mutate(label, method, path, body) {
  console.log(`${apply ? "Uygulanacak" : "Plan"}: ${label}`);
  if (!apply) return null;
  return request(path, { method, body: JSON.stringify(body) });
}

const bot = await request("/users/@me");
try {
  await request(`/guilds/${guildId}`);
} catch (error) {
  if (String(error.message).includes("HTTP 403") || String(error.message).includes("HTTP 404")) {
    throw new Error(
      `Bot erişimi yok: ${bot.username || "bot"} (${bot.id || "ID gizli"}) ` +
      `1572117066071281804 sunucusunda değil veya DISCORD_GUILD_ID yanlış. ` +
      "Botu bu sunucuya bot + applications.commands scope'larıyla davet edin."
    );
  }
  throw error;
}

function byName(items, name) {
  return items.find(item => item.name === name);
}

const channels = await request(`/guilds/${guildId}/channels`);
const categories = new Map(channels.filter(c => c.type === 4).map(c => [c.name, c.id]));
const channelIds = new Map(channels.map(c => [c.name, c.id]));

for (const plan of channelPlan) {
  if (channelIds.has(plan.name)) continue;
  const parentId = plan.category ? categories.get(plan.category) : undefined;
  if (plan.category && !parentId) {
    console.log(`Atlandı: ${plan.name} — kategori ${plan.category} mevcut değil.`);
    continue;
  }
  const created = await mutate(`kanal oluştur: ${plan.name}`, "POST", `/guilds/${guildId}/channels`, {
    name: plan.name, type: plan.type, ...(parentId ? { parent_id: parentId } : {}),
  });
  if (created) channelIds.set(plan.name, created.id);
}

const roles = await request(`/guilds/${guildId}/roles`);
const roleIds = new Map(roles.map(role => [role.name, role.id]));
for (const name of rolePlan) {
  if (roleIds.has(name)) continue;
  const created = await mutate(`rol oluştur: ${name} (izin=0)`, "POST", `/guilds/${guildId}/roles`, {
    name, permissions: "0", mentionable: false,
  });
  if (created) roleIds.set(name, created.id);
}

const onboarding = await request(`/guilds/${guildId}/onboarding`);
const defaultIds = [...defaultChannelNames]
  .map(name => channelIds.get(name))
  .filter(Boolean);
if (defaultIds.length < 3) {
  throw new Error("Onboarding için en az üç mevcut varsayılan kanal bulunamadı.");
}

let onboardingStatus = "updated";
try {
  await mutate("onboarding varsayılan kanalları güncelle", "PATCH", `/guilds/${guildId}/onboarding`, {
    default_channel_ids: defaultIds,
    enabled: Boolean(onboarding.enabled),
    ...(Number.isInteger(onboarding.mode) ? { mode: onboarding.mode } : {}),
    ...(Array.isArray(onboarding.prompts) ? { prompts: onboarding.prompts } : {}),
  });
} catch (error) {
  if (String(error.message).includes("HTTP 405")) {
    onboardingStatus = "skipped_api_unsupported";
    console.warn("Atlandı: Discord bot REST API'si Community Onboarding PATCH isteğini kabul etmiyor; onboarding ayarları Discord masaüstü arayüzünden yapılmalı.");
  } else {
    throw error;
  }
}

console.log(JSON.stringify({
  mode: apply ? "apply" : "dry-run",
  guild_id: guildId,
  ensured_channels: channelPlan.map(item => item.name),
  ensured_roles: rolePlan,
  default_channels: [...defaultChannelNames],
  onboarding_enabled_before: Boolean(onboarding.enabled),
  onboarding_status: onboardingStatus,
}, null, 2));
