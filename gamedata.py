"""Oyun verisi ve eşya tanıma motoru.

OCR (ekran okuma) gürültülüdür: "Strikers nHowster", "DlLUCsercett" gibi bozuk metinler çıkar.
Bu modül okunan metni gerçek oyun verisiyle karşılaştırarak düzeltir:

- Bilinen adlar: tüm gear set'ler, marka setleri, egzotikler, named eşyalar (wiki'den).
- Bilinen talent'ler (silah + ekipman), attribute adları ve **en yüksek değerleri**
  (ör. Critical Hit Chance en fazla %6, Weapon Damage çekirdek %15; Prototype ×1.5).
- Eşyanın türü (silah / ekipman), yuvası, nadirliği, markası/seti; her attribute'un
  en yüksek değere göre yüzdesi ("rulo kalitesi").

Veri `meta/game_data.json` dosyasından gelir; ortak liste (GitHub) yenisini getirebilir.
Oyunun belleğine dokunulmaz, yalnızca ekrandaki yazı okunur.
"""
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

NUMBER = re.compile(r"([+-]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?)\s*(k|%)?", re.I)


def nrm(s):
    s = (s or "").lower().replace("’", "'").replace("č", "c").replace("ý", "y").replace("é", "e")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9&' ]+", " ", s)).strip()


def ratio(a, b):
    sm = SequenceMatcher(None, a, b)
    if sm.real_quick_ratio() < 0.6 or sm.quick_ratio() < 0.6:   # hızlı eleme
        return 0.0
    return sm.ratio()


def best_window(line, target):
    """Satırın içinde hedefe en çok benzeyen kelime penceresinin benzerliği (0-1)."""
    if not line or not target: return 0.0
    if target in line: return 1.0
    words, tw = line.split(), len(target.split())
    best = ratio(line, target) if abs(len(line) - len(target)) <= 4 else 0.0
    for n in {tw, tw + 1, max(1, tw - 1)}:
        for i in range(0, max(1, len(words) - n + 1)):
            best = max(best, ratio(" ".join(words[i:i + n]), target))
    return best


