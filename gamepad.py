"""Kumanda tuşuyla "şimdi çevir": XInput durumu yalnız OKUNUR (oyuna hiçbir girdi gönderilmez).

Canlı çeviri açıkken saniyede 30 kez kumanda durumuna bakılır (ihmal edilebilir yük); seçilen tuş bileşimi birlikte
basılınca bir kez tetiklenir. Xbox ve XInput uyumlu kumandalar (Windows 10 / 11).
"""
import ctypes
import os
import threading

BUTTONS = {"back": 0x0020, "start": 0x0010, "lb": 0x0100, "rb": 0x0200, "ls": 0x0040, "rs": 0x0080,
           "a": 0x1000, "b": 0x2000, "x": 0x4000, "y": 0x8000, "up": 0x0001, "down": 0x0002, "left": 0x0004, "right": 0x0008}
COMBOS = ("off", "back+rb", "back+lb", "ls+rs", "back+y", "lb+rb+y")


def mask_of(combo):
    m = 0
    for k in str(combo or "").lower().split("+"):
        if k in BUTTONS: m |= BUTTONS[k]
    return m


class _GAMEPAD(ctypes.Structure):
    _fields_ = [("wButtons", ctypes.c_ushort), ("bLeftTrigger", ctypes.c_ubyte), ("bRightTrigger", ctypes.c_ubyte),
                ("sThumbLX", ctypes.c_short), ("sThumbLY", ctypes.c_short), ("sThumbRX", ctypes.c_short), ("sThumbRY", ctypes.c_short)]


class _STATE(ctypes.Structure):
    _fields_ = [("dwPacketNumber", ctypes.c_uint), ("Gamepad", _GAMEPAD)]


def _xinput():
    if os.name != "nt": return None
    for dll in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try:
            x = ctypes.WinDLL(dll)
            x.XInputGetState.argtypes = (ctypes.c_uint, ctypes.POINTER(_STATE)); x.XInputGetState.restype = ctypes.c_uint
            return x
        except OSError:
            continue
    return None


class ComboWatcher:
    """Tuş bileşimi basılınca callback() (arka plan iş parçacığından). read_buttons: test için değiştirilebilir."""

    def __init__(self, combo, callback, read_buttons=None, hz=30):
        self.mask = mask_of(combo); self.callback = callback; self.hz = hz
        self._x = None if read_buttons else _xinput()
        self.read_buttons = read_buttons or self._read
        self.stop_ev = threading.Event(); self.thread = None; self.down = False

    @property
    def available(self): return bool(self.mask) and (self._x is not None or self.read_buttons != self._read)

    def _read(self):
        st = _STATE(); b = 0
        for i in range(4):                                        # bağlı ilk kumandalar
            if self._x.XInputGetState(i, ctypes.byref(st)) == 0: b |= st.Gamepad.wButtons
        return b

    def poll(self):
        b = self.read_buttons()
        pressed = (b & self.mask) == self.mask
        if pressed and not self.down:
            self.down = True; self.callback(); return True
        if not pressed: self.down = False
        return False

    def start(self):
        if not self.available: return False
        self.stop_ev.clear()
        def run():
            idle = 0
            while not self.stop_ev.wait(1.0 / self.hz if idle < 300 else 0.5):   # kumanda yoksa yavaşla
                try:
                    b = self.read_buttons()
                    idle = idle + 1 if b == 0 else 0
                    pressed = (b & self.mask) == self.mask
                    if pressed and not self.down: self.down = True; self.callback()
                    elif not pressed: self.down = False
                except Exception:
                    pass
        self.thread = threading.Thread(target=run, daemon=True, name="gamepad"); self.thread.start()
        return True

    def stop(self): self.stop_ev.set()
