"""Yerinde çeviri: Türkçe metin, oyundaki İngilizce yazının tam üstüne, opak bir arka fonla yerleşir.

Neden fon: çeviri doğrudan bindirilirse iki yazı üst üste biner ve okunmaz. Her blok kendi kutusunda, oyunun panel
rengine yakın opak bir fonla gösterilir; fon İngilizce yazıyı tamamen örter. Türkçe daha uzunsa önce yazı küçülür
(en az MIN_PT), yine sığmazsa yalnız boş alana uzar. Komşu satırlar kaydırılmaz; çok dar alanda
yazı küçültülür ve gerekirse üç noktayla kısaltılır. Tam metin geçmiştedir.
Kutular tek bir şeffaf, tıklama geçiren pencerede çizilir ve
ekran yakalamasından dışlanır (program kendi çevirisini yeniden okumaz).

    items = layout(blocks, area, measure)      # saf yerleşim (test edilebilir)
    ov = InPlace(root, style); ov.show(items, area); ov.hide()
"""
import re
import math
import os

MIN_PT = 8
PAD = 4


def wrap(text, width, measure):
    """Kelimeleri genişliğe göre satırlara böl; mevcut satır sonları korunur. measure(s) → piksel."""
    out = []
    for para in str(text).split("\n"):
        words, cur = para.split(), ""
        if not words: out.append(""); continue
        for w in words:
            if measure(w) > width:
                if cur: out.append(cur); cur = ""
                piece = ""
                for char in w:
                    if piece and measure(piece + char) > width:
                        out.append(piece); piece = ""
                    piece += char
                cur = piece
                continue
            cand = (cur + " " + w).strip()
            if not cur or measure(cand) <= width: cur = cand
            else: out.append(cur); cur = w
        out.append(cur)
    return out


def fit(text, w, h, measure_at, start_pt, min_pt=MIN_PT, line_gap=1.05):
    """Kutuya sığan en büyük punto ve satırlar. measure_at(pt) → (ölçü işlevi, satır yüksekliği px).
    Dönüş: (punto, satırlar, gereken yükseklik px)."""
    pt = max(min_pt, int(start_pt))
    while True:
        meas, lh = measure_at(pt)
        lines = wrap(text, max(10, w - 2 * PAD), meas)
        need = int(len(lines) * lh * line_gap) + 2 * PAD
        widest = max((meas(l) for l in lines), default=0) + 2 * PAD
        if (need <= h and widest <= w) or pt <= min_pt:
            return pt, lines, max(need, h)
        pt -= 1


