"""Discord Zengin Durum (Rich Presence): "TD2 Loot Advisor — Envanter düzenliyor · 23 eşya".

Discord masaüstü uygulamasının resmi yerel IPC kanalını kullanır (Windows: \\\\.\\pipe\\discord-ipc-N,
Linux/macOS: discord-ipc-N soketi). Oyuna değil Discord'a konuşur; Discord kapalıysa sessizce bekler.

    p = Presence(client_id); p.update(details="...", state="...", start=ts); p.clear(); p.close()
"""
import json
import logging
import os
import struct
import sys
import threading
import time
import uuid

log = logging.getLogger("td2.presence")
MIN_INTERVAL = 15.0          # Discord sınırı: 20 sn'de 5 güncelleme — güvenli tarafta kal
OP_HANDSHAKE, OP_FRAME, OP_CLOSE = 0, 1, 2


def _paths():
    if sys.platform == "win32":
        return [rf"\\?\pipe\discord-ipc-{i}" for i in range(10)]
    base = os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("TMPDIR") or os.environ.get("TMP") or "/tmp"
    out = []
    for sub in ("", "app/com.discordapp.Discord", "snap.discord", ".flatpak/com.discordapp.Discord/xdg-run"):
        for i in range(10): out.append(os.path.join(base, sub, f"discord-ipc-{i}"))
    return out


class _Conn:
    def __init__(self):
        self.f = self.sock = None
        for p in _paths():
            try:
                if sys.platform == "win32":
                    self.f = open(p, "r+b", buffering=0); break
                import socket
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(3); s.connect(p)
                self.sock = s; break
            except OSError:
                continue
        if not (self.f or self.sock): raise ConnectionError("discord not running")

    def _write(self, b):
        if self.f: self.f.write(b); self.f.flush()
        else: self.sock.sendall(b)

    def _read(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.f.read(n - len(buf)) if self.f else self.sock.recv(n - len(buf))
            if not chunk: raise ConnectionError("closed")
            buf += chunk
        return buf

    def send(self, op, obj):
        data = json.dumps(obj).encode()
        self._write(struct.pack("<II", op, len(data)) + data)

    def recv(self):
        op, n = struct.unpack("<II", self._read(8))
        return op, json.loads(self._read(n) or b"{}")

    def close(self):
        try:
            if self.f: self.f.close()
            if self.sock: self.sock.close()
        except OSError:
            pass


class Presence:
    def __init__(self, client_id, buttons=None):
        self.client_id = str(client_id or "")
        self.buttons = buttons or []
        self.conn, self.last_sent, self.pending, self.current = None, 0.0, None, None
        self.lock = threading.Lock()
        self.ok = False

    def _connect(self):
        if self.conn: return True
        if not self.client_id.isdigit(): return False
        try:
            c = _Conn()
            c.send(OP_HANDSHAKE, {"v": 1, "client_id": self.client_id})
            op, msg = c.recv()
            if op != OP_FRAME or msg.get("evt") != "READY":
                c.close(); log.info("Discord RPC handshake refused: %s", msg.get("message") or msg); return False
            self.conn, self.ok = c, True
            log.info("Discord RPC connected (%s)", (msg.get("data") or {}).get("user", {}).get("username", "?"))
            return True
        except (OSError, ConnectionError, ValueError, struct.error):
            return False

    def _send_activity(self, activity):
        if not self._connect(): return False
        try:
            self.conn.send(OP_FRAME, {"cmd": "SET_ACTIVITY", "args": {"pid": os.getpid(), "activity": activity},
                                      "nonce": str(uuid.uuid4())})
            op, msg = self.conn.recv()
            if msg.get("evt") == "ERROR": log.info("Discord RPC error: %s", msg.get("data")); return False
            self.last_sent = time.time()
            return True
        except (OSError, ConnectionError, ValueError, struct.error):
            self.conn.close(); self.conn, self.ok = None, False
            return False

    def update(self, details, state=None, start=None, large_text=None, small=None, force=False):
        """Etkinliği ayarla; sık çağrılabilir — Discord'a en çok MIN_INTERVAL'de bir gider."""
        act = {"details": str(details)[:128], "assets": {"large_image": "logo", "large_text": (large_text or "TD2 Loot Advisor")[:128]}}
        if state: act["state"] = str(state)[:128]
        if start: act["timestamps"] = {"start": int(start)}
        if small: act["assets"].update(small_image=small[0], small_text=str(small[1])[:128])
        if self.buttons: act["buttons"] = [{"label": b[0][:32], "url": b[1]} for b in self.buttons[:2]]
        with self.lock:
            if act == self.current and not force: return True
            if not force and time.time() - self.last_sent < MIN_INTERVAL:
                self.pending = act; return True
            self.pending = None
            if self._send_activity(act): self.current = act; return True
            return False

    def flush(self):
        """Bekleyen güncellemeyi gönder (zamanlayıcıdan düzenli çağrılır)."""
        with self.lock:
            if self.pending and time.time() - self.last_sent >= MIN_INTERVAL:
                act, self.pending = self.pending, None
                if self._send_activity(act): self.current = act

    def clear(self):
        with self.lock:
            self.pending, self.current = None, None
            if self.conn: self._send_activity(None)

    def close(self):
        self.clear()
        with self.lock:
            if self.conn:
                try: self.conn.send(OP_CLOSE, {})
                except OSError: pass
                self.conn.close(); self.conn = None
