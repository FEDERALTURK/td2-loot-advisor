"""Canlı oyun çevirisi (İngilizce → Türkçe): ekrandaki yazıyı okur (OCR) ve gelişmiş bir dil modeliyle çevirir.

Eşya kartı okur gibi çalışır: seçilen alan (altyazı, bölge ya da tüm oyun penceresi) izlenir; yazı değişip durulunca
okunur, paragraflara ayrılır, çevrilir ve oyunun üstünde gösterilir. Oyunun belleğine / dosyalarına dokunulmaz.

Motorlar
  - "local": OPUS-MT (Helsinki-NLP, CC-BY 4.0) sinir ağı çeviri modeli, CTranslate2 ile bilgisayarda, internetsiz.
    Model ilk kullanımda indirilir (~150-250 MB) ve SHA-256 ile doğrulanır.
  - "ai": Asistan sekmesinde seçilen büyük dil modeli (Claude / OpenAI / Ollama) — oyun bağlamını bilerek çevirir.
Oyun içi özel adlar (eşya, yetenek, set, marka, grup ve yer adları) çevrilmez: çeviriden önce maskelenir.
"""
import hashlib
import json
import os
import re
import threading
import time
import urllib.request
import zipfile
from collections import OrderedDict, Counter
from decimal import Decimal
from pathlib import Path

MODEL_RELEASE = "https://github.com/FEDERALTURK/td2-loot-advisor/releases/download/mt-models/"
MODEL_FILE = "en-tr-opus-mt-tc-big-en-tr.zip"
MODEL_SHA256 = "15b848670994a47a688dd8bbe3e619c4d19bfd7bcb570b9627bdcd218d1f63fc"   # mt-models sürümündeki paket

# Oyunda sık geçen, çevrilmemesi gereken adlar (kütüphanedeki eşya/yetenek/set/marka adlarına ek)
EXTRA_TERMS = [
    "The Division", "Division", "SHD", "ISAC", "JTF", "Dark Zone", "DZ", "Black Tusk", "Hyenas", "True Sons", "Outcasts",
    "Cleaners", "Rikers", "Rogue", "Rogue Agent", "Hunter", "Hunters", "Manhunt", "Scout", "HVT", "Summit", "Countdown",
    "Descent", "Incursion", "Raid", "Conflict", "Legendary", "Heroic", "Challenging", "Washington", "D.C.", "New York",
    "Brooklyn", "Kenly", "Kenly College", "White House", "Castle", "Theater", "Campus", "Capitol", "Pentagon", "DARPA",
    "Keener", "Faye Lau", "Bardon", "Kelso", "Manny", "Odessa", "Calvin", "Hutch", "Theo", "Aaron Keener",
    "Targeted Loot", "Expertise", "Specialization", "Shepherd", "SHD Watch", "Season Pass", "Journey", "Classified Assignment",
    "Global Event", "Safe House", "Settlement", "Control Point", "Bounty", "Exotic", "Named", "Gear Set", "High-End",
]
NOISE = re.compile(r"^[\W\d_]{0,}$")
# Oyunun değil sistemin yazıları: arkadaş bildirimleri (oyuncu adları içerir), kaplama araçları — okunmaz, çevrilmez, gönderilmez
PRIVATE = re.compile(r"\bis (?:now )?(?:playing|online|offline)\b|ubisoft connect|\bwants to (?:join|play)\b|\bfriend request\b|"
                     r"\bsent you\b|\bhas invited you\b|\bsteam\b.*\bfriend|nvidia|geforce|xbox game bar|discord", re.I)
# Ödül sandıkları vb. adlar (ör. "Recalibration Cache", "Gear Crafting Cache") oyuncuların bildiği İngilizce adıyla kalır
CACHE_RE = re.compile(r"(?<![\w'])(?:[A-Z][\w-]*\s){0,3}(?:Cache|Caches)(?![\w])")
PERSONAL_PRONOUN_RE = re.compile(
    r"\b(?:i|me|my|mine|myself|we|us|our|ours|ourselves|you|your|yours|yourself|yourselves|"
    r"he|him|his|himself|she|her|hers|herself|it|its|itself|they|them|their|theirs|"
    r"themself|themselves|who|whom|whose|whoever|whomever|which|whichever|that|this|these|those|"
    r"one|ones|oneself)\b", re.I)
