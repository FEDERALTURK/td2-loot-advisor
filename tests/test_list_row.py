"""Kart kaydırılmış (başlığı görünmüyor) ya da başlık çok yukarıda: eşya adı/seti envanter listesindeki seçili
(turuncu) satırdan okunmalı.   python tests/test_list_row.py   (RapidOCR gerekir)"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image
import engine, gamedata, ocr_backend

E = ocr_backend.Engine("rapidocr")
G = gamedata.GameData(str(ROOT / "meta" / "game_data.json"))
ok = True
for f in ("list_scrolled_a.jpg", "list_scrolled_b.jpg"):
    im = Image.open(ROOT / "tests" / "samples" / f).convert("RGB")
    box = engine.find_card(im, E.data, preprocess=False)
    text = E.text(im.crop(box))
    it = G.recognize(text)
    if it.get("partial") or it.get("name") == "?" or not it.get("slot"):
        row = engine.find_selected_row(im, box)
        hdr = engine.selected_row_header(E.text(im.crop(row)).splitlines()) if row else []
        it = G.recognize("\n".join(hdr) + "\n" + text)
        how = f"list row {hdr}"
    else:
        how = "card header"
    good = (it["name"], it["slot"], it.get("gear_set")) == ("Striker's Pack", "Backpack", "Striker's Battlegear")
    ok &= good
    print("✔" if good else "✖", f, how, "->", it["name"], it["slot"], it.get("gear_set"), it["attrs"])
sys.exit(0 if ok else 1)
