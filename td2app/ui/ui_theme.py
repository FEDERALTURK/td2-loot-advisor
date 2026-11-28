"""
Görünüm ve arayüz sesleri / look & feel and UI sounds for TD2 Loot Advisor.

Harici kütüphane gerektirmez: Tk'nın yerleşik "clam" temasını kendi renk
paletimizle boyar. Kullanıcı üç yerleşik görünüm arasından seçim yapabilir;
eski "default" ayarı geriye dönük uyumluluk için SHD temasına eşlenir.
No third-party dependency: restyles Tk's built-in "clam" theme.

Sesler ilk açılışta küçük WAV dosyaları olarak üretilir (sounds/ klasörü) ve
Windows'ta winsound ile arka planda çalınır; diğer sistemlerde sessizdir.
"""
import math
import struct
import time
import wave
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import ttk

def luminance(hexcol):
    """Göreli parlaklık (WCAG)."""
    h = hexcol.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def on_color(bg):
    """Renkli zemin üstünde okunur yazı rengi (beyaz ya da koyu)."""
    return "#ffffff" if contrast(bg, "#ffffff") >= contrast(bg, "#0b0d11") else "#0b0d11"


# ───────────── renk paleti / palette ─────────────
# Yerleşik görünüm kimlikleri. Renkler yalnızca bu modülden uygulanır; uygulama
# içindeki widget'lar ortak PAL sözlüğünü kullanmaya devam eder.
PALETTES = {
    "shd_tactical": {
        # SHD operasyon konsolu: neredeyse siyah lacivert zemin, tek turuncu
        # sinyal rengi ve soğuk camgöbeği veri vurgusu. Division 2 HUD'unun
        # "karanlık + tek sıcak vurgu" dilini korur; semantik renkler yalnız
        # durum bildirir.
        "bg": "#070b10", "surface": "#0c141c", "surface2": "#121d27", "border": "#23323f",
        "fg": "#eef4f8", "muted": "#8fa4b6", "accent": "#ff6a1a", "accent_hover": "#ff8c47",
        "accent_fg": on_color("#ff6a1a"), "success": "#5ad98c", "danger": "#ff5d6c", "warning": "#ffc24d",
        "info": "#4cc9e0", "select": "#3a2412", "entry": "#05080c", "text_bg": "#05080c",
        "ov_bg": "#0b131b", "ov_fg": "#f5f9fc", "ov_border": "#b3752f",
        "verdict": {"KEEP": "#155c3d", "CONSIDER": "#7a4f12", "DISMANTLE": "#7c2730",
                    "REVIEW": "#1d4f78", "ERROR": "#3f4a55", "IDLE": "#1c2733"},
        "verdict_fg": {"KEEP": "#5ad98c", "CONSIDER": "#ffc24d", "DISMANTLE": "#ff7b86",
                       "REVIEW": "#6cc3ff", "ERROR": "#9aa8b5", "IDLE": "#8fa4b6"},
        # SHD HUD'un ince çizgi / kesik köşe dili için ek belirteçler.
        "line": "#2f4252", "line_strong": "#4a6579", "signal": "#4cc9e0",
        "panel_glass": "#0a1118", "shadow": "#04070a",
    },
    "kaivolt": {
        "bg": "#11111c", "surface": "#1a1b2b", "surface2": "#25243a", "border": "#403d61",
        "fg": "#eeeffa", "muted": "#aaa8c3", "accent": "#b69ae8", "accent_hover": "#d0baf5",
        "accent_fg": on_color("#b69ae8"), "success": "#7bcf9b", "danger": "#ed7c92", "warning": "#e8c477",
        "info": "#83b8e9", "select": "#39334f", "entry": "#0c0c15", "text_bg": "#0c0c15",
        "ov_bg": "#151521", "ov_fg": "#f8f7ff", "ov_border": "#8d72c9",
        "verdict": {"KEEP": "#176b45", "CONSIDER": "#8b5a16", "DISMANTLE": "#8f2d35",
                    "REVIEW": "#245a9b", "ERROR": "#4b5563", "IDLE": "#26313d"},
        "verdict_fg": {"KEEP": "#4ade80", "CONSIDER": "#ffd166", "DISMANTLE": "#ff7b8d",
                       "REVIEW": "#72b7ff", "ERROR": "#b4b8c8", "IDLE": "#a59ac6"},
    },
    "clean_console": {
        "bg": "#0f171b", "surface": "#17242a", "surface2": "#20343b", "border": "#38545d",
        "fg": "#e9f5f4", "muted": "#9ab5b8", "accent": "#63c9c4", "accent_hover": "#91e5df",
        "accent_fg": on_color("#63c9c4"), "success": "#7bce96", "danger": "#eb7f7f", "warning": "#edc878",
        "info": "#78b9d7", "select": "#25484b", "entry": "#0b1215", "text_bg": "#0b1215",
        "ov_bg": "#112025", "ov_fg": "#f4fbfa", "ov_border": "#4d9d9a",
        "verdict": {"KEEP": "#176b45", "CONSIDER": "#8b5a16", "DISMANTLE": "#8f2d35",
                    "REVIEW": "#245a9b", "ERROR": "#4b5563", "IDLE": "#26313d"},
        "verdict_fg": {"KEEP": "#4ade80", "CONSIDER": "#f4c95d", "DISMANTLE": "#ff8585",
                       "REVIEW": "#64b5f6", "ERROR": "#b2c0c6", "IDLE": "#9ab0b8"},
    },
    "ctk_midnight": {
        "bg": "#0d0f14", "surface": "#161a21", "surface2": "#1e2530", "border": "#2d3848",
        "fg": "#dce4ee", "muted": "#8e98a8", "accent": "#1f6aa5", "accent_hover": "#2980c4",
        "accent_fg": on_color("#1f6aa5"), "success": "#2fa572", "danger": "#e85d5d", "warning": "#eca607",
        "info": "#4a9ede", "select": "#162d4a", "entry": "#0a0c10", "text_bg": "#0a0c10",
        "ov_bg": "#0e1118", "ov_fg": "#ffffff", "ov_border": "#1f6aa5",
        "verdict": {"KEEP": "#146040", "CONSIDER": "#8a6010", "DISMANTLE": "#8c2832",
                    "REVIEW": "#1f538d", "ERROR": "#4a4d50", "IDLE": "#252830"},
        "verdict_fg": {"KEEP": "#2fa572", "CONSIDER": "#eca607", "DISMANTLE": "#e85d5d",
                       "REVIEW": "#4a9ede", "ERROR": "#949a9f", "IDLE": "#8e98a8"},
    },
}

