"""Hafif çalışan canlı ana-panel sahnesi.

Fotoğraf arka planı yerine prosedürel bir Kaivolt zemini çizer: dikey gradyan,
ince eğik ızgara, kenar vinyeti ve yavaş akan tarama bandı. Yalnızca Canvas ve
Pillow kullanır; görsel katman 12 FPS ile sınırlıdır, böylece oyun ön plandayken
OCR ve çeviri kuyruğunu etkilemez.
"""
from __future__ import annotations

import math
import random
import time
from pathlib import Path
import tkinter as tk
from . import ui_theme

from PIL import Image, ImageDraw, ImageFilter, ImageTk


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
        # Rastgele "tespit" noktaları: her biri kendi açısı/yarıçapı/ömrüyle doğar ve söner;
        # sabit bir örüntü yok — aynı noktada tekrar eden bir "tarama" hissi kasıtlı olarak önlenir.
        self._blips = []
        self._next_blip_at = 0.0
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

    def _resize(self, _event=None):
        self._size = (0, 0)
        self.delete("scene-bg")
        self._bg_item = None
        self._draw()

    def _backdrop(self, width, height):
        """Prosedürel zemin: dikey gradyan + ince eğik ızgara + kenar vinyeti.

        Önceden `art/backgrounds/isac_operations_scene.png` fotoğrafı
        kullanılıyordu; fotoğraf kaldırıldı. Zemin tamamen palet renklerinden
        üretildiği için tema değişiminde de tutarlı kalır ve diskten büyük
        görsel okumaz.
        """
        bg, surface = _rgb(self.pal["bg"]), _rgb(self.pal["surface"])
        target = tuple(int(bg[i] + (surface[i] - bg[i]) * 0.62) for i in range(3))
        grad = Image.new("RGB", (1, height))
        for y in range(height):
            t = y / max(1, height - 1)
            grad.putpixel((0, y), tuple(int(bg[i] + (target[i] - bg[i]) * t) for i in range(3)))
        base = grad.resize((width, height))

        accent = _rgb(self.pal["accent"])
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        step = 44
        for x in range(-height, width + height, step):
            draw.line([(x, 0), (x - height, height)], fill=(*accent, 16), width=1)
        for y in range(0, height, step):
            draw.line([(0, y), (width, y)], fill=(*accent, 10), width=1)
        # İnce yatay tarama dokusu (fotoğrafın yerini alan HUD hissi).
        for y in range(0, height, 3):
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, 8), width=1)
        # Radar merkezinin arkasında yumuşak vurgu ışıması.
        glow = Image.new("L", (width, height), 0)
        gcx, gcy = width * 0.56, height * 0.50
        gr = max(80, min(width, height) * 0.52)
        ImageDraw.Draw(glow).ellipse([gcx - gr, gcy - gr * 0.55, gcx + gr, gcy + gr * 0.55], fill=44)
        glow = glow.filter(ImageFilter.GaussianBlur(max(18, min(width, height) * 0.16)))
        glow_layer = Image.new("RGBA", (width, height), (*accent, 0))
        glow_layer.putalpha(glow)
        overlay = Image.alpha_composite(overlay, glow_layer)
        draw = ImageDraw.Draw(overlay)
        edge = int(min(width, height) * 0.22)
        for i in range(edge):
            alpha = int(70 * (1 - i / max(1, edge)))
            draw.line([(i, 0), (i, height)], fill=(0, 0, 0, alpha), width=1)
            draw.line([(width - 1 - i, 0), (width - 1 - i, height)], fill=(0, 0, 0, alpha), width=1)
        return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")

    def _background(self, width, height):
        key = (width, height, self.mode)
        if self._size == key and self._photo is not None:
            return
        self._size = key
        try:
            self._photo = ImageTk.PhotoImage(self._backdrop(width, height))
        except Exception:
            self._photo = None

    def _box(self, x1, y1, x2, y2, title, value, accent=None):
        accent = accent or self.pal["accent"]
        text = str(value)
        # Uzun değerler karttan taşmasın: HUD yazısı kademeli küçülür ve
        # gerekiyorsa üç nokta ile kırpılır.
        size = 12 if len(text) <= 20 else (11 if len(text) <= 26 else (10 if len(text) <= 40 else 9))
        avail = max(40, x2 - x1 - 24)
        max_chars = max(8, int(avail / (size * 0.66)))
        if len(text) > max_chars:
            text = text[:max_chars - 1].rstrip() + "…"
        self.create_rectangle(x1, y1, x2, y2, fill=_blend(self.pal["bg"], self.pal["surface"], 0.78),
                              outline=_blend(self.pal.get("line", self.pal["border"]), accent, 0.35),
                              width=1, tags="hud")
        self.create_rectangle(x1, y1, x1 + 3, y2, fill=accent, outline="", tags="hud")
        self.create_text(x1 + 12, y1 + 14, anchor="w", text=title, fill=self.pal["muted"],
                         font=ui_theme.font_spec("mono", 9), tags="hud")
        self.create_text(x1 + 12, y1 + 36, anchor="w", text=text, fill=self.pal["fg"],
                         font=ui_theme.font_spec("display", size, weight="bold"), tags="hud")

    def _draw_blips(self, cx, cy, radius, ry, accent, sweep_deg):
        """Rastgele 'tespit' noktaları: açı/yarıçap her defasında yeniden seçilir,
        her biri kısa bir süre parlayıp söner. Asla sabit bir örüntü/konum tekrarlamaz —
        bu dekoratif bir efekttir, oyunun belleğinden okunan gerçek bir düşman konumu değildir."""
        now = time.time()
        if now >= self._next_blip_at and len(self._blips) < 3:
            # Yeni nokta, tarama çizgisinin az gerisinde "yeni tespit edilmiş" hissiyle doğar;
            # açı ve yarıçap her seferinde rastgele seçilir (aynı konumun tekrarını önler).
            spawn_angle = (sweep_deg + random.uniform(-70, 10)) % 360
            self._blips.append({
                "angle": spawn_angle,
                "rfrac": random.uniform(0.30, 0.94),
                "t0": now,
                "dur": random.uniform(1.6, 2.6),
            })
            self._next_blip_at = now + random.uniform(1.3, 3.4)
        kept = []
        for b in self._blips:
            age = now - b["t0"]
            if age >= b["dur"]:
                continue
            frac = age / b["dur"]
            # Hızlı parlama + yavaş sönme: tespit anı belirgin, sonrası dekoratif bir iz bırakır.
            glow = (1.0 - frac) ** 0.5 * (1.0 if frac > 0.1 else frac / 0.1)
            a = math.radians(b["angle"])
            r = radius * b["rfrac"]
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * ry
            rad = 3 + glow * 4
            self.create_oval(x - rad * 2.1, y - rad * 2.1, x + rad * 2.1, y + rad * 2.1,
                             outline=_blend(self.pal["bg"], accent, 0.18 + glow * 0.35), width=1, tags="hud")
            self.create_oval(x - rad, y - rad, x + rad, y + rad,
                             fill=_blend(self.pal["bg"], accent, 0.45 + glow * 0.55), outline="", tags="hud")
            kept.append(b)
        self._blips = kept

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
        self.delete("fx")
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

        # Fotoğrafın yerini alan hareketli katman: yavaş akan tarama bandı ve
        # kenar veri izleri. Hepsi birkaç çizgi; 12 FPS'te maliyeti düşük.
        band_y = (now * 46) % (height + 160) - 80
        for offset, alpha in ((0, 0.50), (7, 0.18), (-7, 0.18)):
            y = band_y + offset
            if -2 <= y <= height + 2:
                self.create_line(0, y, width, y, fill=_blend(self.pal["bg"], accent, alpha),
                                 width=1, tags="fx")
        for i in range(6):
            x = ((now * 34) + i * (width / 6)) % width
            self.create_line(x, 0, x + 16, 0, fill=_blend(self.pal["bg"], accent, 0.30),
                             width=2, tags="fx")
            self.create_line(x, height - 1, x + 16, height - 1,
                             fill=_blend(self.pal["bg"], accent, 0.22), width=2, tags="fx")
        # Köşe braketleri: sahneyi çerçeveleyen ince HUD işaretleri.
        m, arm = 10, 26
        for x0, y0, dx, dy in ((m, m, 1, 1), (width - m, m, -1, 1),
                               (m, height - m, 1, -1), (width - m, height - m, -1, -1)):
            self.create_line(x0, y0, x0 + dx * arm, y0,
                             fill=_blend(self.pal["bg"], accent, 0.40), width=2, tags="fx")
            self.create_line(x0, y0, x0, y0 + dy * arm,
                             fill=_blend(self.pal["bg"], accent, 0.40), width=2, tags="fx")
        # 3B eğimli radar tabanı: daire yerine basık elips ("squash") çizmek,
        # sahte bir zemin perspektifi verir — halkalar bir masa üstünde değil,
        # eğik bir tarama diski gibi görünür. ry: dikey basıklık oranı.
        ry = 0.50
        # Alt katman: hafif aşağı kaymış, daha donuk bir "derinlik" elipsi —
        # diskin kalınlığı/3B hacmi hissini ucuz şekilde verir.
        self.create_oval(cx - radius, cy - radius * ry + radius * 0.05, cx + radius, cy + radius * ry + radius * 0.05,
                         outline=_blend(self.pal["bg"], accent, 0.10), width=1, tags="hud")
        for frac, width_px in ((1.0, 1), (0.78, 2), (0.57, 1), (0.33, 1)):
            r = radius * frac
            self.create_oval(cx - r, cy - r * ry, cx + r, cy + r * ry,
                             outline=_blend(self.pal["bg"], accent, 0.27), width=width_px, tags="hud")
        for i in range(12):
            angle = math.radians(i * 30)
            x0, y0 = cx + math.cos(angle) * radius * 0.42, cy + math.sin(angle) * radius * 0.42 * ry
            x1, y1 = cx + math.cos(angle) * radius, cy + math.sin(angle) * radius * ry
            self.create_line(x0, y0, x1, y1, fill=_blend(self.pal["bg"], accent, 0.13), width=1, tags="hud")
        if self.mode == "rogue":
            scan = (now * 28) % 360
            for i in range(7):
                start = scan + i * 51
                self.create_arc(cx - radius * .92, cy - radius * .92 * ry, cx + radius * .92, cy + radius * .92 * ry,
                                start=start, extent=15, style="arc", outline=_blend(self.pal["bg"], accent, 0.50), width=4, tags="hud")
            event_text = "ROGUE SİNYALİ // KARARSIZ"
            sweep_deg = scan
        else:
            sweep_deg = (now * 23) % 360
            angle = math.radians(sweep_deg)
            self.create_line(cx, cy, cx + math.cos(angle) * radius, cy + math.sin(angle) * radius * ry,
                             fill=_blend(self.pal["bg"], accent, 0.74), width=2, tags="hud")
            # Dış halkada yavaş dönen kesik yaylar: tarama diskinin "çalışıyor" hissi.
            rot = (now * 12) % 360
            for start in (rot, rot + 120, rot + 240):
                self.create_arc(cx - radius * 1.03, cy - radius * 1.03 * ry,
                                cx + radius * 1.03, cy + radius * 1.03 * ry,
                                start=start, extent=24, style="arc",
                                outline=_blend(self.pal["bg"], accent, 0.35), width=2, tags="hud")
            event_text = "ISAC // CANLI TARAMA"
        pulse = (math.sin(now * 2.0) + 1) / 2
        self.create_oval(cx - radius * (.28 + pulse * .08), cy - radius * (.28 + pulse * .08) * ry,
                         cx + radius * (.28 + pulse * .08), cy + radius * (.28 + pulse * .08) * ry,
                         outline=_blend(self.pal["bg"], accent, 0.16 + pulse * .22), width=2, tags="hud")
        self._draw_blips(cx, cy, radius, ry, accent, sweep_deg)
        self.create_text(cx, cy + radius * ry + 18, text=event_text, fill=_blend(self.pal["bg"], accent, .78),
                         font=ui_theme.font_spec("mono", 10, weight="bold"), tags="hud")

        pad, card_w = 16, min(325, int(width * .27))
        theme_name = "DARK ZONE // ROGUE EVENT" if self.mode == "rogue" else "ISAC // OPERATIONS"
        self.create_text(pad, 18, anchor="w", text=theme_name, fill=accent,
                         font=ui_theme.font_spec("display", 16, weight="bold"), tags="hud")
        self.create_text(pad, 41, anchor="w", text=self.snapshot["status"][:72], fill=self.pal["muted"],
                         font=ui_theme.font_spec("body", 10), tags="hud")
        self._box(pad, 58, pad + card_w, 118, "SON TARAMA", self.snapshot["name"], accent)
        self._box(pad, 126, pad + card_w, 186, "KARAR / BUILD UYUMU", f"{self.snapshot['verdict']}  ·  {self.snapshot['score']}", accent)
        self._box(pad, 194, pad + card_w, 260, "HIZLI İŞLEM", "TARAMAK İÇİN TIKLA", accent)
        self._box(pad, 268, pad + card_w, 342, "LOOT ÖNCELİĞİ", "YÜKSEK DEĞERLİ ÖĞELERİ İZLE", accent)
        right = width - 26
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
