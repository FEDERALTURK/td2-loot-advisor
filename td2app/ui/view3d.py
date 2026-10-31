"""Küçük 3D motor (Tk Canvas üzerinde, ek kütüphane yok).

- AgentView: döndürülebilir 3D ajan modeli. Her ekipman yuvası (maske, göğüs, sırt çantası, eldiven,
  kılıf, dizlik, ana silah, tabanca) ayrı parça; dolu yuva yeşil, eksik yuva kırmızı (nabız gibi yanıp söner),
  build'de kullanılmayan gri. Fareyle sürükle → döndür, tıkla → o yuvayı seç.
- Bars3D: build × yuva puanlarını 3D çubuklarla gösterir (yükseklik = puan), fareyle döndürülür.
Çizim: dönüş + perspektif izdüşüm, arka yüz ayıklama, ressam algoritması (derinliğe göre sıralama), düz gölgeleme.
"""
import math
import time
import tkinter as tk


def _animation_budget(widget, delay_ms):
    try: root = widget._root()
    except (AttributeError, tk.TclError): root = widget
    paused = bool(getattr(root, "_td2_suspend_animations", False))
    try:
        speed = float(getattr(root, "_td2_animation_multiplier", 1.0))
        if not math.isfinite(speed): speed = 1.0
    except (TypeError, ValueError): speed = 1.0
    return paused, max(1, int(delay_ms / max(0.1, min(1.0, speed))))


def _hex(c):
    c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


_SHADE = {}


def _shade(color, k):
    k = round(max(0.15, min(1.25, k)), 2)
    key = (color, k)
    c = _SHADE.get(key)
    if c is None:
        r, g, b = _hex(color)
        c = _SHADE[key] = "#%02x%02x%02x" % tuple(min(255, int(v * k)) for v in (r, g, b))
        if len(_SHADE) > 20000: _SHADE.clear()
    return c


def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(u, v): return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _dot(u, v): return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _norm(u):
    n = math.sqrt(_dot(u, u)) or 1.0
    return (u[0] / n, u[1] / n, u[2] / n)


def _orient(polys, center, color, tag):
    """Her yüzün köşe sırasını dışa bakacak şekilde düzelt (arka yüz ayıklama için)."""
    out = []
    for pts in polys:
        if len(pts) < 3: continue
        n = _cross(_sub(pts[1], pts[0]), _sub(pts[2], pts[0]))
        if _dot(n, n) < 1e-14:                       # kutup üçgenlerinde ilk üç nokta çakışabilir
            n = _cross(_sub(pts[2], pts[0]), _sub(pts[-1], pts[0]))
            if _dot(n, n) < 1e-14: continue
            pts = [pts[0], pts[2], pts[-1]] + [q for q in pts if q not in (pts[0], pts[2], pts[-1])]
        fc = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
        if _dot(n, _sub(fc, center)) < 0: pts = pts[::-1]
        out.append((pts, color, tag))
    return out


def box(cx, cy, cz, sx, sy, sz, color, tag=None):
    """Merkez + boyutlardan kutu: 6 yüz (dört köşe), renk, etiket."""
    return taper(cx, cy, cz, sx, sz, sx, sz, sy, color, tag)


def taper(cx, cy, cz, bx, bz, tx, tz, sy, color, tag=None, top_shift=(0.0, 0.0)):
    """Alt yüzü bx×bz, üst yüzü tx×tz olan kesik piramit (gövde, bacak, çanta için)."""
    y0, y1 = cy - sy / 2, cy + sy / 2
    ox, oz = top_shift
    B = [(cx - bx / 2, y0, cz - bz / 2), (cx + bx / 2, y0, cz - bz / 2), (cx + bx / 2, y0, cz + bz / 2), (cx - bx / 2, y0, cz + bz / 2)]
    T = [(cx + ox - tx / 2, y1, cz + oz - tz / 2), (cx + ox + tx / 2, y1, cz + oz - tz / 2), (cx + ox + tx / 2, y1, cz + oz + tz / 2), (cx + ox - tx / 2, y1, cz + oz + tz / 2)]
    polys = [B, T] + [[B[i], B[(i + 1) % 4], T[(i + 1) % 4], T[i]] for i in range(4)]
    return _orient(polys, (cx + ox / 2, cy, cz + oz / 2), color, tag)


def cyl(p0, p1, r0, r1, color, tag=None, n=7, caps=True):
    """p0→p1 ekseni boyunca konik silindir (uzuv, namlu, rulo)."""
    ax = _norm(_sub(p1, p0))
    ref = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = _norm(_cross(ax, ref)); v = _cross(ax, u)
    A, B = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        A.append(tuple(p0[k] + r0 * (ca * u[k] + sa * v[k]) for k in range(3)))
        B.append(tuple(p1[k] + r1 * (ca * u[k] + sa * v[k]) for k in range(3)))
    polys = [[A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]] for i in range(n)]
    if caps: polys += [A, B]
    c = tuple((p0[k] + p1[k]) / 2 for k in range(3))
    return _orient(polys, c, color, tag)


