"""Rapor paneli uçtan uca testi: sahte GitHub sunucusu + gerçek panel penceresi + ekran görüntüleri.

Akış: 4 örnek rapor yüklenir → biri seçilir → durumu "Çalışılıyor" yapılır → yanıt yazılır → kapatılır.
Her adım sunucu tarafında doğrulanır; shots/panel_*.png kaydedilir. Sonuç: RESULT: PASS / FAIL
    python tests/panel_shot.py            (ekran görüntüsü için Pillow gerekir; yoksa yalnız doğrulama)
"""
import json
import os
import re
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
REPO = "test/reports"


def meta(d): return "\n\n<!-- td2-report " + json.dumps(d, ensure_ascii=False) + " -->"


ISSUES = {
    1: {"title": "[Hata] Striker dizliği eldiven okunuyor", "state": "open", "labels": ["report", "type:bug", "status:new", "v5.0.6", "lang:tr"],
        "body": "Striker setinin dizliği eldiven olarak görünüyor. Envanterde aşağı kaydırınca oluyor." + meta(
            {"type": "bug", "contact": "soner#1234", "system": {"os": "Windows 10", "app": "5.0.6", "res": "3440x1440", "ocr": "rapidocr"},
             "card": "STRIKER'S KNEEPADS\nHigh-End · Kneepads\nArmor 170,000", "log": "12:01 Sync applied\n12:02 Capture area: game window 3440x1440"}),
        "comments": [], "created_at": "2026-10-25T17:10:00Z"},
    2: {"title": "[İstek] Build'leri dışa aktarma", "state": "open", "labels": ["report", "type:feature", "status:triaged", "v5.0.6", "lang:de"],
        "body": "Ich möchte meine Builds als Datei exportieren und teilen." + meta({"type": "feature"}),
        "comments": [{"user": {"login": "someone"}, "body": "+1, çok iyi olur", "created_at": "2026-10-25T16:00:00Z"}], "created_at": "2026-10-25T12:00:00Z"},
    3: {"title": "[Soru] Ultrawide destekleniyor mu?", "state": "open", "labels": ["report", "type:question", "status:new", "v5.0.5", "lang:en"],
        "body": "Does it work on 32:9 monitors?" + meta({"type": "question"}), "comments": [], "created_at": "2026-10-24T09:00:00Z"},
    4: {"title": "[Hata] Sekme efekti takılıyor", "state": "closed", "labels": ["report", "type:bug", "status:done", "v5.0.5", "lang:tr"],
        "body": "Menüler arası geçişte efekt donuyor." + meta({"type": "bug"}), "comments": [], "created_at": "2026-10-22T09:00:00Z"},
}
CALLS = []


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _j(self, code, data):
        b = json.dumps(data).encode(); self.send_response(code)
        self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def _issue(self, n):
        it = ISSUES[n]
        return {"number": n, "title": it["title"], "state": it["state"], "body": it["body"], "labels": [{"name": l} for l in it["labels"]],
                "created_at": it["created_at"], "updated_at": it["created_at"], "comments": len(it["comments"]),
                "html_url": f"https://github.com/{REPO}/issues/{n}"}

    def _body(self):
        n = int(self.headers.get("content-length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        CALLS.append(("GET", self.path))
        if self.headers.get("authorization") != "Bearer test-token": return self._j(401, {"message": "Bad credentials"})
        p = self.path.split("?")[0]
        if p == f"/repos/{REPO}": return self._j(200, {"full_name": REPO, "private": True, "open_issues_count": 3})
        if p == f"/repos/{REPO}/issues":
            return self._j(200, [self._issue(n) for n in sorted(ISSUES, reverse=True)] if "page=1" in self.path else [])
        m = re.match(rf"/repos/{REPO}/issues/(\d+)/comments$", p)
        if m: return self._j(200, ISSUES[int(m.group(1))]["comments"])
        self._j(404, {"message": "Not Found"})

    def do_PUT(self):
        m = re.match(rf"/repos/{REPO}/issues/(\d+)/labels$", self.path)
        d = self._body(); CALLS.append(("PUT", self.path, d))
        ISSUES[int(m.group(1))]["labels"] = d["labels"]; self._j(200, [{"name": l} for l in d["labels"]])

    def do_POST(self):
        m = re.match(rf"/repos/{REPO}/issues/(\d+)/comments$", self.path)
        d = self._body(); CALLS.append(("POST", self.path, d))
        ISSUES[int(m.group(1))]["comments"].append({"user": {"login": "FEDERALTURK"}, "body": d["body"], "created_at": "2026-10-25T19:00:00Z"})
        self._j(201, {"id": 1})

    def do_PATCH(self):
        m = re.match(rf"/repos/{REPO}/issues/(\d+)$", self.path)
        d = self._body(); CALLS.append(("PATCH", self.path, d))
        ISSUES[int(m.group(1))]["state"] = d["state"]; self._j(200, self._issue(int(m.group(1))))


srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
cfg = Path(tempfile.mkdtemp()) / "settings.json"
cfg.write_text(json.dumps({"repo": REPO, "token": "test-token", "api": f"http://127.0.0.1:{srv.server_port}", "admin_login": "FEDERALTURK"}))
os.environ["TD2_PANEL_CONFIG"] = str(cfg)

sys.path.insert(0, str(ROOT / "panel"))
import tkinter as tk  # noqa: E402
import panel  # noqa: E402

panel.messagebox.askyesno = lambda *a, **k: False
root = tk.Tk()
P = panel.Panel(root)
fails = []


def ok(c, msg):
    print(("OK   " if c else "FAIL ") + msg, flush=True)
    if not c: fails.append(msg)


def shot(name):
    try:
        from PIL import ImageGrab
        root.update(); x, y = root.winfo_rootx(), root.winfo_rooty()
        ImageGrab.grab((x, y, x + root.winfo_width(), y + root.winfo_height())).save(SHOTS / f"panel_{name}.png")
    except Exception as e:
        print("  (ekran görüntüsü alınamadı:", e, ")")


def step(i=0):
    steps = [s_loaded, s_select, s_status, s_reply, s_close, s_filter, s_end]
    steps[i]()
    if i + 1 < len(steps): root.after(1500, lambda: step(i + 1))


def s_loaded():
    ok(len(P.issues) == 4, f"4 rapor yüklendi ({len(P.issues)})")
    ok(len(P.view) == 3, f"varsayılan görünüm: 3 açık rapor ({len(P.view)})")
    ok(P.stat_lbl["open"].cget("text") == "3" and P.stat_lbl["bug"].cget("text") == "1", "özet sayaçları")
    ok(P.issues[-1]["meta"].get("contact") or any(i["meta"].get("contact") for i in P.issues), "meta veri (iletişim) okundu")
    shot("1_list")


def s_select():
    P.tree.selection_set("1"); root.update()
    ok(P.cur and P.cur["number"] == 1, "rapor #1 seçildi")
    txt = P.txt.get("1.0", "end")
    ok("Striker setinin" in txt and "3440x1440" in txt and "<!--" not in txt, "detay: açıklama + sistem bilgisi, meta gizli")


def s_status():
    P.set_status("in-progress")


def s_reply():
    ok("status:in-progress" in ISSUES[1]["labels"] and "status:new" not in ISSUES[1]["labels"], f"durum GitHub'da değişti: {ISSUES[1]['labels']}")
    ok(P.tree.set("1", "status") == "Çalışılıyor", "listede durum güncellendi")
    P.reply.insert("1.0", "Teşekkürler! 5.0.7'de düzeltildi, güncellemeyi yükle.")
    P.send_reply()


def s_close():
    ok(ISSUES[1]["comments"] and "5.0.7" in ISSUES[1]["comments"][-1]["body"], "yanıt GitHub'a yorum olarak gitti")
    txt = P.txt.get("1.0", "end")
    ok("5.0.7'de düzeltildi" in txt, "yanıt detayda görünüyor")
    shot("2_detail")
    P.toggle_state()


def s_filter():
    ok(ISSUES[1]["state"] == "closed", "rapor kapatıldı")
    ok(not P.tree.exists("1") and len(P.view) == 2, "kapalı rapor açık listesinden çıktı")
    P.v_state.set("Tümü"); P.v_search.set("ultrawide"); root.update()
    ok(len(P.view) == 1 and P.view[0]["number"] == 3, "arama: 'ultrawide' → #3")
    P.v_search.set(""); P.v_type.set("İstek"); P.apply_filter()
    ok(len(P.view) == 1 and P.view[0]["number"] == 2, "tür filtresi: İstek → #2")
    P.v_type.set("Tümü"); P.apply_filter(); P.tree.selection_set("2"); root.update()
    shot("3_all")
    P.open_settings()


def s_end():
    root.update(); shot("4_settings")
    P._settings_win.destroy()
    print("RESULT: " + ("PASS" if not fails else f"FAIL ({len(fails)})"), flush=True)
    root.after(300, root.destroy)


root.after(2500, step)
root.mainloop()
srv.shutdown()
sys.exit(1 if fails else 0)
