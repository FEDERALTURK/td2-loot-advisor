#!/usr/bin/env python3
"""TD2 Rapor Paneli — kullanıcıların programdan gönderdiği hata raporlarını ve istekleri yönetir.

Panel 1.5: Gösterge sekmesi, sistem tepsisi + Windows bildirimleri, panelin kendi PIN kilidi (Windows şifresi gerekmez),
SHA-256 doğrulamalı kendini güncelleme.

Raporlar özel GitHub deposunda (ör. FEDERALTURK/td2-loot-advisor-reports) issue olarak durur. Panel onları listeler,
filtreler, durumlarını değiştirir (status:* etiketleri), yanıt yazar (kullanıcı programdaki "Raporlarım"da görür),
kapatır/açar ve CSV'ye aktarır. Ayarlar (token dahil) yalnız bu bilgisayarda: %APPDATA%\\TD2RaporPaneli\\settings.json
"""
import csv
import json
import os
import sys
import threading
import time
import tkinter as tk
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_api import GitHub, STATUSES  # noqa: E402
from license_tab import LicenseTab  # noqa: E402
from tasks_tab import TasksTab, SuggestTab  # noqa: E402
from dashboard_tab import DashboardTab  # noqa: E402
import lock  # noqa: E402
import selfupdate  # noqa: E402
from tray import Tray, summarize  # noqa: E402

APP_NAME = "TD2 Rapor Paneli"
VERSION = "1.5.0"

C = {"bg": "#0e1014", "panel": "#161a21", "panel2": "#1d222b", "line": "#2a303b", "text": "#e7e9ee", "dim": "#8b93a3",
     "accent": "#ff6a00", "accent2": "#ff8a33", "ok": "#3fb950", "warn": "#d29922", "bad": "#f85149", "info": "#58a6ff",
     "entry": "#0b0d11", "sel": "#33241a"}
TYPE_TR = {"bug": "Hata", "feature": "İstek", "question": "Soru"}
STATUS_TR = {"new": "Yeni", "triaged": "İncelendi", "in-progress": "Çalışılıyor", "done": "Tamamlandı",
             "wontfix": "Yapılmayacak", "duplicate": "Mükerrer", "closed": "Kapalı"}
STATUS_COLOR = {"new": C["info"], "triaged": C["warn"], "in-progress": C["accent"], "done": C["ok"],
                "wontfix": C["dim"], "duplicate": C["dim"], "closed": C["dim"]}
FONT = ("Segoe UI", 10)


def config_path():
    if os.environ.get("TD2_PANEL_CONFIG"): return Path(os.environ["TD2_PANEL_CONFIG"])
    base = Path(os.environ.get("APPDATA") or Path.home() / ".config")
    return base / "TD2RaporPaneli" / "settings.json"


SECRET = ("token", "admin_token")


