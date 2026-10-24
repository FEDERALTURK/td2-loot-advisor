"""Build paylaşımı: build'i kısa bir koda (ve QR'a) çevir, koddan geri al.

    code = encode(build)   -> "TD2B-eJyr…"
    build = decode(code)   -> dict (doğrulanmış, yalnız bilinen alanlar)
Kod kendi içinde tüm bilgiyi taşır; sunucu gerekmez. Web sayfası hazır olunca aynı kod bir bağlantının sonuna eklenebilir.
"""
import base64
import json
import zlib

PREFIX = "TD2B-"
FIELDS = ("name", "sets_or_brands", "items", "attributes", "talents", "weapons", "slots", "summary")
MAX_RAW = 32 * 1024


def _clean(build):
    b = {k: build[k] for k in FIELDS if k in build and build[k] not in (None, "", [], {})}
    summ = (build.get("meta") or {}).get("summary") or build.get("summary")
    if summ: b["summary"] = summ if isinstance(summ, dict) else {"en": str(summ)}
    return b


def encode(build):
    raw = json.dumps(_clean(build), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return PREFIX + base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode().rstrip("=")


def decode(code):
    """Koddan build. Hatalı / çok büyük / beklenmeyen içerikte ValueError."""
    code = "".join((code or "").split())
    if "#" in code: code = code.split("#", 1)[1]           # bağlantı biçimi: https://…/b#TD2B-…
    if not code.startswith(PREFIX): raise ValueError("not a build code")
    body = code[len(PREFIX):]
    try:
        comp = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        d = zlib.decompressobj()
        raw = d.decompress(comp, MAX_RAW + 1)
        if len(raw) > MAX_RAW or d.unconsumed_tail: raise ValueError("too large")
        b = json.loads(raw.decode("utf-8"))
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"broken code: {e}")
    if not isinstance(b, dict) or not isinstance(b.get("name"), str) or not b["name"].strip():
        raise ValueError("missing name")
    out = {"name": b["name"].strip()[:80]}
    if isinstance(b.get("sets_or_brands"), list): out["sets_or_brands"] = [str(x)[:60] for x in b["sets_or_brands"][:8]]
    if isinstance(b.get("items"), list): out["items"] = [str(x)[:60] for x in b["items"][:12]]
    if isinstance(b.get("slots"), list): out["slots"] = [str(x)[:20] for x in b["slots"][:8]]
    if isinstance(b.get("attributes"), dict):
        out["attributes"] = {str(k)[:40]: {"weight": float((v or {}).get("weight", 1)) if isinstance(v, dict) else 1.0}
                             | ({"good_at": float(v["good_at"])} if isinstance(v, dict) and v.get("good_at") else {})
                             for k, v in list(b["attributes"].items())[:20]}
    if isinstance(b.get("talents"), dict):
        out["talents"] = {str(k)[:60]: float(v) if isinstance(v, (int, float)) else 1.0 for k, v in list(b["talents"].items())[:12]}
    if isinstance(b.get("weapons"), dict):
        w = b["weapons"]; out["weapons"] = {"types": [str(x)[:30] for x in (w.get("types") or [])[:4]]}
    if isinstance(b.get("summary"), dict):
        out["meta"] = {"summary": {str(k)[:5]: str(v)[:600] for k, v in list(b["summary"].items())[:12]}, "shared": True}
    return out
