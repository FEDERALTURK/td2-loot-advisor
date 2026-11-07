import json
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import target_planner as tp


class TargetPlannerTests(unittest.TestCase):
    def test_normalize_target_preserves_prototype_augment(self):
        target = tp.normalize_target({
        "name": "St. Elmo's Engine",
        "slot": "Weapon",
        "attributes": ["Weapon Damage"],
        "talents": ["Eagle's Strike"],
        "prototype_augments": ["Shock Ammo"],
    })
        self.assertEqual(target["name_key"], "st elmo s engine")
        self.assertEqual(target["attributes"], ["weapon damage"])
        self.assertEqual(target["prototype_augments"], ["shock ammo"])


    def test_match_exact_source_and_classify_stale_as_review(self):
        now = datetime(2026, 11, 7, tzinfo=timezone.utc)
        target = tp.normalize_target({"name": "St. Elmo's Engine", "slot": "Weapon", "attributes": ["Weapon Damage"]})
        fresh = {"source": "target_loot", "name": "St. Elmo's Engine", "slot": "Weapon",
                 "attributes": ["Weapon Damage"], "updated_at": now.timestamp(), "cadence": "daily"}
        stale = dict(fresh, updated_at=(now - timedelta(days=3)).timestamp())
        result = tp.match_targets([target], [fresh, stale], now=now)
        self.assertEqual(result[0]["status"], "MATCH")
        self.assertEqual(result[0]["source"], "target_loot")
        self.assertEqual(result[1]["status"], "REVIEW")
        self.assertTrue(result[1]["stale"])


    def test_unmatched_target_is_no_match_and_roundtrip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "targets.json"
            target = tp.normalize_target({"name": "Test Item", "slot": "Chest", "priority": "high"})
            tp.save_targets(path, [target])
            loaded = tp.load_targets(path)
            self.assertEqual(loaded[0]["name"], "Test Item")
            self.assertEqual(tp.match_targets(loaded, [], now=datetime.now(timezone.utc))[0]["status"], "NO_MATCH")


    def test_invalid_target_rejected(self):
        with self.assertRaises(ValueError):
            tp.normalize_target({"name": "", "slot": "Chest"})


if __name__ == "__main__":
    unittest.main()
