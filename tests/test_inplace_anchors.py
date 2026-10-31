"""Source-anchored in-place translation, including project-menu regressions."""
import json
import os
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import livetranslate as lt
import overlay
import ocr_backend


def measure(pt):
    return lambda s: len(s) * pt / .75 * .55, pt / .75 * 1.3


class InplaceTests(unittest.TestCase):
    def test_project_labels_remain_separate_source_rectangles(self):
        lines = [("Season Pass Project", (20, 20, 240, 40), .99),
                 ("DCD Headquarters", (20, 44, 210, 64), .99),
                 ("Base of Operations", (20, 68, 220, 88), .99)]
        result = lt.blocks_from_lines(lines, preserve_lines=True)
        self.assertEqual(len(result), 3)
        self.assertEqual([x[1] for x in result], [x[1] for x in lines])

    def test_real_project_fixture_keeps_line_coordinates(self):
        lines = json.loads((ROOT / "tests/samples/tasks/map_projects_full.json").read_text())["lines"]
        result = lt.blocks_from_lines(lines, preserve_lines=True)
        original = {tuple(x[1]) for x in lines}
        self.assertTrue(result)
        self.assertTrue(all(box in original for _, box, _ in result))

    def test_long_translation_does_not_move_next_label(self):
        blocks = [("Çok uzun bir açıklama " * 20, (10, 10, 150, 30), "A description", 1),
                  ("Ödüller", (10, 42, 150, 62), "Rewards", 1)]
        items = overlay.layout(blocks, {"width": 300, "height": 200}, measure)
        self.assertEqual(items[1]["y"], 42 - overlay.PAD)
        self.assertLessEqual(items[0]["y"] + items[0]["h"], items[1]["y"])
        self.assertTrue(items[0]["clipped"])

    def test_bottom_label_stays_anchored_instead_of_moving_up(self):
        item = overlay.layout([("Çok uzun metin " * 20, (20, 175, 160, 195), "A label", 1)],
                              {"width": 300, "height": 200}, measure)[0]
        self.assertEqual(item["y"], 171)
        self.assertLessEqual(item["y"] + item["h"], 200)

    def test_long_unbroken_word_is_wrapped_inside_measured_width(self):
        result = overlay.wrap("@THEDIVISIONGAME" * 4, 50, lambda s: len(s) * 8)
        self.assertTrue(all(len(line) * 8 <= 50 for line in result))
        self.assertEqual("".join(result), "@THEDIVISIONGAME" * 4)

    def test_invalid_or_offscreen_boxes_are_ignored(self):
        for box in [(1, 1, float("nan"), 30), (40, 0, 10, 10), (600, 0, 700, 20)]:
            self.assertEqual(overlay.layout([("Çeviri", box, "Text", 1)], {"width": 300, "height": 200}, measure), [])

    def test_large_logo_cannot_merge_with_small_neighboring_menu(self):
        words = [("LOGO", (0, 0, 180, 120), .99), ("Projects", (185, 50, 250, 70), .99)]
        result = ocr_backend.group_lines(words, max_gap=1.6)
        self.assertEqual(len(result), 2)

    def test_real_tk_font_and_canvas_text_stay_inside_masks(self):
        import tkinter as tk
        root = tk.Tk(); root.withdraw()
        try:
            # Canvas backend stays covered as a cross-platform fallback;
            # Windows production uses native opaque boxes to avoid DWM's
            # colour-key transparency artefact.
            renderer = overlay.InPlace(root, {"bg": "#111111", "fg": "white", "accent": "orange"},
                                       on_window=lambda win: win.withdraw(), native_boxes=False)
            blocks = [("Haftalık Proje", (10, 10, 170, 35), "Weekly Project", 1),
                      ("Uzun açıklama metni " * 12, (10, 45, 170, 90), "Description", 2),
                      ("Ödüller", (10, 100, 170, 125), "Rewards", 1)]
            area = {"width": 400, "height": 300, "left": 0, "top": 0}
            items = overlay.layout(blocks, area, renderer.measure_at)
            renderer.show(items, area); root.update_idletasks()
            for identity in renderer.cv.find_all():
                if renderer.cv.type(identity) != "text": continue
                x0, y0, x1, y1 = renderer.cv.bbox(identity)
                self.assertTrue(any(x0 >= it["x"] and y0 >= it["y"] and
                                    x1 <= it["x"] + it["w"] and y1 <= it["y"] + it["h"] for it in items),
                                (x0, y0, x1, y1))
            renderer.hide()
        finally:
            root.destroy()

    def test_native_windows_boxes_contain_canvas_text(self):
        """Regression: native boxes must not be dark panels with clipped Labels."""
        import tkinter as tk
        root = tk.Tk(); root.withdraw()
        try:
            renderer = overlay.InPlace(root, {"bg": "#111111", "fg": "white", "accent": "orange"},
                                       native_boxes=True)
            items = [{"x": 8, "y": 8, "w": 160, "h": 42, "pt": 10,
                      "lines": ["Türkçe test metni"], "kind": "text"}]
            renderer.show(items, {"width": 220, "height": 90, "left": 0, "top": 0})
            root.update_idletasks()
            self.assertEqual(len(renderer._wins), 1)
            canvas = renderer._wins[0].winfo_children()[0]
            self.assertTrue(any(canvas.type(i) == "text" for i in canvas.find_all()))
            renderer.hide()
        finally:
            root.destroy()

    @unittest.skipUnless(os.name == "nt", "Windows composition regression")
    def test_native_click_through_keeps_canvas_glyphs_visible(self):
        """A native overlay must stay readable after becoming click-through.

        WS_EX_LAYERED made Canvas text disappear on affected Windows/DX12
        compositions while the dark rectangle remained.  Inspect real screen
        pixels after applying the same non-layered style as production.
        """
        import tkinter as tk
        from PIL import ImageGrab
        from app import click_through
        root = tk.Tk(); root.withdraw()
        try:
            renderer = overlay.InPlace(
                root, {"bg": "#081a27", "fg": "#effdff", "accent": "#36d9e8", "border": "#25869b"},
                on_window=lambda w: click_through(w, layered=not bool(getattr(w, "_td2_native_box", False))),
                native_boxes=True,
            )
            renderer.show([{"x": 8, "y": 8, "w": 220, "h": 52, "pt": 14,
                            "lines": ["Turkce test 123"], "kind": "text"}],
                          {"width": 260, "height": 90, "left": 60, "top": 60})
            root.update(); time.sleep(.15); root.update()
            win = renderer._wins[0]
            x, y = win.winfo_rootx(), win.winfo_rooty()
            image = ImageGrab.grab(bbox=(x, y, x + win.winfo_width(), y + win.winfo_height()))
            bright = sum(1 for red, green, blue in image.convert("RGB").getdata()
                         if red > 185 and green > 210 and blue > 210)
            self.assertGreater(bright, 40, "click-through sonrası Canvas metni görünmez oldu")
            renderer.hide()
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
