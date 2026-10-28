"""İsteğe bağlı hesap: Discord ile giriş, lisans anahtarı / davet kodu / satış anahtarı kullanma.

Program girişsiz de tam ücretsiz çalışır; hesap yalnız premium ve bulut özelliklerini açar.

Güvenlik
  - Şifre yok. Giriş tarayıcıda Discord ile yapılır; Discord dönüşü bu bilgisayardaki programa 127.0.0.1 üzerinden
    gelir (RFC 8252). Oturum için ayrıca programın ürettiği gizli "verifier" gerekir (PKCE benzeri).
  - Oturum belirteci diskte Windows DPAPI ile şifreli durur (yalnız bu Windows kullanıcısı çözebilir).
  - Cihaz kimliği: Windows MachineGuid'in özetinin özeti; ham kimlik hiçbir yere gönderilmez.
  - Premium, sunucunun imzaladığı ve bu bilgisayara bağlı yetki belgesiyle (TD2E) açılır; belge 7 gün internetsiz
    geçerlidir, program açıldıkça arka planda yenilenir.
  - Oyunun belleğine, ağ trafiğine ya da dosyalarına dokunulmaz.
"""
import base64
import hashlib
import json
import os
import secrets
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

TIMEOUT = 12
LOGIN_TIMEOUT = 300
UA = "TD2LootAdvisor-account"


def _b64u(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


# ---------------------------------------------------------------- cihaz kimliği
def _machine_guid():
    if sys.platform == "win32":
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                               winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0))
            v, _ = winreg.QueryValueEx(k, "MachineGuid"); winreg.CloseKey(k)
            if v: return str(v)
        except OSError:
            pass
    import uuid
    return "node-%012x" % uuid.getnode()


_DEVICE = None


def device_id():
    """Sunucuya giden cihaz kimliği (43 karakter, geri çevrilemez)."""
    global _DEVICE
    if _DEVICE is None:
        _DEVICE = _b64u(hashlib.sha256(("td2-device:" + _machine_guid()).encode()).digest())
    return _DEVICE


def device_pub(dev=None):
    """Yetki belgesindeki cihaz alanı (sunucuyla aynı formül)."""
    return hashlib.sha256(("td2e:" + (dev or device_id())).encode()).hexdigest()[:32]


