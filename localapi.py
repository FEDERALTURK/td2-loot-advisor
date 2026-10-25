"""Yerel API: WebSocket + HTTP — telefon, OBS (tarayıcı kaynağı) ve Stream Deck için.

    api = LocalAPI(state_fn, command_fn, port=8766); api.start()
    api.broadcast({"type": "scan", ...})

Uç noktalar (hepsi ?t=<belirteç> ister):
    GET  /api/state            anlık durum (JSON)
    GET  /overlay              OBS tarayıcı kaynağı: şeffaf arka planlı canlı karar kartı
    GET  /deck/<komut>         Stream Deck / kısayol: start | stop | toggle | scan  → {"ok": true}
    WS   /ws                   canlı olaylar: hello, scan, game, session, build;  istemci → {"cmd": "..."}

Güvenlik
  - Varsayılan yalnız bu bilgisayar (127.0.0.1). Ev ağı isteğe bağlı açılır.
  - Her istek rastgele belirteç ister (sabit süreli karşılaştırma).
  - Tarayıcıdan gelen WebSocket isteklerinde Origin bu sunucu değilse reddedilir (başka bir web sitesi bağlanamaz).
  - Komutlar yalnız listedekiler; istemci başına mesaj sınırı; çerçeve boyutu sınırlı.
  - Oyuna hiçbir girdi göndermez — yalnız programın kendi taramasını başlatır / durdurur.
"""
import base64
import hashlib
import hmac
import json
import logging
import secrets
import socket
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

log = logging.getLogger("td2.api")
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
COMMANDS = ("get_state", "start", "stop", "toggle", "scan")
MAX_FRAME = 64 * 1024
MAX_MSGS_PER_10S = 40

OVERLAY = r"""<!doctype html><html><head><meta charset="utf-8"><title>TD2 overlay</title>
<style>
html,body{margin:0;background:transparent;font-family:"Segoe UI",system-ui,sans-serif;color:#fff;overflow:hidden}
#c{display:inline-block;min-width:340px;margin:12px;padding:14px 18px;border-radius:12px;background:rgba(13,15,18,.82);
   border-left:6px solid #555;transition:opacity .4s,transform .4s;opacity:0;transform:translateY(8px)}
#c.on{opacity:1;transform:none}
#v{font-size:26px;font-weight:800;letter-spacing:.06em}#n{font-size:17px;font-weight:600;margin-top:2px}
#m{font-size:13px;color:#b9bec7;margin-top:4px}#s{font-size:12px;color:#8b9098;margin-top:8px}
.KEEP{border-color:#2fbf71!important}.KEEP #v{color:#2fbf71}.CONSIDER{border-color:#e0b03a!important}.CONSIDER #v{color:#e0b03a}
.DISMANTLE{border-color:#e5484d!important}.DISMANTLE #v{color:#e5484d}.REVIEW{border-color:#5b8def!important}.REVIEW #v{color:#5b8def}
</style></head><body><div id="c"><div id="v"></div><div id="n"></div><div id="m"></div><div id="s"></div></div>
<script>
const P=new URLSearchParams(location.search),HIDE=+(P.get("hide")||12)*1000;let tm;
function show(e){const c=document.getElementById("c");c.className="on "+(e.verdict||"");
 document.getElementById("v").textContent=e.verdict_label||e.verdict||"";document.getElementById("n").textContent=e.item?.name||"";
 document.getElementById("m").textContent=[e.item?.slot,e.best].filter(Boolean).join(" · ");
 clearTimeout(tm);if(HIDE>0)tm=setTimeout(()=>c.className="",HIDE)}
function sess(s){if(s)document.getElementById("s").textContent=`${s.label||""} ${s.scanned??0} · ★ ${s.keep??0} · ⚙ ${s.dismantle??0}`}
function go(){const w=new WebSocket(`ws://${location.host}/ws?t=${encodeURIComponent(P.get("t")||"")}`);
 w.onmessage=m=>{const e=JSON.parse(m.data);if(e.type==="scan")show(e);if(e.session)sess(e.session);if(e.type==="hello"&&e.state?.last)sess(e.state.session)};
 w.onclose=()=>setTimeout(go,2000)}
go();
</script></body></html>"""


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):          # kopan bağlantılar konsolu kirletmesin
        log.debug("api connection error from %s", client_address, exc_info=True)


