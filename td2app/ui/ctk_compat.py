"""CustomTkinter uyumluluk katmanı.

Standart tk/ttk widget API'sini CustomTkinter widget'larına yönlendirir.
app.py'de `tk` ve `ttk` modüllerini bu modülün sağladığı wrapper'larla
değiştirmek yeterlidir — mevcut parametreler (bg, fg, font, padx, vb.)
otomatik olarak CTk karşılıklarına çevrilir.

ttk.Notebook, ttk.Treeview, ttk.Style, tk.Canvas gibi CTk karşılığı
olmayan widget'lar orijinal tkinter modülünden aktarılır.

Call sites: app.py:18 (import tkinter as tk), app.py:24 (from tkinter import ttk)
ve bu dosyalardaki 941 widget oluşturma çağrısı.
Kullanıcı talimatı: "CustomTkinter'ı tam entegre etmek 11.000+ satır
widget değişimi gerektirirse de yap"
"""
from __future__ import annotations

import tkinter as _tk
from tkinter import ttk as _ttk

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

_BASE_FRAME = ctk.CTkFrame if CTK_AVAILABLE else _tk.Frame
_BASE_LABEL = ctk.CTkLabel if CTK_AVAILABLE else _tk.Label
_BASE_BUTTON = ctk.CTkButton if CTK_AVAILABLE else _tk.Button
_BASE_ENTRY = ctk.CTkEntry if CTK_AVAILABLE else _tk.Entry
_BASE_CHECKBOX = ctk.CTkCheckBox if CTK_AVAILABLE else _tk.Checkbutton
_BASE_PROGRESSBAR = ctk.CTkProgressBar if CTK_AVAILABLE else _ttk.Progressbar
_BASE_SLIDER = ctk.CTkSlider if CTK_AVAILABLE else _ttk.Scale
_BASE_TEXTBOX = ctk.CTkTextbox if CTK_AVAILABLE else _tk.Text
_BASE_COMBOBOX = ctk.CTkComboBox if CTK_AVAILABLE else _ttk.Combobox


def _dropdown_character_width(values, minimum=30, padding=6, maximum=72):
    """Return a readable popup width for a combo-box value list.

    CustomTkinter's native dropdown menu sizes itself from character width,
    not from the compact field width.  Keeping this calculation here makes
    every combo box behave consistently, including values added after the
    widget was created.  A small padding buffer protects Turkish and other
    Latin-extended glyphs from touching the menu border.
    """
    texts = [str(value) for value in (values or ()) if value is not None]
    longest = max((len(text) for text in texts), default=0)
    return min(maximum, max(minimum, longest + padding))


def _combo_control_width(requested, values, minimum=140, maximum=420):
    """Convert legacy character-style widths to readable CTk pixel widths.

    The application historically passed values such as ``width=10`` using
    ttk's character convention.  CTkComboBox interprets width in pixels, so
    forwarding that value literally produces the one-letter fields visible in
    the UI.  Keep explicitly large pixel widths intact and normalize the
    compact legacy values using the longest option as a lower bound.
    """
    try:
        requested = int(requested)
    except (TypeError, ValueError):
        requested = minimum
    longest = max((len(str(value)) for value in (values or ()) if value is not None), default=0)
    content_width = longest * 8 + 48
    if requested < minimum:
        requested = requested * 8 + 24
    return min(maximum, max(minimum, requested, content_width))


def _entry_control_width(requested, minimum=96, maximum=720):
    """Convert legacy Tk character widths to readable CustomTkinter pixels.

    The application historically passes ``Entry(width=40)`` using Tk's
    character convention.  CustomTkinter interprets the same value as pixels,
    which collapses URL, token and search fields to a few characters.  Keep
    explicit large pixel widths intact while making small legacy values usable.
    """
    try:
        requested = int(requested)
    except (TypeError, ValueError):
        requested = minimum
    if requested < minimum:
        requested = requested * 8 + 24
    return min(maximum, max(minimum, requested))


