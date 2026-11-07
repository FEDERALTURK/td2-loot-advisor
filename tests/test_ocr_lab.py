import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ocr_lab
import review_queue


class OcrLabTests(unittest.TestCase):
    def test_compares_engines_and_marks_low_confidence_for_review(self):
        image = object()
        report = ocr_lab.benchmark(image, {
            "rapidocr": lambda _: [("Rewards", (0, 0, 1, 1), .93)],
            "windows": lambda _: [("Rew ards", (0, 0, 1, 1), .42)],
            "tesseract": lambda _: (_ for _ in ()).throw(RuntimeError("not installed")),
        })
        self.assertEqual(report["winner"], "rapidocr")
        self.assertFalse(report["engines"]["rapidocr"]["review"])
        self.assertTrue(report["engines"]["windows"]["review"])
        self.assertFalse(report["engines"]["tesseract"]["available"])

    def test_review_queue_is_append_only_and_forces_review(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.jsonl"
            ident = review_queue.add(path, "blurred card", {"name": "?", "_text": "secret"}, "DISMANTLE")
            rows = review_queue.load(path)
            self.assertEqual(rows[0]["id"], ident)
            self.assertEqual(rows[0]["verdict"], "REVIEW")
            self.assertNotIn("_text", rows[0]["item"])


if __name__ == "__main__":
    unittest.main()
