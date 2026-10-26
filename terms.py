"""Çeviride geçen oyun terimlerini bulur ve kısa açıklamasını verir.

Kaynaklar: Ansiklopedi (egzotik, adlı eşya, set, marka, yetenek) + meta/terms.json (genel terimler).
Eşleşme İngilizce özgün metin üzerinde yapılır (oyun adları çeviride de korunduğu için Türkçe metinde de görünürler).

    tf = TermFinder(encyclopedia, terms_json_paths, lang="tr", localize=fn)
    tf.find("Equip Striker's Battlegear and open an Exotic Cache")   → [{"name","cat","text"}, ...]
"""
import json
import re
from pathlib import Path

CAT_LABEL = {"exotic": "Egzotik", "named": "Adlı", "gear_set": "Set", "brand": "Marka", "talent": "Yetenek", "term": "Terim"}


def _load(paths):
    for p in paths:
        try: return json.loads(Path(p).read_text(encoding="utf-8")).get("terms", {})
        except (OSError, ValueError): continue
    return {}


class TermFinder:
    def __init__(self, enc=None, term_paths=(), lang="tr", localize=None):
        self.lang, self.localize = lang, localize
        self.entries = {}
        for e in (enc.entries if enc else []):
            if len(e["name"]) >= 4: self.entries.setdefault(e["name"].lower(), e)
        for name, d in _load(term_paths).items():
            self.entries[name.lower()] = {"cat": "term", "name": name, "texts": d}
        names = sorted(self.entries, key=len, reverse=True)
        self._re = re.compile("|".join(r"(?<![\w'])" + re.escape(n) + r"(?![\w])" for n in names), re.I) if names else None

    def describe(self, e, limit=220):
        """Girişin kısa açıklaması (seçili dilde varsa)."""
        if e["cat"] == "term":
            tx = e["texts"]; return tx.get(self.lang) or tx.get("en") or ""
        parts = []
        if e["cat"] in ("gear_set", "brand"):
            parts = [b for b in (e.get("bonuses") or [])][:4]
            text = " · ".join(parts)
        else:
            text = e.get("desc") or ""
            if self.localize and text:
                try: text = self.localize(e, text) or text
                except Exception: pass
            head = " / ".join(x for x in (e.get("slot"), e.get("brand") or e.get("gear_set"), e.get("talent")) if x)
            if head: text = head + (" — " + text if text else "")
        return (text[:limit - 1] + "…") if len(text) > limit else text

    def find(self, text, max_n=6):
        if not self._re or not text: return []
        out, seen = [], set()
        for m in self._re.finditer(text):
            e = self.entries.get(m.group(0).lower())
            if not e or e["name"] in seen: continue
            seen.add(e["name"])
            out.append({"name": e["name"], "cat": e["cat"], "label": CAT_LABEL.get(e["cat"], ""), "text": self.describe(e)})
            if len(out) >= max_n: break
        return out
