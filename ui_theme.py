"""
Görünüm ve arayüz sesleri / look & feel and UI sounds for TD2 Loot Advisor.

Harici kütüphane gerektirmez: Tk'nın yerleşik "clam" temasını kendi renk
paletimizle boyar. "dark" (varsayılan, SHD turuncusu), "light" ve eski
görünüm için "classic" modları vardır.
No third-party dependency: restyles Tk's built-in "clam" theme.

Sesler ilk açılışta küçük WAV dosyaları olarak üretilir (sounds/ klasörü) ve
Windows'ta winsound ile arka planda çalınır; diğer sistemlerde sessizdir.
"""
import math
import struct
import time
import wave
import tkinter as tk
from pathlib import Path
from tkinter import ttk

# ───────────── renk paletleri / palettes ─────────────
PALETTES = {
    "dark": {
        "bg": "#0f1116", "surface": "#171a21", "surface2": "#212530", "border": "#2c313d",
        "fg": "#e8eaef", "muted": "#8d95a5", "accent": "#ff6d10", "accent_hover": "#ff8a3d",
        "accent_fg": "#ffffff", "success": "#22c55e", "danger": "#ef4444", "warning": "#f5b82e",
        "info": "#4ea1ff", "select": "#4a2a12", "entry": "#0b0d11", "text_bg": "#0b0d11",
        "verdict": {"KEEP": "#15803d", "CONSIDER": "#b7791f", "DISMANTLE": "#c53030",
                    "REVIEW": "#2563eb", "ERROR": "#4b5263", "IDLE": "#1d2129"},
        "verdict_fg": {"KEEP": "#4ade80", "CONSIDER": "#facc15", "DISMANTLE": "#f87171",
                       "REVIEW": "#60a5fa", "ERROR": "#9ca3af", "IDLE": "#8d95a5"},
    },
    "light": {
        "bg": "#f2f3f6", "surface": "#ffffff", "surface2": "#e6e8ed", "border": "#d3d7df",
        "fg": "#1a1e26", "muted": "#687082", "accent": "#e35d00", "accent_hover": "#ff7a1f",
        "accent_fg": "#ffffff", "success": "#15803d", "danger": "#c53030", "warning": "#a16207",
        "info": "#1d4ed8", "select": "#ffe1c7", "entry": "#ffffff", "text_bg": "#ffffff",
        "verdict": {"KEEP": "#16a34a", "CONSIDER": "#ca8a04", "DISMANTLE": "#dc2626",
                    "REVIEW": "#2563eb", "ERROR": "#6b7280", "IDLE": "#3a3f4b"},
        "verdict_fg": {"KEEP": "#15803d", "CONSIDER": "#a16207", "DISMANTLE": "#c53030",
                       "REVIEW": "#1d4ed8", "ERROR": "#6b7280", "IDLE": "#687082"},
    },
    # Eski (v5 öncesi) görünüm: renkler önceki sürümle aynı.
    "classic": {
        "bg": "#dcdad5", "surface": "#ffffff", "surface2": "#dcdad5", "border": "#cccccc",
        "fg": "#000000", "muted": "#888888", "accent": "#1f6fb2", "accent_hover": "#1f6fb2",
        "accent_fg": "#ffffff", "success": "#1f8f3a", "danger": "#a82424", "warning": "#b8860b",
        "info": "#1f6fb2", "select": "#4a6984", "entry": "#ffffff", "text_bg": "#ffffff",
        "verdict": {"KEEP": "#1f8f3a", "CONSIDER": "#b8860b", "DISMANTLE": "#a82424",
                    "REVIEW": "#2a5db0", "ERROR": "#555555", "IDLE": "#333333"},
        "verdict_fg": {"KEEP": "#1f8f3a", "CONSIDER": "#b8860b", "DISMANTLE": "#a82424",
                       "REVIEW": "#2a5db0", "ERROR": "#555555", "IDLE": "#333333"},
    },
}
THEME_MODES = ("dark", "light", "classic")

FONT = "Segoe UI"
FONT_SEMI = "Segoe UI Semibold"

# Sekme ikonları (sekme kimliğine göre) / tab icons by tab id
TAB_ICONS = {"dash": "🎯", "builds": "🧩", "progress": "📦", "stash": "🗄", "stats": "📊", "info": "📚", "tasks": "📋",
             "assistant": "🤖", "settings": "⚙", "history": "🕘", "log": "📜", "help": "❓"}


def with_icon(text, icon):
    """Metin zaten bir sembolle başlıyorsa olduğu gibi bırakır, yoksa ikonu ekler."""
    if not text or not icon:
        return text
    return text if not text[0].isalnum() else f"{icon} {text}"