# Tek başına satır olan arayüz başlıkları: modele gitmeden sabit karşılık
UI_TR = {
    "objective": "Hedef", "objectives": "Hedefler", "reward": "Ödül", "rewards": "Ödüller", "complete": "Tamamlandı",
    "completed": "Tamamlandı", "requirements": "Gereksinimler", "requirement": "Gereksinim", "difficulty": "Zorluk",
    "description": "Açıklama", "details": "Ayrıntılar", "progress": "İlerleme", "available": "Mevcut", "locked": "Kilitli",
    "unlocked": "Açıldı", "new": "Yeni", "active": "Etkin", "expired": "Süresi doldu", "in progress": "Devam ediyor",
    "daily project": "Günlük Proje", "weekly project": "Haftalık Proje", "season pass project": "Sezon Bileti Projesi",
    "base of operations": "Operasyon Üssü", "track on screen": "Ekranda takip et", "close map": "Haritayı kapat",
    "fast travel": "Hızlı seyahat", "select": "Seç", "back": "Geri", "abandon": "Bırak", "view donations": "Bağışları gör",
    "projects": "Projeler", "bounties": "Ödül avları", "assignments": "Görevlendirmeler", "legend": "Gösterge",
}
# Model çıktısında sık görülen, oyuna uymayan kelimeler → oyundaki Türkçe karşılığı (ek uyumu korunarak)
WORD_FIX = [
    (r"\bmisyonlarını\b", "görevlerini"), (r"\bmisyonlarına\b", "görevlerine"), (r"\bmisyonları\b", "görevleri"),
    (r"\bmisyonlar\b", "görevler"), (r"\bmisyonunu\b", "görevini"), (r"\bmisyonuna\b", "görevine"),
    (r"\bmisyonunda\b", "görevinde"), (r"\bmisyonu\b", "görevi"), (r"\bmisyonda\b", "görevde"),
    (r"\bmisyona\b", "göreve"), (r"\bmisyonu?n\b", "görevin"), (r"\bmisyon\b", "görev"),
    (r"\bMisyon", "Görev"),
    (r"(\S+) zorluğu üzerinde", r"\1 zorlukta"), (r"(\S+) zorluğunda", r"\1 zorlukta"),
    (r"\bdişli\b", "ekipman"), (r"\bDişli\b", "Ekipman"),
]
COUNTER_RE = re.compile(r"(?<![\w/])(\d{1,3})\s?/\s?(\d{1,3})(?![\w/])")
ICON_RE = re.compile(r"^(?:[^\w\s'\"(]+|[B-HJ-Zb-hj-z])\s+(?=[A-Z])")    # satır başında ikondan okunan tek harf / işaret


# ---------------------------------------------------------------- özel adlar
def load_proper_names(paths):
    """Load curated story/world entities from bundled or source meta JSON files."""
    entries, seen = [], set()
    for path in paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        for entry in data.get("entities", []) if isinstance(data, dict) else []:
            if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
                continue
            key = entry["name"].casefold()
            if key not in seen:
                entries.append(entry); seen.add(key)
    return entries


