"""Tarama zinciri ölçümü (5.0.9 öncesi/sonrası karşılaştırma için).

    python tests/bench_scan.py [--json out.json]
A) Boşta döngü: ekran yakalama + küçük özet (her 0,7 sn'de bir yapılan iş)
B) Kart okuma: örnek kartlar, 1 geçiş vs 3 geçiş; ek geçişler sonucu değiştiriyor mu
C) Kart görüntüsünü PNG kaydetme
"""
import json
import statistics as stt
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageOps  # noqa: E402

import gamedata  # noqa: E402
import ocr_backend  # noqa: E402

out = {}


def timeit(fn, n):
    ts = []
    for _ in range(n):
        t0 = time.perf_counter(); fn(); ts.append((time.perf_counter() - t0) * 1000)
    return round(stt.median(ts), 2)


# ---- A) boşta döngü
try:
    import mss
    with mss.mss() as s:
        mon = s.monitors[1]
    region = {"left": mon["left"], "top": mon["top"], "width": mon["width"], "height": mon["height"]}

    def old_iter():
        with mss.mss() as sct:
            g = sct.grab(region); img = Image.frombytes("RGB", g.size, g.rgb)
        list(ImageOps.grayscale(img).resize((24, 24)).getdata())
    out["idle_old_ms"] = timeit(old_iter, 15)
    try:
        import capture
        cap = capture.Grabber()
        out["idle_new_ms"] = timeit(lambda: cap.thumb(region), 15)
        out["capture_backend"] = cap.backend
    except ImportError:
        pass
    out["screen"] = f"{region['width']}x{region['height']}"
except Exception as e:
    out["idle_error"] = str(e)

# ---- B) kart okuma
truth = json.loads((ROOT / "tests/samples/truth.json").read_text(encoding="utf-8"))
game = gamedata.GameData(ROOT / "tests/.game_cache.json", ROOT / "meta/game_data.json", ROOT / "meta/game_data.json")
eng = ocr_backend.Engine("rapidocr", preprocess=gamedata.text_image); eng.warm_up()
time.sleep(0.5)
rows = []
for smp in truth["samples"]:
    for res, k in (("1440p", 1.0), ("1080p", 0.75)):
        img = Image.open(ROOT / "tests/samples" / smp["file"]).convert("RGB")
        if k != 1: img = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
        gamedata.SCALE, gamedata.THRESHOLD = None, 170
        t0 = time.perf_counter(); lines = eng.lines(img); t1 = (time.perf_counter() - t0) * 1000
        r1 = game.recognize("\n".join(l for l, _, _ in lines))
        a = ocr_backend.Engine.auto_scale(img)
        extra, best = 0.0, r1
        for sc in [x for x in (2.0, 1.0, 1.5) if abs(x - a) > 0.1][:2]:
            t0 = time.perf_counter(); tx = "\n".join(l for l, _, _ in eng.lines(img, sc)); extra += (time.perf_counter() - t0) * 1000
            r = game.recognize(tx)
            if len(r.get("attrs", {})) > len(best.get("attrs", {})): best = r
        want = smp["attrs"]
        hit1 = sum(1 for at, v in want.items() if abs(r1["attrs"].get(at, -1) - v) < 0.05)
        hit3 = sum(1 for at, v in want.items() if abs(best["attrs"].get(at, -1) - v) < 0.05)
        txt1 = "\n".join(l for l, _, _ in lines)
        t0 = time.perf_counter(); game.recognize(txt1); rec_first = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter(); game.recognize(txt1); rec_again = (time.perf_counter() - t0) * 1000
        dig = [c for l, _, c in lines if any(ch.isdigit() for ch in l)]
        confident = bool(r1.get("known")) and not r1.get("partial") and float(r1.get("confidence") or 0) >= 0.95 and bool(r1.get("attrs")) and bool(dig) and min(dig) >= 0.9
        rows.append({"sample": smp["file"], "res": res, "pass1_ms": round(t1), "extra_ms": round(extra),
                     "recognize_first_ms": round(rec_first), "recognize_again_ms": round(rec_again), "confident": confident,
                     "hit1": hit1, "hit3": hit3, "want": len(want), "complete1": r1.get("known", False)})
        t0 = time.perf_counter(); img.save(ROOT / "tests/.bench_card.png"); rows[-1]["png_ms"] = round((time.perf_counter() - t0) * 1000)
out["cards"] = rows
print(json.dumps(out, indent=1, ensure_ascii=False))
if "--json" in sys.argv:
    Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(out, indent=1), encoding="utf-8")
