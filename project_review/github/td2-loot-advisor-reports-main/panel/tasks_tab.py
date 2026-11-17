"""Panel sekmesi: topluluk görevleri (oyuncuların canlı çeviriyle gönderdiği görev ekranları).

Hesap sunucusunun /v1/admin/tasks uçlarını kullanır (aynı yönetici belirteci). Buradan:
  - tüm görevler: kaç farklı oyuncudan geldiği, ilk / son görülme, herkese açık mı (≥2 oyuncu), hangi sürümlerden
  - metnin ve Türkçe çevirinin farklı hâlleri (kaç oyuncu hangisini gönderdi)
  - görevi listeden gizle / geri aç, Türkçe çeviriyi elle düzelt (tüm oyunculara düzeltilmiş hâli gider)
  - JSON dışa aktar
Ham gönderen kimlikleri sunucuda bile yalnız tuzlu özet olarak durur; panel onları göstermez.
"""
import json
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from license_tab import AdminAPI

CAT = {"project": "Proje", "bounty": "Ödül avı", "assignment": "Görevlendirme", "other": "Diğer"}
PER = {"daily": "Günlük", "weekly": "Haftalık", "season": "Sezon", "other": "—"}
FIELDS = (("title", "Başlık"), ("subtitle", "Alt başlık"), ("desc", "Açıklama"), ("objective", "Hedef"))


def fmt_t(ts):
    return datetime.fromtimestamp(ts).strftime("%d.%m %H:%M") if ts else "—"