_BASE_TOPLEVEL = ctk.CTkToplevel if CTK_AVAILABLE else _tk.Toplevel
_BASE_SCROLLBAR = ctk.CTkScrollbar if CTK_AVAILABLE else _ttk.Scrollbar

# The application still exposes the classic Tk ``bg``/``fg`` vocabulary, but
# CustomTkinter needs a semantic palette at construction time.  Keeping this
# tiny bridge here prevents individual screens from inventing their own CTk
# colors and makes theme swaps apply to controls created afterwards.
_THEME = {
    "surface": "#141e27", "surface2": "#1b2a36", "bg": "#0d141b", "entry": "#0a1117",
    "fg": "#e7eef5", "muted": "#91a5b5", "border": "#2d4352",
    "accent": "#f0a35b", "accent_hover": "#ffc17e", "accent_fg": "#17202a",
    "success": "#7cc98a", "danger": "#ed747b", "info": "#71b8d4",
}

# Emoji glyphs have different color, baseline and width behavior across
# Windows font stacks.  Keep the existing localized labels intact while
# normalizing legacy icon prefixes at the shared widget boundary.
_ICON_REPLACEMENTS = {
    "🌐": "◎", "⚡": "↯", "⬇": "↓", "⛶": "□", "🎯": "◈", "🎮": "◆",
    "👥": "☷", "📱": "▣", "🖥": "▤", "📋": "▤", "✉": "→", "📚": "ⓘ",
    "🔗": "↗", "➕": "+", "📍": "⌖", "🔄": "↻", "🔔": "!", "🐞": "!",
    "📨": "→", "👁": "◉", "📝": "≡", "📬": "▤", "🤖": "✦", "🗄": "▤",
    "📊": "▦", "🏢": "□", "🧩": "◇", "📦": "▥", "⭐": "*", "🔥": "!",
    "🔒": "■", "💡": "i", "⚙": "⚙", "⌨": "⌨", "🔍": "⌕", "🪟": "□",
    "🛰": "◎", "🩺": "+", "🧮": "#", "🧾": "≡", "🏪": "□", "📤": "↑",
}


def _clean_text(value):
    if not isinstance(value, str):
        return value
    for source, target in _ICON_REPLACEMENTS.items():
        value = value.replace(source, target)
    return value


def set_theme_palette(palette):
    """Set semantic colors used by CTk wrappers created after a theme swap."""
    if isinstance(palette, dict):
        for key in _THEME:
            if key in palette:
                _THEME[key] = palette[key]


def _focus_ring(widget):
    """Give CTk controls a visible keyboard focus state without hover-only UX."""
    if not CTK_AVAILABLE:
        return
    try:
        base_border = widget.cget("border_color")
        base_width = int(widget.cget("border_width"))
    except (_tk.TclError, AttributeError, TypeError, ValueError):
        base_border, base_width = _THEME["border"], 1

    def focus_in(_event=None):
        try:
            widget.configure(border_width=max(2, base_width), border_color=_THEME["accent"])
        except (_tk.TclError, AttributeError, RuntimeError, ValueError):
            pass

    def focus_out(_event=None):
        try:
            widget.configure(border_width=base_width, border_color=base_border)
        except (_tk.TclError, AttributeError, RuntimeError, ValueError):
            pass

    try:
        pending, targets = [widget], []
        while pending:
            target = pending.pop()
            targets.append(target)
            pending.extend(target.winfo_children())
        for target in targets:
            target.bind("<FocusIn>", focus_in, add="+")
            target.bind("<FocusOut>", focus_out, add="+")
    except (_tk.TclError, AttributeError, RuntimeError):
        pass

def compat_image(pil_image, size=None):
    """HiDPI-aware image: CTkImage when available, PhotoImage fallback.

    Canvas items still need PhotoImage — use this only for CtkLabel/CtkButton.
    """
    if size is None:
        size = (pil_image.width, pil_image.height)
    if CTK_AVAILABLE:
        return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)
    from PIL import ImageTk, Image as _Img
    if pil_image.size != tuple(size):
        pil_image = pil_image.resize(tuple(size), _Img.LANCZOS)
    return ImageTk.PhotoImage(pil_image)


