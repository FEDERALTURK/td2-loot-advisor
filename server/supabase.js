// Optional server-side mirror for the TD2 panel observability tables.
// The service-role key is read only from the Worker secret and is never sent
// to browsers, desktop clients, logs, or error responses.

const MAX_TEXT = 6000;

function clip(value, max = MAX_TEXT) {
  return String(value ?? "").slice(0, max);
}

function enabled(env) {
  const flag = String(env?.SUPABASE_PANEL_ENABLED ?? "false").toLowerCase();
  return !["", "0", "false", "off", "no"].includes(flag)
    && Boolean(String(env?.SUPABASE_URL ?? "").trim())
    && Boolean(String(env?.SUPABASE_SECRET_KEY ?? env?.SUPABASE_SERVICE_ROLE_KEY ?? "").trim());
}

async function post(env, table, row) {
  if (!enabled(env)) return false;
  const base = String(env.SUPABASE_URL).replace(/\/+$/, "");
  const key = String(env.SUPABASE_SECRET_KEY ?? env.SUPABASE_SERVICE_ROLE_KEY);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(`${base}/rest/v1/${table}`, {
      method: "POST",
      headers: {
        apikey: key,
        authorization: `Bearer ${key}`,
        "content-type": "application/json",
        prefer: "return=minimal",
      },
      body: JSON.stringify(row),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`supabase ${res.status}`);
    return true;
  } finally {
    clearTimeout(timer);
  }
}

async function get(env, table, query) {
  if (!enabled(env)) return null;
  const base = String(env.SUPABASE_URL).replace(/\/+$/, "");
  const key = String(env.SUPABASE_SECRET_KEY ?? env.SUPABASE_SERVICE_ROLE_KEY);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(`${base}/rest/v1/${table}?${query}`, {
      headers: { apikey: key, authorization: `Bearer ${key}`, accept: "application/json" },
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`supabase ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

function safePlatform(value) {
  const p = String(value || "unknown").toLowerCase();
  return ["windows", "android", "ios", "server", "unknown"].includes(p) ? p : "unknown";
}

/** Best-effort only: a Supabase outage must never fail the D1 report path. */
export async function mirrorErrorReport(env, input) {
  if (!enabled(env)) return false;
  const row = {
    app_version: clip(input.app_version, 40) || null,
    platform: safePlatform(input.platform),
    severity: ["debug", "info", "warning", "error", "critical"].includes(input.severity)
      ? input.severity : "error",
    error_code: clip(input.error_code, 120) || null,
    message_masked: clip(input.message_masked),
    stack_hash: clip(input.stack_hash, 128) || null,
    user_hash: clip(input.user_hash, 128) || null,
    status: "new",
    metadata: input.metadata && typeof input.metadata === "object" ? input.metadata : {},
  };
  try {
    return await post(env, "panel_error_reports", row);
  } catch (_err) {
    return false;
  }
}

/** Admin-only caller; do not expose service-role credentials to the browser. */
export async function readErrorReports(env, limit = 50) {
  if (!enabled(env)) return null;
  const n = Math.max(1, Math.min(100, Number.parseInt(limit, 10) || 50));
  try {
    const rows = await get(env, "panel_error_reports", new URLSearchParams({
      select: "id,created_at,app_version,platform,severity,error_code,message_masked,stack_hash,user_hash,status,metadata",
      order: "created_at.desc",
      limit: String(n),
    }).toString());
    return Array.isArray(rows) ? rows : [];
  } catch (_err) {
    return false;
  }
}

export function isSupabasePanelEnabled(env) {
  return enabled(env);
}