def ell(cx, cy, cz, rx, ry, rz, color, tag=None, nu=8, nv=6, top=1.0):
    """Elipsoid (baş, eldiven, omuz). top<1 → yalnız üst kısmı (kask/kapüşon kubbesi), altı düz kapak."""
    vmax = math.pi * top
    rings = []
    for j in range(nv + 1):
        v = vmax * j / nv
        rings.append([(cx + rx * math.sin(v) * math.cos(2 * math.pi * i / nu), cy + ry * math.cos(v),
                       cz + rz * math.sin(v) * math.sin(2 * math.pi * i / nu)) for i in range(nu)])
    polys = []
    for j in range(nv):
        a, b = rings[j], rings[j + 1]
        for i in range(nu):
            q = [a[i], a[(i + 1) % nu], b[(i + 1) % nu], b[i]]
            if j == 0: q = [a[i], b[(i + 1) % nu], b[i]]
            elif j == nv - 1 and top >= 0.999: q = [a[i], a[(i + 1) % nu], b[i]]
            polys.append(q)
    if top < 0.999: polys.append(rings[-1])
    cyc = cy + ry * (1 + math.cos(vmax)) / 2 if top < 0.999 else cy
    return _orient(polys, (cx, cyc, cz), color, tag)


class Scene3D(tk.Canvas):
    def __init__(self, parent, bg="#101217", width=420, height=480, **kw):
        super().__init__(parent, bg=bg, width=width, height=height, highlightthickness=0, **kw)
        self.faces, self.yaw, self.pitch, self.zoom = [], 0.6, -0.25, 1.0
        self.key_light = (-0.45, 0.75, -0.65)           # sol-üst-önden gelen ana ışık (görüş uzayında)
        self._drag, self._ids, self.labels = None, {}, []
        self.bind("<ButtonPress-1>", self._press); self.bind("<B1-Motion>", self._move)
        self.bind("<ButtonRelease-1>", self._release); self.bind("<Configure>", lambda e=None: self.render())
        self.bind("<MouseWheel>", self._wheel)
        self.on_pick = None
        self._spin_delay = 40
        self.auto_spin = True
        self._alive = True
        self.bind("<Destroy>", lambda e=None: setattr(self, "_alive", False))

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
        if _animation_budget(self, every)[0]:
            self.after(300, lambda: self.spin(step, every)); return
        delay = every
        if self.auto_spin and not self._drag and self.winfo_ismapped():
            t0 = time.perf_counter()
            self.yaw += step * max(1.0, self._spin_delay / every); self.render()
            ms = (time.perf_counter() - t0) * 1000
            self._spin_ms = 0.8 * getattr(self, "_spin_ms", ms) + 0.2 * ms
            delay = int(max(every, min(200, self._spin_ms * 3)))          # çizim yavaşsa daha seyrek çiz (arayüz akıcı kalsın)
        self._spin_delay = delay
        self.after(_animation_budget(self, delay)[1], lambda: self.spin(step, every))

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
        if getattr(self, "_grad_size", None) == (w, h) and self.find_withtag("bg"): return
        self.delete("bg"); self._grad_size = (w, h)
        a, b = _hex(self.bg_top), _hex(self.bg_bottom or self.bg_top)
        steps = 28
        for i in range(steps):
            k = i / (steps - 1)
            c = "#%02x%02x%02x" % tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3))
            self.create_rectangle(0, h * i / steps, w, h * (i + 1) / steps + 1, fill=c, outline="", tags="bg")

    def label_color(self, tag):
        return "#cfd5df"

    def draw_under(self, w, h, f):
        pass

    def render(self):
        if not self._alive: return
        self.delete("dyn"); self._ids = {}
        w, h = max(50, self.winfo_width()), max(50, self.winfo_height())
        self._gradient(w, h)
        f = min(w, h) * 1.15 * self.zoom
        self.draw_under(w, h, f)
        L = _norm(self.key_light)
        polys = []
        cyw, syw, cp, sp = math.cos(self.yaw), math.sin(self.yaw), math.cos(self.pitch), math.sin(self.pitch)
        hw, hh, cyo, cache = w / 2, h * 0.5, self.center_y, {}
        for pts, color, tag in self.faces:
            pr = []
            for p in pts:                                            # izdüşüm (paylaşılan köşeler bir kez hesaplanır)
                q = cache.get(p)
                if q is None:
                    x, y, z = p[0], p[1] - cyo, p[2]
                    x, z = x * cyw - z * syw, x * syw + z * cyw
                    y, z = y * cp - z * sp, y * sp + z * cp
                    z += 6.0
                    k = f / (z if z > 0.5 else 0.5)
                    q = cache[p] = (hw + x * k, hh - y * k, z, (x, y, z))
                pr.append(q)
            a, b, c = pr[0][3], pr[1][3], pr[2][3]
            n = _norm(_cross(_sub(b, a), _sub(c, a)))
            fc = (sum(p[3][0] for p in pr) / len(pr), sum(p[3][1] for p in pr) / len(pr), sum(p[3][2] for p in pr) / len(pr))
            if _dot(n, fc) > 0: continue                             # arka yüz: görünmez, çizilmez
            scr = [(p[0], p[1]) for p in pr]
            area = 0.0
            for i in range(len(scr)):
                x0, y0 = scr[i - 1]; x1, y1 = scr[i]
                area += x0 * y1 - x1 * y0
            if abs(area) < 3.0: continue                             # ekranda görünmeyecek kadar küçük
            light = 0.38 + 0.72 * max(0.0, _dot(n, L)) + 0.12 * (1 - abs(n[2]))   # ana ışık + kenar parlaması
            polys.append((fc[2], scr, _shade(self.color_of(color, tag), light), tag, abs(area) > 260))
        for depth, pts, col, tag, edge in sorted(polys, key=lambda t: -t[0]):
            i = self.create_polygon(*[c for p in pts for c in p], fill=col, outline=_shade(col, 0.82) if edge else "", tags="dyn")
            if tag: self._ids[i] = tag
        for txt, x, y, col in self.labels:
            self.create_text(x, y, text=txt, fill=col, font=("Segoe UI", 9), anchor="nw", tags="dyn")
        self._draw_anchors(w, h, f)

    def _draw_anchors(self, w, h, f):
        """Yuva etiketleri pencerenin sol/sağ kenarında sütun halinde; parçaya çizgiyle bağlı. Arkadaki parça: kesikli, soluk."""
        if not self.anchors: return
        cols = {-1: [], 1: []}
        for tag, p3, txt in self.anchors:
            x, y, z, _ = self.project(p3, w, h, f)
            cols[1 if x >= w / 2 else -1].append([y, x, z, tag, txt])
        for side, items in cols.items():
            items.sort()
            gap, lo, hi = 17, 12, h - 12
            for i, it in enumerate(items):                      # dikey çakışmayı aç
                it.append(max(it[0], items[i - 1][5] + gap) if i else max(lo, it[0]))
            over = (items[-1][5] - hi) if items else 0
            if over > 0:
                for it in items: it[5] -= over
            for y, x, z, tag, txt, ly in items:
                col = self.label_color(tag)
                behind = z > 6.05
                tx = 6 if side < 0 else w - 6
                i = self.create_text(tx, ly, text=txt, fill=_shade(col, 0.7) if behind else col,
                                     font=("Segoe UI Semibold", 9), anchor="w" if side < 0 else "e", tags="dyn")
                bb = self.bbox(i)
                ex = (bb[2] + 4) if side < 0 else (bb[0] - 4)
                lc = _shade(col, 0.6) if behind else col
                self.create_line(x, y, ex + side * -10, ly, ex, ly, fill=lc, width=1, dash=(2, 3) if behind else None, tags="dyn")
                r = 1.8 if behind else 2.6
                self.create_oval(x - r, y - r, x + r, y + r, fill=lc, outline="", tags="dyn")
                self._ids[i] = tag


