"""Ekran durumu sezicisi: öğrenme, menü / dünya / yükleme, titreme süzgeci.   python tests/test_screenstate.py"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import screenstate as ss  # noqa: E402

fails = 0
def ok(c, m):
    global fails
    print(("OK   " if c else "FAIL ") + m)
    if not c: fails += 1

rng = np.random.default_rng(7)
W, H = 1600, 900
inv = Image.open(ROOT / "tests/samples/inv_striker_pack_scrolled.jpg").convert("RGB")

def world(seed):
    r = np.random.default_rng(seed)
    base = r.random((9, 16, 3)) * 255
    img = Image.fromarray(base.astype("uint8")).resize((W, H), Image.BICUBIC)
    d = ImageDraw.Draw(img)
    for _ in range(40):
        x, y = r.integers(0, W), r.integers(0, H); s = r.integers(20, 200)
        d.rectangle((x, y, x + s, y + s // 2), fill=tuple(int(v) for v in r.integers(0, 255, 3)))
    d.text((40, 40), "HUD 30/30", fill=(255, 255, 255))                 # küçük HUD yazısı
    return img.filter(ImageFilter.GaussianBlur(1.5))

def menu(seed, tab=0):
    """Üstte sabit sekme çubuğu, altta değişen içerik (bulanık dünya + kart)."""
    img = world(seed).filter(ImageFilter.GaussianBlur(12))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 90), fill=(18, 20, 24))
    for i, x in enumerate(range(120, 1500, 230)):
        d.rectangle((x, 28, x + 170, 62), outline=(200, 200, 200), width=2, fill=(255, 109, 16) if i == tab else None)
        d.line((x + 20, 45, x + 150, 45), fill=(230, 230, 230), width=3)
    img.paste(inv.resize((520, 700)), (1000 + seed % 40, 140))
    return img

g = lambda im: ss.from_image(im)
det = ss.Detector()
ok(det.classify(g(menu(1)))[0] == "unknown", "öğrenmeden önce 'unknown' (eski davranış)")
ok(det.classify(g(Image.new("RGB", (W, H), (3, 3, 4))))[0] == "loading", "siyah kare → yükleme")
ok(det.learn(g(menu(1))), "ilk başarılı okumada menü imzası öğrenildi")
ok(not det.learn(g(menu(2))), "aynı menü ikinci kez eklenmez")
hits = [det.classify(g(menu(s)))[0] for s in range(10, 30)]
ok(hits.count("menu") >= 19, f"farklı içerikli menü kareleri tanındı ({hits.count('menu')}/20)")
w = [det.classify(g(world(s))) for s in range(100, 140)]
ok(sum(1 for s, _ in w if s == "world") >= 39, f"dünya kareleri menü sanılmadı ({sum(1 for s,_ in w if s=='world')}/40, en yüksek {max(x for _,x in w):.2f})")
ok(det.classify(g(menu(5, tab=3)))[0] == "menu", "başka sekme seçiliyken de menü")
# titreme süzgeci
det.state = "world"
s1 = det.observe(g(world(500)))
seq = [det.observe(g(menu(s))) for s in (40, 41)]
ok(seq[-1] == "menu", "menüye geçiş en geç 2 karede")
seq = [det.observe(g(world(s))) for s in (600, 601, 602)]
ok(seq[0] == "menu" and seq[-1] == "world", "tek kare dünyaya geçişi tetiklemez, ikincide geçer")
# kalıcılık
import tempfile, os
p = os.path.join(tempfile.mkdtemp(), "st.json")
d1 = ss.Detector(p); d1.learn(g(menu(1)))
d2 = ss.Detector(p)
ok(d2.classify(g(menu(77)))[0] == "menu", "öğrenilen imzalar dosyadan geri yüklendi")
# ham BGRA yolu = PIL yolu
im = menu(3); arr = np.asarray(im)
bgra = np.dstack([arr[..., 2], arr[..., 1], arr[..., 0], np.full(arr.shape[:2], 255, np.uint8)]).tobytes()
a, b = ss.small_gray(bgra, W, H), g(im)
ok(a.shape == b.shape and float(np.abs(a - b).mean()) < 0.03, f"ham ekran tamponundan aynı küçük kare (fark {float(np.abs(a-b).mean()):.3f})")
print("RESULT:", "PASS" if not fails else f"FAIL ({fails})"); sys.exit(1 if fails else 0)
