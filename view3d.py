"""Küçük 3D motor (Tk Canvas üzerinde, ek kütüphane yok).

- AgentView: döndürülebilir 3D ajan modeli. Her ekipman yuvası (maske, göğüs, sırt çantası, eldiven,
  kılıf, dizlik, ana silah, tabanca) ayrı parça; dolu yuva yeşil, eksik yuva kırmızı (nabız gibi yanıp söner),
  build'de kullanılmayan gri. Fareyle sürükle → döndür, tıkla → o yuvayı seç.
- Bars3D: build × yuva puanlarını 3D çubuklarla gösterir (yükseklik = puan), fareyle döndürülür.
Çizim: dönüş + perspektif izdüşüm, arka yüz ayıklama, ressam algoritması (derinliğe göre sıralama), düz gölgeleme.
"""
import math
import tkinter as tk


def _hex(c):
    c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _shade(color, k):
    r, g, b = _hex(color)
    k = max(0.15, min(1.25, k))
    return "#%02x%02x%02x" % tuple(min(255, int(v * k)) for v in (r, g, b))


def box(cx, cy, cz, sx, sy, sz, color, tag=None):
    """Merkez + boyutlardan kutu: 6 yüz (dört köşe), renk, etiket."""
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    quads = [(0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)]
    return [([P[i] for i in q], color, tag) for q in quads]


class Scene3D(tk.Canvas):
    def __init__(self, parent, bg="#101217", width=420, height=480, **kw):
        super().__init__(parent, bg=bg, width=width, height=height, highlightthickness=0, **kw)
        self.faces, self.yaw, self.pitch, self.zoom = [], 0.6, -0.25, 1.0
        self.light = (0.4, -0.7, -0.6)
        self._drag, self._ids, self.labels = None, {}, []
        self.bind("<ButtonPress-1>", self._press); self.bind("<B1-Motion>", self._move)
        self.bind("<ButtonRelease-1>", self._release); self.bind("<Configure>", lambda e: self.render())
        self.bind("<MouseWheel>", self._wheel)
        self.on_pick = None
        self.auto_spin = True
        self._alive = True
        self.bind("<Destroy>", lambda e: setattr(self, "_alive", False))

    # --- etkileşim
    def _press(self, e): self._drag = (e.x, e.y, False)

    def _move(self, e):
        if not self._drag: return
        x, y, _ = self._drag
        self.yaw += (e.x - x) * 0.01; self.pitch = max(-1.2, min(1.2, self.pitch + (e.y - y) * 0.01))
        self._drag = (e.x, e.y, True); self.render()

    def _release(self, e):
        if self._drag and not self._drag[2] and self.on_pick:
            hit = self.find_overlapping(e.x, e.y, e.x, e.y)
            for i in reversed(hit):
                if self._ids.get(i):
                    self.on_pick(self._ids[i]); break
        self._drag = None

    def _wheel(self, e):
        self.zoom = max(0.5, min(2.5, self.zoom * (1.1 if e.delta > 0 else 0.9))); self.render()

    def spin(self, step=0.012, every=40):
        """Boşta yavaşça döndür (sürüklerken durur)."""
        if not self._alive: return
        if self.auto_spin and not self._drag and self.winfo_ismapped():
            self.yaw += step; self.render()
        self.after(every, lambda: self.spin(step, every))

    # --- çizim
    center_y = 0.0

    def project(self, p, w, h, f):
        x, y, z = p
        y -= self.center_y
        cy, sy, cp, sp = math.cos(self.yaw), math.sin(self.yaw), math.cos(self.pitch), math.sin(self.pitch)
        x, z = x * cy - z * sy, x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        z += 6.0
        k = f / max(0.5, z)
        return w / 2 + x * k, h * 0.5 - y * k, z, (x, y, z)

    def color_of(self, color, tag):
        return color

    bg_top, bg_bottom = None, None          # dikey gradyan (ör. "#1b1f27", "#0d0f13")
    anchors = ()                            # [(etiket, (x, y, z), yazı)] → 3D noktaya bağlı etiket

    def _gradient(self, w, h):
        if not self.bg_top: return
        a, b = _hex(self.bg_top), _hex(self.bg_bottom or self.bg_top)
        steps = 28
        for i in range(steps):
            k = i / (steps - 1)
            c = "#%02x%02x%02x" % tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3))
            self.create_rectangle(0, h * i / steps, w, h * (i + 1) / steps + 1, fill=c, outline="")

    def label_color(self, tag):
        return "#cfd5df"

    def draw_under(self, w, h, f):
        pass

    def render(self):
        if not self._alive: return
        self.delete("all"); self._ids = {}
        w, h = max(50, self.winfo_width()), max(50, self.winfo_height())
        self._gradient(w, h)
        f = min(w, h) * 1.15 * self.zoom
        self.draw_under(w, h, f)
        lx, ly, lz = self.light; ln = math.sqrt(lx * lx + ly * ly + lz * lz); lx, ly, lz = lx / ln, ly / ln, lz / ln
        polys = []
        for pts, color, tag in self.faces:
            pr = [self.project(p, w, h, f) for p in pts]
            a, b, c = pr[0][3], pr[1][3], pr[2][3]
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            nn = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
            nx, ny, nz = nx / nn, ny / nn, nz / nn
            light = 0.5 + 0.65 * abs(nx * lx + ny * ly + nz * lz)     # yüz yönünden bağımsız düz gölgeleme
            depth = sum(p[2] for p in pr) / len(pr)
            polys.append((depth, [(p[0], p[1]) for p in pr], _shade(self.color_of(color, tag), light), tag))
        for depth, pts, col, tag in sorted(polys, key=lambda t: -t[0]):
            i = self.create_polygon(*[c for p in pts for c in p], fill=col, outline=_shade(col, 0.6), width=1)
            if tag: self._ids[i] = tag
        for txt, x, y, col in self.labels:
            self.create_text(x, y, text=txt, fill=col, font=("Segoe UI", 9), anchor="nw")
        for tag, p3, txt in self.anchors:               # yuva etiketleri: parçadan dışarı çizgi + yazı
            x, y, z, _ = self.project(p3, w, h, f)
            side = 1 if x >= w / 2 else -1
            lx = x + side * 34; ly = y - 10
            col = self.label_color(tag)
            self.create_line(x, y, lx, ly, lx + side * 8, ly, fill=col, width=1)
            self.create_oval(x - 2.5, y - 2.5, x + 2.5, y + 2.5, fill=col, outline="")
            i = self.create_text(lx + side * 11, ly, text=txt, fill=col, font=("Segoe UI Semibold", 9),
                                 anchor="w" if side > 0 else "e")
            self._ids[i] = tag


