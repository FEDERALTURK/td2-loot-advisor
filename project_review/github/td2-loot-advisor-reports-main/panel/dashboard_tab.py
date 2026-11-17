"""Panel sekmesi: Gösterge — tek bakışta durum.

Kaynaklar:
  - hesap sunucusu /v1/admin/overview (yönetici belirteci): sürüm dağılımı, günlük açılış, hesap/lisans, öneri, görev, olaylar;
  - hesap sunucusu /v1/health (herkese açık): sunucu ayakta mı;
  - panelin zaten yüklediği rapor issue'ları;
  - herkese açık program deposunun sürüm indirme sayıları (GitHub API).
Sürüm sayacı 6.0.1 ile başladı; daha eski sürümler sayılamaz, onlar için indirme sayılarına bakılır.
"""
import json
import threading
import time
import tkinter as tk
import urllib.request
from datetime import datetime, timedelta
from tkinter import ttk

from license_tab import AdminAPI


def ago_s(ts, now=None):
    if not ts: return "—"
    d = (now or time.time()) - ts
    if d < 90: return "az önce"
    if d < 3600: return f"{int(d // 60)} dk önce"
    if d < 86400: return f"{int(d // 3600)} sa önce"
    return f"{int(d // 86400)} gün önce"


def vkey(v):
    try: return tuple(int(x) for x in str(v).split("."))
    except ValueError: return (0,)


