"""Windows CI: canlı çeviri uçtan uca — model yüklü mü, deneme çevirisi, sahte oyun penceresinde altyazı okuma + Türkçe
kaplama, seçili alan, yapay zekâ seçili değilken anlaşılır hata, açıklamaların Türkçesi (ansiklopedi).
Model klasörü: models/en-tr (iş akışı indirir).   python tests/ui_translate_test.py → tests/.translate_result.json"""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
os.environ["TD2_NO_WELCOME"] = "1"
os.environ["TD2_SHOT_OVERLAY"] = "1"          # kaplama ekran görüntüsünde görünsün (OCR yine maskeyle görmez)
from PIL import Image, ImageDraw, ImageFont, ImageGrab  # noqa: E402

W, H = 960, 600
img = Image.new("RGB", (W, H), (40, 52, 60)); d = ImageDraw.Draw(img)
for i in range(0, W, 40): d.line((i, 0, i - 200, H), fill=(48, 62, 70), width=12)
try: font = ImageFont.truetype("segoeui.ttf", 26)
except OSError: font = ImageFont.load_default()
SUB = "Agent, the Black Tusk have taken control of the Capitol Building."
tw = d.textlength(SUB, font=font); d.text(((W - tw) / 2, 500), SUB, fill=(255, 255, 255), font=font)
d.rectangle((40, 90, 900, 160), fill=(18, 22, 26))
d.text((60, 110), "INTEL: Head to the safe house and talk to the quartermaster.", fill=(230, 230, 230), font=font)
img_path = ROOT / "tests" / ".fake_sub.png"; img.save(img_path)
FAKE = r'''
import sys, tkinter as tk
from PIL import Image, ImageTk
root = tk.Tk(); root.title("Tom Clancy's The Division 2"); root.geometry("960x600+30+30")
ph = ImageTk.PhotoImage(Image.open(sys.argv[1])); tk.Label(root, image=ph, bd=0).place(x=0, y=0)
root.after(200000, root.destroy); root.mainloop()
'''
fp = ROOT / "tests" / ".fake_sub_game.py"; fp.write_text(FAKE, encoding="utf-8")
game = subprocess.Popen([sys.executable, str(fp), str(img_path)])
time.sleep(3)

import app  # noqa: E402
app.messagebox.askyesno = lambda *a, **k: False
app.messagebox.showinfo = app.messagebox.showwarning = lambda *a, **k: None
a = app.App()
a.cfg["settings"].update(only_game_active=False, tr_engine="local", tr_mode="subtitle", tr_auto=True, ai_provider="builtin", tr_hide=40)
res = {"steps": []}
def step(name, ok, **kw):
    res["steps"].append({"name": name, "ok": bool(ok), **kw}); print(("OK   " if ok else "FAIL ") + name, kw, flush=True)
def shot(name, full=False, w=None):
    try:
        if full: ImageGrab.grab(all_screens=True).save(SHOTS / f"tr_{name}.png"); return
        w = w or a.root; w.deiconify(); w.lift(); w.update(); time.sleep(0.4)
        x, y = w.winfo_rootx(), w.winfo_rooty()
        ImageGrab.grab(bbox=(x, y, x + w.winfo_width(), y + w.winfo_height()), all_screens=True).save(SHOTS / f"tr_{name}.png")
    except Exception as e: print("shot", e)

def s1():
    a.nb.select(a.tab_keys.index("translate")); a.root.update()
    step("model yüklü görünüyor", "✔" in a.lt_model_lbl.cget("text"), lbl=a.lt_model_lbl.cget("text"))
    a.lt_try(); a.root.after(6000, s2)
def s2():
    out = a.lt_out.cget("text")
    step("deneme çevirisi Türkçe, adlar korundu", "Black Tusk" in out and ("Ajan" in out or "ele geçir" in out), out=out)
    shot("01_tab")
    ok = a.lt_start(quiet=True)
    step("canlı çeviri başladı", ok and bool(a.lt_stop_ev))
    a.root.after(12000, s3)
def s3():
    w = getattr(a, "_lt_win", None)
    hist = getattr(a, "lt_hist", [])
    step("altyazı okundu ve çevrildi", any("Black Tusk" in en for en, _ in hist), hist=hist[-2:])
    step("çeviri kaplaması oyunun üstünde", bool(w) and w.winfo_exists(), geo=w.winfo_geometry() if w else None)
    shot("02_overlay", full=True)
    a.lt_stop()
    step("durduruldu", not getattr(a, "lt_stop_ev", None) and a._lt_win is None)
    a.cfg["settings"].update(tr_mode="region", tr_region={"left": 30 + 30, "top": 30 + 30 + 80, "width": 880, "height": 90})
    a.lt_hist = []; a.lt_once(); a.root.after(8000, s4)