SLOT_POS = {}


class AgentView(Scene3D):
    """3D ajan modeli; yuva durumları: {"Mask": "ok"|"miss"|"off", …}."""
    COLORS = {"ok": "#22c55e", "miss": "#ef4444", "off": "#4b5263", "sel": "#ff6d10"}
    LABELS = {}                              # {"Mask": "Maske", …} — arayüz dilinde yuva adları (dışarıdan verilir)

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.status, self.selected, self._pulse = {}, None, 0.0
        self.center_y, self.zoom = 1.05, 1.55
        self.bg_top, self.bg_bottom = "#1d2230", "#0b0d12"
        cloth, cloth2, skin, boot, metal = "#2c3340", "#232934", "#6b5446", "#16191f", "#3b414d"
        F = []
        # baş + kask
        F += box(0, 2.18, 0, 0.42, 0.48, 0.42, skin)
        F += box(0, 2.45, 0.02, 0.5, 0.14, 0.5, cloth2)                      # bere / kep
        F += box(0, 1.92, 0, 0.2, 0.12, 0.2, skin)                           # boyun
        F += box(0, 2.1, -0.24, 0.46, 0.26, 0.1, "#555", "Mask")              # maske
        # gövde
        F += box(0, 1.45, 0, 0.82, 0.8, 0.42, cloth)                         # gövde üst
        F += box(0, 0.98, 0, 0.7, 0.2, 0.38, cloth2)                         # bel / kemer
        F += box(0, 1.5, -0.25, 0.86, 0.66, 0.1, "#555", "Chest")             # yelek ön plaka
        F += box(0, 1.5, 0.25, 0.86, 0.66, 0.08, "#555", "Chest")             # yelek arka
        F += box(0, 1.5, 0.48, 0.66, 0.78, 0.34, "#555", "Backpack")          # sırt çantası
        F += box(0, 1.98, 0.5, 0.5, 0.16, 0.26, "#555", "Backpack")           # çanta üst rulo
        for sx in (-1, 1):
            F += box(0.55 * sx, 1.74, 0, 0.32, 0.18, 0.4, cloth2)            # omuz
            F += box(0.6 * sx, 1.45, 0, 0.22, 0.48, 0.24, cloth)             # üst kol
            F += box(0.62 * sx, 1.05, -0.04, 0.2, 0.4, 0.22, cloth2)         # ön kol
            F += box(0.63 * sx, 0.78, -0.06, 0.24, 0.2, 0.26, "#555", "Gloves")
            F += box(0.22 * sx, 0.62, 0, 0.3, 0.52, 0.32, cloth)             # uyluk
            F += box(0.22 * sx, 0.12, 0, 0.27, 0.48, 0.28, cloth2)           # baldır
            F += box(0.22 * sx, 0.36, -0.18, 0.28, 0.2, 0.08, "#555", "Kneepads")
            F += box(0.22 * sx, -0.18, -0.04, 0.3, 0.14, 0.4, boot)          # bot
        F += box(0.43, 0.62, -0.02, 0.12, 0.34, 0.24, "#555", "Holster")      # kılıf (sağ uyluk)
        F += box(0.46, 0.78, -0.02, 0.1, 0.16, 0.12, metal)                  # tabanca kabzası kılıfta
        F += box(-0.43, 0.98, 0.0, 0.08, 0.22, 0.14, "#555", "Sidearm")       # tabanca (sol bel)
        # ana silah: gövde, namlu, şarjör, dipçik, nişangah
        F += box(-0.15, 1.28, -0.5, 1.0, 0.14, 0.12, "#555", "Weapon")
        F += box(-0.82, 1.3, -0.5, 0.4, 0.05, 0.05, "#555", "Weapon")
        F += box(-0.05, 1.12, -0.5, 0.1, 0.2, 0.08, "#555", "Weapon")
        F += box(0.45, 1.3, -0.5, 0.26, 0.12, 0.1, "#555", "Weapon")
        F += box(-0.15, 1.39, -0.5, 0.18, 0.07, 0.07, "#555", "Weapon")
        # zemin: koyu disk + turuncu halka
        F += box(0, -0.29, 0, 1.25, 0.04, 1.25, "#12151b")
        self.faces = F
        self.anchors = [("Mask", (0, 2.1, -0.3), "Mask"), ("Chest", (0.3, 1.6, -0.31), "Chest"),
                        ("Backpack", (-0.3, 1.7, 0.66), "Backpack"), ("Gloves", (0.63, 0.78, -0.2), "Gloves"),
                        ("Holster", (0.5, 0.6, -0.15), "Holster"), ("Kneepads", (-0.22, 0.36, -0.23), "Kneepads"),
                        ("Weapon", (-0.9, 1.3, -0.52), "Weapon"), ("Sidearm", (-0.48, 0.98, 0.0), "Sidearm")]

    def set_labels(self, names):
        self.anchors = [(tag, p, names.get(tag, txt)) for tag, p, txt in self.anchors]

    def set_status(self, status, selected=None):
        self.status, self.selected = dict(status), selected
        self.render()

    def label_color(self, tag):
        if tag == self.selected: return self.COLORS["sel"]
        st = self.status.get(tag, "off")
        return {"ok": "#4ade80", "miss": "#f87171", "off": "#8d95a5"}.get(st, "#cfd5df")

    def draw_under(self, w, h, f):
        pts = []
        for a in range(0, 361, 10):                                       # zemin halkası (turuncu, hafif nabız)
            r = 0.8 + 0.03 * math.sin(self._pulse * 0.4)
            x, y, z, _ = self.project((r * math.cos(math.radians(a)), -0.27, r * math.sin(math.radians(a))), w, h, f)
            pts += [x, y]
        self.create_line(*pts, fill="#ff6d10", width=2, smooth=True)

    def color_of(self, color, tag):
        if not tag: return color
        if tag == self.selected: return self.COLORS["sel"]
        st = self.status.get(tag, "off")
        c = self.COLORS.get(st, color)
        if st == "miss":                                                   # eksik parça nabız gibi
            k = 0.75 + 0.35 * (0.5 + 0.5 * math.sin(self._pulse))
            return _shade(c, k)
        return c

    def spin(self, step=0.012, every=40):
        self._pulse += 0.25
        super().spin(step, every)


