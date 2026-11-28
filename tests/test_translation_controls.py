"""Regression tests for statistics/speech state collision and live-job starvation."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
app._load_deferred_modules()
import overlay
import livetranslate


class TranslationControlsTests(unittest.TestCase):
    def test_turkish_key_event_uses_unicode_character_not_tk_keysym(self):
        event = SimpleNamespace(char="ç", keysym="cedilla")
        self.assertEqual(app.hotkey_key_name(event), "ç")
        event = SimpleNamespace(char="ş", keysym="scedilla")
        self.assertEqual(app.hotkey_key_name(event), "ş")
        event = SimpleNamespace(char="", keysym="F8")
        self.assertEqual(app.hotkey_key_name(event), "f8")

    def test_shortcut_keycap_tokens_are_display_only_and_preserve_turkish_keys(self):
        self.assertEqual(app.shortcut_keycap_tokens("w"), ("W",))
        self.assertEqual(app.shortcut_keycap_tokens("<ctrl>+<shift>+t"),
                         ("CTRL", "SHIFT", "T"))
        self.assertEqual(app.shortcut_keycap_tokens("ç"), ("Ç",))
        self.assertEqual(app.shortcut_keycap_tokens("<f8>"), ("F8",))
        self.assertEqual(app.shortcut_keycap_tokens("Tuşa basın…"), ("…",))

    def test_local_translation_memory_is_normalized_and_preferred(self):
        import tempfile
        path = Path(tempfile.mkdtemp()) / "translation_memory.json"
        local = livetranslate.LocalMemory(path)
        self.assertTrue(local.put("  Head   to the White House. ", "Beyaz Saray'a git."))
        self.assertEqual(local.get("head to the white house."), "Beyaz Saray'a git.")
        loaded = livetranslate.LocalMemory(path)
        self.assertEqual(loaded.get("HEAD TO THE WHITE HOUSE."), "Beyaz Saray'a git.")
        shared = livetranslate.LocalMemory()
        shared.put("Head to the White House.", "Paylaşılmış çeviri")
        self.assertEqual(livetranslate.MemoryChain(local, shared).get("Head to the White House."), "Beyaz Saray'a git.")
        self.assertTrue(local.remove("HEAD TO THE WHITE HOUSE."))
        self.assertIsNone(local.get("Head to the White House."))

    def test_translation_font_scales_softly_with_capture_area(self):
        self.assertEqual(overlay.adaptive_font_size(15, 1920, 1080), 15)
        self.assertGreater(overlay.adaptive_font_size(15, 3440, 1440), 15)
        self.assertGreaterEqual(overlay.adaptive_font_size(15, 1200, 2520), 12)
        self.assertLessEqual(overlay.adaptive_font_size(15, 7680, 4320), 30)

    def test_render_exception_preserves_history_and_uses_panel(self):
        obj = app.App.__new__(app.App)
        obj.cfg = {"settings": {"tr_mode": "inplace"}}
        for name in ("_lt_log", "_lt_status", "_lt_hist_fill", "_lt_after", "_lt_hide", "_lt_panel_fallback"):
            setattr(obj, name, Mock())
        obj._lt_show_inplace = Mock(side_effect=RuntimeError("draw failed"))
        pairs = [("Rewards", "Ödüller", (0, 0, 100, 40))]
        with self.assertLogs("td2", level="ERROR"):
            obj._lt_show(pairs, {"width": 100, "height": 100}, 0)
        self.assertEqual(obj.lt_hist, [("Rewards", "Ödüller")])
        obj._lt_panel_fallback.assert_called_once_with(pairs)

    def test_panel_fallback_closes_overlay_and_preserves_translation(self):
        obj = app.App.__new__(app.App)
        obj._lt_hide = Mock()
        obj._lt_status = Mock()
        obj.lt_out = Mock()
        obj._lt_panel_fallback([("Rewards", "Ödüller", (0, 0, 100, 40))])
        obj._lt_hide.assert_called_once()
        self.assertEqual(obj.lt_out.config.call_args.kwargs["text"], "Ödüller")

    def test_empty_layout_uses_panel_without_another_overlay(self):
        obj = app.App.__new__(app.App)
        obj.root = Mock()
        obj.cfg = {"settings": {}}
        obj.lt_style = Mock(return_value={})
        obj._lt_panel_fallback = Mock()
        pairs = [("Rewards", "Ödüller", (0, 0, 100, 40))]
        with patch.object(app.overlay, "InPlace") as renderer, \
             patch.object(app.overlay, "layout", return_value=[]):
            obj._lt_show_inplace(pairs, {"width": 100, "height": 100})
            renderer.return_value.hide.assert_called_once()
            renderer.return_value.show.assert_not_called()
        obj._lt_panel_fallback.assert_called_once_with(pairs)

    def test_building_statistics_does_not_create_a_speech_session(self):
        obj = app.App.__new__(app.App)
        obj.tabs = {"stats": Mock()}
        obj._build_community = Mock()
        obj.refresh_stats_tab = Mock()
        obj.lt_start = Mock(return_value=True)
        obj.toast = Mock()
        with patch.object(app, "CtkFrame"), patch.object(app, "CtkLabel"), \
             patch.object(app, "CtkComboBox"), patch.object(app, "CtkButton"), \
             patch.object(app.tk, "Canvas"):
            obj.build_stats()
        self.assertIsNone(getattr(obj, "sp", None))
        obj.lt_toggle()
        obj.lt_start.assert_called_once_with(quiet=True)

    def test_rebuilding_statistics_preserves_active_speech_session(self):
        obj = app.App.__new__(app.App)
        obj.tabs = {"stats": Mock()}
        obj._build_community = obj.refresh_stats_tab = Mock()
        session = obj.sp = Mock()
        with patch.object(app, "CtkFrame"), patch.object(app, "CtkLabel"), \
             patch.object(app, "CtkComboBox"), patch.object(app, "CtkButton"), \
             patch.object(app.tk, "Canvas"):
            obj.build_stats()
        self.assertIs(obj.sp, session)

    def run_loop(self, active=0, pending=0):
        obj = app.App.__new__(app.App)
        obj.cfg = {"settings": {"only_game_active": False}}
        obj.lt_area = Mock(return_value={"width": 800, "height": 600})
        obj._policy = Mock(return_value=SimpleNamespace(translation_poll_s=.1))
        obj._translation_jobs = Mock()
        obj._translation_jobs.stats.return_value = {"active": active, "pending": pending}
        obj._queue_translation = Mock()
        stop = Mock()
        stop.wait.return_value = False
        stop.is_set.side_effect = [False, False, False, True]
        with patch.object(app.capture, "Grabber"), patch.object(app, "dist", return_value=0):
            obj._lt_loop(stop)
        return obj._queue_translation

    def test_auto_scan_does_not_cancel_active_translation(self):
        self.run_loop(active=1).assert_not_called()

    def test_auto_scan_does_not_replace_pending_manual_translation(self):
        self.run_loop(pending=1).assert_not_called()

    def test_idle_translation_worker_receives_stable_frame(self):
        self.run_loop().assert_called_once()


if __name__ == "__main__":
    unittest.main()
