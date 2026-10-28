"""Haftalık satıcılar ve hedefli loot — build'ine ve sandığına göre eşleştirme.

İki kaynak:
1) Oyunda satıcı ekranını tara ("Satıcı modu": F8 ile okunan eşyalar sandığa değil bu listeye girer) — tamamen bizim verimiz.
2) Topluluk verisi: hi-dep "Division 2 Database" (https://github.com/hi-dep/division2). Veri depomuza KOPYALANMAZ;
   program onu kullanıcının bilgisayarında doğrudan herkese açık adresinden okur ve kaynağı gösterir.
   Depoda lisans belirtilmemiştir: ticari/premium kullanım için sahibinden izin alınmalıdır.

    week = fetch_week()                      # {"week": "2026-10-20", "items": [...], "target_loot": {...}, "source": ...}
    items = [to_item(r, game) for r in week["items"]]
    hits = match(items, builds, plan_fn, owned, game)
"""
import gzip
import io
import json
import logging
import time
import urllib.request

import engine
import stash

log = logging.getLogger("td2.vendor")

SOURCE_NAME = "hi-dep · Division 2 Database"
SOURCE_URL = "https://hidep-division2.pages.dev/?view=vendor"
BASES = ("https://raw.githubusercontent.com/hi-dep/division2/main/division2/data/",
         "https://cdn.jsdelivr.net/gh/hi-dep/division2@main/division2/data/")
UA = {"User-Agent": "TD2-Loot-Advisor (+https://github.com/FEDERALTURK/td2-loot-advisor)"}

WEAPON_TYPES = {"ar": "Assault Rifle", "smg": "Submachine Gun", "lmg": "Light Machine Gun", "mmr": "Marksman Rifle",
                "rifle": "Rifle", "shotgun": "Shotgun", "pistol": "Pistol"}
RARITY = {"highend": "HIGH-END", "named": "NAMED", "gearset": "GEAR SET", "exotic": "EXOTIC", "superior": "SUPERIOR"}
GEAR_SLOTS = {s.lower(): s for s in engine.GEAR_SLOTS}


def _get(path, timeout=15):
    last = None
    for base in BASES:
        try:
            req = urllib.request.Request(base + path, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            if path.endswith(".gz"): data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            last = e
            log.debug("vendor source %s%s failed: %s", base, path, e)
    raise RuntimeError(f"vendor feed unreachable: {last}")


def fetch_week():
    """Bu haftanın satıcı listesi ve hedefli loot'u (ağ gerektirir)."""
    idx = _get("index.json")
    week = idx.get("target_week")
    chunk = next((c for c in reversed(idx.get("chunks", [])) if c.get("start", "") <= (week or "") <= c.get("end", "")),
                 (idx.get("chunks") or [None])[-1])
    if not chunk: raise RuntimeError("vendor feed: no data")
    data = _get(chunk["file"].replace(".db.gz", ".json.gz"))
    weeks = data.get("weeks", {})
    if week not in weeks: week = max(weeks) if weeks else week
    try:
        tl = _get("target_looted/target_looted_latest.json.gz")
    except Exception:
        tl = {}
    return {"week": week, "items": weeks.get(week, []), "target_loot": tl.get("events", {}),
            "fetched": time.time(), "source": SOURCE_NAME}


def load_cache(path):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError):
        return None


def save_cache(path, week):
    with open(path, "w", encoding="utf-8") as f: json.dump(week, f, ensure_ascii=False)


def last_reset(now=None, weekday=1, hour_utc=8):
    """Son haftalık sıfırlama zamanı (Salı ~08:00 UTC = 03:30 EST yaz saati farkıyla yaklaşık)."""
    t = time.gmtime(now or time.time())
    days_back = (t.tm_wday - weekday) % 7
    base = (now or time.time()) - days_back * 86400
    bt = time.gmtime(base)
    reset = time.mktime((bt.tm_year, bt.tm_mon, bt.tm_mday, hour_utc, 0, 0, 0, 0, 0)) - time.timezone
    if reset > (now or time.time()): reset -= 7 * 86400
    return reset


def stale(cache, now=None):
    return not cache or cache.get("fetched", 0) < last_reset(now)


def _attr_key(game, stat):
    from gamedata import nrm, best_window
    n = nrm(stat)
    if n in game.attr_alias: return game.attr_alias[n]
    best, br = None, 0.0
    for al, k in game.attr_alias.items():
        r = best_window(n, al)
        if r > br: best, br = k, r
    return best if br >= 0.85 else None


