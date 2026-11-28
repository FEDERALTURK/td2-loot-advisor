"""Security regression tests for the local HTTP API log boundary."""
import sys
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import localapi


class LocalApiLogSecurityTests(unittest.TestCase):
    def test_auth_query_token_is_redacted_from_request_logs(self):
        token = "unit-test-token-never-log-this"
        api = localapi.LocalAPI(lambda: {"ok": True}, token=token, port=0, allow_control=False)
        api.start()
        port = api.httpd.server_address[1]
        try:
            with patch.object(localapi.log, "debug") as debug:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/api/state?t={token}", timeout=3
                ) as response:
                    self.assertEqual(response.status, 200)
                logged = " ".join(str(call.args) for call in debug.call_args_list)
            self.assertNotIn(token, logged)
            self.assertIn("t=<redacted>", logged)
        finally:
            api.stop()

    def test_lan_listener_fails_closed_without_https(self):
        api = localapi.LocalAPI(lambda: {"ok": True}, token="test-only-token", port=0, lan=True)
        with self.assertRaisesRegex(OSError, "LAN sharing is disabled until HTTPS"):
            api.start()
        self.assertIsNone(api.httpd)


if __name__ == "__main__":
    unittest.main()
