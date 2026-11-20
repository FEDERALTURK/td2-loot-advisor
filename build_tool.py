"""Independent MX-style build planner state and persistence."""
import json
import os
import tempfile
import uuid
import math
import re
import hashlib

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
    snapshot = build.get("catalog_snapshot")
    if isinstance(snapshot, dict):
        out["catalog_snapshot"] = {str(key)[:40]: str(value or "")[:500]
                                    for key, value in snapshot.items()
                                    if key in {"version", "source", "community_name", "community_commit",
                                               "community_date", "community_repository", "community_license", "fingerprint"}}
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


def _attribute_match(slug, attributes):
    normalized = re.sub(r"[^a-z0-9]+", "_", str(slug).casefold()).strip("_")
    candidates = {}
    for key, meta in attributes.items():
        if not isinstance(meta, dict):
            continue
        for label in (key.replace("_", " "), *meta.get("aliases", [])):
            alias = re.sub(r"[^a-z0-9]+", "_", str(label).casefold()).strip("_")
            if alias and (normalized == alias or normalized.startswith(alias + "_")):
                if key not in candidates or len(alias) > candidates[key][0]:
                    candidates[key] = (len(alias), str(label))
    key = max(candidates, key=lambda candidate: candidates[candidate][0]) if candidates else ""
    return key, candidates[key][1] if key else ""


def _attribute_key(slug, attributes):
    return _attribute_match(slug, attributes)[0]


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
                    key, matched_label = _attribute_match(slug, attrs)
                    attribute = attrs.get(key, {}) if key else {}
                    aliases = attribute.get("aliases", []) if isinstance(attribute, dict) else []
                    display = (matched_label.title() if matched_label else
                               key.replace("_", " ").title() if key else slug.replace("-", " ").title())
                    unit = (" rounds" if key == "magazine_size" and not percent else
                            "%" if percent else str(attribute.get("unit", "")))
                    details["fixed_attributes"].append({"slot": str(mod_slot), "name": display,
                                                        "value": raw_value, "unit": unit})
                    if key == "magazine_size":
                        stat = "magazine_percent" if percent else "magazine_bonus"
                        details["weapon_stats"][stat] = details["weapon_stats"].get(stat, 0) + float(raw_value)
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


def catalog_provenance(catalog):
    """Return the catalog's declared origin/version; this does not verify accuracy."""
    catalog = catalog if isinstance(catalog, dict) else {}
    community = catalog.get("community_data_source")
    community = community if isinstance(community, dict) else {}
    identity = "|".join(str(value or "") for value in (
        catalog.get("version"), catalog.get("source"), community.get("commit"), community.get("commit_date")))
    return {
        "version": str(catalog.get("version") or "unknown"),
        "source": str(catalog.get("source") or "Source not recorded"),
        "community_name": str(community.get("name") or "not recorded"),
        "community_commit": str(community.get("commit") or "not recorded"),
        "community_date": str(community.get("commit_date") or "not recorded"),
        "community_repository": str(community.get("repository") or "not recorded"),
        "community_license": str(community.get("license") or "not recorded"),
        "fingerprint": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
    }


def catalog_diagnostics(catalog):
    """Summarize catalog coverage and declared provenance without network access."""
    catalog = catalog if isinstance(catalog, dict) else {}
    provenance = catalog_provenance(catalog)
    items = catalog.get("items") if isinstance(catalog.get("items"), dict) else {}
    weapons = catalog.get("weapon_index") if isinstance(catalog.get("weapon_index"), dict) else {}
    attrs = catalog.get("attributes") if isinstance(catalog.get("attributes"), dict) else {}
    warnings = []
    if provenance["version"] == "unknown":
        warnings.append("Library version is not recorded")
    if provenance["source"] == "Source not recorded":
        warnings.append("Library source is not recorded")
    if provenance["community_commit"] == "not recorded":
        warnings.append("Community data commit is not recorded")
    return {"provenance": provenance, "counts": {
        "gear_items": len(items), "weapons": len(weapons), "attributes": len(attrs),
        "brands": len(catalog.get("brands") or []), "gear_sets": len(catalog.get("gear_sets") or []),
    }, "warnings": warnings}


