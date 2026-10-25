"""Windows OCR (ikinci motor) doğruluk/hız testi — örnek kartlarda RapidOCR ile karşılaştırma. Windows CI.
    python tests/test_winocr.py"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image  # noqa: E402
import gamedata, ocr_backend, engine  # noqa: E402
from PIL import ImageOps  # noqa: E402

print("winocr_available:", ocr_backend.winocr_available())
ocr_backend._win_engine(); print("info:", ocr_backend.winocr_info())
truth = json.loads((ROOT / "tests/samples/truth.json").read_text(encoding="utf-8"))
game = gamedata.GameData(ROOT / "tests/.game_cache.json", ROOT / "meta/game_data.json", ROOT / "meta/game_data.json")
rap = ocr_backend.Engine("rapidocr", preprocess=gamedata.text_image); rap.warm_up(); time.sleep(3)
rows, ok_all = [], True
for res, k in truth["resolutions"].items():
    for smp in truth["samples"]:
        img = Image.open(ROOT / "tests/samples" / smp["file"]).convert("RGB")
        if k != 1: img = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
        out = {"res": res, "sample": smp["file"][:24]}
        box = engine.find_card(img, rap.data, preprocess=False)
        card = img.crop(box) if box else img
        out["card"] = f"{card.width}x{card.height}" if box else "not found"
        inv = lambda im: ImageOps.invert(ImageOps.autocontrast(im.convert("L"))).convert("RGB")
        for name, fn in (("win_full", lambda im: ocr_backend.winocr_lines(im)),
                         ("win_card", lambda im: ocr_backend.winocr_lines(card)),
                         ("win_card_inv", lambda im: ocr_backend.winocr_lines(inv(card))),
                         ("win_card_inv2x", lambda im: ocr_backend.winocr_lines(inv(card), 2.0)),
                         ("rapid_card", lambda im: rap.lines(card))):
            t0 = time.perf_counter(); lines = fn(img); dt = (time.perf_counter() - t0) * 1000
            r = game.recognize("\n".join(l for l, _, _ in lines))
            want = smp["attrs"]; hit = sum(1 for a, v in want.items() if abs(r["attrs"].get(a, -1) - v) < 0.05)
            name_ok = smp.get("name") is None or r["name"] == smp["name"]
            out[name] = f"{hit}/{len(want)}{'' if name_ok else ' name✗'} {dt:.0f}ms"
            if name == "win_card_inv" and lines: out["win_first"] = lines[0][0][:40]
        rows.append(out); print(json.dumps(out, ensure_ascii=False), flush=True)
print("RESULT: DONE")
