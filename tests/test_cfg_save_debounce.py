"""Active-app config saves are coalesced through the Tk result queue."""
from pathlib import Path
import queue
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class ConfigSaveDebounceTests(unittest.TestCase):
    def test_save_cfg_queues_active_app_request(self):
        cfg = {"settings": {"ui_theme": "kaivolt"}}
        requests = queue.Queue()
        active = SimpleNamespace(cfg=cfg, results=requests, _closing=False)
        with patch.object(app, "_ACTIVE_APP", active), patch.object(app.safeio, "write_json") as write:
            app.save_cfg(cfg)
        self.assertEqual(requests.get_nowait(), ("cfg_save_requested",))
        write.assert_not_called()

    def test_scheduled_save_is_coalesced_and_flush_writes_latest_cfg(self):
        cfg = {"settings": {"ui_theme": "field_clean"}}
        root = SimpleNamespace(after=Mock(return_value="new-job"), after_cancel=Mock())
        instance = SimpleNamespace(root=root, cfg=cfg, _cfg_save_job="old-job", _cfg_dirty=True)
        instance._flush_cfg_save = lambda: app.App._flush_cfg_save(instance)
        with patch.object(app.safeio, "seal_settings", return_value=cfg), patch.object(app.safeio, "write_json") as write:
            app.App._schedule_cfg_save(instance)
            root.after_cancel.assert_called_once_with("old-job")
            root.after.assert_called_once()
            app.App._flush_cfg_save(instance)
        write.assert_called_once_with(app.CFG_PATH, cfg)
        self.assertIsNone(instance._cfg_save_job)


if __name__ == "__main__":
    unittest.main()
