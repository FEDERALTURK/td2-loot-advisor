"""Ekran, çözünürlük profilleri ve oyun ayarları (bellek değil, oyunun kendi ayar dosyası).

Benzer projelerden alınan dersler:
- Diablo4Companion: her çözünürlük için hazır "sistem ön ayarı" (OCR ölçeği, gürültü eşiği, kart genişliği).
- d4lf: oyun içi ayar şartları (HDR kapalı, İngilizce, kenarlıksız pencere) kontrol edilip kullanıcı uyarılır.
- RatScanner: oyun üstü bilgi kartı için kenarlıksız/pencereli mod gerekir.

Oyun ayarları `Belgeler\\My Games\\Tom Clancy's The Division 2\\GFXSettings*.xml` dosyasından OKUNUR;
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


def read_game_settings(folder=None):
    """{'file', 'width', 'height', 'refresh', 'display_mode', 'hdr', 'options'} ya da None."""
    d = Path(folder) if folder else settings_dir()
    if not d or not d.is_dir(): return None
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
    if not tips:
        tips.append(("disp.all_good", {}))
    return tips
