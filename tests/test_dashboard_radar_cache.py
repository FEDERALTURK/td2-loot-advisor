"""Dashboard scene contract for the current HUD implementation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class DashboardRadarCacheTests(unittest.TestCase):
    def test_dashboard_uses_current_scene_api(self):
        self.assertTrue(hasattr(app.ui_hud, "DashboardScene"))
        self.assertTrue(hasattr(app.ui_hud.DashboardScene, "set_snapshot"))
        source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertIn("self.dash_scene = ui_hud.DashboardScene", source)

    def test_removed_radar_method_is_not_required_by_app(self):
        source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("_draw_dashboard_radar", source)


if __name__ == "__main__":
    unittest.main()
