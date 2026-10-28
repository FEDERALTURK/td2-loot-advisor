"""Excel kütüphanesini (meta/TD2_Kutuphane.xlsx) programa işler: meta/game_data.json

Okunan sayfalar ve programdaki karşılıkları:
  Eşyalar            → items (yuva, kalite, marka/set), named / exotics listeleri
  Markalar           → brands, brand_bonuses
  Gear Setler        → gear_sets, gear_set_bonuses
  Exoticler          → exotics, weapon_index (exotic silahlar), items (exotic ekipman)
  Named              → named, weapon_index (named silahlar)
  Silahlar           → weapon_index, weapons
  Ekipman/Silah Talentleri → gear_talents / weapon_talents (+ gear_talent_slots)
  Ekipman Modları    → gear_mods        Silah Modları → weapon_mods        Skilller → skills

Kurallar: Excel'deki değer kütüphanedekinden farklıysa Excel kazanır (düzeltme). Excel'den satır silmek kütüphaneden
silmez. TD1 eşyaları meta/sources/corrections.json ile çıkarılır.

    python scripts/import_library_excel.py [kutuphane.xlsx] [--dry]
"""
import json
import re
import sys
import time
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import gamedata  # noqa: E402
from library_excel import apply_corrections  # noqa: E402

N = gamedata.nrm
SLOT_EN = {"Maske": "Mask", "Sırt çantası": "Backpack", "Göğüslük": "Chest", "Eldiven": "Gloves", "Holster": "Holster", "Dizlik": "Kneepads",
           "Mask": "Mask", "Backpack": "Backpack", "Chest": "Chest", "Gloves": "Gloves", "Kneepads": "Kneepads"}
QUAL_EN = {"high-end": "high-end", "gear set": "gear set", "named": "named", "exotic": "exotic"}
WTYPES = {"Assault Rifle", "Rifle", "Marksman Rifle", "Submachine Gun", "Light Machine Gun", "Shotgun", "Pistol"}


def rows(wb, sheet):
    if sheet not in wb.sheetnames: return []
    ws = wb[sheet]
    it = ws.iter_rows(values_only=True)
    head = [str(h or "").strip() for h in next(it)]
    out = []
    for r in it:
        if not r or not r[0] or not str(r[0]).strip(): continue
        out.append({h: (str(v).strip() if isinstance(v, str) else v) for h, v in zip(head, r)})
    return out


def find_key(dct, name):
    n = N(name)
    return next((k for k in dct if N(k) == n), None)


