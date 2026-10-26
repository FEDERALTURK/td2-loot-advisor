"""Yerinde çeviri yerleşimi (overlay.py) — Tk gerektirmez.   python tests/test_overlay.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import overlay  # noqa: E402
import livetranslate as lt  # noqa: E402

fails = 0


def ok(c, m):
    global fails
    print(("OK   " if c else "FAIL ") + m)
    if not c: fails += 1


def measure_at(pt):                      # yaklaşık: harf genişliği 0.55 em, satır 1.3 em (px)
    px = pt / 0.75
    return (lambda s: len(s) * px * 0.55), px * 1.3


area = {"left": 0, "top": 0, "width": 1568, "height": 656}
ok(overlay.wrap("Haftalık Legendary Görevi", 80, lambda s: len(s) * 8) == ["Haftalık", "Legendary", "Görevi"], "satır kaydırma")
ok(overlay.wrap("Hedef\nGörevi tamamla", 1000, len) == ["Hedef", "Görevi tamamla"], "satır sonları korunur")

pt, lines, h = overlay.fit("Kısa", 200, 36, measure_at, 14)
ok(pt == 14 and lines == ["Kısa"] and h == 36, "sığan metin aynı puntoda")
pt, lines, h = overlay.fit("Roosevelt Adası'na taşınan özel kuvvetleri yenebilecek her ajan için özel bir eşyamız var.", 230, 52, measure_at, 14)
ok(pt < 14 and pt >= overlay.MIN_PT, "uzun Türkçe: punto küçüldü (%d)" % pt)
pt2, lines2, h2 = overlay.fit("Çok uzun bir metin " * 12, 120, 20, measure_at, 14)
ok(pt2 == overlay.MIN_PT and h2 > 20, "en küçük puntoda da sığmazsa kutu aşağı uzadı (%d px)" % h2)

# gerçek harita ekranı: OCR → bloklar → (sahte) çeviri → yerleşim
L = json.loads((ROOT / "tests/samples/tasks/map_projects_full.json").read_text())["lines"]
blocks = lt.blocks_from_lines([tuple(x) for x in L])
fake = {"Rewards\nExotic Cache\nRecalibration Cache\nRecalibration Cache\nGear Crafting Cache\nOptimization Cache":
        "Ödüller\nExotic Cache\nRecalibration Cache\nRecalibration Cache\nGear Crafting Cache\nOptimization Cache"}
body = lt.BODY_H[0]
items = overlay.layout([(fake.get(en, en.upper() + " (TR)"), b, en, max(1, en.count("\n") + 1, round((b[3] - b[1]) / (body * 1.15))))
                        for en, b, _ in blocks], area, measure_at)
ok(len(items) == len(blocks), "her bloğa bir kutu (%d)" % len(items))
ok(all(0 <= i["x"] and i["x"] + i["w"] <= area["width"] and 0 <= i["y"] and i["y"] + i["h"] <= area["height"] for i in items), "kutular ekran içinde")
over = 0
for a in items:
    for b in items:
        if a is not b and a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]:
            over += 1
ok(over <= 2, "kutular üst üste binmiyor (%d çakışma)" % over)
same = overlay.layout([("Exotic Cache", (10, 10, 100, 30), "Exotic Cache", 1)], area, measure_at)
ok(same == [], "çeviri özgünle aynıysa kutu çizilmez (oyunun yazısı görünür)")
menu = overlay.layout([("Haritayı kapat", (500, 600, 560, 616), "Close Map", 1)], area, measure_at)
ok(menu and menu[0]["kind"] == "menu" and menu[0]["w"] >= 60 + 2 * overlay.PAD, "menü satırı kendi yerinde")

print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
sys.exit(1 if fails else 0)
