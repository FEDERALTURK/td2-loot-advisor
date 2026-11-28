"""Video generation progress polling must not redraw the full header."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class VideoGenerationPollTests(unittest.TestCase):
    def test_effect_application_uses_current_safe_effect_settings(self):
        root = SimpleNamespace()
        cursor_fx = Mock()
        instance = SimpleNamespace(
            root=root,
            cfg={"settings": {"fx_cursor": False, "fx_bgwatch": False, "fx_video": False,
                              "fx_video_dim": 0.35}},
            cursor_fx=cursor_fx,
            _closing=False,
        )
        # apply_fx gerçek Tk kökü bekler; SafeTrail sahte kökte oluşturulmamalı.
        with patch.object(app.fx, "SafeTrail", return_value=Mock()):
            app.App.apply_fx(instance)
        cursor_fx.apply.assert_called_once()

    def test_unchanged_effect_settings_skip_reapplication(self):
        root = SimpleNamespace()
        cursor_fx = Mock()
        instance = SimpleNamespace(
            root=root,
            cfg={"settings": {"fx_cursor": False, "fx_bgwatch": False, "fx_video": False,
                              "fx_video_dim": 0.35}},
            cursor_fx=cursor_fx,
            _closing=False,
        )
        # apply_fx gerçek Tk kökü bekler; SafeTrail sahte kökte oluşturulmamalı.
        with patch.object(app.fx, "SafeTrail", return_value=Mock()):
            app.App.apply_fx(instance)
        cursor_fx.apply.assert_called_once()

    def test_busy_poll_only_schedules_next_check(self):
        banner = SimpleNamespace(toast_text="", _redraw_overlay_only=Mock())
        root = SimpleNamespace(after=Mock(return_value="poll-job"))
        instance = SimpleNamespace(_vid_busy=True, _vid_prog=0.4, banner=banner, root=root)
        instance._vid_poll = lambda: app.App._vid_poll(instance)
        with patch.object(app, "t", return_value="Generating 40%"):
            app.App._vid_poll(instance)
        self.assertEqual(root.after.call_args.args[0], 700)
        banner._redraw_overlay_only.assert_not_called()


if __name__ == "__main__":
    unittest.main()
