"""OCR motorları: RapidOCR (PP-OCR, ONNX) ve Tesseract — tek arayüz.

RapidOCR oyun kartlarında Tesseract'tan belirgin şekilde daha isabetli (gerçek kartlarla ölçüldü:
1080p %100'e karşı %82-94, 720p %96-100'e karşı %61-76, 480p %80-95'e karşı %14-23 kelime isabeti),
eşik/ön işleme gerektirmez ve Tesseract kurulumu istemez. Kurulu değilse Tesseract'a düşülür.

    eng = Engine("auto", rec_lang="en")
    eng.text(img)  -> "satır\\nsatır"          (kart metni, satırlar yukarıdan aşağıya)
    eng.lines(img) -> [(metin, (x0, y0, x1, y1), güven)]
    eng.data(img)  -> pytesseract.image_to_data(DICT) biçiminde kelime kutuları (find_card için)
"""
import logging
import re
import threading

log = logging.getLogger("td2.ocr")

ENGINES = ("auto", "rapidocr", "tesseract")
# oyun dili -> RapidOCR tanıma modeli (PP-OCRv5 mobil). "en" için paketle gelen PP-OCRv6 kullanılır.
REC_LANGS = {"en": "default", "latin": "latin", "cyrillic": "eslav"}
GAME_LANG_TO_REC = {"en": "en", "tr": "latin", "de": "latin", "fr": "latin", "es": "latin", "it": "latin",
                    "pt": "latin", "pl": "latin", "nl": "latin", "ru": "cyrillic"}

_rapid_cache = {}
_rapid_lock = threading.Lock()
_rapid_error = None


def rapid_available():
    try:
        import rapidocr  # noqa: F401
        import onnxruntime  # noqa: F401
        return True
    except Exception:
        return False


def tesseract_available():
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _rapid(rec_lang="en"):
    """RapidOCR örneği (modeller ilk kullanımda yüklenir, ilk kez indirilir ~15 MB)."""
    global _rapid_error
    key = REC_LANGS.get(rec_lang, "default")
    with _rapid_lock:
        if key in _rapid_cache:
            return _rapid_cache[key]
        from rapidocr import RapidOCR
        params = {"Global.log_level": "error", "Global.use_cls": False}   # kart yazısı hep düz: açı modeli gereksiz (~%10 hız)
        if key != "default":
            from rapidocr import LangRec, OCRVersion, ModelType
            params.update({"Rec.lang_type": getattr(LangRec, key.upper()),
                           "Rec.ocr_version": OCRVersion.PPOCRV5, "Rec.model_type": ModelType.MOBILE})
        try:
            eng = RapidOCR(params=params)
        except Exception as e:                       # dil modeli indirilemedi: varsayılan modele düş
            _rapid_error = f"{type(e).__name__}: {e}"
            log.warning("RapidOCR model '%s' failed (%s); using default", key, e)
            if key == "default": raise
            eng = _rapid_cache.get("default") or RapidOCR(params={"Global.log_level": "error", "Global.use_cls": False})
        _rapid_cache[key] = eng
        return eng


def _np(img):
    import numpy as np
    return np.asarray(img.convert("RGB"))


def _fix(t):
    """Latin modelleri ondalığı virgülle okuyabiliyor: '+15,0%' -> '+15.0%'."""
    return re.sub(r"(\d),(\d)", r"\1.\2", t)


def group_lines(items):
    """[(metin, (x0,y0,x1,y1), güven)] kutularını satırlara topla (aynı yükseklikteki kutular tek satır)."""
    items = sorted(items, key=lambda it: ((it[1][1] + it[1][3]) / 2, it[1][0]))
    rows, cur, cy, ch = [], [], None, 0
    for it in items:
        y = (it[1][1] + it[1][3]) / 2; h = it[1][3] - it[1][1]
        if cy is not None and abs(y - cy) > 0.6 * max(h, ch):
            rows.append(cur); cur = []
        if not cur: cy, ch = y, h
        cur.append(it)
    if cur: rows.append(cur)
    out = []
    for r in rows:
        r.sort(key=lambda it: it[1][0])
        out.append((" ".join(it[0] for it in r),
                    (min(it[1][0] for it in r), min(it[1][1] for it in r),
                     max(it[1][2] for it in r), max(it[1][3] for it in r)),
                    min(it[2] for it in r)))
    return out