# Eski sürümlerde bulunan tema/paket seçenekleri. Ortak karar renkleri SHD
# tabanından gelir; her paket kendi arka plan, vurgu ve overlay renklerini taşır.
_LEGACY_PACKS = {
    "dark": {"bg": "#0f1116", "surface": "#171a21", "surface2": "#212530", "border": "#2c313d", "fg": "#e8eaef", "muted": "#8d95a5", "accent": "#ff6d10", "accent_hover": "#ff8a3d", "select": "#4a2a12", "entry": "#0b0d11", "text_bg": "#0b0d11", "ov_bg": "#111318", "ov_fg": "#ffffff", "ov_border": "#5a3417"},
    "light": {"bg": "#f2f3f6", "surface": "#ffffff", "surface2": "#e6e8ed", "border": "#d3d7df", "fg": "#1a1e26", "muted": "#687082", "accent": "#e35d00", "accent_hover": "#ff7a1f", "select": "#ffe1c7", "entry": "#ffffff", "text_bg": "#ffffff", "ov_bg": "#14161b", "ov_fg": "#ffffff", "ov_border": "#5a3417"},
    "classic": {"bg": "#dcdad5", "surface": "#ffffff", "surface2": "#dcdad5", "border": "#cccccc", "fg": "#1a1e26", "muted": "#687082", "accent": "#1f6fb2", "accent_hover": "#1f6fb2", "select": "#4a6984", "entry": "#ffffff", "text_bg": "#ffffff", "ov_bg": "#101010", "ov_fg": "#ffffff", "ov_border": "#1f6fb2"},
    "darkzone": {"bg": "#0e0b14", "surface": "#17121f", "surface2": "#221a2e", "border": "#33274a", "fg": "#ece8f4", "muted": "#9a8fb0", "accent": "#a855f7", "accent_hover": "#c084fc", "select": "#3b1f5c", "entry": "#0a0810", "ov_bg": "#140f1d", "ov_fg": "#f3eefe", "ov_border": "#5b3a8a"},
    "blacktusk": {"bg": "#0b0c0e", "surface": "#141619", "surface2": "#1d2024", "border": "#2e3238", "fg": "#e9ebee", "muted": "#8a9099", "accent": "#e11d2e", "accent_hover": "#f43f4e", "select": "#4a1016", "entry": "#08090a", "ov_bg": "#121417", "ov_fg": "#ffffff", "ov_border": "#5c1a20"},
    "hunter": {"bg": "#100e0d", "surface": "#1a1715", "surface2": "#25211e", "border": "#3a332d", "fg": "#eee7df", "muted": "#a39788", "accent": "#dd4560", "accent_hover": "#ec6178", "select": "#4c1520", "entry": "#0b0a09", "ov_bg": "#171412", "ov_fg": "#f6efe6", "ov_border": "#6a2a34"},
    "winter_ny": {"bg": "#0d1317", "surface": "#141c22", "surface2": "#1c2830", "border": "#2b3a45", "fg": "#f2f6f8", "muted": "#93a5b1", "accent": "#ff7a1a", "accent_hover": "#ff9447", "select": "#4a2a12", "entry": "#091014", "ov_bg": "#111a20", "ov_fg": "#ffffff", "ov_border": "#3b5363"},
    "nightops": {"bg": "#080d18", "surface": "#0e1626", "surface2": "#152036", "border": "#22324f", "fg": "#e6f1ff", "muted": "#8aa0bf", "accent": "#22d3ee", "accent_hover": "#67e8f9", "select": "#0f3a4a", "entry": "#060a12", "ov_bg": "#0b1322", "ov_fg": "#eaf7ff", "ov_border": "#1f6b80"},
    "kenly": {"bg": "#0b110d", "surface": "#121a15", "surface2": "#1a251e", "border": "#2a3a2f", "fg": "#e7f2ea", "muted": "#8fa597", "accent": "#4ade80", "accent_hover": "#86efac", "select": "#173d26", "entry": "#080d0a", "ov_bg": "#101812", "ov_fg": "#f0fbf3", "ov_border": "#2f6b45"},
    "isac": {"bg": "#0a1720", "surface": "#102430", "surface2": "#18313d", "border": "#294b58", "fg": "#e8f5f6", "muted": "#94adb4", "accent": "#56d8df", "accent_hover": "#88e9ee", "select": "#173a45", "entry": "#09151d", "ov_bg": "#0b1c26", "ov_fg": "#effdff", "ov_border": "#347687"},
    "tactical": {"bg": "#111619", "surface": "#1a2225", "surface2": "#263135", "border": "#354348", "fg": "#edf2ef", "muted": "#9baaaa", "accent": "#b5c6aa", "accent_hover": "#d1dfc9", "select": "#39483c", "entry": "#0c1113", "ov_bg": "#11191c", "ov_fg": "#f3f7f3", "ov_border": "#899d7d"},
    "rogue_signal": {"bg": "#120b15", "surface": "#211421", "surface2": "#30192c", "border": "#56304f", "fg": "#f6eaf5", "muted": "#b99ab5", "accent": "#f04b9c", "accent_hover": "#ff86c4", "select": "#512344", "entry": "#0c0710", "ov_bg": "#180d1c", "ov_fg": "#fff2fa", "ov_border": "#a33d80"},
    "isac_operations": {"bg": "#071722", "surface": "#0b2130", "surface2": "#123247", "border": "#1b5d72", "fg": "#e5fbff", "muted": "#8eb6c0", "accent": "#39d7ef", "accent_hover": "#8df4ff", "select": "#113d4e", "entry": "#06131d", "ov_bg": "#071d2a", "ov_fg": "#eaffff", "ov_border": "#25a4bb"},
    "darkzone_rogue": {"bg": "#170b0d", "surface": "#241215", "surface2": "#35191d", "border": "#713333", "fg": "#fff0ed", "muted": "#d0a29c", "accent": "#ff4d3d", "accent_hover": "#ff897d", "select": "#572120", "entry": "#100708", "ov_bg": "#210d10", "ov_fg": "#fff4f1", "ov_border": "#bf3b32"},
    "field_terminal": {"bg": "#171913", "surface": "#20241a", "surface2": "#303627", "border": "#58614a", "fg": "#f0f1df", "muted": "#b0b49b", "accent": "#d8c46b", "accent_hover": "#eee19a", "select": "#4c5231", "entry": "#11130f", "ov_bg": "#1b1e15", "ov_fg": "#fbfbe9", "ov_border": "#858c5d"},
    "shd_terminal": {"bg": "#0b0e14", "surface": "#111720", "surface2": "#18212c", "border": "#34404c", "fg": "#ffffff", "muted": "#a0aab2", "accent": "#ff5a00", "accent_hover": "#ff7b38", "select": "#54250d", "entry": "#080b10", "ov_bg": "#0d121a", "ov_fg": "#ffffff", "ov_border": "#ff5a00", "info": "#00e5ff"},
}
for _name, _overrides in _LEGACY_PACKS.items():
    PALETTES[_name] = {**PALETTES["shd_tactical"], **_overrides}
    PALETTES[_name]["accent_fg"] = on_color(PALETTES[_name]["accent"])

