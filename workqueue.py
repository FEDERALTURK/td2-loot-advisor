"""Bounded background work for live OCR and translation.

One daemon thread runs one job at a time. While it is busy, only the newest
pending job is retained. A generation token lets callers reject results from
superseded work both before posting to the UI and when the UI handles them.
Running functions are not forcibly interrupted; they should use their own I/O
timeouts and may check ``is_current(token)`` between expensive steps.
"""
import logging
import threading
import time

log = logging.getLogger("td2.workqueue")


class LatestWorker:
    """A single worker with one replaceable pending slot.

    ``submit(fn)`` returns a unique integer token; ``fn(token)`` runs off the UI
    thread. Every new submission immediately makes all earlier tokens stale.
    ``invalidate()`` also drops pending work, for example on stop or a settings
    change. ``close()`` is nonblocking by default and invalidates all tokens.
    """

    def __init__(self, name="latest-work"):
        self._cv = threading.Condition()
        self._pending = None
        self._active = None
        self._latest = None
        self._serial = 0
        self._closed = False
        self._counts = {"submitted": 0, "started": 0, "completed": 0,
                        "failed": 0, "replaced": 0, "cancelled": 0}
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._thread.start()

    def submit(self, fn):
        """Schedule ``fn(token)``; replace any pending job without waiting."""
        if not callable(fn):
            raise TypeError("job must be callable")
        with self._cv:
            if self._closed:
                raise RuntimeError("worker is closed")
            self._serial += 1
            token = self._serial
            self._latest = token
            if self._pending is not None:
                self._counts["replaced"] += 1
            self._pending = (token, fn)
            self._counts["submitted"] += 1
            self._cv.notify_all()
            return token

    def is_current(self, token):
        """Whether a submitted token still represents the newest request."""
        with self._cv:
            return not self._closed and token is not None and token == self._latest

    def invalidate(self):
        """Make all results stale and discard pending work; keep the worker."""
        with self._cv:
            self._latest = None
            if self._pending is not None:
                self._counts["cancelled"] += 1
                self._pending = None
            self._cv.notify_all()

    def close(self, wait=False, timeout=None):
        """Stop accepting work and discard pending work.

        Active work finishes in the daemon thread. The default returns
        immediately even if a model or network call is still running. Optional
        joining is intended for shutdown helpers or tests, never UI callbacks.
        Returns whether the worker thread has exited.
        """
        with self._cv:
            self._closed = True
            self._latest = None
            if self._pending is not None:
                self._counts["cancelled"] += 1
                self._pending = None
            self._cv.notify_all()
        if wait and threading.current_thread() is not self._thread:
            self._thread.join(timeout)
        return not self._thread.is_alive()

    def wait_idle(self, timeout=None):
        """Wait for active and pending work to finish (tests/background only)."""
        end = None if timeout is None else time.monotonic() + max(0, timeout)
        with self._cv:
            while self._active is not None or self._pending is not None:
                if threading.current_thread() is self._thread:
                    raise RuntimeError("worker cannot wait for itself")
                remaining = None if end is None else end - time.monotonic()
                if remaining is not None and remaining <= 0:
                    return False
                self._cv.wait(remaining)
            return True

    def stats(self):
        """Return a thread-safe snapshot; active/pending are always 0 or 1."""
        with self._cv:
            return {**self._counts, "active": int(self._active is not None),
                    "pending": int(self._pending is not None), "closed": self._closed}

    def _run(self):
        while True:
            with self._cv:
                while self._pending is None and not self._closed:
                    self._cv.wait()
                if self._closed:
                    return
                token, fn = self._pending
                self._pending = None
                self._active = token
                self._counts["started"] += 1
            failed = False
            try:
                fn(token)
            except BaseException:
                # A bad job must not permanently disable later translations,
                # including when a third-party helper raises SystemExit.
                failed = True
                log.exception("Background job failed")
            finally:
                with self._cv:
                    self._active = None
                    self._counts["failed" if failed else "completed"] += 1
                    self._cv.notify_all()
