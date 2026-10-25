"""Eşya kütüphanesini The Division Wiki'den tamamlar (meta/game_data.json).

Toplananlar (yalnız The Division 2):
  - tüm markalar (Brand Sets): bonuslar, 6 yuvanın parça adları, markanın named eşyaları
  - tüm gear set'ler: bonuslar, parça adları
  - exotic ve named eşya/silah adları (kütüphanede olmayanlar)
Var olan kayıtlar silinmez, yalnız eksikler eklenir.

    python scripts/build_library.py            # meta/game_data.json'u günceller
    python scripts/build_library.py --dry      # yalnız raporlar

Kaynak: The Division Wiki (thedivision.fandom.com), CC BY-SA 3.0.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import gamedata  # noqa: E402

API = "https://thedivision.fandom.com/api.php"
UA = {"User-Agent": "TD2-Loot-Advisor library builder (https://github.com/FEDERALTURK/td2-loot-advisor)"}
D2 = re.compile(r"Tom Clancy's The Division 2|\(The Division 2\)|\bTD2\b|Warlords of New York|Year \d|Y\d+S\d", re.I)

# yuva anahtar sözcükleri (parça adından yuva çıkarmak için; yalnız bu betikte, OCR'de değil)
SLOT_WORDS = [
    ("Mask", r"mask|helmet|balaclava|respirator|goggles|face|hood|visor|cap|muzzle|snout|headgear|shades"),
    ("Backpack", r"backpack|pack|bag|rucksack|go-bag|kit|satchel|frame|loadout frame|quiver pack|back"),
    ("Chest", r"vest|chest(plate)?|body armou?r|plate carrier|harness|armou?r|jacket|parka|carrier|plate|cage|cuirass|breastplate"),
    ("Gloves", r"gloves?|gauntlets?|grips?|hands|claws|fist guards?|knuckles|mitts|hand protectors?"),
    ("Holster", r"holster|rig|sling|belt|sidearm mount|mount|quiver|sheath|holster system|holder|pouch"),
    ("Kneepads", r"knee ?pads?|knee guards?|knees|kneepads|pads|leggings|pants|trousers|stride|poleyn|greaves|kneelers|collision guards"),
]


UNSLOTTED = []


def api(**params):
    params.setdefault("format", "json")
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            time.sleep(2 + attempt * 2)
    raise RuntimeError("wiki API failed: " + url)


def members(cat):
    out, cont = [], {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle="Category:" + cat, cmlimit=500, cmtype="page", **cont)
        out += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" not in d: return out
        cont = {"cmcontinue": d["continue"]["cmcontinue"]}


def wikitext(title):
    d = api(action="parse", page=title, prop="wikitext", redirects=1)
    return (d.get("parse") or {}).get("wikitext", {}).get("*", "")


def _tpl(body):
    parts = [p.strip() for p in body.split("|")]
    if len(parts) < 2: return ""
    return parts[1] if parts[0].lower() in ("color", "colour") else parts[-1]   # {{color|metin|sınıf}}


def plain(s):
    """Wiki işaretlerini temizle: {{High-end|A|B}} → B, [[A|B]] → B, '''x''' → x."""
    for _ in range(3):                                       # iç içe şablonlar: son parametre metindir
        s = re.sub(r"\{\{([^{}]*)\}\}", lambda m: _tpl(m.group(1)), s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip(" *:-")


def slot_of(name):
    n = name.lower()
    # en sondaki yuva sözcüğü kazanır ("Harness Pack" → Backpack, "Plate Carrier" → Chest)
    best = None
    for slot, pat in SLOT_WORDS:
        for m in re.finditer(r"\b(?:" + pat + r")\b", n):
            if best is None or m.start() > best[0]: best = (m.start(), slot)
    return best[1] if best else None


def section(text, head):
    m = re.search(r"==+\s*" + head + r"\s*==+(.*?)(?=\n==[^=]|\Z)", text, re.I | re.S)
    return m.group(1) if m else ""


def bonuses_of(text):
    out = []
    for m in re.finditer(r"Set Bonus\s*\((\d)\)\s*:\s*(.+)", text, re.I):
        out.append((int(m.group(1)), plain(m.group(2))))
    return out


def parse_set_page(title, text, kind):
    """{'name', 'bonuses', 'pieces': {name: slot}, 'named': {name: (slot, quality)}}"""
    items = section(text, r"Set items?")
    pieces, named = {}, {}
    cur_slot = None
    for line in items.splitlines():
        if not line.strip().startswith("*"): continue
        depth = len(line) - len(line.lstrip("*"))
        raw = line.lstrip("* ").strip()
        txt = plain(raw)
        if not txt or len(txt) > 60: continue
        is_exotic = bool(re.search(r"\{\{\s*exotic", raw, re.I))
        is_named = is_exotic or bool(re.search(r"'''\s*\[\[", raw)) or bool(re.search(r"\{\{\s*named", raw, re.I))
        if kind == "brand" and depth == 1:
            cur_slot = slot_of(txt.replace(title, "")) or slot_of(txt)       # "Unit Alloys Vest" → Chest
            continue
        slot = (cur_slot if kind == "brand" else None) or slot_of(txt)
        if not slot or txt.upper() == "TBD":
            if txt.upper() != "TBD": UNSLOTTED.append(f"{title}: {txt}")
            continue
        if is_named:
            named[txt] = (slot, "exotic" if is_exotic else "named")          # main() kütüphaneye göre düzeltir
        else:
            pieces[txt] = slot
    return {"name": title, "bonuses": bonuses_of(section(text, r"Set completion bonus(es)?") or text),
            "pieces": pieces, "named": named}


def main(dry=False):
    path = ROOT / "meta" / "game_data.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    known = lambda key: {gamedata.nrm(x) for x in data.get(key, [])}
    items = data.setdefault("items", {})
    known_items = {gamedata.nrm(k) for k in items}
    report = {"brands": [], "gear_sets": [], "pieces": 0, "named": [], "exotic": [], "skipped": []}

    def canon_brand(title):
        # wiki adı ↔ kütüphanedeki ad ("Česká Výroba S.R.O." ↔ "Česká Výroba s.r.o.")
        for b in data["brands"]:
            if gamedata.nrm(b) == gamedata.nrm(title): return b
        return title

    def add_items(res, kind):
        base = res["name"]
        for nm, slot in res["pieces"].items():
            if gamedata.nrm(nm) in known_items or gamedata.nrm(nm) == gamedata.nrm(base): continue
            rec = {"slot": slot, "quality": "high-end" if kind == "brand" else "gear set"}
            rec["brand" if kind == "brand" else "gear_set"] = base
            items[nm] = rec; known_items.add(gamedata.nrm(nm)); report["pieces"] += 1
        for nm, (slot, q) in res["named"].items():
            if q == "exotic" and gamedata.nrm(nm) not in known("exotics"): q = "named"   # {{exotic}} renk şablonu
            if gamedata.nrm(nm) not in known_items:
                rec = {"slot": slot, "quality": q}
                if kind == "brand": rec["brand"] = base
                items[nm] = rec; known_items.add(gamedata.nrm(nm))
            key = "exotics" if q == "exotic" else "named"
            if gamedata.nrm(nm) not in known(key):
                data.setdefault(key, []).append(nm); report["exotic" if q == "exotic" else "named"].append(nm)

    # --- markalar: kategori + kütüphanedeki her marka (kategori eksik olabilir: "Unit Alloys" kategoride yok)
    brand_titles = members("Brand Sets")
    have = {gamedata.nrm(t) for t in brand_titles}
    for b in list(data["brands"]):
        if gamedata.nrm(b) not in have: brand_titles.append(b); have.add(gamedata.nrm(b))
    for title in brand_titles:
        text = wikitext(title)
        if not D2.search(text[:1500]): report["skipped"].append(title); continue
        res = parse_set_page(title, text, "brand")
        name = canon_brand(title); res["name"] = name
        if gamedata.nrm(name) not in known("brands"):
            data["brands"].append(name); report["brands"].append(name)
        bb = [b for _, b in sorted(res["bonuses"])]
        if bb and name not in data.setdefault("brand_bonuses", {}):
            data["brand_bonuses"][name] = [re.sub(r"^\+", "", b) for b in bb]
        add_items(res, "brand")
        time.sleep(0.3)

    # --- gear set'ler (TD1 sayfaları atlanır; "(The Division 2)" sürümü varsa o okunur)
    titles = members("Gear Sets")
    have = {gamedata.nrm(t.replace(" (The Division 2)", "")) for t in titles}
    for g in data["gear_sets"]:
        if gamedata.nrm(g) not in have: titles.append(g); have.add(gamedata.nrm(g))
    for title in titles:
        if title.startswith("Gear Sets/"): continue
        if title + " (The Division 2)" in titles: continue          # TD1 sayfası; TD2 sürümü ayrıca okunur
        text = wikitext(title)
        head = text[:2000]
        if "(Weapon Gear Set)" in title or (not D2.search(head)) or re.search(r"in ''\[\[Tom Clancy's The Division\]\]''", head) and not re.search(r"Division 2", head):
            report["skipped"].append(title); continue
        name = title.replace(" (The Division 2)", "")
        name = next((g for g in data["gear_sets"] if gamedata.nrm(g) == gamedata.nrm(name)), name)
        res = parse_set_page(name, text, "gear_set")
        if gamedata.nrm(name) not in known("gear_sets"):
            data["gear_sets"].append(name); report["gear_sets"].append(name)
        if res["bonuses"]:
            data.setdefault("gear_set_bonuses", {}).setdefault(name, [b for _, b in sorted(res["bonuses"])])
        add_items(res, "gear_set")
        time.sleep(0.3)

    # --- exotic eşyalar (kategori) ve named silahlar. Kategori named eşyaları da içerir: sayfa "exotic" demeli.
    wnames = {gamedata.nrm(k) for k in data.get("weapon_index", {})}
    def known_any(n):
        n = gamedata.nrm(re.sub(r"\s*\(.*?\)\s*$", "", n))
        return n in known("exotics") or n in known("named") or n in known_items or n in wnames
    EXO = re.compile(r"is an?\s+(?:'{3}|\[\[|\{\{|[\w ]*\|)*\s*exotic", re.I)
    for title in members("Exotic"):
        if "/" in title or " in " in title or known_any(title): continue
        text = wikitext(title)
        head = text[:2500]
        if not D2.search(head) or not EXO.search(head): continue
        name = re.sub(r"\s*\(.*?\)\s*$", "", title)
        data["exotics"].append(name); report["exotic"].append(name)
        m = re.search(r"exotic\W*(mask|backpack|chest|vest|body armou?r|gloves|holster|knee ?pads)", head, re.I)
        if m:
            sl = m.group(1).lower()
            sl = "Chest" if sl in ("vest", "chest") or "arm" in sl else ("Kneepads" if "knee" in sl else sl.title())
            items[name] = {"slot": sl, "quality": "exotic"}; known_items.add(gamedata.nrm(name))
        time.sleep(0.3)
    for title in members("Named Weapons"):
        if "/" in title or known_any(title): continue
        text = wikitext(title)
        if not D2.search(text[:1500]): continue
        name = re.sub(r"\s*\(.*?\)\s*$", "", title)
        data["named"].append(name); report["named"].append(name)
        time.sleep(0.3)

    slots = data.setdefault("slots", {})
    for w, s in (("chestplate", "Chest"), ("harness", "Chest"), ("plate carrier", "Chest")):
        slots.setdefault(w, s)
    v = str(data.get("version", ""))
    today = time.strftime("%Y-%m-%d")
    data["version"] = f"{today}.{int(v.split('.')[-1]) + 1 if v.startswith(today) and v.split('.')[-1].isdigit() else 1}"
    src = data.get("source", "")
    if "library builder" not in src:
        data["source"] = (src + " + wiki library builder (brand/gear set pieces)").strip(" +")

    print(f"brands +{len(report['brands'])}: {report['brands']}")
    print(f"gear sets +{len(report['gear_sets'])}: {report['gear_sets']}")
    print(f"pieces +{report['pieces']}  named +{len(report['named'])}  exotic +{len(report['exotic'])}")
    print("named:", report["named"][:60]); print("exotic:", report["exotic"][:60])
    print(f"skipped (not TD2): {len(report['skipped'])}")
    print("no slot found:", UNSLOTTED)
    print(f"totals: brands {len(data['brands'])}, gear sets {len(data['gear_sets'])}, items {len(items)}, "
          f"named {len(data['named'])}, exotics {len(data['exotics'])}")
    if not dry:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print("written", path)
    return report


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
