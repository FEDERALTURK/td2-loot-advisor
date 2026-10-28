"""Canlı çeviri: özel adların korunması, OCR satırlarından paragraf, önbellek, model indirme/doğrulama, yapay zekâ yanıtı.
Gerçek model testi için: MT_MODEL_DIR=<en-tr klasörü> python tests/test_livetranslate.py"""
import hashlib, io, json, os, sys, tempfile, time, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import livetranslate as lt  # noqa: E402

fails = 0
def ok(c, m):
    global fails
    print(("OK   " if c else "FAIL ") + m)
    if not c: fails += 1

d = json.loads((ROOT / "meta/game_data.json").read_text(encoding="utf-8"))
names = list(d["exotics"]) + list(d["named"]) + list(d["gear_sets"]) + list(d["brands"]) + list(d["gear_talents"]) + list(d["weapon_talents"])
g = lt.Glossary(names)
m, found = g.mask("Equip Eagle Bearer and Striker's Battlegear, then fight the Black Tusk in the Dark Zone.")
ok(found == ["Eagle Bearer", "Striker's Battlegear", "Black Tusk", "Dark Zone"] and "Eagle" not in m, "özel adlar maskelendi (uzun ad önce)")
ok(g.unmask("ZQ0'ı ve Z Q1'i kuşan, sonra ZQ3'de ZQ2 ile savaş.", found) ==
   "Eagle Bearer'ı ve Striker's Battlegear'i kuşan, sonra Dark Zone'de Black Tusk ile savaş.", "ad geri konuldu, Türkçe ek korunuyor")
ok(g.mask("Kenly College")[1] == ["Kenly College"] and g.mask("agentless")[1] == [], "kelime sınırları")

proper = lt.load_proper_names([ROOT / "meta" / "proper_names.json"])
story = lt.Glossary(proper_names=proper)
name_data = json.loads((ROOT / "meta" / "proper_names.json").read_text(encoding="utf-8"))
source_ids = set(name_data["sources"])
ok(all(e.get("source") in source_ids for e in proper) and
   all(name_data["sources"][s].startswith("https://") for s in source_ids),
   "özel adların tüm kaynak anahtarları geçerli ve HTTPS")
variants = [v.casefold() for e in proper for v in [e["name"], *e.get("aliases", [])]]
ok(len(variants) == len(set(variants)), "özel adlar ve kısa adlar çakışmıyor")
masked, found = story.mask("Faye Lau warned Aaron Keener. She told him they would not trust him.")
ok(found == ["Faye Lau", "Aaron Keener"] and all(p in masked for p in ("She", "him", "they")),
   "öykü özel adları korunur, zamirler İngilizce token olarak maskelenmez")
ok(lt.PERSONAL_PRONOUN_RE.search("Who told them that?"),
   "soru, ilgi ve işaret zamirleri de bağlam korumasını tetikler")
ok(story.pronoun_hints(found) == ["Faye Lau uses she/her"] and "Mel Arnold uses they/them" in
   story.pronoun_hints(["Mel Arnold"]), "yalnız kaynakta doğrulanan karakter zamirleri bağlama eklenir")
ok("singular they" in lt.AIMT.SYSTEM and "referent" in lt.AIMT.SYSTEM,
   "AI yönergesi kişi ve tekil/çoğul gönderimini korur")

lines = [("Agent, the Black Tusk have taken", (100, 500, 700, 530), 0.95), ("control of the Capitol Building.", (102, 534, 690, 562), 0.93),
         ("MAP", (20, 20, 60, 40), 0.99), ("250 / 300", (900, 20, 980, 40), 0.99), ("Ajan, Türkçe çeviri", (100, 300, 400, 330), 0.99),
         ("Head to the safe house.", (100, 700, 500, 730), 0.9), ("x", (5, 5, 9, 9), 0.4)]
