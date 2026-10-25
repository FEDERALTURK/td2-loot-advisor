"""Açılış süresi: program başlatılır, kayıtta 'UI ready' görünene kadar geçen süre (sn). Windows CI için.
    python tests/startup_time.py APP_DIR"""
import subprocess, sys, time
from pathlib import Path
d = Path(sys.argv[1]).resolve(); log = d / "logs" / "app.log"
res = []
for run in range(3):
    if log.exists(): log.unlink()
    t0 = time.perf_counter()
    p = subprocess.Popen([sys.executable, str(d / "app.py")], cwd=d)
    ok = False
    while time.perf_counter() - t0 < 90:
        if log.exists() and "UI ready" in log.read_text(encoding="utf-8", errors="ignore"): ok = True; break
        time.sleep(0.05)
    res.append(round(time.perf_counter() - t0, 2) if ok else None)
    p.kill(); p.wait(); time.sleep(1)
print("STARTUP", d.name, res)
