"""Readiness signaling for OCR warm-up and scan dispatch feedback."""
from pathlib import Path
import sys
import threading
import queue
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ocr_backend as ob


class WarmupReadinessTests(unittest.TestCase):
    def test_non_rapid_engine_returns_already_set_event(self):
        event = ob.Engine("tesseract").warm_up()
        self.assertIsInstance(event, threading.Event)
        self.assertTrue(event.is_set())

    def test_rapid_event_is_set_after_inference_finishes(self):
        entered, release = threading.Event(), threading.Event()
        engine = ob.Engine("tesseract")
        engine.name = "rapidocr"

        def infer(_image):
            entered.set()
            release.wait(2)
            return None

        with patch.object(ob, "_rapid", return_value=infer), patch.object(ob, "_np", side_effect=lambda image: image):
            ready = engine.warm_up()
            self.assertTrue(entered.wait(1))
            self.assertFalse(ready.is_set())
            release.set()
            self.assertTrue(ready.wait(1))

    def test_app_scan_hotkey_reports_warmup_without_blocking(self):
        import app

        feedback = queue.Queue()
        ready = threading.Event()
        instance = SimpleNamespace(
            scan_area=lambda: {"left": 0, "top": 0, "width": 10, "height": 10},
            cfg={"settings": {"only_game_active": False}},
            _ocr_ready_event=ready,
            _scan_feedback_at=0.0,
            results=feedback,
            lock=threading.Lock(),
        )
        instance._queue_scan_feedback = lambda message: app.App._queue_scan_feedback(instance, message)
        with patch.object(app, "game_active", return_value=True):
            app.App.trigger(instance)
        self.assertEqual(feedback.get_nowait()[0], "scan_feedback")

    def test_app_scan_hotkey_reports_busy_lock(self):
        import app

        feedback = queue.Queue()
        lock = threading.Lock()
        lock.acquire()
        instance = SimpleNamespace(
            scan_area=lambda: {"left": 0, "top": 0, "width": 10, "height": 10},
            cfg={"settings": {"only_game_active": False}},
            _ocr_ready_event=threading.Event(),
            _scan_feedback_at=0.0,
            results=feedback,
            lock=lock,
        )
        instance._queue_scan_feedback = lambda message: app.App._queue_scan_feedback(instance, message)
        try:
            with patch.object(app, "game_active", return_value=True):
                app.App.trigger(instance)
            self.assertEqual(feedback.get_nowait()[0], "scan_feedback")
        finally:
            lock.release()

    def test_critical_pages_are_prioritized_but_not_built_synchronously(self):
        import app

        calls = []
        def build_dash(): calls.append("build_dash")
        def build_build_tool(): calls.append("build_build_tool")
        def build_stash(): calls.append("build_stash")
        def build_translate(): calls.append("build_translate")
        def build_asistan(): calls.append("build_asistan")
        def build_settings(): calls.append("build_settings")
        builders = [build_dash, build_build_tool, build_stash, build_translate, build_asistan, build_settings]
        instance = SimpleNamespace(_ui_builders=builders, _ui_build_errors=[])
        app.App._build_critical_ui_pages(instance)
        names = [builder.__name__ for builder in instance._ui_builders]
        self.assertEqual(names, ["build_dash", "build_build_tool"])
        self.assertEqual(set(calls), {"build_stash", "build_translate", "build_asistan", "build_settings"})


if __name__ == "__main__":
    unittest.main()
