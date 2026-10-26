"""Telefon arkadaşı: aynı Wi-Fi'deki telefondan son kararı, build durumunu ve satıcı eşleşmelerini görmek.

Yerel bir web sunucusu (yalnız okuma). Adres rastgele bir anahtar içerir; anahtarsız istekler reddedilir.
İnternete açılmaz: yalnız ev ağında çalışır (Windows ilk açılışta güvenlik duvarı izni sorabilir).

    srv = Companion(state_fn, labels, port=8765); srv.start(); srv.url  -> http://192.168.1.20:8765/?t=...
"""
import os
import hmac
import json
import logging
import secrets
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

log = logging.getLogger("td2.companion")


def lan_ip():
    """Bu bilgisayarın ev ağındaki adresi (paket göndermeden, yönlendirme tablosundan)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1)); return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


PAGE = r"""<!doctype html><html lang="__LANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>TD2 Loot Advisor</title>
<style>
:root{--bg:#0d0f12;--card:#161a20;--fg:#e8e6e3;--mut:#8b9098;--acc:#ff6d10;--keep:#2fbf71;--cons:#e0b03a;--dis:#e5484d;--rev:#5b8def}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:14px}
h1{font-size:15px;letter-spacing:.08em;color:var(--acc);margin:0 0 10px}h2{font-size:13px;color:var(--mut);letter-spacing:.04em;margin:18px 0 6px;font-weight:600}
.card{background:var(--card);border-radius:12px;padding:14px;margin-bottom:10px}
#verdict{font-size:28px;font-weight:700;padding:16px;border-radius:12px;text-align:center;color:#fff;background:#333;margin-bottom:10px}
.KEEP{background:var(--keep)!important}.CONSIDER{background:var(--cons)!important;color:#111!important}.DISMANTLE{background:var(--dis)!important}.REVIEW{background:var(--rev)!important}
.name{font-size:18px;font-weight:600}.mut{color:var(--mut);font-size:13px}
.bar{height:6px;background:#2a2f37;border-radius:3px;overflow:hidden;margin:3px 0 8px}.bar i{display:block;height:100%;background:var(--acc)}
.row{display:flex;justify-content:space-between;gap:8px}.ok{color:var(--keep)}.no{color:var(--dis)}
#stamp{color:var(--mut);font-size:12px;text-align:right}
</style></head><body>
<h1>◆ TD2 LOOT ADVISOR</h1>
<div id="verdict">…</div>
<div class="card"><div class="name" id="iname"></div><div class="mut" id="imeta"></div><div id="attrs"></div><div class="mut" id="note"></div></div>
<h2 id="h_build"></h2><div class="card" id="build"></div>
<h2 id="h_vendor"></h2><div class="card" id="vendor"></div>
<div id="stamp"></div>
<script>
const L=__LABELS__, T=new URLSearchParams(location.search).get("t");
document.getElementById("h_build").textContent=L.build; document.getElementById("h_vendor").textContent=L.vendor;
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
let last="";
async function tick(){
 try{
  const r=await fetch("api/state?t="+encodeURIComponent(T),{cache:"no-store"}); if(!r.ok) throw r.status;
  const s=await r.json(); const sig=JSON.stringify(s); if(sig===last) return; last=sig;
  const v=document.getElementById("verdict"); v.className=s.verdict||""; v.textContent=s.verdict_label||L.waiting;
  document.getElementById("iname").textContent=s.item?.name||"";
  document.getElementById("imeta").textContent=[s.item?.slot,s.item?.source,s.best].filter(Boolean).join(" · ");
  document.getElementById("attrs").innerHTML=(s.item?.attrs||[]).map(a=>`<div class="row"><span>${esc(a.name)}</span><span>${esc(a.value)}${a.q!=null?` · ${a.q}%`:""}</span></div><div class="bar"><i style="width:${a.q??0}%"></i></div>`).join("");
  document.getElementById("note").textContent=s.note||"";
  const b=s.build; document.getElementById("build").innerHTML=b?`<div class="row"><b>${esc(b.name)}</b><span>${b.completion}%</span></div><div class="bar"><i style="width:${b.completion}%"></i></div>`+
    b.slots.map(x=>`<div class="row"><span>${x.done?'<span class="ok">✔</span>':'<span class="no">✖</span>'} ${esc(x.slot)}</span><span class="mut">${esc(x.item||"—")} ${x.item?x.fit+"%":""}</span></div>`).join(""):`<span class="mut">—</span>`;
  const vh=s.vendor||[]; document.getElementById("vendor").innerHTML=vh.length?vh.map(h=>`<div class="row"><span>${esc(h.slot)}: <b>${esc(h.item)}</b></span><span class="mut">${esc(h.vendor)} · ${h.fit}%</span></div>`).join(""):`<span class="mut">${esc(L.no_vendor)}</span>`;
  document.getElementById("stamp").textContent=s.time||"";
 }catch(e){document.getElementById("stamp").textContent=L.offline;}
}
tick(); setInterval(tick,1500);
</script></body></html>"""


class Companion:
    def __init__(self, state_fn, labels=None, port=8765, token=None, lang="en"):
        self.state_fn, self.labels, self.lang = state_fn, labels or {}, lang
        self.port, self.token = int(port), token or secrets.token_urlsafe(12)
        self.httpd = self.thread = None

    @property
    def running(self):
        return self.httpd is not None

    @property
    def url(self):
        return f"http://{lan_ip()}:{self.port}/?t={self.token}"

    def _handler(self):
        comp = self

        class H(BaseHTTPRequestHandler):
            timeout = 15                       # yarım bırakılan bağlantılar iş parçacığı tüketmesin

            def log_message(self, fmt, *a):
                log.debug("companion %s - %s", self.address_string(), fmt % a)

            def _send(self, code, body, ctype):
                data = body.encode("utf-8") if isinstance(body, str) else body
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers(); self.wfile.write(data)

            def do_GET(self):
                u = urlparse(self.path)
                tok = (parse_qs(u.query).get("t") or [""])[0]
                if not hmac.compare_digest(tok.encode(), comp.token.encode()):
                    return self._send(403, "forbidden", "text/plain; charset=utf-8")
                if u.path in ("/", "/index.html"):
                    page = PAGE.replace("__LABELS__", json.dumps(comp.labels, ensure_ascii=False)).replace("__LANG__", comp.lang)
                    return self._send(200, page, "text/html; charset=utf-8")
                if u.path == "/api/state":
                    try: st = comp.state_fn() or {}
                    except Exception as e:
                        log.exception("companion state failed"); st = {"error": str(e)}
                    return self._send(200, json.dumps(st, ensure_ascii=False), "application/json; charset=utf-8")
                return self._send(404, "not found", "text/plain; charset=utf-8")

            def do_POST(self):
                self._send(405, "read only", "text/plain; charset=utf-8")
        return H

    def start(self):
        if self.httpd: return self.url
        class _S(ThreadingHTTPServer):
            daemon_threads = True
            allow_reuse_address = os.name != "nt"          # Windows'ta başka süreç aynı portu çalamasın
        self.httpd = _S(("0.0.0.0", self.port), self._handler())
        self.httpd.daemon_threads = True
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        log.info("Companion on port %s", self.port)
        return self.url

    def stop(self):
        if self.httpd:
            try: self.httpd.shutdown(); self.httpd.server_close()
            except Exception: pass
        self.httpd = self.thread = None


def qr_image(text, box=6):
    """QR kodu (PIL resmi) ya da qrcode paketi yoksa None."""
    try:
        import qrcode
        q = qrcode.QRCode(border=2, box_size=box)
        q.add_data(text); q.make(fit=True)
        return q.make_image(fill_color="black", back_color="white").get_image().convert("RGB")
    except Exception:
        return None
