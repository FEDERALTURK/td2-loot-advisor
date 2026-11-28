"""Export PC catalog facts and reference calculations for the offline companion."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_tool


def export():
    catalog = json.loads((ROOT / "meta/game_data.json").read_text(encoding="utf-8"))
    choices = {slot: [] for slot in build_tool.SLOTS}
    for slot in choices:
        if slot in ("Primary", "Secondary", "SideArm"):
            names = catalog.get("weapon_index", {})
        elif slot in build_tool.SLOTS[:6]:
            names = [name for name, meta in catalog.get("items", {}).items()
                     if meta.get("slot", "").casefold() == slot.casefold()]
            names += list(catalog.get("brands", [])) + list(catalog.get("gear_sets", []))
        elif slot.startswith("Skill"):
            names = catalog.get("skills", [])
        else:
            names = ["Survivalist", "Demolitionist", "Sharpshooter", "Gunner", "Technician", "Firewall"]
        choices[slot] = [build_tool.auto_details(name, slot, catalog) for name in sorted(set(names))]
    out = {"schema": 1, "provenance": build_tool.catalog_provenance(catalog),
           "choices": choices, "attributes": catalog.get("attributes", {}),
           "weapon_index": catalog.get("weapon_index", {}),
           "brand_bonuses": catalog.get("brand_bonuses", {}),
           "gear_set_bonuses": catalog.get("gear_set_bonuses", {})}
    target = ROOT / "mobile/assets/data/build_catalog.json"
    target.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    cases = []
    for item in choices["Primary"]:
        build = build_tool.new_build(item["name"])
        build["slots"]["Primary"] = item
        cases.append({"build": build, "expected": build_tool.calculate(build, catalog)})
    build = build_tool.new_build("Mixed gear regression")
    build["slots"]["Primary"] = choices["Primary"][0]
    build["slots"]["Mask"] = {"name": "Fixture", "core": "Weapon Damage", "attrs": {"crit_chance": 50, "crit_damage": 70}}
    build["slots"]["Chest"] = {"name": "Fixture armor", "core": "Armor", "attrs": {"armor": 1000}}
    cases.append({"build": build, "expected": build_tool.calculate(build, catalog)})
    fixture = ROOT / "mobile/test/build_tool_reference.json"
    fixture.write_text(json.dumps(cases, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Exported {sum(map(len, choices.values()))} choices and {len(cases)} PC reference cases")


if __name__ == "__main__":
    export()
