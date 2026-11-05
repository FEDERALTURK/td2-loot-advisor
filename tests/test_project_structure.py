"""Low-risk package layout and visual frame-budget regression checks."""
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

    def test_single_theme_applies_tactical_nav_and_transitions(self):
        """Tek, sabit tema (eski çoklu tema/paket sistemi kaldırıldı): uygulanınca
        Division 2'ye benzer kademeli (tactical) kenar çubuğu ve geçiş temposu gelir."""
        self.assertEqual(tuple(packaged_theme.PALETTES.keys()), ("default",))
        self.assertEqual(packaged_theme.THEME_MODES, ("default",))
        settings = {}
        self.assertTrue(packaged_theme.apply_pack(settings, "default"))
        self.assertEqual(settings["ui_nav_layout"], "tactical")
        self.assertEqual(settings["fx_transition_style"], "tactical")
        self.assertEqual(settings["ui_layout"], "standard")
        self.assertFalse(packaged_theme.apply_pack({}, "field_terminal"))   # kaldırılan eski paket adı artık geçersiz

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
