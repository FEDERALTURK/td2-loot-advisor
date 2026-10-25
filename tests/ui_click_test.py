"""Windows CI: arka plan saati açıkken gerçek fare tıklaması, imleç ve akıcılık testi.

1) Menü sekmesinin içinde, ekranda şeffaf zemin rengine denk gelen bir nokta bulunur ve oraya GERÇEK bir Windows
   tıklaması (SendInput) gönderilir → sekme değişmeli (eskiden tıklama arka plan penceresine düşüyordu).
2) Arka plan penceresinin imleci programın imleciyle aynı olmalı.
3) Tk olay döngüsünün gecikmesi ölçülür (kasma): 50 ms'lik zamanlayıcının ortalama/en kötü gecikmesi.
Sonuç: tests/.click_result.json
"""
import ctypes
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import app

app.messagebox.askyesno = lambda *a, **k: False
OUT = ROOT / "tests" / ".click_result.json"
a = app.App()
res = {"watch": False}


def click(x, y):
    u = ctypes.windll.user32
    u.SetCursorPos(int(x), int(y))
    time.sleep(0.05)
    u.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(0x0004, 0, 0, 0, 0)


def find_gap_in_tab(tab_index):
    """Hedef sekmenin üstünde, ekranda zemin rengi (şeffaf anahtar) olan bir nokta."""
    import mss
    from PIL import Image
    nb = a.nb
    key = tuple(int(app.PAL["bg"][i:i + 2], 16) for i in (1, 3, 5))
    x0, y0 = nb.winfo_rootx(), nb.winfo_rooty()
    with mss.mss() as s:
        shot = s.grab({"left": x0, "top": y0, "width": nb.winfo_width(), "height": 60})
        img = Image.frombytes("RGB", shot.size, shot.rgb)
    cand = []
    for y in range(2, 58, 2):
        for x in range(2, nb.winfo_width() - 2, 2):
            try:
                if nb.index(f"@{x},{y}") != tab_index: continue
            except Exception:
                continue
            px = img.getpixel((x, y))
            cand.append((sum(abs(px[i] - key[i]) for i in range(3)), x, y))
    if not cand: return None
    d, x, y = min(cand)
    return (x0 + x, y0 + y, d)


def step_click():
    wb = getattr(a, "watch_bg", None)
    res["watch"] = bool(wb)
    res["root_cursor"] = str(a.root.cget("cursor"))
    if wb:
        res["watch_cursor"] = str(wb.cv.cget("cursor"))
    target = a.tab_keys.index("settings")
    g = find_gap_in_tab(target)
    res["gap"] = g
    if g:
        a.nb.select(0); a.root.update()
        click(g[0], g[1])
        a.root.after(800, lambda: check(target))
    else:
        a.root.after(100, step_lag)


def check(target):
    res["tab_after_click"] = a.nb.index(a.nb.select())
    res["click_ok"] = res["tab_after_click"] == target
    a.root.after(100, step_lag)


lags = []


def step_lag(n=[0], t=[0.0]):
    now = time.perf_counter()
    if t[0]: lags.append((now - t[0]) * 1000 - 50)
    t[0] = now
    n[0] += 1
    if n[0] < 200:                                   # ~10 sn, fareyi pencerede gezdirerek (saat akıcı modda)
        if n[0] % 10 == 0:
            ctypes.windll.user32.SetCursorPos(a.root.winfo_rootx() + 200 + (n[0] % 300), a.root.winfo_rooty() + 400)
        a.root.after(50, step_lag)
    else:
        lags.sort()
        res["lag_ms_avg"] = round(sum(lags) / len(lags), 1)
        res["lag_ms_p95"] = round(lags[int(len(lags) * 0.95)], 1)
        res["lag_ms_max"] = round(lags[-1], 1)
        a.root.after(200, step_transition)


def step_transition(i=[0], alphas=[]):
    """Sekme geçiş efekti: pencere saydamlığı değişmemeli, ışık çizgisi çizilmeli; ortasından ekran görüntüsü."""
    import mss
    from PIL import Image
    if i[0] == 0: res["fx_frames_before"] = a.fxbar.frames
    if i[0] >= 4:
        res["fx_frames"] = a.fxbar.frames - res["fx_frames_before"]
        res["alpha_values"] = sorted(set(alphas))
        OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
        print("RESULT", json.dumps(res), flush=True)
        a.root.after(500, a.root.destroy); return
    tabs = ["builds", "stash", "settings", "dash"]
    a.nb.select(a.tab_keys.index(tabs[i[0]]))
    shots = (ROOT / "shots"); shots.mkdir(exist_ok=True)
    def grab(tag):
        nb = a.nb
        with mss.mss() as s:
            g = s.grab({"left": nb.winfo_rootx(), "top": nb.winfo_rooty(), "width": nb.winfo_width(), "height": 70})
        Image.frombytes("RGB", g.size, g.rgb).save(shots / f"fx_{i[0]}_{tag}.png")
        alphas.append(round(float(a.root.attributes("-alpha")), 2))
    a.root.after(120, lambda: grab("a")); a.root.after(330, lambda: grab("b"))
    i[0] += 1
    a.root.after(900, step_transition)


a.root.after(9000, step_click)
a.root.mainloop()