class Glossary:
    def __init__(self, names=(), proper_names=()):
        self.proper_names = [e for e in proper_names if isinstance(e, dict) and e.get("name")]
        curated = []
        self.pronoun_by_alias = {}
        for entry in self.proper_names:
            variants = [entry["name"], *entry.get("aliases", [])]
            curated.extend(variants)
            if entry.get("pronouns"):
                for variant in variants:
                    self.pronoun_by_alias[variant.casefold()] = (entry["name"], entry["pronouns"])
        terms = {n.strip() for n in list(names) + EXTRA_TERMS + curated if isinstance(n, str) and len(n.strip()) >= 3}
        # uzun adlar önce (ör. "Kenly College" "Kenly"den önce)
        self.terms = sorted(terms, key=len, reverse=True)
        alts = [CACHE_RE.pattern] + [r"(?<![\w'])" + re.escape(t) + r"(?![\w])" for t in self.terms]
        self._re = re.compile("|".join(alts))  if self.terms else None
        self._re_i = re.compile("|".join(alts[1:]), re.I) if self.terms else None
        self.canon = {t.lower(): t for t in self.terms}

    def pronoun_hints(self, found):
        """Return only source-confirmed pronouns for recognized character names."""
        hints = set()
        for name in found:
            info = self.pronoun_by_alias.get(name.casefold())
            if info:
                hints.add(f"{info[0]} uses {info[1]}")
        return sorted(hints)

    def mask(self, text):
        """Özel adları ZQ0, ZQ1… belirteçleriyle değiştirir. Dönüş: (maskeli metin, [özgün adlar])."""
        if not self._re: return text, []
        found = []
        def rep(m):
            found.append(m.group(0)); return f"ZQ{len(found) - 1}"
        text = CACHE_RE.sub(rep, text)                       # sandık adları (büyük harf duyarlı)
        return self._re_i.sub(rep, text), found

    def whole(self, text):
        """Satırın tamamı tek bir özel ad mı (ör. "Exotic Cache", "Legendary Roosevelt Island" değil)."""
        t = text.strip()
        if not t or not self._re_i: return False
        if CACHE_RE.fullmatch(t): return True
        m = self._re_i.fullmatch(t)
        return bool(m)

    @staticmethod
    def unmask(text, found):
        def rep(m):
            i = int(m.group(1))
            return found[i] if i < len(found) else m.group(0)
        out = re.sub(r"Z\s?Q\s?(\d{1,2})", rep, text)
        return out


# ---------------------------------------------------------------- metin ayıklama
def is_english(text):
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 3: return False
    ascii_ratio = sum(c.isascii() for c in letters) / len(letters)
    return ascii_ratio > 0.9 and len(re.findall(r"[A-Za-z]{2,}", text)) >= 1


