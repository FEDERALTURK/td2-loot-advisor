"""Panel kilidi ve kendini güncelleme testi.
    python tests/lock_test.py
1) lock.py: şifreleme, yanlış PIN bekleme süresi.
2) Gerçek panel penceresi: ilk açılışta PIN oluşturma → belirteçler diskte PIN+DPAPI ile şifreli → yeniden açılışta kilitli,
   yanlış denemeler, doğru PIN ile belirteçler geri gelir. Ekran görüntüleri: shots/panel_lock_*.png
3) selfupdate.py: sahte GitHub (özel depo sürümleri + S3 benzeri yönlendirme), özet doğrulama, exe değiştirme.
"""
import hashlib
import json
import os
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "panel"))
import lock  # noqa: E402
import selfupdate  # noqa: E402

fails = []


def ok(c, m):
    print(("OK   " if c else "FAIL ") + m, flush=True)
    if not c: fails.append(m)


# ---------------------------------------------------------------- 1) lock.py
rec, key = lock.make("482913")
ok("482913" not in json.dumps(rec), "PIN kayıtta yok")
enc = lock.encrypt(key, "ghp_secret-token-123")
ok(enc.startswith(lock.PREFIX) and "secret" not in enc and lock.decrypt(key, enc) == "ghp_secret-token-123", "şifrele / çöz")
k2, _ = lock.check(rec, "482913"); ok(k2 == key, "doğru PIN aynı anahtarı verir")
bad = enc[:-6] + ("A" if enc[-6] != "A" else "B") + enc[-5:]
try: lock.decrypt(key, bad); ok(False, "bozulmuş veri reddedilmeli")
except ValueError: ok(True, "bozulmuş veri reddedildi (HMAC)")
t0 = 1_000_000.0
for i in range(lock.FREE_TRIES - 1):
    k, w = lock.check(rec, "000000", now=t0); assert k is None and w == 0
k, w = lock.check(rec, "000000", now=t0)
ok(k is None and w == 30, f"{lock.FREE_TRIES}. yanlışta 30 sn bekleme ({w})")
k, w = lock.check(rec, "482913", now=t0 + 5)
ok(k is None and w == 25, "beklerken doğru PIN bile kabul edilmez")
k, w = lock.check(rec, "111111", now=t0 + 31)
ok(w == 60, "sonraki yanlışta süre ikiye katlanır")
k, w = lock.check(rec, "482913", now=t0 + 200)
ok(k == key and rec["fails"] == 0, "süre dolunca doğru PIN açar, sayaç sıfırlanır")
ok(not lock.valid_pin("12345") and not lock.valid_pin(" 123456") and lock.valid_pin("abc123"), "PIN kuralı: en az 6, boşluksuz")

# ---------------------------------------------------------------- 3) selfupdate.py
EXE_BYTES = b"MZ" + os.urandom(4096)
SHA = hashlib.sha256(EXE_BYTES).hexdigest()
state = {"sums": f"{SHA}  TD2RaporPaneli.exe\nffff  other.exe\n", "auth_on_s3": []}


