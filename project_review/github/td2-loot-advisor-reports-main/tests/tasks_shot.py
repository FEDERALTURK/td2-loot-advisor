"""Panel 'Topluluk görevleri' sekmesi uçtan uca: yerel sunucu (app/server/dev_server.mjs) + birkaç sahte oyuncunun
gönderdiği görevler + gerçek panel penceresi. Gizleme ve Türkçe düzeltmenin herkese açık listeye yansıması.
    python tests/tasks_shot.py   (app/ = herkese açık program deposu)
"""
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
sys.path.insert(0, str(APP)); sys.path.insert(0, str(ROOT / "panel"))
port = 8892
srv = subprocess.Popen(["node", str(APP / "server" / "dev_server.mjs"), str(port)], stdout=subprocess.PIPE, text=True)
_, _, ADMIN, _ = srv.stdout.readline().split()
URL = f"http://127.0.0.1:{port}"
import tasks_live  # noqa: E402

samples = json.loads((APP / "tests" / "samples" / "tasks" / "map_projects_panel.json").read_text())["lines"]
weekly = tasks_live.extract(samples)
tr_w = {"title": "Haftalık Legendary Görevi", "subtitle": "Legendary Roosevelt Adası",
        "desc": "Roosevelt Adası'na taşınan özel kuvvetleri yenebilecek her ajan için özel bir eşyamız var.",
        "objective": "Legendary zorlukta Roosevelt Adası görevini tamamlayın"}
daily = {"title": "Daily Project", "subtitle": "Black Tusk Agitation", "desc": "Black Tusk patrols are getting bolder near the Capitol.",
         "objective": "Defeat 50 Black Tusk enemies", "total": 50, "rewards": ["Exotic Cache"], "category": "project", "period": "daily"}
tr_d = {"title": "Günlük Proje", "subtitle": "Black Tusk Kışkırtması", "objective": "50 Black Tusk düşmanını yen"}
bounty = {"title": "Bounty: Ripper", "subtitle": "Downtown West", "objective": "Eliminate the bounty target Ripper",
          "category": "bounty", "period": "other"}
for who, items in (("player-aaaa-1111", [(weekly, tr_w), (daily, tr_d)]), ("player-bbbb-2222", [(weekly, tr_w), (daily, tr_d)]),
                   ("player-cccc-3333", [(weekly, tr_w), (bounty, None)]), ("player-dddd-4444", [(daily, {**tr_d, "objective": "50 Black Tusk öldür"})])):
    s = tasks_live.Submitter(URL, who, None)
    for task, tr in items: s.submit(task, tr, "5.1.8", wait=True)
live0, _ = tasks_live.fetch_live(URL)

cfg = Path(tempfile.mkdtemp()) / "panel.json"
cfg.write_text(json.dumps({"repo": "", "token": "", "acc_url": URL, "admin_token": ADMIN}), encoding="utf-8")
os.environ["TD2_PANEL_CONFIG"] = str(cfg)
os.environ["TD2_PANEL_NOLOCK"] = "1"          # kilit ayrı testte (tests/lock_test.py)
import tkinter as tk  # noqa: E402
from tkinter import messagebox  # noqa: E402
import panel  # noqa: E402
messagebox.askyesno = lambda *a, **k: True
messagebox.showinfo = lambda *a, **k: None
root = tk.Tk()
p = panel.Panel(root)
fails = []
def ok(c, m):
    print(("OK   " if c else "FAIL ") + m, flush=True)
    if not c: fails.append(m)
def shot(name):
    try:
        from PIL import ImageGrab
        root.update(); x, y = root.winfo_rootx(), root.winfo_rooty()
        ImageGrab.grab(bbox=(x, y, x + root.winfo_width(), y + root.winfo_height())).save(SHOTS / f"panel_{name}.png")
    except Exception as e: print("shot", e)
T = p.tasks_tab
ok(len(live0["tasks"]) == 2, "herkese açık liste: 2 görev (tek oyunculu ödül avı yok)")
def s1():
    if getattr(p, "_settings_win", None):
        try: p._settings_win.destroy()
        except Exception: pass
    p.main_nb.select(p.tasks_tab.f)
    root.after(3000, s2)
