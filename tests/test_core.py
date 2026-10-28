"""Lisans (Ed25519) ve sandık optimize edici testleri.   python tests/test_core.py"""
import os, sys, time
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

def test_weapon_limits():
    G = _game()
    assert G.parse_attr_line("+13.5% Critical Hit Chance", weapon=True) == ("crit_chance", 13.5)   # SMG: legal
    assert G.parse_attr_line("+13.5% Critical Hit Chance") is None                                # gear: impossible
    assert G.parse_attr_line("+20.0% Headshot Damage", named=True) == ("headshot_damage", 20.0)   # named "perfect"

def test_decimal_repair():
    """OCR ondalık noktayı kaçırınca ('60%' → 6.0) değer atılmaz, onarılır ve şüpheli işaretlenir."""
    G = _game()
    for line, kw, want in (("+60% Critical Hit Chance", {}, ("crit_chance", 6.0)), ("+125% Critical Hit Damage", {}, ("crit_damage", 12.5)),
                           ("+411.1% Critical Hit Damage", {}, ("crit_damage", 11.1))):
        sus = []
        assert G.parse_attr_line(line, suspects=sus, **kw) == want and sus == [want[0]], (line, sus)
    sus = []
    assert G.parse_attr_line("+6.0% Critical Hit Chance", suspects=sus) == ("crit_chance", 6.0) and sus == []
    assert G.parse_attr_line("170,370 Armor", suspects=sus) == ("armor", 170370.0) and sus == []
    assert G.parse_attr_line("+13.5% Critical Hit Chance", suspects=sus) is None                  # ondalıklı ve imkânsız: yine reddedilir

def test_health_damage_and_large_health_values():
    """Tam phrase eşleşmesi Health Damage'ı Health'ten ayırır; uzun sayılar kesilmez."""
    G = _game()
    assert G.parse_attr_line("+10% Health Damage", weapon=True) == ("damage_to_health", 10.0)
    assert G.parse_attr_line("+10% Damage to Health", weapon=True) == ("damage_to_health", 10.0)
    assert G.parse_attr_line("+18,935 Health") == ("health", 18935.0)
    assert G.parse_attr_line("170,370 Armor") == ("armor", 170370.0)
    card = """St. Elmo's Engine
Exotic
Assault Rifle
Core Attributes
+15% Assault Rifle Damage
+10% Health Damage
Attributes
+10% Damage to Targets Out of Cover
Talents
Actum Est"""
    item = G.recognize(card)
    assert item["name"] == "St. Elmo's Engine", item
    assert item["attrs"]["damage_to_health"] == 10.0 and "health" not in item["attrs"], item

def test_prototype_quality_limits():
    """Prototype kartları tanınır ve Prototype rulo üst sınırı uygulanır."""
    G = _game()
    item = G.recognize("Striker's Kneepads\nPrototype\nGear Set\nArmor\nCore Attributes\n+22.5% Weapon Damage\nAugments\nEntropy")
    assert "PROTOTYPE" in item["rarity"] and item["attrs"].get("weapon_damage") == 22.5, item
    assert item["quality"].get("weapon_damage") == 100, item
    assert "Entropy" in item["talents"], item
    proto_build = {"talents": {"Entropy": 2}, "attributes": {}, "sets_or_brands": []}
    assert engine.score_gear({"name": "Striker's Kneepads", "kind": "gear", "slot": "Gloves",
                              "rarity": ["PROTOTYPE"], "attrs": {}, "talents": ["Entropy"]},
                             proto_build, "", G)[0] == 100
    assert engine.score_gear({"name": "Gloves", "kind": "gear", "slot": "Gloves", "rarity": [],
                              "attrs": {}, "talents": ["Entropy"]}, proto_build, "", G)[0] == 0

def test_catalog_key_integrity_and_unicode_normalization():
    """Marka bonusları marka tablosunda, gear set bonusları kendi tablosunda kalır."""
    G = _game()
    assert gamedata.nrm("Česká Výroba s.r.o.") == "ceska vyroba s r o"
    assert G.data["prototype_augments"] == ["Quantum", "Echo", "Atomize", "Amalgam", "Trapper",
                                               "Entropy", "Anomaly", "Paradox", "Synesthesia"]
    brand_keys = {gamedata.nrm(x) for x in G.data["brands"]}
    set_keys = {gamedata.nrm(x) for x in G.data["gear_sets"]}
    assert all(gamedata.nrm(x) in brand_keys for x in G.data["brand_bonuses"])
    assert all(gamedata.nrm(x) in set_keys for x in G.data["gear_set_bonuses"])
    assert all(not v.get("brand") or gamedata.nrm(v["brand"]) in brand_keys for v in G.data["items"].values())
    assert all(not v.get("gear_set") or gamedata.nrm(v["gear_set"]) in set_keys for v in G.data["items"].values())
    assert not ({gamedata.nrm(x) for x in G.data["gear_talents"]} &
                {gamedata.nrm(x) for x in G.data["weapon_talents"]})
    assert "Galvanize" in G.data["gear_talents"] and "Galvanize" not in G.data["weapon_talents"]

