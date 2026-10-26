"""Bilgi içeriği: ansiklopedi dizini, haber/sezon akışı, meta build vitrini yardımcıları ve bilgi yarışması.

Hepsi programın zaten taşıdığı oyun kütüphanesinden (meta/game_data.json + meta/sources) ve günlük akışlardan
(meta/meta_builds.json, meta/tasks_feed.json, meta/news_feed.json) üretilir. Ağ yalnız akışları indirmek içindir.
"""
import json
import random
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

CATEGORIES = ("exotic", "named", "gear_set", "brand", "talent")
SLOT_ORDER = ("Mask", "Chest", "Backpack", "Gloves", "Holster", "Kneepads", "Weapon", "Sidearm")


def _load(paths):
    for p in paths:
        try:
            return json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return {}


def _clean_desc(text, name=""):
    """Wiki metnini sadeleştir: başlık tekrarları, yıldızlar, gereksiz boşluk."""
    if not text: return ""
    s = str(text)
    if "(Tom Clancy's The Division 2)" in s:                     # wiki'de önce ilk oyunun metni olabilir
        s = s.split("(Tom Clancy's The Division 2)", 1)[1]
    s = re.sub(r"\(Tom Clancy's The Division(?: 2)?\)", "", s)
    s = re.sub(r"\b(?:left|right|center)?\|?thumb\|\d+px", "", s)
    s = re.sub(r"\b\d+px\|(?:left|right|center)\b\s*", "", s)
    s = re.sub(r"^\s*Talent\s*-\s*[^•*\n]{0,60}?(?=\s*[•*])", "", s)
    s = s.replace("**", "•").replace("*", "•")
    s = re.sub(r"\s*•\s*", "\n• ", s)
    s = re.sub(r"[ \t]+", " ", s).strip(" •\n")
    if name and s.lower().startswith(name.lower()): s = s[len(name):].strip(" -:\n")
    return s[:1200]