# ---------------------------------------------------------------- ajan modelleri (özgün tasarımlar)
SLOTS = ("Mask", "Chest", "Backpack", "Gloves", "Holster", "Kneepads", "Weapon", "Sidearm")
MODELS = ("operator", "scout", "heavy", "urban", "arctic")
THEMES = {   # kıyafet renkleri: kumaş, ikinci kumaş, bot, aksan, metal, kayış
    "night":    {"cloth": "#2a303b", "cloth2": "#1f242d", "boot": "#14171c", "accent": "#ff6d10", "metal": "#3a404b", "strap": "#181b21"},
    "woodland": {"cloth": "#4a5a3c", "cloth2": "#36422c", "boot": "#2b2219", "accent": "#a5814a", "metal": "#3d4137", "strap": "#2a3122"},
    "desert":   {"cloth": "#b29b72", "cloth2": "#8e7853", "boot": "#5b4631", "accent": "#e0bd7f", "metal": "#6b6253", "strap": "#7a6646"},
    "winter":   {"cloth": "#d5dae1", "cloth2": "#aab1bc", "boot": "#4b5059", "accent": "#5b8bd6", "metal": "#7d8592", "strap": "#8e96a3"},
    "urban":    {"cloth": "#4d5465", "cloth2": "#373d4a", "boot": "#1b1e24", "accent": "#3aa0ff", "metal": "#5a6170", "strap": "#292e38"},
    "crimson":  {"cloth": "#3d2629", "cloth2": "#2b1b1d", "boot": "#151012", "accent": "#e0413a", "metal": "#4a3f42", "strap": "#21171a"},
}
SKINS = ("#f0c8a4", "#d4a479", "#a8734d", "#6e4a31")
GUN, GEAR = "#2b2f36", "#555"