_TK_IGNORED = frozenset({
    "activebackground", "activeforeground", "highlightthickness",
    "highlightbackground", "highlightcolor", "bd", "borderwidth",
    "relief", "selectbackground", "selectforeground", "insertbackground",
    "overrelief", "compound", "padding", "wraplength", "exportselection",
    "undo", "maxundo", "autoseparators", "spacing1", "spacing2", "spacing3",
    "selectborderwidth", "insertwidth", "insertofftime", "insertontime",
    "readonlybackground", "xscrollcommand", "yscrollcommand",
})


def _pop_tk(kw):
    mapped = {}
    if "bg" in kw:
        mapped["fg_color"] = kw.pop("bg")
    if "background" in kw:
        mapped["fg_color"] = kw.pop("background")
    if "fg" in kw:
        mapped["text_color"] = kw.pop("fg")
    if "foreground" in kw:
        mapped["text_color"] = kw.pop("foreground")
    if "disabledforeground" in kw:
        mapped["text_color_disabled"] = kw.pop("disabledforeground")
    for k in list(kw):
        if k in _TK_IGNORED:
            kw.pop(k)
    kw.pop("style", None)
    kw.pop("takefocus", None)
    return mapped


def _apply_cursor(widget, cursor):
    """Apply Tk's cursor option after CTk construction.

    CustomTkinter accepts ``cursor`` on ``configure`` but rejects it in many
    widget constructors.  Delaying this one option keeps both APIs working.
    """
    if cursor:
        try:
            widget.configure(cursor=cursor)
        except (_tk.TclError, TypeError, ValueError):
            pass


class CtkFrame(_BASE_FRAME):
    def __init__(self, master=None, **kw):
        cursor = kw.pop("cursor", None)
        mapped = _pop_tk(kw)
        if CTK_AVAILABLE:
            mapped.setdefault("fg_color", _THEME["bg"])
        w = kw.pop("width", None)
        h = kw.pop("height", None)
        init_kw = {**mapped}
        if w is not None:
            init_kw["width"] = w
        if h is not None:
            init_kw["height"] = h
        init_kw["corner_radius"] = kw.pop("corner_radius", 0)
        init_kw["border_width"] = kw.pop("border_width", 0)
        if "border_color" in kw:
            init_kw["border_color"] = kw.pop("border_color")
        kw.pop("padx", None)
        kw.pop("pady", None)
        super().__init__(master, **init_kw)
        _apply_cursor(self, cursor)

    def config(self, **kw):
        mapped = _pop_tk(kw)
        kw.update(mapped)
        try:
            super().configure(**kw)
        except (_tk.TclError, ValueError):
            pass

    configure = config

    def cget(self, key):
        alias = {"bg": "fg_color", "background": "fg_color"}
        try:
            return super().cget(alias.get(key, key))
        except ValueError:
            return ""

    def place(self, cnf=None, **kw):
        kw.pop("width", None)
        kw.pop("height", None)
        super().place(cnf, **kw) if cnf else super().place(**kw)


class CtkLabel(_BASE_LABEL):
    def __init__(self, master=None, **kw):
        cursor = kw.pop("cursor", None)
        mapped = _pop_tk(kw)
        if CTK_AVAILABLE:
            mapped.setdefault("text_color", _THEME["fg"])
        init_kw = {**mapped}
        for key in ("text", "font", "anchor", "justify", "image", "width",
                    "height", "textvariable", "fg_color", "border_color",
                    "border_width"):
            if key in kw:
                init_kw[key] = _clean_text(kw.pop(key)) if key == "text" else kw.pop(key)
        init_kw["corner_radius"] = kw.pop("corner_radius", 0)
        super().__init__(master, **init_kw)
        _apply_cursor(self, cursor)

    def config(self, **kw):
        mapped = _pop_tk(kw)
        kw.update(mapped)
        try:
            super().configure(**kw)
        except (_tk.TclError, ValueError):
            pass

    configure = config

    def cget(self, key):
        alias = {"bg": "fg_color", "fg": "text_color", "background": "fg_color",
                 "foreground": "text_color"}
        return super().cget(alias.get(key, key))


