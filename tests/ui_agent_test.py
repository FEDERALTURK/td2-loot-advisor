"""Windows CI: Eksik Parçalar sekmesindeki 3D ajan — modeller, kıyafetler, ten, döndürme (video için ekranda oynatılır).

Doğrulamalar: 5 model ve 6 kıyafet yüklenir, seçim ayarlara kaydedilir, her modelde 8 yuva parçası vardır,
bir kare çizimi makul sürede biter. Ekran görüntüleri: shots/agent_*.png. Sonuç: RESULT: PASS / FAIL
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import app  # noqa: E402
import view3d  # noqa: E402

app.messagebox.askyesno = lambda *a, **k: False
app.messagebox.showinfo = lambda *a, **k: None
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
a = app.App()
fails, times = [], []


def ok(c, msg):
    print(("OK   " if c else "FAIL ") + msg, flush=True)
    if not c: fails.append(msg)


def shot(name):
    try:
        from PIL import ImageGrab
        a.root.update(); ImageGrab.grab().save(SHOTS / f"agent_{name}.png")
    except Exception as e:
        print("  (ekran görüntüsü alınamadı:", e, ")")


def zoom_shot(name):
    try:
        from PIL import ImageGrab
        av = a.agent3d.master; a.root.update()
        x, y = av.winfo_rootx(), av.winfo_rooty()
        ImageGrab.grab((x, y, x + av.winfo_width(), y + av.winfo_height())).save(SHOTS / f"agent_{name}.png")
    except Exception as e:
        print("  (ekran görüntüsü alınamadı:", e, ")")


def timed_render():
    t = time.perf_counter(); a.agent3d.render(); times.append((time.perf_counter() - t) * 1000)


def start():
    a.root.deiconify(); a.root.lift()
    a.nb.select(a.tab_keys.index("progress"))
    a.root.after(2500, lambda: models(0))


def models(i):
    av = a.agent3d
    if i == 0:
        ok(hasattr(a, "_agent_look"), "model/kıyafet seçici var")
        shot("0_tab")
    if i < len(view3d.MODELS):
        if i: a._agent_look["cycle"](1)
        ok(av.model == view3d.MODELS[i], f"model: {av.model}")
        tags = {f[2] for f in av.faces if f[2]}
        ok(set(view3d.SLOTS) <= tags, f"{av.model}: 8 yuva parçası")
        timed_render()
        a.root.after(1800, lambda: (zoom_shot(f"m{i}_{av.model}"), a.root.after(1700, lambda: models(i + 1))))
        return
    a._agent_look["cycle"](1)                                   # başa dön (operatör)
    ok(av.model == "operator", "◀ ▶ döngüsü başa döndü")
    a.root.after(800, lambda: outfits(0))


def outfits(i):
    cb = a._agent_look["outfit"]
    vals = list(cb.cget("values"))
    if i < len(vals):
        cb.set(vals[i]); a._agent_look["pick_outfit"]()
        ok(a.agent3d.outfit == list(view3d.THEMES)[i], f"kıyafet: {a.agent3d.outfit}")
        timed_render()
        a.root.after(1500, lambda: (zoom_shot(f"o{i}_{a.agent3d.outfit}") if i in (1, 3) else None, outfits(i + 1)))
        return
    a.root.after(500, lambda: skins(0))


def skins(i):
    if i < len(view3d.SKINS):
        a.agent3d.set_look(skin=i); timed_render()
        return a.root.after(700, lambda: skins(i + 1))
    a.agent3d.set_look(model="heavy", outfit="desert", skin=2)
    a._agent_look["label"].config(text=app.t("v3d.m_heavy"))
    a._agent_look["outfit"].set(app.t("v3d.o_desert")); a._agent_look["pick_outfit"]()
    a.agent3d.auto_spin = False
    a.root.after(400, lambda: rotate(0))


def rotate(i):                                                 # sürükleyerek döndürme gibi
    if i < 60:
        a.agent3d.yaw += 0.105; timed_render()
        return a.root.after(40, lambda: rotate(i + 1))
    zoom_shot("rotated_back")
    a.agent3d.auto_spin = True
    a.root.after(800, finish)


def finish():
    st = a.cfg["settings"]
    ok((st.get("agent_model"), st.get("agent_outfit"), st.get("agent_skin")) == ("heavy", "desert", 2), f"seçim kaydedildi: {st.get('agent_model')}, {st.get('agent_outfit')}, {st.get('agent_skin')}")
    avg, worst = sum(times) / len(times), max(times)
    print(f"render ms: ort {avg:.1f}, en kötü {worst:.1f}", flush=True)
    ok(avg < 25, "çizim hızı yeterli (ortalama < 25 ms)")
    shot("9_final")
    print("RESULT: " + ("PASS" if not fails else f"FAIL ({len(fails)})"), flush=True)
    a.root.after(800, a.root.destroy)


a.root.after(9000, start)
a.root.mainloop()
sys.exit(1 if fails else 0)
