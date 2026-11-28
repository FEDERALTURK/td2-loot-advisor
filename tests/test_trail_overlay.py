"""Fare izi katmanı: saydam tıklama-geçirgen overlay varsayılan olmalı.

Eski `SafeTrail`, opak sayfa gövdelerinin arkasında kaldığı için panelde
görünmüyordu. `apply_fx` artık önce `TrailFX` overlay'ini dener; overlay
başlatılamazsa güvenli yedeğe döner.
"""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app


class TrailOverlayTests(unittest.TestCase):
    def _instance(self, **settings):
        base = {"fx_trail": True, "fx_trail_color": "#ff6d10", "fx_trail_len": 18}
        base.update(settings)
        return SimpleNamespace(root=Mock(), cfg={"settings": base}, _closing=False, trail_fx=None)

    def _call(self, instance, overlay_start):
        with patch.object(app.fx, "CursorFX") as cursor, \
             patch.object(app.fx, "TrailFX") as trail, \
             patch.object(app.fx, "SafeTrail") as safe:
            cursor.return_value.apply.return_value = True
            trail.return_value.start.return_value = overlay_start
            app.App.apply_fx(instance)
        return trail, safe

    def test_overlay_is_default_trail(self):
        instance = self._instance()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TD2_TRAIL_OVERLAY", None)
            trail, safe = self._call(instance, True)
        trail.assert_called_once()
        safe.assert_not_called()
        self.assertIs(instance.trail_fx, trail.return_value)
        # Overlay tıklama-geçirgen bir pencere kancası almalı.
        self.assertIsNotNone(trail.call_args.kwargs.get("click_through"))

    def test_overlay_failure_falls_back_to_safe_trail(self):
        instance = self._instance()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TD2_TRAIL_OVERLAY", None)
            trail, safe = self._call(instance, False)
        safe.assert_called_once()
        self.assertIs(instance.trail_fx, safe.return_value)

    def test_env_switch_disables_overlay(self):
        instance = self._instance()
        with patch.dict(os.environ, {"TD2_TRAIL_OVERLAY": "0"}, clear=False):
            trail, safe = self._call(instance, True)
        trail.assert_not_called()
        safe.assert_called_once()

    def test_disabled_setting_creates_no_trail(self):
        instance = self._instance(fx_trail=False)
        trail, safe = self._call(instance, True)
        trail.assert_not_called()
        safe.assert_not_called()
        self.assertIsNone(instance.trail_fx)


if __name__ == "__main__":
    unittest.main()