def apply(root, mode="dark"):
    """Temayı uygular ve kullanılan paleti (sözlük) döndürür."""
    mode = mode if mode in PALETTES else "dark"
    p = dict(PALETTES[mode], mode=mode)
    s = ttk.Style(root)
    root.option_clear()                    # önceki temanın tk ayarlarını temizle (anlık tema değişimi)
    if mode == "classic":
        s.theme_use("clam")                # saf clam = eski görünüm
        root.configure(bg=p["bg"])
        return p
    # Her mod kendi ttk temasında tutulur; böylece temalar arasında geçiş temiz olur.
    name = f"td2-{mode}"
    if name not in s.theme_names():
        s.theme_create(name, parent="clam")
    s.theme_use(name)

    bg, sf, sf2, bd, fg, mu = p["bg"], p["surface"], p["surface2"], p["border"], p["fg"], p["muted"]
    ac, ach, ent = p["accent"], p["accent_hover"], p["entry"]
    base = (FONT, 10)

    root.configure(bg=bg)
    s.configure(".", background=bg, foreground=fg, fieldbackground=ent, bordercolor=bd,
                lightcolor=sf2, darkcolor=sf2, troughcolor=sf2, focuscolor=ac,
                selectbackground=ac, selectforeground=p["accent_fg"], insertcolor=fg,
                arrowcolor=fg, font=base)

    # çerçeveler ve yazılar
    s.configure("TFrame", background=bg)
    s.configure("Card.TFrame", background=sf)
    s.configure("Header.TFrame", background=sf)
    s.configure("TLabel", background=bg, foreground=fg)
    s.configure("Muted.TLabel", background=bg, foreground=mu)
    s.configure("Card.TLabel", background=sf, foreground=fg)
    s.configure("CardMuted.TLabel", background=sf, foreground=mu)
    s.configure("Brand.TLabel", background=sf, foreground=ac, font=(FONT_SEMI, 15))
    s.configure("Item.TLabel", background=sf, foreground=fg, font=(FONT_SEMI, 13))
    s.configure("Note.TLabel", background=sf, foreground=p["info"], font=(FONT_SEMI, 10))
    s.configure("Chip.TLabel", background=sf2, foreground=mu, padding=(10, 3), font=(FONT_SEMI, 9))
    s.configure("ChipOn.TLabel", background=p["success"], foreground="#ffffff", padding=(10, 3), font=(FONT_SEMI, 9))
    s.configure("Warn.TLabel", background=bg, foreground=p["warning"])
    s.configure("Section.TLabel", background=bg, foreground=fg, font=(FONT_SEMI, 11))
    s.configure("TSeparator", background=bd)

    # butonlar
    s.configure("TButton", background=sf2, foreground=fg, bordercolor=bd, lightcolor=sf2,
                darkcolor=sf2, padding=(14, 7), relief="flat", focusthickness=0, font=(FONT_SEMI, 10))
    s.map("TButton", background=[("disabled", sf), ("pressed", bd), ("active", bd)],
          foreground=[("disabled", mu)], bordercolor=[("active", ac), ("focus", ac)],
          lightcolor=[("pressed", bd), ("active", bd)], darkcolor=[("pressed", bd), ("active", bd)])
    for name, col, hov in (("Accent", ac, ach), ("Success", p["success"], p["success"]),
                           ("Danger", p["danger"], p["danger"])):
        s.configure(f"{name}.TButton", background=col, foreground="#ffffff", bordercolor=col,
                    lightcolor=col, darkcolor=col, padding=(16, 7), font=(FONT_SEMI, 10))
        s.map(f"{name}.TButton", background=[("pressed", hov), ("active", hov)],
              lightcolor=[("active", hov)], darkcolor=[("active", hov)],
              bordercolor=[("active", "#ffffff"), ("focus", col)])

    # sekmeler
    s.configure("TNotebook", background=bg, borderwidth=1, tabmargins=(6, 6, 6, 0),
                bordercolor=bd, lightcolor=bd, darkcolor=bd)
    s.configure("TNotebook.Tab", background=bg, foreground=mu, padding=(11, 7), bordercolor=bg,
                lightcolor=bg, darkcolor=bg, font=(FONT_SEMI, 10))
    s.map("TNotebook.Tab", background=[("selected", sf), ("active", sf2)],
          foreground=[("selected", ac), ("active", fg)],
          lightcolor=[("selected", ac)], bordercolor=[("selected", bd)])

    # gruplar
    s.configure("TLabelframe", background=bg, bordercolor=bd, lightcolor=bd, darkcolor=bd, relief="solid")
    s.configure("TLabelframe.Label", background=bg, foreground=ac, font=(FONT_SEMI, 10))

    # giriş alanları
    s.configure("TEntry", fieldbackground=ent, foreground=fg, bordercolor=bd, lightcolor=ent,
                darkcolor=ent, insertcolor=fg, padding=5)
    s.map("TEntry", bordercolor=[("focus", ac)], lightcolor=[("focus", ac)])
    s.configure("TCombobox", fieldbackground=ent, background=sf2, foreground=fg, arrowcolor=fg,
                bordercolor=bd, lightcolor=ent, darkcolor=ent, padding=4)
    s.map("TCombobox", fieldbackground=[("readonly", ent)], foreground=[("readonly", fg)],
          selectbackground=[("readonly", ent)], selectforeground=[("readonly", fg)],
          bordercolor=[("focus", ac), ("active", ac)], background=[("active", bd)])
    root.option_add("*TCombobox*Listbox.background", sf)
    root.option_add("*TCombobox*Listbox.foreground", fg)
    root.option_add("*TCombobox*Listbox.selectBackground", ac)
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
    root.option_add("*TCombobox*Listbox.font", base)

    # onay kutuları / seçenekler
    for w in ("TCheckbutton", "TRadiobutton"):
        s.configure(w, background=bg, foreground=fg, indicatorbackground=ent,
                    indicatorforeground=ac, upperbordercolor=bd, lowerbordercolor=bd)
        s.map(w, background=[("active", bg)], foreground=[("active", ac)],
              indicatorbackground=[("selected", ac), ("active", sf2)],
              indicatorforeground=[("selected", "#ffffff")])

    # tablolar
    s.configure("Treeview", background=sf, fieldbackground=sf, foreground=fg, bordercolor=bd,
                lightcolor=sf, darkcolor=sf, rowheight=26)
    s.map("Treeview", background=[("selected", p["select"])], foreground=[("selected", fg)])
    s.configure("Treeview.Heading", background=sf2, foreground=mu, bordercolor=bd, lightcolor=sf2,
                darkcolor=sf2, relief="flat", padding=(8, 6), font=(FONT_SEMI, 9))
    s.map("Treeview.Heading", background=[("active", bd)], foreground=[("active", fg)])

    # ilerleme çubuğu ve kaydırma çubukları
    s.configure("TProgressbar", background=ac, troughcolor=sf2, bordercolor=sf2,
                lightcolor=ac, darkcolor=ac, thickness=12)
    for orient in ("Vertical", "Horizontal"):
        s.configure(f"{orient}.TScrollbar", background=sf2, troughcolor=bg, bordercolor=bg,
                    arrowcolor=mu, lightcolor=sf2, darkcolor=sf2, gripcount=0)
        s.map(f"{orient}.TScrollbar", background=[("active", bd)])

    # klasik tk bileşenleri (Text, Listbox, Canvas)
    for cls in ("Text", "Listbox"):
        root.option_add(f"*{cls}.background", p["text_bg"])
        root.option_add(f"*{cls}.foreground", fg)
        root.option_add(f"*{cls}.selectBackground", ac)
        root.option_add(f"*{cls}.selectForeground", "#ffffff")
        root.option_add(f"*{cls}.relief", "flat")
        root.option_add(f"*{cls}.borderWidth", 0)
        root.option_add(f"*{cls}.highlightThickness", 1)
        root.option_add(f"*{cls}.highlightBackground", bd)
        root.option_add(f"*{cls}.highlightColor", ac)
        root.option_add(f"*{cls}.font", base)
    root.option_add("*Text.insertBackground", fg)
    root.option_add("*Text.padX", 10)
    root.option_add("*Text.padY", 8)
    root.option_add("*Listbox.activeStyle", "none")
    root.option_add("*Canvas.background", sf)
    root.option_add("*Canvas.highlightThickness", 0)
    root.option_add("*Toplevel.background", bg)
    return p


