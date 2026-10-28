"""Bilgi içeriği: ansiklopedi, yarışma (cevaplar veriden doğrulanır), haber akışı, sıfırlama sayaçları, ses paketleri.
    python tests/test_knowledge.py"""
import json, os, random, sys, tempfile, wave
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import knowledge, voicepack, meta_sync  # noqa: E402

fails = 0
def ok(c, m):
    global fails
    print(("OK   " if c else "FAIL ") + m)
    if not c: fails += 1

d = json.loads((ROOT / "meta/game_data.json").read_text(encoding="utf-8"))
enc = knowledge.Encyclopedia(d, [ROOT / "meta/sources"])
c = enc.counts()
ok(c["exotic"] >= 70 and c["named"] >= 150 and c["gear_set"] >= 25 and c["brand"] >= 35 and c["talent"] >= 200, f"ansiklopedi dolu: {c}")
r = enc.search("striker", cat="gear_set")
ok(r and r[0]["name"] == "Striker's Battlegear" and len(r[0]["pieces"]) == 6 and r[0]["talent"], "gear set: parçalar + 4 parça yeteneği")
r = enc.search("ninjabike")
ok(len(r) >= 2 and all(e["cat"] == "exotic" for e in r), "arama: egzotikler")
ok(not any("thumb|" in e.get("desc", "") or "100px" in e.get("desc", "") for e in enc.entries), "wiki işaretleri temizlendi")
tal = sum(1 for e in enc.entries if e["cat"] == "talent" and e["desc"]) / c["talent"]
ok(tal > 0.8, f"yeteneklerin %{int(tal*100)}'inde açıklama var")
br = enc.by_key[("brand", "5.11 Tactical")]
ok(br["bonuses"] and enc.related(br), "marka: bonuslar + ilgili adlı eşyalar")

# yarışma: her soru tipinin cevabı veriden bağımsız olarak doğrulanır
rng = random.Random(1); quiz = knowledge.Quiz(enc, rng)
bad = 0
for i in range(300):
    q = quiz.make()
    if not q or q["right"] not in q["options"] or len(set(q["options"])) != 4: bad += 1; continue
    a, k = q["args"], q["kind"]
    if k == "exotic_slot": good = enc.by_key[("exotic", a["name"])]["slot"] == q["right"]
    elif k == "brand_bonus": good = d["brand_bonuses"][a["name"]][0] == q["right"]
    elif k == "set_talent": good = any(x.endswith(q["right"]) for x in d["gear_set_bonuses"][a["name"]])
    elif k == "weapon_type": good = d["weapon_index"][a["name"]]["type"] == q["right"]
    elif k == "named_brand": good = d["items"][a["name"]]["brand"] == q["right"]
    else: good = q["right"] in enc.talent_desc
    if not good: bad += 1
    if k == "talent_desc" and any(w.lower() in a["desc"].lower() for w in q["right"].split() if len(w) > 3): bad += 1
ok(bad == 0, f"300 soru: doğru cevap seçeneklerde, 4 farklı seçenek, cevap veriyle tutarlı, açıklama cevabı ele vermiyor (hata {bad})")
kinds = {quiz.make(k)["kind"] for k in knowledge.Quiz.KINDS}
ok(kinds == set(knowledge.Quiz.KINDS), "6 soru tipinin hepsi üretilebiliyor")
ok(knowledge.quiz_level(0)[0] == 1 and knowledge.quiz_level(50)[0] == 2 and knowledge.quiz_level(1000)[0] > 5, "seviye eğrisi")

