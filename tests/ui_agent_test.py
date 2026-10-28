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


SPRITE = False


def start():
    global SPRITE
    SPRITE = getattr(a.agent3d, "sprite", False)
    print("görünüm:", "gerçekçi kareler" if SPRITE else "çokgen", flush=True)
    a.root.deiconify(); a.root.lift()
    a.select_page("progress")
    a.root.after(2500, lambda: models(0))


def models(i):
    av = a.agent3d
    if i == 0:
        ok(hasattr(a, "_agent_look"), "model/kıyafet seçici var")
        shot("0_tab")
    mlist = av.models if SPRITE else view3d.MODELS
    if i == 0: ok(not SPRITE or len(mlist) == 5, f"gerçekçi ajanlar yüklendi: {mlist}")
    if i < len(mlist):
        if i: a._agent_look["cycle"](1)
        ok(av.model == mlist[i], f"model: {av.model}")
        if SPRITE:
            seen = set()
            for f in range(0, av.n, 6): seen |= set(av.info["anchors"][f])
            ok(set(view3d.SLOTS) <= seen, f"{av.model}: 8 yuva maskesi")
        else:
            tags = {f[2] for f in av.faces if f[2]}
            ok(set(view3d.SLOTS) <= tags, f"{av.model}: 8 yuva parçası")
        timed_render()
        a.root.after(1800, lambda: (zoom_shot(f"m{i}_{av.model}"), a.root.after(1700, lambda: models(i + 1))))
        return
    a._agent_look["cycle"](1)                                   # başa dön (operatör)
    ok(av.model == "operator", "◀ ▶ döngüsü başa döndü")
    a.root.after(800, (lambda: sprite_extra()) if SPRITE else (lambda: outfits(0)))


def sprite_extra():
    av = a.agent3d
    st = {s: ("ok" if k % 2 else "miss") for k, s in enumerate(view3d.SLOTS)}
    av.set_status(st, None); timed_render()
    picked = []; av.on_pick = picked.append
    w, h, k, ox, oy, dw, dh = av._geom(); ax, ay, _ = av.info["anchors"][av.frame]["Chest"]
    class E: pass
    e = E(); e.x, e.y = int(ox + ax * k), int(oy + ay * k)
    av._press(e); av._release(e)
    ok(picked == ["Chest"], f"tıklama doğru yuvayı seçti: {picked}")
    av.on_pick = a._pick_slot3d
    for _ in range(2): a._agent_look["cycle"](1)                # heavy
    zoom_shot("tinted")
    av.auto_spin = False
    a.root.after(400, lambda: rotate(0))


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
        if SPRITE: a.agent3d.frame = (a.agent3d.frame + 1) % a.agent3d.n
        else: a.agent3d.yaw += 0.105
        timed_render()
        return a.root.after(60 if SPRITE else 40, lambda: rotate(i + 1))
    zoom_shot("rotated_back")
    a.agent3d.auto_spin = True
    a.root.after(800, finish)


def finish():
    st = a.cfg["settings"]
    if SPRITE: ok(st.get("agent_model") == "heavy", f"seçim kaydedildi: {st.get('agent_model')}")
    else: ok((st.get("agent_model"), st.get("agent_outfit"), st.get("agent_skin")) == ("heavy", "desert", 2), f"seçim kaydedildi: {st.get('agent_model')}, {st.get('agent_outfit')}, {st.get('agent_skin')}")
    avg, worst = sum(times) / len(times), max(times)
    print(f"render ms: ort {avg:.1f}, en kötü {worst:.1f}", flush=True)
    ok(avg < 25, "çizim hızı yeterli (ortalama < 25 ms)")
    shot("9_final")
    print("RESULT: " + ("PASS" if not fails else f"FAIL ({len(fails)})"), flush=True)
    a.root.after(800, a.root.destroy)


a.root.after(9000, start)
a.root.mainloop()
sys.exit(1 if fails else 0)