def blocks_from_lines(lines, ui_words=(), preserve_lines=False):
    """OCR satırlarını [(metin, kutu, güven)] paragraf bloklarına toplar; arayüz gürültüsünü atar."""
    ui = {w.lower() for w in ui_words}
    rows = []
    for txt, box, conf in lines:
        s = " ".join(txt.split())
        if conf < 0.5 or len(s) < 3 or NOISE.match(s) or s.lower() in ui or not is_english(s) or PRIVATE.search(s): continue
        s = ICON_RE.sub("", s)
        rows.append([s, list(box), conf])
    rows.sort(key=lambda r: (r[1][1], r[1][0]))
    hs = sorted(max(1.0, r[1][3] - r[1][1]) for r in rows)
    if hs: BODY_H[0] = hs[len(hs) // 2]
    if preserve_lines:
        # In-place text must retain each OCR segment's own source rectangle.
        # Paragraph union boxes erase unrelated UI and lose line positions.
        return [(s, tuple(b), c) for s, b, c in rows if len(s) >= 4]
    blocks = []
    for s, b, c in rows:
        h = max(1.0, b[3] - b[1])
        target = None
        for blk in reversed(blocks[-16:]):             # çok sütunlu ekran: satır kendi sütunundaki bloğa eklenir
            lb, lh = blk[1], blk[3]
            gap = b[1] - lb[3]
            if gap > 0.9 * h or gap < -0.4 * h: continue
            if blk[5][0] > b[2] or b[0] > blk[5][2]: continue        # son satırla yatayda hiç çakışmıyor
            if abs(b[0] - blk[5][0]) < 2.5 * h or (min(b[2], blk[5][2]) - max(b[0], blk[5][0])) > 0.3 * (b[2] - b[0]):
                target = blk; break
        if target:
            lb = target[1]
            target[0] = target[0] + _joiner(target[4], s, target[3], h) + s
            target[1] = [min(lb[0], b[0]), min(lb[1], b[1]), max(lb[2], b[2]), max(lb[3], b[3])]
            target[2] = min(target[2], c); target[3] = h; target[4] = s; target[5] = list(b)
            continue
        blocks.append([s, list(b), c, h, s, list(b)])
    blocks.sort(key=lambda bl: (bl[1][1], bl[1][0]))
    return [(s, tuple(b), c) for s, b, c, _, _, _ in blocks if len(s) >= 4]


def _is_label(s):
    """Başlık / liste öğesi gibi kısa satır: ≤4 kelime, cümle sonu yok, kelimeler büyük harfle başlıyor."""
    w = s.split()
    return 0 < len(w) <= 4 and not re.search(r"[.!?,;]$", s) and all(x[:1].isupper() or x[:1].isdigit() for x in w)


def _joiner(prev, cur, prev_h, cur_h):
    """Aynı bloktaki iki satır arasına boşluk mu (sarılmış paragraf) yeni satır mı (başlık, liste) konacağı."""
    if _is_label(prev):
        if _is_label(cur) and abs(prev_h - cur_h) < 0.15 * max(prev_h, cur_h) and prev_h > 1.25 * BODY_H[0]:
            return " "                                   # büyük puntolu başlığın ikinci satırı
        return "\n"
    if re.search(r"[.!?:]$", prev) and cur[:1].isupper():
        return "\n"
    if _is_label(cur) and len(cur.split()) <= 2:       # paragraftan sonra gelen kısa başlık (ör. "Rewards")
        return "\n"
    return " "


BODY_H = [24.0]          # gövde yazısı yüksekliği (blocks_from_lines her çağrıda günceller)


def clean_for_mt(text):
    """Modelin sözlüğünde olmayan işaretleri sadeleştir (yoksa ⁇ üretir)."""
    text = (text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", " - ")
                .replace("…", "...").replace("\u00a0", " ").replace("×", "x"))
    text = re.sub(r"\b(\d+(?:\.\d+)?)\s?s\b", r"\1 seconds", text)           # "15s" → "15 seconds" (yoksa "15'ler")
    return text


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“(])", text.strip())
    return [p for p in parts if p]


# ---------------------------------------------------------------- önbellek
class Cache:
    def __init__(self, path=None, size=6000):
        self.path, self.size, self.d = (str(path) if path else None), max(1, min(6000, int(size))), OrderedDict()
        self.lock = threading.Lock(); self.dirty = 0
        if self.path:
            try:
                with open(self.path, encoding="utf-8") as f: data = json.load(f).get("items", {})
                if isinstance(data, dict):
                    self.d.update((k, v) for k, v in data.items() if isinstance(k, str) and isinstance(v, str) and v.strip())
                    while len(self.d) > self.size: self.d.popitem(last=False)
            except (OSError, ValueError):
                pass

    @staticmethod
    def key(engine, text):
        return engine + ":" + hashlib.sha1(text.strip().lower().encode()).hexdigest()[:20]

    def get(self, engine, text):
        k = self.key(engine, text)
        with self.lock:
            v = self.d.get(k)
            if v is not None: self.d.move_to_end(k)
            return v

    def put(self, engine, text, value):
        if not isinstance(value, str) or not value.strip(): return
        with self.lock:
            self.d[self.key(engine, text)] = value
            while len(self.d) > self.size: self.d.popitem(last=False)
            self.dirty += 1
        if self.dirty >= 20: self.save()

    def save(self):
        if not self.path: return
        with self.lock:
            data, self.dirty = {"v": 1, "items": dict(self.d)}, 0
        try:
            import safeio
            safeio.write_json(self.path, data, indent=None, backup=False)
        except OSError:
            pass


