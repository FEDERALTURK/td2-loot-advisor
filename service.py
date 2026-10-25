"""Arka plan hizmeti: oyunu algılama, oyunla birlikte başlat/durdur, oturum günlüğü, Windows ile başlatma, sistem tepsisi.

Oyunu yalnız pencere başlığı / süreç adıyla tanır (oyunun belleğine, dosyalarına ya da ağına dokunmaz).

    w = GameWatcher(on_event); w.start()   # olaylar: ("game", "started"|"stopped"), ("focus", True|False)
    log = SessionLog(path); log.begin(); log.add_scan(verdict, item); log.end()
"""
import json
import logging
import os
import sys
import threading
import time

log = logging.getLogger("td2.service")
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "TD2LootAdvisor"


# ---------------------------------------------------------------- oyun algılama
def game_running():
    try:
        import display
        return bool(display.find_game_hwnd())
    except Exception:
        return False


def game_focused():
    if os.name != "nt": return False
    try:
        import ctypes
        import display
        h = display.find_game_hwnd()
        return bool(h) and ctypes.windll.user32.GetForegroundWindow() == h
    except Exception:
        return False


class GameWatcher:
    """2 sn'de bir oyun penceresine bakar; durum değişince on_event çağrılır (arka plan iş parçacığından)."""

    def __init__(self, on_event, interval=2.0, probe=None, focus_probe=None):
        self.on_event, self.interval = on_event, interval
        self.probe, self.focus_probe = probe or game_running, focus_probe or game_focused
        self.running = self.focused = False
        self.started_at = None
        self._stop = threading.Event(); self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive(): return
        self._stop.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True, name="game-watcher"); self.thread.start()

    def stop(self):
        self._stop.set()

    def tick(self):
        r = self.probe()
        if r != self.running:
            self.running = r
            self.started_at = time.time() if r else None
            self._emit("game", "started" if r else "stopped")
        f = bool(r and self.focus_probe())
        if f != self.focused:
            self.focused = f; self._emit("focus", f)

    def _emit(self, kind, value):
        try: self.on_event(kind, value)
        except Exception: log.exception("watcher event %s", kind)

    def _loop(self):
        while not self._stop.is_set():
            try: self.tick()
            except Exception: log.exception("watcher tick")
            self._stop.wait(self.interval)


# ---------------------------------------------------------------- oturum günlüğü
class SessionLog:
    """Oyun oturumları: başlangıç/bitiş, okunan eşya sayısı, kararlar, egzotik/adlı eşyalar, build yükseltmeleri."""
    KEEP_LAST = 200

    def __init__(self, path):
        self.path = str(path)
        self.sessions, self.current = [], None
        try:
            with open(self.path, encoding="utf-8") as f: self.sessions = json.load(f).get("sessions", [])[-self.KEEP_LAST:]
        except (OSError, ValueError):
            pass

    def begin(self, now=None):
        if self.current: return self.current
        self.current = {"start": int(now or time.time()), "end": None, "scanned": 0, "keep": 0, "consider": 0,
                        "dismantle": 0, "exotic": 0, "named": 0, "upgrades": 0, "highlights": [], "menu_s": 0}
        return self.current

    def add_scan(self, verdict, item=None):
        c = self.current or self.begin()
        c["scanned"] += 1
        v = (verdict or "").upper()
        if v in ("KEEP", "CONSIDER", "DISMANTLE"): c[v.lower()] += 1
        rar = " ".join(item.get("rarity") or []) if isinstance(item, dict) else ""
        name = (item or {}).get("name") if isinstance(item, dict) else None
        for k, tag in (("exotic", "EXOTIC"), ("named", "NAMED")):
            if tag in rar.upper(): c[k] += 1
        if name and v == "KEEP" and ("EXOTIC" in rar.upper() or "NAMED" in rar.upper()):
            c["highlights"] = (c["highlights"] + [name])[-10:]

    def add_upgrade(self, name):
        c = self.current or self.begin()
        c["upgrades"] += 1
        if name: c["highlights"] = (c["highlights"] + ["⬆ " + name])[-10:]

    def add_menu_time(self, seconds):
        if self.current: self.current["menu_s"] += int(seconds)

    def end(self, now=None):
        c, self.current = self.current, None
        if not c: return None
        c["end"] = int(now or time.time())
        if c["scanned"] or c["end"] - c["start"] >= 300:          # 5 dk'dan kısa ve boş oturumları saklama
            self.sessions = (self.sessions + [c])[-self.KEEP_LAST:]
            self.save()
        return c

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"v": 1, "sessions": self.sessions}, f, ensure_ascii=False, indent=0)
        os.replace(tmp, self.path)

    def stats(self):
        c = self.current or {}
        return {k: c.get(k, 0) for k in ("scanned", "keep", "consider", "dismantle", "exotic", "named", "upgrades")} | \
               {"start": c.get("start"), "active": bool(self.current)}

    def totals(self, days=7, now=None):
        since = (now or time.time()) - days * 86400
        out = {"sessions": 0, "seconds": 0, "scanned": 0, "keep": 0, "dismantle": 0, "exotic": 0, "named": 0}
        for s in self.sessions:
            if (s.get("end") or 0) < since: continue
            out["sessions"] += 1; out["seconds"] += (s["end"] - s["start"])
            for k in ("scanned", "keep", "dismantle", "exotic", "named"): out[k] += s.get(k, 0)
        return out


# ---------------------------------------------------------------- Windows ile başlat (kullanıcı düzeyi, yönetici gerekmez)
def autostart_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --tray'
    exe = sys.executable.replace("python.exe", "pythonw.exe")
    return f'"{exe}" "{os.path.abspath(sys.argv[0])}" --tray'


def autostart_get():
    if os.name != "nt": return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            v, _ = winreg.QueryValueEx(k, RUN_NAME)
            return bool(v)
    except OSError:
        return False


def autostart_set(on, command=None):
    if os.name != "nt": return False
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as k:
        if on: winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, command or autostart_command())
        else:
            try: winreg.DeleteValue(k, RUN_NAME)
            except FileNotFoundError: pass
    return autostart_get() == bool(on)


# ---------------------------------------------------------------- sistem tepsisi (pystray varsa)
class Tray:
    """Tepsi simgesi. pystray yoksa available=False; program normal pencereyle çalışmaya devam eder."""

    def __init__(self, title, image, items):
        """items: [(etiket, işlev) | None (ayraç)]; işlevler tepsi iş parçacığından çağrılır."""
        self.icon = None
        try:
            import pystray
        except Exception:
            self.available = False; return
        self.available = True
        menu = []
        for i, it in enumerate(items):
            if it is None: menu.append(pystray.Menu.SEPARATOR); continue
            label, fn = it
            menu.append(pystray.MenuItem(label, (lambda f: (lambda icon, item: f()))(fn), default=(i == 0)))
        self.icon = pystray.Icon("td2-loot-advisor", image, title, pystray.Menu(*menu))

    def start(self):
        if not self.icon: return
        if sys.platform == "win32":                  # kendi (daemon) iş parçacığında: program kapanınca beklemez
            threading.Thread(target=self.icon.run, daemon=True, name="tray").start()
        else:
            self.icon.run_detached()

    def notify(self, text, title=None):
        try:
            if self.icon and getattr(self.icon, "HAS_NOTIFICATION", True): self.icon.notify(text, title)
        except Exception:
            pass

    def set_title(self, title):
        if self.icon: self.icon.title = title[:120]

    def stop(self):
        try:
            if self.icon: self.icon.stop()
        except Exception:
            pass
