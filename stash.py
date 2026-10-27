"""Sandık (envanter) — denetim raporu, kopyalar, build optimize edici, kalibrasyon danışmanı.

Oyuna tuş gönderilmez: oyuncu sandıkta gezerken taranan her eşya buraya kaydedilir (stash.json).
Kırılan eşyalar "dismantled" işaretlenir ve hesaplara girmez.

    st = Stash(path); st.add(item, verdict, best_build, score)
    rep = audit(st.owned(), builds, plan_fn, game)
    opt = optimize(build, plan, st.owned(), game)       # en iyi parça seçimi + eksikler + sıradaki en değerli düşüş
    rc  = recal_advice(opt, st.owned(), game)            # hangi attribute hangi eşyadan kalibre edilir
"""
import itertools
import json
import os
import time
import uuid

import engine
import itempolicy

GEAR = engine.GEAR_SLOTS
ITEM_KINDS = ("gear", "weapon")


# ---------------------------------------------------------------- kayıt
def signature(item):
    attrs = ",".join(f"{k}={float(v):g}" for k, v in sorted((item.get("attrs") or {}).items()))
    return f"{(item.get('name') or '?').lower()}|{item.get('slot') or ''}|{attrs}|{','.join(sorted(item.get('talents') or []))}"


# silahta olabilecek attribute'lar (ekipmana ait armor / health / skill tier vb. silahta OCR hatasıdır)
WEAPON_ATTRS = {"weapon_type_damage", "crit_chance", "crit_damage", "headshot_damage", "damage_to_armor",
                "damage_to_health", "damage_out_of_cover", "damage_to_elites", "rate_of_fire", "reload_speed",
                "magazine_size", "optimal_range", "weapon_handling", "stability", "accuracy", "swap_speed"}


def sanitize(rec, game):
    """Kütüphanedeki en yüksek değeri bariz aşan attribute'ları at (eski OCR hataları: 'armor 49232' silahta vb.).
    Kaliteyi (oyundaki en yüksek değere göre %) yeniden hesapla."""
    attrs, quality = {}, {}
    proto = "PROTOTYPE" in (rec.get("rarity") or [])
    for k, v in (rec.get("attrs") or {}).items():
        try: v = float(v)
        except (TypeError, ValueError): continue
        if rec.get("kind") == "weapon" and k not in WEAPON_ATTRS: continue
        weapon = rec.get("kind") == "weapon"
        named = bool({"NAMED", "EXOTIC"} & set(rec.get("rarity") or []))
        lim = game.limit_of(k, proto, weapon, named) if game and game.ok else None
        mx = game.max_of(k, proto, weapon) if game and game.ok else None
        if lim and v > lim * 1.06: continue
        if mx and mx >= 1000 and v < mx * 0.02: continue   # armor/health gibi büyük sabit değerde "15": uzmanlık satırı ya da OCR hatası
        attrs[k] = v
        if mx: quality[k] = round(min(100.0, v / mx * 100))
    rec["attrs"], rec["quality"] = attrs, quality or rec.get("quality") or {}
    return rec