# One semantic status contract is shared by every selectable theme.  Screens
# should pair these colors with a text label or glyph; color is never the only
# signal for a decision such as KEEP, REVIEW or an error.
for _palette in PALETTES.values():
    _palette.setdefault("status", {
        "ready": _palette["info"], "active": _palette["accent"],
        "success": _palette["success"], "warning": _palette["warning"],
        "danger": _palette["danger"], "muted": _palette["muted"],
    })

PALETTES["default"] = PALETTES["shd_tactical"]  # eski ayar dosyaları için alias
PALETTES["field_clean"] = PALETTES["clean_console"]  # eski Field Clean seçimi için alias
PACKS = tuple(_LEGACY_PACKS)
THEME_MODES = ("shd_tactical", "kaivolt", "clean_console", "ctk_midnight") + PACKS + ("default", "field_clean")
THEME_LABELS = {
    "shd_tactical": "SHD Tactical HUD",
    "kaivolt": "Kaivolt Night Operations",
    "clean_console": "Clean Tactical Console",
    "ctk_midnight": "CTK Midnight Blue",
    "field_clean": "Field Clean",
    "dark": "Dark (SHD Orange)", "light": "Light", "classic": "Classic",
    "darkzone": "Dark Zone", "blacktusk": "Black Tusk", "hunter": "Hunter",
    "winter_ny": "Winter New York", "nightops": "Night Operations", "kenly": "Kenly",
    "isac": "ISAC", "tactical": "Tactical", "rogue_signal": "Rogue Signal",
    "isac_operations": "ISAC Operations", "darkzone_rogue": "Dark Zone Rogue",
    "field_terminal": "SHD Field Terminal", "shd_terminal": "SHD Terminal",
}


def canonical_mode(mode):
    """Eski kayıtları yeni üçlü tema seçimine güvenli biçimde eşleştirir."""
    return "shd_tactical" if mode == "default" else mode if mode in THEME_LABELS else "shd_tactical"


def apply_pack(settings, mode):
    """Apply one of the selectable appearance presets to persisted settings."""
    if mode not in THEME_MODES:
        return False
    mode = canonical_mode(mode)
    accent = PALETTES[mode]["accent"]
    settings["ui_theme"] = mode
    # Keep the pointer and trail coordinated with the palette's accent.
    settings["fx_cursor_color"] = accent
    settings["fx_trail_color"] = accent
    settings.update({"event_fx": "standard", "fx_bgwatch": False, "fx_transition_ms": 180,
                     "fx_transition_style": "tactical", "ui_nav_layout": "tactical", "ui_layout": "standard"})
    if mode == "isac_operations":
        settings.update({"event_fx": "isac", "fx_bgwatch": True, "fx_bgwatch_dim": 0.08,
                         "fx_transition_ms": 320, "fx_trail_len": 22})
    elif mode == "darkzone_rogue":
        settings.update({"event_fx": "rogue", "fx_bgwatch": True, "fx_bgwatch_dim": 0.12,
                         "fx_transition_ms": 340, "fx_trail_len": 24})
    elif mode == "field_terminal":
        settings.update({"event_fx": "field", "fx_bgwatch": True, "fx_bgwatch_dim": 0.10,
                         "fx_transition_ms": 220, "fx_trail_len": 12, "ui_layout": "field_command"})
    elif mode == "shd_terminal":
        settings.update({"fx_transition_ms": 240, "fx_transition_style": "tactical", "ui_layout": "shd_terminal"})
    elif mode == "kaivolt":
        settings.update({"fx_transition_ms": 220, "fx_transition_style": "soft", "ui_nav_layout": "flat"})
    return True

# Font aileleri rol bazında seçilir. Tk masaüstünde web fontu indirilmediği için
# çözümleyici yalnızca işletim sistemine kurulu aileleri kullanır; böylece
# çevrimdışı/local-first çalışma ve Türkçe fallback davranışı korunur.
FONT = "Inter"
FONT_SEMI = "Chakra Petch"
FONT_DISPLAY = "Chakra Petch"
FONT_MONO = "JetBrains Mono"
FONT_FALLBACKS = {
    "body": ("Inter", "IBM Plex Sans", "Segoe UI", "Arial", "sans-serif"),
    "display": ("Chakra Petch", "Segoe UI Semibold", "Segoe UI", "Arial", "sans-serif"),
    "mono": ("JetBrains Mono", "Consolas", "Cascadia Mono", "Courier New", "monospace"),
}


