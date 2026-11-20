"""Pinned community-data revision metadata checks."""
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.sync_div2hub_data import source_metadata


def test_source_metadata_accepts_full_revision_and_iso_date():
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory)
        (source / "SOURCE_VERSION.json").write_text(json.dumps({
            "commit": "a" * 40, "commit_date": "2026-11-14",
        }), encoding="utf-8")
        assert source_metadata(source) == {
            "commit": "a" * 40, "commit_date": "2026-11-14",
        }


def test_source_metadata_rejects_short_or_invalid_revision():
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory)
        (source / "SOURCE_VERSION.json").write_text(json.dumps({
            "commit": "abc", "commit_date": "not-a-date",
        }), encoding="utf-8")
        try:
            source_metadata(source)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid Div2Hub revision metadata was accepted")


if __name__ == "__main__":
    test_source_metadata_accepts_full_revision_and_iso_date()
    test_source_metadata_rejects_short_or_invalid_revision()
    print("RESULT: PASS")
