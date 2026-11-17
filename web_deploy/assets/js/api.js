// TD2 Loot Advisor — web sitesi için ortak yardımcılar: GitHub release/haber okuma ve hesap sunucusu istemcisi.
"use strict";

const TD2_TOKEN_KEY = "td2_session_token";
const TD2_VERIFIER_PREFIX = "td2_verifier:"; // + state -> sessionStorage

// ---------------------------------------------------------------- küçük yardımcılar
function td2B64u(bytes) {
  let s = ""; for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function td2RandomB64u(n) { return td2B64u(crypto.getRandomValues(new Uint8Array(n))); }
async function td2Sha256B64u(text) {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)));
  return td2B64u(d);
}
function td2DeviceId() {
  // Masaüstü uygulaması gerçek bir makine kimliği kullanır (bkz. account.py); web tarafında buna karşılık
  // gelen şey, bu tarayıcıya özel, kalıcı (ama kimliksiz) rastgele bir kimliktir.
  try {
    let id = localStorage.getItem("td2_device_id");
    if (!id) { id = td2RandomB64u(32); localStorage.setItem("td2_device_id", id); }
    return id;
  } catch (e) { return td2RandomB64u(32); } // depolama yoksa (gizli pencere) en azından bu oturumda çalışsın
}

// ---------------------------------------------------------------- hesap sunucusu
function td2ApiBase() { return window.TD2_CONFIG.API_BASE.replace(/\/$/, ""); }
function td2Token() { try { return localStorage.getItem(TD2_TOKEN_KEY); } catch (e) { return null; } }
function td2SetToken(t) { try { if (t) localStorage.setItem(TD2_TOKEN_KEY, t); else localStorage.removeItem(TD2_TOKEN_KEY); } catch (e) { /* yoksay */ } }

async function td2Api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "content-type": "application/json" };
  if (auth) { const t = td2Token(); if (t) headers.authorization = "Bearer " + t; }
  const r = await fetch(td2ApiBase() + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  let j = null; try { j = await r.json(); } catch (e) { /* gövdesiz yanıt */ }
  return { ok: r.ok, status: r.status, json: j || {} };
}

// Discord girişini başlatır: sunucudan yetkilendirme bağlantısını alır, doğrulayıcıyı bu state için
// saklar ve tarayıcıyı Discord'a yönlendirir. (bkz. server/accounts.js authStart, "platform":"web")
async function td2LoginStart() {
  const state = td2RandomB64u(24), verifier = td2RandomB64u(32);
  const challenge = await td2Sha256B64u(verifier);
  const r = await td2Api("/v1/auth/start", { method: "POST", auth: false, body: { state, challenge, platform: "web" } });
  if (!r.ok || !r.json.url) throw new Error(r.json.error || "login_start_failed");
  try { sessionStorage.setItem(TD2_VERIFIER_PREFIX + state, verifier); } catch (e) { /* yoksay */ }
  window.location.href = r.json.url;
}

// Discord dönüşünden sonra (#state=..&grant=..) çağrılır: doğrulayıcıyı bulur, oturumu alır.
// Dönüş: {ok:true, data} ya da {ok:false, error}. Başarılıysa URL'deki fragment temizlenir.
async function td2LoginComplete() {
  const frag = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const state = frag.get("state"), grant = frag.get("grant");
  if (!state || !grant) return { ok: false, error: "no_pending_login" };
  let verifier = null;
  try { verifier = sessionStorage.getItem(TD2_VERIFIER_PREFIX + state); } catch (e) { /* yoksay */ }
  if (!verifier) return { ok: false, error: "verifier_missing" }; // başka sekme/tarayıcı ya da süresi dolmuş
  const r = await td2Api("/v1/auth/token", { method: "POST", auth: false,
    body: { state, verifier, grant, device: td2DeviceId() } });
  try { sessionStorage.removeItem(TD2_VERIFIER_PREFIX + state); } catch (e) { /* yoksay */ }
  history.replaceState(null, "", window.location.pathname + window.location.search); // fragment'i temizle
  if (!r.ok || r.json.status !== "ok") return { ok: false, error: r.json.error || "login_failed" };
  td2SetToken(r.json.token);
  return { ok: true, data: r.json };
}

async function td2Me() {
  if (!td2Token()) return null;
  const r = await td2Api("/v1/me");
  if (r.status === 401) { td2SetToken(null); return null; }
  if (!r.ok) throw new Error(r.json.error || "me_failed");
  return r.json;
}
async function td2Logout() {
  if (td2Token()) await td2Api("/v1/auth/logout", { method: "POST" }).catch(() => {});
  td2SetToken(null);
}
async function td2Redeem(code) {
  const r = await td2Api("/v1/license/redeem", { method: "POST", body: { code } });
  if (!r.ok || !r.json.ok) throw new Error(r.json.error || "redeem_failed");
  return r.json;
}
async function td2DeleteAccount() {
  const r = await td2Api("/v1/me", { method: "DELETE" });
  if (!r.ok) throw new Error(r.json.error || "delete_failed");
  td2SetToken(null);
  return r.json;
}

// ---------------------------------------------------------------- GitHub: son sürüm
async function td2LatestRelease() {
  const r = await fetch(`https://api.github.com/repos/${window.TD2_CONFIG.REPO}/releases/latest`,
    { headers: { accept: "application/vnd.github+json" } });
  if (!r.ok) throw new Error("release_fetch_failed");
  return r.json();
}

// ---------------------------------------------------------------- oyun haberleri (uygulamayla aynı kaynak)
// Not: news_cache.json uygulamanın YEREL çalışma zamanı önbelleğidir (.gitignore'da) — GitHub'da yoktur.
// Site, uygulamanın depoya işlenen asıl kaynağını okur: meta/news_feed.json (bkz. README "Knowledge tab").
async function td2News() {
  const url = `https://raw.githubusercontent.com/${window.TD2_CONFIG.REPO}/main/meta/news_feed.json`;
  const r = await fetch(url);
  if (!r.ok) throw new Error("news_fetch_failed");
  return r.json();
}
// The Division 3 durumu — resmî duyurular/kaynaklar, meta/division3_feed.json'dan.
async function td2Division3() {
  const url = `https://raw.githubusercontent.com/${window.TD2_CONFIG.REPO}/main/meta/division3_feed.json`;
  const r = await fetch(url);
  if (!r.ok) throw new Error("d3_fetch_failed");
  return r.json();
}
