"""Warmup and scanning must not run the shared RapidOCR model concurrently."""
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ocr_backend as ob
from PIL import Image


class SerializationTests(unittest.TestCase):
    def test_warmup_and_scan_share_inference_lock(self):
        entered=threading.Event();release=threading.Event();scan_done=threading.Event()
        active=peak=calls=0;lock=threading.Lock()
        def infer(img):
            nonlocal active,peak,calls
            with lock: active+=1;peak=max(peak,active);calls+=1;first=calls==1
            try:
                if first: entered.set();release.wait(2)
                return SimpleNamespace(txts=None)
            finally:
                with lock:active-=1
        eng=ob.Engine("tesseract");eng.name="rapidocr"
        with patch.object(ob,"_rapid",return_value=infer),patch.object(ob,"_np",lambda img:img):
            eng.warm_up();self.assertTrue(entered.wait(1))
            thread=threading.Thread(target=lambda:(eng._rapid_boxes(Image.new("RGB",(8,8))),scan_done.set()))
            thread.start()
            try:
                self.assertFalse(scan_done.wait(.03))
                self.assertEqual(calls,1)
            finally: release.set();thread.join(2)
            self.assertTrue(scan_done.is_set());self.assertEqual(peak,1);self.assertEqual(calls,2)

    def test_failed_inference_does_not_hold_budget(self):
        eng=ob.Engine("tesseract");eng.name="rapidocr"
        with patch.object(ob,"_rapid",return_value=lambda img:(_ for _ in ()).throw(RuntimeError("bad"))),patch.object(ob,"_np",lambda img:img):
            with self.assertRaises(RuntimeError):eng._rapid_boxes(Image.new("RGB",(8,8)))
        self.assertTrue(ob._rapid_run_lock.acquire(blocking=False));ob._rapid_run_lock.release()


if __name__=="__main__":unittest.main()
