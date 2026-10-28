"""
TD2 Loot Advisor — çeviri motoru / translation engine.

Dil dosyaları `lang/<kod>.json` içinde durur. Yeni bir dil eklemek için
`lang/en.json`'u kopyalayıp çevir ve dosyaya dil kodunu ver (örn. `nl.json`).
Uygulama klasördeki tüm .json dosyalarını kendiliğinden bulur.

To add a language: copy `lang/en.json`, translate the values, and save it as
`lang/<code>.json`. The app discovers every .json file in that folder.

Dosya biçimi / file format:
{
  "__meta__": {"name": "Français", "english_name": "French"},
  "__task_dict__": [["control point", "point de contrôle"], ...],
  "some.key": "Translated text with {placeholder}"
}

Arama sırası / lookup order: seçili dil -> İngilizce -> anahtarın kendisi.
"""
import json
import locale
import os
from pathlib import Path

DEFAULT_LANG = "en"

_dir = None          # lang klasörü
_cache = {}          # kod -> yüklenmiş sözlük
_current = {}        # seçili dilin sözlüğü
_fallback = {}       # İngilizce sözlük
_current_code = DEFAULT_LANG
_missing = set()     # bulunamayan anahtarlar (hata ayıklama için)


def init(base_dir):
    """lang klasörünü tanıt ve İngilizceyi yedek olarak yükle."""
    global _dir, _fallback
    _dir = Path(base_dir) / "lang"
    _fallback = _load(DEFAULT_LANG)
    return _dir


def _load(code):
    """Bir dil dosyasını diskten oku. Bulunamazsa boş sözlük döner."""
    if code in _cache:
        return _cache[code]
    data = {}
    if _dir:
        path = _dir / f"{code}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            data = {}
        except Exception as e:  # bozuk JSON uygulamayı çökertmesin
            print(f"[i18n] {path} okunamadi / could not be read: {e}")
            data = {}
    _cache[code] = data
    return data


def available_languages():
    """[(kod, görünen ad)] listesi; ada göre sıralı."""
    out = []
    if _dir and _dir.is_dir():
        for p in sorted(_dir.glob("*.json")):
            code = p.stem
            try:
                meta = json.loads(p.read_text(encoding="utf-8")).get("__meta__", {})
            except Exception:
                meta = {}
            out.append((code, meta.get("name") or code.upper()))
    if not out:
        out = [(DEFAULT_LANG, "English")]
    return sorted(out, key=lambda x: x[1].lower())


def detect_language():
    """İşletim sisteminin dilini tahmin et; dosyası yoksa İngilizceye düş."""
    codes = [c for c, _ in available_languages()]
    try:
        loc = locale.getdefaultlocale()[0] or ""
    except Exception:
        loc = ""
    loc = (loc or os.environ.get("LANG", "")).replace("-", "_")
    if loc:
        short = loc.split("_")[0].lower()
        if loc.lower() in codes:
            return loc.lower()
        if short in codes:
            return short
    return DEFAULT_LANG


def set_language(code):
    """Seçili dili değiştir. Dosya yoksa İngilizce kullanılır."""
    global _current, _current_code
    _current = _load(code)
    _current_code = code if _current else DEFAULT_LANG
    if not _current:
        _current = _fallback
    return _current_code


def current_language():
    return _current_code


def language_name(code=None):
    code = code or _current_code
    return _load(code).get("__meta__", {}).get("name", code.upper())


def english_name(code=None):
    """Yapay zekaya hangi dilde yanıt vereceğini söylemek için (örn. 'French')."""
    code = code or _current_code
    meta = _load(code).get("__meta__", {})
    return meta.get("english_name") or meta.get("name") or code


def t(key, /, **kw):
    """Anahtarı çevir. Yer tutucular {ad} biçiminde doldurulur.

    `key` bilerek yalnızca konumsaldır (/): böylece bir metinde {key} yer
    tutucusu kullanılabilir ve t("state.key", key="F8") çağrısı çakışmaz.
    """
    s = _current.get(key)
    if s is None:
        s = _fallback.get(key)
    if s is None:
        _missing.add(key)
        s = key
    if kw:
        try:
            return s.format(**kw)
        except (KeyError, IndexError, ValueError):
            return s  # bozuk yer tutucu çeviriyi çökertmesin
    return s


def task_dictionary():
    """Yapay zeka yokken kullanılan İngilizce->hedef dil sözlüğü.

    Dil dosyasında yoksa boş liste döner; o durumda metin olduğu gibi kalır.
    """
    d = _current.get("__task_dict__")
    if not isinstance(d, list):
        return []
    return [(a, b) for a, b in d if isinstance(a, str) and isinstance(b, str)]


def missing_keys():
    """Çalışma sırasında karşılığı bulunamayan anahtarlar."""
    return sorted(_missing)