class GH(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        base = f"http://127.0.0.1:{self.server.server_port}"
        if self.path.startswith("/repos/o/r/releases?"):
            rel = lambda tag, n: {"tag_name": tag, "draft": False, "body": "Notlar " + tag, "assets": [
                {"name": "TD2RaporPaneli.exe", "url": f"{base}/api/assets/{n}1", "size": len(EXE_BYTES)},
                {"name": "SHA256SUMS", "url": f"{base}/api/assets/{n}2", "size": 10}]}
            data = [rel("panel-v1.5.1", 1), rel("panel-v1.4.0", 2), rel("arsiv-v5.0", 3), rel("panel-v9.9.9-evil", 4)]
            b = json.dumps(data).encode(); self.send_response(200); self.end_headers(); self.wfile.write(b); return
        if self.path.startswith("/api/assets/"):
            ok_auth = self.headers.get("authorization") == "Bearer tok"
            if not ok_auth: self.send_response(401); self.end_headers(); return
            self.send_response(302); self.send_header("location", f"{base}/s3/{self.path.rsplit('/', 1)[1]}"); self.end_headers(); return
        if self.path.startswith("/s3/"):
            state["auth_on_s3"].append(self.headers.get("authorization"))
            b = EXE_BYTES if self.path.endswith("11") else state["sums"].encode()
            self.send_response(200); self.end_headers(); self.wfile.write(b); return
        self.send_response(404); self.end_headers()


srv = ThreadingHTTPServer(("127.0.0.1", 0), GH); threading.Thread(target=srv.serve_forever, daemon=True).start()
API = f"http://127.0.0.1:{srv.server_port}"
info = selfupdate.latest(API, "o/r", "tok", "1.5.0")
ok(info and info["version"] == "1.5.1", "daha yeni panel sürümü bulundu (arşiv ve hatalı etiketler yok sayıldı)")
ok(selfupdate.latest(API, "o/r", "tok", "1.5.1") is None, "güncelse sürüm yok")
data = selfupdate.download(info, "tok")
ok(data == EXE_BYTES, "indirildi ve SHA-256 doğrulandı")
ok(all(a is None for a in state["auth_on_s3"]), "yönlendirilen adrese token gönderilmedi")
ok(selfupdate.expected_sha("abc  TD2RaporPaneli.exe.bak\n" + "f" * 64 + "  TD2RaporPaneli.exe2\n") is None, "özet satırı tam ad eşleşmeli")
state["sums"] = "0" * 64 + "  TD2RaporPaneli.exe\n"
try: selfupdate.download(info, "tok"); ok(False, "özet tutmazsa reddetmeli")
except RuntimeError: ok(True, "özet tutmayınca kurulmadı")
state["sums"] = "yok\n"
try: selfupdate.download(info, "tok"); ok(False, "özet yoksa reddetmeli")
except RuntimeError: ok(True, "özet yokken kurulmadı")
d = Path(tempfile.mkdtemp()); exe = d / "TD2RaporPaneli.exe"; exe.write_bytes(b"old")
selfupdate.install(EXE_BYTES, exe, relaunch=False)
ok(exe.read_bytes() == EXE_BYTES and (d / "TD2RaporPaneli.exe.old").read_bytes() == b"old", "exe değiştirildi, eskisi .old")
selfupdate.cleanup(exe); ok(not (d / "TD2RaporPaneli.exe.old").exists(), "eski exe temizlendi")
try: selfupdate.install(EXE_BYTES, d / "python.exe", relaunch=False); ok(False, "yanlış exe adı")
except RuntimeError: ok(True, "derlenmiş panel değilse kurmaz")
srv.shutdown()

# ---------------------------------------------------------------- 2) gerçek pencere
cfg = Path(tempfile.mkdtemp()) / "panel.json"
os.environ["TD2_PANEL_CONFIG"] = str(cfg)
os.environ.pop("TD2_PANEL_NOLOCK", None)
import tkinter as tk  # noqa: E402
import panel  # noqa: E402
panel.messagebox.askyesno = lambda *a, **k: False
cfg.write_text(json.dumps({"repo": "", "token": panel.seal("ghp_TESTTOKEN_abcdef"), "acc_url": "",
                           "admin_token": panel.seal("admin-TESTTOKEN-0123456789abcdef")}), encoding="utf-8")


def shot(root, name):
    try:
        from PIL import ImageGrab
        root.update(); x, y = root.winfo_rootx(), root.winfo_rooty()
        ImageGrab.grab((x, y, x + root.winfo_width(), y + root.winfo_height())).save(SHOTS / f"panel_lock_{name}.png")
    except Exception as e:
        print("  (ekran görüntüsü alınamadı:", e, ")")


root = tk.Tk(); P = panel.Panel(root); root.update(); time.sleep(0.5); root.update()
ok(P.locked and P._ov is not None and not P._started, "ilk açılış: PIN oluşturma ekranı, panel kapalı")
shot(root, "1_setup")
v1, v2 = P._lock_vars
v1.set("12345"); v2.set("12345"); P._lock_go(); root.update()
ok(P.locked, "kısa PIN kabul edilmedi")
v1.set("482913"); v2.set("482999"); P._lock_go(); root.update()
ok(P.locked, "iki PIN farklıyken kabul edilmedi")
v1.set("482913"); v2.set("482913"); P._lock_go(); root.update()
ok(not P.locked and P._started, "PIN oluşturuldu, panel açıldı")
disk = json.loads(cfg.read_text(encoding="utf-8"))
raw = panel.unseal(disk["token"]) if sys.platform == "win32" else disk["token"]
ok("TESTTOKEN" not in cfg.read_text(encoding="utf-8") and raw.startswith(lock.PREFIX), "belirteçler diskte PIN ile şifreli")
ok("482913" not in cfg.read_text(encoding="utf-8"), "PIN diskte yok")
P.lock_now(); root.update()
ok(P.locked, "elle kilitlendi")
P._lock_vars[0].set("482913"); P._lock_go(); root.update()
ok(not P.locked, "elle kilitten PIN ile açıldı")
root.destroy()

root = tk.Tk(); P = panel.Panel(root); root.update()
ok(P.locked and P.settings["token"] == "" and P.settings["admin_token"] == "", "yeniden açılış: kilitli, belirteçler bellekte bile yok")
P.open_settings(); ok(getattr(P, "_settings_win", None) is None, "kilitliyken ayarlar açılmaz")
for i in range(lock.FREE_TRIES):
    P._lock_vars[0].set("000000"); P._lock_go(); root.update()
ok(P.locked and lock.wait_left(P.settings["pin"]) > 0, "5 yanlıştan sonra bekleme")
shot(root, "2_wait")
ok(json.loads(cfg.read_text(encoding="utf-8"))["pin"]["fails"] == lock.FREE_TRIES, "yanlış deneme sayısı diske yazıldı (kapatıp açmak sıfırlamaz)")
P.settings["pin"]["until"] = 0
P._lock_vars[0].set("482913"); P._lock_go(); root.update()
ok(not P.locked and P.settings["token"] == "ghp_TESTTOKEN_abcdef" and P.settings["admin_token"].startswith("admin-TESTTOKEN"), "doğru PIN: belirteçler geri geldi")
shot(root, "3_open")
P.settings["lock_minutes"] = 1; P._last_input = time.time() - 120; P._idle_check(); root.update()
ok(P.locked, "boşta kalınca kendiliğinden kilitlendi")
shot(root, "4_idle")
root.destroy()

print("RESULT:", "PASS" if not fails else f"FAIL ({len(fails)})")
sys.exit(1 if fails else 0)

