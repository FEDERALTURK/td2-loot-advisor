import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import display


class DisplayParserLimitTests(unittest.TestCase):
    def test_parse_cfg_rejects_oversized_input_without_tokenizing(self):
        self.assertEqual(display.parse_cfg("x" * (2 * 1024 * 1024 + 1)), {})

    def test_parse_cfg_keeps_small_read_only_tables(self):
        self.assertEqual(display.parse_cfg('{ graphics = { width = 1920, enabled = true } }'),
                         {"graphics": {"width": 1920, "enabled": True}})


if __name__ == "__main__":
    unittest.main()
