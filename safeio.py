"""Güvenli dosya yazımı ve saklanan gizli ayarlar.

- write_json(path, obj): önce geçici dosyaya yazar, diske işler (fsync), sonra tek adımda değiştirir. Program yazarken
  kapanırsa ya da iki iş parçacığı aynı anda kaydederse dosya bozulmaz. Günde bir yedek (.bak) tutar.
- read_json(path, default): bozuksa yedekten (.bak) okur.
- Gizli ayarlar (yapay zekâ API anahtarları, Discord webhook, ntfy konusu, yerel belirteçler) diskte Windows'un kullanıcıya
  bağlı şifrelemesiyle (DPAPI) saklanır: builds.json paylaşılsa ya da başka bir hesaptan okunsa bile açılamaz.
  Bellekte düz metindir; yalnız dosyada şifreli. Windows dışında olduğu gibi kalır.
"""
import base64
import json
import os
import shutil
import sys
import threading
import time
from pathlib import Path

_LOCKS = {}
_LOCKS_GUARD = threading.Lock()
SECRET_KEYS = ("claude_api_key", "openai_api_key", "push_webhook", "push_topic", "api_token", "tr_screen_token")
PREFIX = "dpapi:"
_ENTROPY = b"td2-loot-advisor/settings"


def _lock(path):
    k = str(Path(path).resolve())
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(k, threading.RLock())


def _dumps(obj, indent):
    for _ in range(5):                       # başka iş parçacığı sözlüğü değiştirirken dökülürse yeniden dene
        try: return json.dumps(obj, indent=indent, ensure_ascii=False)
        except RuntimeError: time.sleep(0.01)
    return json.dumps(json.loads(json.dumps(obj, default=str)), indent=indent, ensure_ascii=False)


def write_json(path, obj, indent=2, backup=True):
    path = Path(path)
    with _lock(path):
        data = _dumps(obj, indent)
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(data); f.flush()
            try: os.fsync(f.fileno())
            except OSError: pass
        if backup and path.exists():
            bak = path.with_name(path.name + ".bak")
            try:
                if not bak.exists() or time.time() - bak.stat().st_mtime > 86400:
                    json.loads(path.read_text(encoding="utf-8"))          # yalnız sağlam dosya yedeklenir
                    shutil.copy2(path, bak)
            except (OSError, ValueError):
                pass
        for i in range(10):                  # Windows: virüs tarayıcı dosyayı kısa süre tutabilir
            try: os.replace(tmp, path); break
            except PermissionError:
                if i == 9: raise
                time.sleep(0.05)


def read_json(path, default=None):
    path = Path(path)
    for p in (path, path.with_name(path.name + ".bak")):
        try: return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError): continue
    return default


# ---------------------------------------------------------------- gizli ayarlar (DPAPI)
def _dpapi(data, protect):
    import ctypes
    from ctypes import wintypes

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    def blob(b):
        buf = ctypes.create_string_buffer(b, len(b))
        return BLOB(len(b), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf

    src, _k1 = blob(data); ent, _k2 = blob(_ENTROPY); out = BLOB()
    fn = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
    if not fn(ctypes.byref(src), None, ctypes.byref(ent), None, None, 0x1, ctypes.byref(out)):
        raise OSError("DPAPI")
    try: return ctypes.string_at(out.pbData, out.cbData)
    finally: ctypes.windll.kernel32.LocalFree(out.pbData)


def protect(value):
    if not value or not isinstance(value, str) or value.startswith(PREFIX) or sys.platform != "win32": return value
    try: return PREFIX + base64.b64encode(_dpapi(value.encode("utf-8"), True)).decode()
    except Exception: return value


def unprotect(value):
    if not isinstance(value, str) or not value.startswith(PREFIX): return value
    if sys.platform != "win32": return ""
    try: return _dpapi(base64.b64decode(value[len(PREFIX):]), False).decode("utf-8")
    except Exception: return ""                  # başka bilgisayar / kullanıcı: anahtar yeniden girilmeli


def seal_settings(cfg):
    """Kaydedilecek kopya: gizli ayarlar şifreli (bellekteki cfg değişmez)."""
    st = cfg.get("settings") or {}
    if not any(st.get(k) for k in SECRET_KEYS): return cfg
    out = dict(cfg); out["settings"] = dict(st)
    for k in SECRET_KEYS:
        if st.get(k): out["settings"][k] = protect(st[k])
    return out


def open_settings(cfg):
    st = cfg.get("settings") or {}
    for k in SECRET_KEYS:
        if isinstance(st.get(k), str) and st[k].startswith(PREFIX): st[k] = unprotect(st[k])
    return cfg
