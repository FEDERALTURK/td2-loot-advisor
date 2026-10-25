"""Windows CI: programı açar, PC senkron aracını çalıştırır (ekran görüntüsü iş akışından alınır)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import app
app.messagebox.askyesno = lambda *a, **k: False          # açılıştaki "yeni PC" sorusu testi bekletmesin
a = app.App()
a.root.after(3000, a.run_sync)
a.root.after(45000, a.root.destroy)
a.root.mainloop()