b = lt.blocks_from_lines(lines, ["map"])
ok([x[0] for x in b] == ["Agent, the Black Tusk have taken control of the Capitol Building.", "Head to the safe house."],
   "satırlar paragrafa birleşti; arayüz kelimesi, sayılar ve Türkçe (kendi kaplamamız) atıldı")
ok(lt.split_sentences("Go there. Then talk to him! 5.5 percent.") == ["Go there.", "Then talk to him!", "5.5 percent."], "cümlelere bölme")
ok(lt.clean_for_mt("Buff lasts 15s — “great”…") == 'Buff lasts 15 seconds  -  "great"...', "model sözlüğü için sadeleştirme")

class Fake:
    name = "local"; calls = []
    def translate(self, texts):
        self.calls.append(list(texts)); return [x.replace("Equip", "kuşan").replace("Go", "git") + " ⁇" for x in texts]
cache = lt.Cache(os.path.join(tempfile.mkdtemp(), "c.json"))
tr = lt.Translator(Fake(), g, cache)
out = tr.translate(["Equip Eagle Bearer now.\n• Go fast.", "Equip Eagle Bearer now.\n• Go fast."])
ok(out[0] == "Kuşan Eagle Bearer now.\n• Git fast." and out[1] == out[0], "satır/madde korunur, ⁇ temizlenir, büyük harf")
ok(Fake.calls[0] == ["Equip ZQ0 now.", "Go fast."], "modele maskeli ve maddesiz cümleler gitti")
tr.translate(["Faye Lau warned Aaron Keener. She told him she would stop him."])
ok(Fake.calls[-1] == ["ZQ0 warned ZQ1. She told him she would stop him."],
   "zamirli çok cümleli satır bağlam kaybolmasın diye birlikte çevrilir")
n = len(Fake.calls); tr.translate(["Equip Eagle Bearer now.\n• Go fast."])
ok(len(Fake.calls) == n, "önbellekten geldi (model çağrılmadı)")
cache.save(); ok(lt.Cache(cache.path).get(tr.ck, "Equip Eagle Bearer now.\n• Go fast.") == out[0], "önbellek diske yazıldı")

ai = lt.AIMT(lambda sys_, user: 'Sure: ["Birinci", "İkinci"]')
ok(ai.translate(["a", "b"]) == ["Birinci", "İkinci"], "yapay zekâ JSON yanıtı ayrıştırıldı")
seen = {}
ai_hints = lt.AIMT(lambda system, user: seen.update(system=system, user=user) or '["Ona söyledi."]')
ok(ai_hints.translate(["ZQ0 told ZQ1."], [["Faye Lau uses she/her"]]) == ["Ona söyledi."] and
   "Faye Lau uses she/her" in seen["system"], "AI çevirisine yalnız doğrulanmış zamir bilgisi verilir")
try: lt.AIMT(lambda s, u: "nonsense").translate(["a", "b"]); ok(False, "biçim")
except RuntimeError: ok(True, "bozuk yapay zekâ yanıtı hata verir")

# model indirme + SHA-256 + yol kaçışı
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    for f in ("model.bin", "source.spm", "target.spm"): z.writestr("en-tr/" + f, "x")
data = buf.getvalue(); sha = hashlib.sha256(data).hexdigest()
class R(io.BytesIO):
    headers = {"Content-Length": str(len(data))}
    def __enter__(self): return self
    def __exit__(self, *a): pass
