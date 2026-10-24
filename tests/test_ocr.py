"""OCR regresyon testi: gerçek oyun kartları farklı çözünürlüklerde okunur, attribute'lar doğrulanır.

    python tests/test_ocr.py            # tablo + başarı oranı (RapidOCR ve Tesseract, hangisi kuruluysa)
    python tests/test_ocr.py rapidocr   # tek motor
Çıkış kodu: seçilen/varsayılan motor 1080p ve 720p'de tüm alanları doğru okumazsa 1.
"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image  # noqa: E402
import gamedata, ocr_backend  # noqa: E402

def main(argv):
    truth = json.loads((ROOT / "tests/samples/truth.json").read_text(encoding="utf-8"))
    game = gamedata.GameData(ROOT / "tests/.game_cache.json", ROOT / "meta/game_data.json", ROOT / "meta/game_data.json")
    names = argv[1:] or [n for n, ok in (("rapidocr", ocr_backend.rapid_available()),
                                         ("tesseract", ocr_backend.tesseract_available())) if ok]
    must_pass, failed = {"1080p", "720p"}, False
    print(f"{'engine':10} {'res':6} {'sample':34} {'attrs':>6} {'sec':>5}")
    for name in names:
        eng = ocr_backend.Engine(name, preprocess=gamedata.text_image)
        if eng.name != name: print(f"{name}: not available"); continue
        eng.warm_up() if name == "rapidocr" else None
        for res, k in truth["resolutions"].items():
            for smp in truth["samples"]:
                img = Image.open(ROOT / "tests/samples" / smp["file"]).convert("RGB")
                if k != 1: img = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
                gamedata.SCALE, gamedata.THRESHOLD = None, 170
                t0 = time.time(); r = game.recognize(eng.text(img)); dt = time.time() - t0
                want = smp["attrs"]
                hit = sum(1 for a, v in want.items() if abs(r["attrs"].get(a, -1) - v) < 0.05)
                ok = hit == len(want) and (smp.get("name") is None or r["name"] == smp["name"])
                if not ok and res in must_pass and name == names[0]: failed = True
                print(f"{name:10} {res:6} {smp['file']:34} {hit}/{len(want):<4} {dt:5.1f} {'✔' if ok else '✖'}")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
