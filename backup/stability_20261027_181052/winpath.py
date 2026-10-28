"""Windows'ta Türkçe / ASCII dışı kullanıcı adları (C:\\Users\\Şükrü\\...) için güvenli yol.

Bazı yerel kütüphaneler (CTranslate2, SentencePiece) dosya yolunu dar karakterle açar; kullanıcı klasöründe ş, ğ, ı, ü
gibi harfler varsa model yüklenemez. Çözüm sırası:
  1) yol zaten ASCII ise olduğu gibi,
  2) Windows kısa yolu (8.3, ör. C:\\Users\\SUKRU~1\\...) ASCII ise o,
  3) yoksa model klasörü bir kez ortak, ASCII bir yere kopyalanır (C:\\Users\\Public\\TD2LootAdvisor\\<ad>) ve oradan açılır.
"""
import os
import shutil
from pathlib import Path


def is_ascii(s):
    try: str(s).encode("ascii"); return True
    except UnicodeEncodeError: return False


def short_path(p):
    if os.name != "nt": return str(p)
    try:
        import ctypes
        from ctypes import wintypes
        f = ctypes.windll.kernel32.GetShortPathNameW
        f.argtypes = (wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD); f.restype = wintypes.DWORD
        buf = ctypes.create_unicode_buffer(1024)
        n = f(str(p), buf, 1024)
        return buf.value if 0 < n < 1024 else str(p)
    except Exception:
        return str(p)


def public_root():
    base = os.environ.get("PUBLIC") or r"C:\Users\Public"
    return Path(base) / "TD2LootAdvisor"


def safe_dir(p, name=None):
    """Yerel kütüphanelere verilecek klasör yolu (str)."""
    p = Path(p)
    if os.name != "nt" or is_ascii(p): return str(p)
    sp = short_path(p)
    if is_ascii(sp) and Path(sp).exists(): return sp
    dst = public_root() / (name or p.name)
    if not is_ascii(dst): return str(p)                       # yapılacak bir şey yok
    try:
        src_files = {f.name: f.stat().st_size for f in p.iterdir() if f.is_file()}
        have = {f.name: f.stat().st_size for f in dst.iterdir() if f.is_file()} if dst.exists() else {}
        if have != src_files:
            dst.mkdir(parents=True, exist_ok=True)
            for f in p.iterdir():
                if f.is_file(): shutil.copy2(f, dst / f.name)
        return str(dst)
    except OSError:
        return str(p)
