"""DirectML denemesi (Windows CI): programın kendi --dml-probe yolu ayrı süreçte çalıştırılır.
Test makinesinde ekran kartı yok (Microsoft Basic Render / WARP): DirectML sağlayıcısı listede olmalı, deneme düşmemeli,
sonuç işlemciyle aynı olmalı. Hız burada ölçülemez (gerçek ekran kartı gerekir)."""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
r = subprocess.run([sys.executable, str(ROOT / "app.py"), "--dml-probe", str(ROOT / "meta" / "bench_card.jpg")],
                   capture_output=True, text=True, timeout=600, cwd=str(ROOT))
line = next((l for l in r.stdout.splitlines() if l.startswith("DMLPROBE ")), "")
print("exit", r.returncode, "|", line or r.stdout[-500:] or r.stderr[-1500:])
res = json.loads(line[9:]) if line else {}
ok = r.returncode == 0 and "DmlExecutionProvider" in res.get("providers", []) and res.get("similarity", 0) >= 0.97
print("RESULT:", "PASS" if ok else "FAIL", "(GPU speed not measurable on CI)")
sys.exit(0 if ok else 1)
