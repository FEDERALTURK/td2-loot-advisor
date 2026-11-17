"""Tanıtım videosu için programın gerçek ekranlarını 2x ölçekte (4K'ya uygun) yakalar.
    python capture.py <program_kopyası> <dil> <tema> <çıktı_klasörü> [all|dash]
Xvfb 3840x2160 ekranında çalıştırılır. Program kopyası üzerinde çalışır (asıl depoya dokunmaz).
"""
import json, os, sys, time
from pathlib import Path

APPDIR, LANG, THEME, OUT = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
MODE = sys.argv[5] if len(sys.argv) > 5 else "all"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(APPDIR)); os.chdir(APPDIR)
os.environ["TD2_NO_WELCOME"] = "1"

cfgp = APPDIR / "builds.json"
cfg = json.loads(cfgp.read_text(encoding="utf-8"))
cfg.setdefault("settings", {}).update(language=LANG, ui_theme=THEME, fx_video=False, fx_bgwatch=False, task_live=False,
                                      meta_sync=False, update_check=False, news=False, drop_stats_asked=True)
cfgp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

import app  # noqa: E402
from PIL import Image, ImageDraw, ImageFont, ImageGrab  # noqa: E402
app.messagebox.askyesno = lambda *a, **k: False
app.messagebox.showinfo = app.messagebox.showwarning = lambda *a, **k: None
_orig = app.App.apply_window_profile


def wp(self, initial=False):
    _orig(self, initial)
    self.root.tk.call("tk", "scaling", self._base_scaling * 2.0)
    self.ui_factor = 2.0; self.compact = False
    self.root.geometry("2720x1800+40+40")


app.App.apply_window_profile = wp
a = app.App()

KEEP_TXT = """Striker's Chest Protector RANK
Gear Set 10
112k Armor
Gear Set
Striker's Battlegear (4/6)
4+ Pieces
Striker's Gamble
Core Attribute
+15.0% Weapon Damage
Attributes
+6.0% Critical Hit Chance
+12.0% Critical Hit Damage
Mod Slot
Talents
Obliterate"""
DIS_TXT = """Unsorted Gloves RANK
High-End 10
96k Armor
Brand Set
Murakami Industries (0/3)
Core Attribute
+3.0% Weapon Damage
Attributes
+1.0% Critical Hit Chance
+2.0% Critical Hit Damage
Empty Gear Mod Slot"""

FONT = None
for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
    if Path(f).exists(): FONT = f; break


def card_image(item, accent):
    """Programın 'okunan kart' alanı için özgün, sade bir kart görseli (oyunun tasarımı değil)."""
    W, H = 520, 640
    im = Image.new("RGB", (W, H), (22, 25, 31)); d = ImageDraw.Draw(im)
    fb = ImageFont.truetype(FONT, 30) if FONT else ImageFont.load_default()
    fs = ImageFont.truetype(FONT, 22) if FONT else ImageFont.load_default()
    d.rectangle((0, 0, W, 8), fill=accent)
    d.text((28, 34), item["name"], fill=(236, 238, 242), font=fb)
    y = 96
    for k, v in item.get("attrs", {}).items():
        lab = app.attr_name(k)
        d.text((28, y), f"+{v:g}", fill=accent, font=fs); d.text((140, y), lab, fill=(200, 205, 214), font=fs); y += 44
    for tl in item.get("talents", []):
        d.text((28, y + 10), "✦ " + tl, fill=(255, 190, 90), font=fs); y += 44
    d.rectangle((28, H - 60, W - 28, H - 56), fill=(44, 49, 61))
    d.text((28, H - 46), "DEMO", fill=(110, 116, 128), font=fs)
    return im


def grab(name, w=None):
    w = w or a.root
    w.update(); time.sleep(0.6); w.update()
    x, y, ww, hh = w.winfo_rootx(), w.winfo_rooty(), w.winfo_width(), w.winfo_height()
    ImageGrab.grab((x, y, x + ww, y + hh)).save(OUT / f"{name}.png")
    print("shot", name, ww, hh, flush=True)


def show(txt, counts=None):
    item, verdict, res = app.evaluate(txt, a.cfg)
    a.last_card_img = card_image(item, (63, 185, 80) if verdict == "KEEP" else (248, 81, 73))
    a.show_result(txt, item, verdict, res)
    if counts:
        a.counts.update(counts); a.refresh_counts()
    return item, verdict, res


def popup_big(verdict, item, res, name):
    """Oyun üstü kart: ana pencerenin 2x yazı ölçeği yerine kartın kendi büyütme ayarıyla (overlay_size=2)."""
    a.root.tk.call("tk", "scaling", a._base_scaling); a.cfg["settings"]["overlay_size"] = 2.0
    a.popup(verdict, item, res, None)
    def done():
        grab(name, a.overlay); a.root.tk.call("tk", "scaling", a._base_scaling * 2.0); a.cfg["settings"]["overlay_size"] = 1.0
    a.root.after(900, done)


def tab(key):
    a.nb.select(a.tab_keys.index(key)); a.root.update()


steps = []
if MODE in ("all", "dash"):
    steps.append(lambda: (tab("dash"), show(KEEP_TXT, {"KEEP": 14, "CONSIDER": 6, "DISMANTLE": 31, "REVIEW": 2}), grab("dash_keep")))
if MODE == "all":
    def pop():
        item, verdict, res = show(KEEP_TXT)
        popup_big(verdict, item, res, "popup_keep")
    steps.append(pop)
    steps.append(lambda: (a.overlay and a.overlay.destroy(), setattr(a, "overlay", None), show(DIS_TXT), grab("dash_dismantle")))
    def pop2():
        item, verdict, res = show(DIS_TXT)
        popup_big(verdict, item, res, "popup_dismantle")
    steps.append(pop2)
    steps.append(lambda: (a.overlay and a.overlay.destroy(), setattr(a, "overlay", None), tab("builds"), grab("builds")))
    steps.append(lambda: (tab("progress"), grab("progress")))
    steps.append(lambda: (tab("translate"), grab("translate")))
    steps.append(lambda: (tab("tasks"), grab("tasks")))
    steps.append(lambda: (tab("stash"), grab("stash")))
    steps.append(lambda: (tab("stats"), grab("stats")))
    steps.append(lambda: (tab("settings"), grab("settings")))


if MODE == "phone":
    def phone():
        import subprocess, companion
        item, verdict, res = show(KEEP_TXT)
        a._companion_update(item, verdict, res, None)
        c = companion.Companion(lambda: dict(a.comp_state), a._companion_labels(), 8790, token="promo-token-123", lang=LANG)
        c.start()
        url = "http://127.0.0.1:8790/?t=promo-token-123"
        code = ("from playwright.sync_api import sync_playwright\n"
                "with sync_playwright() as p:\n"
                " b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844}, device_scale_factor=3)\n"
                f" pg.goto('{url}'); pg.wait_for_timeout(2500); pg.screenshot(path='{OUT}/phone.png'); b.close()\n")
        def go():
            r = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=60)
            print("shot phone", r.returncode, r.stderr[-300:], flush=True)
        import threading; threading.Thread(target=go, daemon=True).start()
    steps.append(phone)
    steps.append(lambda: None); steps.append(lambda: None); steps.append(lambda: None)


def run(i=0):
    if i >= len(steps):
        a.root.after(500, a.root.destroy); return
    try: steps[i]()
    except Exception as e: print("step", i, "error", repr(e), flush=True)
    a.root.after(2200, lambda: run(i + 1))


a.root.after(9000, run)
a.root.mainloop()

