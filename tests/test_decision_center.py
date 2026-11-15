import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import decision_center
import target_planner


class DecisionCenterTests(unittest.TestCase):
    def test_protected_named_item_is_review_even_on_exact_target(self):
        target = target_planner.normalize_target({"name": "Test Named", "slot": "Chest"})
        rows = decision_center.compare_item_to_targets(
            {"name": "Test Named", "slot": "Chest", "rarity": ["NAMED"], "confidence": 0.99},
            [target],
        )
        self.assertEqual(rows[0]["recommendation"], "REVIEW")
        self.assertTrue(rows[0]["protected"])

    def test_normal_item_exact_target_is_keep(self):
        target = target_planner.normalize_target({"name": "Test Chest", "slot": "Chest"})
        rows = decision_center.compare_item_to_targets(
            {"name": "Test Chest", "slot": "Chest", "rarity": ["HIGH-END"], "confidence": 0.99},
            [target],
        )
        self.assertEqual(rows[0]["recommendation"], "KEEP")

    def test_string_exotic_rarity_is_protected(self):
        target = target_planner.normalize_target({"name": "Rare Item", "slot": "Chest"})
        rows = decision_center.compare_item_to_targets(
            {"name": "Rare Item", "slot": "Chest", "rarity": "EXOTIC", "confidence": 0.99},
            [target],
        )
        self.assertEqual(rows[0]["recommendation"], "REVIEW")
        self.assertTrue(rows[0]["protected"])

    def test_string_false_locked_flag_does_not_overprotect(self):
        target = target_planner.normalize_target({"name": "Normal Item", "slot": "Chest"})
        rows = decision_center.compare_item_to_targets(
            {"name": "Normal Item", "slot": "Chest", "rarity": "HIGH-END", "locked": "false", "confidence": 0.99},
            [target],
        )
        self.assertEqual(rows[0]["recommendation"], "KEEP")

    def test_numeric_locked_flag_is_protected(self):
        target = target_planner.normalize_target({"name": "Normal Item", "slot": "Chest"})
        for flag, expected in ((1, "REVIEW"), (0, "KEEP")):
            with self.subTest(locked=flag):
                rows = decision_center.compare_item_to_targets(
                    {"name": "Normal Item", "slot": "Chest", "rarity": "HIGH-END", "locked": flag, "confidence": 0.99},
                    [target],
                )
                self.assertEqual(rows[0]["recommendation"], expected)


if __name__ == "__main__":
    unittest.main()