def stamp_catalog(build, catalog):
    """Store the declared local catalog basis on a build when it is first created."""
    if isinstance(build, dict) and not build.get("catalog_snapshot"):
        build["catalog_snapshot"] = catalog_provenance(catalog)
    return build


def roll_quality(build, catalog=None):
    """Compare entered rolls to catalog maxima; explicitly mark unknown lower bounds."""
    build = normalize_build(build)
    catalog = catalog if isinstance(catalog, dict) else {}
    attributes = catalog.get("attributes", {})
    attributes = attributes if isinstance(attributes, dict) else {}
    rows = []
    for slot, item in build["slots"].items():
        if not item:
            continue
        weapon = slot in ("Primary", "Secondary", "SideArm")
        fixed = auto_details(item.get("name"), slot, catalog).get("attrs", {})
        for key, value in item["attrs"].items():
            meta_key = key if key in attributes else _attribute_key(key, attributes)
            meta = attributes.get(meta_key, {}) if isinstance(attributes, dict) else {}
            maximum = _number(meta.get("weapon_max" if weapon else "max"), None) if isinstance(meta, dict) else None
            minimum = _number(meta.get("min"), None) if isinstance(meta, dict) else None
            if key in fixed or maximum is None or maximum <= (minimum if minimum is not None else 0):
                continue
            denominator = maximum - minimum if minimum is not None else maximum
            percent = max(0.0, min(100.0, (value - (minimum or 0.0)) / denominator * 100))
            rows.append({"slot": slot, "item": item["name"], "attribute": key,
                         "value": value, "minimum": minimum, "maximum": maximum,
                         "percent": percent, "range_verified": minimum is not None,
                         "basis": "catalog range" if minimum is not None else "catalog maximum only"})
    return rows


def validate_build(build, catalog=None):
    """Return structural/catalog warnings; never makes gameplay or dismantle decisions."""
    build = normalize_build(build)
    catalog = catalog if isinstance(catalog, dict) else {}
    attrs = catalog.get("attributes", {})
    attrs = attrs if isinstance(attrs, dict) else {}
    issues = []
    gear_slots = SLOTS[:6]
    for slot in gear_slots + ("Primary", "Secondary", "SideArm", "Skill1", "Skill2"):
        item = build["slots"].get(slot)
        if not item:
            issues.append({"level": "info", "slot": slot, "message": "Slot is empty"})
            continue
        is_weapon = slot in ("Primary", "Secondary", "SideArm")
        table = catalog.get("weapon_index", {}) if is_weapon else catalog.get("items", {})
        label, meta = _lookup(table, item.get("name"))
        if slot in gear_slots and not label:
            label, _ = _lookup({name: {} for name in catalog.get("brands", [])}, item.get("name"))
            if not label:
                label, _ = _lookup({name: {} for name in catalog.get("gear_sets", [])}, item.get("name"))
        if slot.startswith("Skill"):
            skills = catalog.get("skills", [])
            names = list(skills if isinstance(skills, (dict, list, tuple)) else [])
            names += [entry.get("name", "") for entry in catalog.get("skill_variants", [])
                      if isinstance(entry, dict)]
            label = next((name for name in names if str(name).casefold() == item["name"].casefold()), "")
        if not label:
            issues.append({"level": "warning", "slot": slot, "message": "Item is not in the current catalog"})
        elif meta.get("slot") and slot in gear_slots and str(meta["slot"]).casefold() != slot.casefold():
            issues.append({"level": "warning", "slot": slot,
                           "message": f"Catalog slot is {meta['slot']}, not {slot}"})
        fixed = auto_details(item.get("name"), slot, catalog).get("attrs", {})
        for key, value in item["attrs"].items():
            data_key = key if key in attrs else _attribute_key(key, attrs)
            data = attrs.get(data_key, {}) if isinstance(attrs, dict) else {}
            maximum = _number(data.get("weapon_max" if is_weapon else "max"), None) if isinstance(data, dict) else None
            minimum = _number(data.get("min"), None) if isinstance(data, dict) else None
            if key in fixed:
                continue
            if maximum is not None and value > maximum:
                issues.append({"level": "warning", "slot": slot,
                               "message": f"{key} ({value:g}) exceeds catalog maximum ({maximum:g})"})
            elif minimum is not None and value < minimum:
                issues.append({"level": "warning", "slot": slot,
                               "message": f"{key} ({value:g}) is below catalog minimum ({minimum:g})"})
    if not build["specialization"]:
        issues.append({"level": "info", "slot": "Specialization", "message": "No specialization selected"})
    if build.get("catalog_snapshot"):
        current = catalog_provenance(catalog)
        if build["catalog_snapshot"].get("fingerprint") != current["fingerprint"]:
            issues.append({"level": "warning", "slot": "Catalog",
                           "message": "Build was last saved against a different catalog version"})
    return issues


