"""Deterministic OCR engine comparison helpers.

The lab accepts already-created callables so tests do not need a display,
network, model download, or a running game. Each callable returns the
project's ``(text, box, confidence)`` line tuples.
"""
from difflib import SequenceMatcher
from time import perf_counter


def _text(lines):
    return " ".join(str(row[0]).strip() for row in lines if row and str(row[0]).strip())


def benchmark(image, engines):
    """Run every named engine once and return comparable timing/quality data.

    ``engines`` is a mapping of name -> callable(image). A failed optional
    engine is reported as unavailable instead of hiding the other results.
    """
    results = {}
    for name, reader in engines.items():
        started = perf_counter()
        try:
            lines = list(reader(image) or [])
            text = _text(lines)
            confidence = [float(row[2]) for row in lines if len(row) >= 3]
            results[name] = {
                "available": True,
                "elapsed_ms": round((perf_counter() - started) * 1000, 2),
                "text": text,
                "line_count": len(lines),
                "mean_confidence": round(sum(confidence) / len(confidence), 4) if confidence else 0.0,
            }
        except Exception as exc:  # optional engine failure is data, not a lab crash
            results[name] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    available = [v for v in results.values() if v.get("available")]
    reference = ""
    if available:
        reference = max((v["text"] for v in available), key=len, default="")
    for value in results.values():
        if value.get("available"):
            value["similarity_to_reference"] = round(SequenceMatcher(None, value["text"].lower(), reference.lower()).ratio(), 4)
            value["review"] = value["mean_confidence"] < 0.68 or not value["text"].strip()
    winner = max(
        ((name, value) for name, value in results.items() if value.get("available")),
        key=lambda pair: (pair[1].get("mean_confidence", 0), len(pair[1].get("text", "")), -pair[1].get("elapsed_ms", 1e9)),
        default=(None, None),
    )[0]
    return {"engines": results, "winner": winner, "reference_text": reference}
