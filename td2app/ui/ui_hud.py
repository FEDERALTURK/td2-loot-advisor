"""Hafif çalışan canlı ana-panel sahnesi.

Yalnızca Canvas ve Pillow kullanır. Görsel katman 12 FPS ile sınırlıdır;
oyun ön plandayken bile OCR ve çeviri kuyruğunu etkilememesi amaçlanır.
"""
from __future__ import annotations

import math
import time
from pathlib import Path
import tkinter as tk

from PIL import Image, ImageOps, ImageTk


def _rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _blend(a: str, b: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    aa, bb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * amount) for x, y in zip(aa, bb))


class DashboardScene(tk.Canvas):
    """ISAC / Rogue görünümünde, gerçek dashboard verisini özetleyen sahne."""

    def __init__(self, parent, pal, art_dir: Path, mode="isac", on_scan=None, on_translate=None):
        # Ana sahne referans ekranlardaki gibi panelin gerçek odağı olmalı;
        # 290 px'lik bant, sinematik arka planı gereğinden fazla kırpıyordu.
        super().__init__(parent, height=370, highlightthickness=0, bd=0, bg=pal["bg"])
        self.pal, self.art_dir, self.mode = pal, Path(art_dir), mode
        self.on_scan, self.on_translate = on_scan, on_translate
        self._image, self._photo, self._size, self._job = None, None, (0, 0), None
        self._bg_item = None
        self._started = time.perf_counter()
        self.snapshot = {"name": "EŞYA TARAMASI BEKLİYOR", "verdict": "READY", "score": "—", "status": "SİSTEM HAZIR", "translation": "Canlı çeviri beklemede"}
        self.configure(cursor="hand2")
        self.bind("<Configure>", self._resize, add="+")
        self.bind("<Button-1>", self._click, add="+")
        self.after(120, self._tick)

    def destroy(self):
        if self._job:
            try: self.after_cancel(self._job)
            except tk.TclError: pass
        super().destroy()

    def set_snapshot(self, *, name=None, verdict=None, score=None, status=None, translation=None):
        for key, value in {"name": name, "verdict": verdict, "score": score, "status": status, "translation": translation}.items():
            if value is not None:
                self.snapshot[key] = str(value)
        self._draw()

    def _scene_path(self):
        name = "darkzone_rogue_scene.png" if self.mode == "rogue" else "isac_operations_scene.png"
        path = self.art_dir / "backgrounds" / name
        return path if path.exists() else None

    def _resize(self, _event=None):
        self._size = (0, 0)
        self.delete("scene-bg")
        self._bg_item = None
        self._draw()

    def _background(self, width, height):
        key = (width, height, self.mode)
        if self._size == key and self._photo is not None:
            return
        self._size = key
        path = self._scene_path()
        try:
            base = Image.open(path).convert("RGB") if path else Image.new("RGB", (width, height), _rgb(self.pal["bg"]))
            base = ImageOps.fit(base, (width, height), Image.Resampling.LANCZOS, centering=(0.52, 0.45))
            veil = Image.new("RGB", base.size, _rgb(self.pal["bg"]))
            # Sahne artık dekor değil: şehir, harita, görev ve risk öğeleri
            # okunur kalırken üstteki veri kartları yeterli kontrastı korur.
            base = Image.blend(base, veil, 0.25)
            self._photo = ImageTk.PhotoImage(base)
        except Exception:
            self._photo = None

    def _box(self, x1, y1, x2, y2, title, value, accent=None):
        accent = accent or self.pal["accent"]
        self.create_rectangle(x1, y1, x2, y2, fill=_blend(self.pal["bg"], self.pal["surface"], 0.78), outline=_blend(accent, self.pal["border"], 0.45), width=1, tags="hud")
        self.create_rectangle(x1, y1, x1 + 3, y2, fill=accent, outline="", tags="hud")
        self.create_text(x1 + 12, y1 + 13, anchor="w", text=title, fill=self.pal["muted"], font=("Segoe UI Semibold", 8), tags="hud")
        self.create_text(x1 + 12, y1 + 33, anchor="w", text=value[:48], fill=self.pal["fg"], font=("Segoe UI Semibold", 11), tags="hud")

    def _draw(self):
        try:
            width, height = self.winfo_width(), self.winfo_height()
        except tk.TclError:
            return
        if width < 80 or height < 80:
            return
        self._background(width, height)
        # Dinamik öğeleri yenile; ağır sinematik bitmapi her karede silip
        # yeniden yaratmak yerine tek Canvas öğesi olarak tut.
        self.delete("hud")
        if self._photo:
            if self._bg_item is None:
                self._bg_item = self.create_image(0, 0, image=self._photo, anchor="nw", tags="scene-bg")
            else:
                self.itemconfigure(self._bg_item, image=self._photo)
            self.tag_lower(self._bg_item)
        else:
            if self._bg_item is None:
                self._bg_item = self.create_rectangle(0, 0, width, height, fill=self.pal["bg"], outline="", tags="scene-bg")
            self.tag_lower(self._bg_item)

        now = time.perf_counter() - self._started
        cx, cy, radius = width * 0.56, height * 0.50, min(width, height) * 0.39
        accent = self.pal["accent"]
        # Arka plan radarı: değişen tema için aynı maliyet, farklı hareket dili.
        for frac, width_px in ((1.0, 1), (0.78, 2), (0.57, 1)):
            r = radius * frac
            self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=_blend(self.pal["bg"], accent, 0.27), width=width_px, tags="hud")
        for i in range(12):
            angle = math.radians(i * 30)
            self.create_line(cx + math.cos(angle) * radius * 0.42, cy + math.sin(angle) * radius * 0.42,
                             cx + math.cos(angle) * radius, cy + math.sin(angle) * radius,
                             fill=_blend(self.pal["bg"], accent, 0.13), width=1, tags="hud")
        if self.mode == "rogue":
            scan = (now * 28) % 360
            for i in range(7):
                start = scan + i * 51
                self.create_arc(cx - radius * .92, cy - radius * .92, cx + radius * .92, cy + radius * .92,
                                start=start, extent=15, style="arc", outline=_blend(self.pal["bg"], accent, 0.50), width=4, tags="hud")
            event_text = "ROGUE SİNYALİ // KARARSIZ"
        else:
            angle = math.radians((now * 23) % 360)
            self.create_line(cx, cy, cx + math.cos(angle) * radius, cy + math.sin(angle) * radius,
                             fill=_blend(self.pal["bg"], accent, 0.74), width=2, tags="hud")
            for i in range(5):
                a = math.radians(now * 17 + i * 71)
                x, y = cx + math.cos(a) * radius * (0.42 + (i % 3) * .18), cy + math.sin(a) * radius * (0.42 + (i % 3) * .18)
                self.create_oval(x - 4, y - 4, x + 4, y + 4, fill=accent, outline="", tags="hud")
            event_text = "ISAC // CANLI TARAMA"
        pulse = (math.sin(now * 2.0) + 1) / 2
        self.create_oval(cx - radius * (.28 + pulse * .08), cy - radius * (.28 + pulse * .08),
                         cx + radius * (.28 + pulse * .08), cy + radius * (.28 + pulse * .08),
                         outline=_blend(self.pal["bg"], accent, 0.16 + pulse * .22), width=2, tags="hud")
        self.create_text(cx, cy + radius * .55, text=event_text, fill=_blend(self.pal["bg"], accent, .78),
                         font=("Segoe UI Semibold", 9), tags="hud")

        pad, card_w = 16, min(325, int(width * .27))
        theme_name = "DARK ZONE // ROGUE EVENT" if self.mode == "rogue" else "ISAC // OPERATIONS"
        self.create_text(pad, 18, anchor="w", text=theme_name, fill=accent, font=("Segoe UI Semibold", 14), tags="hud")
        self.create_text(pad, 39, anchor="w", text=self.snapshot["status"][:72], fill=self.pal["muted"], font=("Segoe UI", 9), tags="hud")
        self._box(pad, 58, pad + card_w, 118, "SON TARAMA", self.snapshot["name"], accent)
        self._box(pad, 126, pad + card_w, 186, "KARAR / BUILD UYUMU", f"{self.snapshot['verdict']}  ·  {self.snapshot['score']}", accent)
        self._box(pad, 194, pad + card_w, 260, "HIZLI İŞLEM", "TARAMAK İÇİN TIKLA", accent)
        self._box(pad, 268, pad + card_w, 342, "LOOT ÖNCELİĞİ", "YÜKSEK DEĞERLİ ÖĞELERİ İZLE", accent)
        right = width - pad
        r_w = min(310, int(width * .25))
        self._box(right - r_w, 58, right, 131, "CANLI ÇEVİRİ", self.snapshot["translation"], accent)
        self._box(right - r_w, 139, right, 205, "GÖREV İSTİHBARATI", "Günlük · Haftalık · Sezon", accent)
        self._box(right - r_w, 213, right, 270, "ETKİNLİK DURUMU", "AKTİF // takip ediliyor", accent)
        self._box(right - r_w, 278, right, 342, "ISAC SİNYALİ", "ONLINE  ·  VERİ AKIŞI KARARLI", accent)

    def _click(self, event):
        # Alt soldaki hızlı işlem kartı taramayı, sağ üst kart çeviri sayfasını açar.
        if event.x < self.winfo_width() * .30 and 185 < event.y < 265:
            if self.on_scan: self.on_scan()
        elif event.x > self.winfo_width() * .70 and event.y < 145:
            if self.on_translate: self.on_translate()

    def _tick(self):
        try:
            root = self.winfo_toplevel()
            # Notebook'te görünmeyen panelin animasyonu UI thread'ini gereksiz
            # yere meşgul etmesin. Bu kontrol menü geçişlerindeki takılmayı da
            # azaltır.
            visible = bool(self.winfo_ismapped() and self.winfo_viewable())
            if visible and not getattr(root, "_td2_suspend_animations", False):
                self._draw()
            speed = max(0.1, min(1.0, float(getattr(root, "_td2_animation_multiplier", 1.0))))
            if not visible:
                delay = 700
            else:
                delay = int((125 if root.focus_displayof() else 300) / speed)
            self._job = self.after(delay, self._tick)
        except tk.TclError:
            self._job = None
