"""Windows CI: hesap arayüzü uçtan uca — karşılama penceresi, Discord ile giriş (sahte), anahtar kullanma, premium.
Yerel test sunucusu (node server/dev_server.mjs) kullanılır; gerçek Discord'a / Cloudflare'e gidilmez.
    python tests/ui_account_test.py      → tests/.account_result.json + shots/acc_*.png
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
port = 8877
srv = subprocess.Popen(["node", str(ROOT / "server" / "dev_server.mjs"), str(port)], stdout=subprocess.PIPE, text=True)
_, _, ADMIN, PUB = srv.stdout.readline().split()
URL = f"http://127.0.0.1:{port}"
os.environ.pop("TD2_NO_WELCOME", None)
os.environ.update(TD2_ACCOUNT_URL=URL, TD2_ENT_PUBKEY=PUB, TD2_ACCOUNT_TEST_BROWSER="Soner")
for f in ("account.dat",): (ROOT / f).unlink(missing_ok=True)

import app  # noqa: E402
from PIL import ImageGrab  # noqa: E402
app.messagebox.askyesno = lambda *a, **k: False      # açılıştaki 'yeni PC' sorusu pencereyi örtmesin
app.messagebox.showinfo = app.messagebox.showwarning = lambda *a, **k: None
a = app.App()
a.cfg["settings"]["acc_asked"] = False
restarts = []
def fake_restart(tab=None, page=None):        # gerçek yeniden başlatma yerine: aynı akış (kaydedilen bayrak + açılış) süreç içinde
    restarts.append(tab)
    print("restart handoff before rebuild:", {"reopen": a.cfg["settings"].get("_acc_reopen"),
          "reopen_msg": a.cfg["settings"].get("_acc_reopen_msg"), "asked": a.cfg["settings"].get("acc_asked")}, flush=True)
    # A fresh process runs account_startup after the first UI frame; mirror that
    # lifecycle because rebuild_ui alone does not schedule startup callbacks.
    a.rebuild_ui(tab=tab)
    print("restart handoff after rebuild:", {"reopen": a.cfg["settings"].get("_acc_reopen"),
          "window": bool(getattr(a, "_acc_win", None))}, flush=True)
    def startup_after_rebuild():
        print("delayed account startup before:", {"reopen": a.cfg["settings"].get("_acc_reopen"),
              "signed_in": a.account.signed_in}, flush=True)
        a.account_startup()
        print("delayed account startup after:", {"reopen": a.cfg["settings"].get("_acc_reopen"),
              "window": bool(getattr(a, "_acc_win", None)), "button": hasattr(a, "_acc_btn")}, flush=True)
    a.root.after(1600, startup_after_rebuild)
a.restart_app = fake_restart
res = {"steps": []}


def step(name, ok, **kw):
    res["steps"].append({"name": name, "ok": bool(ok), **kw}); print(("OK   " if ok else "FAIL ") + name, kw, flush=True)


def shot(name, w=None):
    w = w or a.root
    try:
        w.lift(); w.attributes("-topmost", True); w.update(); w.after(300); w.update(); x, y = w.winfo_rootx(), w.winfo_rooty()
        ImageGrab.grab(bbox=(x, y, x + w.winfo_width(), y + w.winfo_height()), all_screens=True).save(SHOTS / f"{name}.png")
        w.attributes("-topmost", False)
    except Exception as e:
        print("shot failed", name, e)


def admin(path, body=None):
    req = urllib.request.Request(URL + "/v1/admin/" + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Admin " + ADMIN, "Content-Type": "application/json"},
                                 method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req) as r: return json.loads(r.read())


def s1():
    w = getattr(a, "_acc_win", None)
    step("karşılama penceresi açıldı", w is not None and w.winfo_exists())
    step("başlıkta 'Giriş yap' rozeti", any(getattr(c[2], "__name__", "") == "open_account" for c in a.banner.chips if len(c) > 2))
    shot("acc_01_welcome", w)
    a._acc_btn.invoke()
    a.root.after(6000, s2)


def s2():
    step("Discord ile giriş tamamlandı", a.account.signed_in and a.account.username == "Soner", user=a.account.username)
    win = getattr(a, "_acc_win", None)
    reopened = len(restarts) == 1 and bool(win and win.winfo_exists())
    print("post-restart account state:", {"reopen": a.cfg["settings"].get("_acc_reopen"),
          "asked": a.cfg["settings"].get("acc_asked"), "window": bool(win),
          "window_exists": bool(win and win.winfo_exists()), "button": hasattr(a, "_acc_btn")}, flush=True)
    step("girişten sonra program yeniden başlatıldı ve hesap penceresi açıldı", reopened,
         restarts=restarts, msg=getattr(a, "_acc_msg", None))
    if not reopened:
        finish()
        return
    shot("acc_02_signed_in", win)
    key = admin("licenses", {"count": 1, "days": 30, "note": "ci"})["keys"][0]
    a._acc_code.insert(0, key); a._acc_btn.invoke()
    a.root.after(6000, s3)


def s3():
    step("anahtar kullanıldı → premium", a.ent.tier == "premium" and a.ent.source == "account",
         tier=a.ent.tier, src=a.ent.source, why=a.ent.ent_reason)
    step("premium özellik açık", a.ent.has("optimizer_all"))
    chip = a._acc_chip_text()
    step("rozet kullanıcı adı + premium etiketi", "Soner" in chip and "PREMIUM" in chip, chip=chip)
    step("hesap penceresi premium sonrası yeniden açık", getattr(a, "_acc_win", None) is not None and a._acc_win.winfo_exists())
    if not (getattr(a, "_acc_win", None) and a._acc_win.winfo_exists()): a.open_account()
    shot("acc_03_premium", a._acc_win)
    a._acc_win.lift(); a.root.after(800, s4)


def s4():
    a._acc_win.destroy()
    a.open_premium_page()
    a.root.after(1500, s5)


def s5():
    shot("acc_04_settings_premium")
    # yeniden açılış: oturum ve premium hatırlanıyor mu
    import account, features
    acc2 = account.Account(app.ACCOUNT_PATH, URL)
    e2 = features.Entitlements(""); e2.set_entitlement(acc2.entitlement, account.device_pub(), PUB)
    step("yeniden açılışta oturum + premium hatırlandı", acc2.signed_in and e2.tier == "premium")
    raw = app.ACCOUNT_PATH.read_text(encoding="utf-8")
    step("belirteç diskte düz metin değil (DPAPI)", a.account.token not in raw)
    # yönetici iptal → yenile → ücretsiz
    lic = next(l for l in admin("licenses")["licenses"] if l["note"] == "ci")
    admin(f"licenses/{lic['id']}/revoke", {})
    a.account_refresh()
    a.root.after(5000, s6)


def s6():
    step("iptal sonrası premium kapandı", a.ent.tier == "free", tier=a.ent.tier)
    a.open_account(); a.root.after(800, s7)


def s7():
    shot("acc_05_revoked", a._acc_win)
    a._acc_win.destroy()
    a.root.after(200, finish)


def finish():
    res["ok"] = all(s["ok"] for s in res["steps"])
    (ROOT / "tests" / ".account_result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    a.root.destroy()


def guard(fn):
    def run():
        try: fn()
        except Exception as e:
            import traceback; traceback.print_exc()
            step(fn.__name__ + " hata", False, e=repr(e)); finish()
    return run


for _n in ("s1", "s2", "s3", "s4", "s5", "s6", "s7"):
    globals()[_n] = guard(globals()[_n])
_done = []
_finish = finish
def finish():
    if _done: return
    _done.append(1)
    if len(res["steps"]) < 11: step("tüm adımlar çalıştı", False, n=len(res["steps"]))
    _finish()


def start_account_flow():
    print("account UI state:", {"asked": a.cfg["settings"].get("acc_asked"),
          "signed_in": a.account.signed_in, "welcome_suppressed": bool(os.environ.get("TD2_NO_WELCOME")),
          "button_before": hasattr(a, "_acc_btn"),
          "window_exists": bool(getattr(a, "_acc_win", None) and a._acc_win.winfo_exists())}, flush=True)
    a.account_startup()
    a.open_account(welcome=True)
    print("account button after startup:", hasattr(a, "_acc_btn"), flush=True)
    a.root.after(200, s1)

a.root.after(4500, start_account_flow)
a.root.after(90000, finish)
try:
    a.root.mainloop()
finally:
    srv.terminate()
    app.ACCOUNT_PATH.unlink(missing_ok=True)
if __name__ == "__main__":
    print("RESULT:", "PASS" if res.get("ok") else "FAIL")
    sys.exit(0 if res.get("ok") else 1)