dst = tempfile.mkdtemp(); prog = []
p = lt.download_model(dst, lambda a, b_: prog.append(a), url="https://x/m.zip", sha256=sha, opener=lambda *a, **k: R(data))
ok(lt.LocalMT(p).installed() and prog and prog[-1] == len(data), "model indirildi, açıldı, ilerleme bildirildi")
try: lt.download_model(tempfile.mkdtemp(), url="https://x/m.zip", sha256="0" * 64, opener=lambda *a, **k: R(data)); ok(False, "sha")
except RuntimeError: ok(True, "yanlış SHA-256 reddedildi")
buf2 = io.BytesIO()
with zipfile.ZipFile(buf2, "w") as z: z.writestr("../evil.txt", "x")
d2 = buf2.getvalue()
try: lt.download_model(tempfile.mkdtemp(), url="https://x/m.zip", sha256=hashlib.sha256(d2).hexdigest(), opener=lambda *a, **k: R(d2)); ok(False, "zip")
except RuntimeError: ok(True, "arşivden dışarı yazma girişimi reddedildi")

md = os.environ.get("MT_MODEL_DIR")
if md:
    real = lt.Translator(lt.LocalMT(md), g, lt.Cache(None))
    t0 = time.time()
    r = real.translate(["Agent, the Black Tusk have taken control of the Capitol Building. Head to the safe house.",
                        "Headshot kills grant a buff for 15s.\n• +30% accuracy"])
    dt = time.time() - t0
    print("   ", r)
    ok("Black Tusk" in r[0] and "Ajan" in r[0] and "gid" in r[0] and "saniye" in r[1] and r[1].count("\n") == 1,
       f"gerçek model: anlamlı Türkçe, adlar korundu ({dt:.1f}s)")
    ok(all(not any(w * 3 in x for w in x.split()[:3]) for x in r), "tekrar eden çıktı yok")
# --- 5.1.7: başlık / liste satırları, sayaçlar, ikon harfi, sandık adları, kelime düzeltmeleri
L = [("Objective", (10, 120, 120, 144), .99), ("Complete the Roosevelt Island", (10, 150, 300, 174), .99),
     ("00/01", (320, 150, 360, 174), .99), ("mission on Legendary difficulty", (10, 178, 300, 202), .99),
     ("Rewards", (10, 220, 110, 244), .99), ("X Recalibration Cache", (10, 250, 260, 274), .95),
     ("Gear Crafting Cache", (10, 278, 240, 302), .99),
     ("Weekly Legendary", (10, 0, 300, 40), .99), ("Mission", (10, 42, 150, 82), .99)]
bl = lt.blocks_from_lines(L)
txt = [b[0] for b in bl]
ok(txt[0] == "Weekly Legendary Mission", "büyük başlığın satırları birleşti: %r" % txt[0])
ok(any(t.startswith("Objective\nComplete the Roosevelt Island") and "mission on Legendary difficulty" in t for t in txt), "başlık ayrı satır, paragraf birleşik")
ok(any(t.endswith("Rewards\nRecalibration Cache\nGear Crafting Cache") for t in txt), "liste satırları ayrı, ikon harfi atıldı: %r" % txt)

class Echo:
    name = "local"; calls = []
    def translate(self, texts):
        Echo.calls.append(list(texts))
        return [x.replace("Complete the", "Tamamla:").replace("mission on", "misyonunu") .replace("difficulty", "zorluğu üzerinde") for x in texts]
g2 = lt.Glossary(["Roosevelt Island"])
tr2 = lt.Translator(Echo(), g2, lt.Cache(None))
o = tr2.translate(["Objective\nComplete the Roosevelt Island 00/01 mission on Legendary difficulty", "Rewards\nGear Crafting Cache"])
ok(o[0].startswith("Hedef\n") and o[0].endswith("(00/01)") and "00/01 " not in o[0], "sabit başlık + sayaç sona: %r" % o[0])
ok("görevini" in o[0] and "misyon" not in o[0], "misyon → görev düzeltmesi: %r" % o[0])
ok(o[1] == "Ödüller\nGear Crafting Cache", "sandık adı olduğu gibi kaldı: %r" % o[1])
ok(all("Cache" not in u for c in Echo.calls for u in c if "ZQ" not in u), "sandık adları modele gitmedi")

print("RESULT:", "PASS" if not fails else f"FAIL ({fails})"); sys.exit(1 if fails else 0)