# ---------------------------------------------------------------- ansiklopedi
class Encyclopedia:
    def __init__(self, data, sources_dirs=()):
        self.data = data or {}
        talent_desc, exotic_info = {}, {}
        import csv
        for d in sources_dirs:
            for f, col in (("GearTalents.csv", "Talent"), ("WeaponTalents.csv", "Name")):   # yetenek açıklamaları
                try:
                    with open(Path(d) / "mxswat" / f, encoding="utf-8") as fh:
                        for row in csv.DictReader(fh):
                            if row.get(col) and row.get("Desc"): talent_desc.setdefault(row[col].strip(), row["Desc"].strip())
                except OSError:
                    pass
            talent_desc.update(_load([Path(d) / "wiki_talent_desc.json"]) or {})
            exotic_info.update(_load([Path(d) / "wiki_exotics.json"]) or {})
        self.talent_desc, self.exotic_info = talent_desc, exotic_info
        self.entries = self._build()
        self.by_key = {(e["cat"], e["name"]): e for e in self.entries}

    def _build(self):
        d, out = self.data, []
        items, widx = d.get("items", {}), d.get("weapon_index", {})
        gtal_slot = d.get("gear_talent_slots", {})
        for cat, quality, names in (("exotic", "exotic", d.get("exotics", [])), ("named", "named", d.get("named", []))):
            seen = set()
            for n in list(names) + [w for w, v in widx.items() if v.get("quality") == quality or
                                    (quality == "named" and v.get("quality") == "specialization")]:
                if n in seen: continue
                seen.add(n)
                it, w = items.get(n, {}), widx.get(n, {})
                info = self.exotic_info.get(n, {}) if cat == "exotic" else {}
                talent = it.get("talent") or (info.get("talent") if info.get("talent") not in (None, "Talent") else None)
                desc = _clean_desc(info.get("desc", ""), talent or "") if info else ""
                if not desc and talent: desc = self.talent_desc.get(talent, "")
                out.append({"cat": cat, "name": n, "slot": it.get("slot") or ("Weapon" if w else (info.get("type") or "").title() or None),
                            "weapon_type": w.get("type"), "brand": it.get("brand"), "gear_set": it.get("gear_set"),
                            "talent": talent, "desc": desc})
        for n in d.get("gear_sets", []):
            b = d.get("gear_set_bonuses", {}).get(n, [])
            pieces = sorted((k for k, v in items.items() if v.get("gear_set") == n), key=lambda k: SLOT_ORDER.index(items[k]["slot"]) if items[k].get("slot") in SLOT_ORDER else 9)
            out.append({"cat": "gear_set", "name": n, "bonuses": b, "pieces": [(p, items[p].get("slot")) for p in pieces],
                        "talent": next((x.split(":", 1)[1].strip() for x in b if x.lower().startswith("talent:")), None)})
        for n in d.get("brands", []):
            b = d.get("brand_bonuses", {}).get(n, [])
            named = [k for k, v in items.items() if v.get("brand") == n and v.get("quality") == "named"]
            out.append({"cat": "brand", "name": n, "bonuses": b, "named": named})
        for kind, key in (("gear", "gear_talents"), ("weapon", "weapon_talents")):
            for n in d.get(key, []):
                slot = (gtal_slot.get(n) or {}).get("slot") if kind == "gear" else None
                out.append({"cat": "talent", "name": n, "kind": kind, "slot": slot, "desc": self.talent_desc.get(n, "")})
        return out

    def counts(self):
        c = {k: 0 for k in CATEGORIES}
        for e in self.entries: c[e["cat"]] += 1
        return c

    def search(self, query="", cat=None, slot=None, limit=600):
        q = (query or "").strip().lower()
        res = []
        for e in self.entries:
            if cat and e["cat"] != cat: continue
            if slot and e.get("slot") != slot: continue
            if q:
                hay = " ".join(str(x) for x in (e["name"], e.get("talent"), e.get("desc"), e.get("brand"), e.get("gear_set"),
                                                " ".join(e.get("bonuses") or []), e.get("weapon_type"))).lower()
                if q not in hay: continue
                score = 0 if e["name"].lower().startswith(q) else 1 if q in e["name"].lower() else 2
            else:
                score = 0
            res.append((score, CATEGORIES.index(e["cat"]), e["name"].lower(), e))
        res.sort(key=lambda r: r[:3])
        return [r[3] for r in res[:limit]]

    def related(self, e):
        """Bir girişle ilişkili diğer girişler (set parçaları, markanın adlı eşyaları, aynı yetenek)."""
        out = []
        if e["cat"] in ("exotic", "named"):
            for k in (("gear_set", e.get("gear_set")), ("brand", e.get("brand")), ("talent", e.get("talent"))):
                if k[1] and k in self.by_key: out.append(self.by_key[k])
        elif e["cat"] == "brand":
            out += [self.by_key[("named", n)] for n in e.get("named", []) if ("named", n) in self.by_key]
        elif e["cat"] == "talent":
            out += [x for x in self.entries if x["cat"] in ("exotic", "named") and x.get("talent") == e["name"]]
        elif e["cat"] == "gear_set" and e.get("talent") and ("talent", e["talent"]) in self.by_key:
            out.append(self.by_key[("talent", e["talent"])])
        return out[:12]


# ---------------------------------------------------------------- haber / sezon akışı
NEWS_KINDS = ("patch", "event", "season", "maintenance", "dlc", "community")


def _txt(v, n):
    if isinstance(v, dict):
        return {k[:5]: str(x)[:n] for k, x in v.items() if isinstance(x, str) and re.fullmatch(r"[a-z]{2}(-[A-Z]{2})?", k[:5])}
    return {"en": str(v)[:n]} if v else {}


def _iso(v):
    if not v: return None
    try:
        dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except ValueError:
        return None