def _body(P, k=1.0):
    """Ortak gövde: hafif eğik 'hazır' duruş, tüfek gövdenin önünde iki elle tutulur."""
    F = []
    F += taper(0, 0.93, 0, 0.56 * k, 0.32 * k, 0.62 * k, 0.34 * k, 0.22, P["cloth2"])                  # kalça
    F += taper(0, 1.4, 0, 0.6 * k, 0.33 * k, 0.84 * k, 0.42 * k, 0.74, P["cloth"])                     # gövde
    F += box(0, 1.06, 0, 0.65 * k, 0.08, 0.37 * k, P["strap"])                                          # kemer
    F += cyl((0, 1.74, 0), (0, 1.99, 0), 0.1, 0.095, P["skin"], n=6)                                   # boyun
    F += ell(0, 2.17, -0.01, 0.19, 0.24, 0.21, P["skin"], nu=9, nv=5)                                 # baş
    hands = {1: (0.2, 1.17, -0.5), -1: (-0.33, 1.22, -0.52)}
    for sx in (-1, 1):
        sh, el = (0.5 * k * sx, 1.7, 0.0), (0.6 * k * sx, 1.33, -0.2)
        F += ell(0.47 * k * sx, 1.72, 0, 0.17 * k, 0.15, 0.18, P["cloth"], nu=6, nv=3)                 # omuz
        F += cyl(sh, el, 0.11 * k, 0.095 * k, P["cloth"])                                               # üst kol
        F += cyl(el, hands[sx], 0.09 * k, 0.075 * k, P["cloth2"])                                       # ön kol
        F += ell(*hands[sx], 0.085 * k, 0.095, 0.1, GEAR, "Gloves", nu=6, nv=3)                        # eldiven
        hip, knee, ank = (0.19 * k * sx, 0.9, 0), (0.21 * k * sx, 0.44, -0.04), (0.22 * k * sx, -0.08, 0.0)
        F += cyl(hip, knee, 0.15 * k, 0.12 * k, P["cloth"])                                             # uyluk
        F += cyl(knee, ank, 0.115 * k, 0.085 * k, P["cloth2"])                                          # baldır
        F += ell(0.21 * k * sx, 0.45, -0.13, 0.1 * k, 0.11, 0.06, GEAR, "Kneepads", nu=6, nv=3)        # dizlik
        F += taper(0.22 * k * sx, -0.19, -0.06, 0.2 * k, 0.38, 0.17 * k, 0.26, 0.16, P["boot"], top_shift=(0, 0.04))
    F += box(0.37 * k, 0.66, -0.02, 0.1, 0.3, 0.2, GEAR, "Holster")                                    # kılıf (sağ uyluk)
    F += box(0.38 * k, 0.86, 0.01, 0.08, 0.15, 0.1, GEAR, "Sidearm")                                   # tabanca kabzası
    anchors = {"Gloves": (0.2, 1.17, -0.6), "Holster": (0.45 * k, 0.6, -0.13), "Sidearm": (0.42 * k, 0.86, 0.04),
               "Kneepads": (-0.21 * k, 0.45, -0.2)}
    return F, anchors


def _gun(kind, z=-0.52, y=1.25):
    T, F = "Weapon", []
    if kind == "lmg":
        F += box(-0.02, y, z, 0.72, 0.16, 0.12, GEAR, T)
        F += cyl((-0.38, y + 0.01, z), (-0.98, y + 0.01, z), 0.035, 0.03, GEAR, T, n=6)
        F += box(0.05, y - 0.15, z, 0.18, 0.16, 0.15, GEAR, T)                       # kutu şarjör
        F += taper(0.47, y - 0.02, z, 0.24, 0.08, 0.24, 0.07, 0.15, GEAR, T)
        F += cyl((-0.1, y + 0.1, z), (-0.32, y + 0.1, z), 0.045, 0.05, GEAR, T, n=6)
        for dz in (-0.05, 0.05):
            F += cyl((-0.74, y - 0.02, z), (-0.8, y - 0.26, z + dz), 0.012, 0.012, GEAR, T, n=4, caps=False)
        return F, (-0.92, y, z - 0.02)
    long = {"dmr": 1.06, "ar": 0.88, "smg": 0.56}[kind]
    rl = {"dmr": 0.6, "ar": 0.62, "smg": 0.42}[kind]
    F += box(0, y, z, rl, 0.13, 0.09, GEAR, T)                                         # gövde
    F += cyl((-rl / 2, y + 0.01, z), (-long + 0.22, y + 0.01, z), 0.05, 0.05, GEAR, T, n=6)   # el kundağı
    F += cyl((-long + 0.22, y + 0.01, z), (-long, y + 0.01, z), 0.02, 0.02, GEAR, T, n=6)     # namlu
    mag_h = {"dmr": 0.12, "ar": 0.19, "smg": 0.24}[kind]
    F += taper(0.02, y - 0.06 - mag_h / 2, z - 0.0, 0.07, 0.055, 0.08, 0.06, mag_h, GEAR, T, top_shift=(0.03, 0))
    F += box(0.18, y - 0.1, z, 0.06, 0.12, 0.06, GEAR, T)                              # kabza
    stock = 0.18 if kind == "smg" else 0.27
    F += taper(rl / 2 + stock / 2, y - 0.02, z, stock, 0.07, stock, 0.06, 0.14, GEAR, T)
    if kind == "dmr":
        F += cyl((0.16, y + 0.12, z), (-0.2, y + 0.12, z), 0.045, 0.055, GEAR, T)      # dürbün
    else:
        F += cyl((0.08, y + 0.11, z), (-0.1, y + 0.11, z), 0.035, 0.04, GEAR, T, n=6)  # nişangah
    F += box(0, y + 0.075, z, 0.16, 0.03, 0.05, GEAR, T)
    return F, (-long + 0.08, y, z - 0.02)


def _carrier(k, heavy=False):
    """Plaka taşıyıcı yelek (Chest)."""
    T, F = "Chest", []
    d = 0.1 if heavy else 0.08
    F += box(0, 1.47, -0.21 * k - d / 2 + 0.02, 0.64 * k, 0.54, d, GEAR, T)
    F += box(0, 1.47, 0.21 * k + d / 2 - 0.02, 0.64 * k, 0.58, d, GEAR, T)
    for sx in (-1, 1):
        F += box(0.38 * k * sx, 1.36, 0, 0.08, 0.3, 0.38 * k, GEAR, T)                   # yan kemer
        F += box(0.22 * k * sx, 1.77, 0, 0.11, 0.05, 0.46 * k, GEAR, T)                   # omuz askısı
    for x in (-0.19, 0, 0.19):
        F += box(x * k, 1.32, -0.21 * k - d - 0.04, 0.15 * k, 0.16, 0.08, GEAR, T)        # cepler
    return F


