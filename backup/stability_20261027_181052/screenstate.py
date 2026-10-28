"""Oyun ekranının durumu: menü (envanter / satıcı / sandık), yükleme, dünya (oyun içi).

Yalnız ekran görüntüsünden çalışır (oyunun belleğine / dosyalarına dokunmaz).

Nasıl çalışır
  - Yükleme: neredeyse tamamen siyah, düz kare.
  - Menü: program bir eşya kartını başarıyla okuduğunda o anki ekranın ÜST ŞERİDİNİN (sekme / başlık çubuğu)
    kenar imzası öğrenilir. Sonraki karelerde üst şerit öğrenilmiş imzalardan birine benziyorsa "menu".
    Böylece oyunun dili, çözünürlüğü ve arayüz ölçeği ne olursa olsun kendini ayarlar; sabit metin aranmaz.
  - Dünya: en az bir imza öğrenildikten sonra hiçbirine benzemeyen, yüklemede olmayan kareler.
  - Henüz imza yoksa: "unknown" (program eski davranışla tarar).
Kararlar titremesin diye aynı durum art arda en az 2 kez görülünce değişir.
"""
import json
import os
import time

import numpy as np

W = 160                 # küçük kare genişliği
STRIP = 0.11            # üst şerit oranı
MATCH = 0.62            # imza benzerlik eşiği (kenar haritaları arası korelasyon)
MAX_TEMPLATES = 16
STATES = ("unknown", "menu", "world", "loading")


def small_gray(bgra, w, h, width=W):
    """Ham BGRA tamponundan (mss) gri, küçük kare (float32 0..1). Tam görüntü üretmeden."""
    a = np.frombuffer(bgra, dtype=np.uint8).reshape(h, w, 4)
    step = max(1, w // (width * 2))
    sub = a[::step, ::step, :3].astype(np.float32)
    g = (sub[..., 2] * 0.299 + sub[..., 1] * 0.587 + sub[..., 0] * 0.114) / 255.0
    gh, gw = g.shape
    out_w = width; out_h = max(8, int(round(width * h / w)))
    ys = (np.arange(out_h + 1) * gh) // out_h; xs = (np.arange(out_w + 1) * gw) // out_w
    s = np.add.reduceat(np.add.reduceat(g, ys[:-1], axis=0), xs[:-1], axis=1)
    return (s / np.maximum(np.outer(np.diff(ys), np.diff(xs)), 1)).astype(np.float32)


def from_image(img, width=W):
    """PIL görüntüsünden aynı küçük kare (testler / dosyalar için)."""
    g = img.convert("L"); h = max(8, int(round(width * g.height / g.width)))
    return np.asarray(g.resize((width, h)), dtype=np.float32) / 255.0


def signature(small):
    """Üst şeridin kenar imzası: yatay+dikey gradyan büyüklüğü, ortalaması çıkarılmış ve normlanmış vektör."""
    n = max(4, int(round(small.shape[0] * STRIP)))
    s = small[:n]
    gx = np.abs(np.diff(s, axis=1))[:-1, :]; gy = np.abs(np.diff(s, axis=0))[:, :-1]
    e = (gx + gy).ravel()
    e = e - e.mean(); nrm = float(np.linalg.norm(e))
    return (e / nrm).astype(np.float32) if nrm > 1e-4 else None


def similarity(a, b):
    if a is None or b is None or a.shape != b.shape: return 0.0
    return float(np.dot(a, b))


def is_loading(small):
    return float(small.mean()) < 0.06 and float(small.std()) < 0.05


class Detector:
    def __init__(self, path=None):
        self.path = str(path) if path else None
        self.templates = {}           # boyut anahtarı → [imza listesi]
        self.state, self._cand, self._n = "unknown", None, 0
        self.score, self.since = 0.0, time.time()
        self._load()

    # ---- kalıcılık
    def _load(self):
        if not self.path: return
        try:
            with open(self.path, encoding="utf-8") as f: d = json.load(f)
            for k, lst in d.get("templates", {}).items():
                self.templates[k] = [np.asarray(v, dtype=np.float32) for v in lst][-MAX_TEMPLATES:]
        except (OSError, ValueError):
            pass

    def save(self):
        if not self.path: return
        d = {"v": 1, "templates": {k: [np.round(v, 4).tolist() for v in lst] for k, lst in self.templates.items()}}
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(d, f)
        os.replace(tmp, self.path)

    def reset(self):
        self.templates = {}; self.state = "unknown"
        if self.path:
            try: os.remove(self.path)
            except OSError: pass

    @staticmethod
    def _key(small):
        return f"{small.shape[1]}x{small.shape[0]}"

    def learned(self, small=None):
        return len(self.templates.get(self._key(small), [])) if small is not None else sum(map(len, self.templates.values()))

    # ---- öğrenme ve sınıflama
    def learn(self, small):
        """Eşya kartı başarıyla okunduğunda çağrılır: bu ekran bir menüdür."""
        sig = signature(small)
        if sig is None or is_loading(small): return False
        lst = self.templates.setdefault(self._key(small), [])
        if any(similarity(sig, t) > 0.9 for t in lst): return False      # zaten biliniyor
        lst.append(sig); del lst[:-MAX_TEMPLATES]
        try: self.save()
        except OSError: pass
        return True

    def classify(self, small):
        """Tek kare için (durum, puan) — titreme süzgeci olmadan."""
        if is_loading(small): return "loading", 1.0
        lst = self.templates.get(self._key(small))
        if not lst: return "unknown", 0.0
        sig = signature(small)
        best = max((similarity(sig, t) for t in lst), default=0.0)
        return ("menu" if best >= MATCH else "world"), best

    def observe(self, small):
        st, self.score = self.classify(small)
        if st == self.state:
            self._cand, self._n = None, 0
        elif st == self._cand:
            self._n += 1
            if self._n >= 2 or st == "menu" and self.score > 0.85:
                self.state, self.since, self._cand, self._n = st, time.time(), None, 0
        else:
            self._cand, self._n = st, 1
            if st == "menu" and self.score > 0.85:                        # güçlü eşleşme: hemen
                self.state, self.since, self._cand, self._n = st, time.time(), None, 0
        return self.state
