"""Kumanda bileşimi ve Windows OCR.   python tests/test_inputs.py"""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import gamepad  # noqa: E402
import winocr  # noqa: E402

fails = 0


def ok(c, m):
    global fails
    print(("OK   " if c else "FAIL ") + m)
    if not c: fails += 1


ok(gamepad.mask_of("back+rb") == 0x0220 and gamepad.mask_of("off") == 0, "tuş maskeleri")
state = {"b": 0}; hits = []
w = gamepad.ComboWatcher("back+rb", lambda: hits.append(1), read_buttons=lambda: state["b"])
seq = [0, 0x0020, 0x0220, 0x0220, 0x0220, 0x0020, 0, 0x0220, 0x1220]
for b in seq:
    state["b"] = b; w.poll()
ok(len(hits) == 2, "bileşim basılınca bir kez, bırakıp yeniden basınca bir kez daha (%d)" % len(hits))
hits.clear(); state["b"] = 0x0200
for _ in range(5): w.poll()
ok(not hits, "yalnız RB tetiklemez")
w2 = gamepad.ComboWatcher("off", lambda: None, read_buttons=lambda: 0)
ok(not w2.available, "kapalıyken çalışmaz")
if os.name == "nt":
    real = gamepad.ComboWatcher("back+rb", lambda: None)
    t0 = time.perf_counter()
    for _ in range(30): real._x and real._read()
    print(f"     XInput: {'var' if real._x else 'yok'}, 30 okuma {1000 * (time.perf_counter() - t0):.2f} ms")
    ok(real._x is not None, "XInput DLL yüklendi")

# Windows OCR
wo = winocr.WinOCR()
print("     Windows OCR:", "var" if wo.available else f"yok ({wo.error})")
if os.name == "nt" and wo.available:
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (900, 120), (20, 22, 26)); d = ImageDraw.Draw(img)
    try: f = ImageFont.truetype("segoeui.ttf", 30)
    except OSError: f = ImageFont.load_default()
    d.text((20, 15), "Head to the White House and talk to Manny.", fill=(240, 240, 240), font=f)
    d.text((640, 70), "Close Map", fill=(240, 240, 240), font=f)
    t0 = time.perf_counter(); segs = wo.segments(img); ms = 1000 * (time.perf_counter() - t0)
    print("     ", segs, f"{ms:.0f} ms")
    txt = " ".join(s[0] for s in segs).lower()
    ok("white house" in txt and "manny" in txt, "Windows OCR okudu")
    ok(len(segs) >= 2, "sütunlar ayrı parça")

print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
sys.exit(1 if fails else 0)
