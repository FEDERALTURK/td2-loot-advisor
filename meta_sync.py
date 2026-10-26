"""Meta build senkronu.

Herkese açık uygulama için tasarlandı: meta listesi tek bir merkezde (GitHub deposundaki
meta/meta_builds.json) günde bir güncellenir; her kullanıcının programı açılışta, son
denemeden bu yana 20 saat geçtiyse listeyi indirir ve kendi build listesine işler.

Kurallar
- Kullanıcının kendi build'lerine (meta_id'si olmayan) asla dokunulmaz.
- Kullanıcı bir meta build'i düzenlerse o build "meta_locked" olur; artık güncellenmez/silinmez.
- Akıştan çıkan, kilitsiz meta build'ler listeden kaldırılır (ilerleme kayıtları silinmez).
- Sadece HTTPS, en fazla 512 KB, 8 sn zaman aşımı; ilk adres olmazsa yedek adreslere geçer.
- Bilinmeyen alanlar ve bilinmeyen attribute anahtarları atılır, sayılar sınırlanır.
- İnternet yoksa son başarılı kopya (meta_cache.json) kullanılır; program açılışı beklemez.
Ek kütüphane gerektirmez (urllib).
"""
import json
import logging
import re
import ssl
import time
import urllib.request
from datetime import datetime, timedelta, timezone

log = logging.getLogger("td2")

SCHEMA = 1
MAX_BYTES = 512 * 1024
TIMEOUT_S = 8
MAX_BUILDS = 40
SYNC_EVERY_S = 20 * 3600          # "günlük": aynı gün içinde tekrar açılışlarda indirme yapmaz

# Resmî akış: GitHub deposu (raw) + jsDelivr CDN yedeği. Depo hazır olunca OWNER/REPO değişir.
FEED_REPO = "FEDERALTURK/td2-loot-advisor"
FEED_PATH = "meta/meta_builds.json"


def default_urls(repo=FEED_REPO, path=FEED_PATH, branch="main"):
    return [f"https://raw.githubusercontent.com/{repo}/{branch}/{path}",
            f"https://cdn.jsdelivr.net/gh/{repo}@{branch}/{path}"]


def configured_urls(setting):
    """Ayardaki adres(ler): boşsa resmî akış; virgül/boşlukla birden fazla adres verilebilir."""
    urls = [u.strip() for u in re.split(r"[,\s]+", setting or "") if u.strip()]
    urls = urls or default_urls()
    return [u for u in urls if u.lower().startswith("https://") and "OWNER/" not in u]


# ---------------------------------------------------------------- indirme
def fetch(urls, app_version="", timeout=TIMEOUT_S):
    """İlk çalışan adresten akışı indirir. (veri, adres) ya da hata fırlatır."""
    last = None
    ctx = ssl.create_default_context()
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": f"TD2-Loot-Advisor/{app_version}", "Accept": "application/json",
                "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                raw = r.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("feed too large")
            return json.loads(raw.decode("utf-8")), url
        except Exception as e:          # bir sonraki yedek adresi dene
            last = e
            log.debug("Meta feed failed at %s: %s", url, e)
    raise last or RuntimeError("no feed url")


# ---------------------------------------------------------------- doğrulama
def _num(v, lo, hi, default=0.0):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def _text(v, n=120):
    return re.sub(r"[\x00-\x1f]", " ", str(v or "")).strip()[:n]


