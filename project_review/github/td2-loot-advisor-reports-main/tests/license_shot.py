"""Panel 'Kullanıcılar ve lisanslar' sekmesi uçtan uca: yerel hesap sunucusu (app/server/dev_server.mjs, sahte Discord)
+ birkaç kullanıcı girişi + gerçek panel penceresi. Anahtar üretme, davet kodu, cihaz sıfırlama, iptal, engelleme.
    python tests/license_shot.py   (app/ = herkese açık program deposu)
"""
import json, os, subprocess, sys, tempfile, threading, urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
sys.path.insert(0, str(APP)); sys.path.insert(0, str(ROOT / "panel"))
port = 8891
srv = subprocess.Popen(["node", str(APP / "server" / "dev_server.mjs"), str(port)], stdout=subprocess.PIPE, text=True)
_, _, ADMIN, PUB = srv.stdout.readline().split()
URL = f"http://127.0.0.1:{port}"
import account  # noqa: E402

def browser(user):
    def open_url(u):
        st = parse_qs(urlparse(u).query)["state"][0]
        threading.Thread(target=lambda: urllib.request.urlopen(f"{URL}/fake/discord?state={st}&user={user}").read(), daemon=True).start()
    return open_url
tmp = tempfile.mkdtemp()
users = {}
for name in ("Soner", "AgentKeener", "Faye", "Brenda"):
    acc = account.Account(os.path.join(tmp, name + ".dat"), URL); acc.login(open_url=browser(name), timeout=20); users[name] = acc
def admin(path, body=None):
    req = urllib.request.Request(f"{URL}/v1/admin/{path}", data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Admin " + ADMIN, "Content-Type": "application/json"}, method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req) as r: return json.loads(r.read())
k = admin("licenses", {"count": 3, "days": 30, "note": "yayın çekilişi"})["keys"]
users["Soner"].redeem(k[0]); users["Faye"].redeem(k[1])
inv = admin("invites", {"uses": 10, "days": 7, "valid_days": 30, "note": "Discord sunucusu"})["code"]
users["AgentKeener"].redeem(inv)

cfg = Path(tmp) / "panel.json"
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
L = p.lic
def s1():
    if getattr(p, "_settings_win", None):
        try: p._settings_win.destroy()
        except Exception: pass
    p.main_nb.select(p.lic.f)
    root.after(3000, s2)
def s2():
    ok(L.stat["accounts"].cget("text") == "4", "istatistik: 4 hesap")
    ok(len(L.tv_u.get_children()) == 4, "kullanıcı listesi")
    ok(len(L.tv_l.get_children()) == 4, "lisans listesi (3 anahtar + 1 davet)")
    ok(len(L.tv_i.get_children()) == 1, "davet listesi")
    L.nb.select(1); shot("lic_01_licenses")
    L.k_n.set("5"); L.k_days.set(""); L.k_note.set("Gumroad dışı satış"); L.create_keys()
    root.after(3000, s3)
def s3():
    keys = L.out.get("1.0", "end").split()
    ok(len(keys) == 5 and all(x.startswith("TD2K-") for x in keys), "5 süresiz anahtar üretildi ve gösterildi")
    shot("lic_02_created")
    lic = next(i for i in L.tv_l.get_children() if L.tv_l.item(i, "values")[3] == "Soner")
    L.tv_l.selection_set(lic); L.lic_action("reset_devices")
    root.after(2500, s4)
def s4():
    lic = next(i for i in L.tv_l.get_children() if L.tv_l.item(i, "values")[3] == "Faye")
    L.tv_l.selection_set(lic); L.lic_action("revoke")
    root.after(2500, s5)
def s5():
    j = users["Faye"].refresh(); ok(j["tier"] == "free", "panelden iptal → kullanıcı premium kaybetti")
    u = next(i for i in L.tv_u.get_children() if L.tv_u.item(i, "values")[1] == "Brenda")
    L.tv_u.selection_set(u); L.toggle_ban()
    root.after(2500, s6)
def s6():
    try: users["Brenda"].refresh(); ok(False, "engelleme")
    except account.AuthError as e: ok(e.code == "unauthorized", "panelden engelleme → oturum kapandı")
    L.nb.select(0); root.after(800, lambda: (shot("lic_03_users"), L.nb.select(3), root.after(800, s7)))
def s7():
    acts = [L.tv_a.item(i, "values")[2] for i in L.tv_a.get_children()]
    ok("ban" in acts and "revoke" in acts and "create_keys" in acts and "reset_devices" in acts, "denetim kaydı: " + ",".join(acts[:8]))
    shot("lic_04_audit")
    root.destroy()
root.after(1500, s1)
root.after(60000, root.destroy)
root.mainloop()
srv.terminate()
print("RESULT:", "FAIL " + str(fails) if fails else "PASS"); sys.exit(1 if fails else 0)