def _dpapi(data, protect):
    import ctypes
    from ctypes import wintypes

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    def blob(b):
        buf = ctypes.create_string_buffer(b, len(b))
        return BLOB(len(b), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf
    src, _a = blob(data); ent, _b = blob(b"td2-report-panel"); out = BLOB()
    fn = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
    if not fn(ctypes.byref(src), None, ctypes.byref(ent), None, None, 0x1, ctypes.byref(out)): raise OSError("DPAPI")
    try: return ctypes.string_at(out.pbData, out.cbData)
    finally: ctypes.windll.kernel32.LocalFree(out.pbData)


def seal(v):
    import base64
    if not v or sys.platform != "win32" or str(v).startswith("dpapi:"): return v
    try: return "dpapi:" + base64.b64encode(_dpapi(v.encode(), True)).decode()
    except Exception: return v


def unseal(v):
    import base64
    if not isinstance(v, str) or not v.startswith("dpapi:"): return v or ""
    try: return _dpapi(base64.b64decode(v[6:]), False).decode()
    except Exception: return ""


def resource(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / name


def ago(iso):
    try:
        t = datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S")
        d = (datetime.now(timezone.utc).replace(tzinfo=None) - t).total_seconds()
    except Exception:
        return iso[:10]
    if d < 3600: return f"{max(1, int(d // 60))} dk önce"
    if d < 86400: return f"{int(d // 3600)} sa önce"
    if d < 86400 * 30: return f"{int(d // 86400)} gün önce"
    return iso[:10]


class Panel:
    def __init__(self, root):
        self.root = root
        root.title(f"{APP_NAME} {VERSION}")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(1440, sw - 60), min(860, sh - 90)
        root.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}")
        root.minsize(min(1000, w), min(600, h))
        root.configure(bg=C["bg"])
        try: root.iconbitmap(str(resource("icon/td2.ico")))
        except Exception: pass
        self.key = None                                  # PIN'den türetilen şifreleme anahtarı (yalnız bellekte)
        self.settings = self._load()
        self.issues, self.view, self.cur = [], [], None
        self.gh = None
        self._closing = False
        self._known, self._new_reports, self.locked, self._started = None, 0, False, False
        self._last_input = time.time()
        self._style()
        self._build()
        root.bind("<F5>", lambda e: self.refresh())
        root.bind("<Control-f>", lambda e: self.e_search.focus_set())
        for ev in ("<Any-KeyPress>", "<Motion>", "<Button>"):
            root.bind_all(ev, self._touch, add="+")
        self.tray = Tray(root, str(resource("icon/td2.ico")), f"{APP_NAME} {VERSION}",
                         [("Paneli aç", self.show), ("Şimdi yenile", self.poll_now), ("Kilitle", self.lock_now), ("Çıkış", self.quit)])
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        if getattr(sys, "frozen", False): selfupdate.cleanup()
        if os.environ.get("TD2_PANEL_NOLOCK"): self._unlocked()
        elif not self.settings.get("pin"): self._lock_screen(setup=True)
        else: self._lock_screen()
        root.after(30 * 1000, self._idle_check)

    # ---------- ayarlar (GitHub ve yönetici belirteçleri diskte Windows DPAPI ile şifreli)
    def _load(self):
        d = {"repo": "FEDERALTURK/td2-loot-advisor-reports", "token": "", "api": "https://api.github.com", "admin_login": "FEDERALTURK",
             "acc_url": "https://td2-stats.td2loot.workers.dev", "admin_token": ""}
        try: d.update(json.loads(config_path().read_text(encoding="utf-8")))
        except Exception: pass
        d.setdefault("tray", True); d.setdefault("lock_minutes", 10); d.setdefault("update_check", True)
        self._sealed = {}
        for k in SECRET:
            v = unseal(d.get(k, ""))
            if isinstance(v, str) and v.startswith(lock.PREFIX):      # PIN ile şifreli: kilit açılınca çözülür
                self._sealed[k], d[k] = v, ""
            else:
                d[k] = v
        return d

    def _save(self):
        p = config_path(); p.parent.mkdir(parents=True, exist_ok=True)
        out = dict(self.settings)
        for k in SECRET:
            v = out.get(k, "")
            if self.settings.get("pin") and self.key is None:
                v = self._sealed.get(k, "")                           # kilitliyken: şifreli değeri olduğu gibi koru
            elif self.settings.get("pin") and v:
                v = lock.encrypt(self.key, v)
            out[k] = seal(v)
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_text(json.dumps(out, indent=2), encoding="utf-8"); os.replace(tmp, p)

    def _apply_settings(self):
        s = self.settings
        self.gh = GitHub(s["token"], s["repo"], s.get("api")) if s.get("repo") and s.get("token") else None
        self.l_repo.config(text=s.get("repo") or "depo ayarlanmadı")
        if self.gh: self.refresh()
        else: self._status("Ayarlar'dan depo ve token gir.", C["warn"])
        self.lic.api = None
        if s.get("acc_url") and s.get("admin_token"):
            self.lic.configure(s["acc_url"], s["admin_token"]); self.tasks_tab.configure(s["acc_url"], s["admin_token"])
            self.sug_tab.configure(s["acc_url"], s["admin_token"])
        self.dash.configure(s.get("acc_url"), s.get("admin_token"))
        self.dash.refresh()

    # ---------- görünüm
    def _style(self):
        st = ttk.Style(self.root)
        st.theme_use("clam")
        st.configure(".", background=C["panel"], foreground=C["text"], fieldbackground=C["entry"], bordercolor=C["line"],
                     lightcolor=C["panel"], darkcolor=C["panel"], font=FONT)
        st.configure("TFrame", background=C["panel"])
        st.configure("Bg.TFrame", background=C["bg"])
        st.configure("TLabel", background=C["panel"], foreground=C["text"])
        st.configure("Dim.TLabel", foreground=C["dim"])
        st.configure("H.TLabel", font=("Segoe UI Semibold", 15), background=C["bg"])
        st.configure("Sub.TLabel", foreground=C["dim"], background=C["bg"])
        st.configure("Sec.TLabel", font=("Segoe UI Semibold", 9), foreground=C["dim"])
        st.configure("Num.TLabel", font=("Segoe UI Semibold", 18))
        st.configure("TButton", background=C["panel2"], foreground=C["text"], borderwidth=1, focusthickness=0, padding=(10, 5))
        st.map("TButton", background=[("active", C["line"])])
        st.configure("Accent.TButton", background=C["accent"], foreground="#111")
        st.map("Accent.TButton", background=[("active", C["accent2"])])
        st.configure("TEntry", insertcolor=C["text"], padding=5)
        st.configure("TCombobox", arrowcolor=C["text"], padding=4)
        st.map("TCombobox", fieldbackground=[("readonly", C["entry"])], foreground=[("readonly", C["text"])])
        self.root.option_add("*TCombobox*Listbox.background", C["entry"])
        self.root.option_add("*TCombobox*Listbox.foreground", C["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", C["accent"])
        st.configure("Treeview", background=C["panel"], fieldbackground=C["panel"], foreground=C["text"], rowheight=28, borderwidth=0)
        st.configure("Treeview.Heading", background=C["panel2"], foreground=C["dim"], relief="flat", font=("Segoe UI Semibold", 9))
        st.map("Treeview", background=[("selected", C["sel"])], foreground=[("selected", C["text"])])
        st.configure("TNotebook", background=C["bg"], borderwidth=0, tabmargins=(16, 4, 16, 0))
        st.configure("TNotebook.Tab", background=C["panel"], foreground=C["dim"], padding=(14, 6), borderwidth=0,
                     font=("Segoe UI Semibold", 10))
        st.map("TNotebook.Tab", background=[("selected", C["panel2"]), ("active", C["line"])],
               foreground=[("selected", C["accent2"]), ("active", C["text"])])
        st.configure("Vertical.TScrollbar", background=C["panel2"], troughcolor=C["panel"], arrowcolor=C["dim"])

    def _build(self):
        top = ttk.Frame(self.root, style="Bg.TFrame", padding=(16, 12, 16, 8)); top.pack(fill="x")
        ttk.Label(top, text="◆ TD2 Rapor Paneli", style="H.TLabel").pack(side="left")
        self.l_repo = ttk.Label(top, text="", style="Sub.TLabel"); self.l_repo.pack(side="left", padx=14)
        ttk.Button(top, text="⚙ Ayarlar", command=self.open_settings).pack(side="right")
        ttk.Button(top, text="⇩ CSV", command=self.export_csv).pack(side="right", padx=6)
        ttk.Button(top, text="⟳ Yenile (F5)", style="Accent.TButton", command=self.refresh).pack(side="right")
        self.l_status = tk.Label(self.root, text="", anchor="w", bg=C["bg"], fg=C["dim"], font=("Segoe UI", 9), padx=16, pady=6)
        self.l_status.pack(fill="x", side="bottom")
        ttk.Button(top, text="🔒 Kilitle", command=self.lock_now).pack(side="right", padx=6)
        self.main_nb = ttk.Notebook(self.root); self.main_nb.pack(fill="both", expand=True)
        self.dash = DashboardTab(self.main_nb, self, C); self.main_nb.add(self.dash.f, text="  ◆ Gösterge  ")
        tab_r = ttk.Frame(self.main_nb, style="Bg.TFrame"); self.main_nb.add(tab_r, text="  📋 Raporlar  ")
        self.tab_r = tab_r
        self.lic = LicenseTab(self.main_nb, self, C); self.main_nb.add(self.lic.f, text="  🔑 Kullanıcılar ve lisanslar  ")
        self.tasks_tab = TasksTab(self.main_nb, self, C); self.main_nb.add(self.tasks_tab.f, text="  👥 Topluluk görevleri  ")
        self.sug_tab = SuggestTab(self.main_nb, self, C); self.main_nb.add(self.sug_tab.f, text="  ✍ Çeviri önerileri  ")

        body = ttk.Frame(tab_r, style="Bg.TFrame", padding=(16, 8, 16, 0)); body.pack(fill="both", expand=True)
        # sol: filtreler + sayaçlar
        left = ttk.Frame(body, padding=14, width=230); left.pack(side="left", fill="y"); left.pack_propagate(False)
        ttk.Label(left, text="ARA", style="Sec.TLabel").pack(anchor="w")
        self.v_search = tk.StringVar(); self.v_search.trace_add("write", lambda *a: self.apply_filter())
        self.e_search = ttk.Entry(left, textvariable=self.v_search); self.e_search.pack(fill="x", pady=(2, 12))
        self.v_type, self.v_stat, self.v_state = tk.StringVar(value="Tümü"), tk.StringVar(value="Tümü"), tk.StringVar(value="Açık")
        for title, var, vals in (("TÜR", self.v_type, ["Tümü"] + list(TYPE_TR.values())),
                                 ("DURUM", self.v_stat, ["Tümü"] + [STATUS_TR[s] for s in STATUSES]),
                                 ("GÖRÜNÜM", self.v_state, ["Açık", "Kapalı", "Tümü"])):
            ttk.Label(left, text=title, style="Sec.TLabel").pack(anchor="w")
            cb = ttk.Combobox(left, textvariable=var, values=vals, state="readonly"); cb.pack(fill="x", pady=(2, 12))
            cb.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())
        ttk.Separator(left).pack(fill="x", pady=8)
        ttk.Label(left, text="ÖZET", style="Sec.TLabel").pack(anchor="w", pady=(0, 6))
        self.stat_lbl = {}
        grid = ttk.Frame(left); grid.pack(fill="x")
        for i, (k, name, col) in enumerate((("open", "Açık", C["text"]), ("new", "Yeni", C["info"]), ("bug", "Hata", C["bad"]),
                                            ("feature", "İstek", C["accent"]), ("in-progress", "Çalışılıyor", C["warn"]), ("done", "Bitti", C["ok"]))):
            f = ttk.Frame(grid, padding=(0, 2)); f.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 18), pady=2)
            self.stat_lbl[k] = ttk.Label(f, text="–", style="Num.TLabel", foreground=col); self.stat_lbl[k].pack(anchor="w")
            ttk.Label(f, text=name, style="Dim.TLabel").pack(anchor="w")

        # sağ: detay
        right = ttk.Frame(body, padding=14, width=480); right.pack(side="right", fill="y"); right.pack_propagate(False)
        self.l_title = ttk.Label(right, text="Bir rapor seç", font=("Segoe UI Semibold", 13), wraplength=440, justify="left"); self.l_title.pack(anchor="w")
        self.l_meta = ttk.Label(right, text="", style="Dim.TLabel", wraplength=440, justify="left"); self.l_meta.pack(anchor="w", pady=(4, 8))
        sf = ttk.Frame(right); sf.pack(fill="x")
        ttk.Label(sf, text="DURUM", style="Sec.TLabel").pack(anchor="w")
        bf = ttk.Frame(sf); bf.pack(fill="x", pady=(2, 8))
        self.st_btn = {}
        for i, s in enumerate(STATUSES):
            b = tk.Button(bf, text=STATUS_TR[s], command=lambda s=s: self.set_status(s), bg=C["panel2"], fg=C["text"], bd=0,
                          activebackground=C["line"], activeforeground=C["text"], font=("Segoe UI", 9), padx=8, pady=4, cursor="hand2")
            b.grid(row=i // 3, column=i % 3, sticky="ew", padx=2, pady=2); bf.columnconfigure(i % 3, weight=1); self.st_btn[s] = b
        self.txt = tk.Text(right, wrap="word", bg=C["entry"], fg=C["text"], insertbackground=C["text"], bd=0, padx=10, pady=8,
                           font=("Segoe UI", 10), height=14, highlightthickness=1, highlightbackground=C["line"])
        self.txt.pack(fill="both", expand=True)
        for tag, kw in (("h", {"font": ("Segoe UI Semibold", 10), "foreground": C["accent2"]}), ("dim", {"foreground": C["dim"]}),
                        ("admin", {"foreground": C["ok"], "font": ("Segoe UI Semibold", 10)}), ("mono", {"font": ("Consolas", 9), "foreground": C["dim"]})):
            self.txt.tag_configure(tag, **kw)
        self.txt.config(state="disabled")
        ttk.Label(right, text="YANIT (kullanıcı programdaki 'Raporlarım'da görür)", style="Sec.TLabel").pack(anchor="w", pady=(10, 2))
        self.reply = tk.Text(right, wrap="word", height=4, bg=C["entry"], fg=C["text"], insertbackground=C["text"], bd=0, padx=8, pady=6,
                             font=FONT, highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["accent"])
        self.reply.pack(fill="x")
        af = ttk.Frame(right); af.pack(fill="x", pady=(8, 0))
        ttk.Button(af, text="Yanıtla", style="Accent.TButton", command=self.send_reply).pack(side="left")
        self.b_state = ttk.Button(af, text="Kapat", command=self.toggle_state); self.b_state.pack(side="left", padx=6)
        ttk.Button(af, text="GitHub'da aç", command=self.open_web).pack(side="right")

        # orta: liste
        mid = ttk.Frame(body, padding=(1, 0)); 
        mid.pack(side="left", fill="both", expand=True, padx=10)
        cols = ("no", "type", "title", "status", "ver", "lang", "time", "cm")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", selectmode="browse")
        for c, t, w, a in (("no", "#", 52, "e"), ("type", "Tür", 70, "w"), ("title", "Başlık", 230, "w"), ("status", "Durum", 110, "w"),
                           ("ver", "Sürüm", 70, "w"), ("lang", "Dil", 44, "w"), ("time", "Zaman", 92, "w"), ("cm", "💬", 40, "center")):
            self.tree.heading(c, text=t, command=lambda c=c: self.sort(c)); self.tree.column(c, width=w, anchor=a, stretch=(c == "title"))
        for s, col in STATUS_COLOR.items(): self.tree.tag_configure(s, foreground=col)
        self.tree.tag_configure("bug", foreground=C["text"])
        sb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())
        self.tree.bind("<Double-1>", lambda e: self.open_web())

    def _status(self, text, color=None):
        self.l_status.config(text=text, fg=color or C["dim"])

    # ---------- veri
    def _bg(self, fn, done):
        def run():
            res = fn()
            self.root.after(0, lambda: done(res))
        threading.Thread(target=run, daemon=True).start()

    def refresh(self):
        if self.locked: return
        if not self.gh: return self.open_settings()
        self._status("Yükleniyor…", C["info"])
        self._bg(lambda: self.gh.issues("all"), self._loaded)

    def _loaded(self, res):
        ok, data = res
        if not ok:
            self._status(f"Hata: {data}", C["bad"]); return
        keep = self.cur["number"] if self.cur else None
        nums = {i["number"] for i in data}
        if self._known is not None: self._new_reports += len(nums - self._known)
        self._known = nums
        self.issues = data
        self._stats()
        self.apply_filter()
        if keep and self.tree.exists(str(keep)): self.tree.selection_set(str(keep))
        self._status(f"{len(data)} rapor yüklendi · {datetime.now():%H:%M:%S}", C["ok"])
        self.dash.fill()
        if os.environ.get("TD2_PANEL_DEMO_REPLY") and not getattr(self, "_demo", False) and self.view:
            self._demo = True; self.root.after(1500, self._demo_run)

    def _demo_run(self, step=0):
        """Test/video için: en yeni raporu seç → Çalışılıyor yap → yanıtı yazıp gönder (yalnız TD2_PANEL_DEMO_REPLY ile)."""
        text = os.environ["TD2_PANEL_DEMO_REPLY"]
        if step == 0:
            self.tree.selection_set(self.tree.get_children()[0]); self.tree.focus_set()
            return self.root.after(2000, lambda: self._demo_run(1))
        if step == 1:
            self.set_status("in-progress"); return self.root.after(2000, lambda: self._demo_run(2))
        if step < 2 + len(text):
            self.reply.insert("end", text[step - 2]); return self.root.after(35, lambda: self._demo_run(step + 1))
        self.send_reply()
        mark = os.environ.get("TD2_PANEL_DEMO_DONE")
        if mark: self.root.after(2500, lambda: Path(mark).write_text("ok"))

    def _auto(self):
        if self.gh and not self.locked: self.refresh()
        self.root.after(5 * 60 * 1000, self._auto)

    def _stats(self):
        op = [i for i in self.issues if i["state"] == "open"]
        vals = {"open": len(op), "new": sum(i["status"] == "new" for i in op), "bug": sum(i["type"] == "bug" for i in op),
                "feature": sum(i["type"] == "feature" for i in op), "in-progress": sum(i["status"] == "in-progress" for i in op),
                "done": sum(i["status"] == "done" for i in self.issues)}
        for k, v in vals.items(): self.stat_lbl[k].config(text=str(v))

    def apply_filter(self):
        q = self.v_search.get().strip().lower()
        t = {v: k for k, v in TYPE_TR.items()}.get(self.v_type.get())
        s = {v: k for k, v in STATUS_TR.items()}.get(self.v_stat.get())
        st = {"Açık": "open", "Kapalı": "closed"}.get(self.v_state.get())
        self.view = [i for i in self.issues if (not t or i["type"] == t) and (not s or i["status"] == s) and (not st or i["state"] == st)
                     and (not q or q in (i["title"] + " " + i["body"] + " " + str(i["number"])).lower())]
        self.tree.delete(*self.tree.get_children())
        for i in self.view:
            self.tree.insert("", "end", iid=str(i["number"]), tags=(i["status"],), values=(
                i["number"], TYPE_TR.get(i["type"], i["type"]), i["title"], STATUS_TR.get(i["status"], i["status"]),
                i["version"], i["lang"], ago(i["created"]), i["comments"] or ""))

    def sort(self, col):
        key = {"no": lambda i: i["number"], "type": lambda i: i["type"], "title": lambda i: i["title"].lower(), "status": lambda i: i["status"],
               "ver": lambda i: i["version"], "lang": lambda i: i["lang"], "time": lambda i: i["created"], "cm": lambda i: i["comments"]}[col]
        rev = getattr(self, "_sort", None) == col
        self.issues.sort(key=key, reverse=not rev); self._sort = None if rev else col
        self.apply_filter()

    # ---------- detay
    def on_select(self):
        sel = self.tree.selection()
        if not sel: return
        self.cur = next((i for i in self.issues if str(i["number"]) == sel[0]), None)
        if not self.cur: return
        i = self.cur
        self.l_title.config(text=f"#{i['number']}  {i['title']}")
        m = i["meta"]
        bits = [TYPE_TR.get(i["type"], i["type"]), STATUS_TR.get(i["status"], i["status"]), f"v{i['version']}" if i["version"] else "",
                i["lang"], ago(i["created"]), f"İletişim: {m['contact']}" if m.get("contact") else ""]
        self.l_meta.config(text="  ·  ".join(b for b in bits if b))
        for s, b in self.st_btn.items():
            on = s == i["status"]
            b.config(bg=STATUS_COLOR[s] if on else C["panel2"], fg="#111" if on else C["text"])
        self.b_state.config(text="Yeniden aç" if i["state"] == "closed" else "Kapat")
        self._render(i, None)
        num = i["number"]
        self._bg(lambda: self.gh.comments(num), lambda cm: self.cur and self.cur["number"] == num and self._render(i, cm))

    def _render(self, i, comments):
        t = self.txt; t.config(state="normal"); t.delete("1.0", "end")
        t.insert("end", i["body"] or "(açıklama yok)")
        m = i["meta"]
        if m.get("system"):
            t.insert("end", "\n\nSistem\n", "h")
            t.insert("end", "\n".join(f"{k}: {v}" for k, v in m["system"].items()), "mono")
        if m.get("card"):
            t.insert("end", "\n\nEşya kartı\n", "h"); t.insert("end", m["card"], "mono")
        if m.get("log"):
            t.insert("end", "\n\nProgram kaydı (son satırlar)\n", "h"); t.insert("end", m["log"][-3000:], "mono")
        t.insert("end", "\n\nYorumlar\n", "h")
        if comments is None: t.insert("end", "yükleniyor…", "dim")
        elif not comments: t.insert("end", "henüz yorum yok", "dim")
        admin = (self.settings.get("admin_login") or "").lower()
        for c in comments or []:
            who = c.get("user", {}).get("login", "?")
            t.insert("end", f"\n{who} · {ago(c.get('created_at', ''))}\n", "admin" if who.lower() == admin else "dim")
            t.insert("end", c.get("body", "") + "\n")
        if comments and getattr(self, "_scroll_end", False):
            t.see("end"); self._scroll_end = False
        t.config(state="disabled")

    def _need(self):
        if not self.cur: messagebox.showinfo(APP_NAME, "Önce listeden bir rapor seç.", parent=self.root)
        return self.cur

    def set_status(self, s):
        i = self._need()
        if not i: return
        self._status(f"#{i['number']} → {STATUS_TR[s]}…", C["info"])
        def done(res):
            ok, val = res
            if not ok: return self._status(f"Hata: {val}", C["bad"])
            i["labels"], i["status"] = val, s
            if s in ("done", "wontfix", "duplicate") and i["state"] == "open" and messagebox.askyesno(APP_NAME, "Rapor kapatılsın mı?", parent=self.root):
                return self.toggle_state()
            self._stats(); self.apply_filter()
            if self.tree.exists(str(i["number"])): self.tree.selection_set(str(i["number"]))
            self._status(f"#{i['number']} durumu: {STATUS_TR[s]}", C["ok"])
        self._bg(lambda: self.gh.set_status(i["number"], i["labels"], s), done)

    def send_reply(self):
        i = self._need()
        if not i: return
        text = self.reply.get("1.0", "end").strip()
        if not text: return self._status("Yanıt boş.", C["warn"])
        self._status("Gönderiliyor…", C["info"])
        def done(res):
            ok, val = res
            if not ok: return self._status(f"Hata: {val}", C["bad"])
            self.reply.delete("1.0", "end"); i["comments"] += 1; self._scroll_end = True
            self._status(f"#{i['number']} yanıtlandı.", C["ok"]); self.apply_filter()
            if self.tree.exists(str(i["number"])): self.tree.selection_set(str(i["number"]))
            self.on_select()
        self._bg(lambda: self.gh.add_comment(i["number"], text), done)

    def toggle_state(self):
        i = self._need()
        if not i: return
        new = "open" if i["state"] == "closed" else "closed"
        def done(res):
            ok, val = res
            if not ok: return self._status(f"Hata: {val}", C["bad"])
            i["state"] = new; self._stats(); self.apply_filter()
            if self.tree.exists(str(i["number"])): self.tree.selection_set(str(i["number"]))
            self._status(f"#{i['number']} {'kapatıldı' if new == 'closed' else 'yeniden açıldı'}.", C["ok"])
        self._bg(lambda: self.gh.set_state(i["number"], new), done)

    def open_web(self):
        if self.cur and self.cur.get("url"): webbrowser.open(self.cur["url"])

    def export_csv(self):
        if not self.view: return self._status("Aktarılacak rapor yok.", C["warn"])
        p = filedialog.asksaveasfilename(parent=self.root, defaultextension=".csv", initialfile=f"td2_raporlar_{datetime.now():%Y%m%d}.csv",
                                         filetypes=[("CSV", "*.csv")])
        if not p: return
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["No", "Tür", "Başlık", "Durum", "Açık/Kapalı", "Sürüm", "Dil", "Oluşturma", "Yorum", "Açıklama"])
            for i in self.view:
                w.writerow([i["number"], TYPE_TR.get(i["type"], i["type"]), i["title"], STATUS_TR.get(i["status"], i["status"]), i["state"],
                            i["version"], i["lang"], i["created"][:16].replace("T", " "), i["comments"], i["body"][:2000]])
        self._status(f"{len(self.view)} rapor aktarıldı: {p}", C["ok"])

    # ---------- kilit (panelin kendi PIN'i — Windows şifresi gerekmez)
    def _touch(self, _e=None):
        self._last_input = time.time()

    def _lock_screen(self, setup=False):
        """Pencerenin tamamını örten kilit ekranı. setup=True: ilk açılışta PIN oluşturma."""
        self.locked = True
        for w in self.root.winfo_children():
            if isinstance(w, tk.Toplevel): w.destroy()          # açık ayar penceresi vb. kapanır (kaydedilmez)
        ov = tk.Frame(self.root, bg=C["bg"]); ov.place(relx=0, rely=0, relwidth=1, relheight=1); ov.lift()
        self._ov = ov
        box = tk.Frame(ov, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=36, pady=28)
        box.place(relx=0.5, rely=0.42, anchor="center")
        tk.Label(box, text="◆ TD2 Rapor Paneli", bg=C["panel"], fg=C["accent2"], font=("Segoe UI Semibold", 16)).pack(anchor="w")
        info = ("Paneli korumak için bir PIN belirle (en az %d karakter, rakam ya da harf).\n"
                "Windows şifresi gerekmez. PIN hiçbir yerde saklanmaz; belirteçler bununla şifrelenir." % lock.MIN_LEN) if setup \
            else "Panel kilitli. Devam etmek için PIN'ini gir."
        tk.Label(box, text=info, bg=C["panel"], fg=C["dim"], font=("Segoe UI", 10), justify="left").pack(anchor="w", pady=(6, 14))
        v1, v2 = tk.StringVar(), tk.StringVar()
        e1 = ttk.Entry(box, textvariable=v1, show="•", width=34, font=("Segoe UI", 12)); e1.pack(fill="x")
        e2 = None
        if setup:
            tk.Label(box, text="PIN'i tekrar yaz", bg=C["panel"], fg=C["dim"], font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 2))
            e2 = ttk.Entry(box, textvariable=v2, show="•", width=34, font=("Segoe UI", 12)); e2.pack(fill="x")
        msg = tk.Label(box, text="", bg=C["panel"], fg=C["bad"], font=("Segoe UI", 9), justify="left"); msg.pack(anchor="w", pady=(8, 0))
        bf = tk.Frame(box, bg=C["panel"]); bf.pack(fill="x", pady=(12, 0))

        def go(_e=None):
            pin = v1.get()
            if setup:
                if not lock.valid_pin(pin): return msg.config(text="PIN en az %d karakter olmalı (boşluksuz)." % lock.MIN_LEN)
                if pin != v2.get(): return msg.config(text="İki PIN aynı değil.")
                rec, key = lock.make(pin)
                self.settings["pin"], self.key = rec, key
                self._save()                                          # mevcut belirteçler artık PIN ile de şifreli
                return self._unlocked()
            key, wait = lock.check(self.settings["pin"], pin)
            self._save_pin_state()
            if key is None:
                v1.set("")
                if wait: return msg.config(text=f"Çok fazla yanlış deneme. {wait} sn sonra tekrar dene.")
                left = lock.FREE_TRIES - int(self.settings["pin"].get("fails", 0))
                return msg.config(text="PIN yanlış." + (f" {left} deneme hakkın kaldı." if 0 < left <= 3 else ""))
            self.key = key
            for k, val in self._sealed.items():
                try: self.settings[k] = lock.decrypt(key, val)
                except Exception: self.settings[k] = ""
            self._unlocked()

        def forgot():
            if not messagebox.askyesno(APP_NAME, "PIN sıfırlansın mı?\n\nGüvenlik için kayıtlı GitHub token ve yönetici belirteci silinir; "
                                       "yeni PIN'den sonra Ayarlar'dan yeniden girmen gerekir.", parent=self.root):
                return
            self.settings.pop("pin", None); self.key = None; self._sealed = {}
            for k in SECRET: self.settings[k] = ""
            self._save(); ov.destroy(); self._lock_screen(setup=True)

        ttk.Button(bf, text="PIN oluştur" if setup else "Kilidi aç", style="Accent.TButton", command=go).pack(side="right")
        if not setup:
            tk.Button(bf, text="PIN'i unuttum", command=forgot, bg=C["panel"], fg=C["dim"], bd=0, activebackground=C["panel"],
                      activeforeground=C["text"], font=("Segoe UI", 9, "underline"), cursor="hand2").pack(side="left")
        e1.bind("<Return>", go)
        if e2: e2.bind("<Return>", go)
        self.root.after(100, lambda: e1.winfo_exists() and e1.focus_set())
        self._lock_go = go; self._lock_vars = (v1, v2)                  # testler için

    def _save_pin_state(self):
        try:
            p = config_path(); d = json.loads(p.read_text(encoding="utf-8")); d["pin"] = self.settings["pin"]
            tmp = p.with_name(p.name + ".tmp"); tmp.write_text(json.dumps(d, indent=2), encoding="utf-8"); os.replace(tmp, p)
        except Exception:
            pass

    def _unlocked(self):
        self.locked = False
        ov = getattr(self, "_ov", None)
        if ov is not None:
            ov.destroy(); self._ov = None
        self._last_input = time.time()
        if self._started: return
        self._started = True
        self._apply_settings()
        if not (self.settings.get("repo") and self.settings.get("token")):
            self.root.after(300, self.open_settings)
        self.root.after(5 * 60 * 1000, self._auto)
        self.root.after(3 * 60 * 1000, self._poll)
        if getattr(sys, "frozen", False) and self.settings.get("update_check", True):
            self.root.after(4000, lambda: self.check_update(quiet=True))

    def lock_now(self):
        if self.locked or os.environ.get("TD2_PANEL_NOLOCK") or not self.settings.get("pin"): return
        self._lock_screen()

    def _idle_check(self):
        mins = int(self.settings.get("lock_minutes") or 0)
        if mins and not self.locked and time.time() - self._last_input > mins * 60: self.lock_now()
        self.root.after(30 * 1000, self._idle_check)

    # ---------- tepsi ve bildirimler
    def show(self):
        self.root.deiconify(); self.root.lift()
        try: self.root.focus_force()
        except Exception: pass

    def on_close(self):
        if self.tray.available and self.settings.get("tray", True):
            self.root.withdraw()
            if not getattr(self, "_tray_hint", False):
                self._tray_hint = True; self.tray.notify("Panel tepside çalışmaya devam ediyor. Kapatmak için tepsi simgesi → Çıkış.")
        else:
            self.quit()

    def quit(self):
        self._closing = True
        self.tray.stop(); self.root.destroy()

    def poll_now(self):
        if not self.locked: self.refresh(); self._poll(reschedule=False)

    def _poll(self, reschedule=True):
        if reschedule: self.root.after(3 * 60 * 1000, self._poll)
        if self.locked and not self.key and self.settings.get("pin"): return
        if self.gh: self.refresh()
        self.dash.refresh(done=self._notify)

    def _notify(self, d):
        ev = (d or {}).get("events") or {}
        text = summarize(ev, self._new_reports)
        if (d or {}).get("now"):
            first = not self.settings.get("notify_since")
            self.settings["notify_since"] = d["now"]; self._save_key("notify_since")
            if first: return                                        # ilk çalıştırmada eski olaylar için bildirim yok
        self._new_reports = 0
        if text: self.tray.notify(text)

    def _save_key(self, k):
        try:
            p = config_path(); d = json.loads(p.read_text(encoding="utf-8")); d[k] = self.settings[k]
            tmp = p.with_name(p.name + ".tmp"); tmp.write_text(json.dumps(d, indent=2), encoding="utf-8"); os.replace(tmp, p)
        except Exception:
            pass

    def goto(self, name):
        tab = {"reports": self.tab_r, "users": self.lic.f, "tasks": self.tasks_tab.f, "suggest": self.sug_tab.f}.get(name)
        if tab is not None: self.main_nb.select(tab)

    # ---------- kendini güncelleme
    def check_update(self, quiet=False):
        s = self.settings
        if not (s.get("repo") and s.get("token")):
            if not quiet: messagebox.showinfo(APP_NAME, "Güncelleme için Ayarlar'da depo ve GitHub token gerekli.", parent=self.root)
            return
        def work():
            try: return True, selfupdate.latest(s.get("api") or "https://api.github.com", s["repo"], s["token"], VERSION)
            except Exception as e: return False, str(e)
        def done(r):
            ok, info = r
            if not ok:
                if not quiet: messagebox.showwarning(APP_NAME, "Güncelleme denetlenemedi: " + info, parent=self.root)
                return
            if not info:
                if not quiet: messagebox.showinfo(APP_NAME, f"Panel güncel ({VERSION}).", parent=self.root)
                return
            if not messagebox.askyesno(APP_NAME, f"Panel {info['version']} hazır (şu an {VERSION}).\n\n{info['notes'][:600]}\n\nŞimdi güncellensin mi?",
                                       parent=self.root):
                return
            if not getattr(sys, "frozen", False):
                return messagebox.showinfo(APP_NAME, "Kaynak koddan çalışıyor: güncelleme yalnız derlenmiş exe'de kurulur.", parent=self.root)
            self._status("Güncelleme indiriliyor ve doğrulanıyor…", C["info"])
            def dl():
                try: data = selfupdate.download(info, s["token"]); selfupdate.install(data); return True, ""
                except Exception as e: return False, str(e)
            def fin(r2):
                if r2[0]: self.quit()
                else: messagebox.showerror(APP_NAME, "Güncelleme kurulmadı: " + r2[1], parent=self.root); self._status("Güncelleme kurulmadı.", C["bad"])
            self._bg(dl, fin)
        self._bg(work, done)

    # ---------- ayar penceresi
    def open_settings(self):
        if self.locked: return
        w = tk.Toplevel(self.root); w.title("Ayarlar"); w.configure(bg=C["panel"]); w.transient(self.root); w.resizable(False, False)
        try: w.iconbitmap(str(resource("icon/td2.ico")))
        except Exception: pass
        f = ttk.Frame(w, padding=18); f.pack(fill="both")
        vars_ = {}
        rows = (("repo", "Rapor deposu (sahip/ad)", False), ("token", "GitHub token (Issues: okuma-yazma)", True),
                ("admin_login", "Senin GitHub adın (yanıtların yeşil görünür)", False), ("api", "API adresi", False),
                ("acc_url", "Hesap sunucusu (worker adresi)", False), ("admin_token", "Yönetici belirteci (ADMIN_TOKEN)", True))
        for r, (k, label, secret) in enumerate(rows):
            ttk.Label(f, text=label, style="Dim.TLabel").grid(row=r * 2, column=0, sticky="w", pady=(6 if r else 0, 2))
            v = tk.StringVar(value=self.settings.get(k, "")); vars_[k] = v
            e = ttk.Entry(f, textvariable=v, width=58, show="•" if secret else ""); e.grid(row=r * 2 + 1, column=0, sticky="ew")
            if secret:
                ttk.Checkbutton(f, text="göster", command=lambda e=e: e.config(show="" if e.cget("show") else "•")).grid(row=r * 2 + 1, column=1, padx=6)
        o = ttk.Frame(f); o.grid(row=14, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        v_tray = tk.BooleanVar(value=bool(self.settings.get("tray", True)))
        v_upd = tk.BooleanVar(value=bool(self.settings.get("update_check", True)))
        v_lock = tk.StringVar(value=str(self.settings.get("lock_minutes", 10)))
        ttk.Checkbutton(o, text="Kapatınca tepside çalışmaya devam et (bildirimler)", variable=v_tray).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Checkbutton(o, text="Açılışta panel güncellemelerini denetle", variable=v_upd).grid(row=1, column=0, columnspan=3, sticky="w")
        ttk.Label(o, text="Boşta kalınca kilitle (dakika, 0 = kapalı):", style="Dim.TLabel").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(o, textvariable=v_lock, values=["0", "5", "10", "15", "30", "60"], width=5, state="readonly").grid(row=2, column=1, sticky="w", padx=6, pady=(6, 0))
        ob = ttk.Frame(o); ob.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Button(ob, text="PIN'i değiştir", command=lambda: (w.destroy(), self.change_pin())).pack(side="left")
        ttk.Button(ob, text="Güncellemeleri denetle", command=lambda: self.check_update(quiet=False)).pack(side="left", padx=6)
        msg = ttk.Label(f, text="Token yalnız bu bilgisayarda saklanır (PIN + Windows ile şifreli):\n" + str(config_path()), style="Dim.TLabel", justify="left")
        msg.grid(row=19, column=0, columnspan=2, sticky="w", pady=(12, 8))
        bf = ttk.Frame(f); bf.grid(row=20, column=0, columnspan=2, sticky="ew")

        def collect():
            return {k: v.get().strip() for k, v in vars_.items()}

        def test():
            d = collect(); msg.config(text="Deneniyor…", foreground=C["info"])
            gh = GitHub(d["token"], d["repo"], d["api"])
            from license_tab import AdminAPI
            def both():
                r1 = gh.check() if d["token"] else (False, "GitHub token yok")
                r2 = AdminAPI(d["acc_url"], d["admin_token"]).call("GET", "stats") if d["admin_token"] else (False, "yönetici belirteci yok")
                return r1, r2
            def show(r):
                (o1, m1), (o2, m2) = r
                msg.config(text=("✔ " if o1 else "✖ ") + "GitHub: " + str(m1) + "\n" + ("✔ Hesap sunucusu: bağlandı" if o2 else "✖ Hesap sunucusu: " + str(m2)),
                           foreground=C["ok"] if o1 and o2 else C["warn"] if o1 or o2 else C["bad"])
            self._bg(both, show)

        def save():
            self.settings.update(collect())
            self.settings.update(tray=v_tray.get(), update_check=v_upd.get(), lock_minutes=int(v_lock.get() or 0))
            self._save(); w.destroy(); self._apply_settings()
        ttk.Button(bf, text="Bağlantıyı dene", command=test).pack(side="left")
        ttk.Button(bf, text="Kaydet", style="Accent.TButton", command=save).pack(side="right")
        ttk.Button(bf, text="Vazgeç", command=w.destroy).pack(side="right", padx=6)
        w.grab_set()
        self._settings_win = w


    def change_pin(self):
        if os.environ.get("TD2_PANEL_NOLOCK"): return
        if not messagebox.askyesno(APP_NAME, "Yeni bir PIN belirlemek için panel kilitlenecek ve PIN oluşturma ekranı açılacak.\n"
                                   "Kayıtlı belirteçlerin yeni PIN ile yeniden şifrelenir. Devam edilsin mi?", parent=self.root):
            return
        self.settings.pop("pin", None)                                # anahtar bellekte; belirteçler bellekte düz
        self.key = None
        self._lock_screen(setup=True)


def main():
    root = tk.Tk()
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    Panel(root)
    if "--selfcheck" in sys.argv:          # CI: arayüz kurulabildi mi? 3 sn sonra 0 koduyla çık
        root.after(3000, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()