def validate(feed, known_attrs):
    """Akışı güvenli, programın anladığı biçime indirger. Hatalıysa ValueError."""
    if not isinstance(feed, dict) or int(feed.get("schema", 0)) != SCHEMA:
        raise ValueError("unsupported feed schema")
    out = {"schema": SCHEMA, "version": _text(feed.get("version"), 40),
           "updated": _text(feed.get("updated"), 40), "season": _text(feed.get("season"), 60), "builds": []}
    seen = set()
    for b in (feed.get("builds") or [])[:MAX_BUILDS]:
        if not isinstance(b, dict): continue
        mid = re.sub(r"[^a-z0-9\-]", "", str(b.get("id", "")).lower())[:60]
        name = _text(b.get("name"), 80)
        if not mid or not name or mid in seen: continue
        seen.add(mid)
        attrs = {}
        for k, v in (b.get("attributes") or {}).items():
            if k in known_attrs and isinstance(v, dict):
                attrs[k] = {"weight": round(_num(v.get("weight"), 0, 5, 1), 2),
                            "good_at": round(_num(v.get("good_at"), 0, 1_000_000, 0), 2)}
        talents = {}
        for k, v in list((b.get("talents") or {}).items())[:20]:
            k = _text(k, 60)
            if k: talents[k] = round(_num(v, 0, 10, 1), 2)
        build = {
            "meta_id": mid, "name": name,
            "sets_or_brands": [_text(s, 60) for s in (b.get("sets_or_brands") or [])[:6] if _text(s, 60)],
            "set_bonus": round(_num(b.get("set_bonus"), 0, 50, 0), 1),
            "attributes": attrs, "talents": talents,
            "items": [_text(x, 60) for x in (b.get("items") or [])[:8] if _text(x, 60)],
            "meta": {"mode": _text(b.get("mode"), 60), "role": _text(b.get("role"), 20),
                     "popularity": int(_num(b.get("popularity"), 0, 100, 0)),
                     "summary": {str(l)[:5]: _text(s, 300) for l, s in (b.get("summary") or {}).items()},
                     "sources": [{"title": _text(s.get("title"), 80), "url": _text(s.get("url"), 300)}
                                 for s in (b.get("sources") or [])[:6]
                                 if isinstance(s, dict) and str(s.get("url", "")).startswith("https://")]},
        }
        slots = [_text(s, 20) for s in (b.get("slots") or [])[:6] if _text(s, 20)]
        if slots: build["slots"] = slots
        out["builds"].append(build)
    if not out["builds"]:
        raise ValueError("feed has no valid builds")
    return out


# ---------------------------------------------------------------- birleştirme
def merge(builds, feed, hidden=()):
    """Meta build'leri kullanıcının listesine işler. (yeni liste, özet) döner.
    hidden: kullanıcının sildiği meta build kimlikleri (bir daha eklenmez).
    özet["renames"]: {eski ad: yeni ad} — ilerleme kayıtlarını taşımak için."""
    hidden = set(hidden or ())
    incoming = {b["meta_id"]: b for b in feed["builds"] if b["meta_id"] not in hidden}
    result, added, updated, removed, renames = [], 0, 0, 0, {}
    present = set()
    for b in builds:
        mid = b.get("meta_id")
        if not mid:                                   # kullanıcının kendi build'i
            result.append(b); continue
        if b.get("meta_locked"):                      # kullanıcı düzenledi: dokunma
            result.append(b); present.add(mid); continue
        if mid in incoming:
            new = dict(incoming[mid])
            if b.get("slots") and "slots" not in new: new["slots"] = b["slots"]
            if _comparable(b) != _comparable(new): updated += 1
            if b.get("name") != new["name"]: renames[b["name"]] = new["name"]
            result.append(new); present.add(mid)
        else:
            removed += 1                              # akıştan çıktı
    names = {b["name"] for b in result}
    for mid, b in incoming.items():
        if mid in present: continue
        b = dict(b)
        while b["name"] in names: b["name"] += " ★"
        names.add(b["name"]); result.append(b); added += 1
    return result, {"added": added, "updated": updated, "removed": removed, "renames": renames}


def _comparable(b):
    return json.dumps({k: b.get(k) for k in ("name", "sets_or_brands", "set_bonus", "attributes", "talents", "items", "meta")},
                      sort_keys=True, ensure_ascii=False)