def layout(blocks, area, measure_at, px_to_pt=0.75, max_pt=28):
    """blocks: [(çeviri, (x0,y0,x1,y1) alan içinde px, özgün metin, satır sayısı)] → çizim listesi.
    Çeviri özgünle aynıysa (ör. "Exotic Cache") kutu çizilmez, oyunun yazısı görünür kalır."""
    blocks = list(blocks)
    items = []
    aw, ah = int(area["width"]), int(area["height"])
    if aw <= 0 or ah <= 0: return items
    for tr, box, en, nlines in blocks:
        if not tr or not tr.strip() or norm(tr) == norm(en): continue
        x0, y0, x1, y1 = [float(v) for v in box]
        if not all(math.isfinite(v) for v in (x0, y0, x1, y1)) or x1 <= x0 or y1 <= y0: continue
        if x1 <= 0 or y1 <= 0 or x0 >= aw or y0 >= ah: continue
        x, y = max(0, int(x0 - PAD)), max(0, int(y0 - PAD))
        w = min(aw - x, max(24, int(x1 + PAD) - x))
        h = min(ah - y, max(14, int(y1 + PAD) - y))
        # Expand only into free space below this source, never relocate another
        # source rectangle. Leave adjacent controls at their original positions.
        bottom = ah
        for _, other, _, _ in blocks:
            ox0, oy0, ox1, oy1 = other
            overlap = min(x + w, ox1) - max(x, ox0)
            below = (oy0 + oy1) / 2 - (y0 + y1) / 2 > .4 * min(y1 - y0, oy1 - oy0)
            if below and oy0 > y + PAD and overlap > .2 * min(w, ox1 - ox0):
                bottom = min(bottom, int(oy0 - PAD))
        available = max(1, bottom - y)
        h = min(h, available)
        line_px = (y1 - y0) / max(1, nlines)                       # özgün satır yüksekliği → başlangıç puntosu
        start = min(max_pt, max(MIN_PT, line_px * px_to_pt * 0.75))   # satır aralığı ~1.3 em → kutu yüksekliğine denk
        # The renderer uses the same regular font and horizontal padding.
        pt, lines, need_h = fit(tr, w - 4, h, measure_at, start)
        if need_h > available:
            for pt in range(int(pt), 4, -1):
                meas, lh = measure_at(pt)
                lines = wrap(tr, max(1, w - 2 * PAD - 4), meas)
                need_h = math.ceil(len(lines) * lh * 1.05) + 2 * PAD
                if need_h <= available: break
        clipped = need_h > available
        if clipped:
            meas, lh = measure_at(pt)
            count = max(0, int((available - 2 * PAD) / (lh * 1.05)))
            lines = lines[:count]
            if lines:
                last = lines[-1]
                while last and meas(last + "…") > w - 2 * PAD - 4: last = last[:-1]
                lines[-1] = last + "…"
        need_h = min(ah - y, available, max(h, need_h))
        items.append({"x": int(x), "y": int(y), "w": int(w), "h": int(need_h), "pt": int(pt), "lines": lines,
                      "clipped": clipped, "source": (x0, y0, x1, y1),
                      "kind": "menu" if nlines <= 1 and len(en) < 40 else "text"})
    return sorted(items, key=lambda it: (it["y"], it["x"]))


def _unoverlap(items):
    """Uzayan kutu alttakini örterse alttakini aşağı kaydır (aynı sütunda)."""
    items.sort(key=lambda i: (i["y"], i["x"]))
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if b["x"] < a["x"] + a["w"] and a["x"] < b["x"] + b["w"] and a["y"] < b["y"] < a["y"] + a["h"]:
                b["y"] = a["y"] + a["h"] + 1
    return items


def norm(s):
    return re.sub(r"\W+", " ", str(s).lower()).strip()


