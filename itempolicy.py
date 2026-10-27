"""Pure validation shared by OCR decisions, imports and the stash audit.

These helpers do not read files, change input objects or depend on the UI.
"""
from collections.abc import Mapping
from copy import deepcopy
import math
from numbers import Real


PROTECTED_RARITIES = frozenset({"EXOTIC", "NAMED", "PROTOTYPE"})
ITEM_KINDS = frozenset({"gear", "weapon", "gear_mod", "weapon_mod", "skill_mod",
                        "cosmetic", "material", "consumable", "cache"})
SLOTS = frozenset({"Mask", "Chest", "Backpack", "Gloves", "Holster", "Kneepads", "Weapon", "Sidearm"})
VERDICTS = frozenset({"KEEP", "CONSIDER", "DISMANTLE", "REVIEW", "ERROR"})


def _finite_number(value):
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _rarities(item):
    if not isinstance(item, Mapping):
        return set()
    value = item.get("rarity") or []
    # Also protect older or externally imported records containing a single tag.
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set, frozenset)):
        return set()
    return {x.strip().upper() for x in value if isinstance(x, str)}


def is_protected_item(item):
    """Whether a rarity tag requires keeping the final decision at KEEP/REVIEW."""
    return bool(PROTECTED_RARITIES & _rarities(item))


def item_valid(item):
    """True only for a complete, structurally usable item/card record.

Modern OCR records must meet their recognition confidence and show card
evidence. Legacy and stash records have no confidence field, so they need
usable attributes or talents instead. A partial card is never a decision
candidate, even if some of its values happen to score highly.
"""
    if not isinstance(item, Mapping) or item.get("partial"):
        return False
    name = item.get("name")
    if not isinstance(name, str) or not name.strip() or name.strip() == "?" or not any(c.isalnum() for c in name):
        return False
    kind = item.get("kind")
    if kind is not None and (not isinstance(kind, str) or kind not in ITEM_KINDS):
        return False
    attrs = item.get("attrs", {})
    talents = item.get("talents", [])
    if attrs is None: attrs = {}
    if talents is None: talents = []
    if not isinstance(attrs, Mapping) or not all(isinstance(k, str) and k.strip() and _finite_number(v) and v >= 0
                                                for k, v in attrs.items()):
        return False
    if not isinstance(talents, (list, tuple)) or not all(isinstance(t, str) and t.strip() for t in talents):
        return False
    rarity = item.get("rarity")
    if rarity is not None and not isinstance(rarity, (str, list, tuple, set, frozenset)):
        return False
    quality = item.get("quality", {})
    if quality is not None and (not isinstance(quality, Mapping) or
                                not all(_finite_number(v) and v >= 0 for v in quality.values())):
        return False
    if "confidence" in item:
        conf = item["confidence"]
        if not _finite_number(conf) or not 0.5 <= conf <= 1:
            return False
        card_like = bool(attrs or talents or (item.get("sections") and _rarities(item)) or item.get("spec"))
        # These kinds are recognized as non-build items and are always reviewed.
        if kind in ITEM_KINDS - {"gear", "weapon", "gear_mod"}:
            card_like = True
        return card_like
    return bool(attrs or talents)


def protect_verdict(item, verdict):
    """Apply the final policy after any scoring/progress route.

An explicit processing ERROR stays an ERROR. Invalid/partial records are
reviewed. Exotic, Named and Prototype records may be kept for a real match;
all other non-error outcomes for those rarities require manual review.
"""
    if not isinstance(verdict, str) or verdict not in VERDICTS:
        return "REVIEW"
    if verdict == "ERROR":
        return verdict
    if not item_valid(item):
        return "REVIEW"
    if is_protected_item(item) and verdict not in ("KEEP", "REVIEW"):
        return "REVIEW"
    return verdict


def validate_thresholds(keep, consider):
    """Return numeric thresholds or raise ValueError without mutating settings."""
    values = []
    for name, value in (("keep_threshold", keep), ("consider_threshold", consider)):
        if isinstance(value, bool):
            raise ValueError(f"{name}: expected a number from 0 to 100")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f"{name}: expected a number from 0 to 100") from None
        if not math.isfinite(number) or not 0 <= number <= 100:
            raise ValueError(f"{name}: expected a number from 0 to 100")
        values.append(number)
    if values[0] < values[1]:
        raise ValueError("keep_threshold must be at least consider_threshold")
    return tuple(values)


def _text_list(value, field, allowed=None):
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise ValueError(f"{field}: expected a list of non-empty text values")
    if allowed is not None and any(v not in allowed for v in value):
        raise ValueError(f"{field}: unknown slot")


def _nonnegative_number(value, field, positive=False):
    if not _finite_number(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{field}: expected a finite {'positive' if positive else 'non-negative'} number")


def _weights(value, field):
    if not isinstance(value, dict):
        raise ValueError(f"{field}: expected an object")
    for name, weight in value.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{field}: expected non-empty names")
        _nonnegative_number(weight, f"{field}.{name}", positive=True)


def validate_imported_builds(data):
    """Validate an exported build list and return an independent normalized copy.

The accepted envelope is a list or {"builds": [...]}. Unknown metadata is
preserved, while every field used by scoring/planning is checked before the
caller appends anything to its live configuration. Invalid input raises
ValueError, so an import is accepted or rejected as a whole.
"""
    incoming = data.get("builds") if isinstance(data, dict) else data
    if not isinstance(incoming, list):
        raise ValueError("builds: expected a list")
    out = deepcopy(incoming)
    for index, build in enumerate(out, 1):
        field = f"builds[{index}]"
        if not isinstance(build, dict):
            raise ValueError(f"{field}: expected an object")
        name = build.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{field}.name: expected a non-empty name")
        build["name"] = name.strip()
        for key in ("sets_or_brands", "items", "slots"):
            if key in build:
                _text_list(build[key], f"{field}.{key}", SLOTS if key == "slots" else None)
        build.setdefault("sets_or_brands", [])
        build.setdefault("set_bonus", 0)
        _nonnegative_number(build["set_bonus"], f"{field}.set_bonus")
        build.setdefault("attributes", {})
        if not isinstance(build["attributes"], dict):
            raise ValueError(f"{field}.attributes: expected an object")
        for key, rule in build["attributes"].items():
            if not isinstance(key, str) or not key.strip() or not isinstance(rule, dict):
                raise ValueError(f"{field}.attributes: expected attribute objects")
            rule.setdefault("weight", 1)
            rule.setdefault("good_at", 0)
            _nonnegative_number(rule["weight"], f"{field}.attributes.{key}.weight")
            if "good_at" in rule:
                _nonnegative_number(rule["good_at"], f"{field}.attributes.{key}.good_at")
        build.setdefault("talents", {})
        _weights(build["talents"], f"{field}.talents")
        if "weapons" in build:
            weapons = build["weapons"]
            if not isinstance(weapons, dict):
                raise ValueError(f"{field}.weapons: expected an object")
            if "types" in weapons:
                _text_list(weapons["types"], f"{field}.weapons.types")
            if "talents" in weapons:
                _weights(weapons["talents"], f"{field}.weapons.talents")
        if "meta" in build:
            meta = build["meta"]
            if not isinstance(meta, dict):
                raise ValueError(f"{field}.meta: expected an object")
            if "summary" in meta and (not isinstance(meta["summary"], dict) or
                                       not all(isinstance(k, str) and isinstance(v, str) for k, v in meta["summary"].items())):
                raise ValueError(f"{field}.meta.summary: expected translated text")
    return out