# haber akışı
raw = json.loads((ROOT / "meta/news_feed.json").read_text(encoding="utf-8"))
f = knowledge.validate_news(raw)
ok(len(f["items"]) == len(raw["items"]) and all(i["url"].startswith("https://") for i in f["items"]), "haber akışı geçerli, her haberin kaynağı var")
ok(all(set(i["title"]) >= {"en", "tr", "de", "fr", "es", "it", "pt", "pl", "ru", "nl"} for i in f["items"]), "haberler 10 dilde")
t0 = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)
st = {it["id"]: s for it, s in knowledge.news_sorted(f["items"], t0)}
ok(st["y8s3-red-moon-unleashed"] == "live" and st["y8s3-vanguard-overdrive"] == "upcoming" and st["tu-y8s3-2"] == "news", "durumlar: canlı / yakında / haber")
order = [s for _, s in knowledge.news_sorted(f["items"], t0)]
ok(order == sorted(order, key=["live", "upcoming", "news", "ended"].index), "sıralama: canlı → yakında → haber")
late = datetime(2026, 11, 20, tzinfo=timezone.utc)
ok(not any(i["id"] == "y8s3-red-moon-unleashed" for i, _ in knowledge.news_sorted(f["items"], late)), "biten etkinlik 3 gün sonra listeden düşer")
evil = {"schema": 1, "items": [{"id": "x<script>", "title": "a"}, {"id": "ok-1", "title": {"en": "t"}, "url": "javascript:alert(1)"}]}
v = knowledge.validate_news(evil)
ok(len(v["items"]) == 1 and v["items"][0]["url"] == "", "kötü kimlik ve https olmayan bağlantı atıldı")
ok(knowledge.pick_lang({"en": "a", "tr": "b"}, "tr") == "b" and knowledge.pick_lang({"en": "a"}, "pl") == "a", "dil seçimi + İngilizce yedeği")
ok(meta_sync.news_urls("")[0].endswith("meta/news_feed.json"), "akış adresi")

# sıfırlama sayaçları (günlük 08:00 UTC, haftalık salı 08:00 UTC)
res = {"daily_hour_utc": 8, "weekly_weekday": 1, "weekly_hour_utc": 8}
dd, ww = knowledge.next_resets(res, datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc))   # pazartesi
ok(dd == datetime(2026, 10, 27, 8, tzinfo=timezone.utc) and ww == datetime(2026, 10, 27, 8, tzinfo=timezone.utc), "pazartesi öğlen: ikisi de salı 08:00")
dd, ww = knowledge.next_resets(res, datetime(2026, 10, 27, 8, 0, 1, tzinfo=timezone.utc))
ok(dd.day == 28 and ww == datetime(2026, 11, 3, 8, tzinfo=timezone.utc), "sıfırlamadan hemen sonra: bir sonraki")
ok(knowledge.fmt_left(timedelta(days=2, hours=3, minutes=4))[0] == "2g 03:04", "süre biçimi")

# meta vitrini
ok(set(knowledge.build_tags({"mode": "PvE / Legendary", "role": "dps"})) >= {"pve", "endgame", "dps"}, "build etiketleri")
ok(knowledge.trend(80, 70) == "up" and knowledge.trend(60, 70) == "down" and knowledge.trend(70, 71) == "" and knowledge.trend(5, None) == "new", "eğilim")

# ses paketleri
L = voicepack.Lines(ROOT / "meta/voice_lines.json")
for code in ("en", "tr", "de", "fr", "es", "it", "pt", "pl", "ru", "nl"):
    for p in ("tactical", "operator", "brief"):
        s = L.compose(code, p, "KEEP", "EXOTIC", "Striker", 91, "upgrade")
        if not s or "{" in s: ok(False, f"ses cümlesi {code}/{p}: {s!r}")
ok(True, "10 dil × 3 paket cümleleri eksiksiz")
ok("91" in L.compose("en", "tactical", "KEEP", "", "Striker", 91) and L.compose("en", "brief", "DISMANTLE") in ("Scrap.", "Dismantle."), "karar + build yüzdesi")
tmp = tempfile.mkdtemp(); a = voicepack.tone_wav(os.path.join(tmp, "a.wav")); b = voicepack.radio_fx(a, os.path.join(tmp, "b.wav"), seed=2)
with wave.open(a) as w1, wave.open(b) as w2:
    ok(w2.getnframes() > w1.getnframes() and w2.getnchannels() == 1, "telsiz efekti: cızırtı eklendi, mono WAV")
print("RESULT:", "PASS" if not fails else f"FAIL ({fails})"); sys.exit(1 if fails else 0)
