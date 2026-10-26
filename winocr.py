"""Windows'un kendi OCR'ı (Windows.Media.Ocr) — Windows 10 ve 11'de yerleşik, işlemcide çalışır, ekran kartını yormaz.

Canlı çeviride (özellikle altyazıda) hızlı yol olarak kullanılır. Program ilk kullanımda iki yolu (bu ve RapidOCR)
aynı görüntüde ölçer; bilgisayara hangisi hafifse onu seçer (haftada bir yeniden ölçer).

    w = WinOCR(); w.available → bool;  w.segments(pil_image) → [(metin, (x0,y0,x1,y1), güven)]
"""
import logging
import os

log = logging.getLogger("td2.winocr")


class WinOCR:
    name = "windows"

    def __init__(self, lang="en-US"):
        self.lang = lang; self.engine = None; self.error = None
        self.available = False
        if os.name != "nt": self.error = "not windows"; return
        try:
            from winrt.windows.media.ocr import OcrEngine
            from winrt.windows.globalization import Language
            self.engine = OcrEngine.try_create_from_language(Language(lang)) or OcrEngine.try_create_from_user_profile_languages()
            self.available = self.engine is not None
            if not self.available: self.error = "no OCR language"
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"

    def _recognize(self, img):
        import asyncio
        from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat, BitmapAlphaMode
        from winrt.windows.storage.streams import DataWriter
        im = img.convert("RGBA")
        maxd = int(getattr(self.engine, "max_image_dimension", 2600) or 2600)
        if max(im.size) > maxd:
            k = maxd / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)))
        else:
            k = 1.0
        r, g, b, a = im.split()
        from PIL import Image
        data = Image.merge("RGBA", (b, g, r, a)).tobytes()            # BGRA8
        dw = DataWriter(); dw.write_bytes(data)
        bmp = SoftwareBitmap(BitmapPixelFormat.BGRA8, im.width, im.height, BitmapAlphaMode.PREMULTIPLIED)
        bmp.copy_from_buffer(dw.detach_buffer())

        async def run():
            return await self.engine.recognize_async(bmp)
        return asyncio.run(run()), k

    def words(self, img):
        res, k = self._recognize(img)
        out = []
        for line in res.lines:
            for w in line.words:
                rc = w.bounding_rect
                out.append((w.text, (rc.x / k, rc.y / k, (rc.x + rc.width) / k, (rc.y + rc.height) / k), 1.0))
        return out

    def segments(self, img, scale=None):
        """Sütun duyarlı satırlar (ocr_backend.group_lines ile aynı biçim)."""
        import ocr_backend
        return ocr_backend.group_lines(self.words(img), max_gap=1.6)

    def lines(self, img, scale=None):
        import ocr_backend
        return ocr_backend.group_lines(self.words(img))


def similar(a, b):
    """İki OCR sonucunun metin benzerliği (0-1)."""
    from difflib import SequenceMatcher
    ta = " ".join(x[0] for x in a).lower(); tb = " ".join(x[0] for x in b).lower()
    if not ta and not tb: return 1.0
    return SequenceMatcher(None, ta, tb).ratio()