def _accept(key):
    return base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()


def _frame(payload, opcode=0x1):
    b = payload.encode() if isinstance(payload, str) else payload
    n = len(b)
    head = bytes([0x80 | opcode]) + (bytes([n]) if n < 126 else bytes([126]) + struct.pack(">H", n) if n < 65536
                                       else bytes([127]) + struct.pack(">Q", n))
    return head + b


class _Client:
    def __init__(self, sock):
        self.sock, self.lock, self.alive = sock, threading.Lock(), True
        self.times = []

    def send(self, obj):
        if not self.alive: return
        try:
            with self.lock: self.sock.sendall(_frame(json.dumps(obj, ensure_ascii=False)))
        except OSError:
            self.alive = False

    def recv_frame(self):
        def need(n):
            buf = b""
            while len(buf) < n:
                chunk = self.sock.recv(n - len(buf))
                if not chunk: raise ConnectionError
                buf += chunk
            return buf
        b1, b2 = need(2)
        op, masked, n = b1 & 0x0F, b2 & 0x80, b2 & 0x7F
        if n == 126: n = struct.unpack(">H", need(2))[0]
        elif n == 127: n = struct.unpack(">Q", need(8))[0]
        if n > MAX_FRAME or not masked: raise ConnectionError        # istemci çerçeveleri maskeli olmak zorunda
        mask = need(4); data = bytearray(need(n))
        for i in range(n): data[i] ^= mask[i % 4]
        return op, bytes(data)