class CtkButton(_BASE_BUTTON):
    def __init__(self, master=None, **kw):
        cursor = kw.pop("cursor", None)
        style = kw.get("style")
        mapped = _pop_tk(kw)
        if CTK_AVAILABLE:
            style_colors = {
                "Accent.TButton": (_THEME["accent"], _THEME["accent_hover"], _THEME["accent_fg"]),
                "Success.TButton": (_THEME["success"], _THEME["success"], "#ffffff"),
                "Danger.TButton": (_THEME["danger"], _THEME["danger"], "#ffffff"),
            }
            fill, hover, text = style_colors.get(
                style, (_THEME["surface"], _THEME["surface2"], _THEME["fg"])
            )
            mapped.setdefault("fg_color", fill)
            mapped.setdefault("hover_color", hover)
            mapped.setdefault("text_color", text)
            mapped.setdefault("border_color", _THEME["border"])
            mapped.setdefault("border_width", 1)
        init_kw = {**mapped}
        for key in ("text", "font", "command", "image", "width", "height",
                    "state", "textvariable", "anchor"):
            if key in kw:
                init_kw[key] = _clean_text(kw.pop(key)) if key == "text" else kw.pop(key)
        init_kw["corner_radius"] = kw.pop("corner_radius", 4)
        if "hover_color" in kw:
            init_kw["hover_color"] = kw.pop("hover_color")
        if "border_width" in kw:
            init_kw["border_width"] = kw.pop("border_width")
        if "border_color" in kw:
            init_kw["border_color"] = kw.pop("border_color")
        super().__init__(master, **init_kw)
        _apply_cursor(self, cursor)
        _focus_ring(self)

    def config(self, **kw):
        if "text" in kw:
            kw["text"] = _clean_text(kw["text"])
        mapped = _pop_tk(kw)
        kw.update(mapped)
        try:
            super().configure(**kw)
        except (_tk.TclError, ValueError):
            pass

    configure = config

    def cget(self, key):
        alias = {"text": "text", "bg": "fg_color", "fg": "text_color"}
        return super().cget(alias.get(key, key))

    def invoke(self):
        cmd = self.cget("command")
        if callable(cmd):
            cmd()

    def state(self, statespec=None):
        if statespec is None:
            return ("disabled",) if str(self.cget("state")) == "disabled" else ()
        for s in statespec:
            if s == "disabled":
                self.configure(state="disabled")
            elif s == "!disabled":
                self.configure(state="normal")


class CtkEntry(_BASE_ENTRY):
    def __init__(self, master=None, **kw):
        cursor = kw.pop("cursor", None)
        mapped = _pop_tk(kw)
        if CTK_AVAILABLE:
            mapped.setdefault("fg_color", _THEME["entry"] if "entry" in _THEME else _THEME["bg"])
            mapped.setdefault("text_color", _THEME["fg"])
            mapped.setdefault("border_color", _THEME["border"])
            mapped.setdefault("border_width", 1)
        init_kw = {**mapped}
        for key in ("font", "width", "state", "textvariable",
                    "placeholder_text", "justify", "show"):
            if key in kw:
                value = kw.pop(key)
                init_kw[key] = (_entry_control_width(value) if CTK_AVAILABLE and key == "width" else value)
        init_kw["corner_radius"] = kw.pop("corner_radius", 4)
        super().__init__(master, **init_kw)
        _apply_cursor(self, cursor)
        _focus_ring(self)

    def config(self, **kw):
        mapped = _pop_tk(kw)
        kw.update(mapped)
        try:
            super().configure(**kw)
        except (_tk.TclError, ValueError):
            pass

    configure = config


