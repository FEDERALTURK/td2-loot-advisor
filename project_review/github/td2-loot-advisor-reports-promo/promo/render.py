"""TD2 Loot Advisor tanıtım videosu kurgusu.
    python render.py <assets> <lang> <out.mp4> [--w 3840 --h 2160 --fps 30] [--vertical] [--preview]
assets/
  shots/<lang>_dark/*.png, shots/<lang>_<theme>/dash_keep.png, shots/<lang>_dark/phone.png
  vo/<lang>_0..6.wav, music.wav (render sırasında üretilir), fonts/, brief_<lang>.json
Ses: anlatım bölümleri sahne başlarına yerleşir; müzik anlatım altında kısılır (sidechain), -14 LUFS.
"""
import argparse, json, math, subprocess, sys, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ap = argparse.ArgumentParser()
ap.add_argument("assets"); ap.add_argument("lang"); ap.add_argument("out")
ap.add_argument("--w", type=int, default=3840); ap.add_argument("--h", type=int, default=2160); ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--vertical", action="store_true"); ap.add_argument("--preview", action="store_true")
ap.add_argument("--frames", default="")             # "a:b" yalnız bu kare aralığı (denetim için PNG)
A = ap.parse_args()
AS = Path(A.assets); LANG = A.lang
W, H, FPS = A.w, A.h, A.fps
K = W / 3840                                         # her ölçü 4K'ya göre tanımlı
ORANGE, ORANGE2 = (255, 106, 0), (255, 138, 51)
BG0, BG1 = (9, 11, 15), (20, 24, 31)
TXT, DIM = (236, 238, 242), (139, 147, 163)
KEEPC, DISC = (63, 185, 80), (248, 81, 73)
FONTS = AS / "fonts"


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), max(8, int(size * K)))


def raj(s): return font("Rajdhani-Bold.ttf", s)
def rajs(s): return font("Rajdhani-SemiBold.ttf", s)
def inter(s): return font("Inter-SemiBold.otf", s)
def interr(s): return font("Inter-Regular.otf", s)


TEXT = {
    "tr": {"tag": "Sakla mı, kır mı? Saniyeler içinde.", "s2": "SAKLA MI, KIR MI?", "s2b": "Senin build kuralların, senin kararın",
           "s3": "BUILD'LER VE EKSİK PARÇALAR", "s3b": "Meta build'ler tek tıkla", "s4": "CANLI ÇEVİRİ", "s4b": "Oyunun üstünde, kendi dilinde",
           "s5": "GÖREVLER VE TELEFON", "s5b": "Topluluktan derlenen güncel görevler", "s6": "OYUN HAVASINDA TEMALAR", "s6b": "10 dil · kendi dilini ekle",
           "b1": "Oyun belleğine dokunmaz", "b2": "Yalnızca ekranı okur", "b3": "10 dil · Ücretsiz", "keep": "SAKLA", "dis": "KIR",
           "orig": "OYUN METNİ (İngilizce)", "trd": "TD2 LOOT ADVISOR · Türkçe"},
    "en": {"tag": "Keep or dismantle? In seconds.", "s2": "KEEP OR DISMANTLE?", "s2b": "Your build rules, your call",
           "s3": "BUILDS & MISSING PIECES", "s3b": "Import the meta in one click", "s4": "LIVE TRANSLATION", "s4b": "On top of the game, in your language",
           "s5": "PROJECTS & PHONE", "s5b": "Current tasks gathered by the community", "s6": "THEMES INSPIRED BY THE GAME", "s6b": "10 languages · add your own",
           "b1": "Never touches game memory", "b2": "Only reads your screen", "b3": "10 languages · Free", "keep": "KEEP", "dis": "DISMANTLE",
           "orig": "GAME TEXT (English)", "trd": "TD2 LOOT ADVISOR · Turkish"},
}[LANG]
THEMES = [("darkzone", "Dark Zone"), ("blacktusk", "Black Tusk"), ("hunter", "Hunter"), ("winter_ny", "Winter New York"),
          ("nightops", "Night Ops"), ("kenly", "Kenly")]
