"""Windows CI: geri bildirim akışının uçtan uca testi (video için ekranda adım adım oynatılır).

1) Program açılır, 🐞 Geri bildirim penceresi açılır, rapor yazılır (harf harf), gönderilir → "Raporlarım"a düşer
2) Rapor Paneli (ayrı program) açılır, raporu görür, durumunu "Çalışılıyor" yapar ve yanıt yazar
3) Programda "Raporlarım" yenilenir → durum ve geliştirici yanıtı görünür
Her adım sunucu tarafında doğrulanır; shots/fb_*.png kaydedilir. Sonuç: RESULT: PASS / FAIL
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
import fake_reports_server as fake  # noqa: E402

SRV = fake.start()
os.environ["TD2_REPORT_URL"] = SRV.base
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
TMP = Path(tempfile.mkdtemp())
for f in ("reports_sent.json", "reports_queue.json"):
    try: (ROOT / f).unlink()
    except FileNotFoundError: pass

import app  # noqa: E402

app.messagebox.askyesno = lambda *a, **k: False
app.messagebox.showinfo = lambda *a, **k: None
a = app.App()
fails, res = [], {}
REPLY = "Teşekkürler! Bu sorun 5.0.7'de düzeltildi, güncellemeyi yükleyince geçecek."


def ok(c, msg):
    print(("OK   " if c else "FAIL ") + msg, flush=True)
    if not c: fails.append(msg)


def shot(name):
    try:
        from PIL import ImageGrab
        a.root.update(); ImageGrab.grab().save(SHOTS / f"fb_{name}.png")
    except Exception as e:
        print("  (ekran görüntüsü alınamadı:", e, ")")


def typer(widget, text, then, i=0, entry=False):
    if i < len(text):
        widget.insert("end", text[i]); return a.root.after(28, lambda: typer(widget, text, then, i + 1, entry))
    a.root.after(600, then)


def s1_open():
    a.root.deiconify(); a.root.lift()
    a.open_feedback()
    w = a._fb_win
    sw = a.root.winfo_screenwidth()
    w.geometry(f"+{max(0, sw // 2 - 520)}+30"); w.lift(); w.focus_force()
    tv, title, body, contact = a._fb_fields
    tv.set("bug")
    contact.delete(0, "end"); contact.insert(0, "soner#1234")
    typer(title, "Striker dizliği eldiven olarak okunuyor",
          lambda: typer(body, "Envanterde Striker setinin dizliğini seçince program onu eldiven sanıyor.\n"
                              "Kartı aşağı kaydırınca oluyor. Beklenen: Kneepads.", s1_send))


def s1_send():
    shot("1_form")
    a._fb_send()
    a.root.after(3500, s1_check)


def s1_check():
    ok(len(fake.ISSUES) == 1, f"rapor sunucuya gitti, GitHub'da issue açıldı ({len(fake.ISSUES)})")
    it = fake.ISSUES.get(1, {})
    ok(it.get("title") == "[Hata] Striker dizliği eldiven olarak okunuyor", "issue başlığı: " + str(it.get("title")))
    ok("type:bug" in it.get("labels", []) and "status:new" in it.get("labels", []), "etiketler: " + str(it.get("labels")))
    ok('"contact": "soner#1234"' in it.get("body", "") and '"system"' in it.get("body", ""), "iletişim ve sistem bilgisi eklendi")
    sent = a.fb_store.sent
    ok(sent and sent[0].get("number") == 1, "programda 'Raporlarım' listesine eklendi")
    shot("2_sent")
    s2_panel()


def s2_panel():
    cfg = TMP / "panel.json"
    cfg.write_text(json.dumps({"repo": fake.REPO, "token": fake.TOKEN, "api": SRV.base, "admin_login": fake.ADMIN}))
    done = TMP / "panel_done"
    env = {**os.environ, "TD2_PANEL_CONFIG": str(cfg), "TD2_PANEL_DEMO_REPLY": REPLY, "TD2_PANEL_DEMO_DONE": str(done)}
    exe = ROOT / "dist" / "panel" / "TD2RaporPaneli.exe"
    cmd = [str(exe)] if exe.exists() else [sys.executable, str(ROOT / "panel" / "panel.py")]
    res["panel"] = subprocess.Popen(cmd, env=env)
    t0 = time.time()

    def wait():
        if done.exists() or time.time() - t0 > 60: return a.root.after(500, s2_check)
        if time.time() - t0 > 9 and not res.get("panel_shot"):
            res["panel_shot"] = True; shot("3_panel")
        a.root.after(500, wait)
    a.root.after(1000, wait)


def s2_check():
    it = fake.ISSUES.get(1, {})
    ok("status:in-progress" in it.get("labels", []), "panelden durum değişti: " + str(it.get("labels")))
    ok(it.get("comments") and it["comments"][-1]["body"] == REPLY, "panelden yanıt yazıldı")
    shot("4_panel_reply")
    a.root.after(1500, s3_refresh)


def s3_refresh():
    try: res["panel"].terminate()
    except Exception: pass
    a._fb_win.lift(); a._fb_win.focus_force()
    a._fb_refresh()
    a.root.after(3500, s3_check)


def s3_check():
    r = a.fb_store.sent[0] if a.fb_store.sent else {}
    ok(r.get("status") == "in-progress", "programda durum: " + str(r.get("status")))
    ok(r.get("reply") == REPLY, "programda geliştirici yanıtı görünüyor")
    w = a._fb_win
    tree = [c for c in w.winfo_children()[0].winfo_children()[1].winfo_children() if c.winfo_class() == "Treeview"]
    if tree:
        tree[0].selection_set(tree[0].get_children()[0])
    a.root.after(1200, s3_end)


def s3_end():
    shot("5_reply_in_app")
    print("RESULT: " + ("PASS" if not fails else f"FAIL ({len(fails)})"), flush=True)
    a.root.after(1500, a.root.destroy)


a.root.after(9000, s1_open)
a.root.mainloop()
SRV.shutdown()
sys.exit(1 if fails else 0)
