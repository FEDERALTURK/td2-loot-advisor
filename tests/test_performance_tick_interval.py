"""Idle/hidden windows should not probe game focus every second."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class PerformanceTickIntervalTests(unittest.TestCase):
    def test_hidden_window_uses_long_interval_without_focus_probe(self):
        root = SimpleNamespace(state=Mock(return_value="iconic"), after=Mock())
        instance = SimpleNamespace(_closing=False, root=root, cfg={"settings": {}}, game_on=False,
                                   _performance_tick=lambda: None)
        with patch.object(app.game_runtime, "plan", return_value=SimpleNamespace(suspend_animations=True, ui_animation_multiplier=0.0)), \
             patch.object(app.performance, "get_policy", return_value=SimpleNamespace(suspend_animations=True, ui_animation_multiplier=0.0)), \
             patch.object(app, "game_active") as focused:
            app.App._performance_tick(instance)
        focused.assert_not_called()
        self.assertEqual(root.after.call_args.args[0], 4000)


if __name__ == "__main__":
    unittest.main()
