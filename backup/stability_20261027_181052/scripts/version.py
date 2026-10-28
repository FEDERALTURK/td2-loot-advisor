"""app.py'deki APP_VERSION'u yazdırır (build_installer.bat kullanır)."""
import re
from pathlib import Path
m = re.search(r'APP_VERSION = "([^"]+)"', (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8"))
print(m.group(1) if m else "0.0")