class DashboardTab:
    CARDS = (("reports", "Açık rapor", "reports"), ("suggest", "Bekleyen öneri", "suggest"),
             ("tasks", "Herkese açık görev", "tasks"), ("accounts", "Hesap", "users"),
             ("licenses", "Aktif lisans", "users"), ("starts", "Bugün açılış", None))

    def __init__(self, parent, panel, C):
        self.p, self.C = panel, C
        self.api, self.health_url = None, None
        self.data, self.downloads, self.health = None, None, None
        self.f = ttk.Frame(parent, style="Bg.TFrame", padding=(16, 10, 16, 0))
        self._build()

    def configure(self, url, token):
        self.api = AdminAPI(url, token) if url and token else None
        self.health_url = (url or "").rstrip("/") + "/v1/health" if url else None

    # ---------------------------------------------------------------- görünüm
    def _build(self):
        C = self.C
        row = ttk.Frame(self.f, style="Bg.TFrame"); row.pack(fill="x")
        self.card = {}
        for i, (k, title, go) in enumerate(self.CARDS):
            fr = tk.Frame(row, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], cursor="hand2" if go else "")
            fr.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0)); row.columnconfigure(i, weight=1, uniform="c")
            num = tk.Label(fr, text="–", bg=C["panel"], fg=C["text"], font=("Segoe UI Semibold", 22), anchor="w")
            num.pack(fill="x", padx=14, pady=(10, 0))
            lab = tk.Label(fr, text=title, bg=C["panel"], fg=C["dim"], font=("Segoe UI", 9), anchor="w")
            lab.pack(fill="x", padx=14)
            sub = tk.Label(fr, text="", bg=C["panel"], fg=C["dim"], font=("Segoe UI", 8), anchor="w", justify="left")
            fr.bind("<Configure>", lambda e, s_=sub: s_.config(wraplength=max(60, e.width - 24)), add="+")
            sub.pack(fill="x", padx=14, pady=(0, 10))
            self.card[k] = (num, sub)
            if go:
                for w in (fr, num, lab, sub): w.bind("<Button-1>", lambda e, g=go: self.p.goto(g))

        mid = ttk.Frame(self.f, style="Bg.TFrame"); mid.pack(fill="both", expand=True, pady=(12, 0))
        mid.columnconfigure(0, weight=1, uniform="m"); mid.columnconfigure(1, weight=1, uniform="m"); mid.rowconfigure(0, weight=1)
        self.cv_ver = self._chart(mid, 0, "SÜRÜM DAĞILIMI — son 7 gün, açılış sayısı")
        self.cv_day = self._chart(mid, 1, "GÜNLÜK AÇILIŞ — son 30 gün")

        bot = ttk.Frame(self.f, style="Bg.TFrame"); bot.pack(fill="x", pady=(12, 8))
        bot.columnconfigure(0, weight=1, uniform="b"); bot.columnconfigure(1, weight=1, uniform="b")
        dl = ttk.Frame(bot, padding=12); dl.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ttk.Label(dl, text="İNDİRMELER (herkese açık depo)", style="Sec.TLabel").pack(anchor="w")
        self.tv_dl = ttk.Treeview(dl, columns=("tag", "setup", "zip", "date"), show="headings", height=4, selectmode="none")
        for c, t, w, a in (("tag", "Sürüm", 90, "w"), ("setup", "Kurulum", 80, "e"), ("zip", "Taşınabilir", 80, "e"), ("date", "Yayın", 110, "w")):
            self.tv_dl.heading(c, text=t); self.tv_dl.column(c, width=w, anchor=a)
        self.tv_dl.pack(fill="x", pady=(6, 0))
        sv = ttk.Frame(bot, padding=12); sv.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ttk.Label(sv, text="SUNUCU", style="Sec.TLabel").pack(anchor="w")
        self.l_health = tk.Label(sv, text="—", bg=C["panel"], fg=C["dim"], font=("Segoe UI Semibold", 10), anchor="w")
        self.l_health.pack(fill="x", pady=(6, 2))
        self.l_srv = tk.Label(sv, text="", bg=C["panel"], fg=C["text"], font=("Segoe UI", 10), justify="left", anchor="nw")
        self.l_srv.pack(fill="both", expand=True)
        self.l_upd = tk.Label(self.f, text="", bg=C["bg"], fg=C["dim"], font=("Segoe UI", 8), anchor="e")
        self.l_upd.pack(fill="x")

    def _chart(self, parent, col, title):
        fr = ttk.Frame(parent, padding=12); fr.grid(row=0, column=col, sticky="nsew", padx=(0, 6) if col == 0 else (6, 0))
        ttk.Label(fr, text=title, style="Sec.TLabel").pack(anchor="w")
        cv = tk.Canvas(fr, bg=self.C["panel"], highlightthickness=0, height=220)
        cv.pack(fill="both", expand=True, pady=(6, 0))
        cv.bind("<Configure>", lambda e: self.draw())
        return cv

    # ---------------------------------------------------------------- veri
    def refresh(self, done=None):
        api, hu, gh = self.api, self.health_url, self.p.gh
        app_repo = self.p.settings.get("app_repo") or "FEDERALTURK/td2-loot-advisor"

        def work():
            out = {}
            if api: out["ov"] = api.call("GET", "overview?since=%d" % int(self.p.settings.get("notify_since") or 0))
            if hu:
                try:
                    with urllib.request.urlopen(urllib.request.Request(hu, headers={"User-Agent": "TD2Panel"}), timeout=10) as r:
                        out["health"] = json.loads(r.read()).get("ok") is True
                except Exception:
                    out["health"] = False
            if gh:
                ok, rels = gh._req("GET", f"/repos/{app_repo}/releases?per_page=8")
                if ok and isinstance(rels, list): out["dl"] = rels
            return out

        def finish(out):
            ov = out.get("ov")
            if ov and ov[0]: self.data = ov[1]
            elif ov: self.p._status("Gösterge: " + str(ov[1]), self.C["warn"])
            if "health" in out: self.health = out["health"]
            if "dl" in out: self.downloads = out["dl"]
            self.fill()
            if done: done(self.data)

        def run():
            r = work()
            # The panel can be closed while a refresh is in flight.  Tk calls
            # from a worker after root.destroy() raise RuntimeError and used
            # to leak noisy thread tracebacks during shutdown.
            if getattr(self.p, "_closing", False):
                return
            try:
                self.f.after(0, lambda: finish(r))
            except RuntimeError:
                return
        threading.Thread(target=run, daemon=True).start()

    def fill(self):
        C, d = self.C, self.data or {}
        issues = self.p.issues or []
        op = [i for i in issues if i["state"] == "open"]
        new = sum(i["status"] == "new" for i in op)
        self._set("reports", len(op) if issues or self.p.gh else "–", f"{new} yeni" if new else "yeni yok", C["info"] if new else None)
        if d:
            sp = d.get("suggestions_pending") or 0
            self._set("suggest", sp, f"{d.get('lines_approved') or 0} onaylı", C["warn"] if sp else None)
            t = d.get("tasks") or {}
            self._set("tasks", t.get("public", 0), f"{t.get('waiting', 0)} bekliyor · eşik {t.get('min_reporters', 2)}")
            a = d.get("accounts") or {}
            self._set("accounts", a.get("total", 0), f"7 günde {a.get('logins_7d', 0)} giriş")
            exp = a.get("expiring_14d") or 0
            self._set("licenses", a.get("active_licenses", 0), f"{exp} tanesi 14 günde bitiyor" if exp else f"{a.get('unused_keys', 0)} boş anahtar",
                      C["warn"] if exp else None)
            u = d.get("usage") or {}
            self._set("starts", u.get("starts_today", 0), "6.0.1+ sayılır")
            stale = not d.get("cron_last") or (d.get("now", time.time()) - d["cron_last"]) > 3 * 3600
            srv = [f"Saatlik bakım: {ago_s(d.get('cron_last'), d.get('now'))}" + ("  ⚠" if stale else ""),
                   f"GitHub'a iletilmeyi bekleyen rapor: {d.get('reports_queued') or 0}",
                   f"Gizlenen görev: {t.get('hidden', 0)}"]
            self.l_srv.config(text="\n".join(srv))
        if self.health is not None:
            self.l_health.config(text="● Ayakta" if self.health else "● Cevap vermiyor", fg=C["ok"] if self.health else C["bad"])
        self.tv_dl.delete(*self.tv_dl.get_children())
        for r in (self.downloads or [])[:6]:
            setup = sum(a.get("download_count", 0) for a in r.get("assets", []) if a["name"].lower().endswith(".exe"))
            zp = sum(a.get("download_count", 0) for a in r.get("assets", []) if a["name"].lower().endswith(".zip"))
            if r.get("tag_name") == "mt-models": continue
            self.tv_dl.insert("", "end", values=(r.get("tag_name"), setup, zp, (r.get("published_at") or "")[:10]))
        self.l_upd.config(text="Güncellendi: " + datetime.now().strftime("%H:%M:%S"))
        self.draw()

    def _set(self, k, val, sub="", color=None):
        num, s = self.card[k]
        num.config(text=str(val), fg=color or self.C["text"]); s.config(text=sub)

    # ---------------------------------------------------------------- çizim
    def draw(self):
        d = self.data or {}
        u = d.get("usage") or {}
        self._bars(self.cv_ver, [(r["version"], r.get("starts") or 0, r.get("polls") or 0) for r in (u.get("versions_7d") or [])])
        self._days(self.cv_day, u.get("daily_30d") or [])

    def _empty(self, cv, text):
        cv.create_text(cv.winfo_width() // 2, cv.winfo_height() // 2, text=text, fill=self.C["dim"], font=("Segoe UI", 9), justify="center")

    def _bars(self, cv, rows):
        C = self.C
        cv.delete("all")
        W, H = max(cv.winfo_width(), 50), max(cv.winfo_height(), 50)
        if not rows:
            return self._empty(cv, "Henüz veri yok.\nSürüm sayacı 6.0.1 ile başlar; eski sürümler için indirme sayılarına bak.")
        rows = sorted(rows, key=lambda r: vkey(r[0]), reverse=True)[:8]
        newest = rows[0][0]
        total = sum(r[1] for r in rows) or 1
        mx = max(r[1] for r in rows) or 1
        bh = min(26, (H - 10) // len(rows) - 6)
        for i, (v, n, polls) in enumerate(rows):
            y = 6 + i * (bh + 6)
            cv.create_text(8, y + bh / 2, text="v" + v, anchor="w", fill=C["text"], font=("Segoe UI Semibold", 9))
            x0, x1 = 70, 70 + (W - 230) * n / mx
            cv.create_rectangle(x0, y, max(x0 + 2, x1), y + bh, fill=C["accent"] if v == newest else C["line"], width=0)
            hours = polls * 0.5
            cv.create_text(x1 + 8, y + bh / 2, anchor="w", fill=C["dim"], font=("Segoe UI", 8),
                           text=f"{n}  ·  %{round(100 * n / total)}  ·  ~{hours:.0f} sa")

    def _days(self, cv, days):
        C = self.C
        cv.delete("all")
        W, H = max(cv.winfo_width(), 50), max(cv.winfo_height(), 50)
        if not days:
            return self._empty(cv, "Henüz veri yok.")
        have = {d["day"]: d for d in days}
        last = datetime.strptime(days[-1]["day"], "%Y-%m-%d")
        days = []
        for k in range(29, -1, -1):                       # her zaman 30 günlük eksen; veri olmayan gün = 0
            day = (last - timedelta(days=k)).strftime("%Y-%m-%d")
            days.append(have.get(day, {"day": day, "starts": 0}))
        mx = max(d.get("starts") or 0 for d in days) or 1
        n = len(days)
        bw = max(3, (W - 20) / n - 3)
        base, top = H - 22, 22
        for i, d in enumerate(days):
            x = 10 + i * (bw + 3)
            h = (base - top) * (d.get("starts") or 0) / mx
            cv.create_rectangle(x, base - h, x + bw, base, fill=C["accent"] if i == n - 1 else C["accent2"] if i >= n - 7 else C["line"], width=0)
            if i in (0, n - 1, n // 2):
                cv.create_text(x + bw / 2, base + 10, text=d["day"][5:], fill=C["dim"], font=("Segoe UI", 8))
        cv.create_text(W - 8, 4, anchor="ne", text=f"en çok {mx} · son 7 gün açık turuncu", fill=C["dim"], font=("Segoe UI", 8))

