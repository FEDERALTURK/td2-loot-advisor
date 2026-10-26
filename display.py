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
    "426x240": {"label": "426×240 (240p — OCR güvenilmez / unreliable)", "ocr_scale": 6.0, "threshold": 150, "card_w": 0.30, "ui": 0.5, "low": True},
    "640x480": {"label": "640×480 (480p 4:3)", "ocr_scale": 4.0, "threshold": 155, "card_w": 0.32, "ui": 0.6, "low": True},
    "854x480": {"label": "854×480 (480p 16:9)", "ocr_scale": 4.0, "threshold": 155, "card_w": 0.30, "ui": 0.6, "low": True},
    "1280x720": {"label": "1280×720 (720p HD)", "ocr_scale": 3.0, "threshold": 160, "card_w": 0.28, "ui": 0.75},
    "1366x768": {"label": "1366×768 (WXGA)", "ocr_scale": 2.75, "threshold": 160, "card_w": 0.28, "ui": 0.8},
    "1600x900": {"label": "1600×900 (HD+)", "ocr_scale": 2.5, "threshold": 162, "card_w": 0.27, "ui": 0.9},
    "1920x1080": {"label": "1920×1080 (16:9 Full HD)", "ocr_scale": 2.0, "threshold": 165, "card_w": 0.27, "ui": 1.0},
    "2560x1080": {"label": "2560×1080 (21:9)", "ocr_scale": 2.0, "threshold": 165, "card_w": 0.20, "ui": 1.0},
    "2560x1440": {"label": "2560×1440 (16:9 QHD)", "ocr_scale": 1.5, "threshold": 170, "card_w": 0.21, "ui": 1.2},
    "3440x1440": {"label": "3440×1440 (21:9 UWQHD)", "ocr_scale": 1.5, "threshold": 170, "card_w": 0.16, "ui": 1.2},
    "3840x1600": {"label": "3840×1600 (24:10)", "ocr_scale": 1.35, "threshold": 170, "card_w": 0.15, "ui": 1.3},
    "5120x1440": {"label": "5120×1440 (32:9)", "ocr_scale": 1.5, "threshold": 170, "card_w": 0.11, "ui": 1.2},
    "3840x2160": {"label": "3840×2160 (16:9 4K)", "ocr_scale": 1.0, "threshold": 175, "card_w": 0.21, "ui": 1.6},
}


def profile_warning(key, mon_w, mon_h):
    """Seçilen profil monitöre uymuyorsa ya da OCR için çok düşükse uyarı anahtarı."""
    p = PROFILES.get(key)
    if not p: return None
    if p.get("low"): return ("disp.low_res", {})
    w, h = map(int, key.split("x"))
    if (w, h) != (mon_w, mon_h) and abs(h - mon_h) > 100:
        return ("disp.profile_mismatch", {"prof": p["label"], "mon": f"{mon_w}×{mon_h}"})
    return None


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
    """Oyunun çalıştığı ekranın (yoksa ana monitörün) boyutu."""
    g = game_window()
    if g: return g["width"], g["height"]
    try:
        import mss
        with mss.mss() as s:
            m = s.monitors[1]
            return m["width"], m["height"]
    except Exception:
        return 1920, 1080


# ---------------------------------------------------------------- oyun penceresi (yalnız konumu; belleğe dokunulmaz)
GAME_EXES = ("thedivision2.exe", "thedivision2_vulkan.exe", "thedivision2dx12.exe")
_GW_CACHE = {"t": 0.0, "v": None}


_EXE_CACHE = {}            # süreç no → exe adı (oyun izleyici 2 sn'de bir tüm pencerelere bakar; süreç açmak pahalı)


def _exe_of(hwnd):
    try:
        from ctypes import wintypes
        u, k = ctypes.windll.user32, ctypes.windll.kernel32
        pid = wintypes.DWORD(); u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        import time
        now = time.time()
        if now - _EXE_CACHE.get(-1, 0) > 60 or len(_EXE_CACHE) > 512:   # süreç numaraları yeniden kullanılabilir
            _EXE_CACHE.clear(); _EXE_CACHE[-1] = now
        if pid.value in _EXE_CACHE: return _EXE_CACHE[pid.value]
        name = _exe_query(k, pid.value)
        if name: _EXE_CACHE[pid.value] = name
        return name
    except Exception:
        return ""


def _exe_query(k, pid):
    try:
        from ctypes import wintypes
        h = k.OpenProcess(0x1000, False, pid)              # PROCESS_QUERY_LIMITED_INFORMATION
        if not h: return ""
        try:
            buf = ctypes.create_unicode_buffer(520); n = wintypes.DWORD(520)
            ok = k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
            return os.path.basename(buf.value).lower() if ok else ""
        finally:
            k.CloseHandle(h)
    except Exception:
        return ""


