"""Karar motoru v2 + eşya kartı bulucu (21:9 / 3440×1440 dahil her çözünürlük).

- find_card(): tüm ekran görüntüsünde eşya kartını (Core Stats / Attributes / Talents / Mods
  başlıklarının hizasından) bulur ve tam sınırlarını (sol, üst, sağ, alt) döndürür. Bölge seçmek
  zorunlu değildir; 3440×1440 gibi geniş ekranlarda kart nerede açılırsa açılsın bulunur.
- score_gear() / score_weapon(): build'e göre puan; attribute'lar oyundaki en yüksek değere göre
  (rulo kalitesi) değerlendirilir, set/marka ve talent eşleşmesi ayrı ayrı açıklanır.
- decide(): SAKLA / DÜŞÜN / KIR / KONTROL ET kararı + kısa gerekçe.
Oyunun belleğine dokunulmaz.
"""
import re

import gamedata

WEAPON_WORDS = {  # build adındaki kısaltmalardan silah türü tahmini
    "assault rifle": ["ar", "assault", "st elmo", "st. elmo", "police m4", "famas", "carbine"],
    "submachine gun": ["smg", "vector", "ouroboros", "submachine"],
    "light machine gun": ["lmg", "pestilence", "alejandro", "iron lung", "bluescreen", "machine gun"],
    "shotgun": ["shotgun", "fafnir", "acs-12", "close range", "scorpio", "sweet dreams"],
    "marksman rifle": ["sniper", "mmr", "marksman", "hotshot", "model 700", "headhunter"],
    "rifle": ["rifle", "1886", "m1a"],
    "pistol": ["pistol", "regulus", "sidearm"],
}
TYPE_LABEL = {"assault rifle": "Assault Rifle", "submachine gun": "Submachine Gun", "light machine gun": "Light Machine Gun",
              "shotgun": "Shotgun", "marksman rifle": "Marksman Rifle", "rifle": "Rifle", "pistol": "Pistol"}
GEAR_SLOTS = ["Mask", "Chest", "Backpack", "Gloves", "Holster", "Kneepads"]
ALL_SLOTS = GEAR_SLOTS + ["Weapon", "Sidearm"]


# ---------------------------------------------------------------- kart bulma
CARD_ANCHORS = {"core", "attributes", "attribute", "talents", "talent", "mods", "modifications", "stats"}