def _pack(k, w=0.56, h=0.66, d=0.3, y=1.45):
    T, F = "Backpack", []
    z = 0.21 * k + 0.06 + d / 2
    F += taper(0, y, z, w * k, d, (w - 0.06) * k, d - 0.04, h, GEAR, T)
    F += box(0, y + h / 2 + 0.03, z - 0.02, (w - 0.08) * k, 0.08, d - 0.02, GEAR, T)     # kapak
    for sx in (-1, 1):
        F += box((w / 2 + 0.05) * k * sx, y - 0.08, z, 0.1, h * 0.5, d * 0.7, GEAR, T)   # yan cepler
    return F, (-0.3, y + 0.15, z + d / 2 + 0.05)


def m_operator(P):
    k = 1.0
    F, A = _body(P, k)
    F += ell(0, 2.24, 0.0, 0.235, 0.21, 0.255, P["cloth2"], nu=9, nv=4, top=0.55)              # kask
    F += box(0, 2.31, -0.25, 0.09, 0.07, 0.05, P["metal"])                                       # gece görüşü yuvası
    for sx in (-1, 1): F += box(0.235 * sx, 2.2, 0, 0.03, 0.06, 0.22, P["metal"])                # raylar
    F += taper(0, 2.05, -0.17, 0.3, 0.12, 0.27, 0.1, 0.17, GEAR, "Mask")                         # yarım yüz maskesi
    F += _carrier(k)
    pf, pa = _pack(k); F += pf
    gf, ga = _gun("ar"); F += gf
    A.update({"Mask": (0, 2.05, -0.27), "Chest": (0.3, 1.58, -0.31), "Backpack": pa, "Weapon": ga})
    return F, A


def m_scout(P):
    k = 0.94
    F, A = _body(P, k)
    F += ell(0, 2.2, 0.03, 0.255, 0.3, 0.275, P["cloth2"], nu=9, nv=5, top=0.6)                 # kapüşon
    F += taper(0, 1.9, 0.14, 0.34, 0.24, 0.28, 0.2, 0.22, P["cloth2"])                           # kapüşon arkası
    F += ell(0, 2.03, -0.04, 0.2, 0.12, 0.2, GEAR, "Mask", nu=9, nv=4)                         # yüz örtüsü
    F += cyl((0, 1.83, 0), (0, 1.94, 0), 0.155, 0.14, GEAR, "Mask")                              # boyun atkısı
    T = "Chest"                                                                                  # hafif göğüs teçhizatı
    F += box(0, 1.3, -0.2, 0.52 * k, 0.2, 0.06, GEAR, T)
    for x in (-0.18, -0.06, 0.06, 0.18):
        F += box(x, 1.3, -0.26, 0.1, 0.17, 0.07, GEAR, T)
    for sx in (-1, 1):
        F += cyl((0.2 * sx, 1.78, -0.16), (0.16 * sx, 1.4, -0.21), 0.035, 0.035, GEAR, T, n=4)
        F += cyl((0.2 * sx, 1.78, 0.16), (0.16 * sx, 1.35, 0.2), 0.035, 0.035, GEAR, T, n=4)
    pf, pa = _pack(k, w=0.4, h=0.72, d=0.2, y=1.5); F += pf
    F += cyl((0.12, 1.86, 0.37), (0.16, 2.45, 0.39), 0.012, 0.008, GEAR, "Backpack", n=4)        # anten
    gf, ga = _gun("dmr"); F += gf
    A.update({"Mask": (0, 2.03, -0.26), "Chest": (0.26, 1.32, -0.31), "Backpack": pa, "Weapon": ga})
    return F, A


def m_heavy(P):
    k = 1.16
    F, A = _body(P, k)
    F += ell(0, 2.2, 0.01, 0.255, 0.29, 0.27, P["cloth2"], nu=9, nv=5)                          # tam kask
    F += ell(0, 2.14, -0.14, 0.2, 0.19, 0.13, GEAR, "Mask", nu=9, nv=5)                         # yüz siperi
    F += _carrier(k, heavy=True)
    T = "Chest"
    F += cyl((0, 1.78, 0), (0, 1.9, 0), 0.24, 0.2, GEAR, T, n=10)                                # boyun koruması
    F += taper(0, 0.86, -0.2, 0.34, 0.06, 0.3, 0.06, 0.3, GEAR, T)                               # kasık plakası
    for sx in (-1, 1):
        F += ell(0.52 * k * sx, 1.76, 0, 0.2 * k, 0.14, 0.22, GEAR, T, nu=7, nv=3, top=0.6)      # omuz zırhı
        F += cyl((0.24 * sx, 0.36, -0.12), (0.25 * sx, 0.02, -0.11), 0.07, 0.06, GEAR, "Kneepads", n=6)  # kaval koruma
    pf, pa = _pack(k, w=0.66, h=0.82, d=0.38, y=1.42); F += pf
    F += box(-0.2, 0.98, 0.3, 0.16, 0.14, 0.2, GEAR, "Backpack")                                 # cephane kutusu
    gf, ga = _gun("lmg"); F += gf
    A.update({"Mask": (0, 2.12, -0.29), "Chest": (0.36, 1.6, -0.36), "Backpack": pa, "Weapon": ga})
    return F, A


