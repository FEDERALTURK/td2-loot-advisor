"""Görsel efektler (hepsi Ayarlar → Efektler'den kapatılabilir):

- CursorFX: özel fare imleci — nişangâh ve genel silah siluetleri (tüfek, SMG, keskin nişancı, tabanca, pompalı)
  ya da kullanıcının kendi görseli (.png/.cur/.ani). Windows .cur dosyası burada üretilir.
- TrailFX: fare hareket ettikçe arkasında solan iz (pencerenin üstünde, tıklamaları geçiren şeffaf katman).
- Transition: sekme değişince kısa saydamlık geçişi + başlığın altında kayan turuncu ışık.
- VideoFX: başlık bandının arkasında döngüyle oynayan sessiz video (kullanıcının kendi oyun kayıtları;
  art/videos klasörü). PyAV (av) ya da OpenCV gerekir; yoksa sessizce kapanır.
Hiçbiri oyuna dokunmaz; yalnızca bu programın penceresini etkiler.
"""
import math
import logging
import os
import random
import struct
import threading
import time
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

CURSOR_STYLES = ["system", "crosshair", "ring", "rifle", "smg", "sniper", "pistol", "shotgun", "custom"]
VIDEO_EXT = (".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v")
ANIM_EXT = (".webp", ".gif")            # Pillow ile ek paket olmadan oynatılır


def _animation_budget(widget, delay_ms):
    """Read the root's cached policy; never probe window focus from an animation."""
    try:
        root = widget._root()
    except (AttributeError, tk.TclError):
        root = widget
    paused = bool(getattr(root, "_td2_suspend_animations", False))
    try:
        speed = float(getattr(root, "_td2_animation_multiplier", 1.0))
        if not math.isfinite(speed): speed = 1.0
    except (TypeError, ValueError):
        speed = 1.0
    return paused, max(1, int(delay_ms / max(0.1, min(1.0, speed))))


# ---------------------------------------------------------------- .cur dosyası
def _hex(c):
    c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def write_cur(img, path, hotspot=(0, 0)):
    """RGBA görüntüden Windows .cur (32 bit BGRA + AND maskesi) yazar."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    xor = bytearray()
    for y in range(h - 1, -1, -1):                       # BMP: alttan üste
        for x in range(w):
            r, g, b, a = px[x, y]
            xor += bytes((b, g, r, a))
    row = ((w + 31) // 32) * 4
    and_mask = bytearray()
    for y in range(h - 1, -1, -1):
        bits = bytearray(row)
        for x in range(w):
            if px[x, y][3] < 10:
                bits[x // 8] |= 0x80 >> (x % 8)
        and_mask += bits
    bih = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0, len(xor) + len(and_mask), 0, 0, 0, 0)
    data = bih + bytes(xor) + bytes(and_mask)
    head = struct.pack("<HHH", 0, 2, 1)
    entry = struct.pack("<BBBBHHII", w if w < 256 else 0, h if h < 256 else 0, 0, 0, hotspot[0], hotspot[1], len(data), 6 + 16)
    Path(path).write_bytes(head + entry + data)


def _short(path):
    """Tk imleç yolunda boşluk sorun çıkarır: Windows kısa yol adı (8.3)."""
    p = str(Path(path).resolve())
    if os.name == "nt" and " " in p:
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(520)
            if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 520): p = buf.value
        except Exception:
            pass
    return p.replace("\\", "/")


def draw_cursor(style, color="#ff6d10", size=32):
    """Genel (markasız) imleç çizimleri. Dönüş: (RGBA görüntü, sıcak nokta)."""
    S = 4                                               # yüksek çözünürlükte çiz, sonra küçült (yumuşak kenar)
    W = size * S
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = _hex(color) + (255,)
    dark = (12, 14, 18, 255)
    lw = max(2, W // 18)
    if style in ("crosshair", "ring"):
        c = W // 2
        if style == "ring":
            d.ellipse((c - W * 0.36, c - W * 0.36, c + W * 0.36, c + W * 0.36), outline=dark, width=lw + 4)
            d.ellipse((c - W * 0.36, c - W * 0.36, c + W * 0.36, c + W * 0.36), outline=col, width=lw)
        for a, b in (((c, W * 0.06), (c, c - W * 0.12)), ((c, c + W * 0.12), (c, W * 0.94)),
                     ((W * 0.06, c), (c - W * 0.12, c)), ((c + W * 0.12, c), (W * 0.94, c))):
            d.line((a, b), fill=dark, width=lw + 4); d.line((a, b), fill=col, width=lw)
        d.ellipse((c - lw, c - lw, c + lw, c + lw), fill=col)
        hot = (size // 2, size // 2)
    else:
        # silah siluetleri: namlu sol üstte (sıcak nokta), dipçik sağ altta; 45° döndürülmüş yatay çizim
        L = W * 1.25
        g = Image.new("RGBA", (int(L), int(L)), (0, 0, 0, 0))
        q = ImageDraw.Draw(g)
        y0 = L * 0.5
        u = L / 100.0

        def rect(x0, yy0, x1, yy1, fill):
            q.rectangle((x0 * u, y0 + yy0 * u, x1 * u, y0 + yy1 * u), fill=fill)

        def gun(fill):
            if style == "rifle":
                rect(2, -2, 30, 1.5, fill); rect(28, -5, 70, 5, fill); rect(40, 5, 47, 18, fill)      # namlu, gövde, şarjör
                rect(54, 5, 59, 13, fill); rect(68, -4, 92, 6, fill); rect(84, 2, 94, 12, fill)        # kabza, dipçik
                rect(38, -9, 52, -5, fill)                                                             # nişangâh
            elif style == "smg":
                rect(10, -2, 30, 2, fill); rect(28, -6, 66, 6, fill); rect(36, 6, 43, 24, fill)
                rect(52, 6, 58, 15, fill); rect(64, -3, 82, 3, fill); rect(78, -3, 84, 9, fill)
            elif style == "sniper":
                rect(0, -1.5, 40, 1.5, fill); rect(38, -4, 74, 5, fill); rect(44, -12, 64, -6, fill)   # uzun namlu, dürbün
                rect(48, 5, 54, 13, fill); rect(72, -4, 96, 7, fill); rect(90, 3, 98, 14, fill)
            elif style == "pistol":
                rect(16, -6, 62, 4, fill); rect(48, 4, 62, 26, fill); rect(40, 4, 48, 9, fill)
            elif style == "shotgun":
                rect(4, -3.5, 46, 3.5, fill); rect(14, 3.5, 40, 7.5, fill); rect(44, -5, 70, 5, fill)
                rect(56, 5, 61, 13, fill); rect(68, -4, 94, 6, fill)
        gun(dark)
        g = g.filter(ImageFilter.MaxFilter(5))                                                         # koyu dış çizgi
        q = ImageDraw.Draw(g)
        gun(col)
        g = g.rotate(-45, resample=Image.BICUBIC, expand=False)
        g = g.crop((int((L - W) / 2), int((L - W) / 2), int((L + W) / 2), int((L + W) / 2)))
        im.alpha_composite(g)
        bb = im.getbbox() or (0, 0, W, W)
        hot = (max(0, bb[0] // S), max(0, bb[1] // S))
    return im.resize((size, size), Image.LANCZOS), hot


class CursorFX:
    def __init__(self, root, folder):
        self.root, self.folder = root, Path(folder)
        self.current = None
        self.spec = ""
        self.enabled = False
        self._enter_bound = False
        self._native_cursor = None
        self._native_cursors = []
        self._native_path = None
        self._native_windows = set()
        self._native_proc = None
        self._user32 = None
        self._comctl32 = None
        # Tk'nın @.cur desteği bütün uygulama widget'larına uygulanır. Eski
        # Windows subclass kancası bazı Tk/Windows bileşimlerinde hata verip
        # imleç değişimini ve tıklamayı etkileyebiliyordu. Bu köprü yalnız
        # geliştirici tarafından açıkça istenirse denenir; normal kullanıcı
        # her zaman güvenli Tk yolu ile çalışır.
        self._native_bridge_enabled = os.environ.get("TD2_CURSOR_NATIVE", "").strip() == "1"
        self._native_bridge_failed = False

    def _install_native_cursor(self, widget):
        """Make Windows use our .cur for this HWND's WM_SETCURSOR messages."""
        if (os.name != "nt" or not self._native_bridge_enabled or self._native_bridge_failed
                or not self.enabled or not self.current):
            return
        # Bir uygulamadaki tüm alt HWND'leri subclass etmek kararsızdır.
        # Tk zaten her alt widget'a @.cur atıyor; deneysel köprü yalnız ana
        # pencereye uygulanabilir.
        if widget is not self.root or not hasattr(widget, "winfo_id"):
            return
        try:
            import ctypes
            if self._user32 is None:
                self._user32 = ctypes.WinDLL("user32", use_last_error=True)
                self._comctl32 = ctypes.WinDLL("comctl32", use_last_error=True)
                self._user32.LoadCursorFromFileW.argtypes = [ctypes.c_wchar_p]
                self._user32.LoadCursorFromFileW.restype = ctypes.c_void_p
                self._user32.SetCursor.argtypes = [ctypes.c_void_p]
                self._user32.SetCursor.restype = ctypes.c_void_p
                self._user32.DestroyCursor.argtypes = [ctypes.c_void_p]
                self._user32.DestroyCursor.restype = ctypes.c_bool
                self._comctl32.DefSubclassProc.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
                self._comctl32.DefSubclassProc.restype = ctypes.c_ssize_t

                callback_type = ctypes.WINFUNCTYPE(
                    ctypes.c_ssize_t, ctypes.c_void_p, ctypes.c_uint,
                    ctypes.c_size_t, ctypes.c_ssize_t, ctypes.c_size_t, ctypes.c_size_t)

                def wndproc(hwnd, message, wparam, lparam, subclass_id, ref_data):
                    # WM_SETCURSOR over client area: Tk's default class cursor
                    # otherwise restores the Windows arrow after each mouse move.
                    if message == 0x0020 and (lparam & 0xFFFF) == 1 and self.enabled and self._native_cursor:
                        self._user32.SetCursor(self._native_cursor)
                        return 1
                    return self._comctl32.DefSubclassProc(hwnd, message, wparam, lparam)

                self._native_proc = callback_type(wndproc)
                self._comctl32.SetWindowSubclass.argtypes = [
                    ctypes.c_void_p, callback_type, ctypes.c_size_t, ctypes.c_size_t]
                self._comctl32.SetWindowSubclass.restype = ctypes.c_bool

            native_path = str(Path(self.current).resolve())
            if self._native_path != native_path:
                new_cursor = self._user32.LoadCursorFromFileW(native_path)
                if new_cursor:
                    self._native_cursor = new_cursor
                    self._native_path = native_path
                    self._native_cursors.append(new_cursor)
                    logging.getLogger("td2.fx").info("Loaded native cursor: %s", native_path)
                else:
                    self._native_bridge_failed = True
                    logging.getLogger("td2.fx").warning("Native cursor bridge unavailable (%s); using Tk cursor fallback", ctypes.get_last_error())

            if not self._native_cursor:
                return
            hwnd = int(widget.winfo_id())
            if hwnd not in self._native_windows:
                if self._comctl32.SetWindowSubclass(hwnd, self._native_proc, id(self), 0):
                    self._native_windows.add(hwnd)
                    logging.getLogger("td2.fx").debug("Installed native cursor hook for HWND %s", hwnd)
                else:
                    self._native_bridge_failed = True
                    logging.getLogger("td2.fx").warning("Native cursor bridge rejected (%s); using Tk cursor fallback", ctypes.get_last_error())
        except Exception:
            # Tk'nın yapılandırılmış imleci güvenli geri dönüş yoludur.
            # Hata bir kez kaydedilir ve sonraki widget'larda tekrar denenmez.
            self._native_bridge_failed = True
            logging.getLogger("td2.fx").warning("Native cursor bridge unavailable; using Tk cursor fallback", exc_info=True)
            return

    def _apply_tree(self, widget, spec):
        """Tk cursors belong to individual widgets; update the visible tree too."""
        try:
            widget.configure(cursor=spec)
        except Exception:
            pass
        self._install_native_cursor(widget)
        try:
            children = widget.winfo_children()
        except Exception:
            children = ()
        for child in children:
            self._apply_tree(child, spec)

    def _on_enter(self, event):
        # Some screens set hand2/arrow on hover. Apply the selected app cursor
        # after those widget-level bindings have run.
        if not self.enabled or not self.spec:
            return
        widget = getattr(event, "widget", None)
        if widget is not None:
            try:
                widget.configure(cursor=self.spec)
            except Exception:
                pass
            self._install_native_cursor(widget)

    def refresh(self):
        """Reapply the app cursor after tabs or dynamic screen content change."""
        if self.enabled:
            self._apply_tree(self.root, self.spec)

    def apply(self, enabled, style="crosshair", color="#ff6d10", custom="", scale=1.0):
        try:
            if not enabled or style == "system":
                self.enabled = False; self.spec = ""
                self._apply_tree(self.root, "")
                self.current = None
                return True
            if os.name != "nt":                                   # Tk'nın renkli imleç dosyası desteği Windows'ta
                self.enabled = True
                self.spec = "crosshair" if style in ("crosshair", "ring") else "tcross"
                self._apply_tree(self.root, self.spec)
                if not self._enter_bound:
                    self.root.bind_all("<Enter>", self._on_enter, add="+")
                    self._enter_bound = True
                return True
            self.folder.mkdir(parents=True, exist_ok=True)
            size = 48 if scale >= 1.2 else 32
            if style == "custom" and custom and Path(custom).exists():
                if Path(custom).suffix.lower() in (".cur", ".ani"):
                    path = Path(custom)
                else:
                    img = Image.open(custom).convert("RGBA"); img.thumbnail((size, size), Image.LANCZOS)
                    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0)); canvas.alpha_composite(img, (0, 0))
                    path = self.folder / "custom.cur"; write_cur(canvas, path, (0, 0))
            else:
                img, hot = draw_cursor(style if style != "custom" else "crosshair", color, size)
                path = self.folder / f"{style}_{color.lstrip('#')}_{size}.cur"
                if not path.exists(): write_cur(img, path, hot)
            self.spec = "@" + _short(path)
            self.root.config(cursor=self.spec)
            self.current = path
            self.enabled = True
            self._apply_tree(self.root, self.spec)
            if not self._enter_bound:
                self.root.bind_all("<Enter>", self._on_enter, add="+")
                self._enter_bound = True
            return True
        except Exception:
            self.enabled = False; self.spec = ""
            try: self._apply_tree(self.root, "")
            except Exception: pass
            return False


