"""Windows CI: açılıştaki güncelleme merkezi. Eski kütüphane + eski program sürümü + güncellenmiş oyun taklit edilir,
pencere açılır, "Yükle"ye basılır. Program güncellemesi gerçekten indirilmez (do_update yalnız kayda yazar)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import app, gameinfo
app.messagebox.askyesno = lambda *a, **k: False
app.APP_VERSION = "5.0.0"                                         # yayındaki sürüm daha yeni görünsün
app.GAME.data["version"] = "2000-01-01.1"                          # yerel kütüphane eski görünsün
for n in ("Fafnir", "Iron Will", "Loaded for Bear"):
    if n in app.GAME.data["exotics"]: app.GAME.data["exotics"].remove(n)
app.GAME.data["items"].pop("Iron Will", None)
gameinfo.current = lambda: {"path": "C:/Games/TheDivision2.exe", "version": "1.42.0.0", "mtime": 2, "size": 9, "source": "test"}
app.App.do_update = lambda self: app.log.info("DO_UPDATE CALLED %s", self.upd_info.get("version"))
a = app.App()
a.cfg["settings"]["game_install"] = {"path": "C:/Games/TheDivision2.exe", "version": "1.41.0.0", "mtime": 1, "size": 9}
def press():
    f = getattr(a, "_uc_install", None)
    if f: f(); print("INSTALL PRESSED", flush=True)
    else: a.root.after(1500, press)
a.root.after(26000, press)
a.root.after(40000, a.root.destroy)
a.root.mainloop()
print("library now:", app.GAME.data.get("version"))
