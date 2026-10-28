"""Selected card crops avoid locator OCR; invalid input keeps the fallback."""
from copy import deepcopy
from pathlib import Path
import queue
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from performance import TimingStats


CARD = {"name": "Test Gloves", "kind": "gear", "slot": "Gloves", "rarity": ["HIGH-END"],
        "attrs": {"weapon_damage": 15}, "talents": [], "confidence": 1.0,
        "sections": True, "partial": False}


class RegionScanTests(unittest.TestCase):
    def run_scan(self, items, box=None, source="region", width=600, auto=False):
        obj = app.App.__new__(app.App)
        obj.cfg = {"settings": {"scan_source": source, "region": {"width": width, "height": 900},
                                "ocr_passes_auto": False, "ocr_passes": 1}}
        obj.timings = TimingStats()
        obj.results = queue.Queue()
        obj.last_sig, obj.last_time = None, 0
        obj._note_ocr_time = Mock()
        obj.merge_scrolled = lambda *args: args
        obj.scan_area = lambda: {"left": 0, "top": 0}
        responses = [(deepcopy(it), "DISMANTLE", []) for it in items]
        with patch.object(app, "GAME", SimpleNamespace(ok=False)), \
             patch.object(app, "find_card", return_value=box) as locate, \
             patch.object(app, "read_card", return_value=("card text", [])) as read, \
             patch.object(app, "evaluate", side_effect=responses), \
             patch.object(app, "color_hints", side_effect=lambda c, l, i, v: v):
            app.App.scan_image(obj, Image.new("RGB", (width, 900)), auto=auto)
        return locate.call_count, read.call_count, obj

    def test_valid_selected_crop_skips_locator_for_manual_scan(self):
        locate, read, obj = self.run_scan([CARD])
        self.assertEqual((locate, read), (0, 1))
        self.assertIn("ocr_total", obj.timings.snapshot())

    def test_valid_selected_crop_skips_locator_for_automatic_scan(self):
        self.assertEqual(self.run_scan([CARD], auto=True)[0:2], (0, 1))

    def test_invalid_crop_uses_locator_and_reads_recovered_card(self):
        partial = dict(CARD, partial=True)
        locate, read, _ = self.run_scan([partial, CARD], box=(0, 0, 500, 800))
        self.assertEqual((locate, read), (1, 2))

    def test_invalid_crop_without_locator_result_is_not_read_twice(self):
        locate, read, obj = self.run_scan([dict(CARD, partial=True)])
        self.assertEqual((locate, read), (1, 1))
        self.assertEqual(obj.results.get_nowait()[3], "REVIEW")

    def test_full_screen_keeps_locator(self):
        self.assertEqual(self.run_scan([CARD], source="screen")[0:2], (1, 1))

    def test_large_selected_area_keeps_locator(self):
        self.assertEqual(self.run_scan([CARD], width=2000)[0:2], (1, 1))


if __name__ == "__main__":
    unittest.main()
