"""Deterministic in-game controls, microphone lifetime and voiced AI replies."""
from pathlib import Path
import queue
import sys
import threading
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app
import game_assistant as ga
from workqueue import LatestWorker


class Timer:
    def __init__(self, seconds, callback): self.callback, self.cancelled = callback, False
    def start(self): pass
    def cancel(self): self.cancelled = True


class Recorder:
    active = False
    def start(self): self.active = True
    def stop(self): self.active = False; return np.ones(16000, dtype=np.float32)


class ControlsTests(unittest.TestCase):
    def test_defaults_are_six_distinct_shortcuts(self):
        result = ga.bindings({})
        self.assertEqual(len(result), 6)
        self.assertEqual((result["<f6>"], result["<f9>"], result["<f12>"]), ("translate_toggle", "voice", "cancel"))

    def test_duplicate_and_empty_shortcuts_are_rejected(self):
        for settings in [{"voice_hotkey": " <F6> "}, {"voice_hotkey": ""}, {"voice_hotkey": None}]:
            with self.assertRaises(ValueError): ga.bindings(settings)

    def test_hotkeys_debounce_and_old_listener_is_invalidated(self):
        made, events, clock = [], [], [0.0]
        def factory(mapping):
            listener = SimpleNamespace(mapping=mapping, start=Mock(), stop=Mock())
            made.append(listener); return listener
        manager = ga.Hotkeys(events.append, factory, lambda: clock[0])
        manager.configure({}); first = made[0]
        first.mapping["<f9>"](); first.mapping["<f9>"]()
        self.assertEqual(events, ["voice"])
        clock[0] = 1
        manager.configure({})
        first.mapping["<f9>"]()
        self.assertEqual(events, ["voice"])
        made[1].mapping["<f6>"]()
        self.assertEqual(events[-1], "translate_toggle")
        manager.stop(); first.stop.assert_called_once(); made[1].stop.assert_called_once()


class SessionTests(unittest.TestCase):
    def session(self, transcribe=None):
        events = []
        session = ga.VoiceSession(Recorder(), transcribe or (lambda audio: "Bu eşyayı saklayayım mı?"),
                                  lambda *event: events.append(event), timer_factory=Timer)
        self.addCleanup(lambda: (session.close(), session.worker.wait_idle(2)))
        return session, events

    def test_press_twice_records_then_transcribes_and_closes_microphone(self):
        session, events = self.session()
        session.toggle(); self.assertTrue(session.worker.wait_idle(2))
        self.assertTrue(session.recording); self.assertTrue(session.recorder.active)
        session.toggle(); self.assertTrue(session.worker.wait_idle(2))
        self.assertFalse(session.recorder.active)
        self.assertEqual(session.state, "idle")
        self.assertEqual([event[1] for event in events], ["starting", "listening", "transcribing", "text"])

    def test_old_timer_cannot_stop_new_recording(self):
        session, _ = self.session()
        session.toggle(); session.worker.wait_idle(2); old_timer = session.timer
        session.finish(); session.worker.wait_idle(2)
        session.toggle(); session.worker.wait_idle(2)
        old_timer.callback()
        self.assertTrue(session.recorder.active); self.assertEqual(session.state, "listening")

    def test_timeout_finishes_current_recording(self):
        session, events = self.session()
        session.toggle(); session.worker.wait_idle(2)
        session.timer.callback(); session.worker.wait_idle(2)
        self.assertFalse(session.recorder.active)
        self.assertTrue(any(event[1] == "text" for event in events))

    def test_cancel_drops_transcription_result(self):
        entered, release = threading.Event(), threading.Event()
        def transcribe(audio): entered.set(); release.wait(2); return "old question"
        session, events = self.session(transcribe)
        session.toggle(); session.worker.wait_idle(2); session.finish()
        self.assertTrue(entered.wait(1)); session.cancel(); release.set(); session.worker.wait_idle(2)
        self.assertFalse(any(event[1] == "text" for event in events))
        self.assertFalse(session.recorder.active)

    def test_microphone_error_can_be_retried(self):
        session, events = self.session()
        with patch.object(session.recorder, "start", side_effect=RuntimeError("no device")):
            session.toggle(); session.worker.wait_idle(2)
        self.assertEqual(session.state, "idle")
        self.assertEqual(events[-1][1], "error")
        session.toggle(); session.worker.wait_idle(2)
        self.assertTrue(session.recorder.active)

    def test_empty_transcription_is_not_sent_as_question(self):
        session, events = self.session(lambda audio: "")
        session.toggle(); session.worker.wait_idle(2); session.finish(); session.worker.wait_idle(2)
        self.assertTrue(any(event[1] == "empty" for event in events))
        self.assertFalse(any(event[1] == "text" for event in events))


