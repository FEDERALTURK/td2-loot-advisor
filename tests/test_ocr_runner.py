"""Runner behavior when an OCR engine is missing must never look successful."""
import contextlib
import io
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import test_ocr


class OcrRunnerMissingEngineTests(unittest.TestCase):
    def test_no_detected_engines_returns_nonzero_without_loading_samples(self):
        output = io.StringIO()
        with (
            patch.object(test_ocr.ocr_backend, "rapid_available", return_value=False),
            patch.object(test_ocr.ocr_backend, "tesseract_available", return_value=False),
            patch.object(test_ocr.gamedata, "GameData", side_effect=AssertionError("must not run")),
            contextlib.redirect_stdout(output),
        ):
            result = test_ocr.main([str(ROOT / "tests" / "test_ocr.py")])

        self.assertEqual(result, 2)
        self.assertIn("no OCR engine is available", output.getvalue())

    def test_explicit_unavailable_engine_returns_nonzero(self):
        output = io.StringIO()
        with (
            patch.object(test_ocr.ocr_backend, "Engine") as engine_factory,
            contextlib.redirect_stdout(output),
        ):
            engine_factory.return_value.name = "tesseract"
            result = test_ocr.main([str(ROOT / "tests" / "test_ocr.py"), "rapidocr"])

        self.assertEqual(result, 2)
        self.assertIn("requested OCR engine is not available", output.getvalue())


if __name__ == "__main__":
    unittest.main()
