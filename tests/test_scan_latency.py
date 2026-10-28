"""Deterministic autoscan latency and workload checks; no game or capture."""
from pathlib import Path
import queue
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from performance import get_policy


class Clock:
    def __init__(self, duration):
        self.now = 100.0
        self.end = self.now + duration

    def is_set(self):
        return self.now >= self.end

    def wait(self, seconds):
        self.now += seconds


class Lock:
    def __init__(self, clock, busy_until=0):
        self.clock, self.busy_until = clock, busy_until
        self.held = False

    def acquire(self, blocking=True):
        if blocking:
            raise AssertionError("autoscan must not wait on stale images")
        if self.clock.now < self.busy_until:
            return False
        self.held = True
        return True

    def release(self):
        assert self.held
        self.held = False


def simulate(mode="balanced", duration=3, state="menu", change_at=None, busy=0):
    clock = Clock(duration)
    scans, captures = [], []
    policy = get_policy({"perf_mode": mode})
    obj = SimpleNamespace(cfg={"settings": {"only_game_active": False}},
                          _policy=lambda: policy, scan_area=lambda: {"width": 100},
                          _screen_observe=lambda small: state,
                          lock=Lock(clock, 100 + busy), results=queue.Queue(), last_err=None)

    def sample(*args):
        value = 100 if change_at is not None and clock.now >= 100 + change_at else 0
        return [value] * 576, object()

    def scan(img, auto):
        scans.append(round(clock.now - 100, 3))
        return state != "world"

    def grab(region):
        captures.append(round(clock.now - 100, 3))
        return object()

    obj.scan_image = scan
    with patch.object(app.time, "time", side_effect=lambda: clock.now), \
         patch.object(app.capture, "default", return_value=SimpleNamespace(sample=sample)), \
         patch.object(app, "grab", side_effect=grab):
        app.App._auto_loop(obj, clock)
    assert obj.results.empty(), list(obj.results.queue)
    return scans, captures, policy


class ScanLatencyTests(unittest.TestCase):
    def test_initial_card_is_detected_without_waiting_for_full_ocr_interval(self):
        for mode, expected in (("balanced", .4), ("game", .6)):
            scans, _, policy = simulate(mode)
            self.assertEqual(scans, [expected])
            self.assertLess(scans[0], policy.auto_interval_s)

    def test_unchanged_card_does_not_repeat_ocr(self):
        self.assertEqual(simulate(duration=10)[0], [.4])

    def test_changed_card_waits_for_budget_then_is_not_lost(self):
        for mode in ("balanced", "game"):
            scans, _, policy = simulate(mode, duration=4, change_at=.8)
            self.assertEqual(len(scans), 2)
            self.assertGreaterEqual(scans[1] - scans[0] + 1e-6, policy.auto_interval_s)
            self.assertLessEqual(scans[1] - scans[0], policy.auto_interval_s + policy.scan_poll_s + 1e-6)

    def test_busy_ocr_retries_fresh_capture_without_blocking(self):
        scans, captures, _ = simulate(busy=1)
        self.assertEqual(len(scans), 1)
        self.assertGreaterEqual(scans[0], 1)
        self.assertEqual(captures, scans)

    def test_loading_screen_does_not_run_ocr(self):
        self.assertEqual(simulate(state="loading")[0], [])

    def test_world_backoff_and_change_requirement_are_preserved(self):
        self.assertEqual(simulate(state="world", duration=10)[0], [.6])


if __name__ == "__main__":
    unittest.main()