def m_urban(P):
    k = 0.98
    F, A = _body(P, k)
    F += ell(0, 2.3, 0.0, 0.205, 0.12, 0.215, P["accent"], nu=10, nv=4, top=0.5)                # şapka
    F += box(0, 2.3, -0.27, 0.22, 0.025, 0.14, P["accent"])                                      # siper
    F += cyl((0, 1.8, 0), (0, 1.9, 0), 0.17, 0.16, P["cloth"], n=8)                              # ceket yakası
    F += taper(0, 0.9, 0, 0.68 * k, 0.4, 0.64 * k, 0.38, 0.2, P["cloth"])                         # ceket eteği
    F += ell(0, 2.05, -0.17, 0.15, 0.13, 0.1, GEAR, "Mask", nu=6, nv=3)                          # gaz maskesi
    F += cyl((0, 2.0, -0.25), (0, 1.97, -0.34), 0.06, 0.06, GEAR, "Mask")                        # filtre
    for sx in (-1, 1): F += box(0.07 * sx, 2.15, -0.2, 0.08, 0.05, 0.03, GEAR, "Mask")          # camlar
    T = "Chest"
    for sx in (-1, 1): F += box(0.16 * sx, 1.46, -0.23, 0.25, 0.46, 0.07, GEAR, T)              # yelek panelleri
    F += box(0, 1.46, 0.23, 0.56, 0.5, 0.06, GEAR, T)
    F += box(0.05, 1.22, 0.3, 0.46, 0.34, 0.16, GEAR, "Backpack")                                # sırt çantası (askılı)
    F += cyl((-0.3, 1.78, -0.05), (0.33, 1.05, -0.12), 0.03, 0.03, GEAR, "Backpack", n=4)       # çapraz askı
    gf, ga = _gun("smg", z=-0.5); F += gf
    A.update({"Mask": (0, 2.02, -0.33), "Chest": (0.28, 1.55, -0.3), "Backpack": (-0.3, 1.3, 0.42), "Weapon": ga})
    return F, A


def m_arctic(P):
    k = 1.06
    F, A = _body(P, k)
    F += taper(0, 0.86, 0, 0.74 * k, 0.46, 0.68 * k, 0.42, 0.34, P["cloth"])                      # parka eteği
    F += cyl((0, 1.78, 0), (0, 1.92, 0), 0.22, 0.17, "#d8d1c4", n=10)                            # kürk yaka
    F += ell(0, 2.27, 0.0, 0.205, 0.17, 0.225, P["cloth2"], nu=9, nv=4, top=0.55)              # bere
    F += cyl((0, 2.2, 0), (0, 2.27, 0), 0.215, 0.215, P["accent"], n=10)                         # bere kıvrımı
    F += ell(0, 2.04, -0.05, 0.2, 0.11, 0.2, GEAR, "Mask", nu=9, nv=4)                         # yüz örtüsü
    F += box(0, 2.17, -0.2, 0.32, 0.08, 0.06, GEAR, "Mask")                                      # kar gözlüğü
    T = "Chest"
    F += box(0, 1.36, -0.24, 0.56, 0.3, 0.07, GEAR, T)
    for x in (-0.18, 0, 0.18): F += box(x, 1.33, -0.3, 0.14, 0.18, 0.07, GEAR, T)
    for sx in (-1, 1): F += cyl((0.21 * sx, 1.78, -0.2), (0.19 * sx, 1.5, -0.25), 0.035, 0.035, GEAR, T, n=4)
    pf, pa = _pack(k, w=0.62, h=0.74, d=0.34, y=1.44); F += pf
    F += cyl((-0.34, 1.94, 0.48), (0.34, 1.94, 0.48), 0.1, 0.1, GEAR, "Backpack")                # uyku tulumu
    gf, ga = _gun("ar"); F += gf
    A.update({"Mask": (0, 2.06, -0.3), "Chest": (0.3, 1.42, -0.33), "Backpack": pa, "Weapon": ga})
    return F, A


BUILDERS = {"operator": m_operator, "scout": m_scout, "heavy": m_heavy, "urban": m_urban, "arctic": m_arctic}


