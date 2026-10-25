"""Hızlı ekran yakalama.

- Her iş parçacığı için tek, kalıcı bir mss nesnesi (her yakalamada yeniden açılmaz).
- Boşta döngünün "ekran değişti mi?" özeti, tam görüntü Python görüntüsüne çevrilmeden ham piksellerden
  seyrek örnekleme + blok ortalamasıyla hesaplanır (numpy). Tam görüntü yalnız okuma yapılacağı zaman üretilir.

    g = Grabber()
    h = g.thumb(region)          # 24×24 gri özet (liste), eski thumb() ile aynı ölçek
    img = g.grab(region)         # PIL RGB
"""
import threading

from PIL import Image

N = 24


class Grabber:
    def __init__(self):
        self._tls = threading.local()
        self.backend = "mss"

    @staticmethod
    def _factory():
        import mss
        return (getattr(mss, "MSS", None) or mss.mss)()

    def keep(self):
        """Bu iş parçacığı için kalıcı yakalayıcı aç (uzun süren döngüler). Bitince release() çağrılmalı."""
        if getattr(self._tls, "sct", None) is None: self._tls.sct = self._factory()

    def release(self):
        s = getattr(self._tls, "sct", None); self._tls.sct = None
        if s is not None:
            try: s.close()
            except Exception: pass

    def _raw(self, region):
        s = getattr(self._tls, "sct", None)
        if s is None:                             # kısa ömürlü iş parçacığı: aç-yakala-kapat
            with self._factory() as one:
                return one.grab(region)
        try:
            return s.grab(region)
        except Exception:                         # ekran düzeni değişmiş olabilir: bir kez yeniden aç
            self.release(); self.keep()
            return self._tls.sct.grab(region)

    def grab(self, region):
        s = self._raw(region)
        return Image.frombytes("RGB", s.size, s.bgra, "raw", "BGRX")

    def thumb(self, region):
        """24×24 gri özet; eski ImageOps.grayscale(img).resize((24, 24)) ile aynı değer aralığı (0-255)."""
        s = self._raw(region)
        w, h = s.size
        try:
            import numpy as np
            a = np.frombuffer(s.bgra, dtype=np.uint8).reshape(h, w, 4)
            step = max(1, min(w, h) // (N * 8))   # hücre başına ~8×8 örnek
            sub = a[::step, ::step, :3].astype(np.float32)
            g = sub[..., 2] * 0.299 + sub[..., 1] * 0.587 + sub[..., 0] * 0.114
            gh, gw = g.shape
            ys = (np.arange(N + 1) * gh) // N; xs = (np.arange(N + 1) * gw) // N
            out = np.add.reduceat(np.add.reduceat(g, ys[:-1], axis=0), xs[:-1], axis=1)
            cnt = np.outer(np.diff(ys), np.diff(xs))
            return [int(v) for v in (out / np.maximum(cnt, 1)).ravel()]
        except ImportError:
            img = Image.frombytes("RGB", s.size, s.bgra, "raw", "BGRX")
            return list(img.convert("L").resize((N, N)).getdata())


_default = None


def default():
    global _default
    if _default is None: _default = Grabber()
    return _default
