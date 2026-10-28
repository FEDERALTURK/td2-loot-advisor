"""
Özgün görseller / original artwork for TD2 Loot Advisor (Pillow ile çizilir).

- Arka planlar: Division havasında ama tamamen özgün "taktik" bantlar
  (gece şehri, altıgen ızgara, HUD radar, topoğrafik çizgiler, sis).
- Build amblemleri: build'in ROLÜNE göre (DPS, tank, yetenek, yakın mesafe,
  hassas atış, nabız) üretilen özgün amblemler. Oyundaki resmi set
  logoları KULLANILMAZ ve taklit edilmez.
- Bayraklar: dil seçiminde gösterilen ulusal bayraklar.

Kullanıcı kendi görsellerini ekleyebilir:
  art/backgrounds/*.png|jpg      → dönen arka planlara katılır
  art/emblems/<build adı>.png    → o build'in amblemi yerine kullanılır
  art/flags/<dil kodu>.png       → o dilin bayrağı yerine kullanılır
"""
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ART_VERSION = 1
BG_SIZE = (2000, 300)
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
ORANGE = (255, 109, 16)


# ───────────── yardımcılar ─────────────
def _rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _vgradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        img.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img.resize((w, h))


def _vignette(img, strength=0.55):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((-w * 0.15, -h * 0.9, w * 1.15, h * 1.9), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(h * 0.6))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, Image.blend(img, dark, strength), mask)


def _glow(layer, radius):
    """RGBA katmanı bulanıklaştırıp altına ekleyerek parlama verir."""
    blur = layer.filter(ImageFilter.GaussianBlur(radius))
    out = Image.alpha_composite(blur, blur)
    return Image.alpha_composite(out, layer)


