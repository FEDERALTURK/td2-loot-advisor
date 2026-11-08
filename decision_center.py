"""Faz 5: kişisel hedef + taranan eşya için güvenli karar özeti."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

import target_planner


_PROTECTED = {"exotic", "named", "prototype"}


def _protected(item: dict[str, Any]) -> bool:
    rarity = {str(x).lower() for x in (item.get("rarity") or [])}
    text = " ".join(str(x).lower() for x in (item.get("name"), item.get("gear_set"), item.get("brand")) if x)
    return bool(rarity & _PROTECTED or any(word in text for word in _PROTECTED) or item.get("locked"))


def compare_item_to_targets(item: dict[str, Any], targets: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return review-safe target matches for a scanned item; never returns dismantle."""
    source = target_planner.normalize_source({
        "source": "scan",
        "name": item.get("name"),
        "slot": item.get("slot"),
        "attributes": list((item.get("attrs") or {}).keys()),
        "talents": item.get("talents"),
        "prototype_augments": item.get("prototype_augments"),
        "confidence": item.get("confidence", 1.0),
        "updated_at": item.get("seen_at") or item.get("seen") or datetime.now(timezone.utc).timestamp(),
        "cadence": "dated",
    })
    rows = target_planner.match_targets(list(targets), [source])
    protected = _protected(item)
    for row in rows:
        row["recommendation"] = "REVIEW" if protected or row["status"] != "MATCH" else "KEEP"
        row["protected"] = protected
    return rows


def farm_summary(matches: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(matches)
    return {
        "total": len(rows),
        "matches": sum(row.get("status") == "MATCH" for row in rows),
        "review": sum(row.get("status") == "REVIEW" for row in rows),
        "missing": sum(row.get("status") == "NO_MATCH" for row in rows),
        "protected": sum(bool(row.get("protected")) for row in rows),
    }