def find_game_hwnd():
    """The Division 2 penceresi: önce oyunun exe adına, sonra başlığa göre. Simge durumundaki pencere sayılmaz."""
    if os.name != "nt": return None
    try:
        from ctypes import wintypes
        u = ctypes.windll.user32
        found = []
        CB = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def cb(h, _):
            if not u.IsWindowVisible(h) or u.IsIconic(h): return True
            n = u.GetWindowTextLengthW(h)
            buf = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, buf, n + 1)
            title = buf.value.lower()
            if "loot advisor" in title: return True
            exe = _exe_of(h)
            score = 2 if exe in GAME_EXES else (1 if ("division 2" in title or "division2" in title) else 0)
            if score: found.append((score, h))
            return True
        u.EnumWindows(CB(cb), 0)
        return max(found)[1] if found else None
    except Exception:
        return None


def window_client_rect(hwnd):
    """İstemci alanı ekran koordinatlarında (fiziksel piksel; süreç DPI-aware olmalı)."""
    try:
        from ctypes import wintypes
        u = ctypes.windll.user32
        rc = wintypes.RECT()
        if not u.GetClientRect(hwnd, ctypes.byref(rc)): return None
        pt = wintypes.POINT(0, 0)
        u.ClientToScreen(hwnd, ctypes.byref(pt))
        w, h = rc.right - rc.left, rc.bottom - rc.top
        if w < 320 or h < 200: return None
        return {"left": pt.x, "top": pt.y, "width": w, "height": h}
    except Exception:
        return None


def game_window(max_age=2.0):
    """Oyun penceresinin istemci alanı {"left","top","width","height","hwnd"} ya da None (oyun kapalı / simge).
    Hangi monitörde, hangi modda (tam ekran / kenarlıksız / pencere) olursa olsun oyunun gerçek alanı."""
    import time
    now = time.time()
    if now - _GW_CACHE["t"] < max_age: return _GW_CACHE["v"]
    v = None
    h = find_game_hwnd()
    if h:
        r = window_client_rect(h)
        if r: v = {**r, "hwnd": h}
    _GW_CACHE.update(t=now, v=v)
    return v


def clamp_to_screen(r, monitors):
    """Bölgeyi sanal ekranla kesiştir (pencere ekran dışına taşmışsa yakalama hata vermesin)."""
    allm = monitors[0]
    L, T = max(r["left"], allm["left"]), max(r["top"], allm["top"])
    R = min(r["left"] + r["width"], allm["left"] + allm["width"])
    B = min(r["top"] + r["height"], allm["top"] + allm["height"])
    if R - L < 100 or B - T < 100: return None
    return {"left": L, "top": T, "width": R - L, "height": B - T}


def monitor_of(r, monitors):
    """Bölgenin merkezinin bulunduğu monitör (mss monitör sözlüğü)."""
    cx, cy = r["left"] + r["width"] // 2, r["top"] + r["height"] // 2
    for m in monitors[1:]:
        if m["left"] <= cx < m["left"] + m["width"] and m["top"] <= cy < m["top"] + m["height"]:
            return m
    return monitors[1] if len(monitors) > 1 else monitors[0]


# ---------------------------------------------------------------- dinamik profil
# Hazır listede olmayan her çözünürlük için değerler oyunun gerçek boyutundan hesaplanır
# (tablodaki ölçümlerden türetildi: kart genişliği ≈ yüksekliğin %38-48'i, OCR ölçeği ≈ 2160 / yükseklik).
def dynamic_profile(width, height):
    h, w = max(1, int(height)), max(1, int(width))
    def lerp(x, pts):
        pts = sorted(pts)
        if x <= pts[0][0]: return pts[0][1]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x <= x1: return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return pts[-1][1]
    card_h = lerp(h, [(480, 0.50), (1080, 0.48), (1440, 0.38), (2160, 0.37)])
    return {"label": f"{w}×{h} (otomatik / auto)",
            "ocr_scale": round(max(1.0, min(6.0, 2160 / h)), 2),
            "threshold": int(round(lerp(h, [(240, 150), (480, 155), (720, 160), (1080, 165), (1440, 170), (2160, 175)]))),
            "card_w": round(max(0.10, min(0.34, card_h * h / w)), 3),
            "ui": round(max(0.5, min(1.6, lerp(h, [(240, 0.5), (480, 0.6), (720, 0.75), (1080, 1.0), (1440, 1.2), (2160, 1.6)]))), 2),
            "low": h < 600, "dynamic": True}


def profile_for(width, height):
    """(anahtar, profil): tam eşleşen hazır profil, yoksa oyunun boyutundan hesaplanan profil."""
    key = f"{width}x{height}"
    if key in PROFILES: return key, PROFILES[key]
    return key, dynamic_profile(width, height)


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
