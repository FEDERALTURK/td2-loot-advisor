"""Yerel API: belirteç, Origin, WebSocket olay/komut, Stream Deck uçları, OBS sayfası.   python tests/test_localapi.py"""
import base64, json, os, shutil, socket, struct, subprocess, sys, time, urllib.request, urllib.error
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import localapi  # noqa: E402

fails = 0
def ok(c, m):
    global fails
    print(("OK   " if c else "FAIL ") + m)
    if not c: fails += 1

calls = []
state = {"running": False, "game": "menu", "session": {"scanned": 3, "keep": 1, "dismantle": 2}}
def cmd(c, args):
    calls.append(c)
    if c in ("start", "stop", "toggle"): state["running"] = {"start": True, "stop": False, "toggle": not state["running"]}[c]
    return {"running": state["running"]}

port = 18766 + os.getpid() % 500
api = localapi.LocalAPI(lambda: dict(state), cmd, port=port)
api.start()
B = f"http://127.0.0.1:{port}"
def get(path, tok=True, hdr=None):
    sep = "&" if "?" in path else "?"
    req = urllib.request.Request(B + path + (f"{sep}t={api.token}" if tok else ""), headers=hdr or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as r: return r.status, r.read().decode(), r.headers
    except urllib.error.HTTPError as e: return e.code, e.read().decode(), e.headers

ok(get("/api/state", tok=False)[0] == 403, "belirteçsiz istek reddedildi")
ok(get("/api/state?t=wrong", tok=False)[0] == 403, "yanlış belirteç reddedildi")
s, body, _ = get("/api/state"); ok(s == 200 and json.loads(body)["game"] == "menu", "durum JSON")
ok(get("/api/state", tok=False, hdr={"Authorization": "Bearer " + api.token})[0] == 200, "Authorization başlığıyla da çalışır")
s, body, h = get("/overlay"); ok(s == 200 and "WebSocket" in body and "Content-Security-Policy" in h, "OBS sayfası + CSP")
s, body, _ = get("/deck/start"); ok(json.loads(body)["ok"] and state["running"], "Stream Deck: başlat")
s, body, _ = get("/deck/toggle"); ok(json.loads(body)["running"] is False, "Stream Deck: aç/kapa")
s, body, _ = get("/deck/format_c"); ok(json.loads(body)["ok"] is False, "listede olmayan komut reddedildi")

def ws(origin=None, tok=None):
    sk = socket.create_connection(("127.0.0.1", port), timeout=5)
    key = base64.b64encode(os.urandom(16)).decode()
    hdr = f"GET /ws?t={tok or api.token} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
    if origin: hdr += f"Origin: {origin}\r\n"
    sk.sendall((hdr + "\r\n").encode())
    resp = b""
    while b"\r\n\r\n" not in resp: resp += sk.recv(1)
    return sk, resp.decode()
def send(sk, obj):
    b = json.dumps(obj).encode(); m = os.urandom(4)
    sk.sendall(bytes([0x81, 0x80 | len(b)]) + m + bytes(x ^ m[i % 4] for i, x in enumerate(b)))
def recv(sk):
    h = sk.recv(2); n = h[1] & 0x7F
    if n == 126: n = struct.unpack(">H", sk.recv(2))[0]
    d = b""
    while len(d) < n: d += sk.recv(n - len(d))
    return json.loads(d)

sk, resp = ws(origin="https://evil.example")
ok(" 403 " in resp.split("\r\n")[0], "başka web sitesinden WebSocket reddedildi (Origin)")
sk, resp = ws(tok="nope"); ok(" 403 " in resp.split("\r\n")[0], "belirteçsiz WebSocket reddedildi")
sk, resp = ws(origin=f"http://127.0.0.1:{port}")
ok(" 101 " in resp.split("\r\n")[0], "aynı kaynaktan (OBS sayfası) WebSocket kabul")
hello = recv(sk); ok(hello["type"] == "hello" and hello["state"]["game"] == "menu", "hello + anlık durum")
n = api.broadcast({"type": "scan", "verdict": "KEEP", "item": {"name": "Ninjabike"}})
e = recv(sk); ok(n == 1 and e["type"] == "scan" and e["item"]["name"] == "Ninjabike", "tarama olayı yayınlandı")
send(sk, {"cmd": "start", "id": 7}); r = recv(sk); ok(r["type"] == "result" and r["id"] == 7 and r["ok"], "WS komutu: start")
send(sk, {"cmd": "rm -rf"}); r = recv(sk); ok(not r["ok"], "WS: bilinmeyen komut reddedildi")
for i in range(45): send(sk, {"cmd": "get_state"})
got = [recv(sk) for _ in range(45)]
ok(any(g.get("error") == "rate limited" for g in got), "WS mesaj sınırı")
sk.close()

# node'un yerleşik WebSocket istemcisiyle birlikte çalışabilirlik (varsa)
node = shutil.which("node")
if node:
    js = f"""const w=new WebSocket("ws://127.0.0.1:{port}/ws?t={api.token}");let n=0;
w.onmessage=m=>{{const e=JSON.parse(m.data);if(e.type==="hello")w.send(JSON.stringify({{cmd:"get_state",id:1}}));
else if(e.type==="result"){{const ok=e.ok&&e.state.game==="menu";console.log("NODEWS "+(ok?"ok":"bad"));w.close();process.exit(ok?0:1);}}}};
w.onerror=e=>{{console.log("NODEWS err");process.exit(1)}};setTimeout(()=>process.exit(2),5000);"""
    try:
        node_run = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=30)
        out = node_run.stdout
        if node_run.returncode:
            print("NODEWS stderr:", node_run.stderr[-1000:])
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ""
        if isinstance(out, bytes): out = out.decode("utf-8", "replace")
        print("NODEWS timeout after 30s:", (e.stderr or "")[-1000:])
    ok("NODEWS ok" in out, "standart WebSocket istemcisi (node) bağlandı ve komut çalıştı")

api.allow_control = False
s, body, _ = get("/deck/start"); ok(json.loads(body)["error"] == "control disabled", "kontrol kapalıyken komut yok")
api.stop()
try: urllib.request.urlopen(B + "/api/state?t=" + api.token, timeout=2); ok(False, "durdurma")
except Exception: ok(True, "durdurulunca port kapandı")
print("RESULT:", "PASS" if not fails else f"FAIL ({fails})"); sys.exit(1 if fails else 0)
