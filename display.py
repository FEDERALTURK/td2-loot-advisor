"""Ekran, çözünürlük profilleri ve oyun ayarları (bellek değil, oyunun kendi ayar dosyası).

Benzer projelerden alınan dersler:
- Diablo4Companion: her çözünürlük için hazır "sistem ön ayarı" (OCR ölçeği, gürültü eşiği, kart genişliği).
- d4lf: oyun içi ayar şartları (HDR kapalı, İngilizce, kenarlıksız pencere) kontrol edilip kullanıcı uyarılır.
- RatScanner: oyun üstü bilgi kartı için kenarlıksız/pencereli mod gerekir.

Oyun ayarları `Belgeler\\My Games\\Tom Clancy's The Division 2\\state.cfg` (+ graphic settings.cfg, ui config.cfg) dosyalarından OKUNUR;
dosyaya yazılmaz, oyuna/belleğe dokunulmaz.
"""
import ctypes
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------- DPI
def set_dpi_aware():
    """Windows ölçeklendirmesinde (%125, %150) koordinatların kaymaması için. Tk'dan ÖNCE çağrılmalı."""
    if os.name != "nt": return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)      # per-monitor
    except Exception:
        try: ctypes.windll.user32.SetProcessDPIAware()
        except Exception: pass


# ---------------------------------------------------------------- çözünürlük profilleri
# ocr_scale: kart görüntüsünün büyütme oranı; threshold: yazı/zemin ayırma eşiği (0-255);
# card_w: kartın ekran genişliğine oranı (kart bulunamazsa tahmin); ui: arayüz/bindirme ölçeği
PROFILES = {
    "1920x1080": {"label": "1920×1080 (16:9 Full HD)", "ocr_scale": 2.0, "threshold": 165, "card_w": 0.27, "ui": 1.0},
    "2560x1080": {"label": "2560×1080 (21:9)", "ocr_scale": 2.0, "threshold": 165, "card_w": 0.20, "ui": 1.0},
    "2560x1440": {"label": "2560×1440 (16:9 QHD)", "ocr_scale": 1.5, "threshold": 170, "card_w": 0.21, "ui": 1.2},
    "3440x1440": {"label": "3440×1440 (21:9 UWQHD)", "ocr_scale": 1.5, "threshold": 170, "card_w": 0.16, "ui": 1.2},
    "3840x1600": {"label": "3840×1600 (24:10)", "ocr_scale": 1.35, "threshold": 170, "card_w": 0.15, "ui": 1.3},
    "5120x1440": {"label": "5120×1440 (32:9)", "ocr_scale": 1.5, "threshold": 170, "card_w": 0.11, "ui": 1.2},
    "3840x2160": {"label": "3840×2160 (16:9 4K)", "ocr_scale": 1.0, "threshold": 175, "card_w": 0.21, "ui": 1.6},
}


def detect_profile(width, height):
    """En yakın profil anahtarı (yükseklik + en-boy oranına göre)."""
    key = f"{width}x{height}"
    if key in PROFILES: return key
    ar = width / max(1, height)
    def cost(k):
        w, h = map(int, k.split("x"))
        return abs(h - height) / height + abs(w / h - ar)
    return min(PROFILES, key=cost)


def monitor_size():
    try:
        import mss
        with mss.mss() as s:
            m = s.monitors[1]
            return m["width"], m["height"]
    except Exception:
        return 1920, 1080


# ---------------------------------------------------------------- oyun ayar dosyası (yalnız okuma)
def settings_dir():
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    for docs in (home / "Documents", home / "OneDrive" / "Documents", home / "OneDrive" / "Belgeler", home / "Belgeler"):
        d = docs / "My Games" / "Tom Clancy's The Division 2"
        if d.is_dir(): return d
    return None


def parse_cfg(text):
    """Snowdrop (The Division 2) .cfg dosyaları Lua tablosu biçimindedir: { key = value, ["a b"] = 1, t = { … } }.
    Küçük, güvenli bir ayrıştırıcı (kod çalıştırmaz)."""
    tok = re.findall(r'"(?:[^"\\]|\\.)*"|\[|\]|\{|\}|=|,|[^\s\[\]{}=,]+', text)
    pos = [0]

    def val():
        t = tok[pos[0]]; pos[0] += 1
        if t == "{": return table()
        if t.startswith('"'): return t[1:-1]
        if t == "true": return True
        if t == "false": return False
        try: return int(t)
        except ValueError:
            try: return float(t)
            except ValueError: return t

    def table():
        out, arr = {}, []
        while pos[0] < len(tok) and tok[pos[0]] != "}":
            t = tok[pos[0]]
            if t == ",": pos[0] += 1; continue
            if t == "[":                                    # ["anahtar"] = değer
                pos[0] += 1; k = val()                      # anahtar
                pos[0] += 2                                 # "]" ve "="
                out[k] = val(); continue
            if pos[0] + 1 < len(tok) and tok[pos[0] + 1] == "=":
                k = t.strip('"'); pos[0] += 2; out[k] = val(); continue
            arr.append(val())
        pos[0] += 1
        return out if out or not arr else arr

    if not tok or tok[0] != "{": return {}
    pos[0] = 1
    try: return table()
    except (IndexError, ValueError): return {}


