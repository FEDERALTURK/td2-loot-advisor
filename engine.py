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
import itempolicy

WEAPON_WORDS = {  # build adındaki kısaltmalardan silah türü tahmini
    "assault rifle": ["ar", "assault rifle", "st elmo", "st. elmo", "police m4", "famas", "carbine"],
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


def find_card(img, ocr_data_fn, preprocess=True):
    """Eşya kartının (x0, y0, x1, y1) sınırları ya da None. img: tüm ekran ya da seçilen bölge.
    preprocess=False: OCR motoru ham renkli görüntüyü daha iyi okuyorsa (RapidOCR)."""
    from PIL import Image
    W, H = img.size
    k = max(1, -(-W // 1400))                                   # 3440 → 1147 px genişlikte ara
    small = img.resize((W // k, H // k), Image.BILINEAR) if k > 1 else img
    pre = gamedata.text_image(small) if preprocess else small
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
    # kartın başlığı: sağ üstte "RANK" yazar. Bölüm başlıkları (Core/Attributes) çok aşağıdaysa (uzun set
    # açıklaması) başlık kırpılıyordu → aynı kartın RANK'ı varsa üst sınır oradan
    ranks = [w for w in words if w[0] == "rank" and x0 - 0.01 * W <= w[1] <= x0 + 0.32 * W and w[2] < top]
    if ranks:
        top = min(top, min(r[2] for r in ranks))
    # kartın genişliği: başlık sütunundan sağa doğru, aynı satırlardaki kelimelerin en sağı
    # tam ekranda kart ekranın ~%17'si: sağdaki başka paneller karışmasın diye 0.30W ile sınırla.
    # Kırpılmış kart / küçük bölge verildiyse (W < 1600 px) kart görüntünün büyük kısmıdır: sınır yok.
    reach = 0.30 * W if W >= 1600 else W
    inside = [w for w in words if x0 - 0.01 * W <= w[1] <= x0 + reach and w[2] >= top - 0.25 * H]
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
    # "rifle" tek başına: "marksman rifle" / "assault rifle" içindeki rifle sayılmaz (Hotshot sniper build'i ≠ M16A2)
    text_r = re.sub(r"\b(marksman|assault)\s+rifles?\b", r"\1_rifle", text)
    for typ, keys in WEAPON_WORDS.items():
        src = text_r if typ == "rifle" else text
        if any(re.search(r"(?<![a-z_])" + re.escape(k) + r"(?![a-z_])", src) for k in keys):
            found.append(typ)
    return found


def item_weapon_type(item, text):
    low = gamedata.nrm(text)
    for typ in ("light machine gun", "light machinegun", "submachine gun", "assault rifle", "marksman rifle",
                "shotgun", "pistol", "rifle"):
        if typ in low:
            return "light machine gun" if typ == "light machinegun" else typ
    return None


def normalize_build(build, game):
    """Build verisini oyun kütüphanesine göre düzeltir: talent listesine yazılmış eşya adlarını (named/egzotik:
    Equalizer, Chainkiller, Kingbreaker, Catharsis …) 'items' listesine taşır; kütüphanede olmayan talent'leri
    'unknown' olarak işaretler. Dönüş: (değişti mi, bilinmeyenler)."""
    if not game or not game.ok: return False, []
    tal_names = {gamedata.nrm(n) for n, _, _ in game.talents}
    item_names = {n: canon for n, canon, kind in game.names if kind in ("exotic", "named", "weapon")}
    changed, unknown = False, []
    items = list(build.get("items", []))
    for t_name in list(build.get("talents", {})):
        n = gamedata.nrm(t_name)
        core = re.sub(r"^perfect(ly)? ", "", n)
        if n in tal_names or core in tal_names:
            continue
        if n in item_names:
            items.append(item_names[n]); build["talents"].pop(t_name); changed = True
        else:
            unknown.append(t_name)
    if items != build.get("items", []):
        build["items"] = list(dict.fromkeys(items)); changed = True
    return changed, unknown


def build_mentions(build, name):
    """Egzotik/named eşyanın adı build'de geçiyor mu (set listesi, talent, açıklama)?"""
    n = gamedata.nrm(name)
    if len(n) < 4: return False
    hay = " ".join([build.get("name", "")] + build.get("sets_or_brands", []) + list(build.get("talents", {})) + build.get("items", []) +
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
CORE_ATTRS = ("weapon_damage", "armor", "skill_tier")
TALENT_SLOTS = ("Chest", "Backpack")


def _q(item, k, r, game):
    v = item["attrs"][k]
    good = float(r.get("good_at") or 0) or (game.max_of(k) or 0) * 0.9
    return (min(1.0, v / good) if good else item.get("quality", {}).get(k, 100) / 100), v


def score_gear(item, build, low, game):
    """(yüzde, gerekçeler). Eşyanın TAŞIYABİLECEĞİ şeylere göre puanlar:
    - set/marka (build'deki set, marka ya da build'de adı geçen named/egzotik),
    - 1 çekirdek (core) attribute: build'in tercih ettiği çekirdek mi,
    - küçük attribute'lar: gear set parçasında 1, marka/named/egzotikte 2 yuva — build'in en önemli
      attribute'larıyla karşılaştırılır (ulaşılamayacak tam puan istenmez),
    - talent yalnızca göğüs/sırt çantasında (ve kartta talent varsa) sayılır.
    Uzmanlık (expertise) bonusları attribute değildir ve sayılmaz."""
    why = []
    if build.get("slots") and item.get("slot") and item["slot"] not in build["slots"]:
        return 0, ["slot ✗"]
    parts = []                                                # (ağırlık, 0-1)
    attrs = build.get("attributes", {})
    name_n = gamedata.nrm(item.get("name", ""))
    listed = any(gamedata.nrm(x) == name_n for x in build.get("items", [])) and len(name_n) > 3
    set_known = bool(item.get("brand") or item.get("gear_set") or item.get("known") in ("exotic", "named"))
    hit = set_hit(item, build, low)
    if listed:
        parts.append((30, 1.0)); why.append(f"✔ {item['name']}")
    elif build.get("sets_or_brands") and set_known:           # set/marka okunamadıysa (kart kaydırılmış) puanlanmaz
        # set build'leri 4 set parçası + 2 serbest yuva kullanır: başka marka/set parçası "serbest yuva" adayıdır
        parts.append((30, 1.0 if hit else 0.35))
        why.append(f"✔ {hit}" if hit else "set ✗ (flex)")
    # çekirdek
    cores = sorted(((k, r) for k, r in attrs.items() if k in CORE_ATTRS), key=lambda kv: -float(kv[1].get("weight", 1)))
    have_core = [k for k in item.get("attrs", {}) if k in CORE_ATTRS]
    if cores and have_core:
        want = cores[0][0]
        k = have_core[0]
        if k in attrs:
            q, v = _q(item, k, attrs[k], game)
            rel = float(attrs[k].get("weight", 1)) / max(float(cores[0][1].get("weight", 1)), 0.1)
            parts.append((25, q * min(1.0, rel))); why.append(f"{k} {v:g} ({round(q * 100)}%)")
        else:
            parts.append((25, 0.0)); why.append(f"core {k} ✗ ({want})")
    # küçük attribute'lar
    minors_b = sorted(((k, r) for k, r in attrs.items() if k not in CORE_ATTRS), key=lambda kv: -float(kv[1].get("weight", 1)))
    n_slots = 1 if (item.get("gear_set") and not item.get("brand")) else 2
    ideal = sum(float(r.get("weight", 1)) for _, r in minors_b[:n_slots])
    have = [(k, attrs[k]) for k in item.get("attrs", {}) if k not in CORE_ATTRS and k in attrs]
    if ideal:
        got = 0.0
        for k, r in sorted(have, key=lambda kv: -float(kv[1].get("weight", 1)))[:n_slots]:
            q, v = _q(item, k, r, game)
            got += float(r.get("weight", 1)) * q; why.append(f"{k} {v:g} ({round(q * 100)}%)")
        parts.append((35, min(1.0, got / ideal)))
    # talent
    tals = build.get("talents", {})
    slot = item.get("slot")
    if tals and (slot in TALENT_SLOTS or (not slot and item.get("talents"))):
        top = max(tals.values())
        have_t = {gamedata.nrm(x) for x in item.get("talents", [])}
        hits = [(n, w) for n, w in tals.items() if gamedata.nrm(n) in have_t]
        if listed and not hits: hits = [(item["name"], top)]
        if hits:
            n, w = max(hits, key=lambda h: h[1]); parts.append((15, w / top)); why.append(f"talent {n}")
        else:
            parts.append((15, 0.0))
    tot = sum(w for w, _ in parts)
    pct = round(100 * sum(w * v for w, v in parts) / tot) if tot else 0
    return pct, why


def score_mod(item, build, game):
    """Gear mod: modun istatistiği build'de isteniyor mu, rulo ne kadar iyi?"""
    vals = dict(item.get("attrs", {})); vals.update(item.get("mod_attrs", {}))
    best, why = 0, []
    for k, v in vals.items():
        r = build.get("attributes", {}).get(k)
        if not r: continue
        mx = game.max_of(k) or v
        q = min(1.0, v / mx) if mx else 1.0
        sc = round(100 * q * min(1.0, 0.55 + 0.15 * float(r.get("weight", 1))))
        if sc > best: best, why = sc, [f"{k} {v:g} ({round(q * 100)}%)"]
    return best, why


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
        if item.get("kind") == "gear_mod":
            pct, why = score_mod(item, b, game)
        elif item.get("kind") in ("weapon_mod", "skill_mod", "cosmetic", "material", "consumable", "cache"):
            pct, why = 0, []
        elif item.get("kind") == "weapon":
            pct, why = score_weapon(item, b, text, game)
        else:
            pct, why = score_gear(item, b, low, game)
        res.append((pct, b["name"], why))
    res.sort(key=lambda r: r[0], reverse=True)
    return res


def decide(item, res, cfg):
    """(karar, not anahtarı, not parametreleri)."""
    if isinstance(item, dict) and item.get("partial"):
        return "REVIEW", "note.partial_card", {}
    if not itempolicy.item_valid(item):
        return "REVIEW", "note.no_item", {}
    st = cfg["settings"]
    best = res[0][0] if res else 0
    kind = item.get("kind")
    if kind in ("weapon_mod", "skill_mod", "cosmetic", "material", "consumable", "cache"):
        return "REVIEW", "note.kind_" + kind, {}               # build kararı gerekmeyen eşya: kırma önerilmez
    if item.get("spec"):
        return "KEEP", "note.spec_weapon", {"spec": item["spec"]}
    if itempolicy.is_protected_item(item):
        users = [b["name"] for b in cfg["builds"] if build_mentions(b, item.get("name", ""))]
        if users:
            return "KEEP", "note.rare_used", {"builds": ", ".join(users[:2])}
        if best >= st["keep_threshold"]:
            return "KEEP", None, {}
        return "REVIEW", "note.rare_unused", {}
    if best >= st["keep_threshold"]:
        return "KEEP", None, {}
    if best >= st["consider_threshold"]:
        return "CONSIDER", None, {}
    return "DISMANTLE", None, {}


# ---------------------------------------------------------------- build planı (yuva yuva ayrıntı)
SET_SLOT_ORDER = ["Mask", "Gloves", "Holster", "Kneepads", "Backpack", "Chest"]


def _talent_slot(game, name):
    core = re.sub(r"^perfect(ly)? ", "", gamedata.nrm(name))
    for t_name, d in game.data.get("gear_talent_slots", {}).items():
        if gamedata.nrm(t_name) in (core, gamedata.nrm(name)):
            return d.get("slot"), d.get("kind")
    return None, None


def build_plan(build, game):
    """Build'in her yuvası için ne aranmalı: {slot: {"kind", "source", "core", "attrs", "talent", "item"}}.
    - Build'de adı geçen named/egzotik eşyalar kendi yuvasına,
    - gear set varsa 4 parça set (göğüs/sırt çantası set talent'i istenirse onlar da set),
    - kalan yuvalar 'serbest' (build'in markaları ya da herhangi bir marka, doğru çekirdek + attribute),
    - göğüs/sırt çantasına uygun talent, silah yuvalarına tür + silah talent'i."""
    game_ok = bool(game and game.ok)
    attrs = build.get("attributes", {})
    srt = sorted(attrs.items(), key=lambda kv: -float(kv[1].get("weight", 1)))
    cores = [k for k, _ in srt if k in CORE_ATTRS]
    minors = [k for k, _ in srt if k not in CORE_ATTRS]
    core = cores[0] if cores else None
    gs_names = {gamedata.nrm(x) for x in (game.data.get("gear_sets", []) if game_ok else [])}
    br_names = {gamedata.nrm(x) for x in (game.data.get("brands", []) if game_ok else [])}
    sets = [s for s in build.get("sets_or_brands", []) if gamedata.nrm(s) in gs_names]
    brands = [s for s in build.get("sets_or_brands", []) if gamedata.nrm(s) in br_names]
    if not sets and not brands:                         # kütüphane yoksa ya da ad kısaltılmışsa: ilk ad set sayılır
        sets = build.get("sets_or_brands", [])[:1]
    slots = build.get("slots") or ALL_SLOTS
    plan = {s: {"kind": "off"} for s in ALL_SLOTS}
    for s in slots: plan[s] = {"kind": "any", "source": brands[:3], "core": core, "attrs": minors[:2], "talent": None, "item": None}
    # 1) adı geçen eşyalar (items listesi + build adı ve açıklamasında geçen named/egzotik adlar)
    witems = []
    named_list = list(build.get("items", []))
    if game_ok:
        summ = (build.get("meta", {}).get("summary") or build.get("summary") or {})
        hay = gamedata.nrm(build.get("name", "") + " " + str(summ.get("en", "") if isinstance(summ, dict) else summ))
        for n, canon, kind in game.names:
            if kind in ("exotic", "named") and len(n) >= 5 and re.search(r"(?<![a-z])" + re.escape(n) + r"(?![a-z])", hay) \
                    and canon not in named_list:
                named_list.append(canon)
    for it in named_list:
        info = game.items.get(gamedata.nrm(it)) if game_ok else None
        winfo = game.weapon_index.get(gamedata.nrm(it)) if game_ok else None
        if info and info.get("slot") in plan and plan[info["slot"]]["kind"] == "any":
            p = plan[info["slot"]]
            p.update(kind="item", item=it, source=[it], talent=info.get("talent"))
        elif winfo:
            witems.append((it, winfo))
    # 2) talent'ler: göğüs / sırt çantası
    tals = sorted(build.get("talents", {}).items(), key=lambda kv: -kv[1])
    set_talent_slots = []
    for name, _w in tals:
        slot, kind = _talent_slot(game, name) if game_ok else (None, None)
        if slot in ("Chest", "Backpack") and slot in plan and plan[slot]["kind"] in ("any", "item") and not plan[slot].get("talent"):
            plan[slot]["talent"] = name
            if kind == "gear_set": set_talent_slots.append(slot)
    # 3) gear set: 4 parça
    if sets:
        need, order = 4, set_talent_slots + [s for s in SET_SLOT_ORDER if s not in set_talent_slots]
        for s in order:
            if need and s in slots and plan[s]["kind"] == "any":
                plan[s].update(kind="set", source=sets[:1], attrs=minors[:1]); need -= 1
    # 4) silahlar
    wtal = [n for n, _ in tals if game_ok and gamedata.nrm(re.sub(r"(?i)^perfect(ly)? ", "", n)) in
            {gamedata.nrm(x) for x in game.data.get("weapon_talents", [])}]
    types = weapon_types_of(build)
    if "Weapon" in plan and plan["Weapon"]["kind"] != "off":
        w = next(((n, i) for n, i in witems if i.get("type", "").lower() != "pistol"), None)
        plan["Weapon"].update(kind="item" if w else "weapon", item=w[0] if w else None, source=[w[0]] if w else [],
                              types=[TYPE_LABEL.get(x, x) for x in types if x != "pistol"] or ([w[1]["type"]] if w else []),
                              core=None, attrs=[k for k in minors if k in ("crit_chance", "crit_damage", "headshot_damage")][:2],
                              talent=wtal[0] if wtal else None)
    if "Sidearm" in plan and plan["Sidearm"]["kind"] != "off":
        p = next(((n, i) for n, i in witems if i.get("type", "").lower() == "pistol"), None)
        plan["Sidearm"].update(kind="item" if p else "weapon", item=p[0] if p else None, source=[p[0]] if p else [],
                               types=["Pistol"], core=None, attrs=[], talent=None)
    return plan


def check_slot(item, req, game=None):
    """Eşya bu yuvanın şartlarını karşılıyor mu? [(etiket, durum, ayrıntı)] — durum: True / False / None (bilinmiyor)."""
    out = []
    if not req or req.get("kind") == "off":
        return out
    have = [gamedata.nrm(x) for x in (item.get("brand"), item.get("gear_set"), item.get("name") if isinstance(item.get("name"), str) else item.get("item")) if x]
    if req.get("source"):
        ok = any(gamedata.nrm(s) == h or (len(gamedata.nrm(s)) > 4 and gamedata.nrm(s) in h) for s in req["source"] for h in have)
        out.append(("source", ok if have else None, " / ".join(req["source"])))
    if req.get("types"):
        wt = (item.get("weapon_type") or "").lower()
        out.append(("type", (wt in [x.lower() for x in req["types"]]) if wt else None, " / ".join(req["types"])))
    a = item.get("attrs", {}); q = item.get("quality", {})
    if req.get("core"):
        out.append(("core", req["core"] in a, req["core"] + (f" {a[req['core']]:g}" if req["core"] in a else "")))
    for k in req.get("attrs", []):
        out.append(("attr", (q.get(k, 100) >= 80) if k in a else False,
                    k + (f" {a[k]:g} ({q.get(k, '?')}%)" if k in a else "")))
    if req.get("talent"):
        tn = gamedata.nrm(re.sub(r"(?i)^perfect(ly)? ", "", req["talent"]))
        ht = [gamedata.nrm(re.sub(r"(?i)^perfect(ly)? ", "", x)) for x in item.get("talents", [])]
        out.append(("talent", tn in ht if ht or item.get("talents") is not None else None, req["talent"]))
    return out


def slot_done(checks):
    """Tüm şartlar tamam mı (bilinmeyenler sayılmaz)?"""
    known = [c for c in checks if c[1] is not None]
    return bool(known) and all(c[1] for c in known)


# ---------------------------------------------------------------- envanter listesinde seçili satır
def _is_select(px):
    """Oyunun seçili satır vurgusu: turuncu (sağ taraf) ya da sarı-yeşil degrade (sol taraf)."""
    r, g, b = px[:3]
    return (r > 200 and 80 < g < 200 and b < 90) or (r > 150 and g > 160 and b < 90 and abs(r - g) < 70)


def find_selected_row(img, card_box):
    """Kartın solundaki envanter listesinde seçili (vurgulu) satırın kutusu ya da None.
    Kart aşağı kaydırılınca eşyanın adı kartta görünmez; listedeki seçili satırda ad + marka/set her zaman yazar."""
    if not card_box: return None
    W, H = img.size
    x0, y0, x1, y1 = card_box
    cw = max(1, x1 - x0)
    sx0, sx1 = max(0, int(x0 - 1.25 * cw)), max(0, int(x0 - 0.01 * W))
    if sx1 - sx0 < 0.25 * cw: return None
    sy0, sy1 = 0, H                                       # liste kartın çok üstünde/altında da olabilir (kaydırılmış kart)
    strip = img.crop((sx0, sy0, sx1, sy1)).convert("RGB")
    k = max(1, strip.width // 200)                        # hız: her k. piksel
    sw, sh = strip.size
    px = strip.load()
    cover = []
    for y in range(sh):
        n = sum(1 for x in range(0, sw, k) if _is_select(px[x, y]))
        cover.append(n / max(1, (sw + k - 1) // k))
    best, cur = None, None
    for y, c in enumerate(cover + [0]):
        if c >= 0.35:
            cur = (cur[0], y) if cur else (y, y)
        elif cur:
            if best is None or cur[1] - cur[0] > best[1] - best[0]: best = cur
            cur = None
    if not best: return None
    h = best[1] - best[0]
    if h < 0.025 * H or h > 0.2 * H: return None
    # satırın yatay sınırı: vurgunun bulunduğu sütunlar
    cols = [x for x in range(0, sw, k) if sum(1 for y in range(best[0], best[1], max(1, h // 12)) if _is_select(px[x, y])) >= 3]
    if not cols: return None
    return (sx0 + cols[0], sy0 + best[0], sx0 + cols[-1] + k, sy0 + best[1] + 1)


def parse_row_text(lines):
    """Seçili satırın OCR satırlarından (ad, marka/set). 'LEVEL 40', yüzdeler ve attribute satırları atılır."""
    out = []
    for l in lines:
        t = re.sub(r"\s+", " ", (l or "")).strip(" .,:;|")
        t = re.sub(r"(?i)\s*\b(level|rank)\b.*$", "", t)              # "Striker's Pack LEVEL" → ad
        t = re.sub(r"\s+\d{1,3}$", "", t).strip(" .,:;|")             # "Striker's Battlegear 40" → set
        if len(t) < 3 or re.search(r"[%+]|^\d", t) or sum(ch.isalpha() for ch in t) < 3: continue
        out.append(t)
    return (out[0] if out else None), (out[1] if len(out) > 1 else None)


def list_hint(img, card_box, lines_fn):
    """Kart başlığı görünmüyorsa: listedeki seçili satırdan (ad, marka/set, satır kutusu). lines_fn(img) -> [(metin, kutu, güven)]."""
    row = find_selected_row(img, card_box)
    if not row: return None
    try:
        lines = [l for l, _, _ in lines_fn(img.crop(row))]
    except Exception:
        return None
    name, sub = parse_row_text(lines)
    if not name: return None
    return {"name": name, "sub": sub, "box": row, "lines": lines}