def test_share_roundtrip():
    import share
    b = {"name": "Striker", "sets_or_brands": ["Striker's Battlegear"], "attributes": {"crit_chance": {"weight": 2}},
         "talents": {"Perfect Fast Hands": 3}, "items": ["Coyote's Mask"]}
    d = share.decode(share.encode(b))
    assert d["name"] == "Striker" and d["attributes"]["crit_chance"]["weight"] == 2 and d["items"] == ["Coyote's Mask"]
    for bad in ("hello", "TD2B-!!!!"):
        try: share.decode(bad); raise AssertionError("accepted " + bad)
        except ValueError: pass

def test_vendor_record():
    import vendor
    G = _game()
    rec = {"category": "weapon", "rarity": "highend", "vendor_en": "Benitez", "name_en": "Tactical Vector SBR 9mm", "slot_key": "smg",
           "lines": [{"line_type": "talent", "stat_en": "Future Perfect", "value_num": None},
                     {"line_type": "attr", "stat_en": "Critical Hit Chance", "value_num": 13.5}]}
    it = vendor.to_item(rec, G)
    assert it["slot"] == "Weapon" and it["weapon_type"] == "Submachine Gun" and it["attrs"]["crit_chance"] == 13.5
    assert it["talents"] == ["Future Perfect"]

def test_skill_build_not_weapon_type():
    import engine
    b = {"name": "Refactor Drone & Turret (Skill)", "sets_or_brands": ["Refactor"],
         "meta": {"summary": {"en": "Striker Drone and Assault Turret."}}}
    assert engine.weapon_types_of(b) == [], engine.weapon_types_of(b)
    assert engine.weapon_types_of({"name": "Striker AR/SMG"}) == ["assault rifle", "submachine gun"]


def test_real_cards_and_learning():
    """Oyuncunun gerçek okumaları (tests/samples/cards): yuva, tür, marka; öğrenilen kütüphane."""
    import gamedata, tempfile, os
    from pathlib import Path
    base = Path(__file__).parent / "samples" / "cards"
    lib = Path(tempfile.mkdtemp()) / "learned.json"
    G = gamedata.GameData(str(Path(__file__).parent.parent / "meta" / "game_data.json")).attach_learned(lib)
    rd = lambda n: G.recognize((base / n).read_text(encoding="utf-8"))
    it = rd("m16a2.txt"); assert (it["name"], it["kind"], it["slot"]) == ("M16A2", "weapon", "Weapon"), it
    it = rd("striker_kneepads.txt"); assert (it["kind"], it["slot"], it["gear_set"]) == ("gear", "Kneepads", "Striker's Battlegear"), it
    it = rd("unit_alloys_topcut.txt"); assert it["kind"] == "gear" and it["brand"] == "Unit Alloys", it   # zırh ≠ silah
    it = rd("unmatched_backpack.txt")
    assert (it["name"], it["slot"], it["brand"]) == ("Unmatched Backpack", "Backpack", "Unit Alloys"), it   # kütüphanede
    for txt, want in (("Umbra Plate Carrier\nHigh-End 10\n99k Armor", ("Chest", "Grupo Sombra S.A.")),
                      ("Sundown Knee Guards RANK\nHigh-End 10\n99k Armor", ("Kneepads", "Grupo Sombra S.A.")),
                      ("Burdenless Pack\nGear Set 10\n99k Armor", ("Backpack", "Heartbreaker"))):
        it = G.recognize(txt); assert (it["slot"], it["brand"] or it["gear_set"]) == want, it
    # kütüphanede olmayan yeni marka / parça: bir kez okununca öğrenilir ve kalıcıdır
    new_card = "Novel Grip Gloves RANK\nHigh-End 10\n99k Armor\nBrand Set\nNova Testworks (1/3)\n+10% Weapon Handling\nCore Attribute\n+15.0% Weapon Damage"
    it = G.recognize(new_card); learned = G.learn(it)
    assert any("Nova Testworks" in x for x in learned) and any("Gloves" in x for x in learned) and lib.exists(), learned
    G2 = gamedata.GameData(str(Path(__file__).parent.parent / "meta" / "game_data.json")).attach_learned(lib)
    it = G2.recognize("Novel Grip Gloves\n99k Armor\nCore Attribute\n+15.0% Weapon Damage")
    assert (it["slot"], it["brand"]) == ("Gloves", "Nova Testworks"), it
    assert G2.learn(it) == []


