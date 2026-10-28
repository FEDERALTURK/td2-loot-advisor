"""Decision/import safety regressions; no GUI, OCR engine or user data writes.

    python -m unittest discover -s tests -p test_itempolicy.py
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engine
import gamedata
import itempolicy
import stash


def card(**changes):
    item = {"name": "Striker Gloves", "kind": "gear", "slot": "Gloves", "rarity": ["GEAR SET"],
            "attrs": {"weapon_damage": 15, "crit_chance": 6}, "talents": [],
            "quality": {"weapon_damage": 100, "crit_chance": 100}, "confidence": 0.89,
            "gear_set": "Striker's Battlegear", "partial": False, "sections": True}
    item.update(changes)
    return item


CFG = {"settings": {"keep_threshold": 70, "consider_threshold": 40}, "builds": []}


class ItemPolicyTests(unittest.TestCase):
    def test_valid_current_gear_weapon_and_mod_records(self):
        records = [card(), card(name="M1A", kind="weapon", slot="Weapon"),
                   card(name="Gear Mod", kind="gear_mod", slot=None),
                   card(name="Grenade", kind="consumable", slot=None, attrs={}),
                   card(name="Named chest", attrs={}, talents=["Perfect Glass Cannon"]),
                   card(name="Exotic weapon", attrs={}, rarity=["EXOTIC"], sections=True)]
        for item in records:
            with self.subTest(item=item["name"]):
                self.assertTrue(itempolicy.item_valid(item))

    def test_invalid_inputs_never_produce_positive_or_destructive_verdicts(self):
        records = [None, [], "not a card", {}, card(name="?"), card(name=" "), card(name="???"),
                   card(partial=True), card(confidence=0.49), card(confidence="0.9"),
                   card(confidence=float("nan")), card(confidence=float("inf")), card(confidence=True),
                   card(confidence=2), card(attrs={}, talents=[], rarity=[], sections=False),
                   card(attrs=[]), card(attrs={"crit_chance": float("nan")}),
                   card(attrs={"crit_chance": -4}), card(attrs={"crit_chance": "6"}),
                   card(talents={}), card(talents=[None]), card(quality=[]), card(rarity=5),
                   card(kind="unknown"), card(kind=[]), card(attrs={"armor": 10 ** 1000}),
                   card(attrs={}, talents=[], sections=False)]
        for item in records:
            with self.subTest(item=item):
                self.assertFalse(itempolicy.item_valid(item))
                for verdict in ("KEEP", "CONSIDER", "DISMANTLE", "REVIEW"):
                    self.assertEqual(itempolicy.protect_verdict(item, verdict), "REVIEW")
                self.assertEqual(itempolicy.protect_verdict(item, "ERROR"), "ERROR")
        self.assertEqual(itempolicy.protect_verdict(card(), []), "REVIEW")

    def test_all_protected_rarities_require_keep_or_review(self):
        for rarity in ("EXOTIC", "NAMED", "PROTOTYPE", "named", " Exotic "):
            item = card(rarity=[rarity])
            for verdict in ("CONSIDER", "DISMANTLE"):
                with self.subTest(rarity=rarity, verdict=verdict):
                    self.assertEqual(itempolicy.protect_verdict(item, verdict), "REVIEW")
            self.assertEqual(itempolicy.protect_verdict(item, "KEEP"), "KEEP")
            self.assertEqual(itempolicy.protect_verdict(item, "ERROR"), "ERROR")
        self.assertEqual(itempolicy.protect_verdict(card(rarity="NAMED"), "DISMANTLE"), "REVIEW")

    def test_normal_item_scoring_is_preserved(self):
        for kind in ("gear", "weapon", "gear_mod"):
            for score, expected in ((95, "KEEP"), (50, "CONSIDER"), (15, "DISMANTLE")):
                item = card(kind=kind, rarity=["HIGH-END"])
                self.assertEqual(engine.decide(item, [(score, "Test build", [])], CFG)[0], expected)
                self.assertEqual(itempolicy.protect_verdict(item, expected), expected)

    def test_engine_guards_invalid_and_partial_high_score_cards(self):
        for item in (None, {}, card(partial=True), card(confidence=0.1), card(attrs=[])):
            self.assertEqual(engine.decide(item, [(100, "Test build", [])], CFG)[0], "REVIEW")

    def test_engine_protected_rarities_keep_matches_else_review(self):
        for rarity in ("EXOTIC", "NAMED", "PROTOTYPE"):
            item = card(name="Rare Item", rarity=[rarity])
            for score, expected in ((0, "REVIEW"), (50, "REVIEW"), (90, "KEEP")):
                self.assertEqual(engine.decide(item, [(score, "Build", [])], CFG)[0], expected)
            mentioned = {**CFG, "builds": [{"name": "Wanted rare", "items": ["Rare Item"]}]}
            self.assertEqual(engine.decide(item, [(0, "Wanted rare", [])], mentioned)[0], "KEEP")
            # Protection also holds if malformed upstream classification says it is a gear mod.
            self.assertEqual(engine.decide({**item, "kind": "gear_mod"}, [], CFG)[0], "REVIEW")

    def test_review_only_kinds_and_specialization_stay_safe(self):
        for kind in ("weapon_mod", "skill_mod", "cosmetic", "material", "consumable", "cache"):
            self.assertEqual(engine.decide(card(kind=kind), [(100, "Build", [])], CFG)[0], "REVIEW")
        self.assertEqual(engine.decide(card(kind="weapon", spec="Sharpshooter"), [], CFG)[0], "KEEP")

    def test_legacy_and_stash_records_without_confidence_remain_supported(self):
        item = card()
        item.pop("confidence")
        self.assertTrue(itempolicy.item_valid(item))
        self.assertEqual(itempolicy.protect_verdict(item, "DISMANTLE"), "DISMANTLE")
        self.assertFalse(itempolicy.item_valid({"name": "Player Inventory", "rarity": [], "attrs": {}, "talents": []}))

    def test_stash_audit_never_recommends_rare_or_invalid_duplicates(self):
        items = []
        for rarity in ("EXOTIC", "NAMED", "PROTOTYPE", "HIGH-END"):
            for number, value in enumerate((100, 50)):
                item = card(id=f"{rarity}-{number}", name=f"{rarity} Gloves", rarity=[rarity],
                            verdict="DISMANTLE", quality={"crit_chance": value})
                item.pop("confidence")
                items.append(item)
        items += [card(id="partial", partial=True, verdict="DISMANTLE"),
                  card(id="low-confidence", confidence=0.1, verdict="DISMANTLE"),
                  card(id="malformed", attrs=[], verdict="DISMANTLE")]
        before = deepcopy(items)
        report = stash.audit(items)
        self.assertEqual({i["id"] for i in report["dismantle"]}, {"HIGH-END-0", "HIGH-END-1"})
        self.assertEqual(report["counts"]["DISMANTLE"], 2)
        self.assertEqual(report["counts"]["REVIEW"], 9)
        self.assertTrue(all(not itempolicy.is_protected_item(i) for i, _, _ in report["library"]))
        self.assertEqual(items, before)

    def test_stash_duplicates_do_not_bypass_rare_review(self):
        for rarity in ("EXOTIC", "NAMED", "PROTOTYPE"):
            records = [card(id="best", rarity=[rarity], verdict="KEEP"),
                       card(id="copy", rarity=[rarity], verdict="REVIEW", quality={"crit_chance": 20})]
            report = stash.audit(records)
            self.assertTrue(report["duplicates"])
            self.assertEqual(report["dismantle"], [])

    def test_public_sample_cards_are_still_recognized_as_valid(self):
        game = gamedata.GameData(ROOT / "meta" / "game_data.json")
        samples = ROOT / "tests" / "samples" / "cards"
        for name in ("m16a2.txt", "striker_kneepads.txt", "unmatched_backpack.txt"):
            item = game.recognize((samples / name).read_text(encoding="utf-8"))
            with self.subTest(sample=name, item=item["name"]):
                self.assertTrue(itempolicy.item_valid(item))


class ImportValidationTests(unittest.TestCase):
    def test_threshold_boundaries_and_numeric_input(self):
        for keep, consider in ((100, 0), (0, 0), (70, 40), (40, 40), ("80.5", "40")):
            self.assertEqual(itempolicy.validate_thresholds(keep, consider), (float(keep), float(consider)))
        for keep, consider in ((-1, 0), (101, 40), (30, 40), (70, -1), (float("nan"), 40),
                               (70, float("inf")), (True, 0), (None, 0), ("abc", 0)):
            with self.subTest(keep=keep, consider=consider), self.assertRaises(ValueError):
                itempolicy.validate_thresholds(keep, consider)

    def test_public_default_and_meta_builds_validate_without_mutating_input(self):
        for filename in ("scripts/default_builds.json", "meta/meta_builds.json"):
            data = json.loads((ROOT / filename).read_text(encoding="utf-8"))
            before = deepcopy(data)
            result = itempolicy.validate_imported_builds(data)
            self.assertEqual(len(result), len(data["builds"]))
            self.assertEqual(data, before)
            self.assertIsNot(result, data["builds"])
        self.assertEqual(itempolicy.validate_imported_builds([]), [])

    def test_normalized_defaults_and_deep_copy(self):
        source = [{"name": " New build ", "attributes": {"crit_chance": {}},
                   "weapons": {"types": ["Assault Rifle"], "talents": {"Ranger": 2}},
                   "meta": {"summary": {"en": "Example"}}}]
        before = deepcopy(source)
        result = itempolicy.validate_imported_builds(source)
        self.assertEqual(source, before)
        self.assertEqual(result[0]["name"], "New build")
        self.assertEqual(result[0]["attributes"]["crit_chance"], {"weight": 1, "good_at": 0})
        self.assertEqual(result[0]["sets_or_brands"], [])
        result[0]["meta"]["summary"]["en"] = "Changed"
        self.assertEqual(source, before)
        disabled = itempolicy.validate_imported_builds([{"name": "Disabled attribute", "attributes": {"armor": {"weight": 0}}}])
        self.assertEqual(disabled[0]["attributes"]["armor"]["weight"], 0)

    def test_rejects_malformed_import_as_a_whole(self):
        bad = [None, {}, [None], ["not a build"], [{"name": ""}], [{"name": 42}],
               [{"name": "x", "sets_or_brands": "Striker"}], [{"name": "x", "items": [None]}],
               [{"name": "x", "slots": ["Helmet"]}], [{"name": "x", "set_bonus": True}],
               [{"name": "x", "attributes": []}], [{"name": "x", "attributes": {"armor": 15}}],
               [{"name": "x", "attributes": {"armor": {"weight": -1}}}],
               [{"name": "x", "attributes": {"armor": {"good_at": float("nan")}}}],
               [{"name": "x", "talents": {"Ranger": 0}}], [{"name": "x", "talents": {"Ranger": float("inf")}}],
               [{"name": "x", "weapons": []}], [{"name": "x", "weapons": {"types": "Rifle"}}],
               [{"name": "x", "weapons": {"talents": {"Ranger": -1}}}],
               [{"name": "x", "meta": []}], [{"name": "x", "meta": {"summary": "text"}}]]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ValueError):
                itempolicy.validate_imported_builds(data)
        source = [{"name": "valid"}, {"name": "bad", "talents": []}]
        before = deepcopy(source)
        with self.assertRaises(ValueError):
            itempolicy.validate_imported_builds(source)
        self.assertEqual(source, before)


if __name__ == "__main__":
    unittest.main()
