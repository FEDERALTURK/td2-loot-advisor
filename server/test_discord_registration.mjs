import assert from "node:assert/strict";
import { COMMANDS } from "./discord.js";

const names = ["DISCORD_CLIENT_ID", "DISCORD_GUILD_ID", "DISCORD_BOT_TOKEN"];
const previousEnv = Object.fromEntries(names.map(name => [name, process.env[name]]));
const previousArgv = process.argv;
const previousFetch = globalThis.fetch;
const calls = [];

process.env.DISCORD_CLIENT_ID = "1564066001363148920";
process.env.DISCORD_GUILD_ID = "1572117066071281804";
process.env.DISCORD_BOT_TOKEN = "test-token";
process.argv = [...process.argv, "--apply"];
globalThis.fetch = async (url, options) => {
  calls.push({ url: String(url), method: options?.method || "GET" });
  if (calls.length === 1) {
    return new Response("[]", { status: 200, headers: { "content-type": "application/json" } });
  }
  if (calls.length === 7) {
    return new Response(JSON.stringify({ retry_after: 0.01 }), {
      status: 429,
      headers: { "content-type": "application/json", "retry-after": "0.01" },
    });
  }
  return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
};

try {
  await import(`./register_discord_commands.mjs?test=${Date.now()}`);
  assert.equal(calls.length, COMMANDS.length + 2, "the rate-limited command should be retried once");
  assert.equal(calls[6].url, calls[7].url, "retry should target the same command");
  assert.equal(calls[6].method, "POST");
  assert.equal(calls[7].method, "POST");
  console.log("OK   Discord 429 honors Retry-After and safely retries the pending command");
} finally {
  globalThis.fetch = previousFetch;
  process.argv = previousArgv;
  for (const name of names) {
    if (previousEnv[name] === undefined) delete process.env[name];
    else process.env[name] = previousEnv[name];
  }
}
