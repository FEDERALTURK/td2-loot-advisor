"""Sistem tepsisi (saatin yanı) ve Windows bildirimleri.

Panel penceresi kapatılınca (ayar açıksa) tepsiye iner; arka planda birkaç dakikada bir yeni rapor, çeviri önerisi,
görev, hesap ve lisans etkinleştirmesi olup olmadığına bakar ve varsa Windows bildirimi gösterir.
pystray yoksa (ör. kaynak koddan, paket kurulmadan) sessizce devre dışı kalır; panel normal çalışır.
"""
import queue
import threading

try:
    import pystray
    from PIL import Image
except Exception:                        # paket yok: tepsi yok
    pystray = None


def summarize(ev, new_reports=0):
    """Olay sayılarından tek satırlık bildirim metni (boşsa '')."""
    ev = ev or {}
    parts = []
    if new_reports: parts.append(f"{new_reports} yeni rapor")
    for k, name in (("suggestions", "çeviri önerisi"), ("redeems", "lisans etkinleştirmesi"), ("accounts", "yeni hesap"),
                    ("task_reports", "görev bildirimi")):
        n = ev.get(k) or 0
        if n: parts.append(f"{n} {name}")
    return ", ".join(parts)


class Tray:
    def __init__(self, root, icon_path, title, actions):
        """actions: [(etiket, işlev), ...] — işlevler Tk iş parçacığında çalışır; ilk eylem varsayılan (çift tık)."""
        self.root, self.icon, self.q = root, None, queue.Queue()
        self._stopped = False
        self.available = pystray is not None
        if not self.available: return
        try: img = Image.open(icon_path)
        except Exception: img = Image.new("RGBA", (64, 64), (255, 106, 0, 255))
        items = [pystray.MenuItem(lbl, self._cb(fn), default=(i == 0)) for i, (lbl, fn) in enumerate(actions)]
        self.icon = pystray.Icon("td2panel", img, title, menu=pystray.Menu(*items))
        threading.Thread(target=self.icon.run, daemon=True).start()
        self._pump()

    def _cb(self, fn):
        return lambda icon, item: self.q.put(fn)

    def _pump(self):
        if self._stopped:
            return
        try:
            while True: self.q.get_nowait()()
        except queue.Empty:
            pass
        try:
            self.root.after(250, self._pump)
        except Exception:
            self._stopped = True

    def notify(self, text, title="TD2 Rapor Paneli"):
        if self.icon is not None and text:
            try: self.icon.notify(text, title)
            except Exception: pass

    def stop(self):
        self._stopped = True
        if self.icon is not None:
            try: self.icon.stop()
            except Exception: pass