# ---------------------------------------------------------------- zamanlama
def due(settings, kind="builds", now=None):
    """Bu tür (builds/tasks) bugün indirilmeli mi? Hiç indirilmediyse hemen."""
    flag, stamp = {"builds": ("meta_sync", "meta_last_try"), "tasks": ("tasks_sync", "tasks_last_try"),
                   "wiki": ("wiki_sync", "wiki_last_try")}[kind]
    if not settings.get(flag, True): return False
    now = now or time.time()
    return now - float(settings.get(stamp, 0) or 0) >= SYNC_EVERY_S


def run(cfg, cache_path, app_version="", force=False):
    """Arka plan iş parçacığında çağrılır: indirir + doğrular. Ana iş parçacığında
    apply() ile işlenmek üzere (feed, kaynak) döner. Hata olursa önbelleği dener."""
    st = cfg["settings"]
    urls = configured_urls(st.get("meta_feed_url", ""))
    known = set(cfg.get("attributes", {}).keys())
    if not urls:
        raise RuntimeError("meta feed not configured")
    try:
        raw, url = fetch(urls, app_version)
        feed = validate(raw, known)
        try: cache_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")  # ham hali saklanır
        except Exception: pass
        return feed, url
    except Exception as e:
        log.info("Meta feed unavailable (%s); trying cache", e)
        if cache_path.exists() and not force:
            return validate(json.loads(cache_path.read_text(encoding="utf-8")), known), "cache"
        raise


