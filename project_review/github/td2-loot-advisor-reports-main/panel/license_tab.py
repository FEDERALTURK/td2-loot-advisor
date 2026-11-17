"""Panel sekmesi: kullanıcılar, lisans anahtarları, davet kodları, denetim kaydı (hesap sunucusunun /v1/admin uçları).

Yönetici belirteci (ADMIN_TOKEN) yalnız bu bilgisayardaki panel ayarlarında durur ve yalnız HTTPS ile gönderilir.
Üretilen düz anahtarlar/davet kodları yalnız üretildikleri an görünür; sunucuda yalnız özetleri durur.
"""
import json
import threading
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from tkinter import messagebox, ttk


class AdminAPI:
    def __init__(self, url, token, opener=None):
        self.url, self.token = (url or "").rstrip("/"), token or ""
        self._open = opener or urllib.request.urlopen

    def call(self, method, path, body=None, q=None):
        if not self.url.startswith(("https://", "http://127.0.0.1")): return False, "sunucu adresi https olmalı"
        u = f"{self.url}/v1/admin/{path}" + (("?" + urllib.parse.urlencode({"q": q})) if q else "")
        req = urllib.request.Request(u, data=json.dumps(body).encode() if body is not None else None, method=method,
                                     headers={"Authorization": "Admin " + self.token, "Content-Type": "application/json",
                                              "User-Agent": "TD2Panel"})
        try:
            with self._open(req, timeout=20) as r: return True, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return False, {403: "yönetici belirteci yanlış", 404: "uç nokta yok (worker güncel mi?)"}.get(e.code, f"HTTP {e.code}")
        except Exception as e:
            return False, str(e)



