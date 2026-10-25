"""Render karelerini programın kullanacağı biçime çevirir.

    python pack_frames.py RENDER_DIR OUT_DIR OUTFIT
RENDER_DIR: 00.png (RGBA) + 00_id.png (yuva renkleri) … ; OUT_DIR: f00.webp + m00.png (yuva no 0-8) + info.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image

SLOTS = ("Mask", "Chest", "Backpack", "Gloves", "Holster", "Kneepads", "Weapon", "Sidearm")
IDS = {"Mask": (255, 0, 0), "Chest": (0, 255, 0), "Backpack": (0, 0, 255), "Gloves": (255, 255, 0),
       "Holster": (255, 0, 255), "Kneepads": (0, 255, 255), "Weapon": (255, 128, 0), "Sidearm": (128, 0, 255)}


def main(src, dst, outfit):
    src, dst = Path(src), Path(dst); dst.mkdir(parents=True, exist_ok=True)
    frames = sorted(p for p in src.glob("[0-9][0-9].png"))
    pal = [(0, 0, 0)] + [IDS[s] for s in SLOTS]
    anchors, size = [], None
    for i, fp in enumerate(frames):
        im = Image.open(fp).convert("RGBA"); size = im.size
        bbox = im.getbbox()
        im.save(dst / f"f{i:02d}.webp", "WEBP", quality=82, method=6)
        idm = Image.open(src / f"{fp.stem}_id.png").convert("RGB")
        px = idm.load(); w, h = idm.size
        out = Image.new("L", (w, h)); po = out.load()
        acc = {k: [0, 0, 0] for k in range(1, 9)}
        for y in range(h):
            for x in range(w):
                c = px[x, y]
                if c == (0, 0, 0): continue
                k = min(range(1, 9), key=lambda j: sum((c[t] - pal[j][t]) ** 2 for t in range(3)))
                if sum((c[t] - pal[k][t]) ** 2 for t in range(3)) > 6000: continue
                po[x, y] = k; a = acc[k]; a[0] += x; a[1] += y; a[2] += 1
        out.save(dst / f"m{i:02d}.png", optimize=True)
        from fix_anchors import anchors_of
        anchors.append({SLOTS[k - 1]: v for k, v in anchors_of(out).items()})
        print("packed", i, flush=True)
    info = {"outfit": outfit, "frames": len(frames), "size": list(size), "slots": list(SLOTS), "anchors": anchors,
            "credits": "Original design. Body base: MakeHuman (CC0)."}
    (dst / "info.json").write_text(json.dumps(info, separators=(",", ":")))


if __name__ == "__main__":
    main(*sys.argv[1:4])