def compare_builds(first, second, catalog=None):
    """Compare two local builds under the same catalog and calculation assumptions."""
    left = calculate(first, catalog)
    right = calculate(second, catalog)
    stats = {key: {"first": left["stats"].get(key, 0), "second": right["stats"].get(key, 0),
                   "delta": right["stats"].get(key, 0) - left["stats"].get(key, 0)}
             for key in sorted(left["stats"].keys() | right["stats"].keys())}
    weapons = []
    for slot in ("Primary", "Secondary", "SideArm"):
        a = next((weapon for weapon in left["weapons"] if weapon["slot"] == slot), None)
        b = next((weapon for weapon in right["weapons"] if weapon["slot"] == slot), None)
        if a or b:
            weapons.append({"slot": slot, "first": a, "second": b,
                            "dps_delta": (b["dps"] if b else 0) - (a["dps"] if a else 0),
                            "ttk_delta": (b["ttk"] if b else 0) - (a["ttk"] if a else 0)})
    return {"stats": stats, "armor": {"first": left["armor"], "second": right["armor"],
                                       "delta": right["armor"] - left["armor"]},
            "cores": {key: {"first": left["cores"][key], "second": right["cores"][key],
                             "delta": right["cores"][key] - left["cores"][key]}
                      for key in left["cores"]}, "weapons": weapons,
            "assumptions": "Both estimates use the same local catalog and target HP; they are not in-game measurements."}


def stash_matches(build, stash_items, catalog=None):
    """Read-only exact-name/brand/set matching against owned local stash records."""
    build = normalize_build(build)
    owned = [item for item in stash_items if isinstance(item, dict) and item.get("status", "owned") == "owned"]
    matches = []
    for slot in SLOTS[:6]:
        target = build["slots"].get(slot)
        if not target:
            continue
        auto = auto_details(target.get("name"), slot, catalog)
        target_name = str(target.get("name", "")).casefold()
        target_set = str(target.get("gear_set") or auto.get("gear_set") or "").casefold()
        target_brand = str(target.get("brand") or auto.get("brand") or "").casefold()
        candidates = []
        for item in owned:
            if str(item.get("slot", "")).casefold() != slot.casefold():
                continue
            match = ""
            if str(item.get("name", "")).casefold() == target_name:
                match = "exact item"
            elif target_set and str(item.get("gear_set", "")).casefold() == target_set:
                match = "same gear set"
            elif target_brand and str(item.get("brand", "")).casefold() == target_brand:
                match = "same brand"
            if match:
                candidates.append({"name": str(item.get("name") or "Unknown item"),
                                   "match": match, "locked": bool(item.get("locked")),
                                   "rarity": list(item.get("rarity") or [])})
        matches.append({"slot": slot, "target": target.get("name", ""),
                        "brand": target_brand, "gear_set": target_set,
                        "owned": bool(candidates), "candidates": candidates})
    return matches


def farm_routes(matches, target_loot_rows):
    """Match missing gear targets to dated targeted-loot categories; never promise a drop."""
    def key(value):
        return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())

    routes = {}
    for match in matches:
        if match["owned"]:
            continue
        item = match.get("target", "")
        wanted = {key(item)}
        for label in (match.get("brand"), match.get("gear_set")):
            if label:
                wanted.add(key(label))
        found = []
        for event, targets, missions, day in target_loot_rows or ():
            hits = [target for target in targets or () if key(target) in wanted]
            if hits:
                found.append({"event": str(event), "targets": hits,
                              "missions": list(missions or ()), "day": str(day or "")})
        routes[match["slot"]] = found
    return routes


