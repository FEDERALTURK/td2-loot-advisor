"""
TD2 Loot Advisor — updater.py uçtan uca testi
Oyun belleğine dokunulmaz, gerçek GitHub API kullanılır.
Çalıştırmak için: python test_updater_e2e.py
"""
import sys
import os
import hashlib
import json
import tempfile
import io
import unittest
import urllib.request
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# --- updater modülünü import et ---
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import updater


# ---------------------------------------------------------------------------
# 1. parse_version / newer — birim testleri
# ---------------------------------------------------------------------------
class TestVersionParsing(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(updater.parse_version("9.1.5.39"), (9, 1, 5, 39))

    def test_v_prefix(self):
        self.assertEqual(updater.parse_version("v9.1.5.39"), (9, 1, 5, 39))

    def test_newer_true(self):
        self.assertTrue(updater.newer("9.1.5.40", "9.1.5.39"))

    def test_newer_false_equal(self):
        self.assertFalse(updater.newer("9.1.5.39", "9.1.5.39"))

    def test_newer_false_older(self):
        self.assertFalse(updater.newer("9.1.5.38", "9.1.5.39"))

    def test_different_length(self):
        self.assertTrue(updater.newer("10.0", "9.99.99"))


# ---------------------------------------------------------------------------
# 2. latest() — gerçek GitHub API çağrısı
# ---------------------------------------------------------------------------
class TestLatestLive(unittest.TestCase):
    """Gerçek API çağrısı yapar; ağ yoksa atlanır."""

    def setUp(self):
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/FEDERALTURK/td2-loot-advisor/releases/latest",
                headers={"User-Agent": "TD2-test", "Accept": "application/vnd.github+json"},
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            self.skipTest(f"Network unavailable: {e}")

    def test_latest_returns_expected_keys(self):
        info = updater.latest(timeout=15)
        for key in ("version", "tag", "url", "setup", "sha_url", "zipball"):
            self.assertIn(key, info, f"Missing key: {key}")

    def test_version_format(self):
        info = updater.latest(timeout=15)
        v = info["version"]
        self.assertRegex(v, r"^\d+\.\d+", f"Unexpected version format: {v}")

    def test_setup_asset_exists(self):
        info = updater.latest(timeout=15)
        self.assertIsNotNone(info["setup"], "No installer (.exe) asset found in release")
        self.assertTrue(
            info["setup"].lower().endswith(".exe"),
            f"Installer URL doesn't end with .exe: {info['setup']}"
        )

    def test_sha_url_exists(self):
        info = updater.latest(timeout=15)
        self.assertIsNotNone(info["sha_url"], "No SHA256 file found in release")
        self.assertIn(".sha256", info["sha_url"].lower())

    def test_sha256_file_parseable(self):
        """SHA256SUMS dosyasının indirilebilir ve parse edilebilir olduğunu doğrula."""
        info = updater.latest(timeout=15)
        if not info.get("sha_url"):
            self.skipTest("No sha_url in release")

        req = urllib.request.Request(info["sha_url"],
                                     headers={"User-Agent": "TD2-test"})
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode("utf-8", "replace")

        lines = [l.strip() for l in content.splitlines() if l.strip()]
        self.assertGreater(len(lines), 0, "SHA256 file is empty")

        for line in lines:
            parts = line.split()
            self.assertGreaterEqual(
                len(parts), 2,
                f"SHA256 line doesn't have hash + filename: {line!r}"
            )
            sha_part = parts[0].lstrip("*")
            self.assertRegex(sha_part, r"^[0-9a-fA-F]{64}$",
                             f"Invalid SHA256 hash: {sha_part}")


# ---------------------------------------------------------------------------
# 3. _expected_sha() — mock testi
# ---------------------------------------------------------------------------
class TestExpectedSha(unittest.TestCase):
    def _make_info(self, sha_content):
        """SHA256 içeriğini döndüren mock info dict'i oluştur."""
        with patch("updater._get") as mock_get:
            mock_get.return_value = sha_content.encode("utf-8")
            info = {"sha_url": "https://example.com/SHA256SUMS.sha256"}
            result = updater._expected_sha(info, "TD2LootAdvisor_Setup_9.1.5.39.exe")
        return result

    def test_standard_format(self):
        content = "abc123def456" * 4 + "  TD2LootAdvisor_Setup_9.1.5.39.exe\n"
        # 48 chars - not valid; test with real 64-char sha
        sha = "a" * 64
        content = f"{sha}  TD2LootAdvisor_Setup_9.1.5.39.exe\n"
        result = self._make_info(content)
        self.assertEqual(result, sha.lower())

    def test_star_prefix_format(self):
        sha = "b" * 64
        content = f"{sha} *TD2LootAdvisor_Setup_9.1.5.39.exe\n"
        result = self._make_info(content)
        self.assertEqual(result, sha.lower())

    def test_no_match(self):
        sha = "c" * 64
        content = f"{sha}  SomeOtherFile.zip\n"
        result = self._make_info(content)
        self.assertIsNone(result)

    def test_missing_sha_url(self):
        result = updater._expected_sha({"sha_url": None}, "test.exe")
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# 4. _allowed() — kaynak güncelleme whitelist testi
# ---------------------------------------------------------------------------
class TestAllowed(unittest.TestCase):
    def test_py_files_allowed(self):
        self.assertTrue(updater._allowed("app.py"))
        self.assertTrue(updater._allowed("engine.py"))
        self.assertTrue(updater._allowed("updater.py"))

    def test_lang_files_allowed(self):
        self.assertTrue(updater._allowed("lang/tr.json"))
        self.assertTrue(updater._allowed("lang/en.json"))

    def test_meta_files_allowed(self):
        self.assertTrue(updater._allowed("meta/game_data.json"))
        self.assertTrue(updater._allowed("meta/meta_builds.json"))

    def test_requirements_allowed(self):
        self.assertTrue(updater._allowed("requirements.txt"))
        self.assertTrue(updater._allowed("requirements-voice.txt"))

    def test_readme_allowed(self):
        self.assertTrue(updater._allowed("README.md"))
        self.assertTrue(updater._allowed("README.tr.md"))

    def test_never_files_blocked(self):
        for f in ("builds.json", "stash.json", "progress.json", "tasks.json"):
            self.assertFalse(updater._allowed(f), f"Should be blocked: {f}")

    def test_private_blocked(self):
        self.assertFalse(updater._allowed("private/secret.key"))
        self.assertFalse(updater._allowed("private/anything.py"))

    def test_logs_blocked(self):
        self.assertFalse(updater._allowed("logs/app.log"))

    def test_dist_blocked(self):
        self.assertFalse(updater._allowed("dist/TD2LootAdvisor.exe"))

    def test_installer_blocked(self):
        self.assertFalse(updater._allowed("installer/setup.exe"))

    def test_path_traversal_blocked(self):
        self.assertFalse(updater._allowed("../etc/passwd"))


# ---------------------------------------------------------------------------
# 5. install_frozen() — SHA256 doğrulama testi (mock)
# ---------------------------------------------------------------------------
class TestInstallFrozen(unittest.TestCase):
    def test_sha_mismatch_raises(self):
        """Yanlış SHA256 ile install_frozen() RuntimeError fırlatmalı."""
        fake_data = b"fake installer content"
        real_sha = hashlib.sha256(fake_data).hexdigest()
        wrong_sha = "0" * 64

        sha_content = f"{wrong_sha}  TD2LootAdvisor_Setup_9.1.5.39.exe\n"

        def fake_get(url, *args, **kwargs):
            if "SHA256SUMS" in url:
                return sha_content.encode("utf-8")
            return fake_data

        info = {
            "setup": "https://example.com/TD2LootAdvisor_Setup_9.1.5.39.exe",
            "sha_url": "https://example.com/SHA256SUMS.sha256",
        }

        with patch("updater._get", side_effect=fake_get):
            with self.assertRaises(RuntimeError, msg="SHA mismatch must raise"):
                updater.install_frozen(info)

    def test_no_setup_raises(self):
        """Setup URL'si olmadan install_frozen() RuntimeError fırlatmalı."""
        with self.assertRaises(RuntimeError):
            updater.install_frozen({"setup": None, "sha_url": None})


# ---------------------------------------------------------------------------
# 6. update_source() — ZIP dosyası testi (mock)
# ---------------------------------------------------------------------------
class TestUpdateSource(unittest.TestCase):
    def _make_zip(self, files: dict) -> bytes:
        """Dict[rel_path, content] → zipball benzeri zip baytları üret."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for rel, content in files.items():
                zf.writestr(f"owner-repo-abc123/{rel}", content)
        return buf.getvalue()

    def test_allowed_files_updated(self):
        zip_data = self._make_zip({
            "app.py": "# new version\n",
            "lang/tr.json": '{"hello": "merhaba"}',
        })
        info = {"zipball": "https://example.com/source.zip", "tag": "v9.1.5.40"}

        with tempfile.TemporaryDirectory() as base:
            with patch("updater._get", return_value=zip_data):
                changed, backup = updater.update_source(info, base)

        self.assertEqual(changed, 2)

    def test_never_files_not_written(self):
        zip_data = self._make_zip({
            "builds.json": '{"hacked": true}',
            "stash.json": '{}',
            "app.py": "# safe\n",
        })
        info = {"zipball": "https://example.com/source.zip", "tag": "v9.1.5.40"}

        with tempfile.TemporaryDirectory() as base:
            # pre-create builds.json with original content
            orig = Path(base) / "builds.json"
            orig.write_text('{"original": true}')

            with patch("updater._get", return_value=zip_data):
                changed, _ = updater.update_source(info, base)

        # builds.json değiştirilmemeli
        self.assertEqual(orig.read_text(), '{"original": true}',
                         "builds.json must never be overwritten by update_source")
        # sadece app.py değişmeli
        self.assertEqual(changed, 1)

    def test_identical_files_not_counted(self):
        content = "# same\n"
        zip_data = self._make_zip({"app.py": content})
        info = {"zipball": "https://example.com/source.zip", "tag": "v9.1.5.40"}

        with tempfile.TemporaryDirectory() as base:
            (Path(base) / "app.py").write_text(content)
            with patch("updater._get", return_value=zip_data):
                changed, _ = updater.update_source(info, base)

        self.assertEqual(changed, 0, "Identical files should not count as changed")


# ---------------------------------------------------------------------------
# 7. Entegrasyon testi: latest() + newer() akışı
# ---------------------------------------------------------------------------
class TestFullUpdateFlow(unittest.TestCase):
    """Gerçek GitHub API + versiyon karşılaştırma."""

    def setUp(self):
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/FEDERALTURK/td2-loot-advisor/releases/latest",
                headers={"User-Agent": "TD2-test", "Accept": "application/vnd.github+json"},
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            self.skipTest(f"Network unavailable: {e}")

    def test_full_flow_very_old_version(self):
        """Çok eski bir sürüm için güncelleme bulunmalı."""
        info = updater.latest(timeout=15)
        self.assertTrue(
            updater.newer(info["version"], "1.0.0.0"),
            f"Should be newer than 1.0.0.0, got {info['version']}"
        )

    def test_full_flow_current_version(self):
        """Mevcut release versiyonundan daha yeni olmamalı."""
        info = updater.latest(timeout=15)
        self.assertFalse(
            updater.newer(info["version"], info["version"]),
            "Current version should not be newer than itself"
        )


# ---------------------------------------------------------------------------
# Ana çalıştırma
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("TD2 Loot Advisor — updater.py E2E Test Suite")
    print("=" * 60)
    result = unittest.main(verbosity=2, exit=False)
    if result.result.failures or result.result.errors:
        sys.exit(1)
    print("\n✅ All tests passed.")
