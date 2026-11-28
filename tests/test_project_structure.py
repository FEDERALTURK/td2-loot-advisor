"""Low-risk package layout and visual frame-budget regression checks."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import splash
import fx
import ui_theme
from td2app.ui import splash as packaged_splash
from td2app.ui import fx as packaged_fx
from td2app.ui import ui_theme as packaged_theme
from td2app.ui.ctk_compat import _combo_control_width, _dropdown_character_width


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

    def test_combo_popup_width_fits_long_values(self):
        short = _dropdown_character_width(["A", "B"])
        long = _dropdown_character_width(["Very long specialization label"])
        turkish = _dropdown_character_width(["Çeviri motoru: Türkçe / İngilizce"])
        self.assertGreaterEqual(short, 30)
        self.assertGreater(long, short)
        self.assertGreater(turkish, short)
        self.assertLessEqual(turkish, 72)

    def test_ctk_combo_control_width_does_not_collapse_to_one_letter(self):
        self.assertGreaterEqual(_combo_control_width(10, ["DEBUG", "WARNING"]), 140)
        self.assertGreater(_combo_control_width(18, ["Survivalist", "Demolitionist"]), 140)
        self.assertLessEqual(_combo_control_width(48, ["Build"]), 420)

    def test_intro_and_tab_motion_are_capped_at_thirty_fps(self):
        self.assertEqual(packaged_splash.IntroSplash.FPS, 30)
        self.assertAlmostEqual(packaged_splash.IntroSplash.FRAME_INTERVAL_MS, 1000 / 30)
        source = (ROOT / "td2app" / "ui" / "fx.py").read_text(encoding="utf-8")
        self.assertIn("self.root.after(33", source)

    def test_intro_reveal_waits_for_ui_readiness_gate(self):
        source = (ROOT / "td2app" / "ui" / "splash.py").read_text(encoding="utf-8")
        self.assertIn("self.ready", source)
        self.assertIn("self.ready()", source)
        app_source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('ready=lambda: bool(getattr(self, "_ui_ready", False))', app_source)

    def test_gui_launcher_does_not_keep_a_console_over_the_ui(self):
        source = (ROOT / "scripts" / "run.bat").read_text(encoding="utf-8")
        self.assertIn("pythonw.exe", source)
        self.assertIn("start \"\" /b", source)
        self.assertIn(":console_launch", source)

    def test_rebuild_cleans_transient_visual_windows(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("self._destroy_transient_windows()", source)
        for name in ("_lt_win", "_assistant_hud", "_quiz_pop", "_recovery_window"):
            self.assertIn(f'"{name}"', source)

    def test_shutdown_cancels_deferred_tk_callbacks_before_destroy(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("self._cancel_pending_ui_callbacks()", source)
        self.assertIn("self._destroy_child_windows()", source)
        self.assertIn("self._after_ids", source)
        self.assertIn("def _cancel_pending_ui_callbacks", source)
        self.assertIn("def _destroy_child_windows", source)
        self.assertIn("if not getattr(app, \"_closing\", False)", source)

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
        self.assertIn("field_clean", packaged_theme.THEME_MODES)
        self.assertEqual(packaged_theme.THEME_LABELS["field_clean"], "Field Clean")
        self.assertEqual(packaged_theme.PALETTES["kaivolt"]["accent"], "#b69ae8")
        for mode in ("kaivolt", "shd_tactical", "field_clean"):
            palette = packaged_theme.PALETTES[mode]
            self.assertGreaterEqual(packaged_theme.contrast(palette["muted"], palette["surface"]), 4.5)
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

    def test_hybrid_typography_contract_and_turkish_fallback(self):
        self.assertEqual(packaged_theme.DESIGN_TOKENS["font"]["latin_subset"], "latin-ext")
        self.assertEqual(packaged_theme.DESIGN_TOKENS["type"]["body_line_height"], 1.5)
        self.assertAlmostEqual(packaged_theme.DESIGN_TOKENS["type"]["label_tracking"], 0.10)
        self.assertGreaterEqual(packaged_theme.DESIGN_TOKENS["type"]["body"], 13)
        self.assertGreaterEqual(packaged_theme.DESIGN_TOKENS["type"]["control"], 12)
        self.assertGreaterEqual(packaged_theme.DESIGN_TOKENS["control"]["height"], 38)
        self.assertEqual(packaged_theme.DESIGN_TOKENS["focus"]["ring_width"], 2)
        self.assertEqual(packaged_theme.font_spec("body", 11), (packaged_theme.FONT, 11, "normal"))
        self.assertEqual(packaged_theme.font_spec("display", 12), (packaged_theme.FONT_DISPLAY, 12, "bold"))
        self.assertEqual(packaged_theme.font_spec("body", 12, numeric=True), (packaged_theme.FONT_MONO, 12, "normal"))
        self.assertEqual(packaged_theme.label_text("keep / İnceleme"), "KEEP / İNCELEME")
        with patch.object(packaged_theme.tkfont, "families", return_value=("Inter", "Chakra Petch", "JetBrains Mono")):
            self.assertEqual(packaged_theme.resolve_fonts(object()), {
                "body": "Inter", "display": "Chakra Petch", "mono": "JetBrains Mono"})
        turkish = "ğüşıİöç"
        self.assertEqual(packaged_theme.label_text(turkish), turkish.upper())

    def test_app_does_not_bypass_hybrid_font_tokens(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('font=("Segoe UI"', source)
        self.assertNotIn('font=("Consolas"', source)
        self.assertNotIn('font=(ui_theme.FONT_SEMI, 11), width=2', source)

    def test_sync_progressbar_uses_cross_backend_start_signature(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("pb.start()", source)
        self.assertNotIn("pb.start(12)", source)

    def test_game_data_resolves_short_set_aliases_to_canonical_names(self):
        self.assertEqual(packaged_theme.__name__, "td2app.ui.ui_theme")
        import gamedata
        self.assertEqual(gamedata.resolve_name("Striker", ["Striker's Battlegear"]),
                         "Striker's Battlegear")

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

    def test_trail_and_cursor_preview_do_not_cover_or_label_the_ui(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("fx.TrailFX(self.root", source)
        self.assertIn("click_through=_trail_window_hook", source)
        self.assertIn("click_through(win)", source)
        fx_source = (ROOT / "td2app" / "ui" / "fx.py").read_text(encoding="utf-8")
        self.assertIn("self.click_through(self.win)", fx_source)

    def test_agent_clock_resyncs_on_window_move_without_waiting_for_render_timer(self):
        fx_source = (ROOT / "td2app" / "ui" / "fx.py").read_text(encoding="utf-8")
        self.assertIn('("<Map>", "<Configure>", "<Unmap>")', fx_source)
        self.assertIn("self._place(geo)", fx_source)
        self.assertIn("def _resync(self, _e=None)", fx_source)
        self.assertIn("self.root.unbind(sequence, funcid)", fx_source)

    def test_shortcut_fields_have_visible_keycap_width_and_keep_raw_binding(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8-sig")
        self.assertIn('self.shortcut_keycap_hosts = {}', source)
        self.assertIn('keycap_host = CtkFrame(box, width=210, height=44', source)
        self.assertIn('self._render_shortcut_keycaps(key)', source)
        self.assertIn('shortcut_keycap_tokens(var.get())', source)
        self.assertIn('shadow = CtkFrame(host, width=width, height=42', source)
        self.assertIn('face = CtkFrame(shadow, width=width, height=38', source)
        self.assertIn('font=ui_theme.font_spec("display", 13)', source)
        self.assertIn('candidate.update({k: v.get().strip() for k, v in self.shortcut_vars.items()})', source)
        self.assertIn('CtkLabel(prev, text="", image=ph', source)
        self.assertNotIn("# Fare izi devre dışı", source)


if __name__ == "__main__":
    unittest.main()
