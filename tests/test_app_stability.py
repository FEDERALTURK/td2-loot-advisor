"""Integration regressions without App.__init__, Tk windows, network or real CLI.

    python -B -m unittest discover -s tests -p test_app_stability.py -v
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def cfg():
    return {"settings": {"keep_threshold": 70, "consider_threshold": 40},
            "attributes": {"weapon_damage": ["weapon damage"], "crit_chance": ["critical hit chance"]},
            "builds": []}


def card(**changes):
    item = {"name": "Test Gloves", "kind": "gear", "slot": "Gloves", "rarity": ["HIGH-END"],
            "attrs": {"weapon_damage": 15, "crit_chance": 6}, "talents": [],
            "quality": {"weapon_damage": 100, "crit_chance": 100}, "confidence": 0.89,
            "brand": "Grupo Sombra S.A.", "partial": False, "sections": True}
    item.update(changes)
    return item


class AppStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Importing the module does not construct App or call load_cfg. The
        # __main__ entry point is skipped, so no listeners/windows are started.
        name = "_td2_app_stability_target"
        spec = importlib.util.spec_from_file_location(name, ROOT / "app.py")
        cls.app = importlib.util.module_from_spec(spec)
        sys.modules[name] = cls.app
        spec.loader.exec_module(cls.app)

    def bare_app(self):
        obj = self.app.App.__new__(self.app.App)
        obj.cfg = cfg()
        obj.root = Mock()
        obj.results = queue.Queue()
        return obj

    def test_real_modern_and_legacy_invalid_ocr_is_reviewed(self):
        modern = self.app.gamedata.GameData(ROOT / "meta" / "game_data.json")
        for game in (modern, SimpleNamespace(ok=False)):
            for text in ("", "blurry tooltip", "Player inventory 100%", "Palisade Steelworks"):
                with self.subTest(modern=game.ok, text=text), patch.object(self.app, "GAME", game):
                    _, verdict, _ = self.app.evaluate(text, cfg())
                    self.assertEqual(verdict, "REVIEW")

    def test_partial_and_rare_cards_are_safe_through_evaluator(self):
        for item in (card(partial=True), card(confidence=0.1), card(rarity=["EXOTIC"]),
                     card(rarity=["NAMED"]), card(rarity=["PROTOTYPE"])):
            with self.subTest(item=item), patch.object(self.app, "GAME", SimpleNamespace(ok=True)), \
                 patch.object(self.app, "parse_item", return_value=deepcopy(item)), \
                 patch.object(self.app.engine, "evaluate", return_value=[(0, "Unmatched", [])]):
                self.assertEqual(self.app.evaluate("mock OCR card", cfg())[1], "REVIEW")

    def test_legacy_direct_entry_also_applies_policy(self):
        with patch.object(self.app, "GAME", SimpleNamespace(ok=False)):
            for text in ("", "Player inventory 100%", "blurry tooltip"):
                with self.subTest(text=text):
                    self.assertEqual(self.app.evaluate_legacy(text, cfg())[1], "REVIEW")

    def test_result_path_cannot_restore_dismantle_after_progress(self):
        for item in (card(partial=True), card(confidence=0.1), card(rarity=["EXOTIC"]),
                     card(rarity=["NAMED"]), card(rarity=["PROTOTYPE"])):
            obj = self.bare_app()
            obj.cfg["settings"].update(track_progress=True, auto_record=False, speak_verdict=False,
                                        sound=False, log_csv=False, stash_record=False, vendor_mode=False)
            obj.progress = {}
            obj.counts = {v: 0 for v in ("KEEP", "CONSIDER", "DISMANTLE", "REVIEW")}
            for name in ("refresh_counts", "show_result", "popup", "_companion_update", "_service_scan", "record"):
                setattr(obj, name, Mock())
            with self.subTest(item=item), patch.object(self.app, "apply_progress", return_value=("DISMANTLE", None, None, None)):
                obj.handle_result("mock OCR card", item, "REVIEW", [], "test-signature")
            self.assertEqual(obj.counts["DISMANTLE"], 0)
            self.assertEqual(obj.show_result.call_args.args[2], "REVIEW")
            self.assertEqual(obj.popup.call_args.args[0], "REVIEW")
            obj.record.assert_not_called()

    def test_invalid_thresholds_leave_all_settings_untouched(self):
        for keep, consider in ((30, 40), (-1, 0), (101, 40), ("nan", 40)):
            obj = self.bare_app()
            values = {"hotkey": "<f8>", "keep_threshold": keep, "consider_threshold": consider,
                      "overlay_seconds": 8, "auto_interval_ms": 700, "log_max_kb": 1024,
                      "log_backups": 3, "bg_interval": 15}
            obj.sv = {k: SimpleNamespace(get=lambda v=str(v): v) for k, v in values.items()}
            before = deepcopy(obj.cfg)
            with self.subTest(keep=keep, consider=consider), patch.object(self.app, "check_hotkey"), \
                 patch.object(self.app, "save_cfg") as save, patch.object(self.app.messagebox, "showerror") as error, \
                 patch.object(self.app.itempolicy, "validate_thresholds", wraps=self.app.itempolicy.validate_thresholds) as validate:
                obj.save_settings()
            validate.assert_called_once()
            error.assert_called_once()
            save.assert_not_called()
            self.assertEqual(obj.cfg, before)

    def test_import_rejects_entire_malformed_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-builds.json"
            path.write_text(json.dumps([{"name": "valid first"}, {"name": "broken", "talents": []}]), encoding="utf-8")
            obj = self.bare_app()
            obj.cfg["builds"] = [{"name": "Existing", "attributes": {}, "talents": {}}]
            obj.refresh_builds = Mock()
            before = deepcopy(obj.cfg)
            with patch.object(self.app.filedialog, "askopenfilename", return_value=str(path)), \
                 patch.object(self.app.messagebox, "showerror") as error, patch.object(self.app, "save_cfg") as save:
                obj.import_builds()
            error.assert_called_once()
            save.assert_not_called()
            obj.refresh_builds.assert_not_called()
            self.assertEqual(obj.cfg, before)

    def test_valid_build_import_renames_duplicate_and_preserves_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid-builds.json"
            path.write_text(json.dumps({"builds": [{"name": "Existing", "attributes": {"armor": {"weight": 0}}}]}), encoding="utf-8")
            obj = self.bare_app()
            obj.cfg["builds"] = [{"name": "Existing", "attributes": {}, "talents": {}}]
            obj.refresh_builds = Mock()
            before = deepcopy(obj.cfg["settings"])
            with patch.object(self.app.filedialog, "askopenfilename", return_value=str(path)), \
                 patch.object(self.app.messagebox, "showinfo"), patch.object(self.app, "save_cfg") as save:
                obj.import_builds()
            self.assertEqual([b["name"] for b in obj.cfg["builds"]], ["Existing", "Existing (2)"])
            self.assertEqual(obj.cfg["settings"], before)
            self.assertEqual(obj.cfg["builds"][1]["attributes"]["armor"]["weight"], 0)
            save.assert_called_once()

    def test_concurrent_claude_prompts_are_isolated_and_removed(self):
        barrier = threading.Barrier(2)
        seen = []
        lock = threading.Lock()
        def run(args, **kwargs):
            path = Path(args[args.index("--system-prompt-file") + 1])
            barrier.wait(timeout=5)
            text = path.read_text(encoding="utf-8")
            with lock:
                seen.append((path, text))
            return SimpleNamespace(returncode=0, stdout=json.dumps({"result": text}), stderr="")
        with tempfile.TemporaryDirectory() as directory, patch.object(self.app, "BASE", Path(directory)), \
             patch.object(self.app, "find_claude_cli", return_value="mock-claude"), patch("subprocess.run", side_effect=run):
            with ThreadPoolExecutor(max_workers=2) as executor:
                calls = [executor.submit(self.app.ask_claude_code, "test-model", prompt,
                                         [{"role": "user", "content": "question"}]) for prompt in ("first prompt", "second prompt")]
                results = [call.result(timeout=8) for call in calls]
            self.assertEqual(set(results), {"first prompt", "second prompt"})
            self.assertEqual(len({path for path, _ in seen}), 2)
            self.assertTrue(all(not path.exists() for path, _ in seen))

    def test_claude_prompt_is_removed_after_timeout_or_error(self):
        for fail in ("timeout", "error"):
            seen = []
            def run(args, **kwargs):
                path = Path(args[args.index("--system-prompt-file") + 1])
                self.assertEqual(path.read_text(encoding="utf-8"), "private test prompt")
                seen.append(path)
                if fail == "timeout":
                    raise subprocess.TimeoutExpired(args, 1)
                return SimpleNamespace(returncode=1, stdout="", stderr="mock CLI failed")
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as directory:
                with patch.object(self.app, "BASE", Path(directory)), \
                     patch.object(self.app, "find_claude_cli", return_value="mock-claude"), \
                     patch("subprocess.run", side_effect=run), self.assertRaises(RuntimeError):
                    self.app.ask_claude_code("test-model", "private test prompt", [{"role": "user", "content": "question"}])
                self.assertEqual(len(seen), 1)
                # Check before TemporaryDirectory cleans up, so this proves the
                # application removed the prompt even on a failure path.
                self.assertFalse(seen[0].exists())

    def test_poll_applies_only_current_translation_results(self):
        obj = self.bare_app()
        obj._translation_jobs = SimpleNamespace(is_current=lambda token: token == 7)
        old, current = Mock(), Mock()
        obj.results.put(("translation", 6, old))
        obj.results.put(("translation", 7, current))
        obj.poll()
        old.assert_not_called()
        current.assert_called_once_with()
        self.assertTrue(obj.results.empty())
        obj.root.after.assert_called_once()

    def test_translation_posts_queue_callbacks_for_ui_thread(self):
        obj = self.bare_app()
        obj._translation_jobs = SimpleNamespace(is_current=lambda token: token == 7)
        old, current = Mock(), Mock()
        obj._post_translation(6, old)
        obj._post_translation(7, current)
        old.assert_not_called()
        current.assert_not_called()
        self.assertEqual(obj.results.get_nowait(), ("translation", 7, current))
        self.assertTrue(obj.results.empty())

    def translation_app(self, translate):
        obj = self.bare_app()
        obj._translation_jobs = SimpleNamespace(is_current=lambda token: token == 7)
        obj.lock = threading.Lock()
        obj.timings = SimpleNamespace(measure=lambda name: nullcontext())
        obj.lt_ocr = Mock(return_value=[])
        obj.lt_translator = Mock(return_value=SimpleNamespace(translate=translate))
        obj._lt_failure = Mock()
        obj._lt_show = Mock()
        obj._task_seen = Mock()
        obj._lt_last_sig = "previous successful screen"
        return obj

    def test_failed_translation_can_retry_identical_screen(self):
        translate = Mock(side_effect=[RuntimeError("temporary model error"), ["Görevi tamamlayın"]])
        obj = self.translation_app(translate)
        blocks = [("Complete the objective", (0, 0, 200, 20))]
        with patch.object(self.app.livetranslate, "blocks_from_lines", return_value=blocks):
            obj._lt_run(None, {}, token=7)
            self.assertEqual(obj._lt_last_sig, "previous successful screen")
            self.assertTrue(obj.results.empty())
            obj._lt_failure.assert_called_once()
            obj._lt_run(None, {}, token=7)
        self.assertEqual(translate.call_count, 2)
        # The success signature commits when the current callback reaches poll.
        self.assertEqual(obj._lt_last_sig, "previous successful screen")
        obj.poll()
        self.assertEqual(obj._lt_last_sig, "Complete the objective")
        obj._lt_show.assert_called_once()

    def test_empty_or_mismatched_translation_is_not_cached(self):
        for output in ([], [""], [None], ["one", "extra"]):
            obj = self.translation_app(Mock(return_value=output))
            with self.subTest(output=output), patch.object(self.app.livetranslate, "blocks_from_lines",
                                                          return_value=[("Objective", (0, 0, 100, 20))]):
                obj._lt_run(None, {}, token=7)
            self.assertEqual(obj._lt_last_sig, "previous successful screen")
            self.assertTrue(obj.results.empty())
            obj._lt_failure.assert_called_once()
            obj._lt_show.assert_not_called()

    def test_inplace_repositions_identical_text_when_source_moves(self):
        obj = self.translation_app(Mock(return_value=["Hedef"]))
        obj.cfg["settings"]["tr_mode"] = "inplace"
        area = {"left": 0, "top": 0, "width": 1000, "height": 700}
        for box in [(10, 10, 100, 30), (200, 200, 290, 220)]:
            with patch.object(self.app.livetranslate, "blocks_from_lines", return_value=[("Objective", box)]) as blocks:
                obj._lt_run(None, area, token=7)
                self.assertTrue(blocks.call_args.kwargs["preserve_lines"])
            obj.poll()
        self.assertEqual(obj._lt_show.call_count, 2)
        self.assertEqual(obj._lt_show.call_args.args[0][0][2], (200, 200, 290, 220))

    def test_empty_screen_removes_previous_overlay(self):
        obj = self.translation_app(Mock())
        obj._lt_hide = Mock()
        with patch.object(self.app.livetranslate, "blocks_from_lines", return_value=[]):
            obj._lt_run(None, {}, token=7)
        obj.poll()
        obj._lt_hide.assert_called_once()
        self.assertIsNone(obj._lt_last_sig)

    def test_online_voice_switch_updates_both_controls_and_privacy(self):
        obj = self.bare_app()
        obj.vp_online, obj.ts_online_voice, obj.lt_privacy_lbl = Mock(), Mock(), Mock()
        obj._translation_privacy = Mock(return_value="Text goes to the speech service")
        with patch.object(self.app, "save_cfg") as save:
            obj.set_online_voice(True)
        self.assertTrue(obj.cfg["settings"]["voice_online"])
        obj.vp_online.set.assert_called_once_with(True)
        obj.ts_online_voice.set.assert_called_once_with(True)
        obj.lt_privacy_lbl.config.assert_called_once_with(text="Text goes to the speech service")
        save.assert_called_once_with(obj.cfg)

    def test_translation_superseded_during_model_run_is_discarded(self):
        current = [7]
        def translate(text):
            current[0] = 8
            return ["Geç kalmış çeviri"]
        obj = self.translation_app(Mock(side_effect=translate))
        obj._translation_jobs = SimpleNamespace(is_current=lambda token: token == current[0])
        with patch.object(self.app.livetranslate, "blocks_from_lines", return_value=[("Objective", (0, 0, 100, 20))]):
            obj._lt_run(None, {}, token=7)
        self.assertTrue(obj.results.empty())
        self.assertEqual(obj._lt_last_sig, "previous successful screen")
        obj._lt_show.assert_not_called()
        obj._task_seen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
