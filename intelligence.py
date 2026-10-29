"""Personal loot intelligence built from the user's local TD2 records.

The module is deliberately read-only with respect to the game.  It combines a
scanned candidate, the local stash, build requirements and the already-cached
community vendor feed.  UI code decides how to display or persist the result.
"""
from __future__ import annotations

from collections import defaultdict
import time
from typing import Mapping

import stash


def _text(value):
    return " ".join(str(value or "").casefold().split())


def _quality(item):
    values = [float(v) for v in (item.get("quality") or {}).values()
              if isinstance(v, (int, float))]
    if values:
        return sum(values) / len(values)
    try:
        return float(item.get("score") or 0)
    except (TypeError, ValueError):
        return 0.0


def _same_item(a, b):
    """Conservative comparison scope: same type, slot and recognized name."""
    return (a.get("kind") == b.get("kind") and a.get("slot") == b.get("slot")
            and _text(a.get("name")) == _text(b.get("name")) and _text(a.get("name")) not in ("", "?"))


def compare(candidate: Mapping, current: Mapping):
    """Return an explainable, non-destructive item comparison.

    Values are compared only for shared attribute keys.  A missing attribute is
    reported as a structural difference, rather than guessed to be better.
    """
    candidate = dict(candidate or {})
    current = dict(current or {})
    ca, cb = candidate.get("attrs") or {}, current.get("attrs") or {}
    cq, oq = candidate.get("quality") or {}, current.get("quality") or {}
    rows, total = [], 0.0
    for key in sorted(set(ca) | set(cb)):
        new, old = ca.get(key), cb.get(key)
        if new is None or old is None:
            state = "new" if old is None else "missing"
            rows.append({"attr": key, "candidate": new, "current": old, "delta": None, "state": state})
            continue
        try:
            delta = float(new) - float(old)
        except (TypeError, ValueError):
            continue
        # Quality lets large numeric attributes and percentages contribute on
        # the same scale where library maxima are known.
        q_delta = float(cq.get(key, 0) or 0) - float(oq.get(key, 0) or 0)
        total += q_delta if (key in cq or key in oq) else delta
        rows.append({"attr": key, "candidate": new, "current": old, "delta": delta,
                     "quality_delta": q_delta if (key in cq or key in oq) else None,
                     "state": "better" if q_delta > 0 or (not (key in cq or key in oq) and delta > 0)
                     else "worse" if q_delta < 0 or (not (key in cq or key in oq) and delta < 0) else "same"})
    c_score, o_score = _quality(candidate), _quality(current)
    if not rows:
        total = c_score - o_score
    return {"same_item": _same_item(candidate, current), "rows": rows,
            "candidate_quality": round(c_score, 1), "current_quality": round(o_score, 1),
            "quality_delta": round(c_score - o_score, 1), "net_delta": round(total, 1),
            "better": total > 0.5 or (not rows and c_score > o_score + 0.5)}


def stash_match(candidate: Mapping, owned):
    """Find the best local equivalent and return a comparison if one exists."""
    matches = [item for item in owned if _same_item(candidate, item)]
    if not matches:
        return {"found": False, "matches": 0, "best": None, "comparison": None}
    best = max(matches, key=_quality)
    return {"found": True, "matches": len(matches), "best": best,
            "comparison": compare(candidate, best)}


def library_candidates(items, threshold=95):
    """Strong attributes worth retaining for the recalibration library."""
    out = []
    for item in items:
        if "EXOTIC" in set(item.get("rarity") or []):
            continue
        for attr, value in (item.get("attrs") or {}).items():
            quality = (item.get("quality") or {}).get(attr)
            if isinstance(quality, (int, float)) and quality >= threshold:
                out.append({"item": item, "attr": attr, "value": value, "quality": round(float(quality))})
    return sorted(out, key=lambda row: (-row["quality"], _text(row["item"].get("name"))))


def _wanted_labels(requirement, slot):
    labels = {str(slot)}
    for value in requirement.get("source") or []:
        labels.add(str(value))
    if requirement.get("item"):
        labels.add(str(requirement["item"]))
    return labels


def _target_matches(labels, targets):
    labels = {_text(x) for x in labels if _text(x)}
    hits = []
    for target in targets or []:
        normalized = _text(target)
        if normalized and any(label == normalized for label in labels):
            hits.append(target)
    return hits


def farm_plan(build, plan, owned, game, target_loot_rows=()):
    """Match missing build slots to today's cached targeted-loot entries.

    The feed is optional.  Without it callers still receive the local missing
    slot list, so stale or offline community data can never fabricate a route.
    """
    optimized = stash.optimize(build, plan, owned, game)
    missing = []
    for slot, row in optimized["slots"].items():
        if row.get("done"):
            continue
        req = row.get("req") or {}
        wanted = _wanted_labels(req, slot)
        routes = []
        for event, targets, missions, source_day in target_loot_rows or ():
            hit = _target_matches(wanted, targets)
            if hit:
                routes.append({"event": event, "targets": hit, "missions": list(missions or []), "day": source_day})
        missing.append({"slot": slot, "requirement": req, "wanted": sorted(wanted),
                        "fit": row.get("fit", 0), "routes": routes})
    missing.sort(key=lambda row: (-len(row["routes"]), row["fit"]))
    return {"build": build.get("name", ""), "completion": optimized["completion"],
            "done": optimized["done"], "total": optimized["total"], "missing": missing}


def command_snapshot(build, plan, owned, game, target_loot_rows=()):
    """Single model for the command-center page and the companion client."""
    farm = farm_plan(build, plan, owned, game, target_loot_rows)
    audit = stash.audit(owned, [build], lambda _build: plan, game)
    protected = sum(1 for item in owned if item.get('locked') or set(item.get("rarity") or []) & {"EXOTIC", "NAMED", "PROTOTYPE"})
    locations = defaultdict(int)
    expertise = defaultdict(int)
    for item in owned:
        locations[item.get("location") or "stash"] += 1
        expertise[item.get("expertise") or "none"] += 1
    return {"farm": farm, "duplicates": len(audit["duplicates"]), "library": library_candidates(owned),
            "protected": protected, "locations": dict(locations), "expertise": dict(expertise),
            "dismantle": len(audit["dismantle"]), "recalibration": stash.recal_advice(
                stash.optimize(build, plan, owned, game), owned, game)}


def universal_search(query, items=(), builds=()):
    """Search local stash/build records without touching the game or network."""
    needle = _text(query)
    if not needle:
        return {"items": list(items), "builds": list(builds)}
    def hit(value): return needle in _text(value)
    item_rows = []
    for item in items:
        hay = [item.get("name"), item.get("brand"), item.get("gear_set"), item.get("slot"), item.get("weapon_type")]
        hay += list((item.get("attrs") or {}).keys()) + list(item.get("talents") or [])
        if any(hit(x) for x in hay): item_rows.append(item)
    build_rows = []
    for build in builds:
        hay = [build.get("name"), build.get("description")]
        if any(hit(x) for x in hay): build_rows.append(build)
    return {"items": item_rows, "builds": build_rows}


def cache_age(path, now=None):
    """Return cache age in seconds, or None when unavailable."""
    try: return max(0.0, (time.time() if now is None else now) - path.stat().st_mtime)
    except (OSError, AttributeError): return None
