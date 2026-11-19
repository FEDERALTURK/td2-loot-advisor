"""Independent MX-style build planner state and persistence."""
import json
import os
import tempfile
import uuid
import math
import re

SLOTS = ("Mask", "Backpack", "Chest", "Gloves", "Holster", "Kneepads", "Primary", "Secondary",
         "SideArm", "Specialization", "Skill1", "Skill2")


def new_build(name="New Build"):
    return {"id": uuid.uuid4().hex, "name": str(name)[:80], "slots": {slot: None for slot in SLOTS},
            "shd_levels": {}, "specialization": "", "enemy_hp": 2_000_000, "schema": 1}


def normalize_build(build):
    if not isinstance(build, dict):
        raise ValueError("invalid build")
    out = new_build(build.get("name") or "New Build")
    out["id"] = str(build.get("id") or out["id"])[:64]
    slots = build.get("slots") if isinstance(build.get("slots"), dict) else {}
    for slot in SLOTS:
        value = slots.get(slot)
        if value is None or isinstance(value, dict):
            out["slots"][slot] = value
    shd = build.get("shd_levels")
    if isinstance(shd, dict):
        for key, value in shd.items():
            try: out["shd_levels"][str(key)[:40]] = max(0, min(10, int(value)))
            except (TypeError, ValueError): continue
    out["specialization"] = str(build.get("specialization") or "")[:60]
    out["enemy_hp"] = _number(build.get("enemy_hp"), 2_000_000, 1, 100_000_000)
    for slot, item in list(out["slots"].items()):
        if not isinstance(item, dict):
            continue
        clean = {key: str(item.get(key) or "")[:120] for key in
                 ("name", "core", "brand", "gear_set", "talent", "quality")}
        attrs = item.get("attrs") if isinstance(item.get("attrs"), dict) else {}
        clean["attrs"] = {str(key)[:40]: _number(value, 0, -1_000_000, 1_000_000)
                           for key, value in attrs.items() if _number(value, None, -1_000_000, 1_000_000) is not None}
        clean["fixed_attributes"] = _clean_details(item.get("fixed_attributes"), "attribute")
        clean["attachments"] = _clean_details(item.get("attachments"), "attachment")
        clean["mod_slots"] = [str(value)[:80] for value in item.get("mod_slots", [])[:16]
                              if isinstance(value, str)] if isinstance(item.get("mod_slots"), list) else []
        weapon_stats = item.get("weapon_stats") if isinstance(item.get("weapon_stats"), dict) else {}
        clean["weapon_stats"] = {str(key)[:40]: _number(value, 0, -1_000_000, 1_000_000)
                                  for key, value in weapon_stats.items()
                                  if _number(value, None, -1_000_000, 1_000_000) is not None}
        out["slots"][slot] = clean
    return out


def _clean_details(values, kind):
    if not isinstance(values, list):
        return []
    fields = ("slot", "name", "stats", "value", "unit") if kind == "attribute" else (
        "slot", "name", "stats")
    result = []
    for value in values[:24]:
        if not isinstance(value, dict):
            continue
        clean = {key: str(value.get(key) or "")[:120] for key in fields}
        if kind == "attachment":
            clean["fixed"] = bool(value.get("fixed"))
        result.append(clean)
    return result


def _lookup(table, name):
    if not isinstance(table, dict):
        return "", {}
    folded = str(name or "").strip().casefold().replace("’", "'")
    for label, value in table.items():
        if str(label).strip().casefold().replace("’", "'") == folded:
            return str(label), value if isinstance(value, dict) else {}
    return "", {}


def _attribute_key(slug, attributes):
    normalized = re.sub(r"[^a-z0-9]+", "_", str(slug).casefold()).strip("_")
    candidates = {}
    for key, meta in attributes.items():
        if not isinstance(meta, dict):
            continue
        for label in (key.replace("_", " "), *meta.get("aliases", [])):
            alias = re.sub(r"[^a-z0-9]+", "_", str(label).casefold()).strip("_")
            if alias and (normalized == alias or normalized.startswith(alias + "_")):
                candidates[key] = max(candidates.get(key, 0), len(alias))
    return max(candidates, key=candidates.get) if candidates else ""


