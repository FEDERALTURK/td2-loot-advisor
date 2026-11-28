"""Reject non-HTTP and credential/query-bearing API base URLs."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dropstats
import reports


class NetworkUrlSecurityTests(unittest.TestCase):
    def test_valid_http_urls_are_preserved_without_trailing_slash(self):
        for module in (dropstats, reports):
            self.assertEqual(module._http_base("https://example.test/api/"), "https://example.test/api")
            self.assertEqual(module._http_base("http://127.0.0.1:8766"), "http://127.0.0.1:8766")

    def test_non_http_and_ambiguous_urls_are_rejected(self):
        bad_urls = (
            "file:///C:/Users/Public/test",
            "javascript:alert(1)",
            "https://user:password@example.test/api",
            "https://example.test/api?token=secret",
            "https://example.test:invalid/api",
        )
        for module in (dropstats, reports):
            for url in bad_urls:
                with self.subTest(module=module.__name__, url=url), self.assertRaises(ValueError):
                    module._http_base(url)


if __name__ == "__main__":
    unittest.main()
