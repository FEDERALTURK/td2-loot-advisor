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

    def apply(self, enabled, style="crosshair", color="#ff6d10", custom="", scale=1.0):
        try:
            if not enabled or style == "system":
                self.root.config(cursor=""); self.current = None; return True
            if os.name != "nt":                                   # Tk'nın renkli imleç dosyası desteği Windows'ta
                self.root.config(cursor="crosshair" if style in ("crosshair", "ring") else "tcross"); return True
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
            self.root.config(cursor="@" + _short(path))
            self.current = path
            return True
        except Exception:
            try: self.root.config(cursor="")
            except Exception: pass
            return False


# ---------------------------------------------------------------- fare izi
class TrailFX:
    KEY = "#010203"

    def __init__(self, root, color="#ff6d10", length=18, click_through=None):
        self.root, self.color, self.length = root, color, max(4, int(length))
        self.pts, self.win, self.cv, self.alive = [], None, None, False
        self.click_through = click_through

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
            self.cv.delete("all")
            n = len(self.pts)
            for i in range(1, n):
                k = i / n
                (x0, y0, _), (x1, y1, _) = self.pts[i - 1], self.pts[i]
                self.cv.create_line(x0, y0, x1, y1, fill=self._shade(k), width=max(1, int(1 + 5 * k)), capstyle="round")
            if n:
                hx, hy, _ = self.pts[-1]
                self.cv.create_oval(hx - 3, hy - 3, hx + 3, hy + 3, fill=self.color, outline="")
        except Exception:
            pass
        self.root.after(_animation_budget(self.root, 33)[1], self._tick)


# ---------------------------------------------------------------- sekme geçişi
class Transition:
    """Sekme göstergesi: seçili sekmenin altında kalıcı turuncu bir çizgi; sekme değişince eski sekmeden yenisine
    akıcı biçimde kayar ve yeni sekmenin genişliğine oturur. Şekiller her karede yeniden yaratılmaz (yalnız konumları
    güncellenir), pencerenin saydamlığına dokunulmaz. play(notebook, eski, yeni) · duration (ms) ile hız."""

    def __init__(self, root, bar_parent=None, color="#ff6d10", bg="#0f1116", duration_ms=260):
        self.root, self.color, self.bg = root, color, bg
        self.duration = max(120, min(450, int(duration_ms)))
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
            self.bar = tk.Canvas(nb, height=3, bg=self.bg, highlightthickness=0, bd=0)
            self.glow = self.bar.create_rectangle(0, 0, 0, 3, fill=self._dim(0.35), outline="")
            self.line = self.bar.create_rectangle(0, 0, 0, 3, fill=self.color, outline="")
            nb.bind("<Configure>", lambda e: self.snap(nb), add="+")
        self.bar.place(x=0, y=bottom, relwidth=1, height=3)
        self.bar.tk.call("raise", self.bar._w)

    def _draw(self, l, r, glow=0.0):
        pad = 4
        self.bar.coords(self.line, l + pad, 0, r - pad, 3)
        g = 10 * glow
        self.bar.coords(self.glow, l + pad - g, 0, r - pad + g, 3)
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
            self.root.after(12, lambda: self._tick(g, t0, a0, a1))
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

    def __init__(self, canvas, pointer_fn, color="#ff6d10", bg="#0f1116", dim=0.0):
        self.cv, self.pointer_fn, self.c, self.bgc = canvas, pointer_fn, color, bg
        self.dim = dim
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
        """Statik zemin: radyal karanlık, altıgen ızgara, tarama çizgileri (PIL → PhotoImage)."""
        from PIL import ImageTk
        base = Image.new("RGB", (w, h), _hex(self.bgc))
        d = ImageDraw.Draw(base)
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


class WatchBackground:
    """Windows: ana pencerenin ARKASINDA duran ikinci bir pencere ajan saatini çizer; ana pencerenin
    zemin rengi (-transparentcolor) şeffaf yapılır → kartlar ve listeler okunur kalır, boşluklarda saat görünür.
    Diğer sistemlerde (şeffaflık yok) kapalı kalır."""

    def __init__(self, root, bg="#0f1116", color="#ff6d10", dim=0.0, fps=20):
        self.root, self.bgc, self.color, self.dim, self.fps = root, bg, color, dim, fps
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
            self.watch = AgentWatch(self.cv, self._pointer, self.color, self.bgc, self.dim)
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
