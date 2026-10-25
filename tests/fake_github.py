#!/usr/bin/env python3
"""Sahte GitHub + Worker relay: panel ve report client'i test etmek için (hiç GitHub olmadan)."""
import json
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote

sys.path.insert(0, str(Path(__file__).parent.parent))

# Sahte veri deposu
ISSUES = {}
NEXT_ID = 1

class FakeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)
        
        # GitHub API: issue'ları listele (search)
        if u.path == "/search/issues" and "label:" in (u.query or ""):
            qs = parse_qs(u.query)
            q = qs.get("q", [""])[0]
            
            items = []
            for num, issue in ISSUES.items():
                if "label:report" in q and "report" not in issue.get("labels", []):
                    continue
                items.append({
                    "id": num, "number": num, "title": issue["title"],
                    "state": issue["state"], "body": issue["body"][:200],
                    "labels": [{"name": l} for l in issue.get("labels", [])],
                    "created_at": issue.get("created_at", "2026-10-25"),
                    "updated_at": issue.get("updated_at", "2026-10-25"),
                    "comments": len(issue.get("comments", [])),
                    "user": {"login": issue.get("user", "app")}
                })
            
            self._json(200, {"items": items, "total_count": len(items)})
            return
        
        # GitHub API: bir issue'nun detayı
        if u.path.startswith("/repos/") and "/issues/" in u.path:
            parts = u.path.split("/")
            try:
                no = int(parts[-1])
                issue = ISSUES.get(no)
                if issue:
                    self._json(200, {
                        "id": no, "number": no, "title": issue["title"],
                        "state": issue["state"], "body": issue["body"],
                        "labels": [{"name": l} for l in issue.get("labels", [])],
                        "created_at": issue.get("created_at", "2026-10-25"),
                        "comments": len(issue.get("comments", [])),
                        "user": {"login": issue.get("user", "app")}
                    })
                    return
            except ValueError:
                pass
            self._json(404, {"message": "Not Found"})
            return
        
        # GitHub API: issue'nun yorumları
        if u.path.startswith("/repos/") and "/comments" in u.path:
            parts = u.path.split("/")
            no = int(parts[parts.index("issues") + 1])
            issue = ISSUES.get(no)
            if issue:
                self._json(200, [{"id": i, "user": {"login": c.get("user", "app")},
                                 "body": c["body"], "created_at": c.get("created_at", "2026-10-25")}
                                for i, c in enumerate(issue.get("comments", []))])
                return
            self._json(404, {"message": "Not Found"})
            return
        
        # Worker: durum sorgusu
        if u.path == "/v1/reports/status":
            qs = parse_qs(u.query)
            ids = [int(x) for x in (qs.get("ids", [""])[0] or "").split(",") if x]
            reports = [{"id": no, "number": no, "status": ISSUES.get(no, {}).get("status", "new"),
                       "reply": "; ".join(c.get("body", "") for c in ISSUES.get(no, {}).get("comments", [])[-1:])}
                      for no in ids if no in ISSUES]
            self._json(200, {"reports": reports})
            return
        
        self._json(404, {"message": "Not Found"})
    
    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        
        u = urlparse(self.path)
        
        # GitHub API: issue oluştur
        if u.path.startswith("/repos/") and u.path.endswith("/issues"):
            global NEXT_ID
            data = json.loads(body)
            no = NEXT_ID; NEXT_ID += 1
            meta = {}
            if "<!-- td2-report" in data.get("body", ""):
                m = __import__("re").search(r"<!-- td2-report (.+?) -->", data["body"])
                if m: meta = json.loads(m.group(1))
            ISSUES[no] = {
                "title": data["title"],
                "body": data["body"],
                "labels": data.get("labels", []),
                "state": "open",
                "user": data.get("user", "app"),
                "created_at": time.strftime("%Y-%m-%d"),
                "comments": [],
                "meta": meta
            }
            self._json(201, {"id": no, "number": no, "ok": True})
            return
        
        # GitHub API: yorum ekle
        if u.path.startswith("/repos/") and "/comments" in u.path:
            parts = u.path.split("/")
            no = int(parts[parts.index("issues") + 1])
            if no in ISSUES:
                data = json.loads(body)
                ISSUES[no].setdefault("comments", []).append({
                    "body": data["body"],
                    "user": data.get("user", "app"),
                    "created_at": time.strftime("%Y-%m-%d")
                })
                self._json(201, {"ok": True})
                return
            self._json(404, {"message": "Not Found"})
            return
        
        # GitHub API: etiket ayarla
        if u.path.startswith("/repos/") and "/labels" in u.path:
            parts = u.path.split("/")
            no = int(parts[parts.index("issues") + 1])
            if no in ISSUES:
                labels = json.loads(body)
                ISSUES[no]["labels"] = labels
                self._json(200, {"ok": True})
                return
            self._json(404, {"message": "Not Found"})
            return
        
        # GitHub API: state değiştir
        if u.path.startswith("/repos/") and u.path.endswith(str(self.path.split("/")[-1])):
            parts = u.path.split("/")
            try:
                no = int(parts[-1])
                if no in ISSUES:
                    data = json.loads(body)
                    ISSUES[no]["state"] = data.get("state", ISSUES[no]["state"])
                    self._json(200, {"ok": True})
                    return
            except ValueError:
                pass
        
        # Worker: rapor gönder
        if u.path == "/v1/reports":
            global NEXT_ID
            data = json.loads(body)
            
            # Issue oluştur
            title = f"[{data.get('type', 'rapor').title()}] {data.get('title', '')}"
            meta_str = f"\n<!-- td2-report {json.dumps(data, ensure_ascii=False)} -->"
            body_text = f"{data.get('body', '')}{meta_str}"
            
            no = NEXT_ID; NEXT_ID += 1
            labels = [
                "report",
                f"type:{data.get('type', 'bug')}",
                "status:new",
                f"v{data.get('app_version', '?')}",
                f"lang:{data.get('lang', '?')}"
            ]
            ISSUES[no] = {
                "title": title,
                "body": body_text,
                "labels": labels,
                "state": "open",
                "user": data.get("contact", "?"),
                "created_at": time.strftime("%Y-%m-%d"),
                "comments": [],
                "meta": data
            }
            
            self._json(200, {"ok": True, "id": no, "number": no, "queued": False})
            return
        
        self._json(404, {"message": "Not Found"})
    
    def do_PATCH(self):
        length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        
        u = urlparse(self.path)
        parts = u.path.split("/")
        try:
            no = int(parts[-1])
            if no in ISSUES:
                data = json.loads(body)
                ISSUES[no]["state"] = data.get("state", ISSUES[no]["state"])
                self._json(200, {"ok": True})
                return
        except ValueError:
            pass
        
        self._json(404, {"message": "Not Found"})
    
    def _json(self, code, data):
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    
    def log_message(self, fmt, *args):
        pass

def run_server(port=8888):
    server = HTTPServer(("127.0.0.1", port), FakeHandler)
    print(f"Sahte sunucu çalışıyor: http://127.0.0.1:{port}")
    print("- GitHub API (search, get, post, patch)")
    print("- Worker relay (/v1/reports, /v1/reports/status)")
    server.serve_forever()

if __name__ == "__main__":
    # Örnek rapor ekle
    global NEXT_ID
    ISSUES[1] = {
        "title": "[Hata] Eşya yanlış okunuyor",
        "body": "Striker kneepads eldiven olarak okunuyor.\n\n<!-- td2-report {\"type\":\"bug\",\"title\":\"Eşya yanlış okunuyor\"} -->",
        "labels": ["report", "type:bug", "status:new", "v5.0.6", "lang:tr"],
        "state": "open",
        "user": "soner",
        "created_at": "2026-10-25",
        "comments": []
    }
    NEXT_ID = 2
    
    run_server()