class Engine:
    def __init__(self, name="auto", rec_lang="en", tess_lang="eng", tess_config="--psm 6", preprocess=None):
        self.requested = name if name in ENGINES else "auto"
        self.rec_lang = rec_lang if rec_lang in REC_LANGS else "en"
        self.tess_lang, self.tess_config = tess_lang, tess_config
        self.preprocess = preprocess                 # Tesseract için ön işleme (gamedata.text_image)
        self.name = self._resolve()

    def _resolve(self):
        if self.requested == "tesseract": return "tesseract"
        if self.requested == "rapidocr": return "rapidocr" if rapid_available() else "tesseract"
        return "rapidocr" if rapid_available() else "tesseract"

    def warm_up(self):
        """Modeli arka planda yükle (ilk taramada bekleme olmasın)."""
        if self.name != "rapidocr": return
        def go():
            try:
                from PIL import Image
                _rapid(self.rec_lang)(_np(Image.new("RGB", (64, 32))))
            except Exception as e:
                log.warning("RapidOCR warm-up failed: %s", e)
        threading.Thread(target=go, daemon=True).start()

    # ------------------------------------------------------------ RapidOCR
    def _rapid_boxes(self, img, scale=1.0):
        from PIL import Image
        src = img
        if scale != 1.0:
            src = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        r = _rapid(self.rec_lang)(_np(src))
        if r is None or r.txts is None: return []
        out = []
        for box, txt, conf in zip(r.boxes, r.txts, r.scores):
            xs = [p[0] / scale for p in box]; ys = [p[1] / scale for p in box]
            out.append((_fix(str(txt)), (min(xs), min(ys), max(xs), max(ys)), float(conf)))
        return out

    @staticmethod
    def auto_scale(img):
        """Küçük kartlarda (720p ve altı) metni büyüt: algılayıcı ~20 px harf yüksekliğini sever."""
        h = img.height
        return 2.0 if h < 420 else 1.5 if h < 700 else 1.0

    def lines(self, img, scale=None):
        if self.name == "rapidocr":
            try:
                return group_lines(self._rapid_boxes(img, self.auto_scale(img) if scale is None else scale))
            except Exception as e:
                log.exception("RapidOCR failed, falling back to Tesseract: %s", e)
                self.name = "tesseract"
        txt = self._tess_text(img)
        return [(l, (0, 0, 0, 0), 1.0) for l in txt.splitlines() if l.strip()]

    def text(self, img, scale=None):
        return "\n".join(t for t, _, _ in self.lines(img, scale))

    def _tess_text(self, img):
        import pytesseract
        pre = self.preprocess(img) if self.preprocess else img
        return pytesseract.image_to_string(pre, lang=self.tess_lang, config=self.tess_config)

    def data(self, img):
        """Kelime kutuları, pytesseract.Output.DICT biçiminde (text/conf/left/top/width/height)."""
        if self.name == "rapidocr":
            try:
                d = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}
                for txt, (x0, y0, x1, y1), conf in self._rapid_boxes(img):
                    words = txt.split() or [txt]
                    total = sum(len(w) for w in words) + len(words) - 1 or 1
                    cx = x0
                    for w in words:                  # kutuyu kelimelere harf sayısına göre böl
                        ww = (x1 - x0) * len(w) / total
                        d["text"].append(w); d["conf"].append(conf * 100)
                        d["left"].append(int(cx)); d["top"].append(int(y0))
                        d["width"].append(max(1, int(ww))); d["height"].append(max(1, int(y1 - y0)))
                        cx += ww + (x1 - x0) / total
                return d
            except Exception as e:
                log.exception("RapidOCR data failed, falling back to Tesseract: %s", e)
                self.name = "tesseract"
        import pytesseract
        pre = self.preprocess(img) if self.preprocess else img
        d = pytesseract.image_to_data(pre, config="--psm 11", output_type=pytesseract.Output.DICT)
        if self.preprocess and pre.size != img.size:  # ön işleme büyüttüyse kutuları geri ölçekle
            k = img.width / pre.width
            for key in ("left", "top", "width", "height"):
                d[key] = [int(v * k) for v in d[key]]
        return d


# ---------------------------------------------------------------- renk ipuçları (simge/nadirlik)
def _hue_class(pixels):
    """Doygun piksellerin baskın rengi: red / orange / yellow / green / blue / purple / None."""
    import colorsys
    hs = []
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s > 0.45 and v > 0.35: hs.append(h * 360)
    if len(hs) < max(6, len(pixels) // 40): return None
    bins = {"red": 0, "orange": 0, "yellow": 0, "green": 0, "blue": 0, "purple": 0}
    for h in hs:
        if h < 14 or h >= 340: bins["red"] += 1
        elif h < 36: bins["orange"] += 1
        elif h < 65: bins["yellow"] += 1
        elif h < 165: bins["green"] += 1
        elif h < 255: bins["blue"] += 1
        else: bins["purple"] += 1
    return max(bins, key=bins.get)


ICON_CATEGORY = {"red": "offensive", "orange": "offensive", "blue": "defensive", "yellow": "utility"}


def icon_colors(img, lines):
    """Attribute satırlarının solundaki simgenin rengi -> kategori.
    Kırmızı = saldırı (weapon damage, CHC, CHD…), mavi = savunma (armor, health…), sarı = yetenek.
    Dönüş: [(satır metni, 'offensive'|'defensive'|'utility'|None)]"""
    rgb = img.convert("RGB")
    out = []
    for txt, (x0, y0, x1, y1), _ in lines:
        if not re.match(r"^\s*\+?\d+(\.\d+)?\s*%?", txt): continue
        h = max(4, y1 - y0)
        box = (max(0, int(x0 - 2.4 * h)), int(y0), max(1, int(x0 - 0.2 * h)), int(y1))
        if box[2] - box[0] < 3: out.append((txt, None)); continue
        px = list(rgb.crop(box).getdata())
        out.append((txt, ICON_CATEGORY.get(_hue_class(px))))
    return out


RARITY_COLOR = {"yellow": "HIGH-END", "orange": "HIGH-END", "green": "GEAR SET", "red": "EXOTIC",
                "purple": "SUPERIOR", "blue": "SPECIALIZED"}


def rarity_color(img, lines):
    """Kartın başlık şeridinin (adın solundaki dikey renk çubuğu / zemin) rengi -> nadirlik tahmini.
    Yazıdan çıkarılamadığında yardımcı ipucu olarak kullanılır; yazıyla çelişirse yazı kazanır."""
    rgb = img.convert("RGB")
    if not lines: return None
    first = min(lines, key=lambda l: l[1][1])
    _, (x0, y0, x1, y1), _ = first
    h = max(6, y1 - y0)
    box = (0, max(0, int(y0 - h)), max(2, int(x0)), min(rgb.height, int(y1 + 2 * h)))
    if box[2] - box[0] < 2: return None
    return RARITY_COLOR.get(_hue_class(list(rgb.crop(box).getdata())))
