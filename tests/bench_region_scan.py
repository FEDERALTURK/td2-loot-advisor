"""Compare the published scan path and local region path on one real card.

No game, capture, network, personal settings or GUI. Baseline is the reviewed
release checkout under project_review/github/td2-loot-advisor.
"""
import ast
import json
from pathlib import Path
import queue
from statistics import median
import sys
import time
from unittest.mock import Mock, patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app


def main():
    source = (ROOT / "project_review/github/td2-loot-advisor/app.py").read_text(encoding="utf-8")
    cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "App")
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "scan_image")
    fn.name = "baseline_scan"
    scope = dict(app.__dict__)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<release scan>", "exec"), scope)
    baseline = scope["baseline_scan"]
    app.OCR = app.ocr_backend.Engine("rapidocr")
    app.gamedata.SCALE = None
    image = Image.open(ROOT / "tests/samples/stoner_lamg_3440x1440.png").convert("RGB")

    def run(scan):
        obj = app.App.__new__(app.App)
        obj.cfg = json.loads((ROOT / "scripts/default_builds.json").read_text(encoding="utf-8"))
        obj.cfg["settings"].update(scan_source="region", region={"width": image.width, "height": image.height},
                                   ocr_passes_auto=False, ocr_passes=1, save_debug_crop=False)
        obj.results = queue.Queue()
        obj.last_sig, obj.last_time = None, 0
        obj.root = Mock()
        obj.scan_area = lambda: {"left": 0, "top": 0}
        obj.timings = app.performance.TimingStats()
        start = time.perf_counter()
        with patch.object(app.GAME, "learn", return_value=[]):
            scan(obj, image, False)
        elapsed = time.perf_counter() - start
        result = obj.results.get_nowait()
        return elapsed, {"attrs": result[2]["attrs"], "name": result[2]["name"], "verdict": result[3]}

    # Warm both paths and input shapes before measuring; alternate execution order.
    run(baseline)
    run(app.App.scan_image)
    rows = []
    for index in range(4):
        if index % 2:
            after, a = run(app.App.scan_image)
            before, b = run(baseline)
        else:
            before, b = run(baseline)
            after, a = run(app.App.scan_image)
        assert a == b, (a, b)
        rows.append({"baseline_s": round(before, 4), "region_fastpath_s": round(after, 4), "same_result": True})
    report = {"sample": "stoner_lamg_3440x1440.png",
              "conditions": "CPU RapidOCR, both paths warmed, selected card region, one pass; no capture/game",
              "runs": rows, "median_before_s": median(r["baseline_s"] for r in rows),
              "median_after_s": median(r["region_fastpath_s"] for r in rows)}
    (ROOT / "project_review/scan_latency/region_benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