class TasksTab:
    def __init__(self, parent, panel, C):
        self.p, self.C, self.api = panel, C, None
        self.data, self.rows = None, {}
        self.f = ttk.Frame(parent, style="Bg.TFrame", padding=(16, 8, 16, 0))
        self._build()

    def configure(self, url, token):
        self.api = AdminAPI(url, token) if url and token else None
        if self.api: self.refresh()

    def bg(self, fn, done):
        def run():
            r = fn(); self.f.after(0, lambda: done(r))
        threading.Thread(target=run, daemon=True).start()

    def _build(self):
        C = self.C
        st = ttk.Frame(self.f, style="Bg.TFrame"); st.pack(fill="x", pady=(0, 8))
        self.stat = {}
        for k, name, col in (("all", "Toplanan görev", C["text"]), ("public", "Herkese açık (≥2 oyuncu)", C["ok"]),
                             ("waiting", "Onay bekleyen (1 oyuncu)", C["warn"]), ("tr", "Çevirisi hazır", C["info"])):
            box = ttk.Frame(st, padding=(14, 8)); box.pack(side="left", padx=(0, 10))
            self.stat[k] = ttk.Label(box, text="–", style="Num.TLabel", foreground=col); self.stat[k].pack(anchor="w")
            ttk.Label(box, text=name, style="Dim.TLabel").pack(anchor="w")
        ttk.Button(st, text="⟳ Yenile", style="Accent.TButton", command=self.refresh).pack(side="right")
        ttk.Button(st, text="⬇ JSON", command=self.export).pack(side="right", padx=6)

        body = ttk.Frame(self.f, style="Bg.TFrame"); body.pack(fill="both", expand=True)
        right = ttk.Frame(body, padding=14, width=470); right.pack(side="right", fill="y"); right.pack_propagate(False)
        ttk.Label(right, text="AYRINTI", style="Sec.TLabel").pack(anchor="w")
        bar = ttk.Frame(right); bar.pack(side="bottom", fill="x", pady=8)
        ttk.Button(bar, text="✏ Çeviriyi düzelt", style="Accent.TButton", command=self.edit_tr).pack(side="left")
        ttk.Button(bar, text="🙈 Gizle / göster", command=self.toggle_hide).pack(side="left", padx=6)
        self.detail = tk.Text(right, height=14, wrap="word", bg=C["entry"], fg=C["text"], bd=0, padx=10, pady=8,
                              font=("Segoe UI", 10), highlightthickness=1, highlightbackground=C["line"])
        self.detail.tag_configure("h", foreground=C["accent"], font=("Segoe UI Semibold", 10))
        self.detail.tag_configure("dim", foreground=C["dim"])
        self.detail.pack(fill="both", expand=True)

        left = ttk.Frame(body); left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        fbar = ttk.Frame(left); fbar.pack(fill="x", pady=(0, 6))
        self.q = tk.StringVar(); e = ttk.Entry(fbar, textvariable=self.q, width=30); e.pack(side="left")
        e.bind("<KeyRelease>", lambda ev: self.fill())
        self.only_wait = tk.BooleanVar(value=False)
        ttk.Checkbutton(fbar, text="Yalnız onay bekleyenler", variable=self.only_wait, command=self.fill).pack(side="left", padx=10)
        fr = ttk.Frame(left); fr.pack(fill="both", expand=True)
        cols = (("title", "Görev", 260, "w"), ("cat", "Tür", 110, "w"), ("n", "Oyuncu", 60, "center"), ("pub", "Durum", 110, "w"),
                ("tr", "Türkçe", 90, "w"), ("last", "Son görülme", 100, "w"), ("exp", "Bitiş", 100, "w"))
        self.tv = ttk.Treeview(fr, columns=[c for c, *_ in cols], show="headings", selectmode="browse")
        for c, t, w, a in cols:
            self.tv.heading(c, text=t); self.tv.column(c, width=w, anchor=a, stretch=(c == "title"))
        sb = ttk.Scrollbar(fr, orient="vertical", command=self.tv.yview); self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        for tag, col in (("pub", C["ok"]), ("wait", C["warn"]), ("hid", C["dim"])): self.tv.tag_configure(tag, foreground=col)
        self.tv.bind("<<TreeviewSelect>>", lambda e: self.show())

    # ---- veri
    def refresh(self):
        if not self.api:
            self.p.open_settings(); return
        self.p._status("Topluluk görevleri yükleniyor…")
        self.bg(lambda: self.api.call("GET", "tasks"), self._loaded)

    def _loaded(self, r):
        ok, d = r
        if not ok:
            self.p._status("Görevler alınamadı: " + str(d), self.C["bad"]); return
        self.data = d
        minr = d.get("min_reporters", 2)
        ts = d.get("tasks", [])
        self.stat["all"].config(text=str(len(ts)))
        self.stat["public"].config(text=str(sum(1 for x in ts if x["reporters"] >= minr and not x.get("hidden"))))
        self.stat["waiting"].config(text=str(sum(1 for x in ts if x["reporters"] < minr)))
        self.stat["tr"].config(text=str(sum(1 for x in ts if x.get("tr"))))
        self.fill()
        self.p._status(f"{len(ts)} görev yüklendi", self.C["ok"])

    def fill(self):
        if not self.data: return
        minr = self.data.get("min_reporters", 2)
        sel = self.tv.selection()
        self.tv.delete(*self.tv.get_children()); self.rows = {}
        q = self.q.get().strip().lower()
        for x in self.data.get("tasks", []):
            if q and q not in (x["title"] + " " + x.get("objective", "") + " " + (x.get("subtitle") or "")).lower(): continue
            if self.only_wait.get() and x["reporters"] >= minr: continue
            pub = "gizli" if x.get("hidden") else ("herkese açık" if x["reporters"] >= minr else "onay bekliyor")
            tag = "hid" if x.get("hidden") else ("pub" if x["reporters"] >= minr else "wait")
            trs = {"admin": "düzeltildi", "community": "topluluk"}.get(x.get("tr_source"), "—")
            self.tv.insert("", "end", iid=x["key"], tags=(tag,), values=(
                x["title"] + (f" · {x['subtitle']}" if x.get("subtitle") else ""), f"{CAT.get(x.get('category'), '—')} / {PER.get(x.get('period'), '—')}",
                x["reporters"], pub, trs, fmt_t(x.get("last_seen")), fmt_t(x.get("expires_at"))))
            self.rows[x["key"]] = x
        for s in sel:
            if self.tv.exists(s): self.tv.selection_set(s)

    def cur(self):
        s = self.tv.selection()
        return self.rows.get(s[0]) if s else None

    def show(self):
        x = self.cur(); T = self.detail
        T.config(state="normal"); T.delete("1.0", "end")
        if not x: T.config(state="disabled"); return
        T.insert("end", x["title"] + "\n", "h")
        if x.get("subtitle"): T.insert("end", x["subtitle"] + "\n")
        T.insert("end", f"{x['reporters']} oyuncu · ilk {fmt_t(x.get('first_seen'))} · son {fmt_t(x.get('last_seen'))} · "
                        f"sürümler: {', '.join(x.get('apps') or [])}\n\n", "dim")
        if x.get("desc"): T.insert("end", x["desc"] + "\n\n")
        T.insert("end", "Hedef: ", "h"); T.insert("end", x.get("objective", "") + (f"  (0/{x['total']})" if x.get("total") else "") + "\n")
        if x.get("rewards"): T.insert("end", "Ödüller: ", "h"); T.insert("end", ", ".join(x["rewards"]) + "\n")
        T.insert("end", "\nYAYINDAKİ TÜRKÇE", "h"); T.insert("end", f"  ({ {'admin': 'senin düzeltmen', 'community': 'oyunculardan'}.get(x.get('tr_source'), 'yok')})\n", "dim")
        for k, lab in FIELDS:
            if (x.get("tr") or {}).get(k): T.insert("end", f"{lab}: ", "dim"); T.insert("end", x["tr"][k] + "\n")
        v = x.get("variants") or {}
        if len(v.get("tr", [])) > 1 or len(v.get("en", [])) > 1:
            T.insert("end", "\nFARKLI HÂLLER\n", "h")
            for kind, lst in (("İngilizce", v.get("en", [])), ("Türkçe", v.get("tr", []))):
                for it in lst:
                    T.insert("end", f"{kind} ×{it['n']}: ", "dim"); T.insert("end", (it.get("objective") or it.get("title") or "") + "\n")
        T.config(state="disabled")

    # ---- işlemler
    def toggle_hide(self):
        x = self.cur()
        if not x: return
        def done(r):
            ok, d = r
            self.p._status("Güncellendi" if ok else f"Hata: {d}", self.C["ok"] if ok else self.C["bad"])
            if ok: self.refresh()
        self.bg(lambda: self.api.call("POST", "tasks/hide", {"key": x["key"], "hidden": not x.get("hidden")}), done)

    def edit_tr(self):
        x = self.cur()
        if not x: return
        C = self.C
        w = self.edit_win = tk.Toplevel(self.f); w.title("Türkçe çeviriyi düzelt"); w.configure(bg=C["bg"]); w.transient(self.f.winfo_toplevel())
        ents = {}
        for r, (k, lab) in enumerate(FIELDS):
            if not x.get(k): continue
            ttk.Label(w, text=lab, style="Sec.TLabel").grid(row=r * 2, column=0, sticky="w", padx=12, pady=(10, 0))
            ttk.Label(w, text=x[k], style="Dim.TLabel", wraplength=560).grid(row=r * 2, column=1, sticky="w", padx=6, pady=(10, 0))
            tx = tk.Text(w, height=3 if k == "desc" else 1, width=70, wrap="word", bg=C["entry"], fg=C["text"], insertbackground=C["text"], bd=0, padx=6, pady=4)
            tx.insert("1.0", (x.get("tr") or {}).get(k, "")); tx.grid(row=r * 2 + 1, column=0, columnspan=2, sticky="we", padx=12, pady=2)
            ents[k] = tx
        bar = ttk.Frame(w); bar.grid(row=20, column=0, columnspan=2, sticky="e", padx=12, pady=12)
        def save(clear=False):
            tr = None if clear else {k: e.get("1.0", "end").strip() for k, e in ents.items() if e.get("1.0", "end").strip()}
            def done(r):
                ok, d = r
                self.p._status("Çeviri kaydedildi — oyunculara en geç 1 saatte ulaşır" if ok else f"Hata: {d}", C["ok"] if ok else C["bad"])
                if ok: w.destroy(); self.refresh()
            self.bg(lambda: self.api.call("POST", "tasks/override", {"key": x["key"], "tr": tr}), done)
        ttk.Button(bar, text="Düzeltmeyi kaldır", command=lambda: save(True)).pack(side="left", padx=6)
        ttk.Button(bar, text="💾 Kaydet", style="Accent.TButton", command=save).pack(side="left")

    def export(self):
        if not self.data: return
        p = filedialog.asksaveasfilename(defaultextension=".json", initialfile="topluluk_gorevleri.json", filetypes=[("JSON", "*.json")])
        if not p: return
        with open(p, "w", encoding="utf-8") as f: json.dump(self.data, f, ensure_ascii=False, indent=1)
        messagebox.showinfo("Görevler", "Kaydedildi: " + p)