def _fixed_stats(value):
    for part in str(value or "").split("|"):
        match = re.fullmatch(
            r"\s*([a-z0-9-]+)\s*:\s*([+-]?\d+(?:[.,]\d+)?)\s*(%)?\s*", part, re.I
        )
        if match:
            yield match.group(1), match.group(2).replace(",", "."), match.group(3)


def auto_details(name, slot, catalog=None):
    """Return only catalogued fixed item facts; variable rolls remain untouched."""
    catalog = catalog if isinstance(catalog, dict) else {}
    is_weapon = slot in ("Primary", "Secondary", "SideArm")
    source = catalog.get("weapon_index", {}) if is_weapon else catalog.get("items", {})
    label, meta = _lookup(source, name)
    if not label:
        selected = str(name or "").strip()
        def catalog_names(values):
            if isinstance(values, dict):
                return values.keys()
            return values if isinstance(values, (list, tuple, set)) else ()
        brand = next((str(value) for value in catalog_names(catalog.get("brands"))
                      if str(value).strip().casefold() == selected.casefold()), "")
        gear_set = next((str(value) for value in catalog_names(catalog.get("gear_sets"))
                         if str(value).strip().casefold() == selected.casefold()), "")
        return {"name": selected, "quality": "", "core": "", "brand": brand,
                "gear_set": gear_set, "talent": "", "attrs": {}, "fixed_attributes": [],
                "attachments": [], "mod_slots": [], "weapon_stats": {}}

    details = {"name": label, "quality": str(meta.get("quality", "")),
               "core": "", "brand": str(meta.get("brand", "")),
               "gear_set": str(meta.get("gear_set", "")), "talent": str(meta.get("talent", "")),
               "attrs": {}, "fixed_attributes": [], "attachments": [], "mod_slots": [],
               "weapon_stats": {}}
    attrs = catalog.get("attributes", {})
    if is_weapon:
        base = meta.get("base_stats", {}) if isinstance(meta.get("base_stats"), dict) else {}
        details["attrs"] = {target: base[source_key] for target, source_key in (
            ("base_damage", "base_damage"), ("rpm", "base_rpm"),
            ("magazine_size", "base_mag_size"), ("reload_time", "base_reload_time"))
            if base.get(source_key) is not None}
        details["weapon_stats"] = {key: value for key, value in base.items()
                                   if key not in {"base_damage", "base_rpm", "base_mag_size", "base_reload_time"}}
        mods = catalog.get("weapon_mod_details", [])
        mod_index = {str(value.get("name", "")).strip().casefold(): value for value in mods if isinstance(value, dict)}
        raw_slots = meta.get("mod_slots", {})
        for mod_slot, raw in raw_slots.items() if isinstance(raw_slots, dict) else ():
            raw = raw.strip() if isinstance(raw, str) else ""
            fixed = raw.startswith("fixed:")
            mod_name = raw[6:].strip() if fixed else ""
            mod = mod_index.get(mod_name.casefold(), {})
            stats = str(mod.get("stats", ""))
            if fixed:
                details["attachments"].append({"slot": str(mod_slot), "name": mod_name,
                                                "stats": stats, "fixed": True})
                for slug, raw_value, percent in _fixed_stats(stats):
                    key = _attribute_key(slug, attrs)
                    attribute = attrs.get(key, {}) if key else {}
                    aliases = attribute.get("aliases", []) if isinstance(attribute, dict) else []
                    display = (aliases[0].title() if aliases else
                               key.replace("_", " ").title() if key else slug.replace("-", " ").title())
                    unit = (" rounds" if key == "magazine_size" and not percent else
                            "%" if percent else str(attribute.get("unit", "")))
                    details["fixed_attributes"].append({"slot": str(mod_slot), "name": display,
                                                        "value": raw_value, "unit": unit})
                    if key == "magazine_size" and not percent:
                        details["weapon_stats"]["magazine_bonus"] = float(raw_value)
            elif isinstance(raw, str) and raw.startswith("type:"):
                details["mod_slots"].append(str(mod_slot))
    else:
        roll_slots = meta.get("roll_slots", {})
        for roll_slot, raw in roll_slots.items() if isinstance(roll_slots, dict) else ():
            if not isinstance(raw, str) or not raw.startswith("fixed:"):
                continue
            slug = raw[6:].strip()
            key = _attribute_key(slug, attrs)
            attr = attrs.get(key, {}) if key else {}
            if str(roll_slot).startswith("core_"):
                core_key = key or _attribute_key(re.sub(r"-(?:gear|weapon)-core$", "", slug), attrs)
                details["core"] = {"weapon_damage": "Weapon Damage", "armor": "Armor",
                                   "skill_tier": "Skill Tier"}.get(core_key, core_key.replace("_", " ").title())
                continue
            aliases = attr.get("aliases", []) if isinstance(attr, dict) else []
            display = (aliases[0].title() if aliases else
                       key.replace("_", " ").title() if key else slug.replace("-", " ").title())
            value = attr.get("max") if isinstance(attr, dict) else None
            unit = str(attr.get("unit", "")) if isinstance(attr, dict) else ""
            # Named variants can have a unique fixed value above the normal roll cap.
            value = _UNIQUE_FIXED_VALUES.get(slug, value)
            details["fixed_attributes"].append({"slot": str(roll_slot), "name": display,
                                                "value": "" if value is None else str(value), "unit": unit})
            if key and value is not None:
                details["attrs"][key] = value
        raw_mod_slots = meta.get("mod_slots", [])
        if isinstance(raw_mod_slots, list):
            details["mod_slots"] = [str(value.split(":", 1)[-1]).replace("-", " ").title()
                                    for value in raw_mod_slots if isinstance(value, str) and value.startswith("type:")]
    return details