class Bars3D(Scene3D):
    """Satır = build, sütun = yuva; yükseklik = puan (0-100)."""

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.yaw, self.pitch = 0.75, -0.55
        self.auto_spin = False
        self.bg_top, self.bg_bottom = "#1d2230", "#0b0d12"
        self.center_y = 0.3
        self.zoom = 1.2

    def set_data(self, rows, cols, values):
        """values[r][c] = 0..100 ya da None."""
        F, labels = [], []
        nr, nc = max(1, len(rows)), max(1, len(cols))
        s = 3.2 / max(nr, nc)
        for r in range(nr):
            for c in range(nc):
                v = values[r][c] if r < len(values) and c < len(values[r]) else None
                x, z = (c - (nc - 1) / 2) * s, (r - (nr - 1) / 2) * s
                if v is None:
                    F += box(x, -0.02, z, s * 0.7, 0.04, s * 0.7, "#2a2f3a")
                    continue
                hgt = max(0.04, v / 100 * 1.5)
                col = "#22c55e" if v >= 70 else "#eab308" if v >= 40 else "#ef4444"
                F += box(x, hgt / 2 - 0.4, z, s * 0.7, hgt, s * 0.7, col, f"{rows[r]} · {cols[c]}: {v}%")
        F += box(0, -0.45, 0, nc * s + 0.2, 0.05, nr * s + 0.2, "#15181f")
        self.faces = F
        self.labels = [(f"↕ {r}", 8, 8 + 16 * i, "#9aa1ae") for i, r in enumerate(rows[:12])]
        self.render()
