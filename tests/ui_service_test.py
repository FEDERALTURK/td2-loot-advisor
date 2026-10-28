"""Windows CI: hizmet uçtan uca — sahte oyun penceresi açılınca tarama kendiliğinden başlar, kart okunur, ekran
durumu öğrenilir, oturum sayılır, yerel API (HTTP + WebSocket) olayları yayınlar, Stream Deck komutu çalışır,
bildirimler (sahte) gider; oyun kapanınca tarama durur ve oturum özeti kaydedilir. Ayrıca tepsi ve Windows ile başlat.
    python tests/ui_service_test.py   → tests/.service_result.json + shots/svc_*.png
"""
import base64, json, os, socket, struct, subprocess, sys, threading, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
os.environ["TD2_NO_WELCOME"] = "1"
for f in ("sessions.json", "screen_states.json", "account.dat"): (ROOT / f).unlink(missing_ok=True)

import features  # noqa: E402
features.FEATURES["local_api"] = features.FEATURES["push_notify"] = "free"     # test: premium kilidi olmadan
import app, notify, service  # noqa: E402
from PIL import ImageGrab  # noqa: E402
from test_windows_sync import FAKE  # noqa: E402

pushed = []
class _R:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *a): pass
def fake_open(req, timeout=10):
    pushed.append({"url": req.full_url, "title": req.get_header("Title"), "body": (req.data or b"").decode("utf-8", "ignore")}); return _R()
notify.MIN_GAP = 0.1
_orig_init = notify.Notifier.__init__
def _init(self, opener=None): _orig_init(self, opener=fake_open)
notify.Notifier.__init__ = _init

app.messagebox.askyesno = lambda *a, **k: False
app.messagebox.showinfo = app.messagebox.showwarning = lambda *a, **k: None
a = app.App()
st = a.cfg["settings"]
st.update(api_on=True, api_port=8799, api_lan=False, api_control=True, svc_auto_run=True, smart_scan=True, scan_mode="auto",
          push_on=True, push_topic="td2-ci-" + "x" * 16, push_webhook="", rpc_on=False, only_game_active=False)
res = {"steps": []}
def step(name, ok, **kw):
    res["steps"].append({"name": name, "ok": bool(ok), **kw}); print(("OK   " if ok else "FAIL ") + name, kw, flush=True)
def shot(name, w=None):
    w = w or a.root
    try:
        if w is a.root: a.root.deiconify(); a.root.lift(); a.root.attributes("-topmost", True); a.root.update(); time.sleep(0.6)
        w.update(); x, y = w.winfo_rootx(), w.winfo_rooty()
        ImageGrab.grab(bbox=(x, y, x + w.winfo_width(), y + w.winfo_height()), all_screens=True).save(SHOTS / f"{name}.png")
        a.root.attributes("-topmost", False)
    except Exception as e: print("shot failed", e)