def _resolve_font(root, candidates):
    """Return the first installed family; Tk handles Latin Extended glyphs."""
    try:
        installed = {str(name).casefold() for name in tkfont.families(root)}
    except (tk.TclError, RuntimeError, AttributeError):
        installed = set()
    for family in candidates:
        if family.casefold() in installed:
            return family
    # If Tk cannot expose its family list (for example a headless test), use a
    # concrete family rather than a CSS-only generic name. On Windows the
    # resolver normally returns one of the preferred families above.
    return candidates[-2]


def resolve_fonts(root):
    """Resolve the hybrid type roles without downloading or mutating fonts."""
    global FONT, FONT_SEMI, FONT_DISPLAY, FONT_MONO
    FONT = _resolve_font(root, FONT_FALLBACKS["body"])
    FONT_SEMI = _resolve_font(root, FONT_FALLBACKS["display"])
    FONT_DISPLAY = FONT_SEMI
    FONT_MONO = _resolve_font(root, FONT_FALLBACKS["mono"])
    return {"body": FONT, "display": FONT_DISPLAY, "mono": FONT_MONO}


def font_spec(role="body", size=None, weight=None, *, numeric=False):
    """Return a Tk font tuple for the shared desktop typography contract.

    Tk has no CSS ``font-variant-numeric`` or ``letter-spacing`` properties.
    Numeric content therefore opts into the mono role for stable glyph widths,
    while display/label roles use the tactical family and weight requested by
    the caller. The returned tuple is accepted by Label, Text and Canvas.
    """
    role = "mono" if numeric else str(role or "body").lower()
    family = {"body": FONT, "display": FONT_DISPLAY, "mono": FONT_MONO}.get(role, FONT)
    px = int(size or DESIGN_TOKENS["type"].get(role, DESIGN_TOKENS["type"]["body"]))
    if weight is None:
        weight = "bold" if role == "display" else "normal"
    return (family, max(1, px), str(weight))


def label_text(text):
    """Format short tactical labels without forcing body copy to uppercase."""
    return str(text or "").upper()


# Central desktop design system. Tk's native widgets cannot render arbitrary
# rounded corners consistently across Windows themes, so borders stay crisp;
# these tokens define the shared rhythm and hierarchy instead of per-screen
# magic numbers.
DESIGN_TOKENS = {
    "spacing": {"xxs": 2, "xs": 4, "sm": 8, "md": 12, "lg": 18,
                 "xl": 24, "xxl": 32},
    # SHD HUD tipografisi: büyük, harf aralıklı başlıklar; 12 px gövde;
    # 10 px monospace meta etiketler.
    "type": {"meta": 10, "caption": 11, "small": 12, "body": 13,
             "control": 12, "section": 18, "page": 28, "display": 36,
             "body_line_height": 1.5, "label_tracking": 0.10},
    "font": {"body": "Inter", "display": "Chakra Petch", "mono": "JetBrains Mono",
             "latin_subset": "latin-ext", "fallback_policy": "installed-family"},
    "control": {"height": 38, "height_large": 46, "min_width": 112},
    # Keskin köşeler ve ince çizgiler: HUD panelleri yuvarlatılmaz.
    "border": {"hairline": 1, "focus": 2, "card_radius": 2, "control_radius": 2},
    "layout": {"page_padding": 20, "card_gap": 12, "content_max_width": 1500},
    # Geniş ekranda nefes alan komuta kabuğu, dar ekranda kompakt ölçü.
    "shell": {"nav_width": 250, "nav_compact_width": 196, "workspace_gap": 12},
    "focus": {"ring_width": 2, "ring_color": "accent", "text_cursor": "fg"},
    "motion": {"fast_ms": 90, "default_ms": 140, "slow_ms": 220,
               "reduced_ms": 0, "steps": 4},
}
SPACING = DESIGN_TOKENS["spacing"]


def _mix_color(start, end, amount):
    """Interpolate two Tk hex colors for short, low-cost widget transitions."""
    try:
        a = tuple(int(start[i:i + 2], 16) for i in (1, 3, 5))
        b = tuple(int(end[i:i + 2], 16) for i in (1, 3, 5))
        return "#%02x%02x%02x" % tuple(round(x + (y - x) * amount) for x, y in zip(a, b))
    except (TypeError, ValueError):
        return end