class IntegrationTests(unittest.TestCase):
    def obj(self):
        obj = app.App.__new__(app.App)
        obj.cfg = {"settings": {"ai_provider": "ollama", "ollama_url": "http://unused", "ollama_model": "test", "speak_chat": False}}
        obj.results, obj.root, obj._closing = queue.Queue(), Mock(), False
        obj.chat_hist = []
        obj.chat_add, obj.speak, obj._assistant_status = Mock(), Mock(), Mock()
        obj.build_context = Mock(return_value="{}")
        obj._assistant_jobs = LatestWorker("test-assistant")
        obj._assistant_setup_jobs = SimpleNamespace(invalidate=Mock())
        obj._voice_session = SimpleNamespace(current=lambda generation: True, cancel=Mock(), recording=False)
        obj.speaker = Mock()
        self.addCleanup(lambda: obj._assistant_jobs.close(wait=True, timeout=2))
        return obj

    def test_voice_reply_is_spoken_even_when_chat_speech_is_off(self):
        obj = self.obj()
        with patch.object(app, "ask_ollama", return_value="Bu eşyayı sakla."):
            obj.ask("Ne yapmalıyım?", voice=True, voice_generation=1)
            self.assertTrue(obj._assistant_jobs.wait_idle(2)); obj.poll()
        obj.speak.assert_called_once_with("Bu eşyayı sakla.", cancellable=True)
        self.assertEqual(obj.chat_hist[-1]["role"], "assistant")

    def test_cancel_before_ui_delivery_discards_answer_and_audio(self):
        obj = self.obj()
        with patch.object(app, "ask_ollama", return_value="old reply"):
            obj.ask("question", voice=True, voice_generation=1)
            obj._assistant_jobs.wait_idle(2); obj.cancel_assistant(); obj.poll()
        obj.speak.assert_not_called()
        self.assertEqual(len(obj.chat_hist), 1)

    def test_provider_error_is_disclosed_in_voiced_fallback(self):
        obj = self.obj(); obj.quick_answer = Mock(return_value="Yerleşik yanıt")
        with patch.object(app, "ask_ollama", side_effect=RuntimeError("offline")):
            obj.ask("question", voice=True, voice_generation=1)
            obj._assistant_jobs.wait_idle(2); obj.poll()
        self.assertIn(app.t("ga.provider_fallback"), obj.speak.call_args.args[0])
        self.assertIn("Yerleşik yanıt", obj.speak.call_args.args[0])

    def test_new_microphone_generation_discards_old_answer(self):
        obj = self.obj()
        obj._voice_session.current = lambda generation: False
        with patch.object(app, "ask_ollama", return_value="old reply"):
            obj.ask("question", voice=True, voice_generation=1)
            obj._assistant_jobs.wait_idle(2); obj.poll()
        obj.speak.assert_not_called()

    def test_voice_shortcut_is_independent_of_loot_running_state(self):
        obj = self.obj(); obj.running = False; obj.toggle_voice = Mock()
        obj._hotkey_action("voice")
        obj.toggle_voice.assert_called_once()

    def test_translation_pause_keeps_global_shortcuts_and_resumes(self):
        obj = self.obj(); obj.lt_stop_ev = object(); obj.sp = None
        obj.lt_stop = Mock(side_effect=lambda: setattr(obj, "lt_stop_ev", None))
        obj.speech_stop, obj._lt_hide, obj.toast = Mock(), Mock(), Mock()
        obj.lt_start = Mock(return_value=True); obj._global_hotkeys = Mock()
        obj.lt_toggle(); obj.lt_toggle()
        obj.lt_stop.assert_called_once(); obj.lt_start.assert_called_once_with(quiet=True)
        obj._global_hotkeys.stop.assert_not_called()

    def test_delayed_screen_capture_is_rejected_after_pause(self):
        obj = self.obj(); obj._lt_revision = 4; obj._translation_jobs = Mock()
        result = obj._queue_translation({"width": 500}, revision=3)
        self.assertIsNone(result); obj._translation_jobs.submit.assert_not_called()

    def test_stopped_speech_source_cannot_enqueue_new_translation(self):
        obj = self.obj(); obj._speech_generation = 2; obj._translation_jobs = Mock()
        obj._sp_text("Complete the mission", generation=1)
        obj._translation_jobs.submit.assert_not_called()

    def test_recorder_retains_at_most_twenty_seconds(self):
        stream = SimpleNamespace(start=Mock(), stop=Mock(), close=Mock())
        callback = []
        def make_stream(**kwargs): callback.append(kwargs["callback"]); return stream
        with patch.dict(sys.modules, {"sounddevice": SimpleNamespace(InputStream=make_stream)}):
            recorder = app.Recorder(); recorder.start()
            for _ in range(10): callback[0](np.ones((100000, 1), dtype=np.float32), 100000, None, None)
            audio = recorder.stop()
        self.assertEqual(len(audio), 320000)
        stream.close.assert_called_once()
        self.assertFalse(recorder.active)

    def test_stt_model_is_reused_with_bounded_cpu_threads(self):
        constructor = Mock(return_value=SimpleNamespace(transcribe=Mock(return_value=([SimpleNamespace(text="Merhaba")], None))))
        with patch.dict(sys.modules, {"faster_whisper": SimpleNamespace(WhisperModel=constructor)}), \
             patch.dict(app._WHISPER, {"key": None, "model": None, "used": 0}):
            cfg = {"settings": {"stt_model": "base", "stt_device": "cpu"}}
            app.transcribe(np.ones(16000, dtype=np.float32), cfg)
            app.transcribe(np.ones(16000, dtype=np.float32), cfg)
            self.assertEqual(constructor.call_count, 1)
            self.assertEqual(constructor.call_args.kwargs["cpu_threads"], 2)
            self.assertEqual(constructor.call_args.kwargs["compute_type"], "int8")

    def test_voice_question_roundtrip_through_real_local_http_provider(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                payload = json.dumps({"message": {"content": "Bu eşyayı sakla."}}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            obj = self.obj(); obj.cfg["settings"]["ollama_url"] = f"http://127.0.0.1:{server.server_port}"
            obj.ask("Bu eşyayı saklayayım mı?", voice=True, voice_generation=1)
            self.assertTrue(obj._assistant_jobs.wait_idle(3)); obj.poll()
            self.assertEqual(received[0]["messages"][-1]["content"], "Bu eşyayı saklayayım mı?")
            obj.speak.assert_called_once_with("Bu eşyayı sakla.", cancellable=True)
        finally:
            server.shutdown(); server.server_close()


if __name__ == "__main__":
    unittest.main()
