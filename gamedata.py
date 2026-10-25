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
import time
import os
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
        for kind, key in (("exotic", "exotics"), ("named", "named"), ("gear_set", "gear_sets"), ("brand", "brands"), ("weapon", "weapons")):
            for n in d.get(key, []):
                self.names.append((nrm(n), n, kind))
        self.talents = [(nrm(n), n, "gear") for n in d.get("gear_talents", [])] + \
                       [(nrm(n), n, "weapon") for n in d.get("weapon_talents", [])]
        self.attr_alias = {}
        for k, a in d.get("attributes", {}).items():
            for al in a.get("aliases", []):
                self.attr_alias[nrm(al)] = k
        self.weapon_types = [nrm(w) for w in d.get("weapon_types", [])]
        self.items = {nrm(k): v for k, v in d.get("items", {}).items()}
        known = {x[0] for x in self.names}
        for n, v in d.get("items", {}).items():          # marka / set parçaları ("Unmatched Backpack", "Striker's Pack")
            if v.get("quality") in ("high-end", "gear set") and nrm(n) not in known:
                self.names.append((nrm(n), n, "piece")); known.add(nrm(n))
        self.weapon_index = {nrm(k): v for k, v in d.get("weapon_index", {}).items()}
        for n, v in d.get("weapon_index", {}).items():           # adlı/egzotik silahlar ad listesinde de olsun
            if not any(x[0] == nrm(n) for x in self.names):
                self.names.append((nrm(n), n, {"exotic": "exotic", "named": "named", "specialization": "named"}.get(v.get("quality"), "weapon")))
        self.ui_words = {nrm(w) for w in d.get("ui_words", [])}
        self.item_kinds = {k: [nrm(x) for x in v] for k, v in d.get("item_kinds", {}).items()}
        self.weapon_mod_names = [nrm(x) for x in d.get("weapon_mods", []) if len(x) > 8]
        sw = d.get("specialization_weapons", {})
        self.spec_sidearms = {nrm(k): v for k, v in sw.get("sidearms", {}).items()}
        self.spec_signature = [nrm(x) for x in sw.get("signature", [])]
        self.gear_mods = {nrm(m["stat"]): m for m in d.get("gear_mods", [])}
        self.slots = {nrm(k): v for k, v in d.get("slots", {}).items()}

    @property
    def ok(self):
        return bool(self.data)

    # ------------------------------------------------------------ öğrenilen kütüphane
    # Oyuncunun okuttuğu kartlardan öğrenilen markalar, gear set'ler ve parça adları ("Unmatched Backpack" →
    # Backpack, Unit Alloys). Yerel dosyada tutulur (learned_library.json), güncellemede silinmez; yeni sezonda
    # gelen ve kütüphanede henüz olmayan eşyalar bir kez okununca hep tanınır.
    def attach_learned(self, path):
        self.learned_path = Path(path)
        try:
            self.learned = json.loads(self.learned_path.read_text(encoding="utf-8"))
        except Exception:
            self.learned = {}
        for k in ("brands", "gear_sets", "items"):
            self.learned.setdefault(k, {})
        self._apply_learned()
        return self

    def _apply_learned(self):
        L = getattr(self, "learned", None) or {}
        known = {x[0] for x in self.names}
        for key, kind in (("brands", "brand"), ("gear_sets", "gear_set")):
            for n, v in L.get(key, {}).items():
                if nrm(n) not in known:
                    self.names.append((nrm(n), n, kind)); known.add(nrm(n))
                if kind == "brand" and v.get("bonuses") and n not in self.data.get("brand_bonuses", {}):
                    self.data.setdefault("brand_bonuses", {})[n] = v["bonuses"]
        for n, v in L.get("items", {}).items():
            if nrm(n) not in self.items:
                self.items[nrm(n)] = v
            if nrm(n) not in known:
                self.names.append((nrm(n), n, "piece")); known.add(nrm(n))

    def learn(self, item):
        """Okunan karttan yeni bilgi varsa kütüphaneye ekle. Dönüş: öğrenilenlerin listesi (boşsa yeni bir şey yok)."""
        if not getattr(self, "learned_path", None): return []
        info = item.get("_learn") or {}
        new = []
        sname, skind = info.get("set_name"), info.get("set_kind")
        known = {x[0]: x[2] for x in self.names}
        if sname and len(nrm(sname)) >= 4 and nrm(sname) not in known:
            key = "brands" if skind == "brand" else "gear_sets"
            rec = {"seen": time.strftime("%Y-%m-%d")}
            if skind == "brand" and info.get("bonuses"): rec["bonuses"] = info["bonuses"]
            self.learned[key][sname] = rec; new.append(f"{'brand' if skind == 'brand' else 'gear set'}: {sname}")
        title, slot = info.get("title"), item.get("slot")
        base = item.get("brand") or item.get("gear_set") or sname
        if (title and slot and base and item.get("kind") == "gear" and nrm(title) not in self.items
                and nrm(title) != nrm(base) and 2 <= len(title.split()) <= 5 and not re.search(r"\d", title)):
            rec = {"slot": slot, "quality": "gear set" if (item.get("gear_set") or skind == "gear_set") else "high-end",
                   "seen": time.strftime("%Y-%m-%d")}
            rec["gear_set" if rec["quality"] == "gear set" else "brand"] = base
            self.learned["items"][title] = rec; new.append(f"{title} → {slot}")
        if new:
            self._apply_learned()
            try:
                tmp = self.learned_path.with_name(self.learned_path.name + ".tmp")
                tmp.write_text(json.dumps(self.learned, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
                os.replace(tmp, self.learned_path)
            except Exception:
                pass
        return new

    def max_of(self, key, prototype=False, weapon=False):
        """Rulo kalitesi için en yüksek değer. Silahta yan attribute'un en yüksek rulosu (weapon_max)."""
        a = self.data.get("attributes", {}).get(key, {})
        m = (a.get("weapon_max") or a.get("max")) if weapon else a.get("max")
        return m * (self.data.get("prototype_multiplier", 1.5) if prototype else 1) if m else None

    def limit_of(self, key, prototype=False, weapon=False, named=False):
        """OCR denetimi için görülebilecek en yüksek değer (bunun üstü okuma hatasıdır).
        Silah: çekirdekler dahil (SMG CHC 21, MMR HSD 111). Ekipman: en yüksek × 1,5 (prototype olabilir);
        named/egzotik "perfect" attribute'larda × 2 (gözlenen: HSD %20)."""
        a = self.data.get("attributes", {}).get(key, {})
        if weapon:
            m = a.get("weapon_limit") or a.get("weapon_max") or a.get("max")
            return m * (self.data.get("prototype_multiplier", 1.5) if prototype else 1) if m else None
        m = a.get("max")
        if not m: return None
        k = max(self.data.get("prototype_multiplier", 1.5), self.data.get("named_multiplier", 2.0) if named else 0)
        return m * k

    # ------------------------------------------------------------ tanıma
    # Kart bölüm başlıkları (İngilizce oyun). Attribute yalnızca core / attributes / mods bölümlerinden okunur;
    # "Expertise +15% Armor" gibi uzmanlık (expertise) bonusları, set bonusları ve talent açıklamaları sayılmaz.
    SECTIONS = [
        ("core_stats", r"core stats|weapon stats|stats"),
        ("core", r"core attributes?|core attribute"),
        ("attributes", r"attributes?|minor attributes?"),
        ("expertise", r"expertise|proficient|proficiency|no upgrades active"),
        ("talents", r"talents?|weapon talents?"),
        ("mods", r"mods|gear mods|weapon mods|modifications|mod slots?|gear modding|weapon modding"),
        ("bonus", r"brand set bonus(es)?|gear set bonus(es)?|set bonus(es)?|brand bonus(es)?|\d ?pieces?"),
        ("misc", r"dye|appearance|owned.*|source.*|description|skin|vanity|appearance slot|dye slot"),
    ]

    def split_sections(self, lines):
        """[(bölüm, satır)] — başlık satırları atılır; ilk başlıktan önceki satırlar 'head' (ad, nadirlik, tür)."""
        out, cur, found = [], "head", False
        for line in lines:
            l = nrm(line)
            hit = None
            if 0 < len(l.split()) <= 4:
                for key, pat in self.SECTIONS:
                    if re.fullmatch(r"(?:\w{0,2} )?(?:" + pat + r")(?: \w{0,2})?", l):
                        hit = key; break
            if hit:
                cur, found = hit, True
                continue
            out.append((cur, line))
        return out, found

    def _ui_line(self, l):
        if l in self.ui_words: return True
        if re.sub(r"\s+(rank|level)\b.*$", "", l) in self.items: return False   # "Loadout Frame" eşyadır, menü yazısı değil
        return any(l.startswith(w + " ") for w in self.ui_words if len(w) > 6)

    def match_name(self, lines, cutoff=0.82):
        """Satırlarda geçen en iyi bilinen ad: (kanonik, tür, benzerlik) ya da (None, None, 0)."""
        best = (None, None, 0.0)
        for i, line in enumerate(lines[:14]):                 # ad ve marka kartın üst kısmında
            l = nrm(line)
            if len(l) < 3 or self._ui_line(l): continue
            toks = set(l.split())
            for n, canon, kind in self.names:
                if len(n) < 3 and not (len(n) == 2 and any(ch.isdigit() for ch in n)): continue   # M4, M9 birebir
                if len(n) <= 5 or " " not in n and any(ch.isdigit() for ch in n):
                    # kısa adlar (M700, KSG, 93R, MP7): yalnızca birebir kelime eşleşmesi ("700 times" ≠ M700)
                    r = 1.0 if n in toks or (" " in n and n in l) else 0.0
                else:
                    r = best_window(l, n)
                if kind == "piece" and r < 0.92:
                    # parça adları "<sözcük> <yuva>" biçiminde: yuva sözcüğü ortak olduğundan benzerlik yanıltır
                    # ("HG Backpack" ≈ "Unmatched Backpack"); yalnız neredeyse birebir okumalar sayılır
                    continue
                r -= 0.01 * i                                  # üstteki satırlar biraz öncelikli
                r += 0.0005 * min(len(n), 30)                  # eşitlikte daha belirli ad: "Rigger Gear Bag" > "Rigger"
                if r > best[2]: best = (canon, kind, r)
        return best if best[2] >= cutoff else (None, None, best[2])

    def match_brand_or_set(self, lines, cutoff=0.86):
        res = {}
        for line in lines:
            l = nrm(line)
            if self._ui_line(l): continue
            for n, canon, kind in self.names:
                if kind not in ("brand", "gear_set") or kind in res or len(n) < 4: continue
                # tek kelimeyle ("Summit") marka sayılmaz: çok kelimeli adlarda en az 2 kelime örtüşmeli
                if " " in n and len(set(n.split()) & set(l.split())) < min(2, len(n.split())) and best_window(l, n) < 0.93:
                    continue
                if best_window(l, n) >= cutoff:
                    res[kind] = canon
        return res

    def match_talents(self, lines, cutoff=0.86):
        found = []
        idx = next((i for i, l in enumerate(lines) if re.match(r"^\W*talents?\b", nrm(l))), None)
        if idx is not None:
            lines = lines[idx + 1:]
        else:
            cutoff = max(cutoff, 0.93)
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

    def parse_attr_line(self, line, prototype=False, weapon=False, named=False):
        """Tek satırdan (anahtar, değer) ya da None."""
        # attribute satırı sayıyla başlar ("+5.9% Critical Hit Chance", "170,370 Armor");
        # talent açıklamaları ve marka bonusları ("1 piece: …") sayılmaz
        if not re.match(r"^[^A-Za-z]{0,8}?[+-]?\d", line) or re.search(r"(?i)\bpieces?\b|\bfor \d+s\b|\bseconds?\b|\bstacks?\b|\btimes\b", line):
            return None
        cands = list(NUMBER.finditer(line))
        if not cands: return None
        m = next((c for c in cands if c.group(2)), None) or next((c for c in cands if c.group(1)[:1] in "+-"), cands[0])
        raw = m.group(1)
        if re.fullmatch(r"[+-]?\d{1,3}([.,]\d{3})+", raw):        # 170,370 / 170.370 → binlik ayırıcı
            raw = re.sub(r"[.,]", "", raw)
        else:
            raw = raw.replace(",", ".")
        try:
            val = float(raw)
        except ValueError:
            return None
        if (m.group(2) or "").lower() == "k": val *= 1000
        label = nrm(NUMBER.sub(" ", line))
        if len(label.split()) > 7: return None
        key, br = None, 0.0
        for al, k in self.attr_alias.items():
            r = best_window(label, al)
            if r > br: key, br = k, r
        if not key or br < 0.8: return None
        val = abs(val)
        mx0 = self.limit_of(key, prototype, weapon, named)
        if mx0 and val > mx0 * 1.05:
            raw2 = m.group(1).lstrip("+-")
            if raw2[:1] == "4" and len(raw2) > 1:      # "+" çoğu zaman "4" okunur: "411.1%" → "11.1%"
                try:
                    v2 = float(raw2[1:].replace(",", "."))
                except ValueError:
                    return None
                if v2 <= mx0 * 1.05: val = v2
                else: return None
            else:
                return None                           # imkânsız değer (OCR hatası)
        return key, val

    def parse_attrs(self, lines, prototype=False, sections=None, weapon=False, named=False):
        """(attrs, quality, mod_attrs). sections verilirse yalnızca core/attributes/mods bölümleri okunur."""
        attrs, quality, mods = {}, {}, {}
        rows = sections if sections is not None else [(None, l) for l in lines]
        use_sections = sections is not None and any(sec not in ("head",) for sec, _ in rows)
        for sec, line in rows:
            if use_sections and sec not in ("core", "attributes", "mods"):
                continue
            if not use_sections and re.search(r"(?i)expertise|proficien", line):
                continue
            kv = self.parse_attr_line(line, prototype, weapon, named)
            if not kv: continue
            key, val = kv
            target = mods if sec == "mods" else attrs
            if val > target.get(key, -1):
                target[key] = val
                if target is attrs:
                    mx = self.max_of(key, prototype, weapon)
                    if mx: quality[key] = round(min(100.0, val / mx * 100))
        return attrs, quality, mods

    def item_kind(self, head_text, all_text, name_kind):
        """weapon / gear / gear_mod / weapon_mod / skill_mod / cosmetic / material / consumable / cache."""
        for kind in ("skill_mod", "gear_mod", "cosmetic", "material", "consumable", "cache"):
            for ph in self.item_kinds.get(kind, []):
                if re.search(r"\b" + re.escape(ph) + r"\b", head_text):
                    return kind
        if any(best_window(head_text, n) >= 0.9 for n in self.weapon_mod_names) or re.search(r"\bweapon mod\b", head_text):
            return "weapon_mod"
        return None

    def recognize(self, text):
        lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
        low = nrm(text)
        secs, has_sections = self.split_sections(lines)
        head_lines = [l for s, l in secs if s == "head"][:10]
        head = nrm(" ".join(head_lines))
        # "Brand Set / Unit Alloys (0/3)" ya da "Gear Set / Striker's Battlegear (4/6)": kütüphanede olmasa da
        # marka/set adı buradan kesin okunur. Bu bölümden sonrası (set bonusları) eşyanın başlığı değildir.
        set_name = set_kind = None; bonuses = []; set_idx = None
        for i, line in enumerate(lines[:16]):
            l = nrm(line)
            if l in ("brand set", "gear set", "brandset", "gearset") and i + 1 < len(lines):
                m = re.match(r"^\s*(.+?)\s*[\(\[]\s*\d\s*/\s*\d\s*[\)\]]", lines[i + 1])
                if m:
                    set_name, set_kind, set_idx = m.group(1).strip(" .,:;'\"|"), ("brand" if l.startswith("brand") else "gear_set"), i
                    for b in lines[i + 2:i + 9]:
                        if re.match(r"^\s*core attributes?\b", nrm(b)): break
                        mb = re.match(r"^\s*\+?\s*(\d+(?:[.,]\d+)?)\s*%\s*(.+)$", b)
                        if mb: bonuses.append(f"{mb.group(1).replace(',', '.').rstrip('0').rstrip('.')}% {mb.group(2).strip()}")
                        elif bonuses and re.fullmatch(r"[A-Za-z ]{3,20}", b.strip()): bonuses[-1] += " " + b.strip()
                break
        if set_idx is not None:
            head_lines = [l for l in head_lines if l in lines[:set_idx]]
            head = nrm(" ".join(head_lines))
        armor_line = any(re.match(r"^\s*\d+(?:[.,]\d+)?\s*k?\s+armor\b", nrm(l)) for l in lines[:6])
        name, kind, conf = self.match_name(head_lines if has_sections and head_lines else lines)
        sets = self.match_brand_or_set(head_lines if has_sections and head_lines else lines[:14])
        if set_name and not sets:
            m2 = self.match_brand_or_set([set_name])
            sets = m2 or {set_kind: set_name}
        # başlık satırı (eşyanın adı): kartın ilk anlamlı satırı, "RANK" vb. temizlenmiş
        title = None
        for l in lines[:3]:
            tl = re.sub(r"\b(rank|level)\b.*$", "", l, flags=re.I).strip(" .,:;-|")
            if len(tl) >= 6 and not re.search(r"\d", tl) and not self._ui_line(nrm(tl)) and \
                    nrm(tl) not in ("high end", "gear set", "exotic", "named", "brand set"):
                title = tl; break
        info = (self.items.get(nrm(name)) if name else None) or {}
        if info and not sets:                              # öğrenilen parça: marka/set bilgisi kütüphanede
            if info.get("brand"): sets = {"brand": info["brand"]}
            elif info.get("gear_set"): sets = {"gear_set": info["gear_set"]}
        winfo = (self.weapon_index.get(nrm(name)) if name else None) or {}
        rarity = []
        if kind == "exotic" or re.search(r"\bexotic\b", head) or info.get("quality") == "exotic" or winfo.get("quality") == "exotic":
            rarity.append("EXOTIC")
        if kind == "named" or re.search(r"\bnamed\b", head) or info.get("quality") == "named" or winfo.get("quality") == "named":
            rarity.append("NAMED")
        if "prototype" in head: rarity.append("PROTOTYPE")
        if kind == "gear_set" or "gear set" in head or sets.get("gear_set") or info.get("quality") == "gear set": rarity.append("GEAR SET")
        if kind == "brand" or "high end" in head or sets.get("brand") or info.get("quality") == "high-end": rarity.append("HIGH-END")
        # bilinen eşya/silah adındaki sözcükler tür sanılmasın: "Special Ammo Holster", "Ammo Dump" ≠ cephane, "Steel & Sons ACR" ≠ malzeme
        special = None if kind in ("piece", "weapon", "named", "exotic") else self.item_kind(head, low, kind)
        # silah mı? Güçlü kanıt gerekir: bilinen silah adı, ya da kartın üstünde silah türü, ya da RPM + MAG birlikte.
        gearish = kind in ("gear_set", "brand", "piece") or bool(info) or bool(sets) or armor_line or bool(set_name)
        wtype = winfo.get("type")
        if not wtype:
            for w in self.weapon_types:
                if re.search(r"\b" + re.escape(w) + r"\b", head):
                    wtype = w.title().replace("Machinegun", "Machine Gun"); break
        is_weapon = not gearish and (kind == "weapon" or bool(winfo) or bool(wtype) or
                                     (re.search(r"\brpm\b", low) and re.search(r"\b(mag|total dmg|total damage)\b", low)))
        slot = None
        if info.get("slot"):
            slot = info["slot"]
        elif is_weapon:
            slot = "Sidearm" if (wtype or "").lower() in ("pistol", "sidearm") or re.search(r"\b(pistol|sidearm)\b", head) else "Weapon"
        else:
            # önce kartın üstü, bulamazsa tüm kart. Birden çok yuva sözcüğü varsa metinde EN ÖNCE geçen kazanır
            # (sözlük sırası değil: "Striker's Kneepads" kartında açıklamadaki başka bir yuva adı seçilmesin)
            for scope in (head, nrm(" ".join(lines[:8])), low):
                hits = []
                for w, s in self.slots.items():
                    m = re.search(r"\b" + re.escape(w) + r"\b", scope)
                    if m: hits.append((m.start(), s))
                if hits: slot = min(hits)[1]; break
        attrs, quality, mod_attrs = self.parse_attrs(lines, "PROTOTYPE" in rarity, secs if has_sections else None,
                                                     weapon=bool(is_weapon), named=bool({"NAMED", "EXOTIC"} & set(rarity)))
        talents = self.match_talents(lines)
        if not name:                                      # bilinen ad yoksa: marka/set + yuva ("Grupo Sombra Mask")
            base = sets.get("gear_set") or sets.get("brand")
            if base and title and slot and any(re.search(r"\b" + re.escape(w) + r"\b", nrm(title)) for w, sl in self.slots.items() if sl == slot):
                name = title                              # parçanın kendi adı ("Unmatched Backpack")
            else:
                name = f"{base} {slot or ''}".strip() if base else ""
        spec = (self.spec_sidearms.get(nrm(name)) if name else None) or \
               next((n for n in self.spec_signature if n in low), None)
        item_kind = special or ("weapon" if is_weapon else "gear")
        partial = item_kind in ("gear", "weapon") and not name and bool(attrs or talents)   # kartın üstü görünmüyor (kaydırılmış)
        if item_kind == "gear_mod" and not name:
            st = next(iter(attrs or mod_attrs), None)
            name = "Gear Mod" + (f" · {st.replace('_', ' ').title()}" if st else "")
        confidence = round(min(1.0, (0.5 if (kind or sets) else 0) + 0.12 * len(attrs) + 0.1 * len(talents) +
                               (0.15 if slot else 0)), 2)
        return {"name": name or "?", "kind": item_kind, "known": kind, "match": round(conf, 2),
                "brand": sets.get("brand") or info.get("brand") or (name if kind == "brand" else None),
                "gear_set": sets.get("gear_set") or info.get("gear_set") or (name if kind == "gear_set" else None),
                "rarity": rarity, "slot": slot if item_kind in ("weapon", "gear") else None,
                "weapon_type": wtype, "spec": spec, "partial": partial, "sections": has_sections,
                "attrs": attrs, "quality": quality, "mod_attrs": mod_attrs,
                "talents": [t for t, _ in talents], "confidence": confidence,
                "_learn": {"set_name": set_name, "set_kind": set_kind, "bonuses": bonuses, "title": title}}


# ---------------------------------------------------------------- ekran görüntüsü yardımcıları
def text_image(img):
    """Oyunun turuncu/beyaz yazısını koyu arka plandan ayıran ön işleme (OCR için)."""
    from PIL import ImageChops, Image
    r, g, b = img.convert("RGB").split()
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)            # beyaz/turuncu yazı parlak kalır
    # 1440p'de kart yazıları ~20 px: 1,5× büyütmek Tesseract için en iyi sonucu verdi (gerçek oyun kartıyla ölçüldü)
    # 240p/480p/720p kartlarında yazı çok küçük: daha fazla büyüt (Tesseract ~30 px harf yüksekliğini sever)
    h = mx.height
    scale = SCALE or (6.0 if h < 220 else 4.0 if h < 380 else 3.0 if h < 520 else 2.0 if h < 700 else 1.5 if h < 2000 else 1.0)
    if scale != 1: mx = mx.resize((int(mx.width * scale), int(mx.height * scale)), Image.LANCZOS)
    thr = THRESHOLD
    return mx.point(lambda v: 0 if v >= thr else 255)                 # yazı siyah, yarı saydam zemin beyaz


THRESHOLD = 170          # 0-255; oyun parlaklığı/HDR'a göre ayarlardan değiştirilebilir
SCALE = None             # None = otomatik (kart yüksekliğine göre); ayarlardan sabitlenebilir