class SuggestTab:
    """Oyuncuların çeviri satırları için önerdiği daha iyi Türkçeler. Onaylanan satır herkesin çeviri hafızasına girer
    (en geç 1 saatte). Aynı öneriyi yapan oyuncu sayısı gösterilir."""

    def __init__(self, parent, panel, C):
        self.p, self.C, self.api, self.rows = panel, C, None, {}
        self.f = ttk.Frame(parent, style="Bg.TFrame", padding=(16, 8, 16, 0))
        bar = ttk.Frame(self.f, style="Bg.TFrame"); bar.pack(fill="x", pady=(0, 8))
        self.status = tk.StringVar(value="pending")
        for val, lab in (("pending", "Bekleyen"), ("approved", "Onaylanan"), ("rejected", "Reddedilen")):
            ttk.Radiobutton(bar, text=lab, value=val, variable=self.status, command=self.refresh).pack(side="left", padx=(0, 10))
        ttk.Button(bar, text="⟳ Yenile", style="Accent.TButton", command=self.refresh).pack(side="right")
        body = ttk.Frame(self.f, style="Bg.TFrame"); body.pack(fill="both", expand=True)
        right = ttk.Frame(body, padding=14, width=470); right.pack(side="right", fill="y"); right.pack_propagate(False)
        ttk.Label(right, text="ÖNERİ", style="Sec.TLabel").pack(anchor="w")
        bbar = ttk.Frame(right); bbar.pack(side="bottom", fill="x", pady=8)
        ttk.Button(bbar, text="✔ Onayla", style="Accent.TButton", command=lambda: self.decide(True)).pack(side="left")
        ttk.Button(bbar, text="✖ Reddet", command=lambda: self.decide(False)).pack(side="left", padx=6)
        ttk.Button(bbar, text="🗑 Onaylı satırı kaldır", command=self.remove_line).pack(side="right")
        self.info = tk.Text(right, height=8, wrap="word", bg=C["entry"], fg=C["text"], bd=0, padx=10, pady=8, font=("Segoe UI", 10),
                            highlightthickness=1, highlightbackground=C["line"])
        self.info.tag_configure("dim", foreground=C["dim"]); self.info.tag_configure("h", foreground=C["accent"])
        self.info.pack(fill="x")
        ttk.Label(right, text="Yayınlanacak Türkçe (düzenleyebilirsin)", style="Dim.TLabel").pack(anchor="w", pady=(10, 2))
        self.edit = tk.Text(right, height=5, wrap="word", bg=C["entry"], fg=C["text"], insertbackground=C["text"], bd=0, padx=8, pady=6,
                            highlightthickness=1, highlightbackground=C["line"])
        self.edit.pack(fill="x")
        fr = ttk.Frame(body); fr.pack(side="left", fill="both", expand=True, padx=(0, 10))
        cols = (("n", "Oyuncu", 60, "center"), ("en", "İngilizce", 300, "w"), ("new", "Önerilen Türkçe", 300, "w"))
        self.tv = ttk.Treeview(fr, columns=[c for c, *_ in cols], show="headings", selectmode="browse")
        for c, t, w, a in cols:
            self.tv.heading(c, text=t); self.tv.column(c, width=w, anchor=a, stretch=(c != "n"))
        sb = ttk.Scrollbar(fr, orient="vertical", command=self.tv.yview); self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        self.tv.bind("<<TreeviewSelect>>", lambda e: self.show())

    def configure(self, url, token):
        self.api = AdminAPI(url, token) if url and token else None
        if self.api: self.refresh()

    def bg(self, fn, done):
        threading.Thread(target=lambda: (lambda r: self.f.after(0, lambda: done(r)))(fn()), daemon=True).start()

    def refresh(self):
        if not self.api: return
        st = self.status.get()
        self.bg(lambda: self.api.call("GET", "suggestions?status=" + st), self._loaded)

    def _loaded(self, r):
        ok, d = r
        if not ok: return self.p._status("Öneriler alınamadı: " + str(d), self.C["bad"])
        self.tv.delete(*self.tv.get_children()); self.rows = {}
        for x in d.get("suggestions", []):
            iid = str(x["id"]); self.rows[iid] = x
            self.tv.insert("", "end", iid=iid, values=(x["n"], x["en"], x["new"]))
        self.p._status(f"{len(self.rows)} öneri", self.C["ok"])

    def cur(self):
        s = self.tv.selection(); return self.rows.get(s[0]) if s else None

    def show(self):
        x = self.cur(); T = self.info
        T.config(state="normal"); T.delete("1.0", "end")
        if x:
            T.insert("end", x["en"] + "\n\n", "dim")
            T.insert("end", "Program: ", "h"); T.insert("end", (x.get("old") or "—") + "\n")
            if x.get("current"): T.insert("end", "Yayındaki: ", "h"); T.insert("end", x["current"] + "\n")
            T.insert("end", f"\n{x['n']} oyuncu bu öneriyi yaptı", "dim")
            self.edit.delete("1.0", "end"); self.edit.insert("1.0", x["new"])
        T.config(state="disabled")

    def decide(self, approve):
        x = self.cur()
        if not x: return
        body = {"id": x["id"], "approve": approve}
        if approve:
            txt = self.edit.get("1.0", "end").strip()
            if txt and txt != x["new"]: body["text"] = txt
        def done(r):
            ok, d = r
            self.p._status(("Onaylandı — oyunculara en geç 1 saatte ulaşır" if approve else "Reddedildi") if ok else f"Hata: {d}",
                           self.C["ok"] if ok else self.C["bad"])
            if ok: self.refresh()
        self.bg(lambda: self.api.call("POST", "suggestions/decide", body), done)

    def remove_line(self):
        x = self.cur()
        if not x: return
        self.bg(lambda: self.api.call("POST", "suggestions/line", {"en_key": x["en_key"]}),
                lambda r: (self.p._status("Onaylı satır kaldırıldı" if r[0] else f"Hata: {r[1]}"), self.refresh()))

