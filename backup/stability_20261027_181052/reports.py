"""Hata raporu / istek gönderme (programın içinden).

Raporlar topluluk sunucusuna (Cloudflare Worker, dropstats.DEFAULT_URL) gider; sunucu onları özel bir GitHub deposunda
issue olarak açar. Kullanıcının GitHub hesabı gerekmez. Gönderilmeden önce kişisel bilgiler temizlenir (Windows kullanıcı
klasörü yolları, lisans anahtarı, e-postalar, token'lar); sistem bilgisi ve kayıt dosyası yalnız kullanıcı işaretlerse eklenir.
Ağ yoksa rapor reports_queue.json'da bekler; gönderilenler reports_sent.json'da durumlarıyla tutulur.
"""
import json
import platform
import re
import time
import urllib.request
from pathlib import Path

TYPES = ("bug", "feature", "question")
TIMEOUT = 10


def scrub(text):
    """Kişisel bilgileri temizle (sunucu da aynısını yapar; burada da yapılır ki hiç gönderilmesin)."""
    if not text: return ""
    t = str(text)
    t = re.sub(r"TD2P-[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "TD2P-<license>", t)
    t = re.sub(r"([A-Za-z]:\\(?:Users|Documents and Settings)\\)[^\\/\r\n\"']+", r"\1<user>", t, flags=re.I)
    t = re.sub(r"(/(?:home|Users)/)[^/\s\"']+", r"\1<user>", t)
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "<email>", t)
    t = re.sub(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b", "<token>", t)
    for pat, rep in SCRUB_EXTRA: t = re.sub(pat, rep, t, flags=re.I)
    return t


# Ek kalıplar (sunucudaki worker.js scrub ile aynı)
SCRUB_EXTRA = [
    (r"([A-Za-z]:/(?:Users|Documents and Settings)/)[^/\r\n\"']+", r"\1<user>"),          # C:/Users/ad
    (r"\bsk-ant-[A-Za-z0-9_\-]{16,}", "<api-key>"), (r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}", "<api-key>"),
    (r"https?://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/\d+/[\w\-]+", "<webhook>"),
    (r"\bTD2[KIE]-[A-Za-z0-9_\-.]{6,}", "TD2-<key>"), (r"\bdpapi:[A-Za-z0-9+/=]+", "<secret>"),
    (r"([?&](?:t|token|key|access_token)=)[^&\s\"']+", r"\1<token>"), (r"\b(Bearer|Admin|TD2)\s+[A-Za-z0-9._~+/=\-]{12,}", r"\1 <token>"),
    (r"(ntfy\.sh/)[A-Za-z0-9_\-]+", r"\1<topic>"),
    (r"\b(?:10|127)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|\b192\.168\.\d{1,3}\.\d{1,3}\b|\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b", "<lan-ip>"),
]


def system_info(app_version, extra=None):
    info = {"os": f"{platform.system()} {platform.release()}", "python": platform.python_version(), "app": app_version}
    info.update({k: v for k, v in (extra or {}).items() if v not in (None, "")})
    return info


def log_tail(path, lines=120):
    try:
        data = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return ""
    return scrub("\n".join(data[-lines:]))


def build(rtype, title, body, contact="", app_version="", lang="", client="", system=None, log="", card=""):
    if rtype not in TYPES: raise ValueError("type")
    title, body = (title or "").strip(), (body or "").strip()
    if len(title) < 4: raise ValueError("title")
    if len(body) < 10: raise ValueError("body")
    return {"client": client, "type": rtype, "title": scrub(title)[:120], "body": scrub(body)[:6000],
            "contact": scrub(contact.strip())[:80], "app_version": app_version, "lang": lang,
            "system": json.loads(scrub(json.dumps(system or {}, ensure_ascii=False))),
            "log": scrub(log)[-12000:], "card": scrub(card)[:3000]}


def _post(url, payload, timeout=TIMEOUT):
    req = urllib.request.Request(url.rstrip("/") + "/v1/reports", data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"content-type": "application/json", "user-agent": "TD2-Loot-Advisor"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class Store:
    """Gönderilen raporlar ve çevrimdışı kuyruk (programın klasöründe)."""

    def __init__(self, base):
        self.base = Path(base)
        self.sent_p, self.queue_p = self.base / "reports_sent.json", self.base / "reports_queue.json"

    def _load(self, p):
        try: return json.loads(p.read_text(encoding="utf-8"))
        except Exception: return []

    def _save(self, p, data):
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(p)

    @property
    def sent(self): return self._load(self.sent_p)

    @property
    def queue(self): return self._load(self.queue_p)

    def send(self, url, payload):
        """Gönder; ağ yoksa kuyruğa al. Dönüş: ("sent", kayıt) | ("queued", None) | ("error", mesaj)."""
        try:
            res = _post(url, payload)
        except urllib.error.HTTPError as e:
            if e.code in (400, 413, 429): return "error", f"HTTP {e.code}"
            res = None
        except Exception:
            res = None
        if not res or not res.get("ok"):
            q = self.queue; q.append({"t": time.time(), "payload": payload}); self._save(self.queue_p, q)
            return "queued", None
        rec = {"id": res.get("id"), "number": res.get("number"), "type": payload["type"], "title": payload["title"],
               "time": time.strftime("%Y-%m-%d %H:%M"), "status": "queued" if res.get("queued") else "new", "reply": ""}
        s = self.sent; s.insert(0, rec); self._save(self.sent_p, s[:200])
        return "sent", rec

    def flush(self, url):
        """Kuyruktakileri göndermeyi dene. Dönüş: gönderilen sayısı."""
        q, left, n = self.queue, [], 0
        for item in q:
            st, _ = ("error", None)
            try:
                res = _post(url, item["payload"])
                if res.get("ok"):
                    rec = {"id": res.get("id"), "number": res.get("number"), "type": item["payload"]["type"],
                           "title": item["payload"]["title"], "time": time.strftime("%Y-%m-%d %H:%M"),
                           "status": "queued" if res.get("queued") else "new", "reply": ""}
                    s = self.sent; s.insert(0, rec); self._save(self.sent_p, s[:200]); n += 1
                    continue
            except Exception:
                pass
            left.append(item)
        self._save(self.queue_p, left)
        return n

    def refresh(self, url, client, timeout=TIMEOUT):
        """Sunucudan durum ve yanıtları al (yalnız kendi raporları). Dönüş: değişen kayıt sayısı."""
        s = self.sent
        ids = [str(r["id"]) for r in s if r.get("id")][:20]
        if not ids: return 0
        q = urllib.parse.urlencode({"client": client, "ids": ",".join(ids)})
        req = urllib.request.Request(url.rstrip("/") + "/v1/reports/status?" + q, headers={"user-agent": "TD2-Loot-Advisor"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        by = {x["id"]: x for x in data.get("reports", [])}
        changed = 0
        for rec in s:
            x = by.get(rec.get("id"))
            if not x: continue
            st = "closed" if x.get("state") == "closed" else (x.get("status") or rec.get("status"))
            new = {**rec, "number": x.get("number") or rec.get("number"), "status": st, "reply": x.get("reply") or rec.get("reply", "")}
            if new != rec: rec.update(new); changed += 1
        if changed: self._save(self.sent_p, s)
        return changed


import urllib.parse  # noqa: E402  (refresh için)
import urllib.error  # noqa: E402
