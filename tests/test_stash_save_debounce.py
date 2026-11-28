"""The scan result path coalesces stash writes and flushes on close."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class StashSaveDebounceTests(unittest.TestCase):
    def test_repeated_schedule_replaces_timer(self):
        root = SimpleNamespace(after=Mock(return_value="job-2"), after_cancel=Mock())
        instance = SimpleNamespace(root=root, stash=SimpleNamespace(save=Mock()), _stash_save_job="job-1")
        instance._flush_stash_save = lambda: app.App._flush_stash_save(instance)
        app.App._schedule_stash_save(instance)
        root.after_cancel.assert_called_once_with("job-1")
        self.assertEqual(root.after.call_args.args[0], 500)
        self.assertEqual(instance._stash_save_job, "job-2")
        instance.stash.save.assert_not_called()

    def test_flush_clears_pending_timer_and_saves_once(self):
        root = SimpleNamespace(after_cancel=Mock())
        stash = SimpleNamespace(save=Mock())
        instance = SimpleNamespace(root=root, stash=stash, _stash_save_job="pending")
        app.App._flush_stash_save(instance)
        self.assertIsNone(instance._stash_save_job)
        root.after_cancel.assert_called_once_with("pending")
        stash.save.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
