"""Sahte GitHub + sahte rapor sunucusu (worker.js'in /v1/reports uçlarının davranışı) — tek süreçte, ortak bellek.

    srv = start()            # http://127.0.0.1:<port>
    srv.base                 # programın TD2_REPORT_URL'si ve panelin API adresi
    ISSUES                   # {numara: issue}
Program → POST /v1/reports → issue açılır (etiketler + <!-- td2-report --> meta) → panel GitHub API'siyle okur/yanıtlar →
program GET /v1/reports/status ile durum ve yönetici yanıtını alır.
"""
import json
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = "test/reports"
ADMIN = "FEDERALTURK"
TOKEN = "test-token"
ISSUES, REPORTS = {}, {}          # REPORTS: rapor id → {"client", "number"}
TYPE_TR = {"bug": "Hata", "feature": "İstek", "question": "Soru"}


def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _j(self, code, data):
        b = json.dumps(data, ensure_ascii=False).encode(); self.send_response(code)
        self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def _body(self):
        n = int(self.headers.get("content-length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def _issue(self, n):
        it = ISSUES[n]
        return {"number": n, "title": it["title"], "state": it["state"], "body": it["body"], "labels": [{"name": l} for l in it["labels"]],
                "created_at": it["created_at"], "updated_at": it["updated_at"], "comments": len(it["comments"]),
                "html_url": f"https://github.com/{REPO}/issues/{n}"}

    def _auth(self):
        if self.headers.get("authorization") != f"Bearer {TOKEN}":
            self._j(401, {"message": "Bad credentials"}); return False
        return True

    def do_GET(self):
        p, _, q = self.path.partition("?")
        if p == "/v1/reports/status":                       # programın "Raporlarım" yenilemesi
            args = dict(x.split("=", 1) for x in q.split("&") if "=" in x)
            out = []
            for rid in args.get("ids", "").split(","):
                r = REPORTS.get(rid)
                if not r or r["client"] != args.get("client"): continue
                it = ISSUES[r["number"]]
                st = next((l[7:] for l in it["labels"] if l.startswith("status:")), "new")
                reply = next((c["body"] for c in reversed(it["comments"]) if c["user"]["login"] == ADMIN), "")
                out.append({"id": int(rid), "number": r["number"], "state": it["state"], "status": st, "reply": reply, "updated": it["updated_at"]})
            return self._j(200, {"reports": out})
        if not self._auth(): return
        if p == f"/repos/{REPO}": return self._j(200, {"full_name": REPO, "private": True, "open_issues_count": len(ISSUES)})
        if p == f"/repos/{REPO}/issues":
            return self._j(200, [self._issue(n) for n in sorted(ISSUES, reverse=True)] if "page=1" in q else [])
        m = re.match(rf"/repos/{REPO}/issues/(\d+)/comments$", p)
        if m: return self._j(200, ISSUES[int(m.group(1))]["comments"])
        self._j(404, {"message": "Not Found"})

    def do_POST(self):
        d = self._body()
        if self.path == "/v1/reports":                      # worker.js postReport ile aynı biçim
            if d.get("type") not in TYPE_TR or len(d.get("title", "")) < 4: return self._j(400, {"error": "invalid"})
            n = len(ISSUES) + 1
            meta = {"v": 1, "type": d["type"], "app_version": d.get("app_version"), "lang": d.get("lang"), "system": d.get("system"),
                    "contact": d.get("contact"), "card": d.get("card"), "log": d.get("log")}
            ISSUES[n] = {"title": f"[{TYPE_TR[d['type']]}] {d['title']}", "state": "open", "created_at": now(), "updated_at": now(), "comments": [],
                         "labels": ["report", f"type:{d['type']}", "status:new", f"v{d.get('app_version')}", f"lang:{d.get('lang')}"],
                         "body": d.get("body", "") + "\n\n<!-- td2-report " + json.dumps(meta, ensure_ascii=False) + " -->"}
            REPORTS[str(n)] = {"client": d.get("client"), "number": n}
            return self._j(200, {"ok": True, "id": n, "number": n})
        if not self._auth(): return
        m = re.match(rf"/repos/{REPO}/issues/(\d+)/comments$", self.path)
        if m:
            it = ISSUES[int(m.group(1))]
            it["comments"].append({"user": {"login": ADMIN}, "body": d["body"], "created_at": now()}); it["updated_at"] = now()
            return self._j(201, {"id": len(it["comments"])})
        self._j(404, {"message": "Not Found"})

    def do_PUT(self):
        if not self._auth(): return
        m = re.match(rf"/repos/{REPO}/issues/(\d+)/labels$", self.path)
        d = self._body(); ISSUES[int(m.group(1))]["labels"] = d["labels"]; ISSUES[int(m.group(1))]["updated_at"] = now()
        self._j(200, [{"name": l} for l in d["labels"]])

    def do_PATCH(self):
        if not self._auth(): return
        m = re.match(rf"/repos/{REPO}/issues/(\d+)$", self.path)
        d = self._body(); ISSUES[int(m.group(1))]["state"] = d["state"]
        self._j(200, self._issue(int(m.group(1))))


def start():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.base = f"http://127.0.0.1:{srv.server_port}"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    s = start(); print("Sahte sunucu:", s.base, "(Ctrl+C ile çık)")
    try: threading.Event().wait()
    except KeyboardInterrupt: pass