# ───────────── arayüz sesleri / UI sounds ─────────────
SOUND_VERSION = 1
_RATE = 22050


def _tone(parts, volume=0.35):
    """parts: [(frekans_hz_baş, frekans_hz_son, süre_sn), ...] → 16-bit mono örnekler."""
    out = []
    for f0, f1, dur in parts:
        n = max(1, int(_RATE * dur))
        phase = 0.0
        for i in range(n):
            f = f0 + (f1 - f0) * i / n
            phase += 2 * math.pi * f / _RATE
            att = min(1.0, i / (_RATE * 0.004))          # 4 ms yumuşak başlangıç
            rel = min(1.0, (n - i) / (_RATE * 0.012))    # 12 ms yumuşak bitiş
            env = att * rel * (1 - 0.35 * i / n)
            # biraz harmonik: daha "dolgun" ve dijital bir tık sesi
            v = math.sin(phase) * 0.8 + math.sin(2 * phase) * 0.2
            out.append(int(max(-1, min(1, v * env * volume)) * 32767))
    return out


SOUND_SPECS = {
    "click":     ([(2100, 1500, 0.028)], 0.22),
    "tab":       ([(1300, 1700, 0.035)], 0.16),
    "toggle":    ([(1600, 1600, 0.020), (2300, 2300, 0.020)], 0.18),
    "start":     ([(660, 660, 0.06), (990, 990, 0.09)], 0.30),
    "stop":      ([(990, 990, 0.06), (560, 560, 0.10)], 0.30),
    "KEEP":      ([(880, 880, 0.07), (1320, 1320, 0.11)], 0.38),
    "CONSIDER":  ([(880, 880, 0.10)], 0.32),
    "DISMANTLE": ([(420, 300, 0.16)], 0.40),
    "REVIEW":    ([(1180, 1180, 0.07), (0, 0, 0.04), (1180, 1180, 0.07)], 0.34),
    "ERROR":     ([(220, 200, 0.20)], 0.38),
}


