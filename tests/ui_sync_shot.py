"""Windows CI: programı açar, PC senkron aracını çalıştırır (ekran görüntüsü iş akışından alınır)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import app
app.messagebox.askyesno = lambda *a, **k: False          # açılıştaki "yeni PC" sorusu testi bekletmesin
a = app.App()
a.root.after(3000, lambda: a.banner.chips[0][2]())          # üst banttaki "PC senkron" rozeti
def press_apply():
    b = getattr(a, "_sync_apply_btn", None)
    if b and str(b["state"]) == "normal":
        b.invoke(); print("APPLY PRESSED", a.cfg["settings"].get("sync_fp"), a.cfg["settings"].get("sync_time"), flush=True)
    else:
        a.root.after(2000, press_apply)
a.root.after(30000, press_apply)
a.root.after(45000, a.root.destroy)
a.root.mainloop()