class CtkCheckBox(_BASE_CHECKBOX):
    def __init__(self, master=None, **kw):
        cursor = kw.pop("cursor", None)
        mapped = _pop_tk(kw)
        init_kw = {**mapped}
        for key in ("text", "font", "command", "variable", "onvalue",
                    "offvalue", "state", "width", "height"):
            if key in kw:
                init_kw[key] = kw.pop(key)
        init_kw["corner_radius"] = kw.pop("corner_radius", 4)
        super().__init__(master, **init_kw)
        _apply_cursor(self, cursor)
        _focus_ring(self)

    def config(self, **kw):
        mapped = _pop_tk(kw)
        kw.update(mapped)
        try:
            super().configure(**kw)
        except (_tk.TclError, ValueError):
            pass

    configure = config

    def state(self, statespec=None):
        if statespec is None:
            return ("disabled",) if str(self.cget("state")) == "disabled" else ()
        for s in statespec:
            if s == "disabled":
                self.configure(state="disabled")
            elif s == "!disabled":
                self.configure(state="normal")
            elif s == "selected":
                self.select()
            elif s == "!selected":
                self.deselect()


class CtkProgressBar(_BASE_PROGRESSBAR):
    def __init__(self, master=None, **kw):
        mapped = _pop_tk(kw)
        kw.pop("orient", None)
        kw.pop("mode", None)
        kw.pop("maximum", None)
        kw.pop("value", None)
        init_kw = {**mapped}
        for key in ("width", "height"):
            if key in kw:
                init_kw[key] = kw.pop(key)
        init_kw["corner_radius"] = kw.pop("corner_radius", 4)
        if "progress_color" in kw:
            init_kw["progress_color"] = kw.pop("progress_color")
        super().__init__(master, **init_kw)

    def set_value(self, value, maximum=100):
        try:
            self.set(value / maximum)
        except Exception:
            pass

    def __setitem__(self, key, value):
        if key == "value":
            self.set_value(value)
        elif key == "maximum":
            pass
        else:
            self.configure(**{key: value})

    def __getitem__(self, key):
        if key == "value":
            return self.get() * 100
        return self.cget(key)

    def config(self, **kw):
        if "value" in kw:
            val = kw.pop("value")
            mx = kw.pop("maximum", 100)
            self.set_value(val, mx)
        kw.pop("maximum", None)
        mapped = _pop_tk(kw)
        kw.update(mapped)
        try:
            super().configure(**kw)
        except (_tk.TclError, ValueError):
            pass

    configure = config


class CtkSlider(_BASE_SLIDER):
    def __init__(self, master=None, **kw):
        mapped = _pop_tk(kw)
        kw.pop("orient", None)
        init_kw = {**mapped}
        for key in ("from_", "to", "command", "variable", "width",
                    "number_of_steps"):
            if key in kw:
                init_kw[key] = kw.pop(key)
        super().__init__(master, **init_kw)
        _focus_ring(self)


class CtkTextbox(_BASE_TEXTBOX):
    def __init__(self, master=None, **kw):
        mapped = _pop_tk(kw)
        if CTK_AVAILABLE:
            mapped.setdefault("fg_color", _THEME["entry"])
            mapped.setdefault("text_color", _THEME["fg"])
            mapped.setdefault("border_color", _THEME["border"])
        kw.pop("wrap", None)
        init_kw = {**mapped}
        for key in ("font", "width", "height", "state"):
            if key in kw:
                init_kw[key] = kw.pop(key)
        init_kw["corner_radius"] = kw.pop("corner_radius", 4)
        super().__init__(master, **init_kw)
        _focus_ring(self)

    def config(self, **kw):
        mapped = _pop_tk(kw)
        kw.update(mapped)
        try:
            super().configure(**kw)
        except (_tk.TclError, ValueError):
            pass

    configure = config

    def _inner(self):
        return getattr(self, "_textbox", self)

    def tag_configure(self, tag, **kw):
        self._inner().tag_configure(tag, **kw)

    tag_config = tag_configure

    def tag_add(self, tag, *args):
        self._inner().tag_add(tag, *args)

    def tag_remove(self, tag, *args):
        self._inner().tag_remove(tag, *args)

    def tag_names(self, index=None):
        if index is not None:
            return self._inner().tag_names(index)
        return self._inner().tag_names()

    def tag_ranges(self, tag):
        return self._inner().tag_ranges(tag)

    def see(self, index):
        self._inner().see(index)

    def mark_set(self, name, index):
        self._inner().mark_set(name, index)

    def search(self, pattern, index, **kw):
        return self._inner().search(pattern, index, **kw)