def apply(cfg, feed, source):
    """Ana iş parçacığında: birleştirir, ayarlara sürüm/zaman yazar. Özeti döner."""
    st = cfg["settings"]
    cfg["builds"], summary = merge(cfg["builds"], feed, st.get("meta_hidden", []))
    if source != "cache":
        st["meta_version"] = feed.get("version", "")
        st["meta_last_sync"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary.update(version=feed.get("version", ""), season=feed.get("season", ""), source=source)
    return summary


# ================================================================ görev akışı
# Aynı depodaki meta/tasks_feed.json: güncel günlük/haftalık projeler, sezon yolculuğu,
# global etkinlik, manhunt adımları — her biri tüm dillere çevrilmiş olarak gelir.
# Ayrıca oyunun resmî sıfırlama saatlerini (UTC) taşır; program bunları yerel saate çevirir.
TASKS_PATH = "meta/tasks_feed.json"
TASK_CATS = ("projects", "journey", "manhunt")          # oyundaki menülere göre
PROJECT_KINDS = ("daily", "weekly", "settlement", "seasonal")
MAX_TASKS = 80
MAX_GUIDES = 60


def _langs(d, n):
    return {str(l)[:5]: _text(v, n) for l, v in (d or {}).items() if _text(v, n)} if isinstance(d, dict) else {}


def _https(src):
    u = src.get("url") if isinstance(src, dict) else src
    return _text(u, 300) if str(u or "").startswith("https://") else ""


def find_guide(text, guides):
    """Görev metnine (İngilizce) uyan ilk ipucunu döndürür; en uzun anahtar kelime kazanır."""
    low = (text or "").lower()
    best, blen = None, 0
    for g in guides or []:
        for k in g["match"]:
            if k in low and len(k) > blen:
                best, blen = g, len(k)
    return best


def task_urls(builds_setting):
    """Build akışı adreslerinden görev akışı adreslerini türetir (aynı depo/klasör)."""
    return [u.replace("meta_builds.json", "tasks_feed.json") for u in configured_urls(builds_setting)
            if u.endswith("meta_builds.json")]


def _iso_utc(v):
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except Exception:
        return None


def validate_tasks(feed):
    if not isinstance(feed, dict) or int(feed.get("schema", 0)) != SCHEMA:
        raise ValueError("unsupported tasks schema")
    out = {"version": _text(feed.get("version"), 40), "season": _text(feed.get("season"), 60),
           "resets": None, "tasks": [], "guides": [],
           "wiki_season": _text((feed.get("wiki") or {}).get("season_page"), 80) if isinstance(feed.get("wiki"), dict) else ""}
    for g in (feed.get("guides") or [])[:MAX_GUIDES]:
        if not isinstance(g, dict): continue
        keys = [str(k).lower().strip()[:40] for k in (g.get("match") or [])[:12] if str(k).strip()]
        tip = _langs(g.get("tip"), 500)
        if keys and "en" in tip:
            out["guides"].append({"id": _text(g.get("id"), 60), "match": keys, "tip": tip,
                                  "source": _https(g.get("source"))})
    r = feed.get("resets") or {}
    try:
        out["resets"] = {"daily_hour_utc": int(_num(r["daily_hour_utc"], 0, 23)),
                         "weekly_weekday": int(_num(r["weekly_weekday"], 0, 6)),      # 0 = Pazartesi
                         "weekly_hour_utc": int(_num(r["weekly_hour_utc"], 0, 23))}
    except Exception:
        out["resets"] = None
    seen = set()
    for it in (feed.get("tasks") or [])[:MAX_TASKS]:
        if not isinstance(it, dict): continue
        tid = re.sub(r"[^a-z0-9\-]", "", str(it.get("id", "")).lower())[:80]
        cat, kind = it.get("cat"), it.get("kind") if it.get("kind") in PROJECT_KINDS else ""
        if cat in PROJECT_KINDS: cat, kind = "projects", cat          # eski biçim: cat=daily/weekly
        if cat not in TASK_CATS: continue                             # global_event/other artık yok
        texts = {str(l)[:5]: _text(v, 300) for l, v in (it.get("text") or {}).items() if _text(v, 300)}
        if not tid or tid in seen or "en" not in texts: continue
        seen.add(tid)
        until = _iso_utc(it.get("until"))
        src = it.get("source") if isinstance(it.get("source"), dict) else {}
        out["tasks"].append({"feed_id": tid, "wiki_id": _text(it.get("wiki_id"), 80), "cat": cat, "kind": kind if cat == "projects" else "", "texts": texts, "how": _langs(it.get("how"), 500),
                             "until": until.isoformat(timespec="minutes") if until else "",
                             "source": _text(src.get("url"), 300) if str(src.get("url", "")).startswith("https://") else ""})
    return out


def task_expired(item, now=None):
    u = _iso_utc(item.get("until")) if item.get("until") else None
    return bool(u and u <= (now or datetime.now(timezone.utc)))


def merge_tasks(tasks, feed, now=None, scope="feed"):
    """Akış görevlerini kullanıcının görev listesine işler. Kendi eklediği görevlere dokunmaz;
    akış görevlerinin 'yapıldı' işaretini korur; süresi dolanları ve akıştan çıkanları kaldırır.
    scope: "feed" (ortak liste, 🌐), "wiki" (canlı wiki, 📚, kimlikler "wiki-") ya da "community" (oyunculardan
    toplanan görevler, 👥, kimlikler "cm-");
    her kaynak yalnızca kendi görevlerini ekler/siler."""
    prefixes = {"wiki": "wiki-", "community": "cm-"}
    if scope in prefixes: owned = lambda f, p=prefixes[scope]: f.startswith(p)
    else: owned = lambda f: not any(f.startswith(p) for p in prefixes.values())
    now = now or datetime.now(timezone.utc)
    items = tasks.setdefault("items", {})
    done = {x["feed_id"]: x.get("done", False) for c in items.values() for x in c if x.get("feed_id")}
    added = removed = 0
    live = {x["feed_id"] for x in feed["tasks"] if not task_expired(x, now)}
    if scope == "wiki":       # ortak listede (10 dilde, ayrıntılı) zaten olan wiki görevlerini tekrar ekleme
        covered = {x.get("wiki_id") for c in items.values() for x in c if x.get("wiki_id")}
        live -= covered
    for c in TASK_CATS:
        lst = items.setdefault(c, [])
        before = len(lst)
        items[c] = [x for x in lst if not x.get("feed_id") or not owned(x["feed_id"]) or x["feed_id"] in live]
        removed += before - len(items[c])
        have = {x["feed_id"]: x for x in items[c] if x.get("feed_id")}
        for x in feed["tasks"]:
            if x["cat"] != c or x["feed_id"] not in live: continue
            row = {"feed_id": x["feed_id"], "wiki_id": x.get("wiki_id", ""), "kind": x.get("kind", ""), "texts": x["texts"], "how": x.get("how", {}), "en": x["texts"]["en"], "tr": "", "src": {"wiki": "📚", "community": "👥"}.get(scope, "🌐"),
                   "until": x["until"], "url": x["source"], "done": done.get(x["feed_id"], False),
                   "time": now.isoformat(timespec="seconds")}
            if x["feed_id"] in have:
                old = have[x["feed_id"]]
                if old.get("en") == row["en"]:          # metin aynıysa önceki çevirileri koru
                    row["texts"] = {**old.get("texts", {}), **row["texts"]}
                    row["how"] = {**old.get("how", {}), **row["how"]}
                old.update({k: row[k] for k in ("wiki_id", "kind", "texts", "how", "en", "until", "url")})
            else:
                items[c].append(row); added += 1
    def scout_no(x):                             # Manhunt listesi Scout numarasına göre sıralı dursun
        m = re.search(r"Scout (\d+)", x.get("en", ""))
        return int(m.group(1)) if m else 999
    items["manhunt"] = sorted(items.get("manhunt", []), key=scout_no)
    return {"added": added, "removed": removed}


def local_resets(resets, now=None):
    """UTC sıfırlama saatlerini bu bilgisayarın yerel saatine çevirir:
    (günlük saat, haftalık gün 0=Pzt, haftalık saat)."""
    now = now or datetime.now(timezone.utc)
    def conv(weekday, hour):
        base = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        base = base + timedelta(days=(weekday - base.weekday()) % 7)
        loc = base.astimezone()
        return loc.weekday(), loc.hour
    _, dh = conv(now.weekday(), resets["daily_hour_utc"])
    wd, wh = conv(resets["weekly_weekday"], resets["weekly_hour_utc"])
    return dh, wd, wh


def run_tasks(cfg, cache_path, app_version="", force=False):
    urls = task_urls(cfg["settings"].get("meta_feed_url", ""))
    if not urls:
        raise RuntimeError("tasks feed not configured")
    try:
        raw, url = fetch(urls, app_version)
        feed = validate_tasks(raw)
        try: cache_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception: pass
        return feed, url
    except Exception as e:
        log.info("Tasks feed unavailable (%s); trying cache", e)
        if cache_path.exists() and not force:
            return validate_tasks(json.loads(cache_path.read_text(encoding="utf-8"))), "cache"
        raise


# ---------------------------------------------------------------- haber / sezon akışı (meta/news_feed.json)
def news_urls(builds_setting):
    return [u.replace("meta_builds.json", "news_feed.json") for u in configured_urls(builds_setting)
            if u.endswith("meta_builds.json")]


def run_news(cfg, cache_path, app_version="", force=False):
    """Haber akışını indir, doğrula, önbelleğe yaz. Ağ yoksa önbellek, o da yoksa programla gelen dosya."""
    import knowledge
    urls = news_urls(cfg["settings"].get("meta_feed_url", ""))
    try:
        if not urls: raise RuntimeError("news feed not configured")
        raw, url = fetch(urls, app_version)
        feed = knowledge.validate_news(raw)
        try: cache_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception: pass
        return feed, url
    except Exception as e:
        log.info("News feed unavailable (%s); trying cache", e)
        if cache_path.exists():
            return knowledge.validate_news(json.loads(cache_path.read_text(encoding="utf-8"))), "cache"
        raise
