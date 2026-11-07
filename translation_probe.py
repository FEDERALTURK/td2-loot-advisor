"""Offline OCR -> local model -> Tk overlay probe using a generated English card.

No game, microphone, personal settings, network or automatic model download.
The caller supplies an already installed model directory.
"""
import json
import queue
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageGrab, ImageChops, ImageStat


def inspect_render(root, renderer):
    """Measure actual glyph pixels as well as Tk items; capture exclusion must be off."""
    root.update()
    time.sleep(.15)
    root.update()
    windows = renderer._wins or ([renderer.win] if renderer.win else [])
    reports = []
    for win in windows:
        canvases = [w for w in win.winfo_children() if w.winfo_class() == "Canvas"]
        count = bright = 0
        for canvas in canvases:
            for item in canvas.find_all():
                if canvas.type(item) != "text" or not canvas.itemcget(item, "text").strip():
                    continue
                count += 1
                x0, y0, x1, y1 = canvas.bbox(item)
                x0, y0 = max(0, x0), max(0, y0)
                x1, y1 = min(canvas.winfo_width(), x1), min(canvas.winfo_height(), y1)
                if x1 <= x0 or y1 <= y0:
                    continue
                x, y = canvas.winfo_rootx(), canvas.winfo_rooty()
                shot = ImageGrab.grab(bbox=(x+x0, y+y0, x+x1, y+y1)).convert("RGB")
                bright += sum(r > 185 and g > 185 and b > 185 for r, g, b in shot.getdata())
        reports.append({"text_items": count, "bright_glyph_pixels": bright,
                        "visible": bool(count and bright > 40)})
    return {"ok": bool(reports) and all(r["visible"] for r in reports), "windows": reports}


def run(app, model_dir, output):
    root = None
    result = {"ok": False, "steps": [], "checks": {},
              "limits": ["Synthetic desktop only; no game/DX12 verification",
                         "Physical mouse pass-through and monitor DPI change require interactive validation"]}
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
        source = app.tk.Toplevel(root)
        source.geometry("900x180+40+40")
        source.overrideredirect(True)
        source.attributes("-topmost", True)
        photo = ImageTk.PhotoImage(card, master=root)
        app.tk.Label(source, image=photo, bd=0).pack()
        root.update(); time.sleep(.15); root.update()
        area = {"left": source.winfo_rootx(), "top": source.winfo_rooty(), "width": 900, "height": 180}
        card = app.capture.Grabber().grab(area)
        result["checks"]["capture"] = {"ok": card.size == (900, 180)}
        lines = app.OCR.lines(card)
        result["checks"]["ocr"] = {"ok": any("agent" in line[0].lower() for line in lines),
                                     "line_count": len(lines)}
        assert result["checks"]["ocr"]["ok"], "Synthetic window OCR failed"
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
        result["checks"]["translation"] = {"ok": True}
        result["steps"].append("captured synthetic window + RapidOCR + installed OPUS-MT")
        obj._lt_hide()
        # Inspect pixels before capture exclusion; otherwise a working excluded
        # overlay would correctly be absent from the screenshot.
        obj._lt_overlay_window = app.click_through
        foreground = app.ctypes.windll.user32.GetForegroundWindow() if app.os.name == "nt" else None
        obj._lt_show([(en, tr, (25, 50, 650, 90))], area, 0, force_mode="inplace")
        root.update_idletasks()
        assert obj._lt_win and obj._lt_win.winfo_exists(), "In-place overlay missing"
        result["checks"]["render"] = inspect_render(root, obj._lt_inplace)
        assert result["checks"]["render"]["ok"], "Overlay exists but glyph pixels are missing"
        windows = obj._lt_inplace._wins or [obj._lt_win]
        result["checks"]["coordinates"] = {"ok": all(
            area["left"] <= w.winfo_rootx() < area["left"] + area["width"] and
            area["top"] <= w.winfo_rooty() < area["top"] + area["height"] for w in windows)}
        assert result["checks"]["coordinates"]["ok"], "Overlay outside synthetic source"
        if foreground is not None:
            result["checks"]["focus"] = {"ok": foreground == app.ctypes.windll.user32.GetForegroundWindow()}
            flags = []
            for win in windows:
                hwnd = app.ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
                flags.append(app.ctypes.windll.user32.GetWindowLongW(hwnd, -20))
            result["checks"]["click_through_flags"] = {"ok": all(f & 0x08000020 == 0x08000020 for f in flags)}
            excluded = all(app.exclude_from_capture(win, "probe") for win in windows)
            root.update(); time.sleep(.15)
            recaptured = app.capture.Grabber().grab(area)
            difference = max(ImageStat.Stat(ImageChops.difference(card, recaptured)).mean)
            result["checks"]["capture_exclusion"] = {"ok": excluded and difference < 2,
                                                       "mean_difference": round(difference, 3)}
            app.CAPTURE_MASK.pop("probe", None)
        obj._lt_hide()
        scaling = root.tk.call("tk", "scaling")
        scaling_checks = []
        try:
            for value in (1.0, 1.5, 2.0):
                root.tk.call("tk", "scaling", value)
                obj._lt_show([(en, tr, (25, 50, 650, 110))], area, 0, force_mode="inplace")
                scaling_checks.append({"tk_scaling": value, **inspect_render(root, obj._lt_inplace)})
                obj._lt_hide()
        finally:
            root.tk.call("tk", "scaling", scaling)
        result["checks"]["font_scaling"] = {"ok": all(c["ok"] for c in scaling_checks), "samples": scaling_checks}
        result["steps"].append("in-place overlay")
        result["ok"] = all(check["ok"] for check in result["checks"].values())
    except Exception:
        import traceback
        result["error"] = traceback.format_exc()
    finally:
        if 'obj' in locals():
            if hasattr(obj, '_translation_jobs'): obj._translation_jobs.close(wait=True, timeout=5)
            if root: obj._lt_hide()
        if root: root.destroy()
        Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result["ok"]
