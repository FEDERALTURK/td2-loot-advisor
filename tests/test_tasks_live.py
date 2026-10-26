"""Topluluk görevleri (istemci): ayıklama, hafıza, gönderim, liste, Görevler sekmesine birleştirme.

    python tests/test_tasks_live.py            # birim
    python tests/test_tasks_live.py --e2e      # yerel sunucu (node server/dev_server.mjs) + iki sahte oyuncu
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import livetranslate as lt  # noqa: E402
import meta_sync  # noqa: E402
import tasks_live as T  # noqa: E402

fails = 0


def ok(c, msg):
    global fails
    print(("OK   " if c else "FAIL ") + msg)
    if not c: fails += 1


S = ROOT / "tests" / "samples" / "tasks"
full = json.loads((S / "map_projects_full.json").read_text())["lines"]
panel = json.loads((S / "map_projects_panel.json").read_text())["lines"]
NOW = datetime(2026, 10, 26, 6, 0, tzinfo=timezone.utc)                  # Pazartesi

a = T.extract(full, now=NOW); b = T.extract(panel, now=NOW)
ok(a is not None and a["title"] == "Weekly Legendary Mission", "tam ekrandan başlık (yan kartlar karışmadı): %r" % (a or {}).get("title"))
ok(a["subtitle"] == "Legendary Roosevelt Island" and a["desc"].startswith("We've got a special item") and a["desc"].endswith("Roosevelt Island."), "alt başlık ve açıklama")
ok(a["objective"] == "Complete the Roosevelt Island mission on Legendary difficulty" and a["total"] == 1, "hedef + sayaç ayrı")
ok(a["rewards"] == ["Exotic Cache", "Recalibration Cache", "Recalibration Cache", "Gear Crafting Cache", "Optimization Cache"], "ödüller (ikon harfi ayıklandı)")
ok(a["category"] == "project" and a["period"] == "weekly", "tür: haftalık proje")
ok(a["expires_at"] == int(datetime(2026, 10, 27, 8, tzinfo=timezone.utc).timestamp()), "bitiş: haftalık sıfırlama (Salı 08:00 UTC)")
ok(a == b, "tam ekran ve kırpılmış panel aynı görevi verdi (aynı kimlik)")
ok(T.extract([l for l in full if l[0] != "Objective"]) is None, "görev paneli yoksa None")
ok(T.extract([["Objective", [0, 0, 50, 20], 1.0], ["random text here", [0, 30, 200, 50], 1.0]]) is None, "eksik panel → None")
ok(T.task_key("Weekly  Legendary Mission!", "complete the ROOSEVELT island mission on legendary difficulty") ==
   T.task_key(a["title"], a["objective"]), "kimlik büyük/küçük harf ve noktalamadan bağımsız")

# --- canlı liste → hafıza → çeviri
feed = T.validate_feed({"version": "202610260600", "tasks": [{**a, "key": T.task_key(a["title"], a["objective"]),
    "reporters": 3, "last_seen": int(NOW.timestamp()), "tr": {"title": "Haftalık Legendary Görevi", "subtitle": "Legendary Roosevelt Adası",
    "desc": "Roosevelt Adası'na taşınan özel kuvvetleri yenebilecek her ajan için özel bir eşyamız var.",
    "objective": "Legendary zorlukta Roosevelt Adası görevini tamamla"}}, {"bad": 1}, "x"]})
ok(len(feed["tasks"]) == 1, "liste doğrulandı, bozuk kayıtlar atıldı")
mem = T.Memory(feed)
ok(len(mem) == 4 and mem.get("complete the roosevelt island mission on legendary difficulty") == "Legendary zorlukta Roosevelt Adası görevini tamamla", "hafıza")


class NoModel:
    name = "local"; calls = []
    def translate(self, texts):
        NoModel.calls.append(list(texts)); return ["<model>" for _ in texts]


tr = lt.Translator(NoModel(), lt.Glossary([]), lt.Cache(None))
tr.set_memory(mem)
blocks = [x[0] for x in lt.blocks_from_lines([tuple(l) for l in panel])]
out = tr.translate(blocks)
joined = "\n".join(out)
ok("Legendary zorlukta Roosevelt Adası görevini tamamla (00/01)" in joined or "Legendary zorlukta Roosevelt Adası görevini tamamla" in joined, "hedef satırı hafızadan")
ok("Haftalık Legendary Görevi" in joined and "özel bir eşyamız var" in joined, "başlık ve açıklama hafızadan")
ok(not any("<model>" in o for o in out), "bilinen görevde model hiç çalışmadı: %r" % NoModel.calls)
ok(tr.memory_hits >= 4 and tr.ck.endswith(":202610260600"), "hafıza sayacı ve önbellek anahtarı")

# --- Görevler sekmesi
tasks = {"items": {"projects": [{"en": "my own", "texts": {"en": "my own"}}], "journey": [], "manhunt": []}}
r = meta_sync.merge_tasks(tasks, T.to_feed_tasks(feed, now=int(NOW.timestamp())), now=NOW, scope="community")
cm = [x for x in tasks["items"]["projects"] if x.get("feed_id", "").startswith("cm-")]
ok(r["added"] == 1 and len(cm) == 1 and cm[0]["src"] == "👥" and cm[0]["kind"] == "weekly", "Görevler sekmesine 👥 olarak eklendi")
ok(cm[0]["texts"]["tr"].startswith("Haftalık Legendary Görevi – Legendary Roosevelt Adası: Legendary zorlukta"), "Türkçe görev metni")
ok("🎁 Exotic Cache" in cm[0]["how"]["en"], "açıklama + ödüller")
r = meta_sync.merge_tasks(tasks, {"tasks": []}, now=NOW, scope="community")
ok(r["removed"] == 1 and len(tasks["items"]["projects"]) == 1, "listeden düşen topluluk görevi kaldırıldı, kullanıcınınki kaldı")
r = meta_sync.merge_tasks(tasks, {"tasks": []}, now=NOW)                 # ortak liste güncellemesi topluluk görevine dokunmaz
ok(len(tasks["items"]["projects"]) == 1, "ortak liste kendi görevleriyle sınırlı")

# --- gönderim
sent = []


class Resp:
    def __init__(self, data): self.d = data
    def read(self): return self.d
    def __enter__(self): return self
    def __exit__(self, *a): return False


def opener(req, timeout=10):
    sent.append(json.loads(req.data)); return Resp(b'{"ok":true}')


st = os.path.join(tempfile.mkdtemp(), "sent.json")
sub = T.Submitter("http://x", "client-abcdef12", st, opener=opener)
ok(sub.submit(a, {"title": "Haftalık"}, "5.1.8", wait=True) and len(sent) == 1, "gönderildi")
ok(sent[0]["client"] == "client-abcdef12" and sent[0]["task"]["objective"] == a["objective"] and sent[0]["tr"]["title"] == "Haftalık", "gönderilen içerik")
ok(set(sent[0]) == {"client", "app", "task", "tr"} and "lines" not in json.dumps(sent[0]), "yalnız görev yazısı gönderildi")
ok(not sub.submit(a, None, "5.1.8", wait=True) and len(sent) == 1, "aynı gün tekrar gönderilmez")
ok(not T.Submitter("http://x", "client-abcdef12", st, opener=opener).due(a), "durum dosyasından hatırlandı")


def bad_opener(req, timeout=10): raise OSError("offline")


sub2 = T.Submitter("http://x", "c2-abcdefgh", None, opener=bad_opener)
sub2.submit({**a, "title": "Other Task"}, None, "5.1.8", wait=True)
ok(sub2.due({**a, "title": "Other Task"}) and sub2.last_error, "ağ hatasında yeniden denenecek")


# --- uçtan uca: yerel sunucu + iki oyuncu
def e2e():
    port = 8791
    p = subprocess.Popen(["node", str(ROOT / "server" / "dev_server.mjs"), str(port)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        line = p.stdout.readline().split()
        ok(line and line[0] == "READY", "yerel sunucu açıldı")
        url = f"http://127.0.0.1:{port}"
        for i, who in enumerate(("player-one-1234", "player-two-5678")):
            s = T.Submitter(url, who, None)
            s.submit(a, {"title": "Haftalık Legendary Görevi", "objective": "Legendary zorlukta Roosevelt Adası görevini tamamla"}, "5.1.8", wait=True)
            ok(s.last_error is None, f"oyuncu {i + 1} gönderdi")
            if i == 0:
                f1, _ = T.fetch_live(url)
                ok(f1["tasks"] == [], "tek oyuncudan sonra liste boş")
        f2, src = T.fetch_live(url)
        ok(len(f2["tasks"]) == 1 and f2["tasks"][0]["reporters"] == 2 and f2["tasks"][0]["tr"]["objective"].startswith("Legendary zorlukta"), "iki oyuncudan sonra listede, çevirisiyle")
        m = T.Memory(f2)
        tr2 = lt.Translator(NoModel(), lt.Glossary([]), lt.Cache(None)); tr2.set_memory(m)
        o = tr2.translate(["Objective\nComplete the Roosevelt Island 00/01 mission on Legendary difficulty"])[0]
        ok(o == "Hedef\nLegendary zorlukta Roosevelt Adası görevini tamamla (00/01)", "üçüncü oyuncunun ekranında hazır çeviri: %r" % o)
    finally:
        p.terminate()


if "--e2e" in sys.argv: e2e()
print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
sys.exit(1 if fails else 0)
