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


def test_build_tool_health_checks_are_read_only_and_reportable():
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "build_tool.json"
        catalog = {"version": "fixture", "source": "fixture",
                   "community_data_source": {"commit": "a" * 40, "commit_date": "2026-11-14"},
                   "items": {"Fixture Item": {}}, "weapon_index": {}, "attributes": {},
                   "brands": [], "gear_sets": []}
        context = {"settings": {}, "catalog": catalog, "log_dir": Path(directory),
                   "config_path": Path(directory) / "missing-config.json",
                   "build_tool_path": path, "game_window": None}
        checks = diag.run_checks(context)
        by_key = {check.key: check for check in checks}
        assert by_key["game_catalog"].status == "warning"
        assert "Per-item source URL" in by_key["game_catalog"].detail
        assert by_key["build_tool_store"].status == "info"

        original = b'{"builds": false}'
        path.write_bytes(original)
        checks = diag.run_checks(context)
        assert next(check for check in checks if check.key == "build_tool_store").status == "error"
        assert path.read_bytes() == original
        report = diag.markdown_report("test", {"settings": {}, "system": {},
                                     "check_results": checks}, [])
        assert "Gerçek Yerel Kontroller" in report
        print("OK Build Tool diagnostics are read-only")


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


def test_source_scan_reports_syntax_location_without_writing_files():
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "good.py").write_text("def ok():\n    return 'ç'\n", encoding="utf-8")
        (root / "broken.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
        checks = diag.scan_source_tree(root)
        result = next(item for item in checks if item.key == "source_syntax" and "broken.py" in item.evidence)
        assert result.status == "error"
        assert result.source == "broken.py"
        assert result.line == 1
        assert result.category == "Kod / Derleme"
        assert not list(root.glob("*.tmp"))
    print("OK source scan")


def test_log_scan_resolves_runtime_traceback_to_source_line():
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "app.py"
        source.write_text("def broken():\n    return missing\n", encoding="utf-8")
        log = root / "app.log"
        log.write_text(
            f'Traceback (most recent call last):\n  File "{source}", line 2, in broken\n'
            "    return missing\nNameError: name 'missing' is not defined\n",
            encoding="utf-8",
        )
        checks = diag.scan_runtime_log(log, root)
        result = checks[0]
        assert result.status == "error"
        assert result.source == "app.py"
        assert result.line == 2
        assert result.symbol == "broken"
        assert "NameError" in result.detail
    print("OK runtime traceback scan")


def test_run_checks_includes_source_and_runtime_layers():
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "broken.py"
        source.write_text("def broken(:\n    pass\n", encoding="utf-8")
        log = root / "app.log"
        log.write_text(f'Traceback (most recent call last):\n  File "{source}", line 1, in broken\nSyntaxError: bad\n', encoding="utf-8")
        checks = diag.run_checks({"settings": {}, "project_root": root, "log_path": log,
                                  "config_path": root / "missing.json", "log_dir": root})
        assert any(item.key == "source_syntax" and item.status == "error" for item in checks)
        assert any(item.key == "runtime_traceback" and item.source == "broken.py" for item in checks)
    print("OK integrated diagnostic layers")


def test_runtime_log_scan_ignores_tracebacks_before_current_session():
    import tempfile
    import time
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        log = root / "app.log"
        log.write_text(
            "2020-01-01 00:00:01 | ERROR | td2 | old\n"
            "Traceback (most recent call last):\n"
            '  File "C:\\old.py", line 4, in old\n'
            "NameError: old\n"
            "2020-01-01 00:00:02 | INFO | td2 | current\n"
            "Traceback (most recent call last):\n"
            f'  File "{root / "app.py"}", line 8, in current\n'
            "NameError: current\n",
            encoding="utf-8",
        )
        checks = diag.scan_runtime_log(log, root, since=time.mktime((2020, 1, 1, 0, 0, 1, 0, 0, 0)) + 0.5)
        assert len(checks) == 1
        assert checks[0].line == 8
    print("OK runtime session boundary")


if __name__ == "__main__":
    test_safe_view(); test_events(); test_markdown_scrub(); test_build_tool_health_checks_are_read_only_and_reportable(); test_real_check_engine_and_safe_repairs()
    print("RESULT: PASS")
