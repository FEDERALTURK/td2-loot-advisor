"""GitHub API istemcisi: raporlar (özel depo, gizli repo), yorum, etiket yönetimi."""
import json
import urllib.request
import urllib.error
from urllib.parse import quote

GITHUB_API = "https://api.github.com"

class GitHub:
    def __init__(self, token, repo, api_base=GITHUB_API):
        self.token, self.repo, self.api = token, repo, api_base
    
    def _req(self, method, path, data=None):
        url = self.api.rstrip("/") + path
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, method=method,
                                     headers={"authorization": f"token {self.token}",
                                              "accept": "application/vnd.github.v3+json",
                                              "user-agent": "TD2-Admin-Panel"})
        try:
            with urllib.request.urlopen(req) as r:
                return True, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}: {e.reason}"
        except Exception as e:
            return False, str(e)
    
    def issues(self, labels="report", per_page=50, page=1, state="open"):
        """Etiketli issue'ları listele (sayfalı)."""
        q = f"label:{labels} state:{state} repo:{self.repo}"
        url = f"/search/issues?q={quote(q)}&per_page={per_page}&page={page}"
        ok, res = self._req("GET", url)
        if ok:
            return [{"id": it["id"], "number": it["number"], "title": it["title"],
                    "state": it["state"], "body": it["body"], "labels": [l["name"] for l in it["labels"]],
                    "created_at": it["created_at"], "updated_at": it["updated_at"],
                    "comments": it["comments"], "user": it["user"]["login"]} for it in res.get("items", [])]
        return None
    
    def issue(self, number):
        """Bir issue'nun detayını al."""
        ok, res = self._req("GET", f"/repos/{self.repo}/issues/{number}")
        return res if ok else None
    
    def comments(self, number):
        """Issue'nun yorumlarını al."""
        ok, res = self._req("GET", f"/repos/{self.repo}/issues/{number}/comments?per_page=100")
        return (res if isinstance(res, list) else []) if ok else []
    
    def add_comment(self, number, body):
        """Yorum ekle."""
        ok, res = self._req("POST", f"/repos/{self.repo}/issues/{number}/comments", {"body": body})
        return res if ok else None
    
    def set_labels(self, number, labels):
        """Issue'nun etiketlerini ayarla."""
        ok, res = self._req("POST", f"/repos/{self.repo}/issues/{number}/labels", labels)
        return ok
    
    def close(self, number):
        """Issue'yi kapat."""
        ok, res = self._req("PATCH", f"/repos/{self.repo}/issues/{number}", {"state": "closed"})
        return ok
    
    def reopen(self, number):
        """Issue'yi aç."""
        ok, res = self._req("PATCH", f"/repos/{self.repo}/issues/{number}", {"state": "open"})
        return ok
