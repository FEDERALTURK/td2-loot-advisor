"""TD2 Loot Advisor simgesi — özgün tasarım (oyunun/Ubisoft'un logosu değildir).

    python scripts/make_icon.py build/td2.ico            # .ico (16-256 px) + aynı adla .png
    python scripts/make_icon.py preview.png --preview     # üç tasarımın karşılaştırması
Tasarım seçimi: DESIGN değişkeni ("scan", "shield", "card").
"""
import math
import sys
from PIL import Image, ImageDraw, ImageFilter

DESIGN = "watch_real"
ORANGE = (255, 109, 16, 255)
ORANGE_D = (204, 74, 0, 255)
BG_TOP, BG_BOT = (30, 34, 41), (12, 13, 16)
FG = (232, 230, 227, 255)
SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]


def _bg(s):
    """Yuvarlak köşeli koyu zemin, dikey gradyan, ince kenar."""
    grad = Image.new("RGBA", (s, s))
    gd = ImageDraw.Draw(grad)
    for y in range(s):
        k = y / (s - 1)
        gd.line([(0, y), (s, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip(BG_TOP, BG_BOT)) + (255,))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.2), fill=255)
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    im.paste(grad, (0, 0), mask)
    ImageDraw.Draw(im).rounded_rectangle((1, 1, s - 2, s - 2), radius=int(s * 0.2), outline=(255, 255, 255, 28),
                                         width=max(1, s // 128))
    return im


def _glow(im, shape_fn, s, radius):
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    shape_fn(ImageDraw.Draw(g), (255, 109, 16, 150))
    g = g.filter(ImageFilter.GaussianBlur(radius))
    return Image.alpha_composite(im, g)


def design_scan(s):
    """Tarama elması: turuncu elmas + nişangâh."""
    im = _bg(s); c, r = s / 2, s * 0.34
    pts = [(c, c - r), (c + r, c), (c, c + r), (c - r, c)]
    im = _glow(im, lambda d, f: d.polygon(pts, fill=f), s, s * 0.05)
    d = ImageDraw.Draw(im)
    d.polygon(pts, fill=ORANGE)
    r2 = r * 0.55
    d.polygon([(c, c - r2), (c + r2, c), (c, c + r2), (c - r2, c)], fill=BG_BOT + (255,))
    w = max(2, int(s * 0.035)); g = r2 * 0.35
    for a, b in (((c, c - r2 * 0.95), (c, c - g)), ((c, c + g), (c, c + r2 * 0.95)),
                 ((c - r2 * 0.95, c), (c - g, c)), ((c + g, c), (c + r2 * 0.95, c))):
        d.line([a, b], fill=FG, width=w)
    d.ellipse((c - w, c - w, c + w, c + w), fill=ORANGE)
    return im


def design_shield(s):
    """Loot kalkanı: kalkan + yükselen şerit (sakla / yükselt)."""
    im = _bg(s); c = s / 2
    top, bot, half = s * 0.17, s * 0.85, s * 0.31
    pts = [(c - half, top + s * 0.05), (c, top), (c + half, top + s * 0.05), (c + half, s * 0.5),
           (c, bot), (c - half, s * 0.5)]
    im = _glow(im, lambda d, f: d.polygon(pts, fill=f), s, s * 0.05)
    d = ImageDraw.Draw(im)
    d.polygon(pts, fill=ORANGE)
    inset = s * 0.055
    ip = [(c - half + inset, top + s * 0.08), (c, top + inset), (c + half - inset, top + s * 0.08),
          (c + half - inset, s * 0.49), (c, bot - inset * 1.6), (c - half + inset, s * 0.49)]
    d.polygon(ip, fill=BG_BOT + (255,))
    w = max(2, int(s * 0.06))
    for k, col in ((0.0, FG), (0.15, ORANGE)):                # iki yükselen şerit, kalkanın içinde
        y = s * (0.46 + k)
        d.line([(c - s * 0.13, y), (c, y - s * 0.11), (c + s * 0.13, y)], fill=col, width=w, joint="curve")
    return im


def design_card(s):
    """Eşya kartı + tarama köşeleri: programın yaptığı iş (kartı oku, değerlendir)."""
    im = _bg(s)
    x0, y0, x1, y1 = s * 0.27, s * 0.2, s * 0.73, s * 0.8
    card = lambda d, f: d.rounded_rectangle((x0, y0, x1, y1), radius=s * 0.05, fill=f)
    im = _glow(im, card, s, s * 0.04)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0, y0, x1, y1), radius=s * 0.05, fill=(42, 46, 54, 255))
    d.rounded_rectangle((x0, y0, x1, y0 + (y1 - y0) * 0.26), radius=s * 0.05, fill=ORANGE)
    d.rectangle((x0, y0 + (y1 - y0) * 0.16, x1, y0 + (y1 - y0) * 0.26), fill=ORANGE)
    bw = max(2, int(s * 0.045))
    for i, frac in enumerate((0.85, 0.6, 0.95)):
        y = y0 + (y1 - y0) * (0.42 + i * 0.17)
        d.rounded_rectangle((x0 + s * 0.05, y, x1 - s * 0.05, y + bw), radius=bw / 2, fill=(70, 75, 85, 255))
        d.rounded_rectangle((x0 + s * 0.05, y, x0 + s * 0.05 + (x1 - x0 - s * 0.1) * frac, y + bw), radius=bw / 2,
                            fill=FG if i != 1 else ORANGE_D)
    m, L, w = s * 0.12, s * 0.15, max(2, int(s * 0.045))     # tarama köşeleri
    for (cx, cy, dx, dy) in ((m, m, 1, 1), (s - m, m, -1, 1), (m, s - m, 1, -1), (s - m, s - m, -1, -1)):
        d.line([(cx, cy + dy * L), (cx, cy), (cx + dx * L, cy)], fill=ORANGE, width=w, joint="curve")
    return im


