"""Sunucuyu yerelde dener (kayıt, tekrar, doğrulama, lisans, oran sınırı).

    cd server
    npx wrangler d1 execute td2stats --local --file schema.sql
    npx wrangler dev --local --port 8787          # ayrı pencerede
    python test_local.py [lisans-anahtarı] [sunucu-adresi]
"""
import hashlib, json, sys, urllib.error, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import features  # noqa: E402

B = (sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8787").rstrip("/")


def req(path, data=None, hdr=None):
    r = urllib.request.Request(B + path, data=json.dumps(data).encode() if data is not None else None,
                               headers={"content-type": "application/json", "user-agent": "TD2-Loot-Advisor-test", **(hdr or {})})
    try:
        with urllib.request.urlopen(r) as f: return f.status, json.loads(f.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def sig(s): return hashlib.sha256(s.encode()).hexdigest()[:24]


ok = True
def check(name, cond):
    global ok; ok &= bool(cond); print(("✔ " if cond else "✖ ") + name)

c = "test" + sig(str(__import__("time").time()))[:16]
good = {"activity": "countdown", "kind": "gear", "slot": "Gloves", "name": "Striker's Gloves", "gear_set": "Striker's Battlegear",
        "rarity": ["GEAR SET"], "attrs": ["weapon_damage", "crit_chance"], "best_q": 100, "sig": sig(c + "a")}
s, r = req("/v1/drops", {"client": c, "drops": [good, {"kind": "virus", "name": "x", "sig": sig("b")}, {"kind": "gear", "name": "y" * 90, "sig": sig("c")}]})
check("valid drop accepted, invalid ones dropped", s == 200 and r["accepted"] == 1)
s, r = req("/v1/drops", {"client": c, "drops": [good]})
check("same item same day counted once", s == 200 and r["accepted"] == 0)
check("client id required", req("/v1/drops", {"drops": [good]})[0] == 400)
check("summary public", req("/v1/summary")[0] == 200)
check("stats need a license", req("/v1/stats")[0] == 401)
check("forged license rejected", req("/v1/stats", hdr={"authorization": "TD2 " + features.make_key(bytes(32), {"tier": "premium"})})[0] == 401)
if len(sys.argv) > 1:
    s, r = req("/v1/stats?activity=countdown", hdr={"authorization": "TD2 " + sys.argv[1]})
    check("stats with a real license", s == 200 and any(x["activity"] == "countdown" for x in r["activities"]))
sys.exit(0 if ok else 1)