def find_card(img, ocr_data_fn):
    """Eşya kartının (x0, y0, x1, y1) sınırları ya da None. img: tüm ekran ya da seçilen bölge."""
    from PIL import Image
    W, H = img.size
    k = max(1, -(-W // 1400))                                   # 3440 → 1147 px genişlikte ara
    small = img.resize((W // k, H // k), Image.BILINEAR) if k > 1 else img
    pre = gamedata.text_image(small)
    sc = pre.width / small.width
    d = ocr_data_fn(pre)
    words = []
    for i, w in enumerate(d["text"]):
        w = (w or "").strip()
        if not w: continue
        try: conf = float(d["conf"][i])
        except (TypeError, ValueError): conf = -1
        x, y, ww, hh = (d[k2][i] / sc * k for k2 in ("left", "top", "width", "height"))
        words.append((gamedata.nrm(w), x, y, ww, hh, conf))
    anchors = [w for w in words if w[0] in CARD_ANCHORS and w[5] > 35]
    if not anchors: return None
    # aynı sütunda (sol kenarı yakın) en çok başlığı olan küme = kart
    tol = 0.03 * W
    best = max(anchors, key=lambda a: sum(1 for b in anchors if abs(b[1] - a[1]) < tol))
    col = [a for a in anchors if abs(a[1] - best[1]) < tol]
    x0 = min(a[1] for a in col)
    top = min(a[2] for a in col)
    # kartın genişliği: başlık sütunundan sağa doğru, aynı satırlardaki kelimelerin en sağı
    inside = [w for w in words if x0 - 0.01 * W <= w[1] <= x0 + 0.30 * W and w[2] >= top - 0.25 * H]
    x1 = max((w[1] + w[3] for w in inside), default=x0 + 0.18 * W)
    y1 = max((w[2] + w[4] for w in inside), default=H)
    pad = 0.012 * W
    box = (max(0, int(x0 - pad)), max(0, int(top - 0.22 * H)),
           min(W, int(max(x1, x0 + 0.12 * W) + pad)), min(H, int(y1 + 0.03 * H)))
    if box[2] - box[0] < 0.08 * W or box[3] - box[1] < 0.15 * H:
        return None
    return box


# ---------------------------------------------------------------- yardımcılar
def weapon_types_of(build):
    """Build'in silah türleri: açıkça yazılmışsa onlar, yoksa adından/setinden tahmin."""
    w = build.get("weapons") or {}
    if w.get("types"):
        return [t.lower() for t in w["types"]]
    text = (build.get("name", "") + " " + " ".join(build.get("sets_or_brands", [])) + " " +
            str(build.get("meta", {}).get("summary", {}).get("en", ""))).lower()
    found = []
    for typ, keys in WEAPON_WORDS.items():
        if any(re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", text) for k in keys):
            found.append(typ)
    return found


def item_weapon_type(item, text):
    low = gamedata.nrm(text)
    for typ in ("light machine gun", "light machinegun", "submachine gun", "assault rifle", "marksman rifle",
                "shotgun", "pistol", "rifle"):
        if typ in low:
            return "light machine gun" if typ == "light machinegun" else typ
    return None


def build_mentions(build, name):
    """Egzotik/named eşyanın adı build'de geçiyor mu (set listesi, talent, açıklama)?"""
    n = gamedata.nrm(name)
    if len(n) < 4: return False
    hay = " ".join([build.get("name", "")] + build.get("sets_or_brands", []) + list(build.get("talents", {})) +
                   [str(build.get("meta", {}).get("summary", {}).get("en", ""))])
    return n in gamedata.nrm(hay)


def set_hit(item, build, low):
    have = [gamedata.nrm(x) for x in (item.get("brand"), item.get("gear_set"), item.get("name")) if x]
    for s in build.get("sets_or_brands", []):
        sn = gamedata.nrm(s)
        if not sn: continue
        if any(sn == h or (len(sn) >= 5 and (sn in h or h in sn)) or gamedata.ratio(sn, h) >= 0.86 for h in have):
            return s
        if len(sn) >= 6 and sn in low:
            return s
    return None


# ---------------------------------------------------------------- puanlama
def score_gear(item, build, low, game):
    """(yüzde, gerekçeler). Set/marka eşleşmesi, attribute kalitesi, talent."""
    why, got, mx = [], 0.0, 0.0
    if build.get("slots") and item.get("slot") and item["slot"] not in build["slots"]:
        return 0, ["slot ✗"]
    bonus = float(build.get("set_bonus", 0) or 0)
    if build.get("sets_or_brands"):
        mx += bonus
        hit = set_hit(item, build, low)
        if hit:
            got += bonus; why.append(f"✔ {hit}")
    attrs = build.get("attributes", {})
    for k, r in sorted(attrs.items(), key=lambda kv: -kv[1].get("weight", 0)):
        w = float(r.get("weight", 1)) * 10
        mx += w
        if k in item.get("attrs", {}):
            v = item["attrs"][k]
            good = float(r.get("good_at") or 0) or (game.max_of(k) or 0) * 0.9
            q = min(1.0, v / good) if good else item.get("quality", {}).get(k, 100) / 100
            got += w * q
            why.append(f"{k} {v:g} ({round(q * 100)}%)")
    tals = build.get("talents", {})
    if tals:
        top = max(tals.values())
        mx += top * 10
        have = {gamedata.nrm(x) for x in item.get("talents", [])}
        hits = [(n, w) for n, w in tals.items() if gamedata.nrm(n) in have]
        if hits:
            n, w = max(hits, key=lambda h: h[1]); got += w * 10; why.append(f"talent {n}")
    pct = round(min(100, got / mx * 100)) if mx else 0
    if build.get("sets_or_brands") and (item.get("brand") or item.get("gear_set")) and not set_hit(item, build, low):
        pct = round(pct * 0.6); why.insert(0, "set ✗")          # başka bir set/marka: build'e uymaz
    return pct, why


def score_weapon(item, build, text, game):
    why, got, mx = [], 0.0, 0.0
    types = weapon_types_of(build)
    it = item_weapon_type(item, text)
    mx += 50
    if types and it:
        if it in types or (it == "rifle" and "marksman rifle" in types and "marksman" in gamedata.nrm(text)):
            got += 50; why.append(f"✔ {TYPE_LABEL.get(it, it)}")
        else:
            return 0, [f"{TYPE_LABEL.get(it, it)} ✗"]
    elif not types:
        got += 20                                       # build silah türü belirtmemiş: nötr
    wt = {gamedata.nrm(t): (t, w) for t, w in build.get("talents", {}).items()}
    wtal = (build.get("weapons") or {}).get("talents", {})
    wt.update({gamedata.nrm(t): (t, w) for t, w in wtal.items()})
    weap_names = {gamedata.nrm(n) for n in game.data.get("weapon_talents", [])}
    cand = {k: v for k, v in wt.items() if k.replace("perfect ", "") in weap_names}
    mx += 40
    have = {gamedata.nrm(x) for x in item.get("talents", [])}
    hits = [v for k, v in cand.items() if k in have]
    if hits:
        n, w = max(hits, key=lambda h: h[1]); got += 40 * min(1.0, w / max(v[1] for v in cand.values())); why.append(f"talent {n}")
    elif not cand:
        got += 15
    mx += 10
    qs = [q for k, q in item.get("quality", {}).items() if k in ("crit_chance", "crit_damage", "headshot_damage", "weapon_type_damage")]
    if qs:
        got += 10 * (sum(qs) / len(qs)) / 100
    return round(min(100, got / mx * 100)), why


def evaluate(item, text, cfg, game):
    """[(puan, build adı, gerekçeler)] büyükten küçüğe."""
    low = gamedata.nrm(text)
    res = []
    for b in cfg["builds"]:
        if item.get("kind") == "weapon":
            pct, why = score_weapon(item, b, text, game)
        else:
            pct, why = score_gear(item, b, low, game)
        res.append((pct, b["name"], why))
    res.sort(key=lambda r: r[0], reverse=True)
    return res


def decide(item, res, cfg):
    """(karar, not anahtarı, not parametreleri)."""
    st = cfg["settings"]
    best = res[0][0] if res else 0
    rare = {"EXOTIC", "NAMED"} & set(item.get("rarity", []))
    if rare:
        users = [b["name"] for b in cfg["builds"] if build_mentions(b, item.get("name", ""))]
        if users:
            return "KEEP", "note.rare_used", {"builds": ", ".join(users[:2])}
        if best >= st["keep_threshold"]:
            return "KEEP", None, {}
        return "REVIEW", "note.rare_unused", {}
    if "PROTOTYPE" in item.get("rarity", []) and best >= st["consider_threshold"]:
        return "KEEP", None, {}
    if best >= st["keep_threshold"]:
        return "KEEP", None, {}
    if best >= st["consider_threshold"]:
        return "CONSIDER", None, {}
    return "DISMANTLE", None, {}