SCRIPT = json.loads((AS / "script.json").read_text(encoding="utf-8"))[LANG]


# ------------------------------------------------------------------ yardımcılar
def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def ease_out(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def lerp(a, b, x): return a + (b - a) * x


_cache = {}


def load(path):
    if path not in _cache:
        _cache[path] = Image.open(path).convert("RGB")
    return _cache[path]


def shot(name, lang=None, theme="dark"):
    return load(AS / "shots" / f"{lang or LANG}_{theme}" / f"{name}.png")


_shadow = {}


def shadow_for(size, radius):
    key = (size, radius)
    if key not in _shadow:
        w, h = size; pad = radius * 3
        m = Image.new("L", (w + pad * 2, h + pad * 2), 0)
        ImageDraw.Draw(m).rectangle((pad, pad + radius // 2, pad + w, pad + h + radius // 2), fill=200)
        _shadow[key] = (m.filter(ImageFilter.GaussianBlur(radius)), pad)
    return _shadow[key]


def place(canvas, img, cx, cy, width, alpha=1.0, border=None, glow=None):
    """Pencere görüntüsünü ortası (cx, cy) ve genişliği verilerek gölgeli yerleştirir."""
    if alpha <= 0.01 or width < 4: return
    w = int(width); h = int(img.height * width / img.width)
    im = img.resize((w, h), Image.BILINEAR if not A.preview else Image.NEAREST)
    x, y = int(cx - w / 2), int(cy - h / 2)
    r = max(6, int(28 * K))
    sm, pad = shadow_for((w // 8 * 8, h // 8 * 8), r)
    blk = Image.new("RGB", sm.size, (0, 0, 0))
    canvas.paste(blk, (x - pad, y - pad), sm.point(lambda v: int(v * alpha * 0.85)))
    if glow:
        g = Image.new("RGB", sm.size, glow)
        canvas.paste(g, (x - pad, y - pad), sm.point(lambda v: int(v * alpha * 0.55)))
    if border:
        d = ImageDraw.Draw(canvas); bw = max(1, int(3 * K))
        if alpha >= 0.99: d.rectangle((x - bw, y - bw, x + w + bw - 1, y + h + bw - 1), outline=border, width=bw)
    if alpha >= 0.99: canvas.paste(im, (x, y))
    else: canvas.paste(im, (x, y), Image.new("L", im.size, int(255 * alpha)))


def text(canvas, xy, s, f, fill=TXT, anchor="la", alpha=1.0, spacing=0):
    if alpha <= 0.01: return
    if alpha >= 0.99 and not spacing:
        ImageDraw.Draw(canvas).text(xy, s, font=f, fill=fill, anchor=anchor); return
    d = ImageDraw.Draw(canvas)
    bbox = d.textbbox((0, 0), s, font=f, anchor="la")
    tw = bbox[2] + spacing * max(0, len(s) - 1); th = bbox[3] + int(10 * K)
    layer = Image.new("L", (int(tw) + 4, th + 4), 0); ld = ImageDraw.Draw(layer)
    if spacing:
        x = 0
        for ch in s:
            ld.text((x, 0), ch, font=f, fill=255); x += ld.textlength(ch, font=f) + spacing
    else:
        ld.text((0, 0), s, font=f, fill=255)
    x, y = xy
    if anchor[0] == "m": x -= tw / 2
    elif anchor[0] == "r": x -= tw
    if anchor[1] == "m": y -= th / 2
    canvas.paste(Image.new("RGB", layer.size, fill), (int(x), int(y)), layer.point(lambda v: int(v * alpha)))


def diamond(canvas, cx, cy, r, fill=ORANGE, alpha=1.0):
    if alpha <= 0.01: return
    m = Image.new("L", (int(2 * r) + 2, int(2 * r) + 2), 0)
    ImageDraw.Draw(m).polygon([(r, 0), (2 * r, r), (r, 2 * r), (0, r)], fill=int(255 * alpha))
    canvas.paste(Image.new("RGB", m.size, fill), (int(cx - r), int(cy - r)), m)


def title(canvas, big, small, tl, x=None, y=None):
    """Sol üst sahne başlığı: turuncu çizgi + büyük başlık + alt satır."""
    x = int(170 * K) if x is None else x; y = int(150 * K) if y is None else y
    a = ease_out(tl / 0.6); dx = (1 - a) * -60 * K
    d = ImageDraw.Draw(canvas)
    if a > 0.02:
        d.rectangle((x + dx, y, x + dx + int(12 * K), y + int(150 * K)), fill=ORANGE)
    text(canvas, (x + dx + int(44 * K), y - int(6 * K)), big, raj(104), alpha=a, spacing=int(4 * K))
    text(canvas, (x + dx + int(48 * K), y + int(104 * K)), small, inter(40), fill=DIM, alpha=ease_out((tl - 0.25) / 0.6))


# ------------------------------------------------------------------ arka plan
def make_bg():
    bg = Image.new("RGB", (W, H), BG0)
    d = ImageDraw.Draw(bg)
    for i in range(H):                                     # dikey degrade
        c = tuple(int(lerp(BG1[k], BG0[k], i / H)) for k in range(3)); d.line((0, i, W, i), fill=c)
    s = int(120 * K)                                       # altıgen ızgara
    hexw, hexh = s * math.sqrt(3), s * 1.5
    for row in range(int(H / hexh) + 2):
        for col in range(int(W / hexw) + 2):
            cx = col * hexw + (hexw / 2 if row % 2 else 0); cy = row * hexh
            pts = [(cx + s * math.cos(math.radians(60 * k + 30)), cy + s * math.sin(math.radians(60 * k + 30))) for k in range(6)]
            d.polygon(pts, outline=(26, 31, 40))
    vig = Image.new("L", (W, H), 0); vd = ImageDraw.Draw(vig)
    for i in range(40):
        vd.ellipse((-W * 0.25 + i * W * 0.006, -H * 0.3 + i * H * 0.008, W * 1.25 - i * W * 0.006, H * 1.3 - i * H * 0.008), fill=int(i * 6))
    vig = vig.filter(ImageFilter.GaussianBlur(int(80 * K)))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(bg, dark, vig)


BG = make_bg()


def background(t):
    c = BG.copy()
    d = ImageDraw.Draw(c)
    # yavaşça kayan turuncu tarama çizgisi + birkaç "ISAC" parçacığı
    y = int((t * 160 * K) % (H + 400 * K) - 200 * K)
    for i in range(int(60 * K)):
        a = 1 - i / (60 * K)
        col = tuple(int(BG0[k] + (ORANGE[k] - BG0[k]) * 0.06 * a) for k in range(3))
        d.line((0, y + i, W, y + i), fill=col)
    for k in range(18):
        px = (k * 397 + t * (20 + k * 3) * K * 10) % W; py = (k * 211 + math.sin(t * 0.7 + k) * 80 * K + k * 120 * K) % H
        rr = int((2 + (k % 3)) * K * 2)
        d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=(90 + k * 3, 50, 20))
    return c


# ------------------------------------------------------------------ çeviri sahnesi görselleri
def brief_panel(translated):
    """Özgün tasarım 'telsiz kaydı' paneli (oyunun arayüzü değil) + programın yerinde çeviri kutuları."""
    data = json.loads((AS / f"brief_{LANG}.json").read_text(encoding="utf-8"))
    PW, PH = int(2100 * K), int(1500 * K)
    p = Image.new("RGB", (PW, PH), (24, 30, 37)); d = ImageDraw.Draw(p)
    for i in range(0, PW, int(46 * K)): d.line((i, 0, i - int(300 * K), PH), fill=(28, 35, 43), width=max(1, int(14 * K)))
    d.rectangle((0, 0, PW, int(110 * K)), fill=(14, 17, 21))
    text(p, (int(50 * K), int(26 * K)), "COMMS LOG  ·  SECTOR 7", rajs(52), fill=(200, 210, 220), spacing=int(3 * K))
    y = int(190 * K); boxes = []
    for en in data["en"]:
        f = interr(60); lines = wrap(en, f, PW - int(140 * K))
        y0 = y
        for ln in lines:
            d.text((int(70 * K), y), ln, font=f, fill=(225, 230, 236)); y += int(84 * K)
        boxes.append((y0, y)); y += int(60 * K)
    p = p.crop((0, 0, PW, y + int(40 * K))); d = ImageDraw.Draw(p)
    if translated:
        st = data["style"]
        for (y0, y1), trt in zip(boxes, data["tr"]):
            pad = int(18 * K)
            d.rectangle((int(50 * K), y0 - pad, PW - int(50 * K), y1 + pad - int(14 * K)), fill=tuple(st["bg"]), outline=tuple(st["border"]), width=max(1, int(4 * K)))
            f = inter(58); yy = y0
            for ln in wrap(trt, f, PW - int(160 * K)):
                d.text((int(76 * K), yy), ln, font=f, fill=tuple(st["fg"])); yy += int(84 * K)
    return p


def wrap(s, f, maxw):
    d = ImageDraw.Draw(Image.new("L", (10, 10)))
    words, out, cur = s.split(), [], ""
    for w_ in words:
        t_ = (cur + " " + w_).strip()
        if d.textlength(t_, font=f) <= maxw: cur = t_
        else: out.append(cur); cur = w_
    if cur: out.append(cur)
    return out


def phone_frame(img):
    sw = 1170; sh = int(img.height * sw / img.width)
    sh = min(sh, 1650)
    scr = img.resize((sw, int(img.height * sw / img.width))).crop((0, 0, sw, sh))
    bw = 46; fr = Image.new("RGB", (sw + 2 * bw, sh + 2 * bw), (8, 9, 11))
    d = ImageDraw.Draw(fr); d.rounded_rectangle((0, 0, fr.width - 1, fr.height - 1), radius=150, fill=(30, 33, 38))
    d.rounded_rectangle((bw - 8, bw - 8, bw + sw + 7, bw + sh + 7), radius=110, fill=(5, 5, 6))
    m = Image.new("L", (sw, sh), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, sw - 1, sh - 1), radius=100, fill=255)
    fr.paste(scr, (bw, bw), m)
    d.rounded_rectangle((fr.width // 2 - 110, bw + 30, fr.width // 2 + 110, bw + 90), radius=30, fill=(5, 5, 6))
    return fr


# ------------------------------------------------------------------ sahneler
def s_intro(c, tl, dur):
    blur = shot("dash_keep").resize((W // 4, int(W / 4 * 1800 / 2720))).filter(ImageFilter.GaussianBlur(int(8)))
    blur = ImageEnhance.Brightness(blur).enhance(0.35).resize((int(W * 1.1), int(W * 1.1 * 1800 / 2720)))
    a = ease(tl / 1.2) * (1 - ease((tl - dur + 0.5) / 0.5)) * 0.9
    c.paste(blur, (int(-W * 0.05 - tl * 20 * K), int((H - blur.height) / 2)), Image.new("L", blur.size, int(255 * a * 0.6)))
    s = ease_out(tl / 0.9)
    diamond(c, W / 2, H * 0.36, 110 * K * s, alpha=s)
    diamond(c, W / 2, H * 0.36, 52 * K * s, fill=BG0, alpha=s)
    sp = int(lerp(60, 14, ease_out((tl - 0.3) / 1.2)) * K)
    text(c, (W / 2, H * 0.48), "TD2 LOOT ADVISOR", raj(230), anchor="mm", alpha=ease((tl - 0.3) / 0.8), spacing=sp)
    text(c, (W / 2, H * 0.60), TEXT["tag"], inter(64), fill=DIM, anchor="mm", alpha=ease((tl - 1.4) / 0.7))
    ImageDraw.Draw(c).rectangle((W / 2 - 260 * K * ease_out((tl - 1.0) / 0.8), H * 0.545, W / 2 + 260 * K * ease_out((tl - 1.0) / 0.8), H * 0.545 + 6 * K), fill=ORANGE)


def s_verdict(c, tl, dur):
    half = dur * 0.55
    first = tl < half
    lt = tl if first else tl - half
    win = shot("dash_keep" if first else "dash_dismantle"); pop = shot("popup_keep" if first else "popup_dismantle")
    a_in = ease_out(lt / 0.6) if first else 1.0
    wx = lerp(W * 0.40, W * 0.38, tl / dur); wwid = lerp(2400, 2500, tl / dur) * K
    if not first and lt < 0.4:
        place(c, shot("dash_keep"), wx, H * 0.61, wwid, alpha=1 - ease(lt / 0.4))
        place(c, win, wx, H * 0.61, wwid, alpha=ease(lt / 0.4))
    else:
        place(c, win, wx + (1 - a_in) * 300 * K, H * 0.61, wwid, alpha=a_in)
    pa = ease_out((lt - 0.9) / 0.6)
    col = KEEPC if first else DISC
    place(c, pop, W * 0.80 + (1 - pa) * 500 * K, H * 0.58, 1150 * K, alpha=pa, glow=col)
    lab = TEXT["keep"] if first else TEXT["dis"]
    text(c, (W * 0.80, H * 0.84), lab, raj(120), fill=col, anchor="mm", alpha=ease_out((lt - 1.3) / 0.5), spacing=int(10 * K))
    title(c, TEXT["s2"], TEXT["s2b"], tl)


def s_builds(c, tl, dur):
    half = dur * 0.5
    b, p = shot("builds"), shot("progress")
    wid = lerp(2550, 2650, tl / dur) * K
    if tl < half:
        a = ease_out(tl / 0.6); place(c, b, W * 0.5 + (1 - a) * 200 * K, H * 0.615, wid, alpha=a)
    else:
        x = ease((tl - half) / 0.5)
        place(c, b, W * 0.5 - x * 300 * K, H * 0.615, wid, alpha=1 - x)
        place(c, p, W * 0.5 + (1 - x) * 300 * K, H * 0.615, wid, alpha=x)
    title(c, TEXT["s3"], TEXT["s3b"], tl)


_brief = {}


def s_translate(c, tl, dur):
    for k in (False, True):
        if k not in _brief: _brief[k] = brief_panel(k)
    x = ease((tl - dur * 0.32) / 0.7)
    cx, cy, wid = W * 0.37, H * 0.58, lerp(2050, 2130, tl / dur) * K
    a0 = ease_out(tl / 0.6)
    place(c, _brief[False], cx, cy, wid, alpha=a0 * (1 - x) if x < 1 else 0)
    if x > 0: place(c, _brief[True], cx, cy, wid, alpha=x)
    lbl = TEXT["orig"] if x < 0.5 else TEXT["trd"]
    text(c, (cx - wid / 2, cy + _brief[False].height * wid / _brief[False].width / 2 + 40 * K), lbl, rajs(46), fill=ORANGE2 if x >= 0.5 else DIM, alpha=a0)
    ia = ease_out((tl - dur * 0.55) / 0.6)
    place(c, shot("translate"), W * 0.83 + (1 - ia) * 400 * K, H * 0.62, 1150 * K, alpha=ia, border=(44, 49, 61))
    title(c, TEXT["s4"], TEXT["s4b"], tl)


_phone = {}


def s_tasks(c, tl, dur):
    a = ease_out(tl / 0.6)
    place(c, shot("tasks"), W * 0.40 + (1 - a) * -200 * K, H * 0.61, lerp(2350, 2450, tl / dur) * K, alpha=a)
    if "p" not in _phone:
        ph = AS / "shots" / f"{LANG}_dark" / "phone.png"
        _phone["p"] = phone_frame(load(ph)) if ph.exists() else None
    if _phone["p"] is not None:
        pa = ease_out((tl - 0.9) / 0.7)
        pw = 760 * K
        place(c, _phone["p"], W * 0.82, H * 0.60 + (1 - pa) * 700 * K, pw, alpha=pa, glow=ORANGE)
    title(c, TEXT["s5"], TEXT["s5b"], tl)


def s_themes(c, tl, dur):
    cols, rows = 3, 2
    tw = 1000 * K; th = tw * 1800 / 2720; gx = 80 * K
    x0 = (W - (cols * tw + (cols - 1) * gx)) / 2; y0 = H * 0.25
    for i, (key, name) in enumerate(THEMES):
        p = AS / "shots" / f"{LANG}_{key}" / "dash_keep.png"
        if not p.exists(): continue
        a = ease_out((tl - 0.25 - i * 0.22) / 0.5)
        cx = x0 + (i % cols) * (tw + gx) + tw / 2; cy = y0 + (i // cols) * (th + 130 * K) + th / 2
        z = lerp(0.92, 1.0, a) * lerp(1.0, 1.03, tl / dur)
        place(c, load(p), cx, cy + (1 - a) * 80 * K, tw * z, alpha=a)
        text(c, (cx, cy + th * z / 2 + 46 * K), name.upper(), rajs(48), fill=DIM, anchor="mm", alpha=a, spacing=int(4 * K))
    title(c, TEXT["s6"], TEXT["s6b"], tl, y=int(80 * K))


def s_outro(c, tl, dur):
    s = ease_out(tl / 0.8)
    diamond(c, W / 2, H * 0.27, 90 * K * s, alpha=s); diamond(c, W / 2, H * 0.27, 42 * K * s, fill=BG0, alpha=s)
    text(c, (W / 2, H * 0.40), "TD2 LOOT ADVISOR", raj(200), anchor="mm", alpha=ease(tl / 0.8), spacing=int(14 * K))
    for i, b in enumerate((TEXT["b1"], TEXT["b2"], TEXT["b3"])):
        a = ease_out((tl - 0.6 - i * 0.35) / 0.5)
        bx = W / 2 + (i - 1) * 1120 * K; by = H * 0.60
        d = ImageDraw.Draw(c)
        if a > 0.02:
            bw_, bh_ = 1000 * K, 150 * K
            box = Image.new("RGB", (int(bw_), int(bh_)), (24, 28, 36))
            ImageDraw.Draw(box).rectangle((0, 0, int(10 * K), int(bh_)), fill=ORANGE)
            c.paste(box, (int(bx - bw_ / 2), int(by - bh_ / 2 + (1 - a) * 60 * K)), Image.new("L", box.size, int(255 * a)))
            text(c, (bx + 10 * K, by + (1 - a) * 60 * K), b, inter(50), anchor="mm", alpha=a)
    text(c, (W / 2, H * 0.80), "github.com/FEDERALTURK/td2-loot-advisor", inter(58), fill=ORANGE2, anchor="mm", alpha=ease((tl - 1.6) / 0.6))


SCENES = [s_intro, s_verdict, s_builds, s_translate, s_tasks, s_themes, s_outro]


# ------------------------------------------------------------------ zaman çizelgesi ve ses
def wav_dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


vo = [AS / "vo" / f"{LANG}_{i}.wav" for i in range(7)]
durs = [wav_dur(p) for p in vo]
LEAD = 0.9
# hedef ~60 sn: sahneler arası boşluk anlatım süresine göre ayarlanır (en az 0.45 sn, en çok 1.6 sn)
GAP = max(0.45, min(1.6, (60.0 - 1.6 - LEAD - 0.25 * 6 - sum(durs)) / 7))
starts, t = [], 0.0
for i, d in enumerate(durs):
    starts.append(t); t += (LEAD if i == 0 else 0.25) + d + GAP
scene_t = starts + [t]
vo_at = [s + (LEAD if i == 0 else 0.25) for i, s in enumerate(starts)]
TOTAL = t + 1.6
print(f"total {TOTAL:.1f}s", [round(x, 2) for x in durs], flush=True)

work = Path(A.out).with_suffix(""); work.mkdir(parents=True, exist_ok=True)
mus = work / "music.wav"
subprocess.run([sys.executable, str(Path(__file__).with_name("music.py")), str(TOTAL), str(mus)], check=True)
# anlatım izi: her parça kendi zamanına (adelay), sonra müzikle karıştır
inputs = []; flt = []
for i, p in enumerate(vo):
    inputs += ["-i", str(p)]
    ms = int(vo_at[i] * 1000)
    flt.append(f"[{i}:a]aresample=48000,pan=stereo|c0=c0|c1=c0,adelay={ms}|{ms},apad[v{i}]")
flt.append("".join(f"[v{i}]" for i in range(7)) + f"amix=inputs=7:normalize=0,atrim=0:{TOTAL:.3f},asplit=2[vo][sc]")
inputs += ["-i", str(mus)]
flt.append(f"[7:a]volume=0.55[m];[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];"
           f"[vo]volume=1.6[vv];[vv][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.0:LRA=11[out]")
mix = work / "mix.wav"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(flt), "-map", "[out]", "-ar", "48000", str(mix)], check=True)

# altyazı (SRT): ekrandaki metin = senaryonun yazılı hâli
def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f"{h:02}:{m:02}:{int(s):02},{int((s % 1) * 1000):03}"
srt = []
for i, (sub, _say) in enumerate(SCRIPT):
    srt.append(f"{i + 1}\n{ts(vo_at[i])} --> {ts(vo_at[i] + durs[i])}\n{sub}\n")
Path(A.out).with_suffix(".srt").write_text("\n".join(srt), encoding="utf-8")


def frame(t):
    c = background(t)
    for i, fn in enumerate(SCENES):
        a, b = scene_t[i], (scene_t[i + 1] if i + 1 < len(scene_t) else TOTAL)
        if i == len(SCENES) - 1: b = TOTAL
        if a <= t < b + 0.35:
            layer = background(t) if False else None
            if t < b:
                fn(c, t - a, b - a)
            break
    # sahne geçişlerinde kısa karartma
    for s_ in scene_t[1:]:
        dt = abs(t - s_)
        if dt < 0.18:
            c = Image.blend(c, Image.new("RGB", (W, H), BG0), 0.85 * (1 - dt / 0.18))
    if t > TOTAL - 0.8: c = Image.blend(c, Image.new("RGB", (W, H), (0, 0, 0)), ease((t - TOTAL + 0.8) / 0.8))
    if t < 0.3: c = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), c, ease(t / 0.3))
    return c


def caption(t):
    for i, (sub, _s) in enumerate(SCRIPT):
        if vo_at[i] - 0.1 <= t <= vo_at[i] + durs[i] + 0.2: return sub
    return ""


nframes = int(TOTAL * FPS)
if A.frames:
    if ":" in A.frames:
        a_, b_ = map(int, A.frames.split(":")); idxs = range(a_, b_)
    else:
        idxs = [int(float(x) * FPS) for x in A.frames.split(",")]          # saniye listesi
    for fi in idxs:
        frame(fi / FPS).save(work / f"f{fi:05d}.png")
    print("frames saved", work); sys.exit(0)

if A.vertical:
    VW, VH = 1080, 1920
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-",
           "-i", str(mix), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-shortest", A.out]
else:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(mix), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", A.out]
ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
capf = font("Inter-SemiBold.otf", 0)
for fi in range(nframes):
    t = fi / FPS
    img = frame(t)
    if A.vertical:
        v = Image.new("RGB", (VW, VH), BG0)
        bgb = img.resize((VH * W // H, VH)).filter(ImageFilter.GaussianBlur(30))
        v.paste(ImageEnhance.Brightness(bgb).enhance(0.35), (-(bgb.width - VW) // 2, 0))
        fg = img.resize((VW, VW * H // W)); v.paste(fg, (0, 560))
        d = ImageDraw.Draw(v)
        d.text((VW // 2, 300), "TD2 LOOT ADVISOR", font=ImageFont.truetype(str(FONTS / "Rajdhani-Bold.ttf"), 88), fill=TXT, anchor="mm")
        d.rectangle((VW // 2 - 120, 360, VW // 2 + 120, 366), fill=ORANGE)
        cap = caption(t)
        if cap:
            f = ImageFont.truetype(str(FONTS / "Inter-SemiBold.otf"), 50)
            lines = wrap(cap, f, VW - 120); yy = 1300
            for ln in lines:
                d.text((VW // 2, yy), ln, font=f, fill=TXT, anchor="ma", stroke_width=3, stroke_fill=(0, 0, 0)); yy += 66
        img = v
    ff.stdin.write(img.tobytes())
    if fi % (FPS * 5) == 0: print(f"frame {fi}/{nframes}", flush=True)
ff.stdin.close(); ff.wait()
print("done", A.out, ff.returncode)

