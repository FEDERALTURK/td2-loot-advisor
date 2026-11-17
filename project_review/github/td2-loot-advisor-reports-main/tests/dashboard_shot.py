"""Gösterge sekmesi uçtan uca: yerel sunucu (app/server/dev_server.mjs) + farklı sürümlerden sahte açılışlar +
hesap/öneri verisi + gerçek panel penceresi. Bildirim metni de denetlenir.
    python tests/dashboard_shot.py   (app/ = herkese açık program deposu)
"""
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
# The reports-panel checkout is intentionally a partial mirror and may not
# contain the public app/server fixture.  Use the workspace server fixture
# when it is available instead of failing before the dashboard is exercised.
if not (APP / "server" / "dev_server.mjs").exists():
    APP = Path(__file__).resolve().parents[4]
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
sys.path.insert(0, str(APP)); sys.path.insert(0, str(ROOT / "panel"))
port = 8893
srv = subprocess.Popen(["node", str(APP / "server" / "dev_server.mjs"), str(port)], stdout=subprocess.PIPE, text=True)
_, _, ADMIN, _ = srv.stdout.readline().split()
URL = f"http://127.0.0.1:{port}"
import tasks_live  # noqa: E402

fails = []


def ok(c, m):
    print(("OK   " if c else "FAIL ") + m, flush=True)
    if not c: fails.append(m)


# sahte oyuncular: 6.0.1 (7 açılış), 6.0.2 (12 açılış), 6.0.0 (sayılmaz)
for ver, n in (("6.0.1", 7), ("6.0.2", 12)):
    for i in range(n): tasks_live.fetch_live(URL, None, app_version=ver, start=True)
    for i in range(n * 3): tasks_live.fetch_live(URL, None, app_version=ver)
tasks_live.fetch_live(URL, None)
req = urllib.request.Request(URL + "/v1/suggest", data=json.dumps({"client": "player-a-1111", "app": "6.0.2", "en": "Head to the safe house.",
                                                                     "old": "Güvenli eve git.", "new": "Sığınağa git."}).encode(),
                             headers={"content-type": "application/json"}, method="POST")
urllib.request.urlopen(req, timeout=10).read()

cfg = Path(tempfile.mkdtemp()) / "panel.json"
cfg.write_text(json.dumps({"repo": "", "token": "", "acc_url": URL, "admin_token": ADMIN, "notify_since": int(time.time()) - 3600}), encoding="utf-8")
os.environ["TD2_PANEL_CONFIG"] = str(cfg)
os.environ["TD2_PANEL_NOLOCK"] = "1"
import tkinter as tk  # noqa: E402
import panel  # noqa: E402
from tray import summarize  # noqa: E402
panel.messagebox.askyesno = lambda *a, **k: False
root = tk.Tk()
P = panel.Panel(root)
got = {}


def shot(name):
    try:
        from PIL import ImageGrab
        root.update(); x, y = root.winfo_rootx(), root.winfo_rooty()
        ImageGrab.grab((x, y, x + root.winfo_width(), y + root.winfo_height())).save(SHOTS / f"panel_{name}.png")
    except Exception as e:
        print("  (ekran görüntüsü alınamadı:", e, ")")


def s1():
    if getattr(P, "_settings_win", None):
        try: P._settings_win.destroy()
        except Exception: pass
    P.main_nb.select(P.dash.f)
    P.dash.refresh(done=lambda d: got.update(d=d))
    root.after(3500, s2)


def s2():
    d = got.get("d") or {}
    vers = {r["version"]: r["starts"] for r in (d.get("usage") or {}).get("versions_7d", [])}
    ok(vers == {"6.0.2": 12, "6.0.1": 7}, f"sürüm dağılımı: {vers}")
    ok(P.dash.card["starts"][0].cget("text") == "19", "bugün açılış kartı: 19")
    ok(P.dash.card["suggest"][0].cget("text") == "1", "bekleyen öneri kartı: 1")
    ok(P.dash.health is True and "Ayakta" in P.dash.l_health.cget("text"), "sunucu ayakta")
    ok(summarize(d.get("events"), 2) == "2 yeni rapor, 1 çeviri önerisi", "bildirim metni: " + summarize(d.get("events"), 2))
    P.goto("suggest"); root.update()
    ok(P.main_nb.select() == str(P.sug_tab.f), "karta tıklayınca ilgili sekme")
    P.main_nb.select(P.dash.f); root.update(); root.after(800, s3)


def s3():
    shot("dashboard")
    root.after(300, root.destroy)


root.after(2000, s1)
root.mainloop()
srv.terminate()
print("RESULT:", "PASS" if not fails else f"FAIL ({len(fails)})")
sys.exit(1 if fails else 0)

