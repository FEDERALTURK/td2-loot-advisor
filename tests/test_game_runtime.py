"""Faz 1 oyun yardımcısı çalışma planı: yalnız pencere odağına göre karar verir."""
from pathlib import Path
import queue
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import game_runtime
import app


class RuntimePlanTests(unittest.TestCase):
    def test_game_focus_keeps_passive_helpers_available(self):
        plan = game_runtime.plan({"only_game_active": True}, game_focused=True)
        self.assertEqual(plan.state, "game_focus")
        self.assertTrue(plan.passive_capture)
        self.assertTrue(plan.passive_translation)
        self.assertEqual(plan.wait_s, 0)

    def test_background_focus_pauses_passive_helpers_when_requested(self):
        plan = game_runtime.plan({"only_game_active": True}, game_focused=False)
        self.assertEqual(plan.state, "background")
        self.assertFalse(plan.passive_capture)
        self.assertFalse(plan.passive_translation)
        self.assertGreaterEqual(plan.wait_s, 1)

    def test_desktop_mode_preserves_existing_opt_out_behavior(self):
        plan = game_runtime.plan({"only_game_active": False}, game_focused=False)
        self.assertEqual(plan.state, "desktop")
        self.assertTrue(plan.passive_capture)
        self.assertTrue(plan.passive_translation)

    def test_hidden_game_focus_is_reported_without_changing_capture_policy(self):
        plan = game_runtime.plan({"only_game_active": True}, game_focused=True, app_hidden=True)
        self.assertEqual(plan.state, "game_focus_tray")
        self.assertTrue(plan.passive_capture)
        self.assertTrue(plan.passive_translation)

    def test_background_autoscan_waits_without_capturing_the_desktop(self):
        class Stop:
            def __init__(self): self.stopped, self.waits = False, []
            def is_set(self): return self.stopped
            def wait(self, seconds): self.waits.append(seconds); self.stopped = True; return True

        stop = Stop()
        obj = SimpleNamespace(
            cfg={"settings": {"only_game_active": True}},
            _policy=lambda: SimpleNamespace(scan_poll_s=0.1),
            scan_area=Mock(return_value={"left": 0, "top": 0, "width": 10, "height": 10}),
            results=queue.Queue(),
            last_err="",
        )
        with patch.object(app, "game_active", return_value=False), \
                patch.object(app.capture, "default", side_effect=AssertionError("desktop capture must not run")):
            app.App._auto_loop(obj, stop)
        self.assertEqual(stop.waits, [1.5])


if __name__ == "__main__":
    unittest.main()