def test_library_self_check():
    """Kütüphanedeki her parça / named / exotic / silah adı okununca kendisi olarak tanınmalı."""
    import gamedata, json
    from pathlib import Path
    path = Path(__file__).parent.parent / "meta" / "game_data.json"
    d = json.loads(path.read_text(encoding="utf-8")); G = gamedata.GameData(str(path))
    tot = bad = 0
    for name, v in d["items"].items():
        if not v.get("slot"): continue
        q = v.get("quality"); hdr = {"high-end": "High-End", "gear set": "Gear Set"}.get(q, (q or "").title())
        it = G.recognize(f"{name} RANK\n{hdr} 10\n99k Armor\nCore Attribute\n+15.0% Weapon Damage")
        tot += 1; bad += it["slot"] != v["slot"]
    assert tot > 450 and bad <= tot * 0.01, (tot, bad)
    wb = [n for n, v in d["weapon_index"].items() if gamedata.nrm(G.recognize(
        f"{n} RANK\nHigh-End 10\n{v.get('type', 'Rifle')}\nCore Stats\nTotal DMG RPM MAG\n231.72k 437 30")["name"]) != gamedata.nrm(n)]
    assert not wb, wb[:10]


def test_excel_library_in_sync():
    """meta/TD2_Kutuphane.xlsx ile programın kütüphanesi aynı olmalı (Excel → program aktarımı değişiklik üretmez)."""
    import sys, json
    from pathlib import Path
    root = Path(__file__).parent.parent
    sys.path.insert(0, str(root / "scripts"))
    import import_library_excel as I
    before = (root / "meta" / "game_data.json").read_text(encoding="utf-8")
    ch = I.main(root / "meta" / "TD2_Kutuphane.xlsx", dry=True)
    assert not any(ch.values()), ch
    assert (root / "meta" / "game_data.json").read_text(encoding="utf-8") == before
    d = json.loads(before)
    for n in ("Fafnir", "Iron Will", "Loaded for Bear", "Trick Shot", "Melon Baller", "Insult to Injury", "Unmatched Backpack"):
        assert n in d["items"] or n in d["weapon_index"], n
    assert "Cassidy" not in d["weapon_index"] and d["weapon_index"]["Fafnir"]["type"] == "Shotgun"


def test_display_sync_helpers():
    """Oyunun gerçek boyutundan profil; ekran dışına taşan pencere; hangi monitörde."""
    import display
    for (w, h) in ((1920, 1080), (3440, 1440), (3840, 2160)):
        k, p = display.profile_for(w, h); assert k in display.PROFILES and not p.get("dynamic")
    for (w, h) in ((1680, 1050), (2880, 1800), (1280, 800), (1024, 768), (2560, 1600)):
        k, p = display.profile_for(w, h)
        assert p["dynamic"] and 1.0 <= p["ocr_scale"] <= 6 and 0.10 <= p["card_w"] <= 0.34 and 150 <= p["threshold"] <= 175, (k, p)
    d = display.dynamic_profile(3440, 1440); assert abs(d["card_w"] - 0.16) < 0.01 and d["ocr_scale"] == 1.5
    mons = [{"left": -1920, "top": 0, "width": 5360, "height": 1440},
            {"left": 0, "top": 0, "width": 3440, "height": 1440}, {"left": -1920, "top": 200, "width": 1920, "height": 1080}]
    g = {"left": -1800, "top": 300, "width": 1600, "height": 900}
    assert display.monitor_of(g, mons) is mons[2]
    c = display.clamp_to_screen({"left": 3000, "top": -50, "width": 1000, "height": 800}, mons)
    assert c == {"left": 3000, "top": 0, "width": 440, "height": 750}, c
    assert display.game_window() is None or os.name == "nt"


