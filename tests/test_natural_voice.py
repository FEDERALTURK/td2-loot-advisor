"""Offline recordings, opt-in online speech and bounded speaker regressions."""
import hashlib
import json
from pathlib import Path
import queue
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import wave
from array import array

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app
import voicepack


class NaturalVoiceTests(unittest.TestCase):
    def speaker(self):
        obj = app.Speaker.__new__(app.Speaker)
        obj.q, obj.err, obj.last_fx = queue.Queue(maxsize=4), None, None
        obj._serial, obj._closed = 0, False
        return obj

    def run_speaker(self, obj, engine=None):
        obj.q.put_nowait(None)
        init = Mock(return_value=engine or Mock())
        with patch.dict(sys.modules, {"pyttsx3": SimpleNamespace(init=init)}):
            obj.run()

    def test_two_recorded_packs_have_valid_audio_and_hashes(self):
        manifest = json.loads((ROOT / "meta/voice_packs.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["packs"]), set(voicepack.NATURAL_PACKS))
        for pack, data in manifest["packs"].items():
            self.assertEqual(data["voice"], voicepack.NATURAL_VOICES[pack])
            self.assertEqual(set(data["events"]), voicepack.Recordings.EVENTS)
            for event, metadata in data["events"].items():
                path = voicepack.Recordings(ROOT / "meta").event(pack, event)
                self.assertIsNotNone(path)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), metadata["sha256"])
                with wave.open(str(path)) as audio:
                    self.assertEqual((audio.getnchannels(), audio.getsampwidth(), audio.getframerate()), (1, 2, 24000))
                    self.assertAlmostEqual(audio.getnframes() / audio.getframerate(), metadata["seconds"], places=2)
                    self.assertGreater(audio.getnframes() / audio.getframerate(), .3)
                    samples = array("h", audio.readframes(audio.getnframes()))
                    self.assertGreater(max(abs(value) for value in samples), 500)

    def test_recording_paths_reject_unrecognized_pack_and_event(self):
        recordings = voicepack.Recordings(ROOT / "meta")
        self.assertIsNone(recordings.event("../private", "keep"))
        self.assertIsNone(recordings.event("natural_tr", "../../secret"))

    def test_offline_recording_never_invokes_online_tts(self):
        obj = self.speaker(); obj.files(["demo.wav"])
        with patch.object(voicepack, "play_audio") as play, patch.object(voicepack, "neural_audio") as online:
            self.run_speaker(obj)
        play.assert_called_once_with("demo.wav"); online.assert_not_called()

    def test_online_disabled_keeps_dynamic_text_local(self):
        obj = self.speaker(); obj.say("Merhaba", hint="tr-tr", pack="natural_tr", online=False)
        engine = Mock(); engine.getProperty.return_value = []
        with patch.object(voicepack, "neural_audio") as online:
            self.run_speaker(obj, engine)
        online.assert_not_called(); engine.say.assert_called_once_with("Merhaba")

    def test_online_failure_falls_back_without_losing_text(self):
        obj = self.speaker(); obj.say("Merhaba", hint="tr-tr", pack="natural_tr", online=True)
        engine = Mock(); engine.getProperty.return_value = []
        with patch.object(voicepack, "neural_audio", side_effect=TimeoutError):
            self.run_speaker(obj, engine)
        engine.say.assert_called_once_with("Merhaba")
        self.assertIn("fallback", obj.err)

    def test_superseded_online_audio_is_not_played(self):
        obj = self.speaker(); obj.say("old", pack="natural_en", online=True)
        def generate(*args):
            obj._serial += 1
            return "old.mp3"
        with patch.object(voicepack, "neural_audio", side_effect=generate), patch.object(voicepack, "play_audio") as play:
            self.run_speaker(obj)
        play.assert_not_called()

    def test_queue_is_bounded_and_close_does_not_block(self):
        obj = self.speaker()
        for n in range(30): obj.say(str(n), interrupt=False)
        self.assertEqual(obj.q.qsize(), 4)
        obj.say("latest")
        self.assertEqual(obj.q.qsize(), 1)
        obj.close(); obj.say("ignored")
        self.assertIsNone(obj.q.get_nowait()); self.assertTrue(obj.q.empty())

    def test_online_cache_hides_text_and_skips_repeated_service_call(self):
        calls = []
        class Communicate:
            def __init__(self, text, voice, **kwargs): calls.append((text, voice))
            async def save(self, path): Path(path).write_bytes(b"ID3" + b"x" * 2000)
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {"edge_tts": SimpleNamespace(Communicate=Communicate)}):
            first = voicepack.neural_audio("Private example text", "natural_tr", tmp)
            second = voicepack.neural_audio("Private example text", "natural_tr", tmp)
            self.assertEqual(first, second); self.assertEqual(len(calls), 1)
            self.assertNotIn("Private", first.name)
            self.assertEqual([p.suffix for p in Path(tmp).iterdir()], [".mp3"])

    def test_invalid_online_audio_does_not_poison_cache(self):
        class Communicate:
            def __init__(self, *args, **kwargs): pass
            async def save(self, path): Path(path).write_bytes(b"not audio")
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {"edge_tts": SimpleNamespace(Communicate=Communicate)}):
            with self.assertRaises(RuntimeError): voicepack.neural_audio("Example", "natural_en", tmp)
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
