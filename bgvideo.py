"""Özgün arka plan videoları üretir (oyundan görüntü/logo yok — tamamen kodla çizilir).

Stiller (Division havasında, kesintisiz döngü):
  hexscan   — altıgen ızgara, tarayıcı ışık şeridi, yanıp sönen hücreler
  radar     — dönen radar halkaları, HUD yayları, akan veri satırları
  wintercity— kar yağan gece şehri silueti, sokak lambaları, sis
  embers    — yükselen kıvılcımlar ve bokeh ışıklar
  tacmap    — taktik harita: yollar, hareket eden rota, nabız atan hedefler
  storm     — yağmurlu alacakaranlık şehir, şimşek çakmaları
Her stil farklı renk temaları ve tohumlarla çoğaltılabilir (variants).
PyAV (av) gerekir.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

STYLES = ["hexscan", "radar", "wintercity", "embers", "tacmap", "storm"]
THEMES = {"orange": (255, 109, 16), "cyan": (56, 189, 248), "green": (34, 197, 94), "red": (239, 68, 68),
          "amber": (234, 179, 8), "violet": (168, 85, 247)}


def _mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def _bg(w, h, top=(16, 18, 24), bottom=(6, 7, 10)):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        d.line((0, y, w, y), fill=_mix(top, bottom, y / max(1, h - 1)))
    return im


class Renderer:
    def __init__(self, style, w, h, fps, seconds, color, seed):
        self.style, self.w, self.h, self.fps, self.n = style, w, h, fps, int(fps * seconds)
        self.c, self.rng = color, random.Random(seed)
        getattr(self, "_init_" + style)()

    def frame(self, i):
        return getattr(self, "_f_" + self.style)(i, i / self.n)        # p: 0..1 döngü evresi

    # ---------------------------------------------------------- hexscan
    def _init_hexscan(self):
        w, h, r = self.w, self.h, max(10, self.h // 9)
        self.base = _bg(w, h)
        self.hexes = []
        dx, dy = r * 1.732, r * 1.5
        y, row = -r, 0
        while y < h + r:
            x = -r + (dx / 2 if row % 2 else 0)
            while x < w + r:
                pts = [(x + r * 0.92 * math.cos(math.radians(60 * k + 30)), y + r * 0.92 * math.sin(math.radians(60 * k + 30))) for k in range(6)]
                self.hexes.append((x, y, pts, self.rng.random(), self.rng.randint(1, 3)))
                x += dx
            y += dy; row += 1
        d = ImageDraw.Draw(self.base)
        for _, _, pts, _, _ in self.hexes:
            d.polygon(pts, outline=_mix((16, 18, 24), self.c, 0.18))

    def _f_hexscan(self, i, p):
        im = self.base.copy()
        d = ImageDraw.Draw(im)
        sx = (p * 1.4 - 0.2) * self.w
        for x, y, pts, ph, sp in self.hexes:
            near = max(0.0, 1 - abs(x - sx) / (self.w * 0.12))
            blink = max(0.0, math.sin(2 * math.pi * (p * sp + ph))) ** 12
            k = min(1.0, near * 0.55 + blink * 0.45)
            if k > 0.04:
                d.polygon(pts, fill=_mix((14, 16, 21), self.c, k * 0.45), outline=_mix((16, 18, 24), self.c, 0.3 + k * 0.6))
        glow = Image.new("RGB", (self.w, self.h))
        gd = ImageDraw.Draw(glow)
        gd.rectangle((sx - 6, 0, sx + 6, self.h), fill=self.c)
        glow = glow.filter(ImageFilter.GaussianBlur(14))
        return Image.blend(im, Image.composite(glow, im, glow.convert("L")), 0.6)

    # ---------------------------------------------------------- radar
    def _init_radar(self):
        self.base = _bg(self.w, self.h)
        d = ImageDraw.Draw(self.base)
        for x in range(0, self.w, 40): d.line((x, 0, x, self.h), fill=(20, 23, 30))
        for y in range(0, self.h, 40): d.line((0, y, self.w, y), fill=(20, 23, 30))
        self.blips = [(self.rng.uniform(0, 2 * math.pi), self.rng.uniform(0.25, 0.95)) for _ in range(9)]
        self.rows = ["%04X  %s  %5.1f" % (self.rng.randint(0, 65535), self.rng.choice(["SCAN", "LINK", "TRACK", "SYNC", "INTEL"]),
                                          self.rng.uniform(0, 999)) for _ in range(40)]

    def _f_radar(self, i, p):
        im = self.base.copy()
        d = ImageDraw.Draw(im)
        cx, cy, R = self.w * 0.72, self.h * 0.55, self.h * 0.9
        dim = _mix((14, 16, 21), self.c, 0.35)
        for k in (0.33, 0.66, 1.0):
            d.ellipse((cx - R * k, cy - R * k, cx + R * k, cy + R * k), outline=dim, width=2)
        ang = 2 * math.pi * p
        for j in range(18):                                     # tarama yelpazesi
            a = ang - j * 0.035
            col = _mix((14, 16, 21), self.c, max(0.0, 0.8 - j * 0.045))
            d.line((cx, cy, cx + R * math.cos(a), cy + R * math.sin(a)), fill=col, width=3)
        for a0, rr in self.blips:
            diff = (ang - a0) % (2 * math.pi)
            k = max(0.0, 1 - diff / 2.0)
            if k > 0:
                x, y = cx + R * rr * math.cos(a0), cy + R * rr * math.sin(a0)
                s = 3 + 5 * k
                d.ellipse((x - s, y - s, x + s, y + s), fill=_mix((14, 16, 21), self.c, k))
        for j, a in enumerate((0.0, 2.1, 4.2)):                  # dönen HUD yayları
            st = math.degrees(a + 2 * math.pi * p * (1 if j % 2 else -1))
            rr = R * (1.08 + j * 0.06)
            d.arc((cx - rr, cy - rr, cx + rr, cy + rr), st, st + 50, fill=self.c, width=2)
        off = int(p * len(self.rows)) % len(self.rows)
        for j in range(max(3, self.h // 18)):
            txt = self.rows[(off + j) % len(self.rows)]
            d.text((16, 8 + j * 16), txt, fill=_mix((30, 34, 42), self.c, 0.55 if j else 0.95))
        return im

    # ---------------------------------------------------------- wintercity
    def _init_wintercity(self):
        w, h = self.w, self.h
        self.base = _bg(w, h, (18, 22, 34), (8, 9, 14))
        d = ImageDraw.Draw(self.base)
        for layer, (shade, hmin, hmax) in enumerate(((26, 0.35, 0.75), (16, 0.45, 0.95))):
            x = -20
            while x < w:
                bw = self.rng.randint(22, 70); bh = int(h * self.rng.uniform(hmin, hmax))
                d.rectangle((x, h - bh, x + bw, h), fill=(shade, shade + 2, shade + 6))
                for wy in range(h - bh + 6, h - 4, 9):
                    for wx in range(x + 4, x + bw - 4, 8):
                        if self.rng.random() < 0.18:
                            d.rectangle((wx, wy, wx + 3, wy + 4), fill=_mix((40, 40, 40), self.c, self.rng.uniform(0.4, 0.9)))
                x += bw + self.rng.randint(0, 10)
        self.flakes = [(self.rng.uniform(0, w), self.rng.uniform(0, h), self.rng.uniform(0.6, 2.2), self.rng.uniform(0, 1)) for _ in range(260)]
        fog = Image.new("RGB", (w, h), self.c)
        mask = Image.linear_gradient("L").resize((w, h)).point(lambda v: int(v * 0.22))
        self.base = Image.composite(fog, self.base, mask)

    def _f_wintercity(self, i, p):
        im = self.base.copy()
        d = ImageDraw.Draw(im)
        for x, y, s, ph in self.flakes:
            yy = (y + p * self.h * 2 * s) % self.h
            xx = (x + math.sin(2 * math.pi * (p * 2 + ph)) * 12 * s) % self.w
            c = int(150 + 90 * (s / 2.2))
            d.ellipse((xx - s, yy - s, xx + s, yy + s), fill=(c, c, c + 10))
        return im

    # ---------------------------------------------------------- embers
    def _init_embers(self):
        self.base = _bg(self.w, self.h, (14, 12, 12), (5, 5, 7))
        self.parts = [(self.rng.uniform(0, self.w), self.rng.uniform(0, 1), self.rng.uniform(0.5, 1.6), self.rng.uniform(1, 3.5),
                       self.rng.uniform(0, 1)) for _ in range(160)]
        self.bokeh = [(self.rng.uniform(0, self.w), self.rng.uniform(0, self.h), self.rng.uniform(10, 34), self.rng.uniform(0, 1)) for _ in range(14)]

    def _f_embers(self, i, p):
        im = self.base.copy()
        lay = Image.new("RGB", (self.w, self.h))
        d = ImageDraw.Draw(lay)
        for x, y, r, ph in self.bokeh:
            k = 0.15 + 0.15 * math.sin(2 * math.pi * (p + ph))
            d.ellipse((x - r, y - r, x + r, y + r), fill=_mix((0, 0, 0), self.c, k))
        lay = lay.filter(ImageFilter.GaussianBlur(6))
        im = Image.composite(lay, im, lay.convert("L"))
        d = ImageDraw.Draw(im)
        for x, y0, sp, s, ph in self.parts:
            yy = self.h * (1 - ((y0 + p * sp * 2) % 1.0))
            xx = x + math.sin(2 * math.pi * (p * 3 + ph)) * 10
            life = (y0 + p * sp * 2) % 1.0
            col = _mix((255, 230, 180), self.c, life)
            col = _mix((5, 5, 7), col, max(0.15, 1 - life))
            d.ellipse((xx - s, yy - s, xx + s, yy + s), fill=col)
        return im

    # ---------------------------------------------------------- tacmap
    def _init_tacmap(self):
        w, h = self.w, self.h
        self.base = _bg(w, h, (12, 15, 20), (8, 10, 14))
        d = ImageDraw.Draw(self.base)
        for x in range(0, w, 24): d.line((x, 0, x, h), fill=(17, 21, 28))
        for y in range(0, h, 24): d.line((0, y, w, y), fill=(17, 21, 28))
        roads = []
        for _ in range(9):
            if self.rng.random() < 0.5:
                y = self.rng.randint(0, h); roads.append(((0, y), (w, y + self.rng.randint(-30, 30))))
            else:
                x = self.rng.randint(0, w); roads.append(((x, 0), (x + self.rng.randint(-60, 60), h)))
        for a, b in roads: d.line((a, b), fill=(34, 40, 52), width=5)
        for _ in range(40):
            x, y = self.rng.randint(0, w), self.rng.randint(0, h)
            d.rectangle((x, y, x + self.rng.randint(10, 40), y + self.rng.randint(8, 30)), outline=(26, 31, 41))
        self.route = [(self.rng.uniform(0.05, 0.95) * w, self.rng.uniform(0.15, 0.85) * h) for _ in range(6)]
        self.route.append(self.route[0])
        self.targets = [(self.rng.uniform(0, w), self.rng.uniform(0, h), self.rng.uniform(0, 1)) for _ in range(7)]

    def _f_tacmap(self, i, p):
        im = self.base.copy()
        d = ImageDraw.Draw(im)
        pts = self.route
        segs = [(pts[j], pts[j + 1]) for j in range(len(pts) - 1)]
        L = [math.dist(a, b) for a, b in segs]; tot = sum(L)
        for (a, b), l in zip(segs, L):                          # kesikli rota
            n = max(1, int(l // 14))
            for k in range(n):
                if (k + int(p * 40)) % 2: continue
                t0, t1 = k / n, (k + 0.6) / n
                d.line((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0, a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1),
                       fill=_mix((20, 24, 30), self.c, 0.6), width=2)
        pos = p * tot                                          # rota üzerindeki ajan
        for (a, b), l in zip(segs, L):
            if pos <= l:
                x, y = a[0] + (b[0] - a[0]) * pos / l, a[1] + (b[1] - a[1]) * pos / l; break
            pos -= l
        d.polygon([(x, y - 7), (x + 6, y + 5), (x - 6, y + 5)], fill=self.c)
        for tx, ty, ph in self.targets:
            k = (p * 2 + ph) % 1.0
            r = 4 + 18 * k
            d.ellipse((tx - r, ty - r, tx + r, ty + r), outline=_mix((12, 15, 20), (239, 68, 68), 1 - k), width=2)
            d.ellipse((tx - 3, ty - 3, tx + 3, ty + 3), fill=(239, 68, 68))
        return im

    # ---------------------------------------------------------- storm
    def _init_storm(self):
        w, h = self.w, self.h
        self.base = _bg(w, h, (26, 30, 40), (8, 9, 13))
        d = ImageDraw.Draw(self.base)
        x = 0
        while x < w:
            bw = self.rng.randint(18, 60); bh = int(h * self.rng.uniform(0.3, 0.8))
            d.rectangle((x, h - bh, x + bw, h), fill=(12, 13, 17))
            x += bw + self.rng.randint(0, 6)
        self.drops = [(self.rng.uniform(0, w), self.rng.uniform(0, h), self.rng.uniform(0.7, 1.3)) for _ in range(300)]
        self.flash = sorted(self.rng.uniform(0.1, 0.9) for _ in range(2))

    def _f_storm(self, i, p):
        im = self.base.copy()
        fl = max([max(0.0, 1 - abs(p - f) * 40) for f in self.flash] + [0.0])
        if fl > 0:
            im = Image.blend(im, Image.new("RGB", im.size, (200, 210, 235)), fl * 0.45)
        d = ImageDraw.Draw(im)
        for x, y, s in self.drops:
            yy = (y + p * self.h * 6 * s) % self.h
            xx = (x - p * self.w * 0.2 * s) % self.w
            d.line((xx, yy, xx - 3 * s, yy + 9 * s), fill=(120, 135, 160))
        lamp = Image.new("RGB", im.size)
        ld = ImageDraw.Draw(lamp)
        for k in range(5):
            lx = (k + 0.5) * self.w / 5
            ld.ellipse((lx - 40, self.h - 30, lx + 40, self.h + 30), fill=_mix((0, 0, 0), self.c, 0.5))
        lamp = lamp.filter(ImageFilter.GaussianBlur(18))
        return Image.composite(lamp, im, lamp.convert("L").point(lambda v: int(v * 0.8)))


def render(path, style="hexscan", color="orange", seed=1, w=1280, h=200, fps=24, seconds=10, progress=None):
    """Tek bir döngü videosu yazar (mp4). Dönüş: yol."""
    import av
    col = THEMES.get(color, color) if isinstance(color, str) else color
    r = Renderer(style, w, h, fps, seconds, col, seed)
    out = av.open(str(path), "w")
    stream = None
    for codec in ("libx264", "h264", "mpeg4"):
        try:
            stream = out.add_stream(codec, rate=fps)
            break
        except Exception:
            continue
    stream.width, stream.height, stream.pix_fmt = w, h, "yuv420p"
    try: stream.bit_rate = 1_600_000
    except Exception: pass
    for i in range(r.n):
        img = r.frame(i)
        for pkt in stream.encode(av.VideoFrame.from_image(img)): out.mux(pkt)
        if progress and i % 24 == 0: progress(i / r.n)
    for pkt in stream.encode(): out.mux(pkt)
    out.close()
    return Path(path)


def default_set():
    """Varsayılan paket: her stil için 2 renk = 12 video."""
    pairs = []
    cols = ["cyan", "green", "red", "amber", "violet", "cyan"]
    for i, st in enumerate(STYLES):
        pairs.append((st, "orange", 10 + i))
        pairs.append((st, cols[i % len(cols)], 50 + i))
    return pairs


def generate(folder, count=None, start_seed=None, progress=None, stop=lambda: False):
    """Klasöre video üretir. count verilirse yeni tohumlarla rastgele stil/renk (çoğaltma)."""
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    if count is None:
        jobs = default_set()
    else:
        rng = random.Random(start_seed)
        jobs = [(rng.choice(STYLES), rng.choice(list(THEMES)), rng.randint(100, 10 ** 6)) for _ in range(count)]
    made = []
    for k, (st, col, seed) in enumerate(jobs):
        if stop(): break
        p = folder / f"td2bg_{st}_{col}_{seed}.mp4"
        if p.exists(): continue
        render(p, st, col, seed, progress=(lambda f, k=k: progress((k + f) / len(jobs))) if progress else None)
        made.append(p)
    return made


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "art/videos")
    for p in generate(out, progress=lambda f: print(f"{f * 100:5.1f}%", end="\r")):
        print("\n", p)