class RoundedPanel(tk.Canvas):
    """Canvas-backed rounded panel with a clipped inset content frame.

    Tk frames do not support border-radius. A small canvas draws a real rounded
    outline, while content remains ordinary Tk widgets. Hover transitions run
    only while the pointer enters/leaves this panel and honor reduced motion.
    """

    def __init__(self, parent, palette, *, radius=None, selected=False, **content_options):
        surface = content_options.pop("bg", palette["surface"])
        content_options.pop("highlightthickness", None)
        content_options.pop("highlightbackground", None)
        try:
            parent_bg = parent.cget("bg")
        except (tk.TclError, ValueError):
            try:
                parent_bg = parent.cget("fg_color")
                if isinstance(parent_bg, (list, tuple)):
                    parent_bg = parent_bg[-1]
            except Exception:
                parent_bg = palette["bg"]
        super().__init__(parent, bg=parent_bg, bd=0, highlightthickness=0,
                         width=220, height=72)
        self.palette = palette
        self.radius = max(4, int(radius or DESIGN_TOKENS["border"]["card_radius"]))
        self.inset = self.radius
        self.base_fill = surface
        self.base_border = palette["accent"] if selected else palette["border"]
        self.hover_border = palette["accent_hover"]
        self.current_fill = self.base_fill
        self.current_border = self.base_border
        self._animation_job = None
        self._animation_step = 0
        self._animation_from = (self.current_fill, self.current_border)
        self._animation_to = self._animation_from
        self.content = tk.Frame(self, bg=surface, **content_options)
        self._shape = self.create_polygon(0, 0, 1, 1, fill=surface, outline=self.base_border,
                                         width=DESIGN_TOKENS["border"]["hairline"], tags="panel")
        self._window = self.create_window(self.inset, self.inset, anchor="nw", window=self.content)
        self.bind("<Configure>", self._layout_panel, add="+")
        self.content.bind("<Configure>", self._content_resized, add="+")
        self.bind("<Enter>", lambda _event: self._animate_hover(True), add="+")
        self.bind("<Leave>", self._defer_leave, add="+")
        self.content.bind("<Enter>", lambda _event: self._animate_hover(True), add="+")
        self.content.bind("<Leave>", self._defer_leave, add="+")
        self.after_idle(self._fit_content_height)

    def _rounded_points(self, width, height):
        radius = min(self.radius, max(3, width / 2 - 1), max(3, height / 2 - 1))
        points = []
        for cx, cy, start in ((width - radius, radius, -90),
                              (width - radius, height - radius, 0),
                              (radius, height - radius, 90),
                              (radius, radius, 180)):
            for step in range(7):
                angle = math.radians(start + step * 15)
                points.extend((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return points

    def _layout_panel(self, _event=None):
        width, height = max(2, self.winfo_width()), max(2, self.winfo_height())
        inset = min(self.inset, max(1, width // 3), max(1, height // 3))
        self.coords(self._shape, *self._rounded_points(width - 1, height - 1))
        self.coords(self._window, inset, inset)
        self.itemconfigure(self._window, width=max(1, width - inset * 2),
                           height=max(1, height - inset * 2))

    def _content_resized(self, _event=None):
        self._fit_content_height()

    def _fit_content_height(self):
        try:
            requested = self.content.winfo_reqheight() + self.inset * 2
            if requested != self.winfo_reqheight():
                self.configure(height=requested)
        except tk.TclError:
            pass

    def _defer_leave(self, _event=None):
        try:
            self.after_idle(self._leave_if_outside)
        except tk.TclError:
            pass

    def _leave_if_outside(self):
        try:
            root = self.winfo_toplevel()
            target = root.winfo_containing(root.winfo_pointerx(), root.winfo_pointery())
            while target is not None:
                if target is self or target is self.content:
                    return
                target = getattr(target, "master", None)
        except tk.TclError:
            return
        self._animate_hover(False)

    def _animate_hover(self, active):
        try:
            root = self.winfo_toplevel()
            paused = bool(getattr(root, "_td2_suspend_animations", False))
            multiplier = float(getattr(root, "_td2_animation_multiplier", 1.0))
            if not math.isfinite(multiplier):
                multiplier = 1.0
        except (tk.TclError, TypeError, ValueError):
            paused, multiplier = True, 1.0
        target = (self.base_fill, self.hover_border if active else self.base_border)
        if paused or multiplier <= 0 or DESIGN_TOKENS["motion"]["default_ms"] <= 0:
            self._apply_colors(*target)
            return
        if self._animation_job:
            try:
                self.after_cancel(self._animation_job)
            except tk.TclError:
                pass
        self._animation_from = (self.current_fill, self.current_border)
        self._animation_to = target
        self._animation_step = 0
        self._animate_step(max(1, int(DESIGN_TOKENS["motion"]["default_ms"] /
                                      DESIGN_TOKENS["motion"]["steps"] / max(0.1, multiplier))))

    def _animate_step(self, delay):
        steps = max(1, int(DESIGN_TOKENS["motion"]["steps"]))
        self._animation_step += 1
        amount = min(1.0, self._animation_step / steps)
        fill = _mix_color(self._animation_from[0], self._animation_to[0], amount)
        border = _mix_color(self._animation_from[1], self._animation_to[1], amount)
        self._apply_colors(fill, border)
        if amount < 1.0:
            try:
                self._animation_job = self.after(delay, lambda: self._animate_step(delay))
            except tk.TclError:
                self._animation_job = None
        else:
            self._animation_job = None

    def _apply_colors(self, fill, border):
        self.current_fill, self.current_border = fill, border
        try:
            self.itemconfigure(self._shape, fill=fill, outline=border)
        except tk.TclError:
            pass

# Sekme ikonları (sekme kimliğine göre) / tab icons by tab id
# Monochrome glyphs keep navigation crisp on Windows fonts and avoid the
# inconsistent emoji sizing that previously made the shell look like a demo UI.
TAB_ICONS = {"dash": "◈", "builds": "◇", "progress": "▥", "stash": "▤", "stats": "▦", "info": "ⓘ", "translate": "↔", "tasks": "☷",
             "assistant": "✦", "settings": "⚙", "history": "◷", "log": "≡", "help": "?", "about": "□"}


def stripe_treeview(tv, palette):
    """Apply alternating row colors to a ttk.Treeview for readability."""
    odd, even = palette.get("_tv_odd", palette["surface"]), palette.get("_tv_even", palette["surface2"])
    tv.tag_configure("oddrow", background=odd)
    tv.tag_configure("evenrow", background=even)
    def _restripe(_event=None):
        for i, iid in enumerate(tv.get_children()):
            tv.item(iid, tags=("evenrow",) if i % 2 else ("oddrow",))
    tv.bind("<<TreeviewOpen>>", _restripe, add="+")
    tv.bind("<<TreeviewClose>>", _restripe, add="+")
    return _restripe


def with_icon(text, icon):
    """Metin zaten bir sembolle başlıyorsa olduğu gibi bırakır, yoksa ikonu ekler."""
    if not text or not icon:
        return text
    return text if not text[0].isalnum() else f"{icon} {text}"


_LEGACY_ICON_MAP = {
    "🌐": "◎", "⚡": "↯", "⬇": "↓", "⛶": "□", "🎯": "◈", "🎮": "◆",
    "👥": "☷", "📱": "▣", "🖥": "▤", "📋": "▤", "✉": "→", "📚": "ⓘ",
    "🔗": "↗", "➕": "+", "📍": "⌖", "🔄": "↻", "🔔": "!", "🐞": "!",
    "📨": "→", "👁": "◉", "📝": "≡", "📬": "▤", "🤖": "✦", "🗄": "▤",
    "📊": "▦", "🏢": "□", "🧩": "◇", "📦": "▥", "⭐": "*", "🔥": "!",
    "🔒": "■", "💡": "i", "🔍": "⌕", "🪟": "□", "🛰": "◎", "🩺": "+",
    "🧮": "#", "🧾": "≡", "🏪": "□", "📤": "↑", "✨": "✦", "⌨": "⌨",
}


def normalize_surface(root):
    """Normalize legacy visual glyphs across a completed Tk widget tree.

    Older pages still contain localized labels assembled with emoji prefixes.
    Normalizing after each page build gives the whole application one stable
    monochrome icon language without changing the underlying route or text.
    """
    def clean(value):
        if not isinstance(value, str):
            return value
        for old, new in _LEGACY_ICON_MAP.items():
            value = value.replace(old, new)
        return value

    def visit(widget):
        try:
            if widget.winfo_class() == "TNotebook":
                for tab_id in widget.tabs():
                    label = widget.tab(tab_id, "text")
                    cleaned = clean(label)
                    if cleaned != label:
                        widget.tab(tab_id, text=cleaned)
            try:
                text = widget.cget("text")
            except (tk.TclError, TypeError):
                text = None
            cleaned = clean(text)
            if cleaned != text:
                widget.configure(text=cleaned)
        except (tk.TclError, AttributeError, TypeError, ValueError):
            pass
        try:
            children = widget.winfo_children()
        except (tk.TclError, AttributeError):
            children = ()
        for child in children:
            visit(child)

    visit(root)


def apply(root, mode="default"):
    """Temayı uygular ve kullanılan paleti (sözlük) döndürür."""
    resolve_fonts(root)
    mode = canonical_mode(mode)
    p = dict(PALETTES[mode], mode=mode)
    # Keep CustomTkinter wrappers and native ttk controls on the same semantic
    # palette.  The import stays local to avoid a module-level UI cycle.
    try:
        from . import ctk_compat
        ctk_compat.set_theme_palette(p)
    except ImportError:
        pass
    s = ttk.Style(root)
    root.option_clear()                    # önceki tk ayarlarını temizle (anlık tema yeniden kurulumu)
    # ttk teması kendi adında tutulur.
    name = f"td2-{mode}"
    if name not in s.theme_names():
        s.theme_create(name, parent="clam")
    s.theme_use(name)
    s.layout("NoTabs.TNotebook", [("Notebook.client", {"sticky": "nswe"})])
    # ttk Notebook, bazı Windows temalarında sekme öğesini notebook stilinden
    # ayrı çözer; özel sekme stilini de boşaltmak üst navigasyon satırının
    # yeniden görünmesini engeller. Normal TNotebook sekmeleri etkilenmez.
    s.layout("NoTabs.TNotebook.Tab", [])

    bg, sf, sf2, bd, fg, mu = p["bg"], p["surface"], p["surface2"], p["border"], p["fg"], p["muted"]
    ac, ach, ent = p["accent"], p["accent_hover"], p["entry"]
    base = (FONT, DESIGN_TOKENS["type"]["body"])

    root.configure(bg=bg)
    s.configure(".", background=bg, foreground=fg, fieldbackground=ent, bordercolor=bd,
                lightcolor=sf2, darkcolor=sf2, troughcolor=sf2, focuscolor=ac,
                selectbackground=ac, selectforeground=p["accent_fg"], insertcolor=fg,
                arrowcolor=fg, font=base)

    # çerçeveler ve yazılar
    s.configure("TFrame", background=bg)
    s.configure("Sidebar.TFrame", background=sf, bordercolor=bd, borderwidth=1, relief="solid")
    s.configure("SidebarHeader.TFrame", background=sf)
    s.configure("SidebarContent.TFrame", background=sf)
    s.configure("PageContext.TFrame", background=sf2, bordercolor=p.get("line", bd), borderwidth=1, relief="solid")
    s.configure("PageRail.TFrame", background=ac)
    s.configure("PageEyebrow.TLabel", background=sf2, foreground=ac,
                font=(FONT_MONO, DESIGN_TOKENS["type"]["caption"], "bold"))
    s.configure("PageTitle.TLabel", background=sf2, foreground=fg,
                font=(FONT_DISPLAY, DESIGN_TOKENS["type"]["page"], "bold"))
    s.configure("PageStatus.TLabel", background=sf2, foreground=p.get("signal", p["info"]),
                font=(FONT_MONO, DESIGN_TOKENS["type"]["small"]))
    s.configure("NavMasthead.TLabel", background=sf, foreground=ac,
                font=(FONT_DISPLAY, DESIGN_TOKENS["type"]["section"], "bold"))
    s.configure("NavSection.TLabel", background=sf, foreground=mu, font=(FONT_MONO, DESIGN_TOKENS["type"]["caption"]))
    s.configure("NavGroup.TLabel", background=sf, foreground=mu, font=(FONT_SEMI, DESIGN_TOKENS["type"]["meta"]))
    s.configure("NavMeta.TLabel", background=sf, foreground=mu, font=(FONT, DESIGN_TOKENS["type"]["small"]))
    s.configure("NavCategory.TButton", background=sf, foreground=mu, borderwidth=1,
                bordercolor=sf, anchor="w", padding=(SPACING["md"], 9),
                relief="flat", font=(FONT_SEMI, DESIGN_TOKENS["type"]["control"]), focuscolor=ac,
                focusthickness=DESIGN_TOKENS["border"]["focus"])
    s.map("NavCategory.TButton", background=[("active", sf2), ("pressed", p["select"])],
          foreground=[("active", fg), ("pressed", ac)], bordercolor=[("focus", ac)])
    s.configure("NavCategoryActive.TButton", background=p["select"], foreground=ac,
                borderwidth=1, bordercolor=ac, anchor="w",
                padding=(SPACING["md"], 9), relief="flat",
                font=(FONT_SEMI, DESIGN_TOKENS["type"]["control"]), focuscolor=ac,
                focusthickness=DESIGN_TOKENS["border"]["focus"])
    s.map("NavCategoryActive.TButton", background=[("active", sf2), ("pressed", bd)],
          foreground=[("active", ac), ("pressed", fg)], bordercolor=[("focus", ac)])
    s.configure("Nav.TButton", background=sf, foreground=mu, borderwidth=0, anchor="w",
                padding=(SPACING["lg"], 7), relief="flat",
                font=(FONT_SEMI, DESIGN_TOKENS["type"]["control"]), focuscolor=ac,
                focusthickness=DESIGN_TOKENS["border"]["focus"])
    s.map("Nav.TButton", background=[("active", sf2), ("pressed", sf2)],
          foreground=[("active", fg), ("pressed", ac)], bordercolor=[("focus", ac)])
    s.configure("NavActive.TButton", background=sf2, foreground=fg, borderwidth=1,
                bordercolor=ac, anchor="w", padding=(SPACING["lg"], 7),
                relief="flat", font=(FONT_SEMI, DESIGN_TOKENS["type"]["control"]), focuscolor=ac,
                focusthickness=DESIGN_TOKENS["border"]["focus"])
    s.map("NavActive.TButton", background=[("active", sf2), ("pressed", bd)],
          foreground=[("active", ac), ("pressed", fg)], bordercolor=[("focus", ac)])
    # Tam genişlikli Saha Terminali kabuğunun üst operasyon menüsü.
    s.configure("FieldNav.TButton", background=sf, foreground=mu, bordercolor=bd, anchor="center",
                padding=(12, 9), relief="flat", font=(FONT_SEMI, 10))
    s.map("FieldNav.TButton", background=[("active", sf2), ("pressed", p["select"])],
          foreground=[("active", fg), ("pressed", ac)], bordercolor=[("active", ac)])
    s.configure("FieldNavActive.TButton", background=p["select"], foreground=ac, bordercolor=ac, anchor="center",
                padding=(12, 9), relief="flat", font=(FONT_SEMI, 10))
    s.map("FieldNavActive.TButton", background=[("active", sf2), ("pressed", bd)], foreground=[("active", fg)])
    s.configure("Card.TFrame", background=sf, bordercolor=p.get("line", bd), borderwidth=1, relief="solid")
    s.configure("Header.TFrame", background=sf2, bordercolor=p.get("line_strong", bd), borderwidth=1, relief="solid")
    s.configure("TLabel", background=bg, foreground=fg)
    s.configure("Muted.TLabel", background=bg, foreground=mu)
    s.configure("Card.TLabel", background=sf, foreground=fg)
    s.configure("CardMuted.TLabel", background=sf, foreground=mu)
    s.configure("Brand.TLabel", background=sf, foreground=ac, font=(FONT_MONO, 11, "bold"))
    s.configure("Title.TLabel", background=bg, foreground=fg, font=(FONT_SEMI, DESIGN_TOKENS["type"]["page"]))
    s.configure("Item.TLabel", background=sf, foreground=fg, font=(FONT_DISPLAY, 14, "bold"))
    s.configure("Note.TLabel", background=sf, foreground=p["info"], font=(FONT_SEMI, DESIGN_TOKENS["type"]["small"]))
    s.configure("Chip.TLabel", background=sf2, foreground=fg, padding=(10, 4),
                font=(FONT_MONO, DESIGN_TOKENS["type"]["small"]))
    s.configure("ChipOn.TLabel", background=p["success"], foreground="#ffffff", padding=(10, 4),
                font=(FONT_MONO, DESIGN_TOKENS["type"]["small"]))
    s.configure("Warn.TLabel", background=bg, foreground=p["warning"])
    s.configure("Section.TLabel", background=bg, foreground=fg,
                font=(FONT_DISPLAY, DESIGN_TOKENS["type"]["section"], "bold"))
    s.configure("TSeparator", background=bd)

    # butonlar
    s.configure("TButton", background=sf, foreground=fg, bordercolor=bd, lightcolor=sf,
                darkcolor=sf, padding=(SPACING["lg"], 9), relief="flat",
                focuscolor=ac, focusthickness=DESIGN_TOKENS["border"]["focus"],
                font=(FONT_SEMI, DESIGN_TOKENS["type"]["control"], "bold"))
    s.map("TButton", background=[("disabled", bg), ("pressed", bd), ("active", sf2)],
          foreground=[("disabled", mu), ("active", fg)], bordercolor=[("active", ac), ("focus", ac)],
          lightcolor=[("pressed", bd), ("active", sf2)], darkcolor=[("pressed", bd), ("active", sf2)])
    for name, col, hov in (("Accent", ac, ach), ("Success", p["success"], p["success"]),
                           ("Danger", p["danger"], p["danger"])):
        s.configure(f"{name}.TButton", background=col, foreground=p["accent_fg"] if name == "Accent" else "#ffffff", bordercolor=col,
                    lightcolor=col, darkcolor=col, padding=(SPACING["xl"], 9),
                    font=(FONT_SEMI, DESIGN_TOKENS["type"]["control"], "bold"),
                    focuscolor=ac, focusthickness=DESIGN_TOKENS["border"]["focus"])
        s.map(f"{name}.TButton", background=[("pressed", hov), ("active", hov)],
              lightcolor=[("active", hov)], darkcolor=[("active", hov)],
              bordercolor=[("active", "#ffffff"), ("focus", col)])

    # sekmeler: SHD HUD'da sekme çizgisi tek vurgu rengiyle taşınır
    s.configure("TNotebook", background=bg, borderwidth=0, tabmargins=(2, 6, 2, 0),
                bordercolor=p.get("line", bd), lightcolor=p.get("line", bd), darkcolor=p.get("line", bd))
    s.configure("TNotebook.Tab", background=bg, foreground=mu, padding=(16, 9), bordercolor=bg,
                lightcolor=bg, darkcolor=bg, font=(FONT_SEMI, DESIGN_TOKENS["type"]["control"], "bold"))
    s.map("TNotebook.Tab", background=[("selected", sf2), ("active", sf2)],
          foreground=[("selected", ac), ("active", fg)],
          lightcolor=[("selected", ac)], bordercolor=[("selected", ac)])

    # gruplar
    s.configure("TLabelframe", background=bg, bordercolor=bd, lightcolor=bd, darkcolor=bd,
                relief="solid", padding=(SPACING["md"], SPACING["sm"]))
    s.configure("TLabelframe.Label", background=bg, foreground=ac,
                font=(FONT_SEMI, DESIGN_TOKENS["type"]["small"], "bold"))

    # giriş alanları
    s.configure("TEntry", fieldbackground=ent, foreground=fg, bordercolor=bd, lightcolor=ent,
                darkcolor=ent, insertcolor=fg, padding=(10, 7), font=base,
                focusthickness=DESIGN_TOKENS["focus"]["ring_width"])
    s.map("TEntry", bordercolor=[("focus", ac)], lightcolor=[("focus", ac)])
    s.configure("TCombobox", fieldbackground=ent, background=sf2, foreground=fg, arrowcolor=fg,
                bordercolor=bd, lightcolor=ent, darkcolor=ent, padding=(10, 6), font=base,
                focusthickness=DESIGN_TOKENS["focus"]["ring_width"])
    s.map("TCombobox", fieldbackground=[("readonly", ent)], foreground=[("readonly", fg)],
          selectbackground=[("readonly", ent)], selectforeground=[("readonly", fg)],
          bordercolor=[("focus", ac), ("active", ac)], background=[("active", bd)])
    root.option_add("*TCombobox*Listbox.background", sf)
    root.option_add("*TCombobox*Listbox.foreground", fg)
    root.option_add("*TCombobox*Listbox.selectBackground", ac)
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
    root.option_add("*TCombobox*Listbox.font", base)
    # Tk defaults to a short popup list.  Keep enough rows visible for log
    # levels, OCR engines, themes and language lists without truncating the
    # menu to only its first few entries.
    root.option_add("*TCombobox*Listbox.height", 14)
    # The field may stay compact, but its opened list must fit long options.
    root.option_add("*TCombobox*Listbox.width", 36)
    root.option_add("*TCombobox*Listbox.activestyle", "none")

    # onay kutuları / seçenekler
    for w in ("TCheckbutton", "TRadiobutton"):
        s.configure(w, background=bg, foreground=fg, indicatorbackground=ent,
                    indicatorforeground=ac, upperbordercolor=bd, lowerbordercolor=bd)
        s.map(w, background=[("active", bg)], foreground=[("active", ac)],
              indicatorbackground=[("selected", ac), ("active", sf2)],
              indicatorforeground=[("selected", "#ffffff")])

    # tablolar
    s.configure("Treeview", background=sf, fieldbackground=sf, foreground=fg, bordercolor=bd,
                lightcolor=sf, darkcolor=sf, rowheight=38, font=base,
                focusthickness=DESIGN_TOKENS["focus"]["ring_width"])
    s.map("Treeview", background=[("selected", p["select"])], foreground=[("selected", fg)])
    s.configure("Treeview.Heading", background=sf2, foreground=mu, bordercolor=bd, lightcolor=sf2,
                darkcolor=sf2, relief="flat", padding=(10, 9),
                font=(FONT_MONO, DESIGN_TOKENS["type"]["small"], "bold"))
    s.map("Treeview.Heading", background=[("active", bd)], foreground=[("active", ac)])
    p["_tv_odd"] = sf
    p["_tv_even"] = sf2

    # ilerleme çubuğu ve kaydırma çubukları: ince HUD çizgileri
    s.configure("TProgressbar", background=ac, troughcolor=sf, bordercolor=sf,
                lightcolor=ac, darkcolor=ac, thickness=8)
    for orient in ("Vertical", "Horizontal"):
        s.configure(f"{orient}.TScrollbar", background=sf2, troughcolor=bg, bordercolor=bg,
                    arrowcolor=mu, lightcolor=sf2, darkcolor=sf2, gripcount=0, arrowsize=12)
        s.map(f"{orient}.TScrollbar", background=[("active", ac)], arrowcolor=[("active", ac)])

    # klasik tk bileşenleri (Text, Listbox, Canvas)
    for cls in ("Text", "Listbox"):
        root.option_add(f"*{cls}.background", p["text_bg"])
        root.option_add(f"*{cls}.foreground", fg)
        root.option_add(f"*{cls}.selectBackground", ac)
        root.option_add(f"*{cls}.selectForeground", "#ffffff")
        root.option_add(f"*{cls}.relief", "flat")
        root.option_add(f"*{cls}.borderWidth", 0)
        root.option_add(f"*{cls}.highlightThickness", DESIGN_TOKENS["focus"]["ring_width"])
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
    # Native Tk controls need the same visible keyboard ring as ttk controls.
    for cls in ("Entry", "Spinbox", "Scale", "Listbox"):
        root.option_add(f"*{cls}.highlightThickness", DESIGN_TOKENS["focus"]["ring_width"])
        root.option_add(f"*{cls}.highlightBackground", bd)
        root.option_add(f"*{cls}.highlightColor", ac)
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
        # bind_all keeps the callback alive until the pointer leaves the old
        # canvas. During a theme/language rebuild that canvas may already be
        # destroyed while Tk still dispatches the queued wheel event.
        try:
            if not canvas.winfo_exists() or not inner.winfo_exists():
                return
            if e.widget.winfo_class() in ("Text", "Listbox", "Treeview", "TCombobox"):
                return
            if canvas.winfo_height() >= inner.winfo_reqheight():
                return
            step = -1 if (getattr(e, "delta", 0) > 0 or getattr(e, "num", 0) == 4) else 1
            canvas.yview_scroll(step * 3, "units")
        except tk.TclError:
            # A queued event can race with destruction even after the
            # existence check; stale input is harmless and should be ignored.
            return

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
