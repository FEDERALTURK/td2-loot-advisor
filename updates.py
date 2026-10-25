"""Açılıştaki güncelleme denetimi için yardımcılar: eşya kütüphanesi sürümü ve "neler yeni" listesi.

Program güncellemesi updater.py'de, oyun sürümü gameinfo.py'de; burada kütüphane (meta/game_data.json) karşılaştırılır.
"""
import re

import gamedata

N = gamedata.nrm


def lib_version_key(v):
    """'2026-10-25.5' → (2026, 10, 25, 5). Sayısal karşılaştırma ('.10' > '.9')."""
    nums = [int(x) for x in re.findall(r"\d+", str(v or ""))]
    return tuple(nums) or (0,)


def lib_newer(remote, local):
    r, l = lib_version_key(remote), lib_version_key(local)
    n = max(len(r), len(l))
    return r + (0,) * (n - len(r)) > l + (0,) * (n - len(l))


def valid_library(d):
    return isinstance(d, dict) and d.get("schema") == 1 and bool(d.get("attributes")) and bool(d.get("exotics")) and bool(d.get("items"))


def lib_diff(old, new):
    """Yeni kütüphanede eklenenler: {"exotics": [...], "named": [...], "items": [...], "weapons": [...],
    "brands": [...], "gear_sets": [...], "talents": n, "total": n}"""
    old, new = old or {}, new or {}

    def added(key, mapping=False):
        o = {N(x) for x in (old.get(key) or ({} if mapping else []))}
        src = new.get(key) or ({} if mapping else [])
        return [x for x in src if N(x) not in o]
    out = {"exotics": added("exotics"), "named": added("named"), "brands": added("brands"), "gear_sets": added("gear_sets")}
    ex_named = {N(x) for x in out["exotics"] + out["named"]}
    out["items"] = [x for x in added("items", True) if N(x) not in ex_named]
    out["weapons"] = [x for x in added("weapon_index", True) if N(x) not in ex_named]
    out["talents"] = len(added("gear_talents")) + len(added("weapon_talents"))
    out["total"] = sum(len(v) for k, v in out.items() if isinstance(v, list)) + out["talents"]
    return out


def diff_summary(diff, limit=8):
    """Kısa liste: önce exotic ve named (en ilgi çekenler), sonra setler, markalar, parçalar."""
    names = diff["exotics"] + diff["named"] + diff["gear_sets"] + diff["brands"] + diff["weapons"] + diff["items"]
    more = max(0, len(names) - limit)
    return names[:limit], more


def release_highlights(notes, version="", limit=420):
    """Sürüm notlarından o sürümün "neler yeni" maddeleri (indirme tablosu değil).
    Notlarda '**5.0.4 — başlık**' biçimli bölümler aranır; yoksa madde işaretli satırlar kullanılır."""
    text = notes or ""
    secs = list(re.finditer(r"\*\*\s*v?(\d+(?:\.\d+)+)\s*[—–-]\s*([^*]+)\*\*", text))
    pick = next((m for m in secs if version and m.group(1) == str(version).lstrip("vV")), secs[0] if secs else None)
    if pick:
        end = next((m.start() for m in secs if m.start() > pick.start()), len(text))
        body = text[pick.end():end]
        head = pick.group(2).strip()
    else:
        body, head = text, ""
    items = [re.sub(r"\s+", " ", re.sub(r"[*`#>|]+", "", l)).strip(" -•") for l in body.splitlines() if l.strip().startswith(("-", "•", "*"))]
    out = (head + ": " if head else "") + " · ".join(i for i in items if i)
    return (out[:limit - 1] + "…") if len(out) > limit else out
