"""Merge the attributed Div2Hub community snapshot into the app's game-data catalog.

Run after updating meta/sources/div2hub: python scripts/sync_div2hub_data.py
This preserves app-specific records while adding names and metadata from the
versioned community source. It does not download or execute remote code.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "meta" / "sources" / "div2hub"
DATA = ROOT / "meta" / "game_data.json"
sys.path.insert(0, str(ROOT))
import gamedata  # noqa: E402


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normset(values):
    return {gamedata.nrm(x) for x in values if x}


def unique_append(target: list, values) -> None:
    have = normset(target)
    for value in values:
        if value and gamedata.nrm(value) not in have:
            target.append(value)
            have.add(gamedata.nrm(value))


def number(value: str):
    value = (value or "").strip().replace("%", "")
    if not value or value == "N/A":
        return None
    try:
        x = float(value)
        return int(x) if x.is_integer() else x
    except ValueError:
        return None


def fixed_talent(value: str) -> str | None:
    value = (value or "").strip()
    if value.lower().startswith("fixed:"):
        return value.split(":", 1)[1].strip() or None
    return None


def main() -> None:
    if not (SOURCE / "README.md").is_file() or not (SOURCE / "LICENSE").is_file():
        raise SystemExit("Div2Hub source snapshot or license is missing")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    original = json.loads(json.dumps(data))

    # Current canonical names used by the app; incoming variants remain accepted
    # through aliases and source records retain the upstream spelling.
    brand_aliases = {
        "Alps Summit Armaments": "Alps Summit Armament",
        "China Light Industries": "China Light Industries Corporation",
        "Ceska Vyroba s.r.o.": "Ceska Vyroba",
        "Česká Výroba s.r.o.": "Ceska Vyroba",
        "Golan Gear Ltd": "Golan Gear Ltd",
        "Shiny Monkey": "Shiny Monkey Gear",
    }
    gear_set_aliases = {"Aces and Eights": "Aces & Eights"}
    brand_lookup = {gamedata.nrm(x): x for x in data.get("brands", [])}
    set_lookup = {gamedata.nrm(x): x for x in data.get("gear_sets", [])}

    def brand_name(value: str) -> str:
        if not value or value == "N/A":
            return ""
        value = brand_aliases.get(value, value)
        return brand_lookup.get(gamedata.nrm(value), value)

    def gear_set_name(value: str) -> str:
        if not value or value == "N/A":
            return ""
        value = gear_set_aliases.get(value, value)
        return set_lookup.get(gamedata.nrm(value), value)

    # AlphaBridge belongs to The Division (2016), not The Division 2.
    removed_sets = {gamedata.nrm(x) for x in data.get("gear_sets", []) if gamedata.nrm(x) == "alphabridge"}
    data["gear_sets"] = [x for x in data.get("gear_sets", []) if gamedata.nrm(x) not in removed_sets]
    data["gear_set_bonuses"] = {k: v for k, v in data.get("gear_set_bonuses", {}).items()
                                if gamedata.nrm(k) not in removed_sets}
    for key, record in list(data.get("items", {}).items()):
        if gamedata.nrm(record.get("gear_set", "")) in removed_sets:
            del data["items"][key]

    # Gear inventory: include generic brand/set pieces as well as named and exotic.
    gear_files = (("masks.csv", "Mask"), ("backpacks.csv", "Backpack"), ("chests.csv", "Chest"),
                  ("gloves.csv", "Gloves"), ("holsters.csv", "Holster"), ("knees.csv", "Kneepads"))
    item_index = {gamedata.nrm(k): k for k in data.setdefault("items", {})}
    for filename, slot in gear_files:
        for row in rows(SOURCE / "gear" / filename):
            name = row["name"].strip()
            quality = "exotic" if row["is_exotic"] == "TRUE" else "named" if row["is_named"] == "TRUE" else \
                      "gear set" if row["gear_set"] != "N/A" else "high-end"
            rec = {"slot": slot, "quality": quality}
            b = brand_name(row.get("brand_set", ""))
            gs = gear_set_name(row.get("gear_set", ""))
            if b:
                rec["brand"] = b
            if gs:
                rec["gear_set"] = gs
            tal = fixed_talent(row.get("talent_slot", ""))
            if tal:
                rec["talent"] = tal
            # Preserve fixed/random roll and mod-slot definitions for future
            # display without changing current recognition or scoring behavior.
            rec["roll_slots"] = {k: row[k] for k in
                                 ("core_1", "core_2", "core_3", "minor_1", "minor_2", "minor_3")}
            rec["mod_slots"] = [row[k] for k in ("mod_1", "mod_2", "mod_3") if row[k] != "N/A"]
            n = gamedata.nrm(name)
            key = item_index.get(n)
            if key:
                current = data["items"][key]
                for k, v in rec.items():
                    if k not in current or current[k] in (None, ""):
                        current[k] = v
            else:
                data["items"][name] = rec
                item_index[n] = name
            if quality == "named":
                unique_append(data.setdefault("named", []), [name])
            elif quality == "exotic":
                unique_append(data.setdefault("exotics", []), [name])
            if b and b not in data.setdefault("brands", []):
                data["brands"].append(b)
                brand_lookup[gamedata.nrm(b)] = b
            if gs:
                unique_append(data.setdefault("gear_sets", []), [gs])
                set_lookup[gamedata.nrm(gs)] = gs

    # Improvised pieces are a valid item family but intentionally have no set bonuses.
    if "Improvised" not in data["brands"]:
        data["brands"].append("Improvised")
    data.setdefault("brand_bonuses", {}).setdefault("Improvised", [])

    # Current weapon records add exact model, type, rarity, fixed talent and
    # mod-slot context. Existing OCR aliases remain in the index.
    weapon_files = (("assault_rifles.csv", "Assault Rifle"), ("lmgs.csv", "Light Machine Gun"),
                    ("mmrs.csv", "Marksman Rifle"), ("pistols.csv", "Pistol"),
                    ("rifles.csv", "Rifle"), ("shotguns.csv", "Shotgun"), ("smgs.csv", "Submachine Gun"))
    weapon_index = data.setdefault("weapon_index", {})
    weapon_norm = {gamedata.nrm(k): k for k in weapon_index}
    source_weapon_names = []
    for filename, weapon_type in weapon_files:
        for row in rows(SOURCE / "weapons" / filename):
            name = row["name"].strip()
            source_weapon_names.append(name)
            n = gamedata.nrm(name)
            key = weapon_norm.get(n, name)
            quality = "exotic" if row["is_exotic"] == "TRUE" else "named" if row["is_named"] == "TRUE" else "high-end"
            rec = weapon_index.setdefault(key, {})
            rec.setdefault("type", weapon_type)
            rec.setdefault("quality", quality)
            # Correct stale classifications from a newer dated source snapshot.
            rec["type"], rec["quality"] = weapon_type, quality
            tal = fixed_talent(row.get("talent_slot", ""))
            if tal:
                rec["talent"] = tal
            rec["family"] = row.get("family", "")
            rec["base_stats"] = {k: number(row[k]) for k in
                                  ("base_damage", "base_rpm", "base_mag_size", "base_reload_time", "optimal_range", "hsd")}
            rec["mod_slots"] = {k: row[k] for k in ("optics", "magazine", "muzzle", "underbarrel")}
            if n not in weapon_norm:
                weapon_norm[n] = key
            if quality == "named":
                unique_append(data.setdefault("named", []), [name])
            elif quality == "exotic":
                unique_append(data.setdefault("exotics", []), [name])
    unique_append(data.setdefault("weapons", []), source_weapon_names)
    for name, record in data.get("items", {}).items():
        if record.get("quality") == "named":
            unique_append(data.setdefault("named", []), [name])
        elif record.get("quality") == "exotic":
            unique_append(data.setdefault("exotics", []), [name])
    for name, record in data.get("weapon_index", {}).items():
        if record.get("quality") == "named":
            unique_append(data.setdefault("named", []), [name])
        elif record.get("quality") == "exotic":
            unique_append(data.setdefault("exotics", []), [name])

    # Talents: names, supported slots/types and descriptions from the dated snapshot.
    for key, file in (("gear_talents", SOURCE / "gear" / "gear_talents.csv"),
                      ("weapon_talents", SOURCE / "weapons" / "weapon_talents.csv")):
        records = rows(file)
        unique_append(data.setdefault(key, []), [r["name"] for r in records])
        details_key = "gear_talent_details" if key == "gear_talents" else "weapon_talent_details"
        data[details_key] = records

    # Weapon mods now include all 252 current named attachments with their
    # compatibility and stat effects. Retain previous OCR spellings as aliases.
    old_mods = list(data.get("weapon_mods", []))
    weapon_mod_details = rows(SOURCE / "weapons" / "weapon_mods.csv")
    source_mod_names = [r["name"] for r in weapon_mod_details]
    source_mod_lookup = {gamedata.nrm(n): n for n in source_mod_names}
    correction_map = {
        "Bighorn Grip": "Bighorn Horn Grip", "C7 Scope 3.4x": "C79 Scope (3.4x)",
        "C7 Scope (3.4x)": "C79 Scope (3.4x)", "VX-1 Scope (12x)": "VX1 Scope  (12x)",
        "Chameleon ActivCamo Processor": "Chameleon ActivCamo", "Chatterbox Cannister": "Chatterbox Canister",
        "Gunner Large Pouch": "Large Pouch (Gunner mag)", "Jagged Break": "Jagged Beak",
        "Omega 7.62 Rifle Suppressor": "Omega 7.62 Rifle Suppresor", "Osprey 9mm Suppressor": "Osprey 9 Suppressor",
        "Plagured Muzzle": "Plagued Muzzle", "QDC Sound Supressor": "QDC Sound Suppressor",
        "Trigger Mechanisim": "Trigger Mechanism", "VX1 Scope 12x": "VX1 Scope  (12x)",
    }
    aliases = {}
    legacy_extras = []
    for old in old_mods:
        if gamedata.nrm(old) in source_mod_lookup:
            continue
        target = correction_map.get(old)
        if target and gamedata.nrm(target) in source_mod_lookup:
            aliases[old] = source_mod_lookup[gamedata.nrm(target)]
        else:
            legacy_extras.append(old)
    data["weapon_mods"] = list(source_mod_names)
    unique_append(data["weapon_mods"], legacy_extras)
    data["weapon_mod_aliases"] = aliases
    data["weapon_mod_details"] = weapon_mod_details

    # Gear mods are variable-roll items; import the current 17 stat families,
    # their ranges and categories from the same source.
    stats = {r["id"]: r["name"] for r in rows(SOURCE / "stats.csv")}
    gm = []
    for r in rows(SOURCE / "gear" / "gear_mods.csv"):
        stat = stats[r["stat_id"]]
        cat = {"skill": "utility"}.get(r["category"], r["category"])
        gm.append({"stat": stat, "max": number(r["range_max"]), "type": cat,
                   "min": number(r["range_min"]), "fidelity": r["fidelity"], "source_id": r["id"]})
    data["gear_mods"] = gm

    # Attribute aliases and fixed exotic/named stats that were absent from the OCR vocabulary.
    aliases_by_attr = {"damage_out_of_cover": ["damage to targets out of cover", "dtoc"],
                       "blind_resist": ["blind deaf resistance", "blind-deaf resistance"]}
    for key, values in aliases_by_attr.items():
        if key in data["attributes"]:
            current = data["attributes"][key].setdefault("aliases", [])
            unique_append(current, values)
    fixed_attrs = {
        "ammo_capacity": ("Ammo Capacity", 10),
        "melee_damage": ("Melee Damage", 500),
        "reduced_threat": ("Reduced Threat", 50),
        "scanner_pulse_haste": ("Scanner Pulse Haste", 100),
        "shield_health": ("Shield Health", 50),
    }
    for key, (label, maximum) in fixed_attrs.items():
        data.setdefault("attributes", {}).setdefault(key, {"aliases": [label.lower()], "max": maximum, "unit": "%"})

    skill_details = rows(SOURCE / "skills" / "skills.csv")
    unique_append(data.setdefault("skills", []), [r["name"] for r in skill_details])
    data["skill_variants"] = skill_details

    # Data source metadata is embedded so exported catalogs can be audited later.
    data["community_data_source"] = {
        "name": "Division 2 Community Data Hub",
        "repository": "https://github.com/div2hub/game-data",
        "commit": "8d5e75b2fb9eb93118e3958a0b49cbf78e71b0a0",
        "commit_date": "2026-10-17",
        "license": "CC-BY-4.0",
    }
    # Apply the project's verified corrections after importing upstream data,
    # so rerunning this script cannot restore known TD1/quality mistakes.
    sys.path.insert(0, str(ROOT / "scripts"))
    from library_excel import apply_corrections  # noqa: E402
    corrections = json.loads((ROOT / "meta" / "sources" / "corrections.json").read_text(encoding="utf-8"))
    apply_corrections(data, corrections)
    excluded_exotics = normset(corrections.get("remove_td1", []) + corrections.get("remove_from_exotics", []))
    for name, record in data.get("weapon_index", {}).items():
        if record.get("quality") == "named":
            unique_append(data.setdefault("named", []), [name])
        elif record.get("quality") == "exotic" and gamedata.nrm(name) not in excluded_exotics:
            unique_append(data.setdefault("exotics", []), [name])

    # Keep the data version stable on a no-op sync; advance it only when the
    # imported/corrected catalog actually changes.
    current = str(original.get("version", ""))
    before = {k: v for k, v in original.items() if k != "version"}
    after = {k: v for k, v in data.items() if k != "version"}
    if before != after:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        previous = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.(\d+)", current)
        sequence = int(previous.group(2)) + 1 if previous and previous.group(1) == today else 1
        data["version"] = f"{today}.{sequence}"
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Updated", DATA)
    for key in ("items", "weapon_index", "weapons", "gear_sets", "brands", "gear_talents", "weapon_talents",
                "weapon_mods", "gear_mods", "skills", "skill_variants", "prototype_augments"):
        value = data.get(key, [])
        print(f"{key}: {len(value)}")


if __name__ == "__main__":
    main()
