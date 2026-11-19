"""Position and confidence regressions for OCR fallback used by live overlay."""
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ocr_backend


def main():
    def make_data():
        return {"text": ["Complete", "mission", ""], "conf": ["80", "70", "-1"],
                "left": [20, 60, 0], "top": [4, 4, 0], "width": [40, 30, 0],
                "height": [12, 12, 0]}

    fake = SimpleNamespace(Output=SimpleNamespace(DICT="dict"),
                           image_to_data=Mock(side_effect=lambda *args, **kwargs: make_data()))
    image = Image.new("RGB", (100, 100))
    enlarge = lambda value: value.resize((200, 200))

    with patch.dict(sys.modules, {"pytesseract": fake}):
        engine = ocr_backend.Engine("tesseract", preprocess=enlarge)
        lines = engine.segments(image)
        assert len(lines) == 1, lines
        text, box, confidence = lines[0]
        assert text == "Complete mission", text
        assert box == (10, 2, 45, 8), box
        assert abs(confidence - 0.7) < 1e-6, confidence

        engine.name = "rapidocr"
        with patch.object(engine, "_rapid_boxes", side_effect=RuntimeError("probe failure")) as rapid:
            lines = engine.segments(image)
        assert rapid.call_count == 1, rapid.call_count
        assert engine.name == "tesseract"
        assert len(lines) == 1 and lines[0][1] == (10, 2, 45, 8), lines
        assert abs(lines[0][2] - 0.7) < 1e-6, lines

    print("PASS OCR fallback keeps real boxes and confidence")


if __name__ == "__main__":
    main()
