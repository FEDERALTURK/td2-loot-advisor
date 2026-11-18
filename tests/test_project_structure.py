"""Low-risk package layout and visual frame-budget regression checks."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import splash
import fx
import ui_theme
from td2app.ui import splash as packaged_splash
from td2app.ui import fx as packaged_fx
from td2app.ui import ui_theme as packaged_theme


class ProjectStructureTests(unittest.TestCase):
    def test_tests_do_not_embed_live_feed_ids(self):
        """Bot-managed feed IDs belong in fixtures, not in test source literals."""
        feed_ids = set()
        for filename, key in (("news_feed.json", "items"), ("tasks_feed.json", "tasks")):
            payload = json.loads((ROOT / "meta" / filename).read_text(encoding="utf-8"))
            for item in payload.get(key, []):
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    feed_ids.add(item["id"])

        violations = []
        for path in sorted((ROOT / "tests").glob("*.py")):
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for feed_id in feed_ids:
                    if feed_id in line:
                        violations.append(
                            f"Test, bot tarafından güncellenen canlı veriye bağlı: "
                            f"{path.relative_to(ROOT)}:{line_no} '{feed_id}'. Fixture kullan."
                        )
        self.assertFalse(violations, "\n".join(violations))

    def test_ui_compatibility_modules_forward_to_grouped_package(self):
        self.assertIs(splash.IntroSplash, packaged_splash.IntroSplash)
        self.assertIs(fx.Transition, packaged_fx.Transition)
        self.assertIs(ui_theme.apply, packaged_theme.apply)

    def test_intro_and_tab_motion_are_capped_at_thirty_fps(self):
        self.assertEqual(packaged_splash.IntroSplash.FPS, 30)
        self.assertAlmostEqual(packaged_splash.IntroSplash.FRAME_INTERVAL_MS, 1000 / 30)
        source = (ROOT / "td2app" / "ui" / "fx.py").read_text(encoding="utf-8")
        self.assertIn("self.root.after(33", source)

    def test_tactical_navigation_is_lightweight_and_keeps_safe_transition_styles(self):
        self.assertTrue(hasattr(packaged_fx, "NavMotif"))
        self.assertTrue(hasattr(packaged_fx, "CommandRibbon"))
        source = (ROOT / "td2app" / "ui" / "fx.py").read_text(encoding="utf-8")
        self.assertIn("fare olayı bağlamaz", source)
        self.assertIn("self.after(180", source)
        self.assertIn("FPS = 30", source)
        self.assertIn("gerçek paneli kaydırmaz", source)
        self.assertIn('style="soft"', source)
        self.assertIn('(\"soft\", \"tactical\")', source)

    def test_three_selectable_themes_apply_and_keep_legacy_default(self):
        """Üç tema seçilebilir; eski default kaydı SHD temasına eşlenir."""
        modes = ("shd_tactical", "kaivolt", "clean_console")
        self.assertEqual(packaged_theme.THEME_MODES[:3], modes)
        self.assertTrue(set(modes).issubset(packaged_theme.THEME_LABELS))
        self.assertEqual(packaged_theme.canonical_mode("default"), "shd_tactical")
        accents = set()
        for mode in modes:
            settings = {}
            self.assertTrue(packaged_theme.apply_pack(settings, mode))
            self.assertEqual(settings["ui_theme"], mode)
            expected_nav = "flat" if mode == "kaivolt" else "tactical"
            expected_style = "soft" if mode == "kaivolt" else "tactical"
            self.assertEqual(settings["ui_nav_layout"], expected_nav)
            self.assertEqual(settings["fx_transition_style"], expected_style)
            self.assertEqual(settings["ui_layout"], "standard")
            accents.add(settings["fx_trail_color"])
        self.assertEqual(len(accents), 3)
        self.assertTrue(packaged_theme.apply_pack({}, "default"))
        legacy = {}
        self.assertTrue(packaged_theme.apply_pack(legacy, "field_terminal"))
        self.assertEqual(legacy["ui_layout"], "field_command")
        self.assertFalse(packaged_theme.apply_pack({}, "not-a-theme"))

    def test_field_command_shell_code_still_supports_map_scan_variant(self):
        """`_build_field_command_shell` kod olarak kapsam dışı bırakıldı (silinmedi); fx.py'deki
        "field" varyantının kendisi hâlâ var olmalı, yeni tek temadan tetiklenmese de."""
        source = (ROOT / "td2app" / "ui" / "fx.py").read_text(encoding="utf-8")
        self.assertIn('self.variant == "field"', source)
        self.assertIn("SHD FIELD TERMINAL", source)

    def test_structure_guide_describes_staged_migration(self):
        guide = ROOT / "docs" / "architecture" / "PROJECT_STRUCTURE.md"
        self.assertTrue(guide.is_file())
        text = guide.read_text(encoding="utf-8")
        self.assertIn("td2app/ui/", text)
        self.assertIn("testable", text)

    def test_native_cursor_bridge_is_opt_in(self):
        """Varsayılan imleç yolu Tk @.cur olmalı; Win32 subclass değil."""
        cursor = packaged_fx.CursorFX(None, ROOT / "art" / "cursors")
        self.assertFalse(cursor._native_bridge_enabled)


if __name__ == "__main__":
    unittest.main()