# ---------------------------------------------------------------- DPAPI
def _dpapi(data, protect):
    if sys.platform != "win32": return data
    import ctypes
    from ctypes import wintypes

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    def blob(b):
        buf = ctypes.create_string_buffer(b, len(b))
        return BLOB(len(b), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf

    src, _k1 = blob(data); ent, _k2 = blob(b"td2-loot-advisor/account")
    out = BLOB()
    fn = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
    if not fn(ctypes.byref(src), None, ctypes.byref(ent), None, None, 0x1, ctypes.byref(out)):   # UI_FORBIDDEN
        raise OSError("DPAPI")
    try: return ctypes.string_at(out.pbData, out.cbData)
    finally: ctypes.windll.kernel32.LocalFree(out.pbData)


# ---------------------------------------------------------------- yerel dönüş sunucusu
_PAGE = """<!doctype html><meta charset="utf-8"><title>TD2 Loot Advisor</title>
<body style="background:#0f1116;color:#e7e9ee;font-family:Segoe UI,system-ui,sans-serif;display:grid;place-items:center;height:100vh;margin:0">
<div style="text-align:center"><div style="font-size:52px;color:{c}">{i}</div><h2>{t}</h2>
<p style="color:#9aa1ae">{m}</p></div>"""


class _Loopback:
    """127.0.0.1'de tek istek bekleyen küçük sunucu: /callback?state=..&grant=.."""

    def __init__(self, state):
        self.state, self.grant, self.event = state, None, threading.Event()
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass

            def do_GET(self):
                u = urlparse(self.path); q = parse_qs(u.query)
                good = u.path == "/callback" and q.get("state", [""])[0] == outer.state and q.get("grant")
                if good and not outer.event.is_set():
                    outer.grant = q["grant"][0]; outer.event.set()
                    body = _PAGE.format(c="#22c55e", i="✔", t="Giriş tamamlandı / Signed in",
                                        m="Bu sekmeyi kapatıp programa dönebilirsiniz. / You can close this tab.")
                    code = 200
                else:
                    body = _PAGE.format(c="#ef4444", i="✖", t="Geçersiz istek / Invalid request", m="")
                    code = 400
                data = body.encode()
                self.send_response(code)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.end_headers(); self.wfile.write(data)

        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.httpd.timeout = 0.5
        self.port = self.httpd.server_address[1]

    def wait(self, timeout, cancel=None):
        end = time.time() + timeout
        try:
            while time.time() < end and not self.event.is_set():
                if cancel is not None and cancel.is_set(): break
                self.httpd.handle_request()
        finally:
            self.httpd.server_close()
        return self.grant


# ---------------------------------------------------------------- hesap
class AuthError(Exception):
    def __init__(self, code, msg=""):
        super().__init__(msg or code); self.code = code


class Account:
    """Diskte: account.dat — {"v":1, "tok": DPAPI(base64), "ent": TD2E, "user": {...}, "tier", "license", "checked"}"""

    def __init__(self, path, url, opener=None):
        self.path, self.url = str(path), (url or "").rstrip("/")
        self._open = opener or urllib.request.urlopen
        self.token, self.data = None, {}
        self._load()

    # ---- depolama
    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f: d = json.load(f)
            tok = d.pop("tok", None)
            self.token = _dpapi(base64.b64decode(tok), False).decode() if tok else None
            self.data = d
        except (OSError, ValueError, UnicodeError):
            self.token, self.data = None, {}

    def _save(self):
        d = dict(self.data, v=1)
        if self.token: d["tok"] = base64.b64encode(_dpapi(self.token.encode(), True)).decode()
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(d, f)
        os.replace(tmp, self.path)

    def clear(self):
        self.token, self.data = None, {}
        try: os.remove(self.path)
        except OSError: pass

    # ---- durum
    @property
    def signed_in(self): return bool(self.token)

    @property
    def username(self): return (self.data.get("user") or {}).get("username", "")

    @property
    def entitlement(self): return self.data.get("ent") or ""

    # ---- HTTP
    def _req(self, method, path, body=None, auth=True):
        if not self.url: raise AuthError("noserver")
        h = {"Content-Type": "application/json", "User-Agent": UA}
        if auth and self.token: h["Authorization"] = "Bearer " + self.token
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers=h, method=method)
        try:
            with self._open(req, timeout=TIMEOUT) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            try: j = json.loads(e.read() or b"{}")
            except ValueError: j = {}
            raise AuthError({401: "unauthorized", 403: "forbidden", 404: "invalid", 409: "used", 410: "expired",
                             402: "payment", 429: "rate", 503: "disabled"}.get(e.code, "http"), j.get("error", str(e.code)))
        except (urllib.error.URLError, socket.timeout, OSError) as e:
            raise AuthError("offline", str(e))

    def _apply(self, j):
        self.data.update(user=j.get("account") or self.data.get("user"), tier=j.get("tier", "free"),
                         license=j.get("license"), ent=j.get("entitlement") or "", device_limit=bool(j.get("device_limit")),
                         checked=int(time.time()))
        self._save()
        return j

    # ---- akışlar
    def login(self, open_url=webbrowser.open, cancel=None, timeout=LOGIN_TIMEOUT):
        """Tarayıcıda Discord ile giriş; dönüşü yerel sunucu yakalar. Engelleyici — iş parçacığında çağırın."""
        state, verifier = _b64u(secrets.token_bytes(24)), _b64u(secrets.token_bytes(32))
        challenge = _b64u(hashlib.sha256(verifier.encode()).digest())
        lb = _Loopback(state)
        try:
            j = self._req("POST", "/v1/auth/start", {"state": state, "challenge": challenge, "port": lb.port}, auth=False)
            url = j.get("url", "")
            if not url.startswith("https://discord.com/"): raise AuthError("http", "bad url")
        except Exception:
            lb.httpd.server_close(); raise
        open_url(url)
        grant = lb.wait(timeout, cancel)
        if not grant: raise AuthError("cancelled" if cancel is not None and cancel.is_set() else "timeout")
        j = self._req("POST", "/v1/auth/token", {"state": state, "verifier": verifier, "grant": grant,
                                                 "device": device_id()}, auth=False)
        self.token = j.get("token")
        if not self.token: raise AuthError("http", "no token")
        return self._apply(j)

    def refresh(self):
        """Hesap durumunu ve yetki belgesini yenile. Oturum geçersizse yerel hesap silinir."""
        if not self.token: return None
        try:
            return self._apply(self._req("GET", "/v1/me"))
        except AuthError as e:
            if e.code == "unauthorized": self.clear()
            raise

    def redeem(self, code):
        j = self._req("POST", "/v1/license/redeem", {"code": code.strip()})
        return self._apply(j)

    def logout(self):
        try:
            if self.token: self._req("POST", "/v1/auth/logout", {})
        except AuthError:
            pass
        self.clear()

    def needs_refresh(self, max_age=6 * 3600):
        return self.signed_in and time.time() - self.data.get("checked", 0) > max_age