def _read_cfg(path):
    try: return parse_cfg(Path(path).read_text(encoding="utf-8", errors="ignore"))
    except OSError: return {}


def read_game_settings(folder=None):
    """{'file', 'width', 'height', 'refresh', 'display_mode', 'hdr', 'language', 'view_scale', 'enlarge_ui', 'dx12'} ya da None.
    The Division 2: state.cfg (çözünürlük, pencere modu, HDR, dil), graphic settings.cfg (görüntü ölçeği),
    ui config.cfg (arayüz büyütme). Eski sürümler için GFXSettings*.xml de denenir. Hepsi YALNIZCA okunur."""
    d = Path(folder) if folder else settings_dir()
    if not d or not d.is_dir(): return None
    state = d / "state.cfg"
    if state.exists():
        st = _read_cfg(state)
        g = st.get("graphics", {}) if isinstance(st, dict) else {}
        if not g: return {"file": str(state), "error": "unreadable"}
        windowed = bool(g.get("windowed"))
        act = g.get("windowedSettings" if windowed else "fullscreenSettings", {}) or {}
        out = {"file": str(state), "options": {}}
        if act.get("width"): out["width"], out["height"] = int(act["width"]), int(act.get("height", 0))
        try: out["refresh"] = round(act["refresh-rate-numerator"] / max(1, act["refresh-rate-denominator"]))
        except (KeyError, TypeError): pass
        out["display_mode"] = ("Borderless" if act.get("fullscreen") else "Windowed") if windowed else "Fullscreen"
        hdr = g.get("hdr")
        out["hdr"] = None if hdr is None else str(hdr).lower() not in ("off", "0", "false")
        out["dx12"] = g.get("dx12")
        loc = st.get("localization", {})
        if isinstance(loc, dict) and "mainLanguage" in loc: out["language"] = loc["mainLanguage"]
        gs = _read_cfg(d / "graphic settings.cfg")
        if isinstance(gs, dict):
            out["view_scale"] = gs.get("view scale"); out["preset"] = gs.get("preset")
        ui = _read_cfg(d / "ui config.cfg")
        if isinstance(ui, dict):
            out["enlarge_ui"] = ui.get("enlarge ui"); out["dual_monitor"] = ui.get("dual monitor mode")
        return out
    files = sorted(d.glob("GFXSettings*.xml"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files: return None
    f = files[0]
    try:
        root = ET.fromstring(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {"file": str(f), "error": "unreadable"}
    out = {"file": str(f), "options": {}}
    for el in root.iter():
        tag = el.tag.upper()
        a = {k.lower(): v for k, v in el.attrib.items()}
        if tag == "RESOLUTION" or ("width" in a and "height" in a):
            try:
                out["width"], out["height"] = int(float(a.get("width"))), int(float(a.get("height")))
                if a.get("refreshrate"): out["refresh"] = a["refreshrate"]
            except (TypeError, ValueError):
                pass
        if "name" in a and "value" in a:
            out["options"][a["name"]] = a["value"]
    o = {k.lower(): v for k, v in out["options"].items()}
    out["display_mode"] = o.get("displaymode") or o.get("windowmode") or ("Windowed" if o.get("windowed") == "true" else None)
    hdr = next((v for k, v in o.items() if "hdr" in k), None)
    out["hdr"] = None if hdr is None else str(hdr).lower() in ("1", "true", "on", "enabled")
    return out


def recommendations(game, mon_w, mon_h):
    """Uyarı anahtarları (çeviri anahtarı, parametreler) listesi."""
    tips = []
    if not game:
        return [("disp.no_game_file", {})]
    if game.get("error"):
        return [("disp.game_file_bad", {})]
    if game.get("hdr"):
        tips.append(("disp.hdr_on", {}))
    mode = (game.get("display_mode") or "").lower()
    if mode in ("fullscreen", "exclusive", "full screen"):
        tips.append(("disp.exclusive", {}))
    if game.get("width") and game.get("height") and (game["width"], game["height"]) != (mon_w, mon_h):
        tips.append(("disp.res_mismatch", {"game": f"{game['width']}×{game['height']}", "mon": f"{mon_w}×{mon_h}"}))
    if game.get("language") not in (None, 0):
        tips.append(("disp.lang_not_en", {"n": game["language"]}))
    if game.get("enlarge_ui"):
        tips.append(("disp.enlarge_ui", {}))
    if not tips:
        tips.append(("disp.all_good", {}))
    return tips
