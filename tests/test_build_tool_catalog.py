"""Fixed weapon details stay connected to the local community catalog."""
import json
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_tool
import build_tool_ui
from stash import Stash

class BuildToolCatalogTests(unittest.TestCase):
    def test_fixed_weapon_roll_slots_resolve_through_attribute_catalog(self):
        catalog = {
            "weapon_index": {"Test Exotic": {
                "quality": "exotic", "talent": "Test Talent",
                "base_stats": {"base_damage": 100, "base_rpm": 60,
                               "base_mag_size": 30, "base_reload_time": 2}, "mod_slots": {},
                "roll_slots": {"core_1": "fixed:assault-rifle-damage-weapon-core",
                               "core_2": "fixed:health-damage-weapon-core",
                               "minor_1": "type:weapon-minor"},
            }},
            "attributes": {
                "weapon_type_damage": {"aliases": ["assault rifle damage"],
                                       "weapon_max": 15, "unit": "%"},
                "damage_to_health": {"aliases": ["damage to health", "health damage"],
                                      "weapon_max": 10, "unit": "%"},
            },
            "weapon_mod_details": [],
        }
        details = build_tool.auto_details("Test Exotic", "Primary", catalog)
        self.assertEqual(details["core"], "Weapon Damage")
        self.assertEqual(details["attrs"]["weapon_type_damage"], 15)
        self.assertEqual(details["attrs"]["damage_to_health"], 10)
        self.assertEqual(
            {row["name"]: (row["value"], row["unit"]) for row in details["fixed_attributes"]},
            {"Assault Rifle Damage": ("15", "%"), "Health Damage": ("10", "%")},
        )
        build = build_tool.new_build()
        build["slots"]["Primary"] = details
        self.assertAlmostEqual(build_tool.calculate(build, catalog)["weapons"][0]["dps"], 115)

    def test_st_elmos_fixed_weapon_attributes_and_attachments_are_loaded(self):
        catalog = json.loads((ROOT / "meta" / "game_data.json").read_text(encoding="utf-8"))
        details = build_tool.auto_details("St. Elmo's Engine", "Primary", catalog)

        self.assertEqual(details["talent"], "Actum Est")
        self.assertEqual(details["core"], "Weapon Damage")
        self.assertEqual(details["attrs"]["weapon_type_damage"], 15)
        self.assertEqual(details["attrs"]["damage_to_health"], 10)
        actual_fixed = {row["name"]: (row["value"], row["unit"])
                        for row in details["fixed_attributes"]}
        self.assertTrue({"Assault Rifle Damage": ("15", "%"), "Health Damage": ("10", "%")}.items()
                        <= actual_fixed.items())
        self.assertEqual(
            {row["name"] for row in details["attachments"]},
            {"Conductor Rail", "Insulated Magazine", "Overcharged Muzzle", "Insulated Grip"},
        )

    def test_every_fixed_weapon_roll_in_catalog_is_resolved(self):
        catalog = json.loads((ROOT / "meta" / "game_data.json").read_text(encoding="utf-8"))
        for name, item in catalog["weapon_index"].items():
            rolls = item.get("roll_slots", {})
            details = build_tool.auto_details(name, "Primary", catalog)
            resolved = {row["slot"] for row in details["fixed_attributes"]}
            for slot, value in rolls.items():
                if value.startswith("fixed:"):
                    self.assertIn(slot, resolved, (name, slot, value))

    def test_fixed_named_and_exotic_gear_auto_fill_but_generic_rolls_stay_manual(self):
        catalog = {
            "items": {
                "Fixture Exotic Pack": {
                    "slot": "Backpack", "quality": "exotic", "talent": "Fixed Exotic Talent",
                    "roll_slots": {"core_1": "fixed:skill-tier-gear-core",
                                   "minor_1": "fixed:skill-damage-gear-minor"},
                    "mod_slots": ["type:gear-mod"],
                },
                "Fixture Named Kneepads": {
                    "slot": "Kneepads", "quality": "named", "talent": "Fixed Named Talent",
                    "roll_slots": {"core_1": "type:gear-core", "minor_1": "fixed:dtoc-foxs-prayer"},
                },
                "Fixture High-End Mask": {
                    "slot": "Mask", "quality": "high-end", "roll_slots": {"minor_1": "type:gear-minor"},
                },
            },
            "attributes": {
                "skill_tier": {"aliases": ["skill tier"], "max": 6, "unit": ""},
                "skill_damage": {"aliases": ["skill damage"], "max": 10, "unit": "%"},
                "damage_to_armor": {"aliases": ["damage to armor"], "max": 6, "unit": "%"},
            },
            "brands": [], "gear_sets": [],
        }
        exotic = build_tool.auto_details("Fixture Exotic Pack", "Backpack", catalog)
        named = build_tool.auto_details("Fixture Named Kneepads", "Kneepads", catalog)
        generic = build_tool.auto_details("Fixture High-End Mask", "Mask", catalog)

        self.assertEqual(exotic["catalog_status"], "catalogued")
        self.assertEqual(exotic["talent"], "Fixed Exotic Talent")
        self.assertEqual(exotic["core"], "Skill Tier")
        self.assertEqual(exotic["attrs"]["skill_damage"], 10)
        self.assertEqual(exotic["mod_slots"], ["Gear Mod"])
        self.assertEqual(named["talent"], "Fixed Named Talent")
        self.assertEqual(named["attrs"]["damage_to_armor"], 8)
        self.assertEqual(generic["catalog_status"], "catalogued")
        self.assertEqual(generic["fixed_attributes"], [])
        self.assertEqual(generic["attrs"], {})

        manual = build_tool.new_build()
        manual["slots"]["Mask"] = {**generic, "attrs": {"crit_chance": 5.5}}
        self.assertEqual(build_tool.normalize_build(manual)["slots"]["Mask"]["attrs"]["crit_chance"], 5.5)

    def test_unknown_item_is_review_and_not_autofilled(self):
        details = build_tool.auto_details("Unlisted Backpack", "Backpack", {"items": {}})
        self.assertEqual(details["catalog_status"], "unverified")
        self.assertEqual(details["attrs"], {})
        self.assertEqual(details["fixed_attributes"], [])

    def test_pts_catalog_item_is_not_used_for_live_autofill(self):
        catalog = {"items": {"PTS Named Item": {"slot": "Mask", "data_status": "pts",
                                                  "talent": "Experimental Talent",
                                                  "roll_slots": {"minor_1": "fixed:skill-damage-gear-minor"}}},
                   "attributes": {"skill_damage": {"max": 10}}}
        details = build_tool.auto_details("PTS Named Item", "Mask", catalog)
        build = build_tool.new_build()
        build["slots"]["Mask"] = {**details, "talent": "Experimental Talent"}
        messages = [row["message"] for row in build_tool.validate_build(build, catalog)]
        self.assertEqual(details["catalog_status"], "unverified")
        self.assertEqual(details["attrs"], {})
        self.assertTrue(any("PTS/experimental" in value for value in messages))

    def test_pts_weapon_base_stats_do_not_enter_live_estimate(self):
        catalog = {"weapon_index": {"PTS Weapon": {"type": "Assault Rifle", "data_status": "pts",
                                                      "base_stats": {"base_damage": 500, "base_rpm": 600}}}}
        build = build_tool.new_build()
        build["slots"]["Primary"] = {"name": "PTS Weapon", "attrs": {}}
        self.assertEqual(build_tool.calculate(build, catalog)["weapons"], [])

    def test_dashboard_summary_and_compare_report_slots_and_catalog_limits(self):
        catalog = {
            "items": {}, "weapon_index": {}, "attributes": {}, "brands": [], "gear_sets": [],
            "version": "fixture-1", "source": "fixture",
        }
        first, second = build_tool.new_build("A"), build_tool.new_build("B")
        first["slots"]["Mask"] = {"name": "Unknown Mask", "attrs": {}}
        second["slots"]["Mask"] = {"name": "Other Unknown Mask", "attrs": {}}
        summary = build_tool.dashboard_summary(first, catalog, [])
        comparison = build_tool.compare_builds(first, second, catalog)

        self.assertEqual(summary["completion"], 17)
        self.assertEqual(summary["missing_slots"], ["Backpack", "Chest", "Gloves", "Holster", "Kneepads"])
        self.assertEqual(summary["review_count"], 1)
        self.assertEqual(summary["catalog_verification_status"], "partial")
        self.assertEqual(comparison["slot_changes"], [{"slot": "Mask", "first": "Unknown Mask",
                                                       "second": "Other Unknown Mask"}])
        self.assertIn("not in-game measurements", comparison["assumptions"])

    def test_validation_flags_fixed_roll_talent_core_and_duplicate_attribute_conflicts(self):
        catalog = {
            "items": {"Fixture Named": {
                "slot": "Mask", "quality": "named", "talent": "Fixed Talent",
                "roll_slots": {"core_1": "fixed:skill-tier-gear-core",
                               "minor_1": "fixed:damage-to-armor-contractors-gloves"},
            }},
            "attributes": {
                "skill_tier": {"aliases": ["skill tier"], "max": 6},
                "damage_to_armor": {"aliases": ["damage to armor", "armor damage"], "max": 6, "min": 0},
            },
        }
        build = build_tool.new_build()
        build["slots"]["Mask"] = {
            "name": "Fixture Named", "core": "Weapon Damage", "talent": "Wrong Talent",
            "attrs": {"damage_to_armor": 7, "armor_damage": 5},
        }
        issues = build_tool.validate_build(build, catalog)
        messages = [issue["message"] for issue in issues]
        self.assertTrue(any("fixed talent" in message for message in messages))
        self.assertTrue(any("fixed core" in message for message in messages))
        self.assertTrue(any("fixed value" in message for message in messages))
        self.assertTrue(any("Duplicate attribute" in message for message in messages))

    def test_comparison_reports_brand_bonus_threshold_changes(self):
        catalog = {
            "items": {}, "weapon_index": {}, "attributes": {},
            "brands": ["Fixture Brand"], "gear_sets": [],
            "brand_bonuses": {"Fixture Brand": ["Two piece", "Three piece"]},
        }
        first, second = build_tool.new_build("A"), build_tool.new_build("B")
        first["slots"]["Mask"] = {"name": "Mask", "brand": "Fixture Brand"}
        second["slots"]["Mask"] = {"name": "Mask", "brand": "Fixture Brand"}
        second["slots"]["Backpack"] = {"name": "Pack", "brand": "Fixture Brand"}
        compared = build_tool.compare_builds(first, second, catalog)
        self.assertEqual(compared["bonus_changes"]["only_first"], [])
        self.assertEqual(compared["bonus_changes"]["only_second"],
                         [("Fixture Brand", 2, "Three piece")])

    def test_compatibility_warnings_cover_wrong_gear_talent_weapon_talent_and_mod(self):
        catalog = {
            "items": {"Fixture Chest": {"slot": "Chest"}},
            "gear_talent_slots": {"Backpack Talent": {"slot": "Backpack"}},
            "weapon_index": {"Fixture Rifle": {"type": "Rifle", "mod_slots": {
                "optics": "type:optics-long"}}},
            "weapon_talent_details": [{"name": "Rifle Talent", "compatibility": "shotgun"}],
            "weapon_mod_details": [
                {"name": "Compatible Scope", "compatibility": "optics-long|optics-normal"},
                {"name": "Wrong Scope", "compatibility": "optics-short"},
            ],
            "attributes": {},
        }
        build = build_tool.new_build()
        build["slots"]["Chest"] = {"name": "Fixture Chest", "talent": "Backpack Talent"}
        build["slots"]["Primary"] = {"name": "Fixture Rifle", "talent": "Rifle Talent",
                                      "attachments": [
                                          {"slot": "optics", "name": "Compatible Scope"},
                                          {"slot": "optics", "name": "Wrong Scope"},
                                          {"slot": "muzzle", "name": "Unknown Mod"},
                                      ]}
        messages = [row["message"] for row in build_tool.validate_build(build, catalog)]
        self.assertTrue(any("listed for Backpack" in value for value in messages))
        self.assertTrue(any("not listed for weapon type Rifle" in value for value in messages))
        self.assertTrue(any("incompatible with optics" in value for value in messages))
        self.assertTrue(any("compatibility is unverified" in value for value in messages))
        self.assertFalse(any("Compatible Scope is incompatible" in value for value in messages))

    def test_catalog_search_includes_declared_type_brand_and_talent(self):
        catalog = {"items": {
            "Fixture Chest": {"slot": "Chest", "quality": "high-end", "brand": "Alps Summit",
                              "talent": "Kinetic Momentum"},
            "Fixture Pack": {"slot": "Backpack", "quality": "named", "brand": "Petrov"},
        }, "gear_talent_details": [{"name": "Kinetic Momentum", "compatibility": "chest"}]}
        options = ["Fixture Chest", "Fixture Pack"]
        self.assertEqual(build_tool.search_catalog_options(options, "alps", catalog, "Chest"),
                         ["Fixture Chest"])
        self.assertEqual(build_tool.search_catalog_options(options, "kinetic", catalog, "Chest"),
                         ["Fixture Chest"])
        self.assertEqual(build_tool.search_catalog_options(options, "named", catalog, "Chest"),
                         ["Fixture Pack"])

    def test_dashboard_labels_slot_completion_and_stash_availability(self):
        catalog = {"items": {}, "weapon_index": {}, "attributes": {}, "brands": [], "gear_sets": []}
        build = build_tool.new_build()
        available = build_tool.dashboard_summary(build, catalog, [])
        unavailable = build_tool.dashboard_summary(build, catalog, None)
        self.assertEqual(available["completion_basis"], "gear_slots_filled")
        self.assertEqual(available["stash_status"], "available")
        self.assertEqual(unavailable["stash_status"], "unavailable")

    def test_stash_load_failure_is_distinct_from_empty_stash_without_rewriting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stash.json"
            self.assertFalse(Stash(path).load_error)
            original = b'{"items": [invalid'
            path.write_bytes(original)
            loaded = Stash(path)
            self.assertTrue(loaded.load_error)
            self.assertEqual(loaded.owned(), [])
            self.assertEqual(path.read_bytes(), original)

    def test_build_store_round_trip_and_invalid_json_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "build_tool.json"
            build = build_tool.new_build("Round trip")
            build["slots"]["Primary"] = {"name": "Fixture Rifle", "attachments": [
                {"slot": "optics", "name": "Scope", "fixed": False}], "attrs": {}}
            build_tool.save_store(path, [build], [build_tool.new_build("Template")])
            loaded = build_tool.load_store(path)
            self.assertEqual(loaded["builds"][0]["name"], "Round trip")
            self.assertEqual(loaded["builds"][0]["slots"]["Primary"]["attachments"][0]["name"], "Scope")
            self.assertEqual(loaded["templates"][0]["name"], "Template")
            original = b'{"builds": [broken'
            path.write_bytes(original)
            with self.assertRaises(ValueError):
                build_tool.load_store(path)
            self.assertEqual(path.read_bytes(), original)

    def test_build_json_export_import_keeps_user_store_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "export.json"
            store = Path(directory) / "build_tool.json"
            build = build_tool.new_build("Portable")
            build_tool.save_store(store, [build])
            before = store.read_bytes()
            build_tool.export_json(source, [build])
            imported = build_tool.import_json(source)
            self.assertEqual(imported["builds"][0]["name"], "Portable")
            self.assertNotEqual(imported["builds"][0]["id"], build["id"])
            self.assertEqual(store.read_bytes(), before)

    def test_weapon_calculation_returns_explicit_contribution_scope(self):
        build = build_tool.new_build()
        build["slots"]["Primary"] = {"name": "Fixture Rifle", "attrs": {
            "base_damage": 100, "rpm": 600, "weapon_damage": 10, "crit_chance": 20,
            "crit_damage": 50}, "weapon_stats": {}, "attachments": []}
        result = build_tool.calculate(build, {"weapon_index": {}})
        weapon = result["weapons"][0]
        self.assertEqual(weapon["contributions"]["base_damage"], 100)
        self.assertEqual(weapon["contributions"]["weapon_damage_percent"], 10)
        self.assertEqual(weapon["contributions"]["critical_chance_percent"], 20)
        self.assertIn("talent effects", result["contribution_scope"]["excluded"])
        self.assertAlmostEqual(weapon["dps"], 100 * 600 / 60 * 1.1 * (1 + .2 * .5))

    def test_slot_grid_reflows_at_narrow_width_and_translation_keys_exist(self):
        columns, positions = build_tool_ui._slot_grid_positions(500, 11)
        self.assertEqual(columns, 3)
        self.assertEqual(positions[-1], (3, 1))
        self.assertEqual(build_tool_ui._slot_grid_positions(120, 3)[0], 1)
        for path in (ROOT / "lang").glob("*.json"):
            translations = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("build.slot_completion", translations, path.name)


if __name__ == "__main__":
    unittest.main()