class GameData:
    def __init__(self, *paths):
        self.data = {}
        for p in paths:
            try:
                d = json.loads(Path(p).read_text(encoding="utf-8"))
                if d.get("schema") == 1 and d.get("attributes"):
                    if not self.data or str(d.get("version", "")) > str(self.data.get("version", "")):
                        self.data = d
            except Exception:
                continue
        d = self.data
        self.names = []                                   # (normal, kanonik, tür)
        for kind, key in (("exotic", "exotics"), ("named", "named"), ("gear_set", "gear_sets"), ("brand", "brands")):
            for n in d.get(key, []):
                self.names.append((nrm(n), n, kind))
        self.talents = [(nrm(n), n, "gear") for n in d.get("gear_talents", [])] + \
                       [(nrm(n), n, "weapon") for n in d.get("weapon_talents", [])]
        self.attr_alias = {}
        for k, a in d.get("attributes", {}).items():
            for al in a.get("aliases", []):
                self.attr_alias[nrm(al)] = k
        self.weapon_types = [nrm(w) for w in d.get("weapon_types", [])]
        self.slots = {nrm(k): v for k, v in d.get("slots", {}).items()}

    @property
    def ok(self):
        return bool(self.data)

    def max_of(self, key, prototype=False):
        m = self.data.get("attributes", {}).get(key, {}).get("max")
        return m * (self.data.get("prototype_multiplier", 1.5) if prototype else 1) if m else None

    # ------------------------------------------------------------ tanıma
    def match_name(self, lines, cutoff=0.82):
        """Satırlarda geçen en iyi bilinen ad: (kanonik, tür, benzerlik) ya da (None, None, 0)."""
        best = (None, None, 0.0)
        for i, line in enumerate(lines[:14]):                 # ad ve marka kartın üst kısmında
            l = nrm(line)
            if len(l) < 3: continue
            for n, canon, kind in self.names:
                if len(n) < 4: continue
                r = best_window(l, n)
                r -= 0.01 * i                                  # üstteki satırlar biraz öncelikli
                if r > best[2]: best = (canon, kind, r)
        return best if best[2] >= cutoff else (None, None, best[2])

    def match_brand_or_set(self, lines, cutoff=0.84):
        res = {}
        for line in lines:
            l = nrm(line)
            for n, canon, kind in self.names:
                if kind in ("brand", "gear_set") and kind not in res and len(n) >= 4 and best_window(l, n) >= cutoff:
                    res[kind] = canon
        return res

    def match_talents(self, lines, cutoff=0.86):
        found = []
        for line in lines:
            l = nrm(line)
            if not l: continue
            perfect = bool(re.search(r"\bperfect(ed|ly)?\b", l))
            core = re.sub(r"\bperfect(ed|ly)?\b", " ", l).strip()
            best = (None, 0, None)
            for n, canon, kind in self.talents:
                if len(n) < 4: continue
                # talent adı satırın başında yazar ("Obliterate", "Perfect Fast Hands …")
                head = " ".join(core.split()[:len(n.split()) + 1])
                r = max(ratio(head, n), best_window(" ".join(core.split()[:4]), n))
                if r > best[1]: best = (canon, r, kind)
            if best[0] and best[1] >= cutoff:
                name = ("Perfect " if perfect else "") + best[0]
                if name not in [f[0] for f in found]:
                    found.append((name, best[2]))
        return found

    def parse_attrs(self, lines, prototype=False):
        attrs, quality = {}, {}
        for line in lines:
            # attribute satırı sayıyla başlar ("+5.9% Critical Hit Chance", "170,370 Armor");
            # talent açıklamaları ve marka bonusları ("1 piece: …") sayılmaz
            if not re.match(r"^\W{0,3}[+-]?\d", line) or re.search(r"(?i)\bpieces?\b|\bfor \d+s\b|\bseconds?\b", line):
                continue
            m = NUMBER.search(line)
            if not m: continue
            raw = m.group(1)
            if re.fullmatch(r"[+-]?\d{1,3}([.,]\d{3})+", raw):        # 170,370 / 170.370 → binlik ayırıcı
                raw = re.sub(r"[.,]", "", raw)
            else:
                raw = raw.replace(",", ".")
            try:
                val = float(raw)
            except ValueError:
                continue
            if (m.group(2) or "").lower() == "k": val *= 1000
            label = nrm(NUMBER.sub(" ", line))
            if len(label.split()) > 6: continue
            key, br = None, 0.0
            for al, k in self.attr_alias.items():
                r = best_window(label, al)
                if r > br: key, br = k, r
            if key and br >= 0.8:
                val = abs(val)
                if val > attrs.get(key, -1):
                    attrs[key] = val
                    mx = self.max_of(key, prototype)
                    if mx: quality[key] = round(min(100.0, val / mx * 100))
        return attrs, quality

    def recognize(self, text):
        lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
        low = nrm(text)
        name, kind, conf = self.match_name(lines)
        sets = self.match_brand_or_set(lines)
        rarity = []
        if kind == "exotic" or "exotic" in low: rarity.append("EXOTIC")
        if kind == "named" or re.search(r"\bnamed\b", low): rarity.append("NAMED")
        if "prototype" in low: rarity.append("PROTOTYPE")
        if kind == "gear_set" or "gear set" in low or sets.get("gear_set"): rarity.append("GEAR SET")
        if kind == "brand" or "high end" in low or sets.get("brand"): rarity.append("HIGH-END")
        is_weapon = any(w in low for w in self.weapon_types) or bool(re.search(r"\b(rpm|mag)\b", low))
        slot = None
        if not is_weapon:
            for scope in (nrm(" ".join(lines[:8])), low):       # önce kartın üstü, bulamazsa tüm kart
                for w, s in self.slots.items():
                    if re.search(r"\b" + re.escape(w) + r"\b", scope): slot = s; break
                if slot: break
        else:
            slot = "Sidearm" if re.search(r"\b(pistol|sidearm)\b", low) else "Weapon"
        attrs, quality = self.parse_attrs(lines, "PROTOTYPE" in rarity)
        talents = self.match_talents(lines)
        if not name:                                      # bilinen ad yoksa: marka/set + yuva ("Grupo Sombra Mask")
            base = sets.get("gear_set") or sets.get("brand")
            name = f"{base} {slot or ''}".strip() if base else ""
        confidence = round(min(1.0, (0.5 if (kind or sets) else 0) + 0.12 * len(attrs) + 0.1 * len(talents) +
                               (0.15 if slot else 0)), 2)
        return {"name": name or "?", "kind": "weapon" if is_weapon else "gear", "known": kind, "match": round(conf, 2),
                "brand": sets.get("brand") or (name if kind == "brand" else None),
                "gear_set": sets.get("gear_set") or (name if kind == "gear_set" else None),
                "rarity": rarity, "slot": slot, "attrs": attrs, "quality": quality,
                "talents": [t for t, _ in talents], "confidence": confidence}


# ---------------------------------------------------------------- ekran görüntüsü yardımcıları
def text_image(img):
    """Oyunun turuncu/beyaz yazısını koyu arka plandan ayıran ön işleme (OCR için)."""
    from PIL import ImageChops, ImageFilter, ImageOps, Image
    r, g, b = img.convert("RGB").split()
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)            # renkli yazılar da parlak kalır
    scale = 2 if mx.width < 700 else 1
    if scale > 1: mx = mx.resize((mx.width * scale, mx.height * scale), Image.LANCZOS)
    mx = ImageOps.autocontrast(mx, cutoff=1)
    mx = ImageOps.invert(mx)                                          # koyu yazı, açık zemin
    return mx.filter(ImageFilter.SHARPEN)


CARD_ANCHORS = {"core", "attributes", "attribute", "talents", "talent", "mods", "modifications", "stats", "brand", "gear"}


def card_crop(img, ocr_data_fn):
    """Bölge envanter listesi + eşya kartını birlikte içeriyorsa sadece kartı kırpar.
    Kart başlıklarını (Core Stats, Attributes, Talents…) bulup onların solundan keser."""
    try:
        from PIL import Image
        k = max(1, -(-img.width // 800))                              # hızlı olsun: ~800 px genişliğe küçült
        small = img.resize((img.width // k, img.height // k), Image.BILINEAR) if k > 1 else img
        f = img.width / small.width
        d = ocr_data_fn(text_image(small))
        sc = 2 if small.width < 700 else 1
        xs = [d["left"][i] / sc for i, w in enumerate(d["text"])
              if nrm(w) in CARD_ANCHORS and float(d["conf"][i] or 0) > 40]
        if not xs: return img
        x0 = max(0, int(min(xs) * f) - int(0.04 * img.width))
        if x0 < 0.12 * img.width: return img                             # zaten kart
        return img.crop((x0, 0, img.width, img.height))
    except Exception:
        return img
