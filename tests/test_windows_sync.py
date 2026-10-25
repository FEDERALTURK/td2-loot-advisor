"""Windows'ta ekran senkron testi (GitHub Actions windows-latest ya da gerçek bilgisayar).

Sahte bir "oyun penceresi" açılır (başlık: Tom Clancy's The Division 2) ve içinde gerçek bir eşya kartı gösterilir.
Program bu pencereyi bulmalı, yalnız onun alanını okumalı, profili pencerenin boyutundan hesaplamalı ve kartı tanımalı.
Pencere taşınıp yeniden boyutlandırılınca yeni alan ve profil bulunmalı.

    python tests/test_windows_sync.py
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAKE = r'''
import sys, tkinter as tk
from PIL import Image, ImageTk
w, h, x, y, img = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
root = tk.Tk(); root.title("Tom Clancy's The Division 2")
root.geometry(f"{w}x{h}+{x}+{y}"); root.configure(bg="black")
src = Image.open(img).convert("RGB")
k = min(w * 0.6 / src.width, h / src.height)                 # kart oranı korunur (oyun ekranındaki gibi)
pic = Image.new("RGB", (w, h), (12, 14, 18))
pic.paste(src.resize((int(src.width * k), int(src.height * k))), (int(w * 0.08), 0))
ph = ImageTk.PhotoImage(pic)
tk.Label(root, image=ph, bd=0, highlightthickness=0).place(x=0, y=0, relwidth=1, relheight=1)
root.attributes("-topmost", True)
root.after(60000, root.destroy)
root.mainloop()
'''


def spawn(w, h, x, y, img):
    f = ROOT / "tests" / ".fake_game.py"
    f.write_text(FAKE, encoding="utf-8")
    p = subprocess.Popen([sys.executable, str(f), str(w), str(h), str(x), str(y), str(img)])
    time.sleep(3.0)
    return p


def main():
    assert os.name == "nt", "Windows only"
    import display
    display.set_dpi_aware()
    import mss
    with mss.mss() as s:
        mons = s.monitors
    print("monitors:", mons)
    scr = mons[1]
    sample = ROOT / "tests" / "samples" / "stoner_lamg_3440x1440.png"
    ok = True

    # 1) oyun yokken: None, profil ana monitörden
    display._GW_CACHE["t"] = 0
    g0 = display.game_window(max_age=0)
    print("no game:", g0)
    ok &= g0 is None

    # 2) sahte oyun penceresi (ekranın sağ altına, ana monitörün tamamı değil)
    W = min(1000, scr["width"] - 80); H = min(700, scr["height"] - 90)
    p = spawn(W, H, scr["left"] + 60, scr["top"] + 50, sample)
    try:
        g = display.game_window(max_age=0)
        print("game window:", g)
        ok &= bool(g) and abs(g["width"] - W) <= 4 and abs(g["height"] - H) <= 4
        key, prof = display.profile_for(g["width"], g["height"])
        print("profile:", key, {k: prof[k] for k in ("ocr_scale", "threshold", "card_w", "ui")})
        ok &= prof.get("dynamic", False) or key in display.PROFILES

        # 3) programın kendi akışı: active_profile (yanlış kayıtlı profil otomatiğe dönmeli) + yakalama + tanıma
        import app
        st = {"res_profile": "3840x2160", "ocr_threshold": 170}
        k2, p2 = app.active_profile(st)
        print("stale profile 3840x2160 ->", k2)
        ok &= k2 == key
        app.apply_ocr_settings({**app.load_cfg()["settings"], "res_profile": "auto"})
        area = display.clamp_to_screen(g, mons)
        img = app.grab(area)
        box = app.find_card(img)
        card = img.crop(box) if box else img
        text, lines = app.read_card(card)
        item = app.GAME.recognize(text)
        print("read:", item["name"], item["kind"], item["slot"], list(item["attrs"])[:4])
        ok &= item["kind"] == "weapon" and len(item["attrs"]) >= 2

        # 4) pencere yeniden boyutlandı / taşındı → yeni alan bulunmalı
        p.terminate(); p.wait(5)
        W2 = min(820, scr["width"] - 200); H2 = min(600, scr["height"] - 170)
        p = spawn(W2, H2, scr["left"] + 150, scr["top"] + 120, sample)
        g2 = display.game_window(max_age=0)
        print("moved/resized:", g2)
        ok &= bool(g2) and abs(g2["width"] - W2) <= 4 and g2["left"] != g["left"]
        print("monitor_of:", display.monitor_of(g2, mons))
    finally:
        p.terminate()
        try: (ROOT / "tests" / ".fake_game.py").unlink()
        except Exception: pass
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