# ---------------------------------------------------------------- çizim (Tk)
class InPlace:
    """Tek bir şeffaf Toplevel; kutular Canvas'ta. style: {"bg","fg","accent","border","alpha","font"}."""
    KEY = "#010203"                                       # şeffaf renk anahtarı

    def __init__(self, root, style, on_window=None, native_boxes=None):
        self.root, self.style, self.on_window = root, dict(style), on_window
        self.win = self.cv = None
        self._wins = []
        self._fonts = {}
        self.native_boxes = (os.name == "nt") if native_boxes is None else bool(native_boxes)

    def _font(self, pt, bold=False):
        import tkinter.font as tkfont
        k = (pt, bold)
        if k not in self._fonts:
            self._fonts[k] = tkfont.Font(root=self.root, family=self.style.get("font", "Segoe UI"), size=-int(round(pt / 0.75)),
                                         weight="bold" if bold else "normal")
        return self._fonts[k]

    def measure_at(self, pt):
        f = self._font(pt)
        return f.measure, f.metrics("linespace")

    def show(self, items, area):
        import tkinter as tk
        self.hide()
        s = self.style
        # A Tk Toplevel's default background is often black on Windows.  If
        # it differs from the transparent color key, the whole capture area
        # becomes a black rectangle even though the Canvas itself is keyed.
        # Set both surfaces explicitly before the first paint.
        items = [it for it in items if any(str(line).strip() for line in it.get("lines", []))]
        if not items:
            return None
        # Windows' colour-key transparency is not reliable when a game uses a
        # DX12/DWM composition surface: it can leave a black transparent
        # rectangle while Canvas text is absent.  Draw only the actual text
        # boxes as ordinary opaque windows instead; there is no transparent
        # parent surface that can turn black.
        if self.native_boxes:
            return self._show_native_boxes(tk, items, area)
        w = self.win = tk.Toplevel(self.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=self.KEY)
        try: w.attributes("-transparentcolor", self.KEY)
        except tk.TclError: pass                           # Windows dışı: arka plan görünür (testler)
        w.geometry(f"{area['width']}x{area['height']}{int(area['left']):+d}{int(area['top']):+d}")
        cv = self.cv = tk.Canvas(w, bg=self.KEY, highlightthickness=0, bd=0, width=area["width"], height=area["height"])
        cv.pack(fill="both", expand=True)
        for it in items:
            x, y, ww, hh = it["x"], it["y"], it["w"], it["h"]
            cv.create_rectangle(x, y, x + ww, y + hh, fill=s["bg"], outline=s.get("border", s["bg"]), width=1)
            cv.create_rectangle(x, y, x + 3, y + hh, fill=s["accent"] if it["kind"] == "text" else s.get("border", s["accent"]), width=0)
            f = self._font(it["pt"])
            lh = f.metrics("linespace") * 1.05
            ty = y + PAD
            for ln in it["lines"]:
                if s.get("outline"):
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        cv.create_text(x + PAD + 4 + dx, ty + dy, text=ln, anchor="nw", font=f, fill="#000000")
                cv.create_text(x + PAD + 4, ty, text=ln, anchor="nw", font=f, fill=s["fg"])
                ty += lh
        # Tk, özellikle oyun üstü saydam pencerelerde, ilk çizimi geciktirebilir.
        # İlk kareyi burada zorlayarak boş/siyah kaplama görülmesini önle.
        cv.update_idletasks()
        w.update_idletasks()
        if float(s.get("alpha", 1.0)) < 1.0:
            try: w.attributes("-alpha", float(s["alpha"]))
            except tk.TclError: pass
        if self.on_window: self.on_window(w)
        return w

    def _show_native_boxes(self, tk, items, area):
        s = self.style
        for it in items:
            lines = [str(line) for line in it.get("lines", []) if str(line).strip()]
            if not lines:
                continue
            # layout() measures with the Canvas font metrics.  Keep the
            # Windows-safe renderer on Canvas as well: a Frame/Label tree
            # adds its own requested height and padding, which can clip every
            # glyph inside narrow source rectangles (dark box, no text).
            ww, hh = max(24, int(it["w"])), max(14, int(it["h"]))
            w = tk.Toplevel(self.root)
            w.overrideredirect(True)
            w.attributes("-topmost", True)
            # app._lt_overlay_window uses this to keep the box click-through
            # without enabling WS_EX_LAYERED.  Layered Tk Canvas windows can
            # lose their text glyphs over some Windows/DX12 compositions.
            w._td2_native_box = True
            w.configure(bg=s["bg"])
            w.geometry(f"{ww}x{hh}{int(area['left'] + it['x']):+d}{int(area['top'] + it['y']):+d}")
            cv = tk.Canvas(w, bg=s["bg"], highlightthickness=0, bd=0, width=ww, height=hh)
            cv.pack(fill="both", expand=True)
            cv.create_rectangle(0, 0, ww, hh, fill=s["bg"], outline=s.get("border", s["bg"]), width=1)
            stripe = s["accent"] if it["kind"] == "text" else s.get("border", s["accent"])
            cv.create_rectangle(0, 0, 3, hh, fill=stripe, outline="")
            f = self._font(it["pt"])
            lh = f.metrics("linespace") * 1.05
            y = PAD
            for line in lines:
                cv.create_text(PAD + 4, y, text=line, fill=s["fg"], font=f, anchor="nw")
                y += lh
            w.update_idletasks()
            if self.on_window:
                self.on_window(w)
            self._wins.append(w)
        self.win = self._wins[0] if self._wins else None
        return self.win

    def hide(self):
        for w in list(self._wins) or ([self.win] if self.win is not None else []):
            try: w.destroy()
            except Exception: pass
        self._wins = []
        self.win = self.cv = None
