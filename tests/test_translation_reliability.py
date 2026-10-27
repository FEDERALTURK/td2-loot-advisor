"""Translation integrity, bounded cache and idle model lifecycle; no model/network required."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import livetranslate as lt


class Engine:
    name = "local"
    def __init__(self, reply): self.reply = reply
    def translate(self, texts): return self.reply(texts)


class ReliabilityTests(unittest.TestCase):
    def translator(self, reply):
        return lt.Translator(Engine(reply), lt.Glossary(["Eagle Bearer"]), lt.Cache())

    def test_bad_ai_responses_are_not_treated_as_translation(self):
        for reply in ('Sorry, try again', '[null]', '[3]', '[""]', '["a", "b"]'):
            with self.subTest(reply=reply), self.assertRaises(RuntimeError):
                lt.AIMT(lambda s, u, r=reply: r).translate(["Go there"])

    def test_partial_result_does_not_poison_cache(self):
        for reply in ([], [""], [None], "string", ["Tamam", "extra"]):
            tr = self.translator(lambda texts, value=reply: value)
            with self.subTest(reply=reply), self.assertRaises(RuntimeError): tr.translate(["Go there."])
            self.assertIsNone(tr.cache.get(tr.ck, "Go there."))

    def test_lost_or_changed_numbers_are_rejected(self):
        for reply in ("Bekle.", "20 saniye bekle.", "15 saniye ve 2 dakika bekle."):
            tr = self.translator(lambda texts, r=reply: [r])
            with self.subTest(reply=reply), self.assertRaises(RuntimeError): tr.translate(["Wait 15 seconds."])
            self.assertIsNone(tr.cache.get(tr.ck, "Wait 15 seconds."))

    def test_decimal_format_and_proper_name_are_preserved(self):
        tr = self.translator(lambda texts: ["Z Q0 ile 1,5 saniye bekle."])
        self.assertIn("Eagle Bearer", tr.translate(["Wait 1.5 seconds with Eagle Bearer."])[0])

    def test_lost_or_invented_game_name_is_rejected(self):
        for reply in ("Tüfeği kuşan.", "ZQ1 kuşan.", "ZQ0 ve ZQ0 kuşan."):
            tr = self.translator(lambda texts, r=reply: [r])
            with self.subTest(reply=reply), self.assertRaises(RuntimeError): tr.translate(["Equip Eagle Bearer now."])

    def test_loaded_cache_is_bounded_and_discards_blank_values(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/"cache.json"
            p.write_text(json.dumps({"items": {**{str(i): str(i) for i in range(50)}, "empty": "", "bad": None}}), encoding="utf-8")
            cache = lt.Cache(p, size=5)
            self.assertEqual(len(cache.d), 5)
            self.assertEqual(list(cache.d), [str(i) for i in range(45, 50)])

    def test_idle_unload_never_waits_on_active_translation(self):
        model = lt.LocalMT("unused")
        model.tr = model.sps = model.spt = object()
        model.last_use = time.time() - 600
        model.lock.acquire()
        t0 = time.perf_counter()
        try: self.assertFalse(model.unload_if_idle(60))
        finally: model.lock.release()
        self.assertLess(time.perf_counter() - t0, .1)
        self.assertTrue(model.unload_if_idle(60))
        self.assertIsNone(model.tr)

    def test_recent_model_stays_warm(self):
        model = lt.LocalMT("unused"); model.tr = object(); model.last_use = time.time()
        self.assertFalse(model.unload_if_idle(300))
        self.assertIsNotNone(model.tr)

    def test_frame_cache_is_bounded(self):
        from PIL import Image
        import view3d
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"operator"; p.mkdir()
            for i in range(12):
                Image.new("RGBA", (8,8)).save(p/f"f{i:02d}.webp")
                Image.new("L", (8,8)).save(p/f"m{i:02d}.png")
            view = view3d.SpriteAgentView.__new__(view3d.SpriteAgentView)
            view.base, view.model, view._frames = Path(folder), "operator", {}
            for i in range(12): view._get(i)
            self.assertEqual(len(view._frames), 8)
            self.assertEqual(set(view._frames), set(range(4,12)))


if __name__ == "__main__": unittest.main()
