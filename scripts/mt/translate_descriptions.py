"""Ansiklopedi açıklamalarının Türkçe makine çevirisi (ilk tohum). Diğer diller ve iyileştirme günlük görevde.
    python scripts/mt/translate_descriptions.py <ct2_model_dir> meta/descriptions_i18n.json
"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import knowledge, livetranslate

model_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
d = json.loads((ROOT / "meta/game_data.json").read_text(encoding="utf-8"))
enc = knowledge.Encyclopedia(d, [ROOT / "meta/sources"])
names = list(d.get("exotics", [])) + list(d.get("named", [])) + list(d.get("gear_sets", [])) + list(d.get("brands", [])) + \
        list(d.get("gear_talents", [])) + list(d.get("weapon_talents", [])) + list(d.get("weapon_index", {}).keys()) + list(d.get("items", {})) + list(d.get("skills", [])) + \
        [v["talent"] for v in d.get("items", {}).values() if v.get("talent")] + \
        [e["talent"] for e in enc.entries if e.get("talent")]
eng = livetranslate.LocalMT(model_dir)
tr = livetranslate.Translator(eng, livetranslate.Glossary(names), livetranslate.Cache(None, size=100000))
old = {}
if out.exists():
    try: old = json.loads(out.read_text(encoding="utf-8")).get("items", {})
    except ValueError: pass
todo = [(e["cat"], e["name"], e["desc"]) for e in enc.entries if e.get("desc")]
items = dict(old); t0 = time.time(); n = 0
for i in range(0, len(todo), 24):
    chunk = [x for x in todo[i:i + 24] if not (old.get(x[1], {}).get("tr"))]
    if not chunk: continue
    res = tr.translate([x[2] for x in chunk])
    for (cat, name, desc), r in zip(chunk, res):
        items.setdefault(name, {})["tr"] = r; items[name]["_src"] = desc[:80]; items[name]["_mt"] = "tr"; n += 1
print(f"translated {n} descriptions in {time.time() - t0:.0f}s")
out.write_text(json.dumps({"schema": 1, "version": time.strftime("%Y-%m-%d.1", time.gmtime()), "note":
    "Encyclopedia description translations. 'tr' seeded by OPUS-MT machine translation; other languages and reviews by the daily feed task.",
    "items": items}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
for name in list(items)[:5]: print(name, "→", items[name]["tr"][:160])
