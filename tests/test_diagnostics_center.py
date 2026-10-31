#!/usr/bin/env python3
"""Tanılama merkezi: güvenli görünüm, olay tamponu ve rapor maskeleme."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import diagnostics_center as diag


def test_safe_view():
    settings = {"fx_trail": True, "fx_video": True, "ui_theme": "isac"}
    changed = diag.apply_safe_view(settings)
    assert changed
    assert diag.safe_view_active(settings)
    assert settings["fx_trail"] is False
    print("OK safe view")


def test_events():
    buf = diag.EventBuffer(3)
    logger = logging.getLogger("diagnostics-center-test")
    logger.handlers[:] = [buf]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.warning("Translation overlay waiting")
    event = buf.snapshot()[0]
    assert event.category == "Çeviri"
    assert event.level == "WARNING"
    print("OK events")


def test_markdown_scrub():
    report = diag.markdown_report("9.1.5.18", {"settings": {}, "system": {"path": r"C:\\Users\\Secret\\x", "mail": "a@b.com"}}, [])
    assert "Secret" not in report and "a@b.com" not in report
    assert "GitHub'a otomatik gönderilmez" in report
    print("OK markdown")


def test_real_check_engine_and_safe_repairs():
    """Motor bir komutu gerçekten denetler, yalnız güvenli ayarları düzeltir."""
    class Completed:
        returncode, stdout, stderr = 0, "tesseract 5.0", ""
    def fake_command(*_args, **_kwargs): return Completed()
    settings = {"fx_trail": True, "fx_video": True, "fx_bgwatch": False, "tesseract_cmd": sys.executable}
    context = {"settings": settings, "config_path": __file__, "log_dir": Path(__file__).parent,
               "translation_ready": False, "overlay_present": True, "last_error": "overlay error", "game_window": None}
    checks = diag.run_checks(context, command_runner=fake_command)
    assert next(x for x in checks if x.key == "tesseract").status == "ok"
    assert next(x for x in checks if x.key == "visual_stack").repair == "safe_view"
    changed, actions = diag.apply_repairs(settings, checks)
    assert "fx_trail" in changed and settings["fx_trail"] is False
    assert actions["reset_overlay"] is True
    print("OK real check engine")


if __name__ == "__main__":
    test_safe_view(); test_events(); test_markdown_scrub(); test_real_check_engine_and_safe_repairs()
    print("RESULT: PASS")