class LocalAPI:
    def __init__(self, state_fn, command_fn=None, port=8766, token=None, lan=False, allow_control=True):
        self.state_fn, self.command_fn = state_fn, command_fn
        self.port, self.lan, self.allow_control = int(port), bool(lan), bool(allow_control)
        self.token = token or secrets.token_urlsafe(16)
        self.httpd = None; self.clients = []; self._lock = threading.Lock()

    # ---- adresler
    @property
    def host(self):
        if not self.lan: return "127.0.0.1"
        try:
            import companion
            return companion.lan_ip()
        except Exception:
            return "127.0.0.1"

    def url(self, path="/overlay"):
        return f"http://{self.host}:{self.port}{path}?t={self.token}"

    @property
    def ws_url(self):
        return f"ws://{self.host}:{self.port}/ws?t={self.token}"

    @property
    def running(self): return self.httpd is not None

    # ---- olaylar
    def broadcast(self, event):
        with self._lock:
            self.clients = [c for c in self.clients if c.alive]
            cl = list(self.clients)
        for c in cl: c.send(event)
        return len(cl)

    def _command(self, cmd, args=None):
        if cmd == "get_state": return {"ok": True, "state": self._state()}
        if cmd not in COMMANDS: return {"ok": False, "error": "unknown command"}
        if not self.allow_control or not self.command_fn: return {"ok": False, "error": "control disabled"}
        try:
            r = self.command_fn(cmd, args or {})
            return {"ok": True, **(r if isinstance(r, dict) else {})}
        except Exception as e:
            log.exception("api command %s", cmd); return {"ok": False, "error": str(e)}

    def _state(self):
        try: return self.state_fn() or {}
        except Exception as e:
            log.exception("api state"); return {"error": str(e)}

    # ---- sunucu
    def _handler(self):
        api = self

        class H(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, fmt, *a): log.debug("api %s - %s", self.address_string(), fmt % a)

            def _send(self, code, body, ctype="application/json; charset=utf-8"):
                data = body.encode() if isinstance(body, str) else body
                self.send_response(code)
                for k, v in (("Content-Type", ctype), ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff"),
                             ("Content-Length", str(len(data))), ("Referrer-Policy", "no-referrer")):
                    self.send_header(k, v)
                if ctype.startswith("text/html"):
                    self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; "
                                     "script-src 'unsafe-inline'; connect-src ws://" + self.headers.get("Host", "127.0.0.1"))
                self.end_headers(); self.wfile.write(data)

            def _authed(self, u):
                tok = (parse_qs(u.query).get("t") or [""])[0]
                auth = self.headers.get("Authorization", "")
                if auth.startswith("Bearer "): tok = auth[7:].strip()
                return hmac.compare_digest(tok.encode(), api.token.encode())

            def do_GET(self):
                u = urlparse(self.path)
                if not self._authed(u): return self._send(403, '{"error":"forbidden"}')
                if u.path == "/ws": return self._ws()
                if u.path == "/api/state": return self._send(200, json.dumps(api._state(), ensure_ascii=False))
                if u.path == "/overlay": return self._send(200, OVERLAY, "text/html; charset=utf-8")
                if u.path.startswith("/deck/"):
                    return self._send(200, json.dumps(api._command(u.path[6:].strip("/"), {"via": "deck"})))
                return self._send(404, '{"error":"not found"}')

            def do_POST(self):
                self._send(405, '{"error":"use GET or WebSocket"}')

            def _ws(self):
                origin = self.headers.get("Origin")
                host = self.headers.get("Host", "")
                if origin and origin not in ("null", "http://" + host, "https://" + host):
                    return self._send(403, '{"error":"origin"}')
                key = self.headers.get("Sec-WebSocket-Key", "")
                if self.headers.get("Upgrade", "").lower() != "websocket" or not key:
                    return self._send(400, '{"error":"websocket upgrade required"}')
                self.send_response(101, "Switching Protocols")
                self.send_header("Upgrade", "websocket"); self.send_header("Connection", "Upgrade")
                self.send_header("Sec-WebSocket-Accept", _accept(key)); self.end_headers()
                self.wfile.flush()
                c = _Client(self.connection)
                self.connection.settimeout(None)
                with api._lock: api.clients.append(c)
                c.send({"type": "hello", "version": 1, "commands": list(COMMANDS) if api.allow_control else ["get_state"],
                        "state": api._state()})
                try:
                    while c.alive:
                        op, data = c.recv_frame()
                        if op == 0x8: break                                   # kapat
                        if op == 0x9: c.sock.sendall(_frame(data, 0xA)); continue   # ping → pong
                        if op != 0x1: continue
                        now = time.time(); c.times = [x for x in c.times if now - x < 10] + [now]
                        if len(c.times) > MAX_MSGS_PER_10S:
                            c.send({"type": "error", "error": "rate limited"}); continue
                        try: msg = json.loads(data.decode())
                        except ValueError:
                            c.send({"type": "error", "error": "bad json"}); continue
                        res = api._command(str(msg.get("cmd", "")), msg.get("args") if isinstance(msg.get("args"), dict) else {})
                        c.send({"type": "result", "id": msg.get("id"), **res})
                except (ConnectionError, OSError, struct.error):
                    pass
                finally:
                    c.alive = False
                    try: c.sock.sendall(_frame(b"", 0x8))
                    except OSError: pass
                    self.close_connection = True
        return H

    def start(self):
        if self.httpd: return self.url()
        self.httpd = _Server(("0.0.0.0" if self.lan else "127.0.0.1", self.port), self._handler())
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        log.info("Local API on %s:%s (lan=%s)", "0.0.0.0" if self.lan else "127.0.0.1", self.port, self.lan)
        return self.url()

    def stop(self):
        if not self.httpd: return
        with self._lock:
            for c in self.clients:
                c.alive = False
                try: c.sock.shutdown(socket.SHUT_RDWR)
                except OSError: pass
            self.clients = []
        try: self.httpd.shutdown(); self.httpd.server_close()
        except Exception: pass
        self.httpd = None
