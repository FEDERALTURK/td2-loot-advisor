"""Small runtime budgets for the desktop helper, independent of screen detection.

The caller supplies its existing game-focus/minimized state. Policies never change
settings, select a GPU, or select a translation provider. ``ocr_passes`` is an
automatic-scan budget; an explicit manual scan can keep its configured passes.
TimingStats keeps only numeric timings and short phase names in memory.
"""
from collections import deque
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
import math
import re
from statistics import median
import threading
import time


MODES = ("balanced", "game")
_PHASE = re.compile(r"[a-z][a-z0-9_.-]{0,31}\Z")


def _number(value, default, low, high):
    """Return a finite bounded number, including for malformed saved settings."""
    try:
        if isinstance(value, bool):
            raise ValueError("boolean")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("non-finite")
    except (TypeError, ValueError, OverflowError):
        value = default
    return max(low, min(high, value))


@dataclass(frozen=True)
class PerformancePolicy:
    mode: str
    ocr_passes: int
    auto_interval_ms: int
    translation_poll_s: float
    ui_animation_multiplier: float
    suspend_animations: bool

    @property
    def auto_interval_s(self):
        return self.auto_interval_ms / 1000.0


def get_policy(settings, game_active=False, minimized=False):
    """Compute a budget without modifying the user's settings.

    ``settings`` is the application's settings mapping (not the outer config).
    Optional ``tr_poll_ms`` can request a slower translation polling interval.
    Existing autoscan backoff still applies on top of ``auto_interval_ms``.
    Visible UI animation runs at its normal speed in both presets. Decorative
    animation is suspended while the game is foreground or the app is minimized.
    """
    st = settings if isinstance(settings, Mapping) else {}
    mode = st.get("perf_mode", "balanced")
    if mode not in MODES:
        mode = "balanced"
    cap, scan_min, poll_min = (3, 900, 0.50) if mode == "balanced" else (2, 1400, 0.75)
    passes = int(_number(st.get("ocr_passes", 3), 3, 1, 5))
    scan_ms = int(_number(st.get("auto_interval_ms", 700), 700, 200, 60000))
    poll_s = _number(st.get("tr_poll_ms", 350), 350, 100, 5000) / 1000.0
    return PerformancePolicy(
        mode=mode,
        ocr_passes=min(passes, cap),
        auto_interval_ms=max(scan_ms, scan_min),
        translation_poll_s=max(poll_s, poll_min),
        ui_animation_multiplier=1.0,
        suspend_animations=bool(game_active or minimized),
    )


class TimingStats:
    """Bounded, thread-safe phase timings in milliseconds; no disk or text data.

    Use fixed phase names such as ``capture``, ``ocr``, ``translate`` and ``scan``.
    The bound applies to the entire ring, so adding phases cannot grow memory.
    Snapshot counts describe samples still in the ring, not lifetime totals.
    """

    def __init__(self, max_records=128):
        self.max_records = int(_number(max_records, 128, 1, 1024))
        self._records = deque(maxlen=self.max_records)
        self._lock = threading.Lock()

    def __len__(self):
        with self._lock:
            return len(self._records)

    def record(self, phase, elapsed_ms):
        """Add one finite nonnegative timing; reject malformed input quietly."""
        if not isinstance(phase, str) or not _PHASE.fullmatch(phase):
            return False
        try:
            if isinstance(elapsed_ms, bool):
                return False
            elapsed_ms = float(elapsed_ms)
            if not math.isfinite(elapsed_ms) or elapsed_ms < 0:
                return False
        except (TypeError, ValueError, OverflowError):
            return False
        with self._lock:
            self._records.append((phase, elapsed_ms))
        return True

    @contextmanager
    def measure(self, phase):
        """Measure a phase, also recording elapsed time if the operation raises."""
        start = time.perf_counter()
        try:
            yield
        finally:
            self.record(phase, (time.perf_counter() - start) * 1000.0)

    def snapshot(self):
        """Return count, median, nearest-rank p95 and last timing per phase."""
        with self._lock:
            records = tuple(self._records)
        phases = {}
        for phase, elapsed_ms in records:
            phases.setdefault(phase, []).append(elapsed_ms)
        out = {}
        for phase, values in phases.items():
            ordered = sorted(values)
            out[phase] = {"count": len(values), "median_ms": median(values),
                          "p95_ms": ordered[math.ceil(len(values) * 0.95) - 1],
                          "last_ms": values[-1]}
        return out

    def clear(self):
        with self._lock:
            self._records.clear()