class AgentView(Scene3D):
    """3D ajan modeli; yuva durumları: {"Mask": "ok"|"miss"|"off", …}. Modeller ve kıyafetler değiştirilebilir."""
    COLORS = {"ok": "#22c55e", "miss": "#ef4444", "off": "#4b5263", "sel": "#ff6d10"}
    LABELS = {}

    def __init__(self, parent, model="operator", outfit="night", skin=1, **kw):
        super().__init__(parent, **kw)
        self.status, self.selected, self._pulse, self._names = {}, None, 0.0, {}
        self.center_y, self.zoom = 1.05, 1.55
        self.bg_top, self.bg_bottom = "#1d2230", "#0b0d12"
        self.model, self.outfit, self.skin = "operator", "night", 1
        self.set_look(model, outfit, skin, render=False)

    def set_look(self, model=None, outfit=None, skin=None, render=True):
        if model in BUILDERS: self.model = model
        if outfit in THEMES: self.outfit = outfit
        if isinstance(skin, int) and 0 <= skin < len(SKINS): self.skin = skin
        P = dict(THEMES[self.outfit]); P["skin"] = SKINS[self.skin]
        F, A = BUILDERS[self.model](P)
        F += cyl((0, -0.31, 0), (0, -0.27, 0), 0.7, 0.7, "#12151b", n=16)                         # zemin diski
        self.faces = F
        self.anchors = [(tag, A[tag], self._names.get(tag, tag)) for tag in SLOTS if tag in A]
        if render: self.render()

    def cycle(self, step=1):
        i = (MODELS.index(self.model) + step) % len(MODELS)
        self.set_look(MODELS[i]); return self.model

    def set_labels(self, names):
        self._names = dict(names)
        self.anchors = [(tag, p, self._names.get(tag, txt)) for tag, p, txt in self.anchors]

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
            r = 0.82 + 0.03 * math.sin(self._pulse * 0.4)
            x, y, z, _ = self.project((r * math.cos(math.radians(a)), -0.27, r * math.sin(math.radians(a))), w, h, f)
            pts += [x, y]
        self.create_line(*pts, fill=THEMES[self.outfit]["accent"] if self.outfit != "night" else "#ff6d10", width=2, smooth=True, tags="dyn")

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
        if not _animation_budget(self, every)[0]: self._pulse += 0.25
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
        F = []
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


# ---------------------------------------------------------------- gerçekçi ajanlar (önceden render edilmiş 360° kareler)
SPRITE_MODELS = ("operator", "scout", "heavy", "urban", "arctic")


def sprite_models(base):
    """meta/agents altında kareleri olan kıyafetler (sıralı)."""
    from pathlib import Path
    b = Path(base)
    return [m for m in SPRITE_MODELS if (b / m / "info.json").exists() and (b / m / "f00.webp").exists()]