def test_sync_plan():
    """PC + oyun taramasından ayar planı: oyun penceresi, eski profil/eşik, başka PC'den kalan bölge, HDR, hız."""
    import syncer
    pc = {"cpu": "Test CPU", "cores": 8, "ram_gb": 16, "gpus": ["GPU"],
          "monitors": [{"left": 0, "top": 0, "width": 2560, "height": 1440, "scale": 125},
                       {"left": 2560, "top": 0, "width": 1920, "height": 1080, "scale": 100}]}
    game = {"settings": {"width": 1920, "height": 1080, "display_mode": "Borderless", "hdr": True, "language": 0},
            "window": {"left": 2560, "top": 0, "width": 1920, "height": 1080,
                       "monitor": {"left": 2560, "top": 0, "width": 1920, "height": 1080}}, "running": True}
    st = {"res_profile": "3440x1440", "ocr_threshold": 170, "ocr_tuned": True, "scan_source": "region",
          "region": {"left": 100, "top": 100, "width": 800, "height": 1000}, "game_lang": "de"}
    F, C = syncer.make_plan(pc, game, {"seconds": 1.1, "ok": True, "name": "Stoner LAMG", "attrs": 3}, st)
    keys = [k for _, k, _ in F]
    assert {"sync.game_window", "sync.multi_monitor", "sync.dpi", "sync.hdr", "sync.region_reset", "sync.read_ok"} <= set(keys), keys
    assert C["res_profile"] == "auto" and C["ocr_tuned"] is False and C["ocr_threshold"] == 165
    assert C["scan_source"] == "screen" and C["game_lang"] == "en" and C["ocr_passes"] == 2
    F2, C2 = syncer.make_plan(pc, game, {"seconds": 3.0, "ok": False, "name": "?", "attrs": 0}, st)
    assert C2["ocr_passes"] == 1 and C2["auto_interval_ms"] == 1600 and ("bad", "sync.read_bad") in [(l, k) for l, k, _ in F2]
    st2 = dict(st); old = syncer.apply_plan(st2, C, pc, game)
    assert st2["res_profile"] == "auto" and old["res_profile"] == "3440x1440" and st2["sync_fp"] == syncer.fingerprint(pc, game)
    pc2 = dict(pc, monitors=pc["monitors"][:1])                    # monitör çıkarıldı → yeniden senkron önerilir
    assert syncer.fingerprint(pc2, game) != st2["sync_fp"]
    nogame = syncer.make_plan(pc, {"settings": None, "window": None}, None, {})
    assert "sync.no_game" in [k for _, k, _ in nogame[0]] and nogame[1]["res_profile"] == "auto"


def test_update_center_logic():
    """Kütüphane sürümü (sayısal), "neler yeni" listesi, oyun sürümü değişimi."""
    import updates, gameinfo, json
    from pathlib import Path
    assert updates.lib_newer("2026-10-25.10", "2026-10-25.9") and not updates.lib_newer("2026-10-25.5", "2026-10-25.5")
    assert updates.lib_newer("2026-10-26.1", "2026-10-25.9") and not updates.lib_newer("", "2026-10-25.1")
    new = json.loads((Path(__file__).parent.parent / "meta" / "game_data.json").read_text(encoding="utf-8"))
    old = json.loads(json.dumps(new))
    old["exotics"] = [x for x in old["exotics"] if x not in ("Fafnir", "Iron Will")]
    old["items"].pop("Iron Will"); old["items"].pop("Unmatched Backpack"); old["weapon_index"].pop("Fafnir")
    old["gear_sets"].remove("Ember Engine")
    d = updates.lib_diff(old, new)
    assert set(d["exotics"]) == {"Fafnir", "Iron Will"} and d["items"] == ["Unmatched Backpack"] and d["gear_sets"] == ["Ember Engine"]
    assert "Iron Will" not in d["items"] and "Fafnir" not in d["weapons"] and d["total"] == 4, d
    names, more = updates.diff_summary(d, limit=2); assert set(names) == {"Fafnir", "Iron Will"} and more == 2
    assert updates.valid_library(new) and not updates.valid_library({"schema": 1})
    a = {"version": "1.0.0.1", "mtime": 1, "size": 5}
    assert gameinfo.changed(a, {"version": "1.0.0.2", "mtime": 1, "size": 5}) and not gameinfo.changed(a, dict(a))
    assert gameinfo.changed({"version": "", "mtime": 1, "size": 5}, {"version": "", "mtime": 2, "size": 5})
    assert not gameinfo.changed(None, a) and gameinfo.label({"version": "1.2", "mtime": 0}).startswith("1.2 (")
    g = {"version": "1.0.0.0", "mtime": 100, "size": 7}                       # genel sürüm: tarih/boyut belirler
    assert gameinfo.changed(g, dict(g, mtime=200)) and not gameinfo.changed(g, dict(g))
    assert "1.0.0.0" not in gameinfo.label(g)
    notes = "## TD2\n| Dosya | Ne |\n**5.0.4 — senkron**\n- Birinci\n- İkinci\n\n**5.0.3 — kütüphane**\n- Eski\n"
    h = updates.release_highlights(notes, "5.0.4"); assert h == "senkron: Birinci · İkinci", h
    assert updates.release_highlights(notes, "5.0.3") == "kütüphane: Eski"


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
