"""Deterministic latest-request worker tests, without app imports or user data."""
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workqueue import LatestWorker


class LatestWorkerTests(unittest.TestCase):
    def setUp(self):
        self.worker = LatestWorker("test-latest-work")
        self.releases = []

    def tearDown(self):
        for event in self.releases:
            event.set()
        self.assertTrue(self.worker.close(wait=True, timeout=2))

    def blocked_job(self, entered, seen=None):
        release = threading.Event()
        self.releases.append(release)

        def run(token):
            if seen is not None:
                seen.append(token)
            entered.set()
            if not release.wait(2):
                raise RuntimeError("test did not release active job")
        return run, release

    def test_only_active_and_latest_pending_run(self):
        entered, seen = threading.Event(), []
        job, release = self.blocked_job(entered, seen)
        first = self.worker.submit(job)
        self.assertTrue(entered.wait(2))
        middle = self.worker.submit(lambda token: seen.append(token))
        latest = self.worker.submit(lambda token: seen.append(token))
        self.assertEqual(self.worker.stats()["active"], 1)
        self.assertEqual(self.worker.stats()["pending"], 1)
        self.assertEqual(seen, [first])
        self.assertFalse(self.worker.is_current(first))
        self.assertFalse(self.worker.is_current(middle))
        self.assertTrue(self.worker.is_current(latest))
        release.set()
        self.assertTrue(self.worker.wait_idle(2))
        self.assertEqual(seen, [first, latest])
        self.assertEqual(self.worker.stats()["replaced"], 1)

    def test_heavy_jobs_never_overlap(self):
        entered = threading.Event()
        lock = threading.Lock()
        counts = {"active": 0, "maximum": 0}
        release = threading.Event()
        self.releases.append(release)

        def run(token):
            with lock:
                counts["active"] += 1
                counts["maximum"] = max(counts["maximum"], counts["active"])
            entered.set()
            try:
                if not release.wait(2):
                    raise RuntimeError("test did not release heavy job")
            finally:
                with lock:
                    counts["active"] -= 1

        self.worker.submit(run)
        self.assertTrue(entered.wait(2))
        for _ in range(100):
            self.worker.submit(run)
            self.assertEqual(self.worker.stats()["pending"], 1)
        release.set()
        self.assertTrue(self.worker.wait_idle(2))
        self.assertEqual(counts, {"active": 0, "maximum": 1})
        self.assertEqual(self.worker.stats()["started"], 2)

    def test_invalidate_discards_pending_and_rejects_queued_ui_result(self):
        entered, seen = threading.Event(), []
        job, release = self.blocked_job(entered)
        active = self.worker.submit(job)
        self.assertTrue(entered.wait(2))
        pending = self.worker.submit(lambda token: seen.append(token))
        self.worker.invalidate()
        self.assertFalse(self.worker.is_current(active))
        self.assertFalse(self.worker.is_current(pending))
        self.assertEqual(self.worker.stats()["pending"], 0)
        release.set()
        self.assertTrue(self.worker.wait_idle(2))
        self.assertEqual(seen, [])
        fresh = self.worker.submit(lambda token: seen.append(token))
        self.assertGreater(fresh, pending)
        self.assertTrue(self.worker.wait_idle(2))
        self.assertTrue(self.worker.is_current(fresh))
        # This models a result already posted to the UI before stop/config change.
        self.worker.invalidate()
        self.assertFalse(self.worker.is_current(fresh))

    def test_failure_does_not_disable_later_work(self):
        def fail(token):
            raise SystemExit("third-party helper failed")
        with self.assertLogs("td2.workqueue", level="ERROR"):
            self.worker.submit(fail)
            self.assertTrue(self.worker.wait_idle(2))
        done = threading.Event()
        self.worker.submit(lambda token: done.set())
        self.assertTrue(done.wait(2))
        self.assertTrue(self.worker.wait_idle(2))
        self.assertEqual(self.worker.stats()["failed"], 1)
        self.assertEqual(self.worker.stats()["completed"], 1)

    def test_close_returns_while_active_job_is_blocked(self):
        entered, closed, pending_ran = threading.Event(), threading.Event(), threading.Event()
        job, release = self.blocked_job(entered)
        active = self.worker.submit(job)
        self.assertTrue(entered.wait(2))
        pending = self.worker.submit(lambda token: pending_ran.set())

        def close():
            self.worker.close()
            closed.set()
        caller = threading.Thread(target=close, daemon=True)
        caller.start()
        # Active work stays blocked until after close has returned; this proves
        # close does not wait on a model/network call without timing a fast CPU.
        self.assertTrue(closed.wait(1))
        self.assertFalse(release.is_set())
        self.assertFalse(self.worker.is_current(active))
        self.assertFalse(self.worker.is_current(pending))
        self.assertTrue(self.worker.stats()["closed"])
        with self.assertRaises(RuntimeError):
            self.worker.submit(lambda token: None)
        release.set()
        self.assertTrue(self.worker.close(wait=True, timeout=2))
        self.assertFalse(pending_ran.is_set())

    def test_concurrent_producers_keep_only_latest_pending(self):
        entered, start, seen = threading.Event(), threading.Event(), []
        job, release = self.blocked_job(entered)
        self.worker.submit(job)
        self.assertTrue(entered.wait(2))
        tokens, lock = [], threading.Lock()

        def produce():
            start.wait()
            local = [self.worker.submit(lambda token: seen.append(token)) for _ in range(25)]
            with lock:
                tokens.extend(local)

        producers = [threading.Thread(target=produce, daemon=True) for _ in range(8)]
        for producer in producers:
            producer.start()
        start.set()
        for producer in producers:
            producer.join(2)
            self.assertFalse(producer.is_alive())
        self.assertEqual(len(tokens), 200)
        self.assertEqual(len(set(tokens)), 200)
        self.assertTrue(self.worker.is_current(max(tokens)))
        self.assertEqual(self.worker.stats()["pending"], 1)
        release.set()
        self.assertTrue(self.worker.wait_idle(2))
        self.assertEqual(seen, [max(tokens)])

    def test_submit_validation_and_wait_idle_timeout(self):
        with self.assertRaises(TypeError):
            self.worker.submit(None)
        entered = threading.Event()
        job, release = self.blocked_job(entered)
        self.worker.submit(job)
        self.assertTrue(entered.wait(2))
        self.assertFalse(self.worker.wait_idle(0))
        release.set()
        self.assertTrue(self.worker.wait_idle(2))


if __name__ == "__main__":
    unittest.main()
