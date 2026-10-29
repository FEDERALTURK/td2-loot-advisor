"""Focused checks for local loot-intelligence decisions.

These do not open the game, capture a screen or contact a community feed.
"""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import intelligence
import stash


def item(name="Test Rifle", quality=70, attrs=None):
    return {"id": name + str(quality), "name": name, "kind": "weapon", "slot": "Weapon",
            "attrs": attrs or {"crit_damage": quality / 10}, "quality": {"crit_damage": quality},
            "rarity": [], "talents": []}


class IntelligenceTests(unittest.TestCase):
    def test_compare_prefers_quality_and_reports_attribute_delta(self):
        old = item(quality=70)
        fresh = item(quality=90)
        result = intelligence.compare(fresh, old)
        self.assertTrue(result["same_item"])
        self.assertTrue(result["better"])
        self.assertGreater(result["quality_delta"], 0)
        self.assertEqual(result["rows"][0]["state"], "better")

    def test_stash_match_selects_the_best_existing_copy(self):
        candidate = item(quality=88)
        result = intelligence.stash_match(candidate, [item(quality=65), item(quality=82)])
        self.assertTrue(result["found"])
        self.assertEqual(result["matches"], 2)
        self.assertEqual(result["best"]["quality"]["crit_damage"], 82)

    def test_locked_item_cannot_be_marked_dismantled(self):
        with tempfile.TemporaryDirectory() as directory:
            store = stash.Stash(Path(directory) / "stash.json")
            record, created = store.add(item(), game=None)
            self.assertTrue(created)
            store.set_locked(record["id"], True)
            self.assertIsNone(store.mark(record["id"], "dismantled"))
            self.assertEqual(store.find(record["id"])["status"], "owned")
            store.set_location(record["id"], "character_2")
            store.set_expertise(record["id"], "target")
            self.assertEqual(store.find(record["id"])["location"], "character_2")
            self.assertEqual(store.find(record["id"])["expertise"], "target")

    def test_universal_search_finds_item_and_build(self):
        result = intelligence.universal_search("striker", [{"name": "Striker's Battlegear", "slot": "Chest"}], [{"name": "Striker DPS"}])
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(len(result["builds"]), 1)
    def test_farm_plan_only_lists_a_route_when_target_loot_matches(self):
        optimized = {"completion": 33, "done": 1, "total": 3,
                     "slots": {"Chest": {"done": False, "fit": 42,
                                          "req": {"source": ["Striker's Battlegear"]}}}}
        rows = [("Escalation", ["Striker's Battlegear"], ["District Union Arena"], "2026-10-28")]
        with patch.object(intelligence.stash, "optimize", return_value=optimized):
            plan = intelligence.farm_plan({"name": "Test"}, {}, [], None, rows)
        self.assertEqual(plan["missing"][0]["routes"][0]["missions"], ["District Union Arena"])


if __name__ == "__main__":
    unittest.main()
