"""Offline OCR -> local model -> Tk overlay probe using a generated English card.

No game, microphone, personal settings, network or automatic model download.
The caller supplies an already installed model directory.
"""
import json
import queue
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def run(app, model_dir, output):
    root = None
    result = {"ok": False, "steps": []}
    try:
        app.i18n.init(app.BUNDLE)
        app.i18n.set_language("tr")
        root = app.tk.Tk()
        root.withdraw()
        obj = app.App.__new__(app.App)
        obj.root = root
        obj.cfg = {"settings": {"tr_engine": "local", "tr_ocr": "rapid", "tr_mode": "screen",
                                "tr_hide": 30, "tr_speak": "off", "task_live": False}}
        obj.lt_model_dir = lambda: Path(model_dir)
        obj.lt_cache = app.livetranslate.Cache()
        obj.timings = app.performance.TimingStats()
        obj.results = queue.Queue()
        obj._translation_jobs = app.workqueue.LatestWorker("translation-probe")
        obj._lt_status = lambda text, kind="muted": result.update(status=text)
        obj._lt_hist_fill = lambda: None
        obj._task_seen = lambda *args: None
        obj._microphone_busy = lambda: False
        obj.tabs = {"stats": app.ttk.Frame(root)}
        obj._build_community = lambda f: None
        obj.refresh_stats_tab = lambda: None
        obj.build_stats()
        assert getattr(obj, "sp", None) is None, "Statistics overwrote speech session"
        result["steps"].append("statistics preserves translation state")
        # Exercise the actual button/shortcut command after the stats page exists.
        started = []
        obj.lt_start = lambda quiet=False: started.append(True) or True
        obj.toast = lambda *args: None
        obj.lt_toggle()
        assert started, "Start control did not start screen translation"
        result["steps"].append("start command after statistics")
        app.OCR = app.ocr_backend.Engine("rapidocr")
        card = Image.new("RGB", (900, 180), "#172028")
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
        ImageDraw.Draw(card).text((25, 50), "Agent, move to the safe house.", fill="white", font=font)
        area = {"left": 40, "top": 40, "width": 900, "height": 180}
        t0 = time.monotonic()
        obj._lt_run(card, area, force=True)
        assert obj._translation_jobs.wait_idle(120), "Translation timed out"
        while not obj.results.empty():
            _, token, callback = obj.results.get_nowait()
            if obj._translation_jobs.is_current(token): callback()
        root.update_idletasks()
        assert getattr(obj, "lt_hist", None), result.get("status", "No translation")
        assert obj._lt_win and obj._lt_win.winfo_exists(), "Overlay missing"
        en, tr = obj.lt_hist[-1]
        assert "agent" in en.lower() and tr != en and "ajan" in tr.lower(), (en, tr)
        result.update(english=en, turkish=tr, elapsed_ms=round((time.monotonic()-t0)*1000))
        result["steps"].append("real RapidOCR + installed OPUS-MT + visible overlay")
        obj._lt_hide()
        obj._lt_show([(en, tr, (25, 50, 650, 90))], area, 0, force_mode="inplace")
        root.update_idletasks()
        assert obj._lt_win and obj._lt_win.winfo_exists(), "In-place overlay missing"
        result["steps"].append("in-place overlay")
        result["ok"] = True
    except Exception as exc:
        import traceback
        result["error"] = traceback.format_exc()
    finally:
        if 'obj' in locals():
            if hasattr(obj, '_translation_jobs'): obj._translation_jobs.close(wait=True, timeout=5)
            if root: obj._lt_hide()
        if root: root.destroy()
        Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result["ok"]