class Sounds:
    """Kısa arayüz sesleri. Windows dışında sessizce hiçbir şey yapmaz."""

    def __init__(self, folder, enabled=True):
        self.folder = Path(folder)
        self.enabled = enabled
        self._last = 0.0
        self.ok = False
        try:
            import winsound  # noqa: F401  (sadece Windows)
            self._ensure_files()
            self.ok = True
        except Exception:
            self.ok = False

    def _ensure_files(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        stamp = self.folder / f".v{SOUND_VERSION}"
        for name, (parts, vol) in SOUND_SPECS.items():
            path = self.folder / f"{name}.wav"
            if path.exists() and stamp.exists():
                continue
            with wave.open(str(path), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(_RATE)
                w.writeframes(b"".join(struct.pack("<h", s) for s in _tone(parts, vol)))
        stamp.touch()

    def play(self, name, force=False):
        """Sesi arka planda çalar. Çok sık tıklamalarda (40 ms) tekrar etmez."""
        if not self.ok or (not self.enabled and not force):
            return
        now = time.monotonic()
        if now - self._last < 0.04:
            return
        self._last = now
        path = self.folder / f"{name}.wav"
        if not path.exists():
            return
        try:
            import winsound
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception:
            pass


def bind_click_sounds(root, sounds):
    """Tüm buton, onay kutusu, seçenek ve açılır listelere tık sesi bağlar."""
    def click(_e=None):
        sounds.play("click")
    def toggle(_e=None):
        sounds.play("toggle")
    root.bind_class("TButton", "<Button-1>", click, add="+")
    root.bind_class("TCheckbutton", "<Button-1>", toggle, add="+")
    root.bind_class("TRadiobutton", "<Button-1>", toggle, add="+")
    root.bind_class("TCombobox", "<<ComboboxSelected>>", toggle, add="+")


def scrollable(parent, bg):
    """Dikey kaydırılabilir bir alan oluşturur ve içine yerleştirilecek çerçeveyi döndürür.
    Fare tekerleği; metin kutusu, liste ve tablo dışındaki her yerde sayfayı kaydırır."""
    canvas = tk.Canvas(parent, highlightthickness=0, bd=0, bg=bg)
    sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas)
    win = canvas.create_window((0, 0), window=inner, anchor="nw")
    # e=None: arayüz yeniden kurulurken Tk eski bir komut adını argümansız çağırabiliyor (zararsız, yok sayılır)
    inner.bind("<Configure>", lambda e=None: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e=None: canvas.itemconfigure(win, width=e.width) if e is not None else None)
    canvas.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    def wheel(e):
        if e.widget.winfo_class() in ("Text", "Listbox", "Treeview", "TCombobox"):
            return
        if canvas.winfo_height() >= inner.winfo_reqheight():
            return
        step = -1 if (getattr(e, "delta", 0) > 0 or getattr(e, "num", 0) == 4) else 1
        canvas.yview_scroll(step * 3, "units")

    def enter(_e):
        canvas.bind_all("<MouseWheel>", wheel)
        canvas.bind_all("<Button-4>", wheel)
        canvas.bind_all("<Button-5>", wheel)

    def leave(_e):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", enter)
    canvas.bind("<Leave>", leave)
    return inner
