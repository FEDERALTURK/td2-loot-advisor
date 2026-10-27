"""Pure runtime-budget and bounded timing checks. python tests/test_performance.py"""
import math
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from performance import TimingStats, get_policy


class PolicyTests(unittest.TestCase):
    def test_default_preserves_ocr_quality(self):
        p = get_policy({})
        self.assertEqual(p.mode, "balanced")
        self.assertEqual(p.ocr_passes, 3)
        self.assertEqual(p.auto_interval_ms, 900)
        self.assertEqual(p.translation_poll_s, 0.5)

    def test_game_budget_is_moderate_and_does_not_mutate_config(self):
        st = {"perf_mode": "game", "ocr_passes": 3, "auto_interval_ms": 700,
              "ocr_gpu": "off", "tr_engine": "ai", "fx_video": True}
        original = dict(st)
        p = get_policy(st)
        self.assertEqual(p.ocr_passes, 2)
        self.assertEqual(p.auto_interval_ms, 1400)
        self.assertEqual(p.translation_poll_s, 0.75)
        self.assertEqual(st, original)
        self.assertFalse(p.suspend_animations)

    def test_respects_existing_slower_intervals_and_lower_passes(self):
        for mode in ("balanced", "game"):
            p = get_policy({"perf_mode": mode, "ocr_passes": 1,
                            "auto_interval_ms": 5000, "tr_poll_ms": 2000})
            self.assertEqual((p.ocr_passes, p.auto_interval_ms, p.translation_poll_s), (1, 5000, 2))
            self.assertEqual(p.auto_interval_s, 5)

    def test_visuals_resume_when_window_is_visible_again(self):
        for mode in ("balanced", "game"):
            for foreground, minimized in ((True, False), (False, True), (True, True)):
                self.assertTrue(get_policy({"perf_mode": mode}, foreground, minimized).suspend_animations)
            visible = get_policy({"perf_mode": mode}, False, False)
            self.assertFalse(visible.suspend_animations)
            self.assertEqual(visible.ui_animation_multiplier, 1)

    def test_bad_saved_values_cannot_create_nonfinite_or_busy_poll(self):
        for bad in (None, "bad", float("nan"), float("inf"), float("-inf"), True, [], {}):
            p = get_policy({"perf_mode": bad, "ocr_passes": bad,
                            "auto_interval_ms": bad, "tr_poll_ms": bad})
            self.assertEqual(p.mode, "balanced")
            self.assertTrue(1 <= p.ocr_passes <= 3)
            self.assertTrue(900 <= p.auto_interval_ms <= 60000)
            self.assertTrue(math.isfinite(p.translation_poll_s) and p.translation_poll_s >= 0.5)
        self.assertEqual(get_policy(None), get_policy({}))

    def test_finite_extremes_are_bounded(self):
        p = get_policy({"ocr_passes": 999, "auto_interval_ms": 1e100, "tr_poll_ms": 1e100})
        self.assertEqual((p.ocr_passes, p.auto_interval_ms, p.translation_poll_s), (3, 60000, 5))
        p = get_policy({"ocr_passes": -99, "auto_interval_ms": -1, "tr_poll_ms": -1})
        self.assertEqual((p.ocr_passes, p.auto_interval_ms, p.translation_poll_s), (1, 900, 0.5))


class TimingTests(unittest.TestCase):
    def test_median_and_p95_are_phase_specific(self):
        stats = TimingStats()
        for value in range(1, 21):
            stats.record("ocr", value)
        stats.record("capture", 2.5)
        self.assertEqual(stats.snapshot()["ocr"], {"count": 20, "median_ms": 10.5, "p95_ms": 19, "last_ms": 20})
        self.assertEqual(stats.snapshot()["capture"]["p95_ms"], 2.5)

    def test_entire_ring_is_bounded_across_phases(self):
        stats = TimingStats(3)
        for phase in ("capture", "ocr", "translate", "scan"):
            stats.record(phase, 1)
        self.assertEqual(len(stats), 3)
        self.assertNotIn("capture", stats.snapshot())
        stats.clear()
        self.assertEqual(stats.snapshot(), {})

    def test_rejects_invalid_durations_and_text_labels(self):
        stats = TimingStats()
        for bad in (float("nan"), float("inf"), -1, True, None, "error"):
            self.assertFalse(stats.record("ocr", bad))
        for phase in ("card text with spaces", "C:/Users/Someone", "x" * 33, "", None):
            self.assertFalse(stats.record(phase, 1))
        self.assertEqual(len(stats), 0)

    def test_measure_records_on_success_and_failure(self):
        stats = TimingStats()
        with patch("performance.time.perf_counter", side_effect=[1, 1.025, 2, 2.05]):
            with stats.measure("capture"):
                pass
            with self.assertRaises(ValueError):
                with stats.measure("ocr"):
                    raise ValueError("test")
        self.assertAlmostEqual(stats.snapshot()["capture"]["last_ms"], 25)
        self.assertAlmostEqual(stats.snapshot()["ocr"]["last_ms"], 50)

    def test_concurrent_writers_keep_bound(self):
        stats = TimingStats(128)
        threads = [threading.Thread(target=lambda: [stats.record("ocr", n) for n in range(200)]) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(stats), 128)
        self.assertEqual(stats.snapshot()["ocr"]["count"], 128)

    def test_capacity_is_bounded_for_malformed_configuration(self):
        self.assertEqual(TimingStats(float("inf")).max_records, 128)
        self.assertEqual(TimingStats(-2).max_records, 1)
        self.assertEqual(TimingStats(100000).max_records, 1024)


if __name__ == "__main__":
    unittest.main()