def validate_news(feed):
    if not isinstance(feed, dict) or feed.get("schema") != 1: raise ValueError("news schema")
    items = []
    for it in feed.get("items", [])[:60]:
        if not isinstance(it, dict) or not re.fullmatch(r"[a-z0-9\-]{3,60}", str(it.get("id", ""))): continue
        title = _txt(it.get("title"), 140)
        if not title: continue
        url = str(it.get("url") or "")
        items.append({"id": it["id"], "kind": it.get("kind") if it.get("kind") in NEWS_KINDS else "community",
                      "title": title, "text": _txt(it.get("text"), 900), "date": _iso(it.get("date")),
                      "start": _iso(it.get("start")), "end": _iso(it.get("end")),
                      "url": url if url.startswith("https://") else "", "source": str(it.get("source") or "")[:60]})
    return {"version": str(feed.get("version", ""))[:20], "season": str(feed.get("season", ""))[:80], "items": items}


def news_status(item, now=None):
    now = now or datetime.now(timezone.utc)
    s, e = item.get("start"), item.get("end")
    if e and now > e: return "ended"
    if s and now < s: return "upcoming"
    if s or e: return "live"
    return "news"


def news_sorted(items, now=None, keep_ended_days=3):
    now = now or datetime.now(timezone.utc)
    order = {"live": 0, "upcoming": 1, "news": 2, "ended": 3}
    out = []
    for it in items:
        st = news_status(it, now)
        if st == "ended" and it["end"] and now - it["end"] > timedelta(days=keep_ended_days): continue
        key_t = it.get("end") if st == "live" else it.get("start") if st == "upcoming" else it.get("date") or it.get("start")
        out.append((order[st], (key_t or now).timestamp() * (1 if st in ("live", "upcoming") else -1), it, st))
    out.sort(key=lambda r: (r[0], r[1]))
    return [(r[2], r[3]) for r in out]


def pick_lang(d, lang):
    if not d: return ""
    return d.get(lang) or d.get(lang.split("-")[0]) or d.get("en") or next(iter(d.values()))


def next_resets(resets, now=None):
    """(günlük sıfırlama, haftalık sıfırlama) — UTC datetime."""
    now = now or datetime.now(timezone.utc)
    r = resets or {}
    dh, wd, wh = int(r.get("daily_hour_utc", 8)), int(r.get("weekly_weekday", 1)), int(r.get("weekly_hour_utc", 8))
    daily = now.replace(hour=dh, minute=0, second=0, microsecond=0)
    if daily <= now: daily += timedelta(days=1)
    weekly = now.replace(hour=wh, minute=0, second=0, microsecond=0) + timedelta(days=(wd - now.weekday()) % 7)
    if weekly <= now: weekly += timedelta(days=7)
    return daily, weekly


def fmt_left(delta):
    s = max(0, int(delta.total_seconds()))
    d, s = divmod(s, 86400); h, s = divmod(s, 3600); m = s // 60
    return (f"{d}g {h:02d}:{m:02d}" if d else f"{h:02d}:{m:02d}"), (d, h, m)


# ---------------------------------------------------------------- meta build vitrini
def build_tags(b):
    mode = (b.get("mode") or "").lower()
    tags = []
    if "pvp" in mode or "dark zone" in mode or "conflict" in mode: tags.append("pvp")
    if "pve" in mode or "legendary" in mode or "heroic" in mode or "raid" in mode or "incursion" in mode: tags.append("pve")
    if "solo" in mode: tags.append("solo")
    if "group" in mode or "raid" in mode or "incursion" in mode: tags.append("group")
    if "legendary" in mode or "heroic" in mode or "raid" in mode or "incursion" in mode: tags.append("endgame")
    if b.get("role"): tags.append(b["role"])
    return tags


def trend(cur, prev):
    """Popülerlik değişimi: 'up' / 'down' / 'new' / '' ."""
    if prev is None: return "new"
    if cur >= prev + 3: return "up"
    if cur <= prev - 3: return "down"
    return ""