def load_store(path):
    try:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return {"builds": [], "templates": []}
    if not isinstance(data, dict) or not isinstance(data.get("builds"), list):
        raise ValueError("invalid Build Tool store")
    templates = data.get("templates", [])
    if not isinstance(templates, list):
        raise ValueError("invalid Build Tool templates")
    return {"builds": [normalize_build(value) for value in data["builds"][:200]],
            "templates": [normalize_build(value) for value in templates[:100]]}


def save_store(path, builds, templates=()):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="build-tool-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"schema": 2, "builds": [normalize_build(b) for b in builds[:200]],
                       "templates": [normalize_build(b) for b in list(templates)[:100]]},
                      stream, ensure_ascii=False, indent=2)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path): os.unlink(temp_path)


def export_json(path, builds, templates=()):
    save_store(path, builds, templates)


def import_json(path):
    if os.path.getsize(path) > 2_000_000:
        raise ValueError("Build Tool JSON is larger than 2 MB")
    data = load_store(path)
    if not data["builds"] and not data["templates"]:
        raise ValueError("No builds or templates were found in this file")
    for build in data["builds"] + data["templates"]:
        build["id"] = uuid.uuid4().hex
    return data


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
        if slot not in ("Primary", "Secondary", "SideArm"):
            for key, value in item["attrs"].items():
                if key in stats:
                    stats[key] += value
            if "skill" in core or "utility" in core:
                stats["skill_tier"] += 1
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
        magazine = _number(base_stats.get("base_mag_size", attrs.get("magazine_size")), 0)
        weapon_stats = item.get("weapon_stats", {})
        magazine += _number(weapon_stats.get("magazine_bonus"), 0)
        magazine *= 1 + _number(weapon_stats.get("magazine_percent"), 0) / 100
        reload_time = _number(attrs.get("reload_time", base_stats.get("base_reload_time")), 0)
        weapon_mod_stats = {}
        weapon_mod_magazine_percent = 0.0
        for attachment in item.get("attachments", []):
            for key, value, percent in _fixed_stats(attachment.get("stats", "")):
                attr_key = _attribute_key(key, catalog.get("attributes", {}))
                if attr_key:
                    weapon_mod_stats[attr_key] = weapon_mod_stats.get(attr_key, 0) + float(value)
                    if attr_key == "magazine_size" and percent:
                        weapon_mod_magazine_percent += float(value)
        if damage and rpm:
            weapon_damage = stats["weapon_damage"] + attrs.get("weapon_damage", 0) + weapon_mod_stats.get("weapon_damage", 0)
            crit_chance = min(60, stats["crit_chance"] + attrs.get("crit_chance", 0) + weapon_mod_stats.get("crit_chance", 0))
            crit_damage = stats["crit_damage"] + attrs.get("crit_damage", 0) + weapon_mod_stats.get("crit_damage", 0)
            rate_of_fire = attrs.get("rate_of_fire", 0) + weapon_mod_stats.get("rate_of_fire", 0)
            reload_speed = stats["reload_speed"] + attrs.get("reload_speed", 0) + weapon_mod_stats.get("reload_speed", 0)
            rpm *= 1 + rate_of_fire / 100
            reload_time = reload_time / (1 + reload_speed / 100) if reload_time else 0
            magazine *= 1 + weapon_mod_magazine_percent / 100
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
    for name, count in brands.items():
        tiers = brand_bonus_data.get(name, []) if isinstance(brand_bonus_data, dict) else []
        for tier, description in enumerate(tiers[:count], 1):
            bonuses["brands"].append({"name": name, "tier": tier, "text": str(description)})
    for name, count in sets.items():
        tiers = gear_bonus_data.get(name, []) if isinstance(gear_bonus_data, dict) else []
        for tier, description in enumerate(tiers[:max(0, count - 1)], 2):
            bonuses["gear_sets"].append({"name": name, "tier": tier, "text": str(description)})
    return {"stats": stats, "cores": cores, "armor": armor, "brands": brands, "gear_sets": sets,
            "bonuses": bonuses, "weapons": weapons, "enemy_hp": build["enemy_hp"]}


def load(path):
    return load_store(path)["builds"]


def save(path, builds):
    try:
        templates = load_store(path)["templates"]
    except (OSError, ValueError):
        templates = []
    save_store(path, builds, templates)