# ---------------------------------------------------------------- fare izi
class TrailFX:
    KEY = "#010203"

    def __init__(self, root, color="#ff6d10", length=18, click_through=None):
        self.root, self.color, self.length = root, color, max(4, int(length))
        self.pts, self.win, self.cv, self.alive = [], None, None, False
        self.click_through = click_through
        self._line_ids = []
        self._dot_id = None

    def start(self):
        if self.alive or os.name != "nt": return False
        try:
            w = self.win = tk.Toplevel(self.root)
            w.overrideredirect(True)
            w.attributes("-transparentcolor", self.KEY)
            w.configure(bg=self.KEY)
            w.transient(self.root)
            self.cv = tk.Canvas(w, bg=self.KEY, highlightthickness=0, bd=0)
            self.cv.pack(fill="both", expand=True)
            w.update_idletasks()
            if self.click_through: self.click_through(w)
            self.alive = True
            self._tick()
            return True
        except Exception:
            self.stop(); return False

    def stop(self):
        self.alive = False
        try:
            if self.win: self.win.destroy()
        except Exception:
            pass
        self.win = self.cv = None; self.pts = []
        self._line_ids = []; self._dot_id = None

    def _shade(self, k):
        r, g, b = _hex(self.color)
        br, bg_, bb = 15, 17, 22
        return "#%02x%02x%02x" % (int(br + (r - br) * k), int(bg_ + (g - bg_) * k), int(bb + (b - bb) * k))

    def _tick(self):
        if not self.alive: return
        try:
            r = self.root
            if r.state() == "iconic" or not r.winfo_viewable():
                self.win.withdraw(); self.root.after(200, self._tick); return
            paused, _ = _animation_budget(r, 33)
            if paused:
                self.win.withdraw(); self.root.after(300, self._tick); return
            if self.win.state() == "withdrawn": self.win.deiconify()
            x, y, w, h = r.winfo_rootx(), r.winfo_rooty(), r.winfo_width(), r.winfo_height()
            geo = f"{w}x{h}+{x}+{y}"
            if self.win.geometry() != geo: self.win.geometry(geo)
            self._n = getattr(self, "_n", 0) + 1
            if self._n % 15 == 0: self.win.lift(r)               # her karede değil (pencere sırası savaşı = kasma)
            px, py = r.winfo_pointerxy()
            inside = x <= px < x + w and y <= py < y + h
            if inside and (not self.pts or (px - x, py - y) != self.pts[-1][:2]):
                self.pts.append((px - x, py - y, time.time()))
            now = time.time()
            self.pts = [p for p in self.pts if now - p[2] < 0.35][-self.length:]
            if not self.pts and getattr(self, "_empty", False):
                self.root.after(60, self._tick); return          # iz yok: çizme
            self._empty = not self.pts
            n = len(self.pts)
            for i in range(1, n):
                k = i / n
                (x0, y0, _), (x1, y1, _) = self.pts[i - 1], self.pts[i]
                opts = {"fill": self._shade(k), "width": max(1, int(1 + 5 * k)), "capstyle": "round", "state": "normal"}
                if i - 1 < len(self._line_ids):
                    item = self._line_ids[i - 1]
                    self.cv.coords(item, x0, y0, x1, y1); self.cv.itemconfigure(item, **opts)
                else:
                    self._line_ids.append(self.cv.create_line(x0, y0, x1, y1, **opts))
            for item in self._line_ids[max(0, n - 1):]:
                self.cv.itemconfigure(item, state="hidden")
            if n:
                hx, hy, _ = self.pts[-1]
                if self._dot_id is None:
                    self._dot_id = self.cv.create_oval(hx - 3, hy - 3, hx + 3, hy + 3, fill=self.color, outline="")
                else:
                    self.cv.coords(self._dot_id, hx - 3, hy - 3, hx + 3, hy + 3)
                    self.cv.itemconfigure(self._dot_id, fill=self.color, state="normal")
            elif self._dot_id is not None:
                self.cv.itemconfigure(self._dot_id, state="hidden")
        except Exception:
            pass
        self.root.after(_animation_budget(self.root, 40)[1], self._tick)


