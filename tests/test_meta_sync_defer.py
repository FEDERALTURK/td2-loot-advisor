"""Meta download completion must yield to Tk before applying widget updates."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class MetaSyncDeferTests(unittest.TestCase):
    def test_completion_is_scheduled_after_idle(self):
        callback = Mock()
        root = SimpleNamespace(after_idle=Mock(return_value="job"))
        instance = SimpleNamespace(root=root, _closing=False, sync_done=callback)
        app.App._defer_meta_sync_done(instance, {"news": []}, True)
        root.after_idle.assert_called_once()
        root.after_idle.call_args.args[0]()
        callback.assert_called_once_with({"news": []}, True)


if __name__ == "__main__":
    unittest.main()
