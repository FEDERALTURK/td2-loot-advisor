"""Thread-safe hotkey routing and bounded, cancellable microphone sessions.

No Tk calls, provider credentials, screen capture or network in this module.
"""
import threading
import time
from workqueue import LatestWorker


HOTKEYS = {
    "scan": ("hotkey", "<f8>"), "voice": ("voice_hotkey", "<f9>"),
    "tasks": ("tasks_hotkey", "<f10>"), "translate_once": ("tr_hotkey", "<f7>"),
    "translate_toggle": ("tr_toggle_hotkey", "<f6>"), "cancel": ("assistant_cancel_hotkey", "<f12>"),
}


def bindings(settings, validator=None):
    result, seen = {}, {}
    for action, (key, default) in HOTKEYS.items():
        value = settings.get(key, default)
        if not isinstance(value, str) or not value.strip(): raise ValueError(key + ": empty hotkey")
        value = value.strip().lower().replace(" ", "")
        identity = tuple(sorted(value.split("+")))
        if identity in seen: raise ValueError(f"{key}: conflicts with {seen[identity]}")
        if validator: validator(value)
        seen[identity] = key
        result[value] = action
    return result


class Hotkeys:
    def __init__(self, emit, factory=None, clock=time.monotonic):
        self.emit, self.factory, self.clock = emit, factory, clock
        self.listener = None
        self.generation = 0
        self.last = {}

    def configure(self, settings):
        from pynput import keyboard
        mapping = bindings(settings, keyboard.HotKey.parse)
        self.stop()
        generation = self.generation
        def fire(action):
            if generation != self.generation: return
            now = self.clock()
            if now - self.last.get(action, float("-inf")) < .35: return
            self.last[action] = now
            self.emit(action)
        listener = (self.factory or keyboard.GlobalHotKeys)(
            {key: lambda action=action: fire(action) for key, action in mapping.items()})
        self.listener = listener
        try: listener.start()
        except Exception:
            self.stop()
            raise

    def stop(self):
        self.generation += 1
        self.last.clear()
        if self.listener:
            self.listener.stop()
            self.listener = None


class VoiceSession:
    """One recording or transcription at a time; old timers/results are ignored."""
    def __init__(self, recorder, transcribe, emit, max_seconds=20, timer_factory=threading.Timer):
        self.recorder, self.transcribe, self.emit = recorder, transcribe, emit
        self.max_seconds, self.timer_factory = max_seconds, timer_factory
        self.worker = LatestWorker("assistant-microphone")
        self.lock = threading.RLock()
        self.generation, self.state, self.timer, self.closed = 0, "idle", None, False

    def current(self, generation):
        with self.lock: return not self.closed and generation == self.generation

    @property
    def recording(self):
        with self.lock: return self.state in ("starting", "listening")

    def _event(self, generation, kind, value=""):
        if self.current(generation): self.emit(generation, kind, value)

    def toggle(self):
        with self.lock:
            if self.closed: return
            if self.state == "listening": return self.finish(self.generation)
            if self.state != "idle":
                self._event(self.generation, "busy")
                return
            self.generation += 1
            generation = self.generation
            self.state = "starting"
        self._event(generation, "starting")
        def start(token):
            try:
                if self.recorder.active: self.recorder.stop()
                if not self.current(generation): return
                self.recorder.start()
                with self.lock:
                    if not self.current(generation):
                        self.recorder.stop(); return
                    self.state = "listening"
                    self.timer = self.timer_factory(self.max_seconds, lambda: self.finish(generation))
                    self.timer.daemon = True
                    self.timer.start()
                self._event(generation, "listening")
            except Exception as error:
                if self.recorder.active:
                    try: self.recorder.stop()
                    except Exception: pass
                with self.lock:
                    if self.current(generation): self.state = "idle"
                self._event(generation, "error", str(error))
        self.worker.submit(start)

    def finish(self, generation=None):
        with self.lock:
            generation = self.generation if generation is None else generation
            if not self.current(generation) or self.state != "listening": return
            self.state = "transcribing"
            if self.timer: self.timer.cancel(); self.timer = None
        self._event(generation, "transcribing")
        def finish(token):
            try:
                audio = self.recorder.stop()
                if not self.current(generation): return
                if len(audio) < 8000:
                    self._event(generation, "too_short")
                    return
                text = self.transcribe(audio)
                self._event(generation, "text" if text else "empty", text)
            except Exception as error:
                self._event(generation, "error", str(error))
            finally:
                with self.lock:
                    if self.current(generation): self.state = "idle"
        self.worker.submit(finish)

    def cancel(self):
        with self.lock:
            self.generation += 1
            generation = self.generation
            self.state = "idle"
            if self.timer: self.timer.cancel(); self.timer = None
        self.worker.invalidate()
        # A following start may replace this cleanup, but start always closes
        # any previous stream before opening a new one.
        def cleanup(token):
            if self.recorder.active: self.recorder.stop()
        if not self.closed: self.worker.submit(cleanup)
        return generation

    def close(self):
        with self.lock:
            if self.closed: return
        self.cancel()
        with self.lock: self.closed = True
        # Keep the pending stream cleanup; close the worker after it executes.
        def cleanup(token):
            try:
                if self.recorder.active: self.recorder.stop()
            finally: self.worker.close()
        self.worker.submit(cleanup)
