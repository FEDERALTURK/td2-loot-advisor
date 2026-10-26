"""Tek kopya: program ikinci kez açılırsa yeni kopya başlamaz, açık olan pencere öne getirilir.

Windows'ta adlı mutex + adlı olay (event) kullanılır; ağ ya da dosya gerekmez. Başka sistemlerde her zaman izin verir.

    inst = SingleInstance()
    if not inst.acquire(wait=0):     # zaten açık
        inst.signal_show(); sys.exit(0)
    ...
    if inst.poll_show(): pencereyi_öne_getir()
"""
import os
import time

ERROR_ALREADY_EXISTS = 183
WAIT_OBJECT_0 = 0


class SingleInstance:
    def __init__(self, name="TD2LootAdvisor"):
        self.name = name
        self.mutex = self.event = None
        self._k = None
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            k = ctypes.WinDLL("kernel32", use_last_error=True)
            k.CreateMutexW.restype = wintypes.HANDLE
            k.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
            k.CreateEventW.restype = wintypes.HANDLE
            k.CreateEventW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR)
            k.SetEvent.argtypes = (wintypes.HANDLE,)
            k.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
            k.WaitForSingleObject.restype = wintypes.DWORD
            k.CloseHandle.argtypes = (wintypes.HANDLE,)
            self._k, self._ct = k, ctypes

    def _open_event(self):
        if not self.event:            # otomatik sıfırlanan olay: her sinyal bir kez yakalanır
            self.event = self._k.CreateEventW(None, False, False, f"Local\\{self.name}.show")
        return self.event

    def acquire(self, wait=0.0):
        """Bu kopya tek kopya olabildiyse True. wait>0: önceki kopyanın kapanmasını bu kadar saniye bekle (yeniden başlatma)."""
        if not self._k: return True
        end = time.time() + max(0.0, wait)
        while True:
            h = self._k.CreateMutexW(None, False, f"Local\\{self.name}.instance")
            err = self._ct.get_last_error()
            if h and err != ERROR_ALREADY_EXISTS:
                self.mutex = h
                self._open_event()
                return True
            if h: self._k.CloseHandle(h)
            if time.time() >= end: return False
            time.sleep(0.25)

    def signal_show(self):
        """Açık olan kopyaya 'pencereni göster' de."""
        if not self._k: return False
        try: self._ct.windll.user32.AllowSetForegroundWindow(-1)    # ASFW_ANY: açık kopya öne gelebilsin
        except Exception: pass
        e = self._open_event()
        return bool(e and self._k.SetEvent(e))

    def poll_show(self):
        """Başka bir açılma denemesi pencerenin gösterilmesini istediyse True (beklemeden bakar)."""
        if not self._k or not self.event: return False
        return self._k.WaitForSingleObject(self.event, 0) == WAIT_OBJECT_0
