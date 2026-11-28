import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app


class WindowProfileTests(unittest.TestCase):
    def test_ultrawide_work_area_uses_bounded_window(self):
        width, height, factor = app.calculate_window_profile(3440, 1369, dpi_scale=1.14)
        self.assertEqual((width, height), (1540, 960))
        self.assertGreaterEqual(factor, 1.0)
        self.assertLessEqual(factor, 1.35)

    def test_full_hd_work_area_keeps_breathing_margin(self):
        width, height, factor = app.calculate_window_profile(1920, 1040, dpi_scale=1.0)
        self.assertEqual((width, height), (1360, 852))
        self.assertGreater(factor, 1.0)

    def test_small_work_area_never_exceeds_desktop(self):
        width, height, factor = app.calculate_window_profile(1024, 720, dpi_scale=1.25)
        self.assertLessEqual(width, 1000)
        self.assertLessEqual(height, 696)
        self.assertGreaterEqual(factor, 0.78)


if __name__ == "__main__":
    unittest.main()
