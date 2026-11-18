"""Regression checks for UTF-8 UI labels and icon text."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    ROOT / "app.py",
    ROOT / "td2app" / "ui" / "ui_theme.py",
    ROOT / "td2app" / "ui" / "ui_hud.py",
    ROOT / "lang" / "tr.json",
)
# Do not flag Turkish circumflex letters such as ``zekâ``/``ZEKÂ``.
MOJIBAKE_MARKERS = ("Ã", "Ä", "Å", "ğŸ", "ðŸ", "�")


def test_ui_sources_have_no_common_mojibake_markers():
    findings = []
    for path in SOURCE_FILES:
        text = path.read_text(encoding="utf-8")
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                findings.append(f"{path.relative_to(ROOT)}: {marker}")
    assert not findings, "UTF-8 UI text was decoded with the wrong code page: " + ", ".join(findings)


if __name__ == "__main__":
    test_ui_sources_have_no_common_mojibake_markers()
    print("RESULT: PASS")