def _noise(img, amount=10, seed=1):
    rnd = random.Random(seed)
    w, h = img.size
    n = Image.new("L", (w // 4, h // 4))
    n.putdata([rnd.randint(128 - amount, 128 + amount) for _ in range((w // 4) * (h // 4))])
    n = n.resize((w, h))
    return Image.blend(img, Image.merge("RGB", (n, n, n)), 0.06)


# ───────────── arka planlar ─────────────
def bg_skyline(seed=11):
    w, h = BG_SIZE
    rnd = random.Random(seed)
    img = _vgradient((w, h), (8, 10, 16), (38, 22, 14)).convert("RGBA")
    haze = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(haze).ellipse((w * 0.25, h * 0.55, w * 0.95, h * 1.6), fill=(255, 110, 30, 90))
    img = Image.alpha_composite(img, haze.filter(ImageFilter.GaussianBlur(60)))
    for depth, (col, hmin, hmax, win) in enumerate((((26, 26, 34), 70, 150, 0.04),
                                                      ((18, 18, 25), 100, 210, 0.07),
                                                      ((10, 10, 14), 130, 260, 0.11))):
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        x = -20
        while x < w:
            bw = rnd.randint(40, 120 - depth * 10); bh = rnd.randint(hmin, hmax)
            top = h - bh
            d.rectangle((x, top, x + bw, h), fill=col + (255,))
            if rnd.random() < 0.25:                       # çatı detayı / anten
                d.rectangle((x + bw // 3, top - rnd.randint(8, 24), x + bw // 3 + 3, top), fill=col + (255,))
            for wy in range(top + 8, h - 6, 11):           # pencereler
                for wx in range(x + 6, x + bw - 6, 9):
                    if rnd.random() < win:
                        c = (255, rnd.randint(150, 200), 90, rnd.randint(140, 230))
                        d.rectangle((wx, wy, wx + 3, wy + 4), fill=c)
            x += bw + rnd.randint(0, 6)
        img = Image.alpha_composite(img, layer)
    snow = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(snow)
    for _ in range(900):                                    # kar taneleri
        sx, sy, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.choice((1, 1, 1, 2))
        d.ellipse((sx, sy, sx + r, sy + r), fill=(235, 240, 255, rnd.randint(60, 170)))
    img = Image.alpha_composite(img, snow)
    return _noise(_vignette(img.convert("RGB")), seed=seed)


def bg_hexgrid(seed=22):
    w, h = BG_SIZE
    rnd = random.Random(seed)
    img = _vgradient((w, h), (12, 15, 22), (6, 7, 10)).convert("RGBA")
    lines = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lines)
    hot = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dh = ImageDraw.Draw(hot)
    r = 34; hw = r * math.sqrt(3)
    for row in range(-1, int(h / (r * 1.5)) + 2):
        for col in range(-1, int(w / hw) + 2):
            cx = col * hw + (hw / 2 if row % 2 else 0); cy = row * r * 1.5
            pts = [(cx + r * math.cos(math.radians(60 * k - 30)), cy + r * math.sin(math.radians(60 * k - 30))) for k in range(6)]
            fade = 1 - abs(cx - w * 0.7) / (w * 0.9)
            d.polygon(pts, outline=(120, 140, 170, int(25 + 45 * max(0, fade))))
            if rnd.random() < 0.035:
                dh.polygon(pts, fill=ORANGE + (rnd.randint(40, 110),), outline=ORANGE + (230,))
    img = Image.alpha_composite(img, lines)
    img = Image.alpha_composite(img, _glow(hot, 12))
    sweep = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sweep).polygon([(w * 0.45, 0), (w * 0.55, 0), (w * 0.42, h), (w * 0.32, h)], fill=(255, 140, 60, 26))
    img = Image.alpha_composite(img, sweep.filter(ImageFilter.GaussianBlur(30)))
    return _noise(_vignette(img.convert("RGB"), 0.45), seed=seed)


def bg_radar(seed=33):
    w, h = BG_SIZE
    rnd = random.Random(seed)
    img = _vgradient((w, h), (7, 12, 16), (10, 9, 12)).convert("RGBA")
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(grid)
    for x in range(0, w, 40): d.line((x, 0, x, h), fill=(70, 120, 140, 28))
    for y in range(0, h, 40): d.line((0, y, w, y), fill=(70, 120, 140, 28))
    img = Image.alpha_composite(img, grid)
    hud = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(hud)
    cx, cy = w * 0.78, h * 0.5
    for i, rr in enumerate((40, 85, 130, 175, 220, 265)):
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=ORANGE + (150 - i * 18,), width=2)
    for a in range(0, 360, 10):
        x1 = cx + 265 * math.cos(math.radians(a)); y1 = cy + 265 * math.sin(math.radians(a))
        x2 = cx + (250 if a % 30 else 238) * math.cos(math.radians(a)); y2 = cy + (250 if a % 30 else 238) * math.sin(math.radians(a))
        d.line((x1, y1, x2, y2), fill=ORANGE + (170,), width=2)
    d.pieslice((cx - 265, cy - 265, cx + 265, cy + 265), -60, -20, fill=ORANGE + (45,))
    d.line((cx - 290, cy, cx + 290, cy), fill=ORANGE + (90,)); d.line((cx, cy - 290, cx, cy + 290), fill=ORANGE + (90,))
    for _ in range(9):                                     # hedef işaretleri
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(50, 250)
        px, py = cx + rr * math.cos(a), cy + rr * math.sin(a)
        d.rectangle((px - 4, py - 4, px + 4, py + 4), outline=(255, 210, 120, 220), width=2)
    img = Image.alpha_composite(img, _glow(hud, 6))
    ticks = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(ticks)
    for i in range(26):                                     # soldaki veri çizgileri
        y = 30 + i * 9; ln = rnd.randint(60, 340)
        d.line((w * 0.42, y, w * 0.42 + ln, y), fill=(140, 190, 210, rnd.randint(30, 80)), width=2)
    img = Image.alpha_composite(img, ticks)
    for y in range(0, h, 3):                               # tarama çizgileri
        ImageDraw.Draw(img).line((0, y, w, y), fill=(0, 0, 0, 38))
    return _noise(_vignette(img.convert("RGB"), 0.4), seed=seed)


def bg_topo(seed=44):
    w, h = BG_SIZE
    rnd = random.Random(seed)
    img = _vgradient((w, h), (14, 13, 12), (9, 11, 15)).convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    waves = [(rnd.uniform(0.002, 0.006), rnd.uniform(0, 6.28), rnd.uniform(18, 40)) for _ in range(3)]
    for i in range(-6, 26):
        base = i * 16
        pts = []
        for x in range(0, w + 20, 20):
            y = base + sum(a * math.sin(f * x * (1 + i * 0.02) + p) for f, p, a in waves)
            pts.append((x, y))
        hot = i % 5 == 0
        d.line(pts, fill=(ORANGE + (150,)) if hot else (150, 170, 190, 45), width=2 if hot else 1)
    img = Image.alpha_composite(img, _glow(layer, 3))
    marks = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(marks)
    for _ in range(6):                                     # konum işaretleri
        x, y = rnd.uniform(w * 0.4, w * 0.95), rnd.uniform(40, h - 40)
        d.ellipse((x - 9, y - 9, x + 9, y + 9), outline=ORANGE + (230,), width=3)
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=ORANGE + (255,))
    img = Image.alpha_composite(img, _glow(marks, 5))
    return _noise(_vignette(img.convert("RGB"), 0.45), seed=seed)


def bg_smoke(seed=55):
    w, h = BG_SIZE
    rnd = random.Random(seed)
    img = _vgradient((w, h), (16, 14, 14), (6, 6, 8)).convert("RGBA")
    fog = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(fog)
    for _ in range(70):
        x, y, r = rnd.uniform(-100, w), rnd.uniform(-50, h + 50), rnd.uniform(40, 160)
        warm = rnd.random() < 0.35
        col = (255, 120, 40, rnd.randint(18, 40)) if warm else (150, 155, 165, rnd.randint(10, 26))
        d.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=col)
    img = Image.alpha_composite(img, fog.filter(ImageFilter.GaussianBlur(40)))
    stripes = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(stripes)
    for i in range(0, w + h, 46):                           # çapraz uyarı şeritleri (sağ alt köşe)
        if i > w * 0.62:
            d.polygon([(i, h), (i + 22, h), (i + 22 - 70, h - 70), (i - 70, h - 70)], fill=ORANGE + (70,))
    img = Image.alpha_composite(img, stripes)
    embers = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(embers)
    for _ in range(160):                                   # kıvılcımlar
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        d.ellipse((x, y, x + 2, y + 2), fill=(255, rnd.randint(140, 200), 80, rnd.randint(80, 200)))
    img = Image.alpha_composite(img, _glow(embers, 3))
    return _noise(_vignette(img.convert("RGB"), 0.4), seed=seed)


BACKGROUNDS = {"skyline": bg_skyline, "hexgrid": bg_hexgrid, "radar": bg_radar, "topo": bg_topo, "smoke": bg_smoke}


def ensure_backgrounds(folder):
    """Varsayılan arka planları (yoksa) üretir. Klasördeki tüm görsellerin yollarını döndürür."""
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    stamp = folder / f".default_v{ART_VERSION}"
    for name, fn in BACKGROUNDS.items():
        p = folder / f"default_{name}.png"
        if not p.exists() or not stamp.exists():
            fn().save(p, optimize=True)
    stamp.touch()
    return list_images(folder)


def list_images(folder):
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT)


# ───────────── build amblemleri ─────────────
ROLES = {  # rol: (anahtar kelimeler, renk)
    "pulse":     (("heart", "kalp", "pulse"), "#ef4444"),
    "tank":      (("tank", "hybrid", "shield", "kalkan", "foundry", "armor", "zırh"), "#3b82f6"),
    "skill":     (("skill", "yetenek", "tech", "hive", "turret", "drone"), "#14b8a6"),
    "close":     (("close", "shotgun", "fury", "hunter", "yakın"), "#f59e0b"),
    "precision": (("marksman", "sniper", "rifle", "mmr", "headshot", "keskin"), "#22c55e"),
    "dps":       (("striker", "dps", "ar", "damage", "hasar", "crit"), "#ff6d10"),
}


def build_role(name, sets=()):
    text = " ".join([name] + list(sets)).lower()
    words = set(re.findall(r"[a-zçğıöşü']+", text))
    for role, (keys, _c) in ROLES.items():
        if any((k in words) if len(k) <= 3 else (k in text) for k in keys):
            return role
    return "default"


def _safe(name):
    return re.sub(r'[<>:"/\\|?*]+', "_", name).strip() or "build"


def _initials(name):
    words = [w for w in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]+", name) if w.lower() not in ("the", "and", "pve", "pvp")]
    return "".join(w[0] for w in words[:2]).upper() or "?"


def emblem(name, sets=(), user_folder=None, size=512):
    """Build için amblem (RGBA). Kullanıcı görseli varsa onu döndürür."""
    if user_folder:
        for ext in IMG_EXT:
            p = Path(user_folder) / f"{_safe(name)}{ext}"
            if p.exists():
                try:
                    return Image.open(p).convert("RGBA")
                except Exception:
                    pass
    role = build_role(name, sets)
    col = _rgb(ROLES.get(role, ((), "#ff6d10"))[1])
    S = size * 2                                     # 2x çizip küçült: yumuşak kenarlar
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    c = S / 2
    hexpts = lambda r, rot=30: [(c + r * math.cos(math.radians(60 * k + rot)), c + r * math.sin(math.radians(60 * k + rot))) for k in range(6)]
    d.polygon(hexpts(S * 0.48), fill=col + (255,))
    d.polygon(hexpts(S * 0.44), fill=(16, 18, 24, 255))
    d.polygon(hexpts(S * 0.40), outline=col + (120,), width=int(S * 0.006))
    g = S * 0.20                                     # simge yarıçapı
    lw = int(S * 0.022)
    white = (240, 242, 246, 255)
    cy = c - S * 0.04
    if role == "dps":                                # nişangah + rütbe şeritleri
        d.ellipse((c - g, cy - g, c + g, cy + g), outline=white, width=lw)
        for a in range(4):
            x, y = math.cos(math.radians(90 * a)), math.sin(math.radians(90 * a))
            d.line((c + x * g * 0.55, cy + y * g * 0.55, c + x * g * 1.35, cy + y * g * 1.35), fill=col + (255,), width=lw)
        d.ellipse((c - lw, cy - lw, c + lw, cy + lw), fill=col + (255,))
    elif role == "pulse":                            # nabız (EKG) çizgisi
        pts = [(-1.3, 0), (-0.55, 0), (-0.35, -0.25), (-0.15, 0.2), (0.05, -0.95), (0.3, 0.75), (0.5, -0.1), (0.7, 0), (1.3, 0)]
        d.line([(c + x * g, cy + y * g) for x, y in pts], fill=col + (255,), width=int(lw * 1.3), joint="curve")
        d.ellipse((c - g * 1.25, cy - g * 1.25, c + g * 1.25, cy + g * 1.25), outline=white, width=int(lw * 0.6))
    elif role == "tank":                             # kalkan + çift köşeli şerit
        sh = [(c - g, cy - g * 1.05), (c + g, cy - g * 1.05), (c + g, cy + g * 0.15), (c, cy + g * 1.25), (c - g, cy + g * 0.15)]
        d.polygon(sh, outline=white, width=lw)
        for k in (0, 1):
            y0 = cy - g * 0.35 + k * g * 0.5
            d.line([(c - g * 0.55, y0), (c, y0 + g * 0.35), (c + g * 0.55, y0)], fill=col + (255,), width=lw, joint="curve")
    elif role == "skill":                            # dişli + devre
        teeth = 10
        pts = []
        for k in range(teeth * 2):
            r = g * (1.15 if k % 2 == 0 else 0.92)
            a = math.radians(k * 180 / teeth)
            pts.append((c + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, outline=white, width=lw)
        d.ellipse((c - g * 0.45, cy - g * 0.45, c + g * 0.45, cy + g * 0.45), outline=col + (255,), width=lw)
        d.ellipse((c - lw, cy - lw, c + lw, cy + lw), fill=col + (255,))
    elif role == "close":                            # saçma dağılımı / patlama
        for k in range(12):
            a = math.radians(k * 30)
            r1, r2 = g * 0.35, g * (1.3 if k % 2 == 0 else 0.95)
            d.line((c + r1 * math.cos(a), cy + r1 * math.sin(a), c + r2 * math.cos(a), cy + r2 * math.sin(a)),
                   fill=(col if k % 2 else white[:3]) + (255,), width=lw)
        d.ellipse((c - g * 0.22, cy - g * 0.22, c + g * 0.22, cy + g * 0.22), fill=white)
    elif role == "precision":                        # dürbün retikülü
        d.ellipse((c - g * 1.15, cy - g * 1.15, c + g * 1.15, cy + g * 1.15), outline=white, width=lw)
        d.line((c - g * 1.15, cy, c + g * 1.15, cy), fill=white, width=int(lw * 0.6))
        d.line((c, cy - g * 1.15, c, cy + g * 1.15), fill=white, width=int(lw * 0.6))
        for k in (-2, -1, 1, 2):
            d.ellipse((c + k * g * 0.35 - lw * 0.7, cy - lw * 0.7, c + k * g * 0.35 + lw * 0.7, cy + lw * 0.7), fill=col + (255,))
        d.polygon([(c, cy + lw * 2), (c - lw * 1.6, cy + lw * 5), (c + lw * 1.6, cy + lw * 5)], fill=col + (255,))
    else:                                            # üç köşeli rütbe şeridi
        for k in range(3):
            y0 = cy - g * 0.7 + k * g * 0.6
            d.line([(c - g, y0), (c, y0 + g * 0.55), (c + g, y0)], fill=(col if k == 0 else white[:3]) + (255,), width=lw, joint="curve")
    # alt bant: baş harfler
    ini = _initials(name)
    bw, bh = S * 0.30, S * 0.085
    d.rectangle((c - bw / 2, c + S * 0.24, c + bw / 2, c + S * 0.24 + bh), fill=col + (255,))
    try:
        from PIL import ImageFont
        font = None
        for fname in ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
            try:
                font = ImageFont.truetype(fname, int(bh * 0.72)); break
            except Exception:
                continue
        font = font or ImageFont.load_default()
        tb = d.textbbox((0, 0), ini, font=font)
        d.text((c - (tb[2] - tb[0]) / 2 - tb[0], c + S * 0.24 + (bh - (tb[3] - tb[1])) / 2 - tb[1]), ini, font=font, fill=(255, 255, 255, 255))
    except Exception:
        pass
    shadow = img.split()[3].filter(ImageFilter.GaussianBlur(S * 0.02))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste((0, 0, 0, 160), (0, int(S * 0.01)), shadow)
    out = Image.alpha_composite(out, img)
    return out.resize((size, size), Image.LANCZOS)


def role_color(name, sets=()):
    return ROLES.get(build_role(name, sets), ((), "#ff6d10"))[1]


# ───────────── bayraklar ─────────────
def _star(d, cx, cy, r, rot, fill):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.382
        a = math.radians(rot + k * 36)
        pts.append((cx + rr * math.sin(a), cy - rr * math.cos(a)))
    d.polygon(pts, fill=fill)


def _bands(d, w, h, cols, vertical=False, weights=None):
    weights = weights or [1] * len(cols)
    tot = sum(weights); pos = 0
    for c, wt in zip(cols, weights):
        a, b = pos / tot, (pos + wt) / tot; pos += wt
        if vertical:
            d.rectangle((a * w, 0, b * w, h), fill=c)
        else:
            d.rectangle((0, a * h, w, b * h), fill=c)


def flag(code, user_folder=None, height=400):
    """Dil koduna göre bayrak (RGBA). Bilinmeyen kodda None döner."""
    code = (code or "").lower()
    if user_folder:
        for ext in IMG_EXT:
            p = Path(user_folder) / f"{code}{ext}"
            if p.exists():
                try:
                    return Image.open(p).convert("RGBA")
                except Exception:
                    pass
    H = height * 2
    W = int(H * 1.5)
    img = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(img)
    base = code.split("-")[0]
    if base == "tr":
        d.rectangle((0, 0, W, H), fill="#E30A17")
        cx = H * 0.5
        d.ellipse((cx - H * 0.25, H * 0.25, cx + H * 0.25, H * 0.75), fill="white")
        cx2 = cx + H * 0.0625
        d.ellipse((cx2 - H * 0.2, H * 0.3, cx2 + H * 0.2, H * 0.7), fill="#E30A17")
        _star(d, H * 0.8458, H * 0.5, H * 0.125, -90, "white")
    elif base == "de":
        _bands(d, W, H, ["#000000", "#DD0000", "#FFCE00"])
    elif base == "fr":
        _bands(d, W, H, ["#002395", "#FFFFFF", "#ED2939"], vertical=True)
    elif base == "it":
        _bands(d, W, H, ["#009246", "#FFFFFF", "#CE2B37"], vertical=True)
    elif base == "es":
        _bands(d, W, H, ["#AA151B", "#F1BF00", "#AA151B"], weights=[1, 2, 1])
    elif base == "ru":
        _bands(d, W, H, ["#FFFFFF", "#0039A6", "#D52B1E"])
    elif base == "pl":
        _bands(d, W, H, ["#FFFFFF", "#DC143C"])
    elif base == "nl":
        _bands(d, W, H, ["#AE1C28", "#FFFFFF", "#21468B"])
    elif base == "pt":
        _bands(d, W, H, ["#006600", "#FF0000"], vertical=True, weights=[2, 3])
        cx, r = W * 0.4, H * 0.22
        d.ellipse((cx - r, H / 2 - r, cx + r, H / 2 + r), outline="#FFE500", width=int(H * 0.035))
        d.rectangle((cx - r * 0.45, H / 2 - r * 0.55, cx + r * 0.45, H / 2 + r * 0.45), fill="white", outline="#FF0000", width=int(H * 0.02))
    elif base == "en":                             # Birleşik Krallık
        W = H * 2
        img = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(img)
        d.rectangle((0, 0, W, H), fill="#012169")
        t = H / 30
        for a, b in (((0, 0), (W, H)), ((0, H), (W, 0))):
            d.line((a, b), fill="white", width=int(6 * t))
        d.line(((0, 0), (W, H)), fill="#C8102E", width=int(2 * t))
        d.line(((0, H), (W, 0)), fill="#C8102E", width=int(2 * t))
        d.rectangle((W / 2 - 5 * t, 0, W / 2 + 5 * t, H), fill="white")
        d.rectangle((0, H / 2 - 5 * t, W, H / 2 + 5 * t), fill="white")
        d.rectangle((W / 2 - 3 * t, 0, W / 2 + 3 * t, H), fill="#C8102E")
        d.rectangle((0, H / 2 - 3 * t, W, H / 2 + 3 * t), fill="#C8102E")
    else:
        return None
    # hafif dalga gölgesi + kenar
    shade = Image.new("L", img.size)
    sw, sh = img.size
    shade.putdata([int(128 + 40 * math.sin(x / sw * math.pi * 2.2)) for y in range(1) for x in range(sw)] * 1)
    shade = shade.crop((0, 0, sw, 1)).resize((sw, sh))
    img = Image.composite(img, Image.new("RGBA", img.size, (0, 0, 0, 255)), shade.point(lambda v: min(255, 200 + v // 5)))
    ImageDraw.Draw(img).rectangle((0, 0, sw - 1, sh - 1), outline=(0, 0, 0, 90), width=4)
    return img.resize((sw // 2, sh // 2), Image.LANCZOS)


# ───────────── dönen arka planlı başlık bandı / rotating header banner ─────────────
import threading
import tkinter as tk

from PIL import ImageOps, ImageTk


class Banner:
    """Üst başlık bandı: arka planlar belirli aralıkla yumuşak geçişle değişir;
    flash() ile bir amblem/bayrak birkaç saniye gösterilip temaya geri dönülür."""

    def __init__(self, parent, pal, bg_folder, interval_s=15, height=118, title="", subtitle=""):
        self.pal, self.h, self.interval = pal, height, max(0, int(interval_s or 0))
        self.folder = Path(bg_folder)
        self.cv = tk.Canvas(parent, height=height, highlightthickness=0, bd=0, bg="#0f1116")
        self.cv.pack(fill="x")
        self.title, self.subtitle = title, subtitle
        self.paths, self.idx, self._raw = [], 0, {}
        self.base = None            # şu anki arka plan (boyutlandırılmış, RGB)
        self.frame = None           # ekrandaki kare
        self.photo = None
        self.flash_state = None     # (rgba, başlık, alt başlık, renk)
        self.chips, self.toast_text = [], ""
        self._jobs = {}
        self._size = (0, 0)
        self._grad_cache = {}
        self._vframe, self.video_on = None, False
        self.transparent = False        # tüm pencere arka planı (ajan saati) açıkken bant şeffaf: yalnızca yazılar
        self.alive = True
        self.cv.bind("<Configure>", self._on_resize)
        self._ready = False
        threading.Thread(target=self._prepare, daemon=True).start()
        self._poll_ready()

    # --- hazırlık ---
    def _prepare(self):
        try:
            self._found = ensure_backgrounds(self.folder)
        except Exception:
            self._found = list_images(self.folder)
        self._ready = True

    def _poll_ready(self):
        if not self.alive: return
        if not self._ready:
            self._after("ready", 250, self._poll_ready); return
        self.paths = self._found
        self.idx = 0
        self.base = self._fitted(self._current_path())
        self._render(fade=True)
        self._schedule_rotate()

    def _after(self, key, ms, fn):
        if not self.alive: return
        old = self._jobs.pop(key, None)
        if old:
            try: self.cv.after_cancel(old)
            except Exception: pass
        self._jobs[key] = self.cv.after(ms, fn)

    def destroy(self):
        self.alive = False
        for j in self._jobs.values():
            try: self.cv.after_cancel(j)
            except Exception: pass
        self._jobs.clear()
        self.cv.destroy()

    # --- görseller ---
    def _current_path(self):
        return self.paths[self.idx % len(self.paths)] if self.paths else None

    def _fitted(self, path):
        w, h = self._wh()
        if path is None:
            return _vgradient((w, h), (20, 22, 28), (10, 11, 15))
        try:
            raw = self._raw.get(path)
            if raw is None:
                raw = Image.open(path).convert("RGB")
                if len(self._raw) > 12: self._raw.clear()
                self._raw[path] = raw
            return ImageOps.fit(raw, (w, h), Image.LANCZOS, centering=(0.5, 0.5))
        except Exception:
            return _vgradient((w, h), (20, 22, 28), (10, 11, 15))

    def _wh(self):
        return max(200, self.cv.winfo_width()), self.h

    def _compose(self, base):
        w, h = base.size
        img = base.convert("RGBA")
        # okunabilirlik için soldan koyu geçiş
        grad = self._grad_cache.get((w, h))
        if grad is None:
            grad = Image.linear_gradient("L").rotate(-90).resize((w, h))  # solda 255 (koyu), sağda 0
            grad = grad.point(lambda v: int(v * 0.85) if v > 90 else int(v * 0.5))
            self._grad_cache = {(w, h): grad}
        img = Image.composite(Image.new("RGBA", (w, h), (8, 9, 12, 255)), img, grad)
        if self.flash_state:
            rgba, _t, _s, col = self.flash_state
            dark = Image.new("RGBA", (w, h), (8, 9, 12, 255))
            img = Image.blend(img, dark, 0.55)
            tint = Image.new("RGBA", (w, h), _rgb(col) + (255,))
            img = Image.blend(img, tint, 0.12)
            eh = h - 18
            ew = int(rgba.width * eh / rgba.height)
            if ew > w * 0.32:                       # bayrak gibi geniş görseller
                ew = int(w * 0.32); eh = int(rgba.height * ew / rgba.width)
            em = rgba.resize((ew, eh), Image.LANCZOS)
            img.alpha_composite(em, (int(w * 0.47) - ew // 2, (h - eh) // 2))
        # alt kenarda ince turuncu çizgi
        ImageDraw.Draw(img).rectangle((0, h - 3, w, h), fill=_rgb(self.pal.get("accent", "#ff6d10")) + (255,))
        return img.convert("RGB")

    # --- çizim ---
    def _render(self, fade=False):
        if not self.alive or self.base is None: return
        new = self._compose(self.base)
        if fade and self.frame is not None and self.frame.size == new.size:
            self._fade(self.frame, new, 0)
        else:
            self._show(new)

    def _fade(self, a, b, step, steps=7):
        if not self.alive: return
        if step >= steps:
            self._show(b); return
        self._show(Image.blend(a, b, (step + 1) / steps), keep=False)
        self._after("fade", 45, lambda: self._fade(a, b, step + 1, steps))

    def set_transparent(self, on):
        self.transparent = bool(on)
        if self.alive:
            if on:
                self.cv.config(bg=self.pal.get("bg", "#0f1116")); self.cv.delete("all"); self._draw_overlay()
            else:
                self._resized()

    def _show(self, img, keep=True):
        if self.transparent:
            self.cv.delete("all"); self._draw_overlay(); return
        if keep: self.frame = img
        self.photo = ImageTk.PhotoImage(img)
        self.cv.delete("all")
        self.cv.create_image(0, 0, anchor="nw", image=self.photo)
        self._draw_overlay()

    def _draw_overlay(self):
        cv, w, h = self.cv, self._wh()[0], self.h
        fs = self.pal
        if h >= 90:
            cv.create_text(22, 40, anchor="w", text=self.title, fill=fs.get("accent", "#ff6d10"),
                           font=("Segoe UI Semibold", 21))
            cv.create_text(24, 72, anchor="w", text=self.subtitle, fill="#c9ced8", font=("Segoe UI", 10))
        else:                                                   # kompakt (küçük ekran): tek satır
            cv.create_text(14, h / 2, anchor="w", text=f"{self.title}  {self.subtitle}", fill=fs.get("accent", "#ff6d10"),
                           font=("Segoe UI Semibold", max(9, int(h / 3.2))))
        if self.flash_state:
            _rgba, t1, t2, col = self.flash_state
            x = int(w * 0.47) + int(min(h - 18, w * 0.32) * 0.75) + 18
            cv.create_text(x, h / 2 - 12, anchor="w", text=t1, fill="#ffffff", font=("Segoe UI Semibold", 17))
            cv.create_text(x, h / 2 + 16, anchor="w", text=t2, fill=col, font=("Segoe UI Semibold", 10))
        # rozetler (sağ üst)
        x = w - 16
        for i, chip in reversed(list(enumerate(self.chips))):
            text, kind = chip[0], chip[1]
            cb = chip[2] if len(chip) > 2 else None             # tıklanabilir rozet (ör. "PC senkron")
            bg = {"on": fs.get("success", "#22c55e"), "btn": fs.get("accent", "#ff6d10")}.get(kind, "#1d2129")
            fg = "#ffffff" if kind in ("on", "btn") else "#c9ced8"
            tag = f"chip{i}"
            tid = cv.create_text(0, 0, text=text, font=("Segoe UI Semibold", 9), fill=fg, anchor="e", tags=(tag,))
            bx = cv.bbox(tid); tw = bx[2] - bx[0]
            cv.coords(tid, x - 10, 26)
            cv.create_rectangle(x - tw - 20, 14, x, 38, fill=bg, outline="", tags=(tag,))
            cv.tag_raise(tid)
            if cb:
                cv.tag_bind(tag, "<Button-1>", lambda e, cb=cb: cb())
                cv.tag_bind(tag, "<Enter>", lambda e: cv.config(cursor="hand2"))
                cv.tag_bind(tag, "<Leave>", lambda e: cv.config(cursor=""))
            x -= tw + 28
        if self.toast_text:
            tid = cv.create_text(w - 26, h - 26, text=self.toast_text, anchor="e", fill="#ffffff",
                                 font=("Segoe UI Semibold", 10))
            bx = cv.bbox(tid)
            cv.create_rectangle(bx[0] - 12, bx[1] - 6, bx[2] + 12, bx[3] + 6, fill=fs.get("accent", "#ff6d10"), outline="")
            cv.tag_raise(tid)

    def _redraw_overlay_only(self):
        if self.transparent:
            self.cv.delete("all"); self._draw_overlay(); return
        if self.frame is not None:
            self._show(self.frame)

    def _on_resize(self, _e=None):
        if self._wh() == self._size: return
        self._size = self._wh()
        self._after("resize", 120, self._resized)

    def _resized(self):
        self.base = self._fitted(self._current_path())
        self.frame = None
        self._render()

    # --- arka plan videosu (fx.VideoFX kareleri gönderir) ---
    def push_video(self, img):
        """Video iş parçacığından çağrılır: yalnızca son kare saklanır."""
        self._vframe = img

    def video_size(self):
        return self._wh()

    def start_video(self):
        self.video_on = True
        self._video_tick()

    def stop_video(self):
        self.video_on = False
        self._vframe = None
        if self.alive: self._resized()

    def _video_tick(self):
        if not self.alive or not self.video_on: return
        f, self._vframe = self._vframe, None
        if f is not None and f.size == self._wh() and self.flash_state is None:
            self._show(self._compose(f), keep=False)
        self._after("video", 40, self._video_tick)

    # --- dönüş ---
    def set_interval(self, seconds):
        self.interval = max(0, int(seconds or 0))
        self._schedule_rotate()

    def _schedule_rotate(self):
        old = self._jobs.pop("rotate", None)
        if old:
            try: self.cv.after_cancel(old)
            except Exception: pass
        if self.interval > 0 and len(self.paths) > 1:
            self._after("rotate", self.interval * 1000, self.next)

    def next(self):
        if self.flash_state is None and self.paths and not self.video_on:
            self.idx = (self.idx + 1) % len(self.paths)
            self.base = self._fitted(self._current_path())
            self._render(fade=True)
        self._schedule_rotate()

    # --- geçici gösterim ---
    def flash(self, rgba, title, subtitle="", color="#ff6d10", seconds=5):
        if rgba is None or not self.alive: return
        self.flash_state = (rgba, title, subtitle, color)
        self._render(fade=True)
        self._after("unflash", int(seconds * 1000), self.unflash)

    def unflash(self):
        if self.flash_state is None: return
        self.flash_state = None
        self._render(fade=True)

    def set_chips(self, chips):
        self.chips = list(chips)
        self._redraw_overlay_only()

    def toast(self, text, seconds=2.5):
        self.toast_text = text
        self._redraw_overlay_only()
        self._after("toast", int(seconds * 1000), self._clear_toast)

    def _clear_toast(self):
        self.toast_text = ""
        self._redraw_overlay_only()