def s2():
    ok(T.stat["all"].cget("text") == "3" and T.stat["public"].cget("text") == "2" and T.stat["waiting"].cget("text") == "1", "istatistik: 3 toplanan, 2 açık, 1 bekleyen")
    key = tasks_live.task_key(daily["title"], daily["objective"])
    T.tv.selection_set(key); T.show()
    txt = T.detail.get("1.0", "end")
    ok("3 oyuncu" in txt and "Türkçe ×2" in txt and "Türkçe ×1" in txt, "ayrıntı: oyuncu sayısı ve farklı çeviriler")
    shot("tasks_01_list")
    T.only_wait.set(True); T.fill()
    ok(len(T.tv.get_children()) == 1, "yalnız onay bekleyenler süzgeci")
    T.only_wait.set(False); T.fill()
    T.tv.selection_set(tasks_live.task_key(weekly["title"], weekly["objective"])); T.show()
    T.toggle_hide()
    root.after(2500, s3)
def s3():
    live, _ = tasks_live.fetch_live(URL)
    ok(len(live["tasks"]) == 1 and live["tasks"][0]["title"] == "Daily Project", "panelden gizlenen görev herkese açık listeden çıktı")
    T.tv.selection_set(tasks_live.task_key(daily["title"], daily["objective"])); T.show()
    T.edit_tr()
    root.after(800, s4)
def s4():
    w = T.edit_win
    texts = [x for x in w.winfo_children() if isinstance(x, tk.Text)]
    texts[-1].delete("1.0", "end"); texts[-1].insert("1.0", "50 Black Tusk düşmanını etkisiz hâle getir")
    shot("tasks_02_edit")
    btn = [b for fr in w.winfo_children() if isinstance(fr, tk.ttk.Frame) for b in fr.winfo_children()][-1]
    btn.invoke()
    root.after(2500, s5)
def s5():
    live, _ = tasks_live.fetch_live(URL)
    t = live["tasks"][0]
    ok(t["tr"]["objective"] == "50 Black Tusk düşmanını etkisiz hâle getir" and t.get("tr_source", "admin") , "panel düzeltmesi oyunculara giden listede")
    m = tasks_live.Memory(live)
    ok(m.get("Defeat 50 Black Tusk enemies") == "50 Black Tusk düşmanını etkisiz hâle getir", "çeviri hafızasına düzeltilmiş hâli girdi")
    shot("tasks_03_after")
    for who in ("sug-aaaa-1111", "sug-bbbb-2222"):
        ok(tasks_live.suggest(URL, who, "Head to the White House and talk to Manny.", "Beyaz Saray'a gidin.", "White House'a git ve Manny ile konuş.", "5.1.9"), "öneri gönderildi " + who)
    p.main_nb.select(p.sug_tab.f); p.sug_tab.refresh()
    root.after(2500, s6)
def s6():
    S = p.sug_tab
    kids = S.tv.get_children()
    ok(len(kids) == 1 and S.tv.item(kids[0], "values")[0] in (2, "2"), "panel: öneri 2 oyuncudan, tek satır")
    S.tv.selection_set(kids[0]); root.update(); S.show()
    S.edit.delete("1.0", "end"); S.edit.insert("1.0", "White House'a git ve Manny ile konuş!")
    shot("tasks_04_suggest")
    S.decide(True)
    root.after(2500, s7)
def s7():
    live, _ = tasks_live.fetch_live(URL)
    ok(live["lines"] == [{"en": "Head to the White House and talk to Manny.", "tr": "White House'a git ve Manny ile konuş!"}], "düzenlenerek onaylanan öneri herkesin listesinde")
    ok(tasks_live.Memory(live).get("head to the white house and talk to manny") == "White House'a git ve Manny ile konuş!", "çeviri hafızasında")
    root.destroy()
root.after(1500, s1)
root.after(60000, root.destroy)
root.mainloop()
srv.terminate()
print("RESULT:", "FAIL " + str(fails) if fails else "PASS"); sys.exit(1 if fails else 0)

