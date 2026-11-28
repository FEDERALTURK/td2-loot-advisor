import socket
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import localapi


class LocalApiPortTests(unittest.TestCase):
    def test_find_available_port_skips_reserved_port(self):
        port = localapi.find_available_port(18797, reserved=(18797,))
        self.assertIsNotNone(port)
        self.assertNotEqual(port, 18797)

    def test_find_available_port_skips_port_already_bound(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        busy = sock.getsockname()[1]
        try:
            port = localapi.find_available_port(busy, host="127.0.0.1")
            self.assertIsNotNone(port)
            self.assertNotEqual(port, busy)
        finally:
            sock.close()


if __name__ == "__main__":
    unittest.main()