def s4():
    hist = getattr(a, "lt_hist", [])
    step("seçili alan (istihbarat metni) çevrildi", any("quartermaster" in en for en, _ in hist), hist=hist[-1:])
    shot("03_region", full=True); a._lt_hide()
    a.cfg["settings"]["tr_engine"] = "ai"
    try:
        a.lt_translator().translate(["x"]); step("yapay zekâ seçili değilken hata", False)
    except RuntimeError as e:
        step("yapay zekâ seçili değilken anlaşılır hata", app.t("lt.no_ai") in str(e), e=str(e))
    a.cfg["settings"]["tr_engine"] = "local"
    app.i18n.set_language("tr")
    txt = a.localized_desc("Obliterate", "Critical hits increase total weapon damage by 1% for 5s. Stacks up to 15 times.")
    step("ansiklopedi açıklaması Türkçe", "Kritik" in txt, txt=txt)
    # yerinde çeviri
    a.cfg["settings"].update(tr_mode="inplace", tr_hide=40); a._lt_last_sig = None
    a.lt_hist = []; a.lt_once(); a.root.after(9000, s5)
def s5():
    ip = getattr(a, "_lt_inplace", None)
    n = len(ip.cv.find_all()) if ip and ip.cv else 0
    step("yerinde çeviri: kutular oyun yazılarının yerinde", bool(ip and ip.win and n >= 4), canvas_items=n)
    shot("04_inplace", full=True); a._lt_hide()
    # telefon / ikinci ekran
    a.cfg["settings"].update(tr_screen=True, tr_screen_port=8797); url = a.tr_screen_apply()
    import urllib.request
    try:
        page = urllib.request.urlopen(url, timeout=5).read().decode("utf-8")
        st_ = json.loads(urllib.request.urlopen(url.replace("/tr?", "/api/state?"), timeout=5).read())
        step("telefon sayfası açıldı ve son çeviriler hazır", "CANLI" in page and len(st_["translate"]["recent"]) >= 1,
             recent=[x["tr"][:40] for x in st_["translate"]["recent"][-2:]])
        terms_ = [t_ for x in st_["translate"]["recent"] for t_ in x.get("terms", [])]
        step("terimler bulundu (Black Tusk vb.)", any(t_["name"] == "Black Tusk" for t_ in terms_), terms=[t_["name"] for t_ in terms_][:6])
        edge = next((p_ for p_ in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe") if os.path.exists(p_)), None)
        if edge:
            subprocess.run([edge, "--headless=new", "--disable-gpu", "--window-size=420,820", "--virtual-time-budget=6000",
                            f"--screenshot={SHOTS / 'tr_05_phone.png'}", url], timeout=40)
    except Exception as e:
        step("telefon sayfası", False, e=repr(e))
    a._ts_ui()
    a.nb.select(a.tab_keys.index("translate")); shot("06_tab_new")
    a.lt_suggest("Agent, the Black Tusk have taken control of the Capitol Building.", "Ajan, Black Tusk Capitol Binası'nın kontrolünü ele geçirdi.")
    a.root.after(1200, s6)
def s6():
    tops = [w for w in a.root.winfo_children() if isinstance(w, app.tk.Toplevel)]
    step("düzeltme önerisi penceresi", bool(tops))
    if tops: shot("07_suggest", w=tops[-1]); tops[-1].destroy()
    a.apply_theme_pack("nightops"); a.root.after(2500, s7)
def s7():
    step("tema paketi uygulandı (Gece Operasyonu)", a.cfg["settings"]["ui_theme"] == "nightops" and app.PAL["accent"] == "#22d3ee")
    shot("08_theme_nightops")
    a.apply_theme_pack("blacktusk"); a.root.after(2500, s8)
def s8():
    a.nb.select(a.tab_keys.index("translate")); shot("09_theme_blacktusk")
    a.apply_theme_pack("dark")
    finish()
def finish():
    if res.get("done"): return
    res["done"] = True
    res["ok"] = all(s["ok"] for s in res["steps"]) and len(res["steps"]) >= 9
    (ROOT / "tests" / ".translate_result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    game.terminate(); a.on_close(force=True)
def guard(fn):
    def run():
        try: fn()
        except Exception as e:
            import traceback; traceback.print_exc(); step(fn.__name__ + " hata", False, e=repr(e)); finish()
    return run
for _n in ("s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"): globals()[_n] = guard(globals()[_n])
a.root.after(4000, s1); a.root.after(240000, finish)
a.root.mainloop()
print("RESULT:", "PASS" if res.get("ok") else "FAIL"); sys.exit(0 if res.get("ok") else 1)
