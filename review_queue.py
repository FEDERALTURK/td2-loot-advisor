"""Local OCR review queue. It never authorizes destructive item actions."""
import json
import time
import uuid
from pathlib import Path


def add(path, text, item, verdict, reason="low-confidence OCR"):
    """Append a masked, review-only record and return its stable id."""
    record = {
        "id": uuid.uuid4().hex,
        "created": int(time.time()),
        "text": str(text or "")[:4000],
        "item": dict(item or {}),
        "verdict": "REVIEW",
        "reason": reason,
        "resolved": False,
    }
    record["item"].pop("_text", None)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Autoscan can see the same blurred card repeatedly; keep one pending
    # review entry for that text/name instead of growing the runtime log.
    for previous in load(target)[-100:]:
        if previous.get("text") == record["text"] and previous.get("item", {}).get("name") == record["item"].get("name"):
            return previous["id"]
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    return record["id"]


def load(path):
    target = Path(path)
    if not target.exists():
        return []
    rows = []
    for line in target.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            if isinstance(row, dict) and not row.get("resolved"):
                rows.append(row)
        except (ValueError, TypeError):
            continue
    return rows