# ---------------------------------------------------------------- sekme geçişi
class NavMotif(tk.Canvas):
    """Sidebar için düşük maliyetli, oyun-HUD esintili çapraz veri bandı.

    Sadece birkaç çizgi çizer; fare olayı bağlamaz ve üstteki düğmelerin hitbox
    alanına girmez. ``flash`` yalnızca menü değiştiğinde tek seferlik vurgu
    yapar, sürekli bir animasyon döngüsü başlatmaz.
    """

    def __init__(self, parent, accent="#ff6d10", bg="#0f1116", muted="#2c313d"):
        super().__init__(parent, height=24, bg=bg, highlightthickness=0, bd=0)
        self.accent, self.bg, self.muted = accent, bg, muted
        self._flash = 0
        self.bind("<Configure>", self._draw, add="+")
        self.after_idle(self._draw)

    def _draw(self, _event=None):
        try:
            w, h = max(1, self.winfo_width()), max(1, self.winfo_height())
            self.delete("all")
            # İnce çapraz yüzeyler: kart eğmek yerine görsel yön hissi verir.
            self.create_line(0, h - 3, min(w, 76), 3, fill=self.muted, width=1)
            self.create_line(52, h - 3, min(w, 140), 3, fill=self.muted, width=1)
            self.create_line(126, h - 3, min(w, 214), 3, fill=self.muted, width=1)
            self.create_line(0, h - 1, min(w, 74), 1, fill=self.accent, width=2)
            if self._flash:
                self.create_polygon(74, 1, min(w, 104), 1, min(w, 92), h - 1, 62, h - 1,
                                    fill=self.accent, outline="")
        except tk.TclError:
            return

    def flash(self):
        self._flash += 1
        token = self._flash
        self._draw()
        self.after(180, lambda: self._clear_flash(token))

    def _clear_flash(self, token):
        if token != self._flash:
            return
        self._flash = 0
        self._draw()


