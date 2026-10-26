"""Tek kopya denetimi.

    python tests/test_single.py          # birim (Windows'ta süreçler arası; diğerlerinde her zaman izin)
    python tests/test_single.py --app    # uçtan uca: program açıkken ikinci açılış yeni kopya başlatmamalı
"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import single  # noqa: E402

HOLD = r"""
import sys, time; sys.path.insert(0, sys.argv[1]); import single
i = single.SingleInstance(sys.argv[2]); assert i.acquire(); print("held", flush=True)
end = time.time() + float(sys.argv[3]); shown = False
while time.time() < end:
    if i.poll_show(): shown = True; print("shown", flush=True)
    time.sleep(0.05)
"""


def unit():
    name = f"TD2Test{os.getpid()}"
    if os.name != "nt":
        assert single.SingleInstance(name).acquire() and single.SingleInstance(name).acquire()
        print("single: non-Windows passthrough ok"); return
    p = subprocess.Popen([sys.executable, "-c", HOLD, str(ROOT), name, "3"], stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "held"
    b = single.SingleInstance(name)
    assert not b.acquire(), "second copy must not acquire while the first runs"
    assert b.signal_show()
    out = p.communicate(timeout=10)[0]
    assert "shown" in out, out
    t0 = time.time()                                 # ilk kopya kapandı: artık alınabilir
    assert single.SingleInstance(name).acquire(wait=2)
    # yeniden başlatma: önceki kopya kapanana kadar bekler
    p = subprocess.Popen([sys.executable, "-c", HOLD, str(ROOT), name + "r", "1.5"], stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "held"
    t0 = time.time()
    assert single.SingleInstance(name + "r").acquire(wait=8)
    assert time.time() - t0 >= 0.5, "acquire(wait) should have waited for the holder"
    p.wait(5)
    print("single: unit ok")


def app_e2e():
    log = ROOT / "logs" / "app.log"
    start = log.stat().st_size if log.exists() else 0
    env = dict(os.environ, TD2_NO_WELCOME="1", PYTHONIOENCODING="utf-8")
    first = subprocess.Popen([sys.executable, str(ROOT / "app.py")], cwd=str(ROOT), env=env)

    def tail():
        try:
            with open(log, encoding="utf-8", errors="replace") as f: f.seek(start); return f.read()
        except OSError:
            return ""
    try:
        end = time.time() + 120
        while "UI ready" not in tail():
            assert first.poll() is None, "first copy exited"
            assert time.time() < end, "first copy did not start"
            time.sleep(1)
        t0 = time.time()
        second = subprocess.run([sys.executable, str(ROOT / "app.py")], cwd=str(ROOT), env=env, timeout=60)
        took = time.time() - t0
        assert second.returncode == 0, second.returncode
        time.sleep(2)
        txt = tail()
        assert txt.count("starting ===") == 1, "a second copy started:\n" + txt[-2000:]
        assert "Already running" in txt and "Second launch: showing" in txt, txt[-2000:]
        assert first.poll() is None, "first copy must keep running"
        print(f"single: app e2e ok (second launch exited in {took:.1f}s)")
    finally:
        first.terminate()
        try: first.wait(15)
        except subprocess.TimeoutExpired: first.kill()


if __name__ == "__main__":
    unit()
    if "--app" in sys.argv: app_e2e()