class SpriteAgentView(tk.Canvas):
    """Blender'da render edilmiş özgün ajan: sürükle → döndür (kareler arası), tıkla → yuva, eksik parça renkli parlar.
    AgentView ile aynı arayüz: set_status, set_labels, set_look, cycle, on_pick, spin, model."""
    COLORS = {"ok": (34, 197, 94), "miss": (239, 68, 68), "sel": (255, 109, 16)}
    sprite = True

    def __init__(self, parent, base, model="operator", width=360, height=420, bg="#101217", **kw):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kw)
        from pathlib import Path
        self.base = Path(base)
        self.models = sprite_models(self.base)
        self.status, self.selected, self._names = {}, None, {}
        self.on_pick, self.auto_spin, self._alive = None, True, True
        self.outfit, self.skin = None, 0
        self.zoom, self._pulse, self._drag = 1.0, 0.0, None
        self._frames, self._cache, self._bg = {}, {}, None
        self.bg_top, self.bg_bottom = "#1d2230", "#0b0d12"
        self.bind("<ButtonPress-1>", self._press); self.bind("<B1-Motion>", self._move)
        self.bind("<ButtonRelease-1>", self._release); self.bind("<MouseWheel>", self._wheel)
        self.bind("<Configure>", lambda e=None: (self._cache.clear(), setattr(self, "_bg", None), self.render()))
        self.bind("<Destroy>", lambda e=None: setattr(self, "_alive", False))
        self.model = None
        self.set_look(model if model in self.models else (self.models[0] if self.models else None), render=False)

    # --- veri
    def _load(self, m):
        import json
        self.info = json.loads((self.base / m / "info.json").read_text(encoding="utf-8"))
        self.n = int(self.info["frames"]); self.size = tuple(self.info["size"])
        self.frame = round(35 / 360 * self.n) % self.n            # 3/4 açıyla başla
        self._frames.clear(); self._cache.clear()

    def _get(self, i):
        from PIL import Image
        if i not in self._frames:
            d = self.base / self.model
            img = Image.open(d / f"f{i:02d}.webp").convert("RGBA"); img.load()
            msk = Image.open(d / f"m{i:02d}.png").convert("L"); msk.load()
            if len(self._frames) >= 8: self._frames.pop(next(iter(self._frames)))
            self._frames[i] = (img, msk)
        return self._frames[i]

    def _geom(self):
        w, h = max(50, self.winfo_width()), max(50, self.winfo_height())
        sw, sh = self.size
        k = min(w / sw, h / sh) * self.zoom
        dw, dh = int(sw * k), int(sh * k)
        return w, h, k, (w - dw) // 2, h - dh - (0 if self.zoom <= 1.0 else int((self.zoom - 1) * dh * 0.35)), dw, dh

    def _background(self, w, h):
        from PIL import Image
        if self._bg and self._bg.size == (w, h): return self._bg
        a, b = _hex(self.bg_top), _hex(self.bg_bottom)
        col = Image.new("RGB", (1, h))
        for y in range(h):
            k = y / max(1, h - 1); col.putpixel((0, y), tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3)))
        self._bg = col.resize((w, h)).convert("RGBA")
        return self._bg

    def _compose(self, i):
        from PIL import Image, ImageTk
        pb = 3 if self.auto_spin and not self._drag else int((0.5 + 0.5 * math.sin(self._pulse)) * 4)   # dönerken sabit, dururken nabız
        key = (i, pb, self.zoom, tuple(sorted(self.status.items())), self.selected, self.winfo_width(), self.winfo_height())
        if key in self._cache: return self._cache[key]
        img, msk = self._get(i)
        r, g, b, a = [0] * 256, [0] * 256, [0] * 256, [0] * 256
        for k, slot in enumerate(self.info.get("slots", SLOTS), start=1):
            st = "sel" if slot == self.selected else self.status.get(slot, "off")
            if st == "off": continue
            c = self.COLORS.get(st)
            if not c: continue
            r[k], g[k], b[k] = c
            a[k] = {"ok": 92, "sel": 130}.get(st, 70 + pb * 22)
        ov = Image.merge("RGBA", (msk.point(r), msk.point(g), msk.point(b), msk.point(a)))
        comp = Image.alpha_composite(img, ov)
        w, h, k, ox, oy, dw, dh = self._geom()
        comp = comp.resize((dw, dh), Image.LANCZOS if (dw, dh) != comp.size else Image.NEAREST)
        canvas = self._background(w, h).copy()
        canvas.alpha_composite(comp, (max(0, ox), max(0, oy)) if ox >= 0 and oy >= 0 else (0, 0))
        ph = ImageTk.PhotoImage(canvas)
        if len(self._cache) >= 16: self._cache.pop(next(iter(self._cache)))
        self._cache[key] = ph
        return ph

    # --- arayüz
    def set_look(self, model=None, outfit=None, skin=None, render=True):
        if model and model in self.models and model != self.model:
            self.model = model; self._load(model)
        if render: self.render()

    def cycle(self, step=1):
        if not self.models: return self.model
        i = (self.models.index(self.model) + step) % len(self.models)
        self.set_look(self.models[i]); return self.model

    def set_labels(self, names): self._names = dict(names)

    def set_status(self, status, selected=None):
        self.status, self.selected = dict(status), selected
        self.render()

    def label_color(self, tag):
        if tag == self.selected: return "#ff6d10"
        return {"ok": "#4ade80", "miss": "#f87171", "off": "#8d95a5"}.get(self.status.get(tag, "off"), "#cfd5df")

    def render(self):
        if not self._alive or not self.model: return
        self.delete("dyn")
        self._ph = self._compose(self.frame)
        self.create_image(0, 0, image=self._ph, anchor="nw", tags="dyn")
        self._labels()

    def _labels(self):
        w, h, k, ox, oy, dw, dh = self._geom()
        anchors = self.info["anchors"][self.frame] if self.frame < len(self.info["anchors"]) else {}
        cols = {-1: [], 1: []}
        for slot in self.info.get("slots", SLOTS):
            if slot not in anchors: continue
            x, y, cnt = anchors[slot]
            X, Y = ox + x * k, oy + y * k
            cols[1 if X >= w / 2 else -1].append([Y, X, cnt < 160, slot, self._names.get(slot, slot)])
        for side, items in cols.items():
            items.sort()
            for j, it in enumerate(items):
                it.append(max(it[0], items[j - 1][5] + 17) if j else max(12, it[0]))
            over = (items[-1][5] - (h - 12)) if items else 0
            if over > 0:
                for it in items: it[5] -= over
            for Y, X, small, slot, txt, ly in items:
                col = self.label_color(slot)
                tx = 6 if side < 0 else w - 6
                i = self.create_text(tx, ly, text=txt, fill=_shade(col, 0.75) if small else col, font=("Segoe UI Semibold", 9),
                                     anchor="w" if side < 0 else "e", tags="dyn")
                bb = self.bbox(i); ex = (bb[2] + 4) if side < 0 else (bb[0] - 4)
                lc = _shade(col, 0.6) if small else col
                self.create_line(X, Y, ex - side * 10, ly, ex, ly, fill=lc, width=1, dash=(2, 3) if small else None, tags="dyn")
                self.create_oval(X - 2.6, Y - 2.6, X + 2.6, Y + 2.6, fill=lc, outline="", tags="dyn")
                self.tag_bind(i, "<Button-1>", lambda e, s=slot: self.on_pick and self.on_pick(s))

    # --- etkileşim
    def _press(self, e): self._drag = [e.x, e.y, False, 0.0]

    def _move(self, e):
        if not self._drag or not self.model: return
        dx = e.x - self._drag[0]; self._drag[0] = e.x
        self._drag[3] += dx
        steps = int(self._drag[3] / 7)
        if steps:
            self._drag[3] -= steps * 7; self._drag[2] = True
            self.frame = (self.frame - steps) % self.n; self.render()

    def _release(self, e):
        if self._drag and not self._drag[2] and self.on_pick and self.model:
            w, h, k, ox, oy, dw, dh = self._geom()
            x, y = int((e.x - ox) / k), int((e.y - oy) / k)
            if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
                v = self._get(self.frame)[1].getpixel((x, y))
                slots = self.info.get("slots", SLOTS)
                if 1 <= v <= len(slots): self.on_pick(slots[v - 1])
        self._drag = None

    def _wheel(self, e):
        self.zoom = max(1.0, min(1.8, self.zoom * (1.1 if e.delta > 0 else 0.9))); self._cache.clear(); self.render()

    def spin(self, every=110):
        if not self._alive: return
        paused, delay = _animation_budget(self, every)
        if paused:
            self.after(300, lambda: self.spin(every)); return
        self._pulse += 0.6
        if self.winfo_ismapped() and self.model:
            if self.auto_spin and not self._drag: self.frame = (self.frame + 1) % self.n
            if self.auto_spin or any(v == "miss" for v in self.status.values()): self.render()
        self.after(delay, lambda: self.spin(every))