DESIGNS = {"scan": design_scan, "shield": design_shield, "card": design_card}


def _grime(im, s, seed=7, amount=0.10):
    """Hafif aşınmış metal dokusu (oyunun taktik havası için)."""
    import random
    rnd = random.Random(seed)
    tex = Image.new("L", (s // 8, s // 8))
    tex.putdata([int(128 + rnd.gauss(0, 38)) for _ in range((s // 8) ** 2)])
    tex = tex.resize((s, s), Image.BICUBIC).filter(ImageFilter.GaussianBlur(s / 220))
    a = im.split()[3]
    dark = Image.new("RGBA", (s, s), (0, 0, 0, 0)); dark.putalpha(tex.point(lambda v: int(max(0, 128 - v) * amount * 4)))
    lite = Image.new("RGBA", (s, s), (255, 255, 255, 0)); lite.putalpha(tex.point(lambda v: int(max(0, v - 128) * amount * 2)))
    out = Image.alpha_composite(Image.alpha_composite(im, dark), lite)
    out.putalpha(a)
    return out


def design_hud(s):
    """Ajan HUD'u havasında: bölümlü turuncu halka + ortada loot elması (özgün; oyunun logosu değildir)."""
    im = _bg(s); c = s / 2
    R, w = s * 0.36, s * 0.05
    ring = lambda d, f: [d.arc((c - R, c - R, c + R, c + R), a0, a0 + 100, fill=f, width=int(w)) for a0 in (-80, 40, 160)]
    im = _glow(im, ring, s, s * 0.035)
    d = ImageDraw.Draw(im)
    # bölümlü halka: 3 yay, aralarda boşluk
    for a0 in (-80, 40, 160):
        d.arc((c - R, c - R, c + R, c + R), a0, a0 + 100, fill=ORANGE, width=int(w))
    # dış ince tik halkası
    R2 = R + s * 0.07
    for k in range(48):
        ang = math.radians(k * 7.5)
        L = s * (0.03 if k % 4 == 0 else 0.015)
        x1, y1 = c + math.cos(ang) * R2, c + math.sin(ang) * R2
        x2, y2 = c + math.cos(ang) * (R2 - L), c + math.sin(ang) * (R2 - L)
        d.line([(x1, y1), (x2, y2)], fill=(232, 230, 227, 170 if k % 4 == 0 else 90), width=max(1, int(s * 0.006)))
    # ortada loot elması + nokta
    r = s * 0.15
    d.polygon([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], fill=FG)
    r2 = r * 0.45
    d.polygon([(c, c - r2), (c + r2, c), (c, c + r2), (c - r2, c)], fill=ORANGE)
    return _grime(im, s, amount=0.09)


def design_badge(s):
    """Taktik rozet: stencil köşeli kalkan, turuncu şerit ve elmas; aşınmış doku."""
    im = _bg(s); c = s / 2
    t, b, hw = s * 0.15, s * 0.86, s * 0.32
    cut = s * 0.07
    pts = [(c - hw + cut, t), (c + hw - cut, t), (c + hw, t + cut), (c + hw, s * 0.56), (c, b), (c - hw, s * 0.56), (c - hw, t + cut)]
    im = _glow(im, lambda d, f: d.polygon(pts, fill=f), s, s * 0.04)
    d = ImageDraw.Draw(im)
    d.polygon(pts, fill=(48, 52, 60, 255))
    d.line(pts + [pts[0]], fill=ORANGE, width=int(s * 0.035), joint="curve")
    # üst turuncu şerit (stencil kesikli)
    y0, y1 = s * 0.27, s * 0.35
    for i in range(5):
        x = c - hw * 0.72 + i * hw * 0.3
        d.rectangle((x, y0, x + hw * 0.24, y1), fill=ORANGE)
    # elmas
    r = s * 0.13; cy = s * 0.56
    d.polygon([(c, cy - r), (c + r, cy), (c, cy + r), (c - r, cy)], fill=FG)
    r2 = r * 0.42
    d.polygon([(c, cy - r2), (c + r2, cy), (c, cy + r2), (c - r2, cy)], fill=ORANGE)
    return _grime(im, s, seed=11, amount=0.11)


DESIGNS.update({"hud": design_hud, "badge": design_badge})


def design_watch(s):
    """Özgün taktik kol saati (dijital, köşeli kasa): ekranda loot elması ve rulo çubukları.
    Oyunun SHD saati değildir; kasa, ekran ve düzen bu projeye özgüdür."""
    im = _bg(s); c = s / 2
    d = ImageDraw.Draw(im)
    strap = (58, 62, 70, 255); strap_d = (40, 43, 50, 255)
    # kayış (üst ve alt), dikiş çizgileri
    for y0, y1 in ((-s * 0.02, s * 0.3), (s * 0.7, s * 1.02)):
        d.rounded_rectangle((c - s * 0.17, y0, c + s * 0.17, y1), radius=s * 0.04, fill=strap)
        for yy in range(int(y0 + s * 0.05), int(y1 - s * 0.02), max(2, int(s * 0.045))):
            d.line([(c - s * 0.12, yy), (c - s * 0.12, yy + s * 0.02)], fill=strap_d, width=max(1, int(s * 0.008)))
            d.line([(c + s * 0.12, yy), (c + s * 0.12, yy + s * 0.02)], fill=strap_d, width=max(1, int(s * 0.008)))
    # kasa (köşeleri kesik sekizgen)
    hw, hh, cut = s * 0.29, s * 0.27, s * 0.08
    case = [(c - hw + cut, c - hh), (c + hw - cut, c - hh), (c + hw, c - hh + cut), (c + hw, c + hh - cut),
            (c + hw - cut, c + hh), (c - hw + cut, c + hh), (c - hw, c + hh - cut), (c - hw, c - hh + cut)]
    im = _glow(im, lambda dd, f: dd.polygon(case, fill=(255, 109, 16, 60)), s, s * 0.04)
    d = ImageDraw.Draw(im)
    d.polygon(case, fill=(70, 75, 85, 255))
    d.line(case + [case[0]], fill=(110, 116, 128, 255), width=max(1, int(s * 0.012)))
    # yan düğmeler (turuncu)
    for yy in (c - s * 0.12, c + s * 0.12):
        d.rounded_rectangle((c + hw - s * 0.005, yy - s * 0.03, c + hw + s * 0.035, yy + s * 0.03), radius=s * 0.01, fill=ORANGE)
        d.rounded_rectangle((c - hw - s * 0.035, yy - s * 0.03, c - hw + s * 0.005, yy + s * 0.03), radius=s * 0.01, fill=ORANGE_D)
    # ekran
    sx, sy = s * 0.21, s * 0.19
    d.rounded_rectangle((c - sx, c - sy, c + sx, c + sy), radius=s * 0.035, fill=(10, 12, 15, 255))
    # ekranda loot elması (sol) ve rulo çubukları (sağ)
    ex, r = c - s * 0.09, s * 0.09
    d.polygon([(ex, c - r), (ex + r, c), (ex, c + r), (ex - r, c)], fill=ORANGE)
    r2 = r * 0.42
    d.polygon([(ex, c - r2), (ex + r2, c), (ex, c + r2), (ex - r2, c)], fill=(10, 12, 15, 255))
    bw = max(2, int(s * 0.03))
    for i, frac in enumerate((1.0, 0.7, 0.45)):
        y = c - s * 0.09 + i * s * 0.075
        d.rounded_rectangle((c + s * 0.03, y, c + s * 0.03 + s * 0.15 * frac, y + bw), radius=bw / 2,
                            fill=FG if i == 0 else (150, 155, 165, 255))
    return _grime(im, s, seed=5, amount=0.07)


DESIGNS["watch"] = design_watch


def _lin(size, c0, c1, horizontal=False):
    w, h = size
    g = Image.new("RGBA", size)
    gd = ImageDraw.Draw(g)
    n = w if horizontal else h
    for i in range(n):
        k = i / max(1, n - 1)
        col = tuple(int(a + (b - a) * k) for a, b in zip(c0, c1))
        if horizontal: gd.line([(i, 0), (i, h)], fill=col)
        else: gd.line([(0, i), (w, i)], fill=col)
    return g


def _mask_poly(s, pts):
    m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).polygon(pts, fill=255); return m


def _mask_rrect(s, box, r):
    m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle(box, radius=r, fill=255); return m


def _paint(im, mask, layer):
    out = im.copy(); out.paste(layer, (0, 0), mask); return out


def _noise(s, sigma, seed, scale=4, blur=0.6):
    import random
    rnd = random.Random(seed); n = max(8, s // scale)
    t = Image.new("L", (n, n)); t.putdata([max(0, min(255, int(128 + rnd.gauss(0, sigma)))) for _ in range(n * n)])
    return t.resize((s, s), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))


def design_watch_real(s):
    """Gerçekçi özgün taktik saat: fırçalanmış metal, kauçuk kayış, cam yansıması, gölge (oyunun saati değildir)."""
    c = s / 2
    im = _bg(s)
    # --- yere düşen gölge
    hw, hh, cut = s * 0.30, s * 0.28, s * 0.085
    case = [(c - hw + cut, c - hh), (c + hw - cut, c - hh), (c + hw, c - hh + cut), (c + hw, c + hh - cut),
            (c + hw - cut, c + hh), (c - hw + cut, c + hh), (c - hw, c + hh - cut), (c - hw, c - hh + cut)]
    sh = Image.new("RGBA", (s, s), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.polygon([(x + s * 0.02, y + s * 0.035) for x, y in case], fill=(0, 0, 0, 170))
    sd.rounded_rectangle((c - s * 0.17 + s * 0.02, -s * 0.1, c + s * 0.17 + s * 0.02, s * 1.1), radius=s * 0.05, fill=(0, 0, 0, 120))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(s * 0.03)))
    # --- kauçuk kayış: gradyan + doku + oluklar
    for y0, y1 in ((-s * 0.05, c - hh + s * 0.02), (c + hh - s * 0.02, s * 1.05)):
        box = (c - s * 0.17, y0, c + s * 0.17, y1)
        m = _mask_rrect(s, box, s * 0.05)
        strap = _lin((s, s), (34, 37, 43), (64, 69, 78), horizontal=True)
        strap = Image.composite(_lin((s, s), (64, 69, 78), (30, 33, 38), horizontal=True), strap,
                                Image.new("L", (s, s), 0).point(lambda v: 0))
        im = _paint(im, m, strap)
        tex = _noise(s, 26, 3, scale=3, blur=0.8)
        grain = Image.new("RGBA", (s, s), (255, 255, 255, 0)); grain.putalpha(tex.point(lambda v: max(0, v - 128) // 3))
        im = Image.composite(Image.alpha_composite(im, grain), im, m)
        d = ImageDraw.Draw(im)
        step = s * 0.055
        yy = y0 + step
        while yy < y1 - step * 0.5:
            d.line([(c - s * 0.13, yy), (c + s * 0.13, yy)], fill=(22, 24, 28, 255), width=max(1, int(s * 0.01)))
            d.line([(c - s * 0.13, yy + s * 0.008), (c + s * 0.13, yy + s * 0.008)], fill=(90, 96, 108, 120), width=max(1, int(s * 0.004)))
            yy += step
    # --- kasa: fırçalanmış metal + kenar ışığı (bevel)
    cm = _mask_poly(s, case)
    metal = _lin((s, s), (150, 156, 166), (58, 62, 70))
    brush = _noise(s, 22, 9, scale=2, blur=0.3).resize((s, s // 6), Image.BILINEAR).resize((s, s), Image.BILINEAR)
    metal = Image.composite(Image.new("RGBA", (s, s), (200, 205, 215, 255)), metal, brush.point(lambda v: max(0, v - 120) * 2))
    im = _paint(im, cm, metal)
    edge = cm.filter(ImageFilter.GaussianBlur(s * 0.012))
    inner = Image.eval(edge, lambda v: 255 - v)
    hl = Image.new("RGBA", (s, s), (255, 255, 255, 0)); hl.putalpha(Image.eval(inner, lambda v: v // 3))
    im = Image.composite(Image.alpha_composite(im, hl), im, cm)
    # vidalar
    d = ImageDraw.Draw(im)
    for sx_, sy_ in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x, y = c + sx_ * (hw - s * 0.045), c + sy_ * (hh - s * 0.045)
        r = s * 0.014
        d.ellipse((x - r, y - r, x + r, y + r), fill=(40, 43, 48, 255)); d.line([(x - r * 0.7, y), (x + r * 0.7, y)], fill=(120, 126, 136, 255), width=max(1, int(s * 0.004)))
    # yan düğmeler (turuncu, gradyanlı)
    for yy in (c - s * 0.12, c + s * 0.12):
        for side in (1, -1):
            bx0 = c + side * hw - (0 if side > 0 else s * 0.04); bx1 = bx0 + s * 0.04
            bm = _mask_rrect(s, (bx0, yy - s * 0.032, bx1, yy + s * 0.032), s * 0.012)
            im = _paint(im, bm, _lin((s, s), (255, 150, 70), (170, 60, 0)))
    # --- ekran: çerçeve, iç gölge, parlayan içerik
    sx, sy = s * 0.215, s * 0.195
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((c - sx - s * 0.012, c - sy - s * 0.012, c + sx + s * 0.012, c + sy + s * 0.012), radius=s * 0.045, fill=(20, 22, 26, 255))
    scr = _mask_rrect(s, (c - sx, c - sy, c + sx, c + sy), s * 0.035)
    im = _paint(im, scr, _lin((s, s), (16, 20, 26), (6, 8, 10)))
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    ex, r = c - s * 0.095, s * 0.09
    dia = [(ex, c - r), (ex + r, c), (ex, c + r), (ex - r, c)]
    gd.polygon(dia, fill=(255, 120, 30, 200))
    im = Image.composite(Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(s * 0.025))), im, scr)
    d = ImageDraw.Draw(im)
    d.polygon(dia, fill=ORANGE); r2 = r * 0.42
    d.polygon([(ex, c - r2), (ex + r2, c), (ex, c + r2), (ex - r2, c)], fill=(8, 10, 12, 255))
    bw = max(2, int(s * 0.026))
    for i, frac in enumerate((1.0, 0.72, 0.46)):
        y = c - s * 0.085 + i * s * 0.07
        d.rounded_rectangle((c + s * 0.025, y, c + s * 0.025 + s * 0.16, y + bw), radius=bw / 2, fill=(40, 44, 50, 255))
        d.rounded_rectangle((c + s * 0.025, y, c + s * 0.025 + s * 0.16 * frac, y + bw), radius=bw / 2,
                            fill=(236, 234, 230, 255) if i == 0 else (255, 140, 60, 255) if i == 1 else (150, 156, 166, 255))
    # cam yansıması (çapraz parlama)
    refl = Image.new("RGBA", (s, s), (255, 255, 255, 0)); rd = ImageDraw.Draw(refl)
    rd.polygon([(c - sx, c - sy), (c - sx + s * 0.22, c - sy), (c - sx + s * 0.06, c + sy), (c - sx, c + sy)], fill=(255, 255, 255, 34))
    rd.polygon([(c - sx + s * 0.26, c - sy), (c - sx + s * 0.30, c - sy), (c - sx + s * 0.14, c + sy), (c - sx + s * 0.10, c + sy)], fill=(255, 255, 255, 18))
    im = Image.composite(Image.alpha_composite(im, refl.filter(ImageFilter.GaussianBlur(s * 0.004))), im, scr)
    return im


DESIGNS["watch_real"] = design_watch_real


def render(size, design=None):
    s = max(256, size) * 4                      # büyük çiz, küçült: kenarlar yumuşak
    return DESIGNS[design or DESIGN](s).resize((size, size), Image.LANCZOS)


def save_ico(out, design=None):
    imgs = [render(n, design) for n in SIZES]
    imgs[-1].save(out, format="ICO", sizes=[(n, n) for n in SIZES], append_images=imgs[:-1])
    imgs[-1].save(str(out).rsplit(".", 1)[0] + ".png")
    return out


def preview(out, names=None):
    names = names or list(DESIGNS)
    W = 40 + len(names) * 300
    sheet = Image.new("RGB", (W, 420), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        x = 40 + i * 300
        sheet.paste(render(256, n), (x, 30), render(256, n))
        for j, sz in enumerate((64, 32, 16)):
            im = render(sz, n); sheet.paste(im, (x + j * 90, 320 + (64 - sz) // 2), im)
        d.text((x, 300), f"{i + 1}. {n}", fill=(40, 40, 40))
    sheet.save(out)
    return out


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "td2.ico"
    if "--preview" in sys.argv:
        sel = [a for a in sys.argv[2:] if a in DESIGNS]
        print("preview:", preview(out, sel or None))
    else: print("icon:", save_ico(out))
