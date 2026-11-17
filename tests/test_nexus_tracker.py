"""
tests/test_nexus_tracker.py
Tests for nexus_tracker.py — Nexus Mods API stats integration.

Run:
    python -m pytest tests/test_nexus_tracker.py -v
or:
    python tests/test_nexus_tracker.py
"""

import json
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Make sure the module under test is importable from the repo root.
sys.path.insert(0, str(Path(__file__).parent.parent / "Thedivision2program"))

import nexus_tracker  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_API_RESPONSE = {
    "mod_id": 12345,
    "name": "TD2 Loot Advisor",
    "summary": "Smart loot advisor for The Division 2",
    "game_id": 42,
    "mod_downloads": 9876,
    "mod_unique_downloads": 4321,
    "endorsement_count": 150,
    "updated_time": 1700000000,
    "created_time": 1699000000,
}


def _make_mock_response(data: dict):
    """Return a mock HTTP response whose .read() yields JSON bytes."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestHeaders(unittest.TestCase):
    """_headers() should always set User-Agent; add apikey when env set."""

    def test_user_agent_always_present(self):
        with patch.dict("os.environ", {}, clear=True):
            hdrs = nexus_tracker._headers()
        self.assertIn("User-Agent", hdrs)
        self.assertIn("TD2LootAdvisor", hdrs["User-Agent"])

    def test_no_apikey_when_env_unset(self):
        with patch.dict("os.environ", {}, clear=True):
            hdrs = nexus_tracker._headers()
        self.assertNotIn("apikey", hdrs)

    def test_apikey_injected_from_env(self):
        with patch.dict("os.environ", {"NEXUS_API_KEY": "test-key-abc"}):
            hdrs = nexus_tracker._headers()
        self.assertEqual(hdrs["apikey"], "test-key-abc")


class TestFetchFromApi(unittest.TestCase):
    """_fetch_from_api() should parse JSON and handle errors gracefully."""

    def test_success_returns_dict(self):
        mock_resp = _make_mock_response(SAMPLE_API_RESPONSE)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = nexus_tracker._fetch_from_api("thedivision2", 12345)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["mod_downloads"], 9876)
        self.assertEqual(result["endorsement_count"], 150)

    def test_http_error_returns_none(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                url="", code=403, msg="Forbidden", hdrs={}, fp=None)):
            result = nexus_tracker._fetch_from_api("thedivision2", 12345)
        self.assertIsNone(result)

    def test_network_error_returns_none(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            result = nexus_tracker._fetch_from_api("thedivision2", 12345)
        self.assertIsNone(result)

    def test_unexpected_error_returns_none(self):
        with patch("urllib.request.urlopen", side_effect=RuntimeError("unexpected")):
            result = nexus_tracker._fetch_from_api("thedivision2", 12345)
        self.assertIsNone(result)


class TestCache(unittest.TestCase):
    """Cache read/write round-trip and TTL expiry."""

    def setUp(self):
        import tempfile
        self._tmpdir = tempfile.mkdtemp()
        self._orig_cache_path = nexus_tracker._cache_path

    def tearDown(self):
        nexus_tracker._cache_path = self._orig_cache_path
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _patch_cache(self, filename="test_cache.json"):
        path = Path(self._tmpdir) / filename
        nexus_tracker._cache_path = lambda: path
        return path

    def test_save_and_load_roundtrip(self):
        path = self._patch_cache()
        nexus_tracker._save_cache(SAMPLE_API_RESPONSE)
        loaded = nexus_tracker._load_cache()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["mod_downloads"], 9876)

    def test_stale_cache_returns_none(self):
        path = self._patch_cache()
        # Write a cache entry with a timestamp older than TTL
        stale = dict(SAMPLE_API_RESPONSE)
        stale["_cached_at"] = time.time() - nexus_tracker.CACHE_TTL_SECONDS - 1
        path.write_text(json.dumps(stale), encoding="utf-8")
        result = nexus_tracker._load_cache()
        self.assertIsNone(result)

    def test_missing_cache_returns_none(self):
        self._patch_cache("nonexistent.json")
        result = nexus_tracker._load_cache()
        self.assertIsNone(result)

    def test_corrupted_cache_returns_none(self):
        path = self._patch_cache()
        path.write_text("not json!!!", encoding="utf-8")
        result = nexus_tracker._load_cache()
        self.assertIsNone(result)


class TestGetStats(unittest.TestCase):
    """get_stats() public interface."""

    def test_returns_none_when_mod_id_not_configured(self):
        orig = nexus_tracker.NEXUS_MOD_ID
        try:
            nexus_tracker.NEXUS_MOD_ID = None
            result = nexus_tracker.get_stats()
            self.assertIsNone(result)
        finally:
            nexus_tracker.NEXUS_MOD_ID = orig

    def test_returns_api_data_on_fresh_fetch(self):
        orig = nexus_tracker.NEXUS_MOD_ID
        try:
            nexus_tracker.NEXUS_MOD_ID = 12345
            mock_resp = _make_mock_response(SAMPLE_API_RESPONSE)
            with patch("urllib.request.urlopen", return_value=mock_resp), \
                 patch("nexus_tracker._load_cache", return_value=None), \
                 patch("nexus_tracker._save_cache"):
                result = nexus_tracker.get_stats(force_refresh=True)
            self.assertIsNotNone(result)
            self.assertEqual(result["mod_downloads"], 9876)
        finally:
            nexus_tracker.NEXUS_MOD_ID = orig

    def test_uses_cache_when_fresh(self):
        orig = nexus_tracker.NEXUS_MOD_ID
        try:
            nexus_tracker.NEXUS_MOD_ID = 12345
            cached = dict(SAMPLE_API_RESPONSE)
            cached["_cached_at"] = time.time()
            with patch("nexus_tracker._load_cache", return_value=cached) as mock_cache, \
                 patch("nexus_tracker._fetch_from_api") as mock_fetch:
                result = nexus_tracker.get_stats()
            mock_cache.assert_called_once()
            mock_fetch.assert_not_called()
            self.assertEqual(result["mod_downloads"], 9876)
        finally:
            nexus_tracker.NEXUS_MOD_ID = orig

    def test_falls_back_to_stale_cache_on_api_error(self):
        orig = nexus_tracker.NEXUS_MOD_ID
        try:
            nexus_tracker.NEXUS_MOD_ID = 12345
            stale = dict(SAMPLE_API_RESPONSE)
            stale["_cached_at"] = 0
            # cache TTL expired → load_cache returns None, API fails
            with patch("nexus_tracker._load_cache", return_value=None), \
                 patch("nexus_tracker._fetch_from_api", return_value=None), \
                 patch("nexus_tracker._cache_path") as mock_path:
                import tempfile, os
                tmp = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False, encoding="utf-8")
                json.dump(stale, tmp)
                tmp.close()
                mock_path.return_value = Path(tmp.name)
                result = nexus_tracker.get_stats()
                os.unlink(tmp.name)
            self.assertIsNotNone(result)
        finally:
            nexus_tracker.NEXUS_MOD_ID = orig


class TestFormatStats(unittest.TestCase):
    """format_stats() should return a readable string."""

    def test_format_with_full_data(self):
        s = nexus_tracker.format_stats(SAMPLE_API_RESPONSE)
        self.assertIn("9,876", s)
        self.assertIn("4,321", s)
        self.assertIn("150", s)
        self.assertIn("TD2 Loot Advisor", s)

    def test_format_with_missing_fields(self):
        # Should not raise
        s = nexus_tracker.format_stats({})
        self.assertIsInstance(s, str)
        self.assertIn("?", s)


# ---------------------------------------------------------------------------
# Integration test (skipped if no network / NEXUS_MOD_ID not set)
# ---------------------------------------------------------------------------

@unittest.skipUnless(nexus_tracker.NEXUS_MOD_ID is not None, "NEXUS_MOD_ID not configured")
class TestLiveAPI(unittest.TestCase):
    """Live smoke test against the real Nexus Mods API."""

    def test_live_fetch_returns_dict(self):
        result = nexus_tracker._fetch_from_api(
            nexus_tracker.NEXUS_GAME_DOMAIN, nexus_tracker.NEXUS_MOD_ID
        )
        self.assertIsInstance(result, dict)
        self.assertIn("mod_id", result)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
