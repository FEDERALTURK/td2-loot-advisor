#!/usr/bin/env python3
"""TD2 Rapor Paneli — kullanıcıların programdan gönderdiği hata raporlarını ve istekleri yönetir.

Raporlar özel GitHub deposunda (ör. FEDERALTURK/td2-loot-advisor-reports) issue olarak durur. Panel onları listeler,
filtreler, durumlarını değiştirir (status:* etiketleri), yanıt yazar (kullanıcı programdaki "Raporlarım"da görür),
kapatır/açar ve CSV'ye aktarır. Ayarlar (token dahil) yalnız bu bilgisayarda: %APPDATA%\\TD2RaporPaneli\\settings.json
"""
import csv
import json
import os
import sys
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_api import GitHub, STATUSES  # noqa: E402

APP_NAME = "TD2 Rapor Paneli"
VERSION = "1.0.0"

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


def resource(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / name


def ago(iso):
    try:
        t = datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S")
        d = (datetime.utcnow() - t).total_seconds()
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
        self.settings = self._load()
        self.issues, self.view, self.cur = [], [], None
        self.gh = None
        self._style()
        self._build()
        self._apply_settings()
        root.bind("<F5>", lambda e: self.refresh())
        root.bind("<Control-f>", lambda e: self.e_search.focus_set())
        if not (self.settings.get("repo") and self.settings.get("token")):
            root.after(300, self.open_settings)
        root.after(5 * 60 * 1000, self._auto)

    # ---------- ayarlar
    def _load(self):
        d = {"repo": "FEDERALTURK/td2-loot-advisor-reports", "token": "", "api": "https://api.github.com", "admin_login": "FEDERALTURK"}
        try: d.update(json.loads(config_path().read_text(encoding="utf-8")))
        except Exception: pass
        return d

    def _save(self):
        p = config_path(); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def _apply_settings(self):
        s = self.settings
        self.gh = GitHub(s["token"], s["repo"], s.get("api")) if s.get("repo") and s.get("token") else None
        self.l_repo.config(text=s.get("repo") or "depo ayarlanmadı")
        if self.gh: self.refresh()
        else: self._status("Ayarlar'dan depo ve token gir.", C["warn"])

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
        st.configure("Vertical.TScrollbar", background=C["panel2"], troughcolor=C["panel"], arrowcolor=C["dim"])

    def _build(self):
        top = ttk.Frame(self.root, style="Bg.TFrame", padding=(16, 12, 16, 8)); top.pack(fill="x")
        ttk.Label(top, text="◆ TD2 Rapor Paneli", style="H.TLabel").pack(side="left")
        self.l_repo = ttk.Label(top, text="", style="Sub.TLabel"); self.l_repo.pack(side="left", padx=14)
        ttk.Button(top, text="⚙ Ayarlar", command=self.open_settings).pack(side="right")
        ttk.Button(top, text="⇩ CSV", command=self.export_csv).pack(side="right", padx=6)
        ttk.Button(top, text="⟳ Yenile (F5)", style="Accent.TButton", command=self.refresh).pack(side="right")

        body = ttk.Frame(self.root, style="Bg.TFrame", padding=(16, 0, 16, 0)); body.pack(fill="both", expand=True)
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

        self.l_status = tk.Label(self.root, text="", anchor="w", bg=C["bg"], fg=C["dim"], font=("Segoe UI", 9), padx=16, pady=6)
        self.l_status.pack(fill="x", side="bottom")

    def _status(self, text, color=None):
        self.l_status.config(text=text, fg=color or C["dim"])

    # ---------- veri
    def _bg(self, fn, done):
        def run():
            res = fn()
            self.root.after(0, lambda: done(res))
        threading.Thread(target=run, daemon=True).start()

    def refresh(self):
        if not self.gh: return self.open_settings()
        self._status("Yükleniyor…", C["info"])
        self._bg(lambda: self.gh.issues("all"), self._loaded)

    def _loaded(self, res):
        ok, data = res
        if not ok:
            self._status(f"Hata: {data}", C["bad"]); return
        keep = self.cur["number"] if self.cur else None
        self.issues = data
        self._stats()
        self.apply_filter()
        if keep and self.tree.exists(str(keep)): self.tree.selection_set(str(keep))
        self._status(f"{len(data)} rapor yüklendi · {datetime.now():%H:%M:%S}", C["ok"])

    def _auto(self):
        if self.gh: self.refresh()
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

    # ---------- ayar penceresi
    def open_settings(self):
        w = tk.Toplevel(self.root); w.title("Ayarlar"); w.configure(bg=C["panel"]); w.transient(self.root); w.resizable(False, False)
        try: w.iconbitmap(str(resource("icon/td2.ico")))
        except Exception: pass
        f = ttk.Frame(w, padding=18); f.pack(fill="both")
        vars_ = {}
        rows = (("repo", "Rapor deposu (sahip/ad)", False), ("token", "GitHub token (Issues: okuma-yazma)", True),
                ("admin_login", "Senin GitHub adın (yanıtların yeşil görünür)", False), ("api", "API adresi", False))
        for r, (k, label, secret) in enumerate(rows):
            ttk.Label(f, text=label, style="Dim.TLabel").grid(row=r * 2, column=0, sticky="w", pady=(6 if r else 0, 2))
            v = tk.StringVar(value=self.settings.get(k, "")); vars_[k] = v
            e = ttk.Entry(f, textvariable=v, width=58, show="•" if secret else ""); e.grid(row=r * 2 + 1, column=0, sticky="ew")
            if secret:
                ttk.Checkbutton(f, text="göster", command=lambda e=e: e.config(show="" if e.cget("show") else "•")).grid(row=r * 2 + 1, column=1, padx=6)
        msg = ttk.Label(f, text="Token yalnız bu bilgisayarda saklanır:\n" + str(config_path()), style="Dim.TLabel", justify="left")
        msg.grid(row=9, column=0, columnspan=2, sticky="w", pady=(12, 8))
        bf = ttk.Frame(f); bf.grid(row=10, column=0, columnspan=2, sticky="ew")

        def collect():
            return {k: v.get().strip() for k, v in vars_.items()}

        def test():
            d = collect(); msg.config(text="Deneniyor…", foreground=C["info"])
            gh = GitHub(d["token"], d["repo"], d["api"])
            self._bg(gh.check, lambda r: msg.config(text=("✔ " if r[0] else "✖ ") + r[1], foreground=C["ok"] if r[0] else C["bad"]))

        def save():
            self.settings.update(collect()); self._save(); w.destroy(); self._apply_settings()
        ttk.Button(bf, text="Bağlantıyı dene", command=test).pack(side="left")
        ttk.Button(bf, text="Kaydet", style="Accent.TButton", command=save).pack(side="right")
        ttk.Button(bf, text="Vazgeç", command=w.destroy).pack(side="right", padx=6)
        w.grab_set()
        self._settings_win = w


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