events = []
def ws_listen():
    try:
        sk = socket.create_connection(("127.0.0.1", 8799), timeout=120)
        key = base64.b64encode(os.urandom(16)).decode()
        sk.sendall((f"GET /ws?t={st['api_token']} HTTP/1.1\r\nHost: 127.0.0.1:8799\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf: buf += sk.recv(1)
        while True:
            h = sk.recv(2)
            if len(h) < 2: break
            n = h[1] & 0x7F
            if n == 126: n = struct.unpack(">H", sk.recv(2))[0]
            elif n == 127: n = struct.unpack(">Q", sk.recv(8))[0]
            d = b""
            while len(d) < n: d += sk.recv(n - len(d))
            events.append(json.loads(d))
    except Exception as e:
        events.append({"type": "ws_error", "e": str(e)})
game = None

def s0():
    a._push_configure(); a.api_apply()
    step("yerel API açıldı", a.api is not None and a.api.running)
    threading.Thread(target=ws_listen, daemon=True).start()
    step("tepsi simgesi (pystray)", bool(a.tray and a.tray.available), tray=bool(a.tray))
    try:
        cmd = '"C:\\\\x\\\\td2.exe" --tray'
        ok_on = service.autostart_set(True, cmd); got = service.autostart_get(); ok_off = service.autostart_set(False)
        step("Windows ile başlat (kayıt defteri, kullanıcı düzeyi) aç/kapat", ok_on and got and ok_off and not service.autostart_get())
    except Exception as e: step("Windows ile başlat", False, e=str(e))
    a.root.after(1500, s1)

def s1():
    global game
    f = ROOT / "tests" / ".fake_game.py"; f.write_text(FAKE, encoding="utf-8")
    game = subprocess.Popen([sys.executable, str(f), "1280", "720", "40", "40", str(ROOT / "tests/samples/stoner_lamg_3440x1440.png")])
    a.root.after(20000, s2)

def s2():
    step("oyun algılandı", a.game_on)
    step("tarama oyunla kendiliğinden başladı", a.running and a._auto_started)
    s = a.sessions.stats()
    step("kart okundu ve oturuma sayıldı", s["scanned"] >= 1, session=s, last=(a.comp_state.get("item") or {}).get("name"))
    step("ekran durumu: menü imzası öğrenildi", a.screen.learned() >= 1, learned=a.screen.learned(), state=a.game_state)
    step("başlıkta oyun rozeti", any(str(c[0]).startswith("🎮") for c in a.banner.chips), chips=[c[0] for c in a.banner.chips][:4])
    with urllib.request.urlopen(f"http://127.0.0.1:8799/api/state?t={st['api_token']}", timeout=5) as r: js = json.loads(r.read())
    step("API durumu: oyun + son karar", js["game"]["running"] and js["last"] and js["session"]["scanned"] >= 1, game=js["game"])
    kinds = [e.get("type") for e in events]
    step("WebSocket: hello + game + scan olayları", "hello" in kinds and "game" in kinds and "scan" in kinds, kinds=kinds[:12])
    shot("svc_01_running")
    a.select_page("settings"); a.select_settings_page("service")
    a.root.after(1500, s3)

def s3():
    shot("svc_02_settings")
    def deck(cmd):
        with urllib.request.urlopen(f"http://127.0.0.1:8799/deck/{cmd}?t={st['api_token']}", timeout=10) as r: return json.loads(r.read())
    out = {}
    def work():                                   # Stream Deck başka bir süreçtir: istekler arayüz iş parçacığından yapılmaz
        out["stop"] = deck("stop"); out["stop_run"] = a.running
        out["start"] = deck("start"); out["start_run"] = a.running
    th = threading.Thread(target=work, daemon=True); th.start()
    def check():
        if th.is_alive(): return a.root.after(300, check)
        step("Stream Deck komutu: durdur", out["stop"].get("ok") and out["stop"].get("running") is False and not out["stop_run"], d=out["stop"])
        step("Stream Deck komutu: başlat", out["start"].get("ok") and out["start"].get("running") is True and out["start_run"], d=out["start"])
        s3b()
    a.root.after(300, check)

def s3b():
    a.root.after(3000, s4)

def s4():
    game.terminate()
    a.root.after(8000, s5)

def s5():
    step("oyun kapanınca tarama durdu", not a.game_on and not a.running)
    ss = service.SessionLog(app.SESSIONS_PATH).sessions
    step("oturum dosyaya kaydedildi", bool(ss) and ss[-1]["scanned"] >= 1, last=ss[-1] if ss else None)
    titles = [p["title"] or "" for p in pushed]
    step("bildirim: oturum özeti gönderildi", any(p["url"].endswith(st["push_topic"]) for p in pushed) and len(pushed) >= 1,
         n=len(pushed), titles=titles[:5])
    finish()

def finish():
    if res.get("done"): return
    res["done"] = True
    res["ok"] = all(s["ok"] for s in res["steps"]) and len(res["steps"]) >= 15
    (ROOT / "tests" / ".service_result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    try: game and game.terminate()
    except Exception: pass
    a.on_close(force=True)

def guard(fn):
    def run():
        try: fn()
        except Exception as e:
            import traceback; traceback.print_exc(); step(fn.__name__ + " hata", False, e=repr(e)); finish()
    return run
for _n in ("s0", "s1", "s2", "s3", "s3b", "s4", "s5"): globals()[_n] = guard(globals()[_n])
a.root.after(4000, s0)
a.root.after(150000, finish)
a.root.mainloop()
print("RESULT:", "PASS" if res.get("ok") else "FAIL"); sys.exit(0 if res.get("ok") else 1)