class Stash:
    def __init__(self, path):
        self.path = path
        self.data = {"version": 1, "items": []}
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict) and isinstance(d.get("items"), list): self.data = d
        except (OSError, ValueError):
            pass

    def save(self):
        import safeio                                  # atomik + kilitli + günlük yedek (tarama ve arayüz aynı anda kaydedebilir)
        safeio.write_json(self.path, self.data, indent=1)

    @property
    def items(self):
        return self.data["items"]

    def owned(self):
        return [r for r in self.items if r.get("status", "owned") == "owned"]

    def find(self, rid):
        return next((r for r in self.items if r.get("id") == rid), None)

    def add(self, item, verdict=None, best=None, score=None, game=None, source="scan"):
        """Taranan eşyayı ekle. Aynı imzalı eşya varsa günceller. Dönüş: (kayıt, yeni mi)."""
        if not isinstance(item, dict) or item.get("kind") not in ITEM_KINDS or not item.get("slot"):
            return None, False
        if (item.get("name") in (None, "", "?")) and not (item.get("brand") or item.get("gear_set")):
            return None, False
        rec = {k: item.get(k) for k in ("name", "kind", "slot", "brand", "gear_set", "rarity", "weapon_type",
                                         "attrs", "quality", "talents")}
        rec["attrs"] = dict(rec.get("attrs") or {}); rec["talents"] = list(rec.get("talents") or [])
        if game: sanitize(rec, game)
        sig = signature(rec)
        old = next((r for r in self.items if r.get("sig") == sig and r.get("status", "owned") == "owned"), None)
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        if old:
            old.update(verdict=verdict or old.get("verdict"), best=best or old.get("best"),
                       score=score if score is not None else old.get("score"), seen=stamp)
            return old, False
        rec.update(id=uuid.uuid4().hex[:10], sig=sig, verdict=verdict, best=best, score=score, time=stamp, seen=stamp,
                   status="owned", source=source)
        self.items.append(rec)
        return rec, True

    def mark(self, rid, status):
        r = self.find(rid)
        if r: r["status"] = status; r["seen"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        return r

    def remove(self, rid):
        self.data["items"] = [r for r in self.items if r.get("id") != rid]

    def clear(self):
        self.data["items"] = []

    def import_progress(self, progress, game):
        """Eski sürümlerin progress.json kayıtlarını (build'e uyan eşyalar) sandığa aktar. Dönüş: eklenen sayısı."""
        n = 0
        for _b, slots in (progress or {}).items():
            for slot, cur in (slots or {}).items():
                if not isinstance(cur, dict) or not cur.get("item"): continue
                item = {"name": cur.get("item"), "slot": slot, "kind": "weapon" if slot in ("Weapon", "Sidearm") else "gear",
                        "brand": cur.get("brand"), "gear_set": cur.get("gear_set"), "rarity": cur.get("rarity") or [],
                        "attrs": cur.get("attrs") or {}, "quality": cur.get("quality") or {}, "talents": cur.get("talents") or []}
                _, new = self.add(item, game=game, source="progress")
                n += new
        return n


# ---------------------------------------------------------------- yuva uyumu
W_SOURCE, W_TYPE, W_CORE, W_ATTRS, W_TALENT = 30, 20, 20, 35, 15
SET_PIECE_BONUS = 20          # optimize: gerçek set parçasıyla dolan her set yuvası için ek puan
SET_FULL_BONUS = 120          # set tamamlanınca (oyunda 4 parça bonusu ancak o zaman gelir)


def slot_fit(item, req, game=None):
    """Eşya bu yuva şartına ne kadar uyuyor: (0-100, checks). Attribute'larda rulo kalitesi de sayılır."""
    if not req or req.get("kind") == "off": return 0, []
    checks = engine.check_slot(item, req, game)
    q = item.get("quality") or {}
    got = tot = 0.0
    n_attr = max(1, sum(1 for c in checks if c[0] == "attr"))
    must_source = req.get("kind") in ("set", "item")
    source_fail = any(c[0] == "source" and c[1] is False for c in checks)
    for kind, ok, _txt in checks:
        w = {"source": W_SOURCE, "type": W_TYPE, "core": W_CORE, "attr": W_ATTRS / n_attr, "talent": W_TALENT}[kind]
        tot += w
        if kind == "attr":
            key = _txt.split(" ")[0]
            if key in (item.get("attrs") or {}): got += w * min(1.0, q.get(key, 80) / 100)
        elif ok is None: got += w * 0.5
        elif ok: got += w
    score = round(100 * got / tot) if tot else 50
    if must_source and source_fail:                  # set parçası / adı geçen eşya yerine başka eşya: set bonusu bozulur
        score = round(score * 0.35)
    return score, checks


def _variants(plan):
    """Set parçalarının yuvası esnek: 4 set parçası 6 yuvanın herhangi 4'ünde olabilir (talent isteyen göğüs/sırt hariç).
    Dönüş: (set_req, any_req, esnek yuvalar, gereken set sayısı)."""
    set_slots = [s for s in GEAR if plan.get(s, {}).get("kind") == "set"]
    if not set_slots: return None, None, [], 0
    set_req = dict(plan[set_slots[0]]); set_req.pop("talent", None)
    any_src = next((plan[s] for s in GEAR if plan.get(s, {}).get("kind") == "any"), None)
    any_req = dict(any_src) if any_src else {"kind": "any", "source": [], "core": set_req.get("core"),
                                              "attrs": set_req.get("attrs", []), "talent": None}
    any_req.pop("talent", None)
    fixed_talent = [s for s in set_slots if plan[s].get("talent")]
    flex = [s for s in GEAR if plan.get(s, {}).get("kind") in ("set", "any") and s not in fixed_talent]
    return set_req, any_req, flex, len(set_slots) - len(fixed_talent)


def _best_for(slot, req, items, game, exclude=()):
    best = (None, -1, [])
    for it in items:
        if it.get("slot") != slot or it.get("id") in exclude: continue
        sc, ch = slot_fit(it, req, game)
        if sc > best[1]: best = (it, sc, ch)
    return best


def optimize(build, plan, items, game=None):
    """Sandıktaki eşyalarla build için en iyi parça seçimi.
    Dönüş: {"slots": {yuva: {"item", "fit", "checks", "req", "done"}}, "completion": %, "done": n, "total": n,
            "next_drop": [(yuva, kazanç, şart)], "set_slots": [...]}"""
    slots = [s for s in engine.ALL_SLOTS if plan.get(s, {}).get("kind", "off") != "off"]
    items = [i for i in items if i.get("kind") in ITEM_KINDS]
    chosen = {}
    set_req, any_req, flex, need = _variants(plan)
    if need and len(flex) >= need:
        best_total, best_combo = -1, None
        cache = {}
        for s in flex:
            for tag, rq in (("set", set_req), ("any", any_req)):
                r = dict(rq); r["talent"] = plan[s].get("talent") if s in ("Chest", "Backpack") else None
                cache[(s, tag)] = (_best_for(s, r, items, game), r)
        def filled(s):                                # yuvada gerçekten set parçası var mı (kaynak tutuyor)
            it, _sc, ch = cache[(s, "set")][0]
            return bool(it) and any(c[0] == "source" and c[1] for c in ch)
        for combo in itertools.combinations(flex, need):
            tot = sum(cache[(s, "set" if s in combo else "any")][0][1] for s in flex)
            nf = sum(1 for s in combo if filled(s))     # set bonusu build'in çekirdeği: tam set ayrıca ödüllenir
            tot += SET_PIECE_BONUS * nf + (SET_FULL_BONUS if nf == need else 0)
            if tot > best_total: best_total, best_combo = tot, combo
        for s in flex:
            (it, sc, ch), r = cache[(s, "set" if s in best_combo else "any")]
            r = dict(r, kind="set" if s in best_combo else "any")
            chosen[s] = (it, max(sc, 0), ch, r)
    for s in slots:
        if s in chosen: continue
        req = plan[s]
        it, sc, ch = _best_for(s, req, items, game)
        chosen[s] = (it, max(sc, 0), ch, req)
    out, fits, done = {}, [], 0
    for s in slots:
        it, sc, ch, req = chosen[s]
        if it is None: sc, ch = 0, []
        ok = bool(it) and engine.slot_done(ch)
        done += ok; fits.append(sc)
        out[s] = {"item": it, "fit": sc, "checks": ch, "req": req, "done": ok}
    gains = sorted(((s, 100 - out[s]["fit"], out[s]["req"]) for s in slots if not out[s]["done"]), key=lambda x: -x[1])
    return {"slots": out, "completion": round(sum(fits) / len(fits)) if fits else 0, "done": done,
            "total": len(slots), "next_drop": gains[:3],
            "set_slots": [s for s in slots if out[s]["req"].get("kind") == "set"]}


def rank_builds(builds, plan_fn, items, game=None):
    """Sandığa göre hangi build'e en yakınsın: [(tamamlanma %, build adı, sonuç)] büyükten küçüğe."""
    res = []
    for b in builds:
        try:
            r = optimize(b, plan_fn(b), items, game)
            res.append((r["completion"], b["name"], r))
        except Exception:
            continue
    return sorted(res, key=lambda x: -x[0])


# ---------------------------------------------------------------- kalibrasyon
def recal_advice(opt, items, game=None, min_gain=10):
    """Seçilen parçalarda eksik/zayıf attribute'u, kullanılmayan başka bir eşyadan kalibre etme önerileri.
    Oyunda kalibrasyon: eşya başına TEK attribute (ya da talent) değiştirilebilir; kaynak eşya kütüphaneye
    eklenirken kırılır, kütüphanedeki değer sonra istenen kadar eşyaya uygulanabilir. Dönüş: [{"slot", "target", "attr", "have", "donor", "value", "quality", "gain"}]"""
    used = {v["item"]["id"] for v in opt["slots"].values() if v.get("item")}
    out = []
    for slot, v in opt["slots"].items():
        it, req = v.get("item"), v.get("req") or {}
        if not it: continue
        q = it.get("quality") or {}
        wants = ([req["core"]] if req.get("core") else []) + list(req.get("attrs") or [])
        best = None
        for a in wants:
            have = q.get(a, 0) if a in (it.get("attrs") or {}) else 0
            if have >= 95: continue
            for d in items:
                if d.get("id") in used or d.get("id") == it.get("id"): continue
                if d.get("kind") != it.get("kind"): continue            # silah ve ekipman kütüphaneleri ayrı
                if "EXOTIC" in (d.get("rarity") or []): continue        # egzotikler kütüphaneye eklenemez
                if a not in (d.get("attrs") or {}): continue
                dq = (d.get("quality") or {}).get(a, 0)
                gain = dq - have
                if gain >= min_gain and (best is None or gain > best["gain"]):
                    best = {"slot": slot, "target": it.get("name"), "attr": a, "have": have,
                            "donor": d.get("name"), "donor_id": d.get("id"), "value": d["attrs"][a],
                            "quality": dq, "gain": gain}
        if best: out.append(best)               # eşya başına tek öneri (oyun kuralı)
    return sorted(out, key=lambda x: -x["gain"])


# ---------------------------------------------------------------- denetim raporu
def duplicates(items):
    """Aynı eşyanın kopyaları: aynı ad + yuva + aynı attribute türleri. Her grupta en iyisi hariç diğerleri."""
    groups = {}
    for it in items:
        key = ((it.get("name") or "").lower(), it.get("slot"), tuple(sorted((it.get("attrs") or {}).keys())))
        groups.setdefault(key, []).append(it)
    out = []
    for g in groups.values():
        if len(g) < 2: continue
        g = sorted(g, key=lambda r: -sum((r.get("quality") or {}).values()))
        out.append((g[0], g[1:]))
    return out


def audit(items, builds=None, plan_fn=None, game=None):
    """Sandık özeti: karar sayıları, kırılacaklar, kopyalar, kütüphane adayları, en yakın build'ler."""
    from collections import Counter
    items = [i for i in items if isinstance(i, dict) and i.get("kind") in ITEM_KINDS]
    counts = Counter(itempolicy.protect_verdict(i, i.get("verdict") or "REVIEW") for i in items)
    valid = [i for i in items if itempolicy.item_valid(i)]
    used = set()
    ranks = []
    if builds and plan_fn:
        ranks = rank_builds(builds, plan_fn, valid, game)
        for _c, _n, r in ranks[:5]:                    # en yakın 5 build'in kullandığı parçalar korunur
            used |= {v["item"]["id"] for v in r["slots"].values() if v.get("item")}
    dups = duplicates(valid)
    dup_ids = {d["id"] for _best, rest in dups for d in rest}
    dismantle = [i for i in valid if i.get("id") and i["id"] not in used and
                 (i.get("verdict") == "DISMANTLE" or i["id"] in dup_ids) and
                 itempolicy.protect_verdict(i, "DISMANTLE") == "DISMANTLE"]
    # kırmadan önce kütüphaneye ekle: kırılacak eşyada %95+ attribute
    library = [(i, a, (i.get("quality") or {}).get(a)) for i in dismantle for a in (i.get("attrs") or {})
               if (i.get("quality") or {}).get(a, 0) >= 95]
    return {"total": len(items), "counts": dict(counts), "dismantle": dismantle, "duplicates": dups,
            "library": library, "protected": len(used), "ranks": ranks}


def export_csv(items, path):
    import csv
    cols = ["name", "slot", "kind", "brand", "gear_set", "rarity", "attrs", "talents", "verdict", "best", "score", "time"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in items:
            w.writerow([("/".join(r.get(c) or []) if c == "rarity" else
                         ", ".join(f"{k} {v:g}" for k, v in (r.get(c) or {}).items()) if c == "attrs" else
                         ", ".join(r.get(c) or []) if c == "talents" else r.get(c, "")) for c in cols])
