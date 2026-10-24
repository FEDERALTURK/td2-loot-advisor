"""Lisans (Ed25519) ve sandık optimize edici testleri.   python tests/test_core.py"""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import features, gamedata, engine, stash  # noqa: E402

def test_ed25519_rfc8032():
    sk = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    pk = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    sig = bytes.fromhex("e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b")
    assert features.public_key(sk) == pk and features.sign(sk, b"") == sig
    assert features.verify(pk, b"", sig) and not features.verify(pk, b"x", sig)

def test_license_key():
    seed = bytes(range(32)); pub = features.public_key(seed).hex()
    k = features.make_key(seed, {"name": "t", "tier": "premium", "exp": time.time() + 60})
    assert features.check_key(k, pub)[2] == "ok"
    assert features.check_key(k[:-4] + "AAAA", pub)[2] == "signature"
    assert features.check_key(features.make_key(seed, {"exp": 1}), pub)[2] == "expired"
    assert features.check_key("hello", pub)[2] == "format"
    e = features.Entitlements(""); assert e.has("scan") and not e.has("recal_advisor")

def _game():
    return gamedata.GameData(ROOT / "tests/.game_cache.json", ROOT / "meta/game_data.json", ROOT / "meta/game_data.json")

def test_optimizer_keeps_set_bonus():
    G = _game()
    build = {"name": "Striker", "sets_or_brands": ["Striker's Battlegear"], "talents": {},
             "attributes": {"weapon_damage": {"weight": 3}, "crit_chance": {"weight": 2}, "crit_damage": {"weight": 2}}}
    plan = engine.build_plan(build, G)
    st = stash.Stash(ROOT / "tests/.stash_test.json"); st.clear()
    def add(name, slot, attrs, gs=None, br=None, rar=None):
        st.add({"name": name, "slot": slot, "kind": "gear", "gear_set": gs, "brand": br, "rarity": rar or [],
                "attrs": attrs, "talents": []}, "KEEP", game=G)
    for s in ("Mask", "Gloves", "Holster", "Kneepads"):
        add(f"Striker's {s}", s, {"weapon_damage": 15, "crit_damage": 12}, gs="Striker's Battlegear")
    add("Coyote's Mask", "Mask", {"weapon_damage": 15, "crit_chance": 6, "crit_damage": 12}, rar=["EXOTIC"])
    add("Overlord Holster", "Holster", {"armor": 150000, "crit_chance": 6}, br="Overlord Armaments")
    r = stash.optimize(build, plan, st.owned(), G)
    sets = [s for s, v in r["slots"].items() if v["item"] and v["item"].get("gear_set")]
    assert len(sets) >= 4, r["slots"]                                   # exotic must not break the 4-piece bonus
    adv = stash.recal_advice(r, st.owned(), G)
    assert adv and all(a["donor"] != "Coyote's Mask" for a in adv)     # exotics are never recalibration donors

def test_sanitize():
    G = _game()
    w = stash.sanitize({"kind": "weapon", "attrs": {"armor": 49232, "crit_chance": 8}}, G)
    assert "armor" not in w["attrs"]
    g = stash.sanitize({"kind": "gear", "attrs": {"armor": 15, "crit_chance": 6}}, G)
    assert "armor" not in g["attrs"] and g["quality"]["crit_chance"] == 100

if __name__ == "__main__":
    fails = 0
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            try: f(); print("✔", n)
            except Exception as e: fails += 1; print("✖", n, type(e).__name__, e)
    for p in ("tests/.stash_test.json",):
        try: (ROOT / p).unlink()
        except OSError: pass
    sys.exit(1 if fails else 0)
