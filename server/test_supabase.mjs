import assert from "node:assert/strict";
import { mirrorErrorReport, readErrorReports, isSupabasePanelEnabled } from "./supabase.js";
import worker from "./worker.js";

const calls = [];
const realFetch = globalThis.fetch;
globalThis.fetch = async (url, opts = {}) => {
  calls.push({ url, opts });
  return new Response(null, { status: 201 });
};

const base = {
  SUPABASE_URL: "https://example.supabase.co/",
  SUPABASE_SECRET_KEY: "sb_secret_test-only",
  SUPABASE_PANEL_ENABLED: "true",
};

assert.equal(isSupabasePanelEnabled({ ...base }), true);
assert.equal(isSupabasePanelEnabled({ ...base, SUPABASE_PANEL_ENABLED: "false" }), false);
const health = await worker.fetch(new Request("https://w/v1/health"), base);
const healthJson = await health.json();
assert.equal(healthJson.panel_mirror, "enabled");
const disabledHealth = await worker.fetch(new Request("https://w/v1/health"), { ...base, SUPABASE_PANEL_ENABLED: "false" });
assert.equal((await disabledHealth.json()).panel_mirror, "disabled");
assert.equal(await mirrorErrorReport({ ...base, SUPABASE_PANEL_ENABLED: "false" }, { message_masked: "x" }), false);
assert.equal(calls.length, 0, "disabled mirror must not call the network");

const ok = await mirrorErrorReport(base, {
  app_version: "9.1.5.36",
  platform: "windows",
  severity: "error",
  error_code: "ocr_empty",
  message_masked: "OCR output empty",
  stack_hash: "abc",
  user_hash: "def",
  metadata: { report_type: "bug", lang: "tr" },
});
assert.equal(ok, true);
assert.equal(calls.length, 1);
assert.equal(calls[0].url, "https://example.supabase.co/rest/v1/panel_error_reports");
assert.equal(calls[0].opts.method, "POST");
assert.equal(calls[0].opts.headers.apikey, base.SUPABASE_SECRET_KEY);
const sent = JSON.parse(calls[0].opts.body);
assert.equal(sent.platform, "windows");
assert.equal(sent.status, "new");
assert.equal(sent.metadata.lang, "tr");

globalThis.fetch = async (url, opts = {}) => {
  calls.push({ url, opts });
  return Response.json([{ id: 1, status: "new", message_masked: "safe" }]);
};
const rows = await readErrorReports(base, 10);
assert.equal(rows.length, 1);
assert.match(calls.at(-1).url, /panel_error_reports\?/);

globalThis.fetch = async () => new Response("down", { status: 503 });
assert.equal(await mirrorErrorReport(base, { message_masked: "still safe" }), false);

globalThis.fetch = realFetch;
console.log("RESULT: PASS");