_UNIQUE_FIXED_VALUES = {
    "damage-to-armor-contractors-gloves": 8,
    "dtoc-foxs-prayer": 8,
    "health-damage-the-hollow-man": 10,
    "headshot-damage-punch-drunk": 20,
    "status-effects-firm-handshake": 16,
    "melee-damage-claws-out": 400,
    "weapon-damage-picaros-holster": 15,
}


def _number(value, default=None, low=-1e12, high=1e12):
    try:
        number = float(str(value).replace(",", "."))
        return max(low, min(high, number)) if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def calculate(build, catalog=None):
    """Summarize only explicitly selected local build values; never read the stash/game process."""
    build = normalize_build(build)
    catalog = catalog if isinstance(catalog, dict) else {}
    stats = {key: 0.0 for key in ("weapon_damage", "headshot_damage", "crit_chance", "crit_damage", "reload_speed",
                                   "stability", "accuracy", "ammo_capacity", "armor", "explosive_resistance",
                                   "hazard_protection", "health", "skill_haste", "skill_damage", "skill_duration",
                                   "repair_skills", "skill_tier")}
    cores = {"offensive": 0, "defensive": 0, "utility": 0}
    brands, sets = {}, {}
    for slot, item in build["slots"].items():
        if not item:
            continue
        core = item.get("core", "").lower()
        if slot in SLOTS[:6]:
            if "weapon" in core or "offensive" in core:
                cores["offensive"] += 1
            elif "armor" in core or "defensive" in core:
                cores["defensive"] += 1
            elif "skill" in core or "utility" in core:
                cores["utility"] += 1
        for key, value in item["attrs"].items():
            if key in stats:
                stats[key] += value
        if slot in SLOTS[:6]:
            for key, target in (("brand", brands), ("gear_set", sets)):
                value = item.get(key)
                if value:
                    target[value] = target.get(value, 0) + 1
    armor = 660_014 + cores["defensive"] * 170_000 + stats["armor"]
    weapons = []
    weapon_index = catalog.get("weapon_index", {})
    for slot in ("Primary", "Secondary", "SideArm"):
        item = build["slots"].get(slot)
        if not item:
            continue
        attrs = item["attrs"]
        weapon_meta = next((meta for name, meta in weapon_index.items()
                            if name.casefold() == item["name"].casefold()), {}) if isinstance(weapon_index, dict) else {}
        base_stats = weapon_meta.get("base_stats", {}) if isinstance(weapon_meta, dict) else {}
        damage = _number(attrs.get("base_damage", base_stats.get("base_damage")), 0)
        rpm = _number(attrs.get("rpm", base_stats.get("base_rpm")), 0)
        magazine = _number(attrs.get("magazine_size", base_stats.get("base_mag_size")), 0)
        magazine += _number(item.get("weapon_stats", {}).get("magazine_bonus"), 0)
        reload_time = _number(attrs.get("reload_time", base_stats.get("base_reload_time")), 0)
        weapon_mod_stats = {}
        for attachment in item.get("attachments", []):
            for key, value, _percent in _fixed_stats(attachment.get("stats", "")):
                attr_key = _attribute_key(key, catalog.get("attributes", {}))
                if attr_key:
                    weapon_mod_stats[attr_key] = weapon_mod_stats.get(attr_key, 0) + float(value)
        if damage and rpm:
            weapon_damage = stats["weapon_damage"] + weapon_mod_stats.get("weapon_damage", 0)
            crit_chance = stats["crit_chance"] + weapon_mod_stats.get("crit_chance", 0)
            crit_damage = stats["crit_damage"] + weapon_mod_stats.get("crit_damage", 0)
            crit = 1 + (crit_chance / 100) * (crit_damage / 100)
            dps = damage * rpm / 60 * (1 + cores["offensive"] * .15 + weapon_damage / 100) * crit
            if magazine and reload_time:
                shot_damage = damage * (1 + cores["offensive"] * .15 + weapon_damage / 100) * crit
                shots = math.ceil(build["enemy_hp"] / max(shot_damage, 1))
                magazines = max(0, math.ceil(shots / magazine) - 1)
                ttk = max(0, shots - 1) * 60 / rpm + magazines * reload_time
            else:
                ttk = build["enemy_hp"] / dps if dps else 0
            weapons.append({"slot": slot, "name": item["name"], "dps": dps, "ttk": ttk,
                            "damage": damage, "rpm": rpm, "magazine": magazine, "reload": reload_time})
    brand_bonus_data = catalog.get("brand_bonuses", {})
    gear_bonus_data = catalog.get("gear_set_bonuses", {})
    bonuses = {"brands": [], "gear_sets": []}
    for key, counts, source, target in (("brand", brands, brand_bonus_data, "brands"),
                                        ("gear_set", sets, gear_bonus_data, "gear_sets")):
        for name, count in counts.items():
            tiers = source.get(name, []) if isinstance(source, dict) else []
            for tier, description in enumerate(tiers[:count], 1):
                bonuses[target].append({"name": name, "tier": tier, "text": str(description)})
    return {"stats": stats, "cores": cores, "armor": armor, "brands": brands, "gear_sets": sets,
            "bonuses": bonuses, "weapons": weapons, "enemy_hp": build["enemy_hp"]}


def load(path):
    try:
        with open(path, encoding="utf-8") as stream: data = json.load(stream)
    except FileNotFoundError:
        return []
    if not isinstance(data, dict) or not isinstance(data.get("builds"), list):
        raise ValueError("invalid Build Tool store")
    return [normalize_build(build) for build in data["builds"]]


def save(path, builds):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="build-tool-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"schema": 1, "builds": [normalize_build(b) for b in builds]}, stream, ensure_ascii=False, indent=2)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path): os.unlink(temp_path)
