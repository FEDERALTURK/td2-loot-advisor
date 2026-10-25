"""Envanter ekranı: kart aşağı kaydırılınca eşyanın adı ve seti listedeki seçili satırdan okunmalı.
Gerçek oyun ekranları (tests/samples/inv_*.jpg). RapidOCR gerekir.   python tests/test_inventory.py"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image
import engine, gamedata, ocr_backend

CASES = [  # dosya, beklenen ad, yuva, set/marka, kart tek başına adı göstermiyor mu
    ("inv_striker_pack_scrolled.jpg", "Striker's Pack", "Backpack", "Striker's Battlegear", True),
    ("inv_unmatched_backpack.jpg", "Unmatched Backpack", "Backpack", "Unit Alloys", False),
]


def main():
    E = ocr_backend.Engine("rapidocr")
    G = gamedata.GameData(str(ROOT / "meta" / "game_data.json"))
    ok = True
    for f, name, slot, base, scrolled in CASES:
        img = Image.open(ROOT / "tests" / "samples" / f).convert("RGB")
        box = engine.find_card(img, E.data, preprocess=False)
        card_text = "\n".join(l for l, _, _ in E.lines(img.crop(box)))
        alone = G.recognize(card_text)
        hint = engine.list_hint(img, box, E.lines)
        text = (hint["name"] + "\n" + (hint["sub"] or "") + "\n" + card_text) if hint else card_text
        it = G.recognize(text)
        got = (it["name"], it["slot"], it.get("gear_set") or it.get("brand"))
        good = got == (name, slot, base) and (not scrolled or alone["name"] in ("?", "") or alone.get("partial") or alone["name"] != name)
        ok &= good
        print("✔" if good else "✖", f, "| card alone:", alone["name"], alone["slot"], "| list:", hint and (hint["name"], hint["sub"]), "->", got)
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