# ---------------------------------------------------------------- motorlar
class LocalMT:
    """OPUS-MT + CTranslate2 (int8, CPU)."""
    name = "local"

    def __init__(self, model_dir):
        self.dir = Path(model_dir)
        self.tr = self.sps = self.spt = None
        self.prefix = ""
        self.lock = threading.Lock()

    @staticmethod
    def available():
        try:
            import ctranslate2, sentencepiece  # noqa: F401
            return True
        except Exception:
            return False

    def installed(self):
        return (self.dir / "model.bin").exists() and (self.dir / "source.spm").exists() and (self.dir / "target.spm").exists()

    def load(self):
        if self.tr: return
        import ctranslate2, sentencepiece as spm
        meta = {}
        try: meta = json.loads((self.dir / "td2_model.json").read_text(encoding="utf-8"))
        except (OSError, ValueError): pass
        self.prefix = meta.get("target_prefix", "")
        threads = max(1, min(4, (os.cpu_count() or 2) // 2))     # oyunla işlemciyi paylaş: çekirdeklerin en çok yarısı
        import winpath
        d = winpath.safe_dir(self.dir, "mt-" + self.dir.name)  # Türkçe kullanıcı adı: yerel kütüphane yolu açabilsin
        self.tr = ctranslate2.Translator(d, device="cpu", compute_type="int8", inter_threads=1, intra_threads=threads)
        self.sps = spm.SentencePieceProcessor(os.path.join(d, "source.spm"))
        self.spt = spm.SentencePieceProcessor(os.path.join(d, "target.spm"))
        self.last_use = time.time()

    def unload(self):
        """Bellekten çıkar (canlı çeviri bir süre kullanılmayınca ~300 MB geri verilir)."""
        with self.lock: self.tr = self.sps = self.spt = None

    def unload_if_idle(self, idle_seconds=300):
        """UI bakım çağrısı çalışan çeviriyi beklemez; boşta duran model bırakılır."""
        if not self.lock.acquire(blocking=False): return False
        try:
            if self.tr is None or time.time() - getattr(self, "last_use", time.time()) < idle_seconds: return False
            self.tr = self.sps = self.spt = None
            return True
        finally:
            self.lock.release()

    def translate(self, texts):
        with self.lock:
            self.load(); self.last_use = time.time()
            # Marian/OPUS-MT: kaynak cümle </s> ile bitmeli (yoksa model cümleyi tekrar eder)
            toks = [([self.prefix] if self.prefix else []) + self.sps.encode(t, out_type=str) + ["</s>"] for t in texts]
            res = self.tr.translate_batch(toks, beam_size=3, max_decoding_length=256, max_batch_size=16,
                                          no_repeat_ngram_size=4, repetition_penalty=1.1)
            return [self.spt.decode(r.hypotheses[0]) for r in res]


class AIMT:
    """Büyük dil modeliyle çeviri. complete(system, user) → metin (uygulama sağlar)."""
    name = "ai"
    SYSTEM = ("You translate on-screen text from the video game Tom Clancy's The Division 2 from English into natural, "
              "fluent Turkish for a player. Keep tokens like ZQ0, ZQ1 exactly as they are (they are proper names); add Turkish "
              "suffixes after them with an apostrophe when grammar needs it (ZQ0'ı). Preserve each pronoun's referent, "
              "person, grammatical role and singular/plural meaning. Translate pronouns naturally into Turkish; do not leave "
              "English pronouns, change who they refer to, or change singular they into a gendered character. Turkish may "
              "omit a pronoun only when the referent and role remain unambiguous. Keep numbers, percentages and units. "
              "Use the informal 'sen' form for instructions. Return ONLY a JSON array of strings, one translation per input "
              "line, in the same order, nothing else.")

    def __init__(self, complete):
        self.complete = complete

    def translate(self, texts, pronoun_hints=None):
        payload = json.dumps(texts, ensure_ascii=False)
        hints = []
        for i, values in enumerate(pronoun_hints or []):
            if values:
                hints.append(f"Input {i + 1}: " + "; ".join(values))
        system = self.SYSTEM
        if hints:
            system += " Use only these verified character pronouns when the name is present and clearly referred to: " + " | ".join(hints) + "."
        raw = self.complete(system, payload) or ""
        m = re.search(r"\[.*\]", raw, re.S)
        try:
            out = json.loads(m.group(0)) if m else None
        except ValueError:
            out = None
        if not isinstance(out, list) or len(out) != len(texts):
            raise RuntimeError("AI translation format")
        if any(not isinstance(x, str) or not x.strip() for x in out):
            raise RuntimeError("AI translation format")
        return out


class Translator:
    """Maskeleme + cümlelere bölme + önbellek + motor."""

    def __init__(self, engine, glossary, cache):
        self.engine, self.glossary, self.cache = engine, glossary, cache
        self.ck = engine.name + "@4"           # ad sözlüğü ve zamir/bağlam kuralları değişti; eski çıktılar yenilenir
        self.memory = None                     # topluluk görevleri (tasks_live.Memory): bilinen satırın doğrulanmış Türkçesi
        self.memory_hits = 0

    def set_memory(self, memory):
        """Hafıza değişince önbellek anahtarı da değişir (düzeltilmiş çeviri eski önbellekten gelmesin)."""
        self.memory = memory if memory is not None and len(memory) else None
        self.ck = self.engine.name + "@4" + (":" + getattr(memory, "version", "") if self.memory else "")

    def translate(self, texts, allow_partial=False):
        self.last_errors = {}
        out, todo, first = [None] * len(texts), [], {}
        for i, t in enumerate(texts):
            c = self.cache.get(self.ck, t)
            if c is not None: out[i] = c
            elif t in first: continue                      # aynı metin bir kez çevrilir
            else: first[t] = i; todo.append(i)
        if todo:
            # her metin → satırlar (madde işaretleri korunur) → cümleler; modele yalnız düz cümleler gider
            units, owners, masks, pronoun_hints = [], [], [], []  # owners: (metin no, satır no, madde işareti, sayaç)
            lines = {}
            for i in todo:
                for ln_no, line in enumerate(texts[i].split("\n")):
                    m_b = re.match(r"^\s*([•\-*]+)\s*", line)
                    bullet = "• " if m_b else ""
                    body = clean_for_mt(line[m_b.end():] if m_b else line)
                    if not body.strip():
                        continue
                    counters = COUNTER_RE.findall(body)            # "00/01" ilerleme sayaçları cümleden çıkarılır, sona eklenir
                    if counters: body = " ".join(COUNTER_RE.sub(" ", body).split())
                    fixed = UI_TR.get(body.strip().lower())
                    if not fixed and self.memory is not None:
                        fixed = self.memory.get(body)
                        if fixed: self.memory_hits += 1
                    if fixed or self.glossary.whole(body):
                        lines.setdefault(i, {}).setdefault(ln_no, [bullet, []])[1].append(fixed or body.strip())
                        if counters: lines[i][ln_no][1].append("(" + ", ".join(f"{a}/{b}" for a, b in counters) + ")")
                        continue
                    sents = split_sentences(body) if self.engine.name == "local" else [body]
                    # Sentence-by-sentence MT loses antecedents. Keep a short paragraph
                    # together when personal pronouns need the preceding sentence for context.
                    if len(sents) > 1 and PERSONAL_PRONOUN_RE.search(body):
                        sents = [body]
                    for k, s_ in enumerate(sents):
                        m, found = self.glossary.mask(s_)
                        tail = ("(" + ", ".join(f"{a}/{b}" for a, b in counters) + ")") if counters and k == len(sents) - 1 else ""
                        units.append(m); owners.append((i, ln_no, bullet, tail)); masks.append(found)
                        pronoun_hints.append(self.glossary.pronoun_hints(found))
            if units and self.engine.name == "ai":
                res = self.engine.translate(units, pronoun_hints=pronoun_hints)
            else:
                res = self.engine.translate(units) if units else []
            if not isinstance(res, (list, tuple)) or len(res) != len(units) or any(
                    not isinstance(r, str) or not r.strip() for r in res):
                raise RuntimeError("Incomplete translation; retry the text")
            for unit_index, ((i, ln_no, bullet, tail), r, found) in enumerate(zip(owners, res, masks)):
                # OCR'daki sayısal hedefler değişmişse hatalı çeviriyi gösterme/önbelleğe alma.
                placeholders = lambda value: Counter(int(n) for n in re.findall(r"Z\s*Q\s*(\d+)", value, flags=re.I))
                if placeholders(units[unit_index]) != placeholders(r):
                    if allow_partial:
                        self.last_errors[i] = "proper_name"
                        continue
                    raise RuntimeError("Translation lost a game name; retry the text")
                clean = lambda value: re.sub(r"Z\s*Q\s*\d+", "", value, flags=re.I)
                digits = lambda value: sorted(Decimal(n.replace(",", ".")) for n in re.findall(r"(?<!\w)\d+(?:[.,]\d+)?", clean(value)))
                if digits(units[unit_index]) != digits(r):
                    if allow_partial:
                        self.last_errors[i] = "number"
                        continue
                    raise RuntimeError("Translation changed a number; retry the text")
                r = re.sub(r"\s*⁇\s*", " ", self.glossary.unmask(r, found)).strip()
                for pat, rep in WORD_FIX: r = re.sub(pat, rep, r)
                if tail: r = r + " " + tail
                if r[:1].islower(): r = r[:1].upper() + r[1:]
                r = re.sub(r"%\s+(\d)", r"%\1", r)              # "% 30" → "%30"
                r = re.sub(r"([^\s+\-(])%(\d)", r"\1 %\2", r)     # "boyunca%1" → "boyunca %1"
                lines.setdefault(i, {}).setdefault(ln_no, [bullet, []])[1].append(r)
            for i in todo:
                if i in self.last_errors: continue
                rows = lines.get(i, {})
                out[i] = "\n".join(x for x in ((b + " ".join(parts)).strip() for _, (b, parts) in sorted(rows.items())) if x not in ("•", "")).strip()
                self.cache.put(self.ck, texts[i], out[i])
            for i, t in enumerate(texts):
                if out[i] is None:
                    out[i] = out[first[t]]
                    if first[t] in self.last_errors:
                        self.last_errors[i] = self.last_errors[first[t]]
        return out


# ---------------------------------------------------------------- model indirme
def download_model(dest_dir, progress=None, url=None, sha256=None, opener=None):
    """Modeli indirir, doğrular ve dest_dir altına açar (dest_dir/en-tr). Dönüş: model klasörü."""
    dest = Path(dest_dir); dest.mkdir(parents=True, exist_ok=True)
    url = url or (MODEL_RELEASE + MODEL_FILE)
    sha256 = MODEL_SHA256 if sha256 is None else sha256
    if not sha256:                                       # özet sürümle gelmediyse yayımlanan .sha256 dosyasından al
        try:
            with (opener or urllib.request.urlopen)(url + ".sha256", timeout=20) as r:
                sha256 = r.read().decode().split()[0]
        except Exception:
            sha256 = ""
    tmp = dest / "model.download"
    req = urllib.request.Request(url, headers={"User-Agent": "TD2LootAdvisor"})
    h = hashlib.sha256()
    with (opener or urllib.request.urlopen)(req, timeout=60) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0); got = 0
        while True:
            chunk = r.read(1 << 16)
            if not chunk: break
            f.write(chunk); h.update(chunk); got += len(chunk)
            if progress: progress(got, total)
    if sha256 and h.hexdigest() != sha256.lower():
        tmp.unlink(missing_ok=True); raise RuntimeError("SHA-256 mismatch")
    root = dest.resolve()
    with zipfile.ZipFile(tmp) as z:
        for n in z.namelist():                           # yol kaçışına karşı (mutlak yol, sürücü harfi, .., ters eğik çizgi)
            p = n.replace("\\", "/")
            if p.startswith("/") or ":" in p or ".." in Path(p).parts or not (root / p).resolve().is_relative_to(root):
                raise RuntimeError("bad archive")
        z.extractall(dest)
    tmp.unlink(missing_ok=True)
    return dest / "en-tr"