def fmt_t(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "—"


def fmt_d(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "süresiz"


SRC_TR = {"admin": "anahtar", "invite": "davet", "gumroad": "satış"}


class LicenseTab:
    def __init__(self, parent, panel, C):
        self.p, self.C, self.api = panel, C, None
        self.f = ttk.Frame(parent, style="Bg.TFrame", padding=(16, 8, 16, 0))
        self._build()

    # ---- yardımcılar
    def configure(self, url, token):
        self.api = AdminAPI(url, token) if url and token else None
        if self.api: self.refresh()
        else: self.msg("Ayarlar'dan hesap sunucusu adresini ve yönetici belirtecini gir.", self.C["warn"])

    def msg(self, text, color=None):
        self.p._status(text, color)

    def bg(self, fn, done):
        def run():
            r = fn(); self.f.after(0, lambda: done(r))
        threading.Thread(target=run, daemon=True).start()

    def need(self):
        if not self.api:
            self.p.open_settings(); return False
        return True

    def tree(self, parent, cols, height=10):
        fr = ttk.Frame(parent); fr.pack(fill="both", expand=True)
        tv = ttk.Treeview(fr, columns=[c for c, *_ in cols], show="headings", height=height, selectmode="browse")
        for c, t, w, a in cols:
            tv.heading(c, text=t); tv.column(c, width=w, anchor=a, stretch=(a == "w"))
        sb = ttk.Scrollbar(fr, orient="vertical", command=tv.yview); tv.configure(yscrollcommand=sb.set)
        tv.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        for tag, col in (("off", self.C["dim"]), ("bad", self.C["bad"]), ("ok", self.C["ok"])): tv.tag_configure(tag, foreground=col)
        return tv

    # ---- görünüm
    def _build(self):
        C = self.C
        st = ttk.Frame(self.f, style="Bg.TFrame"); st.pack(fill="x", pady=(0, 8))
        self.stat = {}
        for k, name, col in (("accounts", "Hesap", C["text"]), ("active_licenses", "Etkin lisans", C["ok"]),
                             ("unused_keys", "Kullanılmamış anahtar", C["info"]), ("logins_24h", "24 sa giriş", C["accent"])):
            box = ttk.Frame(st, padding=(14, 8)); box.pack(side="left", padx=(0, 10))
            self.stat[k] = ttk.Label(box, text="–", style="Num.TLabel", foreground=col); self.stat[k].pack(anchor="w")
            ttk.Label(box, text=name, style="Dim.TLabel").pack(anchor="w")
        ttk.Button(st, text="⟳ Yenile", style="Accent.TButton", command=self.refresh).pack(side="right")

        body = ttk.Frame(self.f, style="Bg.TFrame"); body.pack(fill="both", expand=True)
        # sağ: üretim formları
        right = ttk.Frame(body, padding=14, width=360); right.pack(side="right", fill="y"); right.pack_propagate(False)
        ttk.Label(right, text="ANAHTAR ÜRET", style="Sec.TLabel").pack(anchor="w")
        g = ttk.Frame(right); g.pack(fill="x", pady=(4, 0))
        self.k_n, self.k_days, self.k_note = tk.StringVar(value="1"), tk.StringVar(value="30"), tk.StringVar()
        for r, (lab, var, w) in enumerate((("Adet", self.k_n, 6), ("Gün (boş = süresiz)", self.k_days, 8), ("Not", self.k_note, 22))):
            ttk.Label(g, text=lab, style="Dim.TLabel").grid(row=r, column=0, sticky="w", pady=2)
            ttk.Entry(g, textvariable=var, width=w).grid(row=r, column=1, sticky="w", padx=6, pady=2)
        ttk.Button(right, text="🔑 Üret", style="Accent.TButton", command=self.create_keys).pack(anchor="w", pady=6)
        ttk.Separator(right).pack(fill="x", pady=8)
        ttk.Label(right, text="DAVET / HEDİYE KODU", style="Sec.TLabel").pack(anchor="w")
        g2 = ttk.Frame(right); g2.pack(fill="x", pady=(4, 0))
        self.i_uses, self.i_days, self.i_valid, self.i_note = tk.StringVar(value="1"), tk.StringVar(value="7"), tk.StringVar(value="30"), tk.StringVar()
        for r, (lab, var, w) in enumerate((("Kullanım hakkı", self.i_uses, 6), ("Premium gün (boş = süresiz)", self.i_days, 8),
                                           ("Kod geçerlilik günü", self.i_valid, 8), ("Not", self.i_note, 22))):
            ttk.Label(g2, text=lab, style="Dim.TLabel").grid(row=r, column=0, sticky="w", pady=2)
            ttk.Entry(g2, textvariable=var, width=w).grid(row=r, column=1, sticky="w", padx=6, pady=2)
        ttk.Button(right, text="🎁 Davet kodu oluştur", style="Accent.TButton", command=self.create_invite).pack(anchor="w", pady=6)
        ttk.Label(right, text="SON ÜRETİLENLER (yalnız şimdi görünür — kopyala)", style="Sec.TLabel").pack(anchor="w", pady=(10, 2))
        self.out = tk.Text(right, height=8, bg=C["entry"], fg=C["ok"], insertbackground=C["text"], bd=0, padx=8, pady=6,
                           font=("Consolas", 10), highlightthickness=1, highlightbackground=C["line"])
        self.out.pack(fill="both", expand=True)
        ttk.Button(right, text="📋 Kopyala", command=self.copy_out).pack(anchor="w", pady=6)

        # orta: sekmeler
        nb = ttk.Notebook(body); nb.pack(side="left", fill="both", expand=True, padx=(0, 10))
        # kullanıcılar
        uf = ttk.Frame(nb, padding=8); nb.add(uf, text="👤 Kullanıcılar")
        bar = ttk.Frame(uf); bar.pack(fill="x", pady=(0, 6))
        self.u_q = tk.StringVar(); e = ttk.Entry(bar, textvariable=self.u_q, width=28); e.pack(side="left")
        e.bind("<Return>", lambda ev: self.load_accounts())
        ttk.Button(bar, text="Ara", command=self.load_accounts).pack(side="left", padx=6)
        ttk.Button(bar, text="⛔ Engelle / kaldır", command=self.toggle_ban).pack(side="right")
        self.tv_u = self.tree(uf, (("id", "#", 50, "e"), ("name", "Discord adı", 180, "w"), ("did", "Discord ID", 160, "w"),
                                   ("lic", "Etkin lisans", 90, "center"), ("since", "Kayıt", 130, "w"), ("last", "Son giriş", 130, "w"),
                                   ("ban", "Durum", 80, "w")))
        # lisanslar
        lf = ttk.Frame(nb, padding=8); nb.add(lf, text="🔑 Lisanslar")
        bar = ttk.Frame(lf); bar.pack(fill="x", pady=(0, 6))
        self.l_q = tk.StringVar(); e = ttk.Entry(bar, textvariable=self.l_q, width=28); e.pack(side="left")
        e.bind("<Return>", lambda ev: self.load_licenses())
        ttk.Button(bar, text="Ara", command=self.load_licenses).pack(side="left", padx=6)
        for txt, act in (("⛔ İptal / geri al", "revoke"), ("💻 Cihazı sıfırla", "reset_devices"), ("➕ 30 gün uzat", "extend")):
            ttk.Button(bar, text=txt, command=lambda a=act: self.lic_action(a)).pack(side="right", padx=(6, 0))
        self.tv_l = self.tree(lf, (("id", "#", 50, "e"), ("hint", "Anahtar", 70, "w"), ("src", "Kaynak", 70, "w"), ("user", "Kullanıcı", 150, "w"),
                                   ("exp", "Bitiş", 100, "w"), ("dev", "Cihaz", 60, "center"), ("note", "Not", 160, "w"), ("st", "Durum", 90, "w")))
        # davetler
        inf = ttk.Frame(nb, padding=8); nb.add(inf, text="🎁 Davet kodları")
        bar = ttk.Frame(inf); bar.pack(fill="x", pady=(0, 6))
        ttk.Button(bar, text="⛔ Kodu iptal et", command=self.revoke_invite).pack(side="right")
        self.tv_i = self.tree(inf, (("id", "#", 50, "e"), ("hint", "Kod", 70, "w"), ("left", "Kalan", 60, "center"), ("days", "Premium", 90, "w"),
                                    ("exp", "Geçerlilik", 110, "w"), ("note", "Not", 200, "w"), ("st", "Durum", 80, "w")))
        # denetim
        af = ttk.Frame(nb, padding=8); nb.add(af, text="📜 Denetim kaydı")
        self.tv_a = self.tree(af, (("t", "Zaman", 140, "w"), ("actor", "Kim", 110, "w"), ("action", "İşlem", 130, "w"), ("detail", "Ayrıntı", 360, "w")))
        self.nb = nb

    # ---- veri
    def refresh(self):
        if not self.need(): return
        self.msg("Lisans verileri yükleniyor…", self.C["info"])
        def work():
            out = {}
            for k, path in (("stats", "stats"), ("accounts", "accounts"), ("licenses", "licenses"), ("invites", "invites"), ("audit", "audit")):
                ok, d = self.api.call("GET", path)
                if not ok: return False, d
                out[k] = d
            return True, out
        self.bg(work, self._loaded)

    def _loaded(self, r):
        ok, d = r
        if not ok: return self.msg("Hesap sunucusu: " + str(d), self.C["bad"])
        for k, lbl in self.stat.items(): lbl.config(text=str(d["stats"].get(k, "–")))
        self._fill_accounts(d["accounts"]["accounts"]); self._fill_licenses(d["licenses"]["licenses"])
        self._fill_invites(d["invites"]["invites"]); self._fill_audit(d["audit"]["audit"])
        self.msg(f"Lisanslar güncel · {datetime.now():%H:%M:%S}", self.C["ok"])

    def _fill(self, tv, rows):
        tv.delete(*tv.get_children())
        for iid, vals, tag in rows: tv.insert("", "end", iid=str(iid), values=vals, tags=(tag,) if tag else ())

    def _fill_accounts(self, rows):
        self._fill(self.tv_u, [(a["id"], (a["id"], a["username"], a["discord_id"], a["active"], fmt_t(a["created"]), fmt_t(a["last_login"]),
                                          "engelli" if a["banned"] else "etkin"), "bad" if a["banned"] else ("ok" if a["active"] else ""))
                               for a in rows])

    def _fill_licenses(self, rows):
        import time
        now = time.time()
        def state(l):
            if l["revoked"]: return "iptal", "bad"
            if not l.get("username"): return "kullanılmadı", ""
            if l["expires"] and l["expires"] < now: return "süresi doldu", "off"
            return "etkin", "ok"
        self._fill(self.tv_l, [(l["id"], (l["id"], "…" + l["key_hint"], SRC_TR.get(l["source"], l["source"]), l.get("username") or "—",
                                          fmt_d(l["expires"]) if l.get("username") else (f"{l['duration_days']} gün" if l.get("duration_days") else "süresiz"),
                                          f"{l['devices']}/{l['max_devices']}", l.get("note") or "", state(l)[0]), state(l)[1]) for l in rows])

    def _fill_invites(self, rows):
        self._fill(self.tv_i, [(i["id"], (i["id"], "…" + i["code_hint"], i["uses_left"], f"{i['duration_days']} gün" if i["duration_days"] else "süresiz",
                                          fmt_d(i["expires"]) if i["expires"] else "süresiz", i.get("note") or "",
                                          "iptal" if i["revoked"] else ("bitti" if i["uses_left"] <= 0 else "etkin")),
                                "bad" if i["revoked"] else ("off" if i["uses_left"] <= 0 else "ok")) for i in rows])

    def _fill_audit(self, rows):
        self._fill(self.tv_a, [(n, (fmt_t(a["t"]), a["actor"], a["action"], a["detail"]), "") for n, a in enumerate(rows)])

    def load_accounts(self):
        if not self.need(): return
        self.bg(lambda: self.api.call("GET", "accounts", q=self.u_q.get().strip() or None),
                lambda r: self._fill_accounts(r[1]["accounts"]) if r[0] else self.msg(str(r[1]), self.C["bad"]))

    def load_licenses(self):
        if not self.need(): return
        self.bg(lambda: self.api.call("GET", "licenses", q=self.l_q.get().strip() or None),
                lambda r: self._fill_licenses(r[1]["licenses"]) if r[0] else self.msg(str(r[1]), self.C["bad"]))

    # ---- işlemler
    def _sel(self, tv, what):
        s = tv.selection()
        if not s: messagebox.showinfo("Panel", f"Önce bir {what} seç."); return None
        return s[0], tv.item(s[0], "values")

    def _done(self, r, ok_text):
        if r[0]: self.msg(ok_text, self.C["ok"]); self.refresh()
        else: self.msg("Hata: " + str(r[1]), self.C["bad"])

    def toggle_ban(self):
        s = self._sel(self.tv_u, "kullanıcı")
        if not s: return
        iid, v = s; ban = v[6] != "engelli"
        if ban and not messagebox.askyesno("Panel", f"{v[1]} engellensin mi? Tüm oturumları kapanır."): return
        self.bg(lambda: self.api.call("POST", f"accounts/{iid}/ban", {"banned": ban}),
                lambda r: self._done(r, f"{v[1]} {'engellendi' if ban else 'engeli kaldırıldı'}"))

    def lic_action(self, act):
        s = self._sel(self.tv_l, "lisans")
        if not s: return
        iid, v = s
        if act == "revoke" and v[7] == "iptal": act = "unrevoke"
        if act == "revoke" and not messagebox.askyesno("Panel", f"Lisans …{v[1][-4:]} iptal edilsin mi?"): return
        body = {"days": 30} if act == "extend" else {}
        names = {"revoke": "iptal edildi", "unrevoke": "geri alındı", "reset_devices": "cihazı sıfırlandı", "extend": "30 gün uzatıldı"}
        self.bg(lambda: self.api.call("POST", f"licenses/{iid}/{act}", body), lambda r: self._done(r, f"Lisans #{iid} {names[act]}"))

    def revoke_invite(self):
        s = self._sel(self.tv_i, "davet kodu")
        if not s or not messagebox.askyesno("Panel", f"Davet kodu …{s[1][1][-4:]} iptal edilsin mi?"): return
        self.bg(lambda: self.api.call("POST", f"invites/{s[0]}/revoke", {}), lambda r: self._done(r, "Davet kodu iptal edildi"))

    def _int(self, var, lo, hi, empty=None):
        t = var.get().strip()
        if not t: return empty
        try: return max(lo, min(hi, int(t)))
        except ValueError: return empty

    def create_keys(self):
        if not self.need(): return
        n, days = self._int(self.k_n, 1, 100, 1), self._int(self.k_days, 1, 3650)
        if not messagebox.askyesno("Panel", f"{n} anahtar üretilsin mi? ({'süresiz' if not days else str(days) + ' gün'})"): return
        def done(r):
            if not r[0]: return self.msg("Hata: " + str(r[1]), self.C["bad"])
            self.out.delete("1.0", "end"); self.out.insert("end", "\n".join(r[1]["keys"]))
            self.msg(f"{len(r[1]['keys'])} anahtar üretildi — şimdi kopyala, bir daha gösterilmez.", self.C["ok"]); self.refresh()
        self.bg(lambda: self.api.call("POST", "licenses", {"count": n, "days": days, "note": self.k_note.get().strip()}), done)

    def create_invite(self):
        if not self.need(): return
        body = {"uses": self._int(self.i_uses, 1, 10000, 1), "days": self._int(self.i_days, 1, 3650),
                "valid_days": self._int(self.i_valid, 1, 365), "note": self.i_note.get().strip()}
        def done(r):
            if not r[0]: return self.msg("Hata: " + str(r[1]), self.C["bad"])
            self.out.delete("1.0", "end"); self.out.insert("end", r[1]["code"])
            self.msg("Davet kodu oluşturuldu — şimdi kopyala.", self.C["ok"]); self.refresh()
        self.bg(lambda: self.api.call("POST", "invites", body), done)

    def copy_out(self):
        t = self.out.get("1.0", "end").strip()
        if t:
            self.f.clipboard_clear(); self.f.clipboard_append(t); self.msg("Panoya kopyalandı.", self.C["ok"])

