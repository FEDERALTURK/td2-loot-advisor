"""Expensive scan popup rendering is deferred until Tk is idle."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class ResultUiDeferTests(unittest.TestCase):
    def test_popup_waits_for_idle_and_skips_after_close(self):
        callbacks, shown = [], []
        class FakeTkRoot(app.tk.Misc):
            def after_idle(self, callback): callbacks.append(callback)
        instance = SimpleNamespace(root=FakeTkRoot(), _closing=False,
                                   popup=lambda *args: shown.append(args))
        app.App._defer_scan_popup(instance, "KEEP", {"name": "Example"}, [], None)
        self.assertEqual(shown, [])
        callbacks.pop()()
        self.assertEqual(shown, [("KEEP", {"name": "Example"}, [], None)])
        app.App._defer_scan_popup(instance, "KEEP", {}, [], None)
        instance._closing = True
        callbacks.pop()()
        self.assertEqual(len(shown), 1)


if __name__ == "__main__":
    unittest.main()
