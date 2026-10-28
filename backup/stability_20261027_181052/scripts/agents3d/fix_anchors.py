"""Etiket noktalarını maskelerden yeniden hesapla: her yuva için, o yuvanın piksellerinden ağırlık merkezine en yakın olanı.

    python fix_anchors.py meta/agents/<kıyafet>      (ya da birden çok klasör)
"""
import json
import sys
from pathlib import Path

from PIL import Image


def anchors_of(mask, nslots=8, step=2):
    px = mask.load(); w, h = mask.size
    pts = {k: [] for k in range(1, nslots + 1)}
    for y in range(0, h, step):
        for x in range(0, w, step):
            k = px[x, y]
            if k: pts[k].append((x, y))
    out = {}
    for k, ps in pts.items():
        if len(ps) * step * step < 12: continue
        cx = sum(p[0] for p in ps) / len(ps); cy = sum(p[1] for p in ps) / len(ps)
        bx, by = min(ps, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
        out[k] = [bx, by, len(ps) * step * step]
    return out


def main(dirs):
    for d in map(Path, dirs):
        info = json.loads((d / "info.json").read_text(encoding="utf-8"))
        slots = info["slots"]
        info["anchors"] = [{slots[k - 1]: v for k, v in anchors_of(Image.open(d / f"m{i:02d}.png")).items()}
                           for i in range(info["frames"])]
        (d / "info.json").write_text(json.dumps(info, separators=(",", ":")))
        print("fixed", d)


if __name__ == "__main__":
    main(sys.argv[1:])
