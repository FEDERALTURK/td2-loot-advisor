"""GitHub REST istemcisi (yalnız standart kütüphane): rapor issue'ları, yorumlar, etiketler."""
import json
import re
import urllib.error
import urllib.request

GITHUB_API = "https://api.github.com"
META_RE = re.compile(r"<!--\s*td2-report\s+(\{.*?\})\s*-->", re.S)
STATUSES = ("new", "triaged", "in-progress", "done", "wontfix", "duplicate")


def parse_meta(body):
    """Issue gövdesinin sonundaki <!-- td2-report {...} --> verisi ve meta'sız gövde."""
    body = body or ""
    m = META_RE.search(body)
    meta = {}
    if m:
        try: meta = json.loads(m.group(1))
        except Exception: meta = {}
        body = (body[:m.start()] + body[m.end():]).strip()
    return meta, body


def label_value(labels, prefix, default=""):
    for l in labels:
        if l.startswith(prefix): return l[len(prefix):]
    return default


class GitHub:
    def __init__(self, token, repo, api_base=GITHUB_API, timeout=20):
        self.token, self.repo, self.api, self.timeout = token.strip(), repo.strip(), (api_base or GITHUB_API).rstrip("/"), timeout

    def _req(self, method, path, data=None):
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(self.api + path, data=body, method=method, headers={
            "authorization": f"Bearer {self.token}", "accept": "application/vnd.github+json",
            "x-github-api-version": "2022-11-28", "user-agent": "TD2-Report-Panel",
            **({"content-type": "application/json"} if body else {})})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read().decode("utf-8")
                return True, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            msg = e.reason
            try: msg = json.loads(e.read().decode("utf-8")).get("message", msg)
            except Exception: pass
            return False, f"HTTP {e.code}: {msg}"
        except Exception as e:
            return False, str(e)

    def check(self):
        """Bağlantı testi: (ok, mesaj)."""
        ok, res = self._req("GET", f"/repos/{self.repo}")
        if not ok: return False, res
        return True, f"{res.get('full_name')} ({'özel' if res.get('private') else 'açık'}) — {res.get('open_issues_count', 0)} açık issue"

    def issues(self, state="all", label="report", max_pages=10):
        """Etiketli issue'lar (PR'ler hariç). Hata olursa (False, mesaj)."""
        out = []
        for page in range(1, max_pages + 1):
            ok, res = self._req("GET", f"/repos/{self.repo}/issues?labels={label}&state={state}&per_page=100&page={page}&sort=created&direction=desc")
            if not ok: return False, res
            for it in res:
                if "pull_request" in it: continue
                labels = [l["name"] for l in it.get("labels", [])]
                meta, body = parse_meta(it.get("body"))
                out.append({"number": it["number"], "title": it["title"], "state": it["state"], "body": body, "meta": meta,
                            "labels": labels, "type": label_value(labels, "type:", meta.get("type", "?")),
                            "status": "closed" if it["state"] == "closed" and not label_value(labels, "status:") else label_value(labels, "status:", "new"),
                            "version": label_value(labels, "v", meta.get("app_version", "")), "lang": label_value(labels, "lang:", meta.get("lang", "")),
                            "created": it["created_at"], "updated": it["updated_at"], "comments": it.get("comments", 0),
                            "url": it.get("html_url", "")})
            if len(res) < 100: break
        return True, out

    def comments(self, number):
        ok, res = self._req("GET", f"/repos/{self.repo}/issues/{number}/comments?per_page=100")
        return res if ok and isinstance(res, list) else []

    def add_comment(self, number, body):
        return self._req("POST", f"/repos/{self.repo}/issues/{number}/comments", {"body": body})

    def set_labels(self, number, labels):
        return self._req("PUT", f"/repos/{self.repo}/issues/{number}/labels", {"labels": list(labels)})

    def set_status(self, number, labels, status):
        """status:* etiketini değiştir (diğer etiketler korunur)."""
        new = [l for l in labels if not l.startswith("status:")] + [f"status:{status}"]
        ok, res = self.set_labels(number, new)
        return ok, (new if ok else res)

    def set_state(self, number, state):
        return self._req("PATCH", f"/repos/{self.repo}/issues/{number}", {"state": state})
