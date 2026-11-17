"""
nexus_tracker.py — Nexus Mods download/endorsement stats tracker
=================================================================
Fetches mod statistics from the Nexus Mods public REST API v1 and
caches the result locally so the app can display a live download count
without hammering the API on every launch.

Usage (standalone):
    python nexus_tracker.py          # prints stats JSON to stdout
    python nexus_tracker.py --refresh  # forces a cache refresh

Usage (from app code):
    from nexus_tracker import get_stats
    stats = get_stats()              # returns dict or None on error
    print(stats["mod_downloads"])

Environment variable (optional):
    NEXUS_API_KEY — your personal Nexus Mods API key (account → settings →
                    API Keys).  Without it the endpoint still works but rate
                    limits are much tighter (50 req/day vs 2 500 req/day).

API reference:
    GET https://api.nexusmods.com/v1/games/{game_domain_name}/mods/{mod_id}.json
    Response includes:
        mod_id, name, summary, description, game_id, author,
        mod_downloads, mod_unique_downloads, endorsement_count,
        updated_time, created_time, ...
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — change these when the mod page exists on Nexus
# ---------------------------------------------------------------------------
NEXUS_GAME_DOMAIN = "thedivision2"      # game slug on nexusmods.com
NEXUS_MOD_ID: Optional[int] = None     # Set to your mod's numeric ID once
                                        # the page is created on Nexus Mods.
                                        # e.g. NEXUS_MOD_ID = 12345

NEXUS_API_BASE = "https://api.nexusmods.com/v1"
CACHE_TTL_SECONDS = 3600                # re-fetch at most once per hour
CACHE_FILENAME = "nexus_stats_cache.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cache_path() -> Path:
    """Return the path to the local stats cache file."""
    # Store next to this module file so it's portable / portable.
    return Path(__file__).parent / "meta" / CACHE_FILENAME


def _headers() -> dict:
    """Build HTTP headers for the Nexus API request."""
    hdrs = {
        "User-Agent": "TD2LootAdvisor/1.0 (https://github.com/FEDERALTURK/td2-loot-advisor)",
        "Accept": "application/json",
    }
    api_key = os.environ.get("NEXUS_API_KEY", "").strip()
    if api_key:
        hdrs["apikey"] = api_key
    return hdrs


def _fetch_from_api(game_domain: str, mod_id: int) -> Optional[dict]:
    """Fetch mod info directly from the Nexus Mods REST API.

    Returns the parsed JSON dict on success, None on any error.
    """
    url = f"{NEXUS_API_BASE}/games/{game_domain}/mods/{mod_id}.json"
    req = urllib.request.Request(url, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            data = json.loads(raw)
            return data
    except urllib.error.HTTPError as exc:
        logger.warning("Nexus API HTTP %s for %s", exc.code, url)
    except urllib.error.URLError as exc:
        logger.warning("Nexus API network error: %s", exc.reason)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Nexus API unexpected error: %s", exc)
    return None


def _load_cache() -> Optional[dict]:
    """Load cached stats if they are still fresh."""
    path = _cache_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cached_at = data.get("_cached_at", 0)
        if time.time() - cached_at < CACHE_TTL_SECONDS:
            return data
    except Exception as exc:  # noqa: BLE001
        logger.debug("Cache load failed: %s", exc)
    return None


def _save_cache(stats: dict) -> None:
    """Persist stats dict to the local cache file."""
    path = _cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(stats)
        payload["_cached_at"] = time.time()
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.debug("Cache save failed: %s", exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_stats(force_refresh: bool = False) -> Optional[dict]:
    """Return mod statistics as a dict.

    Keys of interest (all may be absent if the mod page doesn't exist yet):
        mod_downloads       — total all-time downloads
        mod_unique_downloads — unique downloader count
        endorsement_count   — number of endorsements
        name                — mod display name
        summary             — short description
        updated_time        — Unix timestamp of last update

    Returns None when:
        - NEXUS_MOD_ID is not configured
        - The API is unreachable and no cache is available
    """
    if NEXUS_MOD_ID is None:
        logger.debug("NEXUS_MOD_ID not configured — skipping stats fetch")
        return None

    if not force_refresh:
        cached = _load_cache()
        if cached:
            return cached

    stats = _fetch_from_api(NEXUS_GAME_DOMAIN, NEXUS_MOD_ID)
    if stats:
        _save_cache(stats)
        return stats

    # API unavailable — fall back to stale cache if any
    path = _cache_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass

    return None


def format_stats(stats: dict) -> str:
    """Return a one-line human-readable summary of the stats dict."""
    def _fmt(v):
        return f"{v:,}" if isinstance(v, int) else str(v)

    dl = stats.get("mod_downloads", "?")
    udl = stats.get("mod_unique_downloads", "?")
    end = stats.get("endorsement_count", "?")
    name = stats.get("name", "TD2 Loot Advisor")
    return f"{name}: {_fmt(dl)} downloads · {_fmt(udl)} unique · {_fmt(end)} endorsements"


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    force = "--refresh" in sys.argv

    if NEXUS_MOD_ID is None:
        print("NEXUS_MOD_ID is not set in nexus_tracker.py.")
        print("Set it to your mod's numeric ID after creating the mod page on Nexus Mods.")
        print(f"Game domain: {NEXUS_GAME_DOMAIN}")
        sys.exit(0)

    stats = get_stats(force_refresh=force)
    if stats is None:
        print("Could not retrieve stats (API error or no cache).")
        sys.exit(1)

    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print()
    print(format_stats(stats))


if __name__ == "__main__":
    _main()