class CtkComboBox(_BASE_COMBOBOX):
    def __init__(self, master=None, **kw):
        mapped = _pop_tk(kw)
        init_kw = {**mapped}
        values = kw.get("values", ())
        if "textvariable" in kw:
            init_kw["variable"] = kw.pop("textvariable")
        if "values" in kw:
            init_kw["values"] = kw.pop("values")
        if "state" in kw:
            st = kw.pop("state")
            init_kw["state"] = "readonly" if st == "readonly" else st
        for key in ("font", "width", "command", "justify"):
            if key in kw:
                init_kw[key] = kw.pop(key)
        init_kw["corner_radius"] = kw.pop("corner_radius", 4)
        if CTK_AVAILABLE:
            init_kw["width"] = _combo_control_width(init_kw.get("width", 140), values)
        super().__init__(master, **init_kw)
        _focus_ring(self)
        if CTK_AVAILABLE:
            # DropdownMenu uses this value to pad each menu item.  The field
            # itself remains compact; only the opened list becomes readable.
            self._dropdown_menu.configure(
                min_character_width=_dropdown_character_width(values)
            )

    def config(self, cnf=None, **kw):
        if cnf is not None:
            if isinstance(cnf, str):
                return self.cget(cnf)
            kw.update(cnf)
        if "textvariable" in kw:
            kw["variable"] = kw.pop("textvariable")
        values = kw.get("values")
        if CTK_AVAILABLE and "width" in kw:
            current_values = values
            if current_values is None:
                try:
                    current_values = self.cget("values")
                except (_tk.TclError, RuntimeError):
                    current_values = ()
            kw["width"] = _combo_control_width(kw["width"], current_values)
        mapped = _pop_tk(kw)
        kw.update(mapped)
        if CTK_AVAILABLE and values is not None:
            # This is an internal DropdownMenu option, not a CTkComboBox
            # constructor option, so apply it after normal option mapping.
            kw["_td2_dropdown_min_character_width"] = _dropdown_character_width(values)
        try:
            popup_width = kw.pop("_td2_dropdown_min_character_width", None)
            super().configure(**kw)
            if CTK_AVAILABLE and popup_width is not None:
                self._dropdown_menu.configure(min_character_width=popup_width)
        except (_tk.TclError, ValueError):
            pass

    configure = config

    def current(self, index=None):
        if index is None:
            try:
                vals = self.cget("values")
                cur = self.get()
            except (_tk.TclError, RuntimeError):
                # A parent rebuild can destroy the native widget before a
                # queued dashboard refresh runs. Treat that stale selection as
                # empty instead of leaking a Tk callback exception.
                return -1
            try:
                return list(vals).index(cur)
            except (ValueError, TypeError):
                return -1
        else:
            vals = self.cget("values")
            if vals and 0 <= index < len(vals):
                self.set(vals[index])


class CtkToplevel(_BASE_TOPLEVEL):
    def __init__(self, master=None, **kw):
        mapped = _pop_tk(kw)
        init_kw = {**mapped}
        for key in ("width", "height"):
            if key in kw:
                init_kw[key] = kw.pop(key)
        super().__init__(master, **init_kw)

    def config(self, **kw):
        mapped = _pop_tk(kw)
        kw.update(mapped)
        try:
            super().configure(**kw)
        except (_tk.TclError, ValueError):
            pass

    configure = config


class CtkScrollbar(_BASE_SCROLLBAR):
    def __init__(self, master=None, **kw):
        mapped = _pop_tk(kw)
        kw.pop("orient", None)
        init_kw = {**mapped}
        if "command" in kw:
            init_kw["command"] = kw.pop("command")
        super().__init__(master, **init_kw)

    def config(self, **kw):
        mapped = _pop_tk(kw)
        kw.update(mapped)
        try:
            super().configure(**kw)
        except (_tk.TclError, ValueError):
            pass

    configure = config
