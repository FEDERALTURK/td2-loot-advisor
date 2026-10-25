"""The Division 2'nin kurulu sürümü: oyun güncellendi mi?

Oyunun exe dosyasının yeri (Ubisoft Connect / Steam kayıtları ya da çalışan oyunun süreci) bulunur ve dosya sürümü
(Windows dosya özellikleri) okunur. Yalnızca dosyanın SÜRÜM BİLGİSİ okunur; oyunun dosyalarına ve belleğine dokunulmaz.

    info = current()          # {"path", "version", "mtime", "source"} ya da None
    changed(old, new)         # oyun güncellendi mi
"""
import ctypes
import os
import re
from pathlib import Path

EXE_NAMES = ("TheDivision2.exe", "TheDivision2_vulkan.exe", "TheDivision2DX12.exe")


def _reg_values(root, path):
    try:
        import winreg
        out = []
        with winreg.OpenKey(root, path) as k:
            i = 0
            while True:
                try: out.append(winreg.EnumKey(k, i)); i += 1
                except OSError: break
        return out
    except Exception:
        return []


def _reg_get(root, path, name):
    try:
        import winreg
        with winreg.OpenKey(root, path) as k:
            return winreg.QueryValueEx(k, name)[0]
    except Exception:
        return None


def install_dirs():
    """Oyunun olası kurulum klasörleri: Ubisoft Connect, Steam, Epic, varsayılan yollar."""
    dirs = []
    if os.name != "nt": return dirs
    import winreg
    for base in (r"SOFTWARE\WOW6432Node\Ubisoft\Launcher\Installs", r"SOFTWARE\Ubisoft\Launcher\Installs"):
        for gid in _reg_values(winreg.HKEY_LOCAL_MACHINE, base):
            d = _reg_get(winreg.HKEY_LOCAL_MACHINE, base + "\\" + gid, "InstallDir")
            if d and "division 2" in d.lower(): dirs.append(("ubisoft", d))
    steam = _reg_get(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath")
    if steam:
        libs = [Path(steam)]
        vdf = Path(steam) / "steamapps" / "libraryfolders.vdf"
        try:
            for m in re.finditer(r'"path"\s+"([^"]+)"', vdf.read_text(encoding="utf-8", errors="ignore")):
                libs.append(Path(m.group(1).replace("\\\\", "\\")))
        except Exception:
            pass
        for lib in libs:
            dirs.append(("steam", str(lib / "steamapps" / "common" / "Tom Clancy's The Division 2")))
    for pf in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if pf:
            dirs.append(("ubisoft", str(Path(pf) / "Ubisoft" / "Ubisoft Game Launcher" / "games" / "Tom Clancy's The Division 2")))
            dirs.append(("epic", str(Path(pf) / "Epic Games" / "TomClancysTheDivision2")))
    seen, out = set(), []
    for src, d in dirs:
        k = d.lower().rstrip("\\/")
        if k not in seen: seen.add(k); out.append((src, d))
    return out


def running_exe():
    """Çalışan oyunun exe yolu (pencere üzerinden), yoksa None."""
    if os.name != "nt": return None
    try:
        import display
        from ctypes import wintypes
        h = display.find_game_hwnd()
        if not h: return None
        u, k = ctypes.windll.user32, ctypes.windll.kernel32
        pid = wintypes.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(pid))
        ph = k.OpenProcess(0x1000, False, pid.value)
        if not ph: return None
        try:
            buf = ctypes.create_unicode_buffer(1024); n = wintypes.DWORD(1024)
            if k.QueryFullProcessImageNameW(ph, 0, buf, ctypes.byref(n)):
                p = buf.value
                return p if os.path.basename(p).lower() in {e.lower() for e in EXE_NAMES} else None
        finally:
            k.CloseHandle(ph)
    except Exception:
        return None
    return None


def file_version(path):
    """Windows dosya sürümü ("1.2.3.4") ya da None."""
    if os.name != "nt": return None
    try:
        ver = ctypes.windll.version
        size = ver.GetFileVersionInfoSizeW(str(path), None)
        if not size: return None
        buf = ctypes.create_string_buffer(size)
        if not ver.GetFileVersionInfoW(str(path), 0, size, buf): return None
        p, ln = ctypes.c_void_p(), ctypes.c_uint()
        if not ver.VerQueryValueW(buf, "\\", ctypes.byref(p), ctypes.byref(ln)): return None

        class VS(ctypes.Structure):
            _fields_ = [("sig", ctypes.c_uint32), ("struc", ctypes.c_uint32), ("ms", ctypes.c_uint32), ("ls", ctypes.c_uint32),
                        ("pms", ctypes.c_uint32), ("pls", ctypes.c_uint32)]
        v = ctypes.cast(p, ctypes.POINTER(VS)).contents
        if v.sig != 0xFEEF04BD: return None
        return f"{v.ms >> 16}.{v.ms & 0xFFFF}.{v.ls >> 16}.{v.ls & 0xFFFF}"
    except Exception:
        return None


def current():
    """Kurulu oyun: önce çalışan süreç, sonra kayıtlı kurulum klasörleri."""
    cands = []
    exe = running_exe()
    if exe: cands.append(("running", exe))
    for src, d in install_dirs():
        for name in EXE_NAMES:
            cands.append((src, str(Path(d) / name)))
    for src, p in cands:
        try:
            st = os.stat(p)
        except OSError:
            continue
        return {"path": p, "version": file_version(p) or "", "mtime": int(st.st_mtime), "size": st.st_size, "source": src}
    return None


GENERIC = {"", "1.0.0.0", "0.0.0.0"}     # oyunun exe'si her yamada aynı genel sürümü taşıyabiliyor


def label(info):
    if not info: return "?"
    import time
    day = time.strftime("%Y-%m-%d", time.localtime(info.get("mtime", 0)))
    v = info.get("version") or ""
    return day if v in GENERIC else f"{v} ({day})"


def changed(old, new):
    """Oyun güncellendi mi? Anlamlı bir sürüm numarası değiştiyse ya da exe'nin tarihi/boyutu değiştiyse."""
    if not old or not new: return False
    ov, nv = old.get("version") or "", new.get("version") or ""
    if ov not in GENERIC and nv not in GENERIC and ov != nv:
        return True
    return (old.get("mtime"), old.get("size")) != (new.get("mtime"), new.get("size"))
