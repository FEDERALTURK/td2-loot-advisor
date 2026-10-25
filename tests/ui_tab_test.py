"""Windows CI: sekme göstergesi. Sekmeler değiştirilir; çizgi yeni sekmenin altına oturmalı, akıcı (yeterli kare)
çizilmeli, animasyon sırasında olay döngüsü donmamalı. Ekran görüntüleri iş akışından alınır.
Sonuç: tests/.tab_result.json"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import app
app.messagebox.askyesno = lambda *a, **k: False
OUT = ROOT / "tests" / ".tab_result.json"
a = app.App()
res = {"switches": []}
seq = ["settings", "stash", "builds", "dash", "stats", "history", "dash"]


def switch(i=0):
    if i >= len(seq):
        OUT.write_text(json.dumps(res, indent=1), encoding="utf-8"); print("RESULT", json.dumps(res), flush=True)
        a.root.after(800, a.root.destroy); return
    fx = a.fxbar
    f0, t0 = fx.frames, time.perf_counter()
    a.nb.select(a.tab_keys.index(seq[i]))
    gaps, last = [], [time.perf_counter()]
    def probe(n=0):
        now = time.perf_counter(); gaps.append((now - last[0]) * 1000); last[0] = now
        if n < 30: a.root.after(10, lambda: probe(n + 1))
    probe()
    def done():
        spans = fx.debug.get("spans", {}); new = fx.debug.get("new")
        target = spans.get(str(new)); line = fx.bar.coords(fx.line) if fx.bar else None
        on_tab = bool(target and line and abs(line[0] - (target[0] + 4)) < 3 and abs(line[2] - (target[1] - 4)) < 3)
        res["switches"].append({"tab": seq[i], "frames": fx.frames - f0, "on_tab": on_tab, "why": fx.debug.get("why"),
                                "max_gap_ms": round(max(gaps), 1), "visible": bool(fx.bar and fx.bar.winfo_ismapped())})
        a.root.after(900, lambda: switch(i + 1))
    a.root.after(fx.duration + 150, done)


a.root.after(9000, switch)
a.root.mainloop()