# ---------------------------------------------------------------- bilgi yarışması
class Quiz:
    """Soruları oyun kütüphanesinden üretir: cevap her zaman veriden gelir, uydurma yok.
    Soru metinleri dil dosyasından (quiz.q_*), eşya/marka/yetenek adları oyundaki gibi (İngilizce)."""
    KINDS = ("exotic_slot", "brand_bonus", "set_talent", "weapon_type", "talent_desc", "named_brand")

    def __init__(self, enc, rng=None):
        self.enc, self.rng = enc, rng or random.Random()
        self.d = enc.data

    def _opts(self, right, pool, n=4):
        pool = [p for p in dict.fromkeys(pool) if p and p != right]
        if len(pool) < n - 1: return None
        opts = self.rng.sample(pool, n - 1) + [right]
        self.rng.shuffle(opts)
        return opts

    def make(self, kind=None, tries=30):
        for _ in range(tries):
            q = getattr(self, "_q_" + (kind or self.rng.choice(self.KINDS)))()
            if q: return q
        return None

    def _q_exotic_slot(self):
        ex = [e for e in self.enc.entries if e["cat"] == "exotic" and e.get("slot") in SLOT_ORDER[:6]]
        if not ex: return None
        e = self.rng.choice(ex)
        return {"kind": "exotic_slot", "args": {"name": e["name"]}, "right": e["slot"],
                "options": self._opts(e["slot"], list(SLOT_ORDER[:6]))}

    def _q_brand_bonus(self):
        bb = {k: v for k, v in self.d.get("brand_bonuses", {}).items() if v}
        if len(bb) < 4: return None
        name = self.rng.choice(list(bb))
        right = bb[name][0]
        others = [v[0] for k, v in bb.items() if k != name and v and v[0] != right]
        return {"kind": "brand_bonus", "args": {"name": name}, "right": right, "options": self._opts(right, others)}

    def _q_set_talent(self):
        sets = {}
        for k, v in self.d.get("gear_set_bonuses", {}).items():
            tal = next((x.split(":", 1)[1].strip() for x in v if x.lower().startswith("talent:")), None)
            if tal: sets[k] = tal
        if len(sets) < 4: return None
        name = self.rng.choice(list(sets))
        return {"kind": "set_talent", "args": {"name": name}, "right": sets[name],
                "options": self._opts(sets[name], [v for k, v in sets.items() if k != name])}

    def _q_weapon_type(self):
        w = {k: v["type"] for k, v in self.d.get("weapon_index", {}).items() if v.get("quality") in ("exotic", "named") and v.get("type")}
        if len(w) < 4: return None
        name = self.rng.choice(list(w))
        return {"kind": "weapon_type", "args": {"name": name}, "right": w[name],
                "options": self._opts(w[name], list(self.d.get("weapon_types", [])) or list(set(w.values())))}

    def _q_talent_desc(self):
        td = {k: v for k, v in self.enc.talent_desc.items() if v and len(v) > 30}
        if len(td) < 4: return None
        name = self.rng.choice(list(td))
        desc = td[name]
        for word in re.findall(r"[A-Za-z']+", name):                  # cevabı açık eden kelimeleri gizle
            if len(word) > 3: desc = re.sub(re.escape(word), "▢▢▢", desc, flags=re.I)
        return {"kind": "talent_desc", "args": {"desc": desc[:260]}, "right": name,
                "options": self._opts(name, list(td))}

    def _q_named_brand(self):
        named = [(k, v["brand"]) for k, v in self.d.get("items", {}).items() if v.get("quality") == "named" and v.get("brand")
                 and v["brand"].split()[0].lower() not in k.lower()]
        if not named: return None
        name, brand = self.rng.choice(named)
        return {"kind": "named_brand", "args": {"name": name}, "right": brand,
                "options": self._opts(brand, list(self.d.get("brands", [])))}


def quiz_level(xp):
    """XP → (seviye, bu seviyedeki xp, sonraki seviye için gereken)."""
    lvl, need, x = 1, 50, int(xp)
    while x >= need:
        x -= need; lvl += 1; need = int(need * 1.25)
    return lvl, x, need
