"""Regression checks for the Worker administration dashboard summary."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import td2_panel


def test_overview_metric_values():
    assert td2_panel.overview_metric_values({
        "accounts": {"total": 12, "active_licenses": 3},
        "usage": {"starts_today": 8},
        "suggestions_pending": 2,
        "tasks": {"public": 15},
        "reports_queued": 1,
    }) == {
        "accounts": "12",
        "licenses": "3",
        "starts": "8",
        "suggestions": "2",
        "tasks": "15",
        "queued": "1",
    }


def test_missing_or_malformed_metrics_are_not_reported_as_zero():
    assert td2_panel.overview_metric_values({"accounts": "bad", "usage": None, "tasks": []}) == {
        "accounts": "—",
        "licenses": "—",
        "starts": "—",
        "suggestions": "—",
        "tasks": "—",
        "queued": "—",
    }


def test_empty_healthy_report_queue_has_an_explanation():
    assert td2_panel.report_load_status({"ok": True, "panel_mirror": "enabled"}, []) == (
        "Worker ve Supabase yanıt verdi; henüz hata raporu yok"
    )
    assert td2_panel.report_load_status({"ok": False}, [{"id": "1"}]) == "1 kayıt yüklendi"


if __name__ == "__main__":
    test_overview_metric_values()
    test_missing_or_malformed_metrics_are_not_reported_as_zero()
    test_empty_healthy_report_queue_has_an_explanation()
    print("RESULT: PASS")
