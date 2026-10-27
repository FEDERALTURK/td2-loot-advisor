"""Launcher decisions without installing packages or starting the application."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("td2_launch",ROOT/"scripts/launch.py")
launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/"requirements.txt").write_text("mss\n")
        self.installed=set(launch.CORE)|{m for _,m in launch.OCR};self.calls=[]
    def find(self,m): return object() if m in self.installed else None
    def fake_run(self,args,**kw): self.calls.append(args);self.installed.update(launch.CORE);return SimpleNamespace(returncode=0)
    def prepare(self,**kw): return launch.prepare(self.root,finder=self.find,runner=self.fake_run,**kw)
    def test_first_and_repeated_ready_launch_never_runs_pip(self):
        self.assertTrue(self.prepare()[0]);self.assertTrue(self.prepare()[0]);self.assertEqual(self.calls,[])
    def test_missing_core_installs_and_rechecks(self):
        self.installed.remove("mss");self.assertTrue(self.prepare()[0]);self.assertEqual(len(self.calls),1)
        self.assertIn("-r",self.calls[0])
    def test_check_does_not_install_or_write(self):
        self.installed.remove("mss");self.assertEqual(self.prepare(check_only=True),(False,["mss"]))
        self.assertEqual(self.calls,[]);self.assertFalse((self.root/"cache").exists())
    def test_changed_requirements_revalidated(self):
        self.prepare();(self.root/"requirements.txt").write_text("mss\npillow\n")
        self.assertTrue(self.prepare()[0]);self.assertEqual(len(self.calls),1)
    def test_optional_voice_is_only_installed_on_request(self):
        self.prepare();self.assertEqual(self.calls,[]);self.prepare(extras=True)
        self.assertIn("faster-whisper",self.calls[0]);self.assertNotIn("onnxruntime",self.calls[0])
    def test_existing_directml_module_is_not_replaced(self):
        self.installed.remove("rapidocr");self.prepare();self.assertIn("rapidocr",self.calls[0])
        self.assertNotIn("onnxruntime",self.calls[0]);self.prepare();self.assertEqual(len(self.calls),1)
    def test_core_install_failure_prevents_launch(self):
        self.installed.remove("mss")
        ok,_=launch.prepare(self.root,finder=self.find,runner=lambda *a,**k:SimpleNamespace(returncode=1))
        self.assertFalse(ok);self.assertFalse((self.root/"cache").exists())


if __name__=="__main__":unittest.main()