def to_item(rec, game, vendor=None):
    """Topluluk kaydı -> uygulamanın eşya biçimi (sandık / optimize ile aynı)."""
    cat = rec.get("category")
    slot_raw = (rec.get("slot_key") or "").lower()
    kind = {"gear": "gear", "weapon": "weapon"}.get(cat, "mod" if cat == "mod" else cat)
    wtype = WEAPON_TYPES.get(slot_raw) if kind == "weapon" else None
    slot = GEAR_SLOTS.get(slot_raw) if kind == "gear" else ("Sidearm" if wtype == "Pistol" else "Weapon") if kind == "weapon" else None
    rarity = [RARITY.get(rec.get("rarity"), (rec.get("rarity") or "").upper())]
    brand = rec.get("brand_en")
    gs = brand if rec.get("rarity") == "gearset" else None
    attrs, quality, talents = {}, {}, []
    for ln in rec.get("lines", []):
        if ln.get("line_type") == "talent":
            if ln.get("stat_en"): talents.append(ln["stat_en"])
            continue
        if ln.get("value_num") is None: continue
        k = _attr_key(game, ln.get("stat_en", "")) if game and game.ok else None
        if not k: continue
        v = float(ln["value_num"]); attrs[k] = v
        mx = game.max_of(k, False, kind == "weapon")
        if mx: quality[k] = round(min(100.0, v / mx * 100))
    name = rec.get("name_en") or " ".join(x for x in (brand, rec.get("slot_en")) if x) or "?"
    return {"name": name, "kind": kind, "slot": slot, "brand": None if gs else brand, "gear_set": gs,
            "rarity": rarity, "weapon_type": wtype, "attrs": attrs, "quality": quality, "talents": talents,
            "vendor": vendor or rec.get("vendor_en"), "id": "v:" + str(rec.get("item_id", id(rec)))}


def match(items, builds, plan_fn, owned, game=None, min_gain=15, min_fit=60, per_slot=2):
    """Satıcıdaki eşyalardan hangisi hangi build'de sendekinden daha iyi?
    Dönüş: [{"build", "slot", "item", "vendor", "fit", "have", "have_item", "gain", "checks"}] (kazanca göre)."""
    out = []
    gear = [i for i in items if i.get("kind") in ("gear", "weapon") and i.get("slot")]
    for b in builds:
        try:
            plan = plan_fn(b)
            base = stash.optimize(b, plan, owned, game)
        except Exception:
            continue
        for it in gear:
            cur = base["slots"].get(it["slot"])
            if not cur: continue
            reqs = [cur["req"], plan.get(it["slot"])]
            fit, checks = max((stash.slot_fit(it, r, game) for r in reqs if r), key=lambda x: x[0], default=(0, []))
            if not any(c[0] in ("source", "core", "attr", "talent") for c in checks):
                continue                                  # yalnız "tür" şartı olan yuva (ör. herhangi bir tabanca): öneri değil
            gain = fit - (cur["fit"] if cur.get("item") else 0)
            if fit >= min_fit and gain >= min_gain:
                out.append({"build": b["name"], "slot": it["slot"], "item": it, "vendor": it.get("vendor"), "fit": fit,
                            "have": cur["fit"] if cur.get("item") else 0,
                            "have_item": (cur.get("item") or {}).get("name"), "gain": gain, "checks": checks})
    out.sort(key=lambda m: (-m["gain"], -m["fit"]))
    keep, seen = [], {}
    for m in out:                                         # build + yuva başına en iyi 2 öneri
        k = (m["build"], m["slot"])
        if seen.get(k, 0) < per_slot:
            keep.append(m); seen[k] = seen.get(k, 0) + 1
    return keep


def target_loot_today(week, day=None):
    """[(etkinlik, [hedef loot], görev listesi)] — bugünün hedefli loot'u."""
    day = day or time.strftime("%Y-%m-%d", time.gmtime())
    out = []
    for ev, rows in (week or {}).get("target_loot", {}).items():
        for row in rows or []:
            days = row.get("target_loot_by_day") or []
            today = next((d for d in days if d.get("day") == day), days[-1] if days else None)
            if today:
                out.append((ev, today.get("target_loot", []), row.get("missions", []), today.get("day")))
    return out
