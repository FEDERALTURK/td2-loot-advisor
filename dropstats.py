"""Topluluk düşüş istatistikleri — istemci (gönüllü, anonim).

Gönderilen: eşya adı / marka / set, tür, yuva, nadirlik, attribute TÜRLERİ (değer yok), en iyi rulo kalitesi %,
oyuncunun seçtiği aktivite ve rastgele bir istemci kimliği. Gönderilmeyen: kullanıcı adı, e-posta, lisans anahtarı,
bilgisayar bilgisi, attribute değerleri. Sunucu IP saklamaz ve istemci kimliğini tuzlu özetle tutar.

Bir tarama "düşüş" sayılmaz; yalnız oyuncu Panel'de bir aktivite seçtiyse ve eşya sandıkta YOKSA sayılır.
Sunucu adresi yoksa kayıtlar yerelde birikir (en çok MAX_QUEUE), adres girilince gönderilir.
"""
import hashlib
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
import uuid

log = logging.getLogger("td2.drops")

DEFAULT_URL = ""          # yayına alınınca: "https://td2-stats.<hesap>.workers.dev"
ACTIVITIES = ["none", "open_world", "mission", "legendary", "countdown", "summit", "incursion", "raid", "dark_zone",
              "conflict", "descent", "manhunt", "control_point", "bounty", "season", "caches", "crafting"]
KINDS = ("gear", "weapon", "gear_mod", "weapon_mod", "skill_mod")
MAX_QUEUE = 2000
BATCH = 50
UA = {"User-Agent": "TD2-Loot-Advisor", "Content-Type": "application/json"}


def new_client_id():
    return uuid.uuid4().hex


def item_sig(item):
    attrs = ",".join(f"{k}={float(v):g}" for k, v in sorted((item.get("attrs") or {}).items()))
    raw = f"{(item.get('name') or '').lower()}|{item.get('slot') or ''}|{attrs}|{','.join(sorted(item.get('talents') or []))}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def record(item, activity):
    """Taranan eşyadan gönderilecek anonim kayıt (ya da uygun değilse None)."""
    if activity in (None, "", "none") or item.get("kind") not in KINDS: return None
    name = item.get("name") if item.get("name") not in (None, "", "?") else None
    if not (name or item.get("brand") or item.get("gear_set")): return None
    q = item.get("quality") or {}
    return {"activity": activity, "kind": item.get("kind"), "slot": item.get("slot"), "name": name,
            "brand": item.get("brand"), "gear_set": item.get("gear_set"), "rarity": list(item.get("rarity") or [])[:3],
            "attrs": sorted((item.get("attrs") or {}).keys())[:6], "best_q": max(q.values()) if q else None,
            "sig": item_sig(item), "t": int(time.time())}


class Queue:
    def __init__(self, path):
        self.path, self.lock = path, threading.Lock()
        try:
            with open(path, encoding="utf-8") as f: self.items = json.load(f).get("drops", [])
        except (OSError, ValueError):
            self.items = []
        self.sent_total = 0

    def save(self):
        with self.lock:
            tmp = str(self.path) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f: json.dump({"drops": self.items[-MAX_QUEUE:]}, f)
            os.replace(tmp, self.path)

    def add(self, rec):
        if not rec: return False
        with self.lock:
            if any(r.get("sig") == rec["sig"] for r in self.items[-200:]): return False
            self.items.append(rec)
            del self.items[:-MAX_QUEUE]
        self.save()
        return True

    def __len__(self):
        return len(self.items)

    def flush(self, url, client, timeout=8):
        """Biriken kayıtları gönder. Dönüş: (gönderilen, hata ya da None)."""
        url = (url or DEFAULT_URL).rstrip("/")
        if not url or not self.items: return 0, None
        sent = 0
        while self.items:
            with self.lock: batch = self.items[:BATCH]
            body = json.dumps({"client": client, "drops": [{k: v for k, v in r.items() if k != "t"} for r in batch]}).encode()
            try:
                req = urllib.request.Request(url + "/v1/drops", data=body, headers=UA, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as resp: json.loads(resp.read() or b"{}")
            except urllib.error.HTTPError as e:
                if e.code == 400:                    # bozuk kayıtlar: at, takılı kalmasın
                    with self.lock: del self.items[:len(batch)]
                    continue
                self.save(); return sent, f"HTTP {e.code}"
            except Exception as e:
                self.save(); return sent, f"{type(e).__name__}: {e}"
            with self.lock: del self.items[:len(batch)]
            sent += len(batch)
        self.sent_total += sent
        self.save()
        return sent, None


def _get(url, path, headers=None, timeout=10):
    req = urllib.request.Request((url or DEFAULT_URL).rstrip("/") + path, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def summary(url):
    return _get(url, "/v1/summary")


def stats(url, license_key, activity=None, q=None, weeks=4):
    from urllib.parse import urlencode
    params = {"weeks": weeks}
    if activity and activity != "none": params["activity"] = activity
    if q: params["q"] = q
    return _get(url, "/v1/stats?" + urlencode(params), {"Authorization": "TD2 " + (license_key or "")})