def main(xlsx, dry=False):
    path = ROOT / "meta" / "game_data.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    orig = json.loads(json.dumps(d))
    corr_p = ROOT / "meta" / "sources" / "corrections.json"
    before = {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in d.items()}
    if corr_p.exists():
        apply_corrections(d, json.loads(corr_p.read_text(encoding="utf-8")))
    wb = load_workbook(xlsx, read_only=True, data_only=True)
    ch = {"items+": 0, "items~": 0, "weapons+": 0, "weapons~": 0, "talents+": 0, "mods+": 0, "lists+": 0, "bonuses~": 0}
    items, windex = d.setdefault("items", {}), d.setdefault("weapon_index", {})

    def add_list(key, name):
        if name and N(name) not in {N(x) for x in d.setdefault(key, [])}:
            d[key].append(name); ch["lists+"] += 1

    def set_item(name, slot, qual, base):
        slot = SLOT_EN.get(slot or "", slot or "")
        qual = QUAL_EN.get((qual or "").lower(), (qual or "").lower())
        if slot not in SLOT_EN.values() or qual not in QUAL_EN: return
        k = find_key(items, name)
        rec = {"slot": slot, "quality": qual}
        if base:
            if qual == "gear set": rec["gear_set"] = base
            elif qual in ("high-end", "named"): rec["brand"] = base
        if k is None:
            items[name] = rec; ch["items+"] += 1
        else:
            old = items[k]
            new = {**old, **rec}
            if qual == "gear set": new.pop("brand", None)
            if new != old: items[k] = new; ch["items~"] += 1

    def set_weapon(name, wtype, qual):
        qual = (qual or "").lower()
        k = find_key(windex, name)
        rec = {}
        if wtype in WTYPES: rec["type"] = wtype
        if qual in ("high-end", "named", "exotic", "specialization"): rec["quality"] = qual
        if not rec: return
        if k is None:
            windex[name] = rec; ch["weapons+"] += 1
            add_list("weapons", name)
        else:
            new = {**windex[k], **rec}
            if new != windex[k]: windex[k] = new; ch["weapons~"] += 1

    # ---- Eşyalar
    for r in rows(wb, "Eşyalar"):
        set_item(r["Eşya adı"], r.get("Yuva"), r.get("Kalite"), r.get("Marka / Set"))
        q = (r.get("Kalite") or "").lower()
        if q == "exotic": add_list("exotics", r["Eşya adı"])
        elif q == "named": add_list("named", r["Eşya adı"])
        if r.get("Talent") and q in ("named", "exotic"):
            k = find_key(items, r["Eşya adı"])
            if k and items[k].get("talent") != r["Talent"]: items[k]["talent"] = r["Talent"]

    # ---- Markalar / Gear setler
    for r in rows(wb, "Markalar"):
        add_list("brands", r["Marka"])
        bon = [str(r.get(c) or "").strip() for c in ("1 parça", "2 parça", "3 parça")]
        bon = [b for b in bon if b]
        if bon and d.setdefault("brand_bonuses", {}).get(r["Marka"]) != bon:
            d["brand_bonuses"][r["Marka"]] = bon; ch["bonuses~"] += 1
    for r in rows(wb, "Gear Setler"):
        add_list("gear_sets", r["Gear set"])
        bon = [re.sub(r"^\d:\s*", "", str(r.get(c) or "").strip()) for c in ("2 parça", "3 parça", "4 parça")]
        bon = [b for b in bon if b]
        if bon and d.setdefault("gear_set_bonuses", {}).get(r["Gear set"]) != bon:
            d["gear_set_bonuses"][r["Gear set"]] = bon; ch["bonuses~"] += 1

    # ---- Exoticler / Named / Silahlar
    for r in rows(wb, "Exoticler"):
        add_list("exotics", r["Exotic"])
        if r.get("Tür") == "Silah": set_weapon(r["Exotic"], r.get("Yuva / Silah türü"), "exotic")
        elif r.get("Tür") == "Ekipman": set_item(r["Exotic"], r.get("Yuva / Silah türü"), "exotic", "")
    for r in rows(wb, "Named"):
        add_list("named", r["Named eşya"])
        if r.get("Tür") == "Silah": set_weapon(r["Named eşya"], r.get("Yuva / Silah türü"), "named")
        elif r.get("Tür") == "Ekipman": set_item(r["Named eşya"], r.get("Yuva / Silah türü"), "named", r.get("Marka / Temel silah"))
    for r in rows(wb, "Silahlar"):
        set_weapon(r["Silah"], r.get("Tür"), r.get("Kalite"))

    # ---- Talentler
    gts = d.setdefault("gear_talent_slots", {})
    for r in rows(wb, "Ekipman Talentleri"):
        t = r["Talent"]
        if N(t) not in {N(x) for x in d["gear_talents"]}: d["gear_talents"].append(t); ch["talents+"] += 1
        slot = SLOT_EN.get(r.get("Yuva") or "", "")
        if slot and t not in gts: gts[t] = {"slot": slot, "kind": "perfect" if t.lower().startswith("perfect") else "normal"}
    for r in rows(wb, "Silah Talentleri"):
        t = r["Talent"]
        if N(t) not in {N(x) for x in d["weapon_talents"]}: d["weapon_talents"].append(t); ch["talents+"] += 1

    # ---- Modlar, skill'ler
    have = {N(m["stat"]) for m in d.get("gear_mods", [])}
    for r in rows(wb, "Ekipman Modları"):
        if N(r["Stat"]) not in have and r.get("En yüksek") is not None:
            d.setdefault("gear_mods", []).append({"stat": r["Stat"], "max": float(r["En yüksek"]),
                                                  "type": {"Saldırı": "offensive", "Savunma": "defensive", "Yardımcı": "utility"}.get(r.get("Tür"), "")})
            ch["mods+"] += 1
    for r in rows(wb, "Silah Modları"):
        if r.get("Mod") and N(r["Mod"]) not in {N(x) for x in d.setdefault("weapon_mods", [])}:
            d["weapon_mods"].append(r["Mod"]); ch["mods+"] += 1
    for r in rows(wb, "Skilller"):
        if N(r["Skill"]) not in {N(x) for x in d.setdefault("skills", [])}:
            d["skills"].append(r["Skill"]); ch["lists+"] += 1

    # gerçek fark (aynı kayda art arda yazılıp eski değerine dönenler sayılmaz)
    ch = {"eşya eklendi": sum(1 for k in items if k not in orig["items"]),
          "eşya düzeltildi": sum(1 for k in items if k in orig["items"] and items[k] != orig["items"][k]),
          "silah eklendi": sum(1 for k in windex if k not in orig["weapon_index"]),
          "silah düzeltildi": sum(1 for k in windex if k in orig["weapon_index"] and windex[k] != orig["weapon_index"][k]),
          "silinen (TD1)": sum(1 for k in orig["items"] if k not in items) + sum(1 for k in orig["weapon_index"] if k not in windex),
          "liste değişti": sum(1 for k in ("exotics", "named", "gear_sets", "brands", "gear_talents", "weapon_talents", "weapons",
                                          "weapon_mods", "skills") if d.get(k) != orig.get(k)),
          "bonus değişti": sum(1 for k in ("brand_bonuses", "gear_set_bonuses") for b in d.get(k, {}) if d[k][b] != orig.get(k, {}).get(b))}
    if not any(ch.values()):
        print("değişiklik yok: Excel ile kütüphane aynı"); return ch
    v = str(d.get("version", "")); today = time.strftime("%Y-%m-%d")
    d["version"] = f"{today}.{int(v.split('.')[-1]) + 1 if v.startswith(today) and v.split('.')[-1].isdigit() else 1}"
    if "TD2_Kutuphane.xlsx" not in d.get("source", ""):
        d["source"] = d.get("source", "") + " + TD2_Kutuphane.xlsx (Ubisoft sezon notları Y8)"
    after = {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in d.items()}
    print("değişiklikler:", ch)
    print("önce → sonra:", {k: f"{before.get(k)}→{after[k]}" for k in after if before.get(k) != after[k]})
    if not dry:
        path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print("yazıldı:", path, "sürüm", d["version"])
    return ch


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(Path(args[0]) if args else ROOT / "meta" / "TD2_Kutuphane.xlsx", dry="--dry" in sys.argv)
