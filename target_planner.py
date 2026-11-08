"""Faz 4: kişisel hedefler ile görev/satıcı/hedef-loot kaynaklarını eşleştirir.

Bu modül yalnızca yerel veri planlaması yapar. Oyun belleğine veya oyun dosyalarına erişmez;
eşleşme sonucu hiçbir zaman silme/kırma kararı üretmez.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


_SPACE = re.compile(r"\s+")
_NONWORD = re.compile(r"[^a-z0-9çğıöşü]+", re.I)
_CADENCE_MAX_AGE = {"daily": 36 * 3600, "weekly": 9 * 86400, "dated": 36 * 3600}


def _norm(value: Any) -> str:
    text = str(value or "").lower().replace("’", "'")
    text = _NONWORD.sub(" ", text)
    return _SPACE.sub(" ", text).strip()


def _list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    return sorted({_norm(x) for x in values if _norm(x)})


def normalize_target(record: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize one user target record."""
    if not isinstance(record, dict):
        raise ValueError("target must be an object")
    name = str(record.get("name") or "").strip()
    if not name:
        raise ValueError("target name is required")
    slot = str(record.get("slot") or "").strip()
    if not slot:
        raise ValueError("target slot is required")
    priority = str(record.get("priority") or "normal").lower()
    if priority not in {"low", "normal", "high", "critical"}:
        priority = "normal"
    return {
        "name": name,
        "name_key": _norm(name),
        "slot": slot,
        "slot_key": _norm(slot),
        "attributes": _list(record.get("attributes")),
        "talents": _list(record.get("talents")),
        "prototype_augments": _list(record.get("prototype_augments")),
        "priority": priority,
        "enabled": bool(record.get("enabled", True)),
        "notes": str(record.get("notes") or "").strip()[:500],
    }


def normalize_source(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize a task/vendor/target-loot source row without trusting its freshness."""
    if not isinstance(record, dict):
        return {"source": "unknown", "name": "", "name_key": "", "attributes": [], "talents": []}
    name = str(record.get("name") or record.get("name_en") or record.get("item") or record.get("title") or "").strip()
    cadence = str(record.get("cadence") or record.get("period") or "unknown").lower()
    if cadence not in _CADENCE_MAX_AGE:
        cadence = "unknown"
    updated = record.get("updated_at", record.get("fetched", 0))
    try:
        updated = float(updated or 0)
    except (TypeError, ValueError):
        updated = 0.0
    return {
        "source": str(record.get("source") or "unknown"),
        "name": name,
        "name_key": _norm(name),
        "slot": str(record.get("slot") or record.get("slot_en") or record.get("slot_key") or ""),
        "slot_key": _norm(record.get("slot") or record.get("slot_en") or record.get("slot_key") or ""),
        "attributes": _list(record.get("attributes") or record.get("attrs")),
        "talents": _list(record.get("talents")),
        "prototype_augments": _list(record.get("prototype_augments")),
        "updated_at": updated,
        "cadence": cadence,
        "confidence": float(record.get("confidence", 1.0) or 0.0),
        "raw": record,
    }


def _is_stale(source: dict[str, Any], now: datetime) -> bool:
    updated = source.get("updated_at", 0)
    if not updated:
        return True
    max_age = _CADENCE_MAX_AGE.get(source.get("cadence"), 24 * 3600)
    return now.timestamp() - float(updated) > max_age


def _match_score(target: dict[str, Any], source: dict[str, Any]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    if target["name_key"] != source["name_key"]:
        return 0, reasons
    score = 50
    reasons.append("name")
    if target["slot_key"] and target["slot_key"] == source["slot_key"]:
        score += 20
        reasons.append("slot")
    elif target["slot_key"] and source["slot_key"]:
        return 0, reasons
    for field, weight in (("attributes", 15), ("talents", 10), ("prototype_augments", 10)):
        wanted = set(target[field])
        if wanted and wanted.issubset(set(source[field])):
            score += weight
            reasons.append(field)
        elif wanted:
            return 0, reasons
    return min(score, 100), reasons


def match_targets(targets: Iterable[dict[str, Any]], sources: Iterable[dict[str, Any]], now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    rows = [normalize_source(x) for x in sources]
    output: list[dict[str, Any]] = []
    for raw_target in targets:
        target = normalize_target(raw_target)
        if not target["enabled"]:
            continue
        matches = []
        for source in rows:
            score, reasons = _match_score(target, source)
            if score:
                stale = _is_stale(source, now)
                review = stale or source["confidence"] < 0.75
                matches.append({"target": target, "source": source["source"], "source_record": source["raw"],
                                "score": score, "reasons": reasons, "stale": stale,
                                "status": "REVIEW" if review else "MATCH"})
        if matches:
            matches.sort(key=lambda x: (x["status"] != "MATCH", -x["score"]))
            output.extend(matches)
        else:
            output.append({"target": target, "source": None, "source_record": None, "score": 0,
                           "reasons": [], "stale": False, "status": "NO_MATCH"})
    return output


def load_targets(path: str | os.PathLike[str]) -> list[dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []
    values = data.get("targets", data) if isinstance(data, dict) else data
    if not isinstance(values, list):
        return []
    out = []
    for row in values:
        try:
            out.append(normalize_target(row))
        except ValueError:
            continue
    return out


def save_targets(path: str | os.PathLike[str], targets: Iterable[dict[str, Any]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "targets": [normalize_target(x) for x in targets]}
    fd, temp_name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, destination)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
