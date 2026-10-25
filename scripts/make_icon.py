"""Uygulama simgesi (TD2 turuncu elmas) — build/td2.ico üretir. Kullanım: python scripts/make_icon.py <çıktı.ico>"""
import sys
from PIL import Image, ImageDraw


def draw(size):
    s = size * 4                                   # büyük çiz, küçült: kenarlar yumuşak olsun
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=s // 6, fill=(16, 18, 22, 255))
    c, r = s / 2, s * 0.36
    d.polygon([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], fill=(255, 109, 16, 255))
    r2 = r * 0.42
    d.polygon([(c, c - r2), (c + r2, c), (c, c + r2), (c - r2, c)], fill=(16, 18, 22, 255))
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "td2.ico"
    sizes = [16, 24, 32, 48, 64, 128, 256]
    big = draw(256)
    big.save(out, format="ICO", sizes=[(n, n) for n in sizes])
    print("icon:", out)