class DigitalRain(tk.Canvas):
    """Üst menü şeridi için aşağı akan yeşil/camgöbeği kod animasyonu (Matrix esintili).

    Yalnızca dekoratiftir: fare/tık olayı bağlamaz. Üstüne `create_window` ile gömülen
    gerçek widget'lar (ör. menü düğmeleri) aralarındaki boşluklarda animasyonu görünür
    bırakır — ayrı bir sidebar veya şeffaflık hilesi gerekmez. Kare başı hücre silip
    yeniden yaratmak yerine sabit bir ızgara item'ı yeniden kullanılır (Tk'da asıl yük budur).
    """

    FPS = 12
    GLYPHS = "01" + "ABCDEF0123456789" + ":;.·-_/"   # her fontta güvenle render olan sade bir küme

    def __init__(self, parent, bg="#0a0d12", dim="#1f7a73", bright="#6aedd9", height=50, cell_w=15, cell_h=16):
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self.dim_color, self.bright_color = dim, bright
        self.cell_w, self.cell_h = cell_w, cell_h
        self._cols = []            # her sütun: {head, speed, trail, glyphs: {row: char}}
        self._grid = []            # [[item_id, ...], ...] sütun x satır, kalıcı metin item'ları
        self._size = (0, 0)
        self._alive = True
        self.bind("<Configure>", self._on_resize, add="+")
        self.bind("<Destroy>", lambda _e: setattr(self, "_alive", False), add="+")
        self.after_idle(self._tick)

    def _on_resize(self, _event=None):
        w, h = max(1, self.winfo_width()), max(1, self.winfo_height())
        n_cols = max(1, w // self.cell_w)
        n_rows = max(1, h // self.cell_h) + 2       # +2: iz, görünür alanın az ötesine taşabilsin
        if (n_cols, n_rows) == self._size:
            return
        self._size = (n_cols, n_rows)
        self.delete("rain")
        self._grid = [[self.create_text((c + 0.5) * self.cell_w, r * self.cell_h, text="",
                                        fill=self.dim_color, font=("Consolas", 10), anchor="n", tags=("rain",))
                       for r in range(n_rows)] for c in range(n_cols)]
        self._cols = [self._new_column(n_rows) for _ in range(n_cols)]
        self.tag_lower("rain")

    def _new_column(self, n_rows):
        return {"head": random.uniform(-n_rows, 0), "speed": random.uniform(0.35, 1.1),
                "trail": random.randint(5, max(6, n_rows)), "glyphs": {}}

    def _tick(self):
        if not self._alive:
            return
        try:
            if not self.winfo_viewable():
                self.after(260, self._tick); return
            self._on_resize()
            paused, delay = _animation_budget(self, round(1000 / self.FPS))
            if not paused:
                self._advance()
            self.after(delay, self._tick)
        except tk.TclError:
            self._alive = False

    def _advance(self):
        n_cols, n_rows = self._size
        for c in range(n_cols):
            col = self._cols[c]
            col["head"] += col["speed"]
            if col["head"] - col["trail"] > n_rows:           # kuyruk ekranın tamamen dışına çıktı: baştan başlat
                self._cols[c] = col = self._new_column(n_rows)
            glyphs, head, trail = col["glyphs"], col["head"], col["trail"]
            for r in range(n_rows):
                item = self._grid[c][r]
                dist = head - r
                if dist < 0 or dist >= trail:
                    self.itemconfigure(item, text="")
                    glyphs.pop(r, None)
                    continue
                if r not in glyphs or random.random() < 0.04:      # karakterler ara sıra kendiliğinden değişir
                    glyphs[r] = random.choice(self.GLYPHS)
                k = 1.0 - dist / trail                              # 1.0 = baş (parlak), 0 = kuyruk ucu (soluk)
                color = self.bright_color if dist < 1.1 else _blend_hex(self.dim_color, self.bright_color, max(0.0, k))
                self.itemconfigure(item, text=glyphs[r], fill=color)

    def destroy(self):
        self._alive = False
        super().destroy()


def _blend_hex(a, b, amount):
    amount = max(0.0, min(1.0, amount))
    ar, ag, ab = _hex(a); br, bg_, bb = _hex(b)
    return "#%02x%02x%02x" % (int(ar + (br - ar) * amount), int(ag + (bg_ - ag) * amount), int(ab + (bb - ab) * amount))


class CommandRibbon(tk.Canvas):
    """İçerik alanı için TD2-esintili komuta şeridi.

    Bu şerit gerçek paneli kaydırmaz: Tk widget'larının yerleşimini oynatmak
    küçük pencerede odak ve tıklama sorunları çıkarır. Bunun yerine seçilen
    bölüm değiştiğinde şerit üzerinde kısa bir veri taraması gösterir.
    """

    FPS = 30
    INTERVAL_MS = round(1000 / FPS)

    def __init__(self, parent, accent="#ff6d10", bg="#0f1116", surface="#151a22", muted="#667080"):
        super().__init__(parent, height=42, bg=bg, highlightthickness=0, bd=0)
        self.accent, self.bg, self.surface, self.muted = accent, bg, surface, muted
        self.title, self.detail = "ISAC // OPERATION CENTER", "SYSTEM NOMINAL"
        self._generation = 0
        self.bind("<Configure>", self._draw, add="+")
        self.after_idle(self._draw)

    def set_context(self, title, detail=""):
        self.title = (title or "ISAC").upper()
        self.detail = (detail or "SYSTEM NOMINAL").upper()
        self._draw()

    def _draw(self, _event=None, sweep=None):
        try:
            w, h = max(1, self.winfo_width()), max(1, self.winfo_height())
            self.delete("all")
            # Çapraz uçlu yüzey; oyun arayüzü ritmi verir, ancak alanın tamamı
            # pasiftir ve altındaki sekmelere hiç girdi göndermez.
            cut = min(24, max(10, w // 24))
            self.create_polygon(0, 2, w - cut, 2, w, h - 2, 0, h - 2,
                                fill=self.surface, outline=self.muted)
            self.create_rectangle(0, 2, 5, h - 2, fill=self.accent, outline="")
            for x in range(14, min(w, 180), 28):
                self.create_line(x, h - 4, x + 13, 4, fill=self.muted, width=1)
            self.create_text(16, 14, anchor="w", text=self.title, fill="#ffffff",
                             font=("Segoe UI Semibold", 10))
            self.create_text(16, 30, anchor="w", text=self.detail, fill=self.muted,
                             font=("Segoe UI", 8))
            self.create_text(w - 16, 21, anchor="e", text="●  LINKED", fill=self.accent,
                             font=("Segoe UI Semibold", 8))
            if sweep is not None:
                x = int(max(-70, min(w + 20, sweep)))
                self.create_polygon(x - 38, 3, x, 3, x - 18, h - 3, x - 56, h - 3,
                                    fill=self.accent, outline="")
        except tk.TclError:
            return

    def pulse(self):
        self._generation += 1
        token, started = self._generation, time.perf_counter()
        self._pulse_tick(token, started)

    def _pulse_tick(self, token, started):
        if token != self._generation:
            return
        try:
            if not self.winfo_exists():
                return
            ratio = min(1.0, (time.perf_counter() - started) / 0.24)
            self._draw(-55 + (self.winfo_width() + 100) * ratio)
            if ratio < 1.0:
                self.after(self.INTERVAL_MS, lambda: self._pulse_tick(token, started))
            else:
                self._draw()
        except tk.TclError:
            return


class FieldConsole(CommandRibbon):
    """Tam kabuk düzeni için büyük saha-terminali başlığı."""
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.configure(height=82)

    def _draw(self, _event=None, sweep=None):
        try:
            w, h = max(1, self.winfo_width()), max(1, self.winfo_height())
            self.delete("all")
            cut = min(54, max(24, w // 18))
            self.create_polygon(0, 3, w - cut, 3, w, h - 3, 0, h - 3, fill=self.surface, outline=self.muted)
            self.create_rectangle(0, 3, 7, h - 3, fill=self.accent, outline="")
            for x in range(18, w, 46): self.create_line(x, h - 5, x + 28, 5, fill=self.muted, width=1)
            self.create_text(22, 25, anchor="w", text=self.title, fill="#ffffff", font=("Segoe UI Semibold", 18))
            self.create_text(22, 51, anchor="w", text=self.detail + "  //  SECURE UPLINK", fill=self.muted, font=("Segoe UI Semibold", 9))
            self.create_text(w - 22, 25, anchor="e", text="SHD-02  •  ONLINE", fill=self.accent, font=("Segoe UI Semibold", 10))
            self.create_text(w - 22, 50, anchor="e", text="FIELD NETWORK / ENCRYPTED", fill=self.muted, font=("Segoe UI", 8))
            if sweep is not None:
                x = int(max(-90, min(w + 25, sweep)))
                self.create_polygon(x - 55, 4, x, 4, x - 28, h - 4, x - 83, h - 4, fill=self.accent, outline="")
        except tk.TclError:
            return


class SHDStatusBar(tk.Canvas):
    """Özgün SHD-terminal kromu: bağlantı, saat, ping ve 30 FPS scanner çizgisi."""
    def __init__(self, parent, accent="#ff5a00", bg="#0b0e14", fg="#ffffff", muted="#a0aab2", footer=False):
        super().__init__(parent, height=26 if footer else 54, bg=bg, highlightthickness=0, bd=0)
        self.accent, self.bg, self.fg, self.muted, self.footer = accent, bg, fg, muted, footer
        self.t0 = time.perf_counter(); self.bind("<Configure>", self._draw, add="+"); self.after_idle(self._tick)
    def _draw(self, _event=None):
        try:
            w, h = max(1,self.winfo_width()), max(1,self.winfo_height()); self.delete("all")
            scan = int((time.perf_counter()-self.t0)*150)%max(1,w)
            if self.footer:
                self.create_text(10,h//2,anchor="w",text="[ LOG ]  SYSTEM READY  //  OCR LINK STANDBY  //  MEMORY NOMINAL",fill=self.muted,font=("Consolas",8))
                self.create_text(w-10,h//2,anchor="e",text="[ SHD // LOCAL ]",fill=self.accent,font=("Consolas",8))
            else:
                self.create_text(12,16,anchor="w",text="[ SHD_NET // SECURE_CONNECTION ]",fill=self.fg,font=("Consolas",10,"bold"))
                self.create_text(w-12,16,anchor="e",text=time.strftime("%H:%M:%S")+"  //  ONLINE - 14ms",fill=self.muted,font=("Consolas",9))
                self.create_line(0,39,w,39,fill=self.muted,width=1)
                self.create_line(max(0,scan-80),39,min(w,scan),39,fill=self.accent,width=2)
                self.create_text(12,49,anchor="w",text="[ STRATEGIC HOMELAND DIVISION // TERMINAL ]",fill=self.accent,font=("Consolas",7))
        except tk.TclError: return
    def _tick(self):
        self._draw(); self.after(33,self._tick)


class SafeTrail:
    """Tıklama geçiren ayrı pencere olmadan, ana pencerenin arkasında fare izi.

    Canvas en alta indirildiği için yalnız boş/terminal arka planında görünür;
    düğme, liste ve metin bileşenlerinin üstüne hiç çıkmaz. Böylece eski
    transparent Toplevel'in siyah kutu ve tıklama engelleme riski yoktur.
    """
    FPS = 30
    def __init__(self, root, color="#ff5a00", length=14):
        self.root, self.color = root, color
        self.length = max(6, min(32, int(length)))
        self.cv = tk.Canvas(root, bg=root.cget("bg"), highlightthickness=0, bd=0)
        self.cv.place(x=0, y=0, relwidth=1, relheight=1)
        # NOT: self.cv.lower() ÇAĞIRMA — Canvas kendi .lower() metodunu canvas-öge (tag_lower)
        # sözdizimiyle gölgeliyor; argümansız çağrılırsa Tcl "wrong # args" TclError fırlatır.
        # Pencere yığın sırasında bu widget'ı geriye almak için Misc'in orijinal metodunu kullan.
        tk.Misc.lower(self.cv)
        self.points, self.alive, self._job = [], True, None
        self._bind = root.bind("<Motion>", self._motion, add="+")

    def _motion(self, event):
        if not self.alive: return
        try:
            x, y = event.x_root - self.root.winfo_rootx(), event.y_root - self.root.winfo_rooty()
            if not self.points or abs(x-self.points[-1][0]) + abs(y-self.points[-1][1]) >= 3:
                self.points.append((x,y,time.perf_counter()))
                self.points = self.points[-self.length:]
            if self._job is None: self._tick()
        except tk.TclError: pass

    def _tick(self):
        if not self.alive: return
        try:
            now=time.perf_counter(); self.points=[p for p in self.points if now-p[2] < .48]
            self.cv.delete("trail")
            for i,(x,y,stamp) in enumerate(self.points):
                age=now-stamp; radius=max(2,int(7*(1-age/.55)))
                # Tk alpha yok; küçükten büyüğe dolgu yerine ince halkalar çizilir.
                self.cv.create_oval(x-radius,y-radius,x+radius,y+radius,outline=self.color,width=1,tags="trail")
            if self.points: self._job=self.root.after(round(1000/self.FPS),self._tick)
            else: self._job=None
        except tk.TclError: self._job=None

    def stop(self):
        self.alive=False
        try:
            if self._job: self.root.after_cancel(self._job)
            self.root.unbind("<Motion>", self._bind)
            self.cv.destroy()
        except tk.TclError: pass


class Transition:
    """Sekme göstergesi: seçili sekmenin altında kalıcı turuncu bir çizgi; sekme değişince eski sekmeden yenisine
    akıcı biçimde kayar ve yeni sekmenin genişliğine oturur. Şekiller her karede yeniden yaratılmaz (yalnız konumları
    güncellenir), pencerenin saydamlığına dokunulmaz. play(notebook, eski, yeni) · duration (ms) ile hız."""

    def __init__(self, root, bar_parent=None, color="#ff6d10", bg="#0f1116", duration_ms=260, style="soft"):
        self.root, self.color, self.bg = root, color, bg
        self.duration = max(120, min(450, int(duration_ms)))
        self.style = style if style in ("soft", "tactical") else "soft"
        self.bar = None
        self._gen = 0
        self._spans = {}
        self._pos = None                                 # (sol, sağ) şu anki çizgi
        self.frames = 0                                  # test: çizilen kare sayısı
        self.debug = {}

    def _tab_spans(self, nb):
        """Sekmelerin x aralıkları ve sekme satırının alt kenarı (Tk'dan; ekran ölçeğinden bağımsız)."""
        w = nb.winfo_width()
        key = (w, nb.index("end"), tuple(nb.tab(i, "text") for i in range(nb.index("end"))))
        if self._spans.get("key") == key: return self._spans["v"]
        ymid = None
        for y in range(2, 90, 2):
            try:
                nb.index(f"@20,{y}"); ymid = y; break
            except tk.TclError:
                continue
        spans, bottom = {}, 0
        if ymid is not None:
            x = 0
            while x < w:                                  # kaba tarama, sınırlarda inceltme
                try:
                    i = nb.index(f"@{x},{ymid}")
                    a, b = spans.get(i, (x, x)); spans[i] = (min(a, x), max(b, x))
                except tk.TclError:
                    pass
                x += 4
            for y in range(ymid, ymid + 120):
                try: nb.index(f"@20,{y}"); bottom = y
                except tk.TclError: break
        v = (spans, bottom + 1)
        self._spans = {"key": key, "v": v}
        return v

    def _ensure_bar(self, nb, bottom):
        if self.bar is None or not self.bar.winfo_exists() or self.bar.master is not nb:
            self.bar = tk.Canvas(nb, height=5, bg=self.bg, highlightthickness=0, bd=0)
            self.glow = self.bar.create_rectangle(0, 1, 0, 4, fill=self._dim(0.35), outline="")
            self.line = self.bar.create_rectangle(0, 1, 0, 4, fill=self.color, outline="")
            self.tip = self.bar.create_polygon(0, 0, 0, 0, 0, 0, fill=self.color, outline="")
            nb.bind("<Configure>", lambda e: self.snap(nb), add="+")
        self.bar.place(x=0, y=bottom, relwidth=1, height=5)
        self.bar.tk.call("raise", self.bar._w)

    def _draw(self, l, r, glow=0.0):
        pad = 4
        self.bar.coords(self.line, l + pad, 1, r - pad, 4)
        g = 10 * glow
        self.bar.coords(self.glow, l + pad - g, 1, r - pad + g, 4)
        if self.style == "tactical":
            # TD2 benzeri yön oku: kısa, yalnız geçiş çizgisine bağlı ve
            # 30 FPS bütçesinde. Bu nedenle içerik alanını yeniden çizmez.
            self.bar.coords(self.tip, r - pad, 0, r - pad + 8, 2.5, r - pad, 5)
            self.bar.itemconfigure(self.tip, state="normal")
        else:
            self.bar.itemconfigure(self.tip, state="hidden")
        self._pos = (l, r)

    def snap(self, nb):
        """Çizgiyi animasyonsuz seçili sekmenin altına koy (açılış, pencere boyutu değişince)."""
        try:
            spans, bottom = self._tab_spans(nb)
            cur = nb.index(nb.select())
            if cur not in spans: return
            self._ensure_bar(nb, bottom)
            self._draw(*spans[cur])
        except Exception:
            pass

    def play(self, nb=None, old=None, new=None):
        self._gen += 1
        g = self._gen
        self.debug = {"old": old, "new": new}
        try:
            if nb is None: self.debug["why"] = "no notebook"; return
            spans, bottom = self._tab_spans(nb)
            self.debug.update(spans={str(k): v for k, v in spans.items()}, bottom=bottom)
            if new not in spans: self.debug["why"] = "tab not found"; return
            self._ensure_bar(nb, bottom)
            a0 = self._pos or spans.get(old, spans[new]); a1 = spans[new]
            self.debug["from"], self.debug["to"] = a0, a1
            self._tick(g, time.perf_counter(), a0, a1)
        except Exception as e:
            self.debug["why"] = repr(e)

    @staticmethod
    def _ease(k):
        return 1 - (1 - k) ** 3

    def _tick(self, g, t0, a0, a1):
        if g != self._gen: return                         # yeni geçiş başladı: o devralır
        try:
            if not self.bar.winfo_exists(): return
        except tk.TclError:
            return
        k = min(1.0, (time.perf_counter() - t0) * 1000 / self.duration)
        e = self._ease(k)
        l = a0[0] + (a1[0] - a0[0]) * e
        r = a0[1] + (a1[1] - a0[1]) * e
        self._draw(l, r, glow=(1 - k) * 1.0)
        self.frames += 1
        if k < 1.0:
            # Sekme çizgisi dekoratiftir; 30 FPS akıcı görünür ve dar
            # pencerede menü tıklamalarına rakip olmaz.
            self.root.after(33, lambda: self._tick(g, t0, a0, a1))
        else:
            self.debug["end"] = self._pos

    def _dim(self, a):
        r, g, b = _hex(self.color); br, bg_, bb = _hex(self.bg)
        a = max(0.0, min(1.0, a))
        return "#%02x%02x%02x" % (int(br + (r - br) * a), int(bg_ + (g - bg_) * a), int(bb + (b - bb) * a))

    def destroy(self):
        try:
            if self.bar: self.bar.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------- arka plan videosu
def video_backend():
    """av / cv2 varsa mp4 de oynar; yoksa 'pil' (yalnızca .webp/.gif animasyonları, ek paket gerekmez)."""
    try:
        import av  # noqa: F401  (yalnızca var mı diye)
        return "av"
    except Exception:
        pass
    try:
        import cv2  # noqa: F401
        return "cv2"
    except Exception:
        return "pil"


def list_videos(folder, backend=None):
    """Oynatılabilir dosyalar. Aynı adlı .mp4 ve .webp varsa biri seçilir (mp4 oynatıcı varsa mp4)."""
    f = Path(folder)
    be = backend or video_backend()
    exts = ANIM_EXT + (VIDEO_EXT if be in ("av", "cv2") else ())
    try:
        files = sorted(p for p in f.iterdir() if p.suffix.lower() in exts)
    except Exception:
        return []
    by_stem = {}
    for p in files:
        cur = by_stem.get(p.stem)
        if cur is None or (be in ("av", "cv2") and p.suffix.lower() in VIDEO_EXT):
            by_stem[p.stem] = p
    return sorted(by_stem.values())


class VideoFX:
    """Videoları sırayla/karışık döngüde çözer, (genişlik, yükseklik) boyutunda karartılmış PIL kareleri verir."""

    def __init__(self, folder, on_frame, size_fn, fps=24, dim=0.45, pause_fn=None):
        self.folder, self.on_frame, self.size_fn = Path(folder), on_frame, size_fn
        self.fps, self.dim = fps, dim
        self.alive, self.thread, self.error = False, None, None
        self.pause_fn = pause_fn

    def _paused(self):
        try: return bool(self.pause_fn and self.pause_fn())
        except Exception: return False

    def start(self):
        if self.alive: return True
        if not list_videos(self.folder):
            self.error = "no_videos"; return False
        self.alive = True
        self.thread = threading.Thread(target=self._run, daemon=True); self.thread.start()
        return True

    def stop(self):
        self.alive = False

    def _frames_av(self, path):
        import av
        with av.open(str(path)) as c:
            st = c.streams.video[0]
            st.thread_type = "AUTO"
            for fr in c.decode(st):
                if not self.alive: return
                w, h = self.size_fn()
                yield fr.to_image()

    def _frames_pil(self, path):
        from PIL import ImageSequence
        with Image.open(path) as im:
            dur = im.info.get("duration") or 1000 / self.fps
            self._frame_dt = max(0.02, float(dur) / 1000)
            for fr in ImageSequence.Iterator(im):
                if not self.alive: return
                yield fr.convert("RGB")

    def _frames_cv2(self, path):
        import cv2
        cap = cv2.VideoCapture(str(path))
        try:
            while self.alive:
                ok, fr = cap.read()
                if not ok: return
                yield Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        finally:
            cap.release()

    def _run(self):
        from PIL import ImageOps
        be = video_backend()
        while self.alive:
            vids = list_videos(self.folder)
            if not vids: break
            random.shuffle(vids)
            for v in vids:
                if not self.alive: break
                gen = self._frames_pil if v.suffix.lower() in ANIM_EXT else (self._frames_av if be == "av" else self._frames_cv2)
                self._frame_dt = 1.0 / self.fps
                try:
                    frames = iter(gen(v))
                    try:
                        while self.alive:
                            if self._paused():
                                time.sleep(0.3); continue       # do not decode/resize a hidden frame
                            try: img = next(frames)
                            except StopIteration: break
                            t0 = time.time()
                            w, h = self.size_fn()
                            if w < 10 or h < 10: time.sleep(0.2); continue
                            frame = ImageOps.fit(img, (w, h), Image.BILINEAR)
                            if self.dim > 0:
                                frame = Image.blend(frame, Image.new("RGB", frame.size, (8, 9, 12)), self.dim)
                            self.on_frame(frame)
                            time.sleep(max(0.0, self._frame_dt - (time.time() - t0)))
                    finally:
                        close = getattr(frames, "close", None)
                        if close: close()
                except Exception as e:
                    self.error = f"{type(e).__name__}: {e}"
                    time.sleep(0.5)
        self.alive = False


# ---------------------------------------------------------------- tüm pencere arka planı: ajan saati
class _ItemPool:
    """Canvas şekillerini her karede silip yeniden yaratmak yerine yeniden kullanır (Tk'da asıl yük budur).
    Her kare aynı sırayla çizildiği için üst üste binme sırası değişmez."""

    def __init__(self, cv):
        self.cv, self.items, self.idx = cv, {}, {}

    def reset(self):
        self.items, self.idx = {}, {}

    def begin(self):
        self.idx = {k: 0 for k in self.items}

    def put(self, kind, *coords, **opts):
        opts.pop("tags", None)
        lst = self.items.setdefault(kind, [])
        i = self.idx.get(kind, 0); self.idx[kind] = i + 1
        if i < len(lst):
            it = lst[i]
            self.cv.coords(it, *coords)
            self.cv.itemconfigure(it, state="normal", **opts)
        else:
            lst.append(getattr(self.cv, "create_" + kind)(*coords, tags="dyn", **opts))

    def end(self):
        for kind, lst in self.items.items():
            for it in lst[self.idx.get(kind, 0):]:
                self.cv.itemconfigure(it, state="hidden")
        self.cv.tag_raise("dyn")


class AgentWatch:
    """Canvas üzerinde çizilen, fareyi takip eden turuncu ajan saati (özgün tasarım, oyun logosu yok).
    Halkalar, saniye çizgileri, dönen kesikli yaylar, saat/dakika/saniye yayları, ortada saat;
    dış halkadaki turuncu ışık (kuyruklu) fare hangi yöndeyse oraya döner."""

    def __init__(self, canvas, pointer_fn, color="#ff6d10", bg="#0f1116", dim=0.0, variant="standard"):
        self.cv, self.pointer_fn, self.c, self.bgc = canvas, pointer_fn, color, bg
        self.dim = dim
        self.variant = variant
        self.angle = -90.0                  # ışığın açısı (derece, Tk: 0 = doğu, saat yönünün tersi pozitif)
        self.alive, self._size, self._img = True, (0, 0), None
        self.t0 = time.time()
        self._pool = _ItemPool(canvas)

    def _col(self, k):
        """k: 0 = arka plan, 1 = tam turuncu."""
        r, g, b = _hex(self.c); br, bg_, bb = _hex(self.bgc)
        k = max(0.0, min(1.0, k * (1 - self.dim)))
        return "#%02x%02x%02x" % (int(br + (r - br) * k), int(bg_ + (g - bg_) * k), int(bb + (b - bb) * k))

    def _grey(self, k):
        br, bg_, bb = _hex(self.bgc)
        k = k * (1 - self.dim)
        return "#%02x%02x%02x" % (int(br + (110 - br) * k), int(bg_ + (118 - bg_) * k), int(bb + (132 - bb) * k))

    def _backdrop(self, w, h):
        """Statik zemin: tema varyantına göre HUD veya saha haritası (PIL → PhotoImage)."""
        from PIL import ImageTk
        base = Image.new("RGB", (w, h), _hex(self.bgc))
        d = ImageDraw.Draw(base)
        if self.variant == "field":
            # Field Terminal: saat/halkalardan tamamen ayrı, düşük kontrastlı
            # sokak/koordinat ızgarası. Statik üretildiği için kare maliyeti yok.
            r, g, b = _hex(self.bgc)
            grid = (min(255, r + 22), min(255, g + 24), min(255, b + 16))
            faint = (min(255, r + 12), min(255, g + 13), min(255, b + 9))
            for x in range(-h, w + h, 54): d.line((x, 0, x + h, h), fill=faint, width=1)
            for y in range(18, h, 36): d.line((0, y, w, y), fill=grid if y % 72 == 18 else faint, width=1)
            for x in range(28, w, 86): d.line((x, 0, x, h), fill=faint, width=1)
            # bölge blokları — harita hissi, gerçek oyun haritası/varlığı değil.
            for i in range(9):
                x = (i * 137 + 35) % max(1, w); y = (i * 79 + 30) % max(1, h)
                d.rectangle((x, y, min(w, x + 82), min(h, y + 34)), outline=grid, width=1)
            self._img = ImageTk.PhotoImage(base)
            return self._img
        r = 26
        gcol = tuple(min(255, int(v * 1.25) + 4) for v in _hex(self.bgc))
        y, row = -r, 0
        while y < h + r:
            x = -r + (r * 0.866 if row % 2 else 0)
            while x < w + r:
                d.polygon([(x + r * 0.9 * math.cos(math.radians(60 * k + 30)), y + r * 0.9 * math.sin(math.radians(60 * k + 30)))
                           for k in range(6)], outline=gcol)
                x += r * 1.732
            y += r * 1.5; row += 1
        for yy in range(0, h, 4):
            d.line((0, yy, w, yy), fill=tuple(max(0, v - 3) for v in _hex(self.bgc)))
        # merkezden dışa doğru kararan vinyet
        cx, cy = self.center(w, h)
        mask = Image.new("L", (w, h), 0)
        md = ImageDraw.Draw(mask)
        R = max(w, h)
        for k in range(30, 0, -1):
            rr = R * k / 30
            md.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=int(255 * (1 - k / 30) ** 0.7))
        dark = Image.new("RGB", (w, h), tuple(max(0, v - 8) for v in _hex(self.bgc)))
        base = Image.composite(base, dark, mask)
        self._img = ImageTk.PhotoImage(base)
        return self._img

    def center(self, w, h):
        return w * 0.5, h * 0.54

    def _arc(self, cx, cy, r, start, extent, color, width, tag="dyn"):
        self._pool.put("arc", cx - r, cy - r, cx + r, cy + r, start=start, extent=extent, style="arc",
                       outline=color, width=width)

    def render(self):
        if not self.alive: return
        try:
            w, h = max(100, self.cv.winfo_width()), max(100, self.cv.winfo_height())
        except tk.TclError:
            self.alive = False; return
        cv = self.cv
        if (w, h) != self._size:
            self._size = (w, h)
            cv.delete("all"); self._pool.reset()
            cv.create_image(0, 0, anchor="nw", image=self._backdrop(w, h), tags="bgimg")
        P = self._pool; P.begin()
        cx, cy = self.center(w, h)
        R = min(w, h) * 0.40
        now = time.time(); tt = now - self.t0
        lt = time.localtime(now)
        # fare yönü (yumuşak takip)
        try:
            px, py = self.pointer_fn()
            target = math.degrees(math.atan2(-(py - cy), px - cx))
        except Exception:
            target = self.angle
        diff = (target - self.angle + 540) % 360 - 180
        self.angle += diff * 0.18
        if self.variant == "field":
            self._render_field(P, w, h, cx, cy, R, tt, target)
            P.end()
            return
        # dış çerçeve
        for k, wd in ((1.12, 1), (1.06, 2)):
            P.put("oval", cx - R * k, cy - R * k, cx + R * k, cy + R * k, outline=self._grey(0.22), width=wd, tags="dyn")
        # saniye çizgileri (60), saniyeye gelen turuncu
        sec = lt.tm_sec + (now % 1)
        for i in range(60):
            a = math.radians(90 - i * 6)
            long_ = i % 5 == 0
            r0, r1 = R * (0.93 if long_ else 0.96), R * 1.0
            near = max(0.0, 1 - ((sec - i) % 60) / 8)
            col = self._col(0.35 + 0.65 * near) if near > 0 else self._grey(0.45 if long_ else 0.25)
            P.put("line", cx + r0 * math.cos(a), cy - r0 * math.sin(a), cx + r1 * math.cos(a), cy - r1 * math.sin(a),
                           fill=col, width=3 if long_ else 1, tags="dyn")
        # dönen kesikli yaylar
        for k, (rr, spd, n, ext) in enumerate(((0.86, 12, 12, 18), (0.78, -7, 6, 34), (0.62, 20, 24, 6))):
            for j in range(n):
                self._arc(cx, cy, R * rr, (tt * spd + j * 360 / n) % 360, ext, self._col(0.28 + 0.1 * k), 2)
        # saat / dakika / saniye yayları
        hh = (lt.tm_hour % 12 + lt.tm_min / 60) / 12
        mm = (lt.tm_min + sec / 60) / 60
        for rr, frac, wd, k in ((0.70, hh, 6, 0.55), (0.66, mm, 4, 0.75), (0.735, sec / 60, 2, 1.0)):
            self._arc(cx, cy, R * rr, 90, -360 * max(0.002, frac), self._col(k), wd)
            self._arc(cx, cy, R * rr, 90 - 360 * frac, -(360 * (1 - frac)), self._grey(0.12), 1)
        # genişleyen nabız halkası
        p = (tt % 4) / 4
        rr = R * (0.4 + 0.75 * p)
        P.put("oval", cx - rr, cy - rr, cx + rr, cy + rr, outline=self._col(0.5 * (1 - p)), width=2, tags="dyn")
        # Etkinlik katmanları boş alanları doldurur; yalnızca arka planda çizilir ve 12 FPS sınırını korur.
        scan_angle = (tt * (18 if self.variant == "isac" else 11)) % 360
        if self.variant == "isac":
            # ISAC: tarama ışını, veri düğümleri ve koordinat çizgileri.
            a = math.radians(scan_angle)
            ex, ey = cx + R * 1.04 * math.cos(a), cy - R * 1.04 * math.sin(a)
            P.put("line", cx, cy, ex, ey, fill=self._col(0.42), width=2, tags="dyn")
            for j in range(5):
                aa = math.radians(scan_angle + j * 47)
                nr = R * (0.38 + (j % 3) * 0.19)
                nx, ny = cx + nr * math.cos(aa), cy - nr * math.sin(aa)
                pulse = 0.35 + 0.35 * (0.5 + 0.5 * math.sin(tt * 2.4 + j))
                P.put("oval", nx - 4, ny - 4, nx + 4, ny + 4, fill=self._col(pulse), outline="", tags="dyn")
                P.put("line", nx, ny, cx + (nx - cx) * 0.78, cy + (ny - cy) * 0.78,
                           fill=self._col(0.18), width=1, dash=(3, 4), tags="dyn")
            P.put("text", cx, cy + R * 0.34, text="ISAC // LIVE SCAN", fill=self._col(0.44),
                       font=("Segoe UI Semibold", max(8, int(R * 0.22) // 5)), tags="dyn")
        elif self.variant == "rogue":
            # Rogue: kırmızı risk dilimleri, bozulan sinyal parçaları ve uyarı nabzı.
            for j in range(7):
                start = (scan_angle + j * 51) % 360
                self._arc(cx, cy, R * (0.52 + (j % 2) * 0.22), start, 18,
                          self._col(0.22 + 0.11 * (j % 3)), 3)
            for j in range(6):
                xx = cx - R * 0.82 + j * R * 0.32
                yy = cy + R * (0.46 + 0.08 * math.sin(tt * 1.8 + j))
                P.put("line", xx, yy, xx + R * 0.16, yy, fill=self._col(0.26 + 0.12 * (j % 2)), width=2, tags="dyn")
            warn = 0.45 + 0.35 * (0.5 + 0.5 * math.sin(tt * 3.0))
            P.put("text", cx, cy + R * 0.34, text="ROGUE SIGNAL // UNSTABLE", fill=self._col(warn),
                       font=("Segoe UI Semibold", max(8, int(R * 0.22) // 5)), tags="dyn")
        # fareyi takip eden turuncu ışık + kuyruk + parıltı katmanları
        A = self.angle
        for k in range(6, 0, -1):                                   # kuyruk (ters yönde, solarak)
            self._arc(cx, cy, R * 1.06, A - 18 - k * 9 * (1 if diff >= 0 else -1) * 0.6, 14, self._col(0.15 + 0.1 * (6 - k)), 3)
        for wd, k in ((22, 0.18), (14, 0.35), (8, 0.7), (4, 1.0)):   # parıltı
            self._arc(cx, cy, R * 1.06, A - 18, 36, self._col(k), wd)
        ax, ay = cx + R * 1.06 * math.cos(math.radians(A)), cy - R * 1.06 * math.sin(math.radians(A))
        for rad, k in ((12, 0.25), (7, 0.6), (4, 1.0)):
            P.put("oval", ax - rad, ay - rad, ax + rad, ay + rad, fill=self._col(k), outline="", tags="dyn")
        ix, iy = cx + R * 0.55 * math.cos(math.radians(A)), cy - R * 0.55 * math.sin(math.radians(A))
        P.put("line", ix, iy, cx + R * 0.97 * math.cos(math.radians(A)), cy - R * 0.97 * math.sin(math.radians(A)),
                       fill=self._col(0.45), width=1, dash=(4, 4), tags="dyn")
        # merkez: saat
        fs = max(14, int(R * 0.22))
        P.put("text", cx, cy - R * 0.06, text=time.strftime("%H:%M", lt), fill=self._col(1.0),
                       font=("Segoe UI Semibold", fs), tags="dyn")
        P.put("text", cx + R * 0.34, cy - R * 0.02, text=time.strftime("%S", lt), fill=self._col(0.7),
                       font=("Segoe UI Semibold", max(9, fs // 3)), tags="dyn", anchor="w")
        P.put("text", cx, cy + R * 0.16, text=time.strftime("%d.%m.%Y", lt), fill=self._grey(0.8),
                       font=("Segoe UI", max(8, fs // 4)), tags="dyn")
        P.put("text", cx, cy - R * 0.33, text="◆ AGENT", fill=self._col(0.6), font=("Segoe UI Semibold", max(8, fs // 4)), tags="dyn")
        P.end()

    def _render_field(self, P, w, h, cx, cy, R, tt, target):
        """Saat/agent halkası olmadan saha haritası taraması — 12 FPS arka plan katmanı."""
        # Koordinat köşeleri ve tarama bandı, gerçek oyun haritasını kopyalamaz.
        P.put("text", 22, 18, text="SHD FIELD TERMINAL", fill=self._col(0.88),
              font=("Segoe UI Semibold", 11), anchor="w", tags="dyn")
        P.put("text", 22, 35, text="SECTOR MAP // DATA LINK STABLE", fill=self._grey(0.7),
              font=("Segoe UI", 8), anchor="w", tags="dyn")
        P.put("text", w - 22, 18, text="GRID 04-A", fill=self._col(0.62),
              font=("Segoe UI Semibold", 9), anchor="e", tags="dyn")
        # Harita merkezi + merkezden fare yönüne kısa doğrultu; ajan saati yok.
        mx, my = cx, cy
        P.put("rectangle", mx - R * 0.58, my - R * 0.34, mx + R * 0.58, my + R * 0.34,
              outline=self._grey(0.38), width=1, tags="dyn")
        scan_x = mx - R * 0.58 + ((tt * R * 0.55) % max(1, R * 1.16))
        P.put("line", scan_x, my - R * 0.34, scan_x, my + R * 0.34,
              fill=self._col(0.52), width=2, tags="dyn")
        a = math.radians(target)
        ex, ey = mx + R * 0.48 * math.cos(a), my - R * 0.48 * math.sin(a)
        P.put("line", mx, my, ex, ey, fill=self._col(0.50), width=2, tags="dyn")
        # Değişmeyen düğümler, hafif periyodik güç değerleri.
        for index, (dx, dy) in enumerate(((-.38, -.18), (-.12, .20), (.22, -.10), (.42, .24), (.06, -.29))):
            nx, ny = mx + R * dx, my + R * dy
            pulse = .30 + .35 * (0.5 + 0.5 * math.sin(tt * 2.6 + index * 1.7))
            P.put("oval", nx - 4, ny - 4, nx + 4, ny + 4, fill=self._col(pulse), outline="", tags="dyn")
            P.put("line", nx, ny, mx + (nx - mx) * .72, my + (ny - my) * .72,
                  fill=self._grey(.25), width=1, dash=(3, 4), tags="dyn")
        for step, label in enumerate(("SAFEHOUSE", "SUPPLY", "INTEL")):
            x = 22 + step * 115
            P.put("text", x, h - 22, text="■ " + label, fill=self._grey(.70),
                  font=("Segoe UI Semibold", 8), anchor="w", tags="dyn")


class WatchBackground:
    """Windows: ana pencerenin ARKASINDA duran ikinci bir pencere ajan saatini çizer; ana pencerenin
    zemin rengi (-transparentcolor) şeffaf yapılır → kartlar ve listeler okunur kalır, boşluklarda saat görünür.
    Diğer sistemlerde (şeffaflık yok) kapalı kalır."""

    def __init__(self, root, bg="#0f1116", color="#ff6d10", dim=0.0, fps=12, variant="standard"):
        self.root, self.bgc, self.color, self.dim, self.fps = root, bg, color, dim, fps
        self.variant = variant
        self.win = self.cv = self.watch = None
        self.alive = False
        self._geo = None

    def start(self):
        if self.alive or os.name != "nt": return False
        try:
            w = self.win = tk.Toplevel(self.root)
            w.overrideredirect(True)
            w.configure(bg=self.bgc)
            self.cv = tk.Canvas(w, bg=self.bgc, highlightthickness=0, bd=0)
            self.cv.pack(fill="both", expand=True)
            self.watch = AgentWatch(self.cv, self._pointer, self.color, self.bgc, self.dim, self.variant)
            # Şeffaf zemin piksellerine yapılan tıklamaları Windows bu pencereye verir: programdaki karşılığına ilet
            # (menü sekmesi, düğme, liste) — yoksa harflerin arası / kenarlar tıklanmıyormuş gibi olur.
            for seq in ("<ButtonPress-1>", "<ButtonRelease-1>", "<Double-Button-1>", "<ButtonPress-3>", "<ButtonRelease-3>",
                        "<B1-Motion>", "<MouseWheel>"):
                self.cv.bind(seq, lambda e, seq=seq: self._forward(e, seq))
            self._last_ptr, self._last_move, self._last_z = None, time.time(), 0.0
            w.withdraw()                                 # doğru yere konana kadar görünmesin (sol üstte belirmesin)
            w.update_idletasks()
            self._style(w)
            self.alive = True
            self._n, self._keyed = 0, False                # zemin, saat yerine oturunca şeffaflaşır
            for ev in ("<Map>", "<Configure>"):            # açılış, büyütme/küçültme, taşıma: konumu yeniden eşitle
                self.root.bind(ev, self._resync, add="+")
            self._tick()
            return True
        except Exception:
            self.stop(); return False

    def _style(self, w):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(w.winfo_id())
            ex = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex | 0x08000000 | 0x80)   # NOACTIVATE + TOOLWINDOW
            self._hwnd = hwnd
        except Exception:
            self._hwnd = None

    def _below_root(self):
        try:
            import ctypes
            rh = ctypes.windll.user32.GetParent(self.root.winfo_id())
            # SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE: arka plan penceresini ana pencerenin hemen altına koy
            ctypes.windll.user32.SetWindowPos(self._hwnd, rh, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0010)
        except Exception:
            pass

    def _pointer(self):
        x, y = self.root.winfo_pointerxy()
        return x - self.root.winfo_rootx(), y - self.root.winfo_rooty()

    def _forward(self, e, seq):
        """Arka plana düşen fare olayını, ana pencerede o noktadaki bileşene gönder."""
        try:
            if seq == "<ButtonPress-1>": self.root.focus_force()
            tgt = self._widget_at(e.x_root, e.y_root)
            if tgt is None: return
            kw = {"x": e.x_root - tgt.winfo_rootx(), "y": e.y_root - tgt.winfo_rooty(), "rootx": e.x_root, "rooty": e.y_root}
            if seq == "<MouseWheel>":
                tgt.event_generate("<MouseWheel>", delta=e.delta, **kw)
            else:
                tgt.event_generate(seq, **kw)
        except Exception:
            pass

    def _widget_at(self, X, Y):
        """Ana pencerede ekran noktasındaki en içteki bileşen. winfo_containing kullanılamaz: Windows şeffaf
        pikselde arka plan penceresini döndürür. Bileşen ağacı ve konumları Tk'dan okunur."""
        w = self.root
        if not (w.winfo_rootx() <= X < w.winfo_rootx() + w.winfo_width() and w.winfo_rooty() <= Y < w.winfo_rooty() + w.winfo_height()):
            return None
        while True:
            nxt = None
            for c in reversed(w.winfo_children()):             # sonra eklenen üstte
                try:
                    if isinstance(c, tk.Toplevel) or not c.winfo_ismapped(): continue
                    x, y = c.winfo_rootx(), c.winfo_rooty()
                    if x <= X < x + c.winfo_width() and y <= Y < y + c.winfo_height():
                        nxt = c; break
                except tk.TclError:
                    continue
            if nxt is None: return w
            w = nxt

    def set_cursor(self, spec):
        """Arka plan penceresinde de programın imleci (boşluklarda Windows'un beyaz oku görünmesin)."""
        try:
            if self.win: self.win.configure(cursor=spec)
            if self.cv: self.cv.configure(cursor=spec)
        except Exception:
            pass

    def _active(self):
        """Program öndeyken ve fare yakın zamanda oynadıysa akıcı; değilse yavaş çiz (kasma olmasın)."""
        try:
            p = self.root.winfo_pointerxy()
            if p != self._last_ptr: self._last_ptr, self._last_move = p, time.time()
            import ctypes
            from ctypes import wintypes
            fg = ctypes.windll.user32.GetForegroundWindow()
            pid = wintypes.DWORD(); ctypes.windll.user32.GetWindowThreadProcessId(fg, ctypes.byref(pid))
            return pid.value == os.getpid() and time.time() - self._last_move < 3.0
        except Exception:
            return True

    def stop(self):
        self.alive = False
        self._keyed = False
        try: self.root.attributes("-transparentcolor", "")
        except Exception: pass
        try:
            if self.win: self.win.destroy()
        except Exception:
            pass
        self.win = self.cv = self.watch = None

    def _resync(self, _e=None):
        self._geo = None

    def _client_rect(self):
        """Ana pencerenin iç alanının GERÇEK ekran koordinatları (Windows'tan; Tk'nın açılıştaki eski değerleri değil)."""
        try:
            import ctypes
            from ctypes import wintypes
            h = self.root.winfo_id()
            rc = wintypes.RECT(); ctypes.windll.user32.GetClientRect(h, ctypes.byref(rc))
            pt = wintypes.POINT(0, 0); ctypes.windll.user32.ClientToScreen(h, ctypes.byref(pt))
            if rc.right > 1 and rc.bottom > 1:
                return pt.x, pt.y, rc.right, rc.bottom
        except Exception:
            pass
        r = self.root
        return r.winfo_rootx(), r.winfo_rooty(), r.winfo_width(), r.winfo_height()

    def _place(self, geo):
        """Konum + boyut + z-sırası tek çağrıda: ana pencerenin hemen arkası."""
        x, y, w, h = geo
        try:
            import ctypes
            rh = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if self._hwnd and ctypes.windll.user32.SetWindowPos(self._hwnd, rh, x, y, w, h, 0x0010 | 0x0040):  # NOACTIVATE|SHOWWINDOW
                return
        except Exception:
            pass
        self.win.geometry(f"{w}x{h}+{x}+{y}")

    def _tick(self):
        if not self.alive: return
        try:
            r = self.root
            if r.state() in ("iconic", "withdrawn") or not r.winfo_viewable():
                if self.win.state() != "withdrawn": self.win.withdraw()
                self._geo = None
                self.root.after(250, self._tick); return
            if _animation_budget(r, 50)[0]:
                self.root.after(300, self._tick); return       # keep last frame and click forwarding intact
            self._n += 1
            active = self._active()
            fps = self.fps if active else 5
            if self._n % max(1, fps) == 0: self._geo = None           # saniyede bir zorla eşitle
            geo = self._client_rect()
            if self.win.state() == "withdrawn":
                self.win.deiconify(); self._geo = None
            if geo != self._geo:
                self._geo = geo
                self._place(geo)
                if not self._keyed:                        # artık saat arkada: boşluklarda masaüstü değil saat görünür
                    self.root.attributes("-transparentcolor", self.bgc); self._keyed = True
            elif time.time() - self._last_z > 1.0:          # pencere sırası her karede değil, saniyede bir
                self._below_root(); self._last_z = time.time()
            self.watch.render()
        except Exception:
            fps = 5
        self.root.after(_animation_budget(self.root, int(1000 / max(1, fps)))[1], self._tick)
