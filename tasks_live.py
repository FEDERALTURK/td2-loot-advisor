"""Topluluk görevleri: canlı çeviri sırasında ekrandaki görev panelini tanır, (izin verildiyse) sunucuya gönderir;
oyunculardan toplanan güncel görev listesini çeker ve çeviri hafızası olarak kullanır.

Gönderilen: yalnız oyunun görev yazısı (başlık, alt başlık, açıklama, hedef, ödül adları, tür) ve programın Türkçe
çevirisi. Ekran görüntüsü, oyuncu adı, bilgisayar bilgisi gönderilmez. Sunucu bir görevi ancak en az 2 farklı
oyuncudan geldiyse herkese açık listeye koyar (server/tasks.js).

    task = extract(lines)                       # OCR satırları [(metin, (x0,y0,x1,y1), güven)] → görev ya da None
    sub = Submitter(url, client_id, state_path); sub.submit(task, tr, app_version)
    feed = fetch_live(url)                      # {"tasks": [...]} (doğrulanmış)
    mem = Memory(feed)                          # İngilizce satır → Türkçe (Translator'a verilir)
"""
import hashlib
import json
import re
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone

HEAD_OBJ = re.compile(r"^objectives?:?$", re.I)
HEAD_REW = re.compile(r"^rewards?:?$", re.I)
COUNTER = re.compile(r"(?<![\w/])(\d{1,3})\s?/\s?(\d{1,3})(?![\w/])")
ICON = re.compile(r"^(?:[^\w\s'\"(]+|[B-HJ-Zb-hj-z])\s+(?=[A-Z])")
LOCATIONS = {"base of operations", "white house", "the white house", "castle", "theater", "campus", "haven"}
TIMER = re.compile(r"^\s*(?:\d+\s*[dhm]\s*)+$", re.I)
COUNTDOWN = re.compile(r"\b\d+\s?[dh]\b\s*\d+\s?[hm]\b", re.I)      # "02h 51m", "1d 2h" — panel üstündeki geri sayım
LIMITS = {"title": 80, "subtitle": 80, "desc": 420, "objective": 220}


def norm(s):
    """Sunucudaki norm() ile aynı (server/tasks.js)."""
    s = str(s or "").lower().replace("’", "'")
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def task_key(title, objective):
    return hashlib.sha256(("task|" + norm(title) + "|" + norm(objective)).encode()).hexdigest()[:16]


def _english(s):
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 3 and sum(c.isascii() for c in letters) / len(letters) >= 0.9


# ---------------------------------------------------------------- ekrandan görev ayıklama
def extract(lines, resets=None, now=None):
    """Görev paneli: üstte başlık (+ alt başlık, yer), açıklama paragrafı, "Objective" başlığı + hedef, "Rewards" + liste.
    Sütun duyarlı OCR satırları beklenir (ocr_backend.Engine.segments). Bulunamazsa None."""
    import livetranslate
    rows = [(" ".join(str(t).split()), tuple(float(v) for v in b), float(c)) for t, b, c in lines
            if str(t).strip() and not livetranslate.PRIVATE.search(str(t))]          # arkadaş bildirimleri vb. asla
    objs = [r for r in rows if HEAD_OBJ.match(r[0])]
    if not objs: return None
    for o in objs:
        t = _extract_at(rows, o, resets, now)
        if t: return t
    return None


def _h(r): return max(1.0, r[1][3] - r[1][1])


def _extract_at(rows, o, resets, now):
    h = _h(o); x0 = o[1][0]
    rew = [r for r in rows if HEAD_REW.match(r[0]) and abs(r[1][0] - x0) < 3 * h and r[1][1] > o[1][3]]
    if not rew: return None
    rw = min(rew, key=lambda r: r[1][1])
    # panelin sağ kenarı: hedef satırlarının en sağı (sayaç dahil)
    band = [r for r in rows if o[1][3] - 0.2 * h <= r[1][1] < rw[1][1] - 0.2 * h]
    starts = [r for r in band if abs(r[1][0] - x0) < 2 * h]                 # hedef başlığıyla aynı hizada başlayanlar
    if not starts: return None
    right = max(r[1][2] for r in starts)
    for r in band:                                                          # aynı satırdaki sayaç (00/01)
        if COUNTER.fullmatch(r[0].strip()) and any(abs(r[1][1] - q[1][1]) < 0.6 * h and 0 <= r[1][0] - q[1][2] < 4 * h for q in starts):
            right = max(right, r[1][2])
    obj_rows = [r for r in band if r[1][0] >= x0 - 2 * h and r[1][2] <= right + h]
    width = right - x0
    if width < 4 * h: return None
    in_col = lambda r: r[1][0] >= x0 - 2 * h and r[1][2] <= right + 1.5 * h and r[1][0] < right
    obj_rows = [r for r in obj_rows if in_col(r)]
    total = None
    obj_txt = []
    for r in sorted(obj_rows, key=lambda r: (r[1][1], r[1][0])):
        m = COUNTER.search(r[0])
        if m: total = int(m.group(2)) or None
        s = " ".join(COUNTER.sub(" ", r[0]).split())
        if s: obj_txt.append(s)
    objective = " ".join(obj_txt)
    # ödüller: başlığın altında, aynı sütunda, aralıksız satırlar
    rewards, last = [], rw
    for r in sorted([r for r in rows if r[1][1] > rw[1][3] - 0.2 * h and in_col(r)], key=lambda r: r[1][1]):
        if r[1][1] - last[1][3] > 1.6 * h: break
        s = ICON.sub("", r[0]).strip()
        if s and _english(s) and not TIMER.match(s): rewards.append(s)
        last = r
        if len(rewards) >= 8: break
    # yukarı: açıklama paragrafı (hedef başlığının hemen üstü), sonra başlık bölümü
    above = sorted([r for r in rows if r[1][3] <= o[1][1] + 0.2 * h and in_col(r)], key=lambda r: -r[1][1])
    desc, cur = [], o
    for r in above:
        if cur[1][1] - r[1][3] > (0.6 * h if desc else 2.2 * h): break       # paragraf satırları bitişik
        if abs(_h(r) - h) > 0.35 * h: break                        # farklı punto: başlık bölümüne gelindi
        desc.insert(0, r[0]); cur = r
    head = []
    for r in above:
        if r[1][3] > cur[1][1] + 0.1 * h: continue
        if cur[1][1] - r[1][3] > 3.5 * h: break
        head.insert(0, r); cur = r
        if len(head) >= 6: break
    head = [r for r in head if not TIMER.match(r[0]) and not COUNTDOWN.search(r[0]) and _english(r[0])]
    if not head: return None
    big = max(_h(r) for r in head)
    title_rows = [r for r in head if _h(r) >= 0.8 * big]
    sub_rows = [r for r in head if r not in title_rows and norm(r[0]) not in LOCATIONS]
    location = next((r[0] for r in head if norm(r[0]) in LOCATIONS), "")
    title = " ".join(r[0] for r in title_rows)
    subtitle = " ".join(r[0] for r in sub_rows)
    task = {"title": title, "subtitle": subtitle, "desc": " ".join(desc), "objective": objective}
    for k, n in LIMITS.items():
        task[k] = task[k].strip()
        if len(task[k]) > n: return None
        if task[k] and not _english(task[k]): return None
    if not task["title"] or not task["objective"] or len(task["objective"]) < 8: return None
    if total: task["total"] = total
    if rewards: task["rewards"] = rewards
    low = (title + " " + subtitle + " " + location).lower()
    task["category"] = ("bounty" if "bounty" in low else "assignment" if ("assignment" in low or "classified" in low)
                        else "project" if ("project" in low or location.lower() == "base of operations" or
                                           re.search(r"\b(daily|weekly)\b", low)) else "other")
    task["period"] = ("daily" if re.search(r"\bdaily\b", low) else "weekly" if re.search(r"\bweekly\b", low)
                      else "season" if "season" in low else "other")
    exp = expires_for(task["period"], resets, now)
    if exp: task["expires_at"] = exp
    return task


def expires_for(period, resets=None, now=None):
    """Günlük / haftalık görevin biteceği an (UTC saniye); diğerleri None. resets: {"daily_hour_utc", "weekly_weekday", "weekly_hour_utc"}."""
    if period not in ("daily", "weekly"): return None
    now = now or datetime.now(timezone.utc)
    r = resets or {}
    dh, wd, wh = int(r.get("daily_hour_utc", 8)), int(r.get("weekly_weekday", 1)), int(r.get("weekly_hour_utc", 8))
    if period == "daily":
        t = now.replace(hour=dh, minute=0, second=0, microsecond=0)
        if t <= now: t += timedelta(days=1)
    else:
        t = now.replace(hour=wh, minute=0, second=0, microsecond=0) + timedelta(days=(wd - now.weekday()) % 7)
        if t <= now: t += timedelta(days=7)
    return int(t.timestamp())


# ---------------------------------------------------------------- gönderim
class Submitter:
    """Aynı görev aynı gün bir kez gönderilir (durum dosyasında); ağ işi arka planda."""

    def __init__(self, url, client_id, state_path=None, opener=None):
        self.url = (url or "").rstrip("/")
        self.client = client_id
        self.path = str(state_path) if state_path else None
        self.opener = opener or urllib.request.urlopen
        self.sent = {}
        self.lock = threading.Lock()
        self.last_error = None
        if self.path:
            try:
                with open(self.path, encoding="utf-8") as f: self.sent = json.load(f).get("sent", {})
            except (OSError, ValueError):
                pass

    def _save(self):
        if not self.path: return
        cutoff = time.time() - 3 * 86400
        self.sent = {k: v for k, v in self.sent.items() if v > cutoff}
        try:
            with open(self.path, "w", encoding="utf-8") as f: json.dump({"sent": self.sent}, f)
        except OSError:
            pass

    def due(self, task):
        k = task_key(task["title"], task["objective"]) + time.strftime(":%Y%m%d", time.gmtime())
        with self.lock:
            return k not in self.sent

    def submit(self, task, tr=None, app_version=None, wait=False):
        """Gönderilmesi gerekiyorsa gönderir. Dönüş: başlatıldıysa True."""
        if not self.url or not self.client: return False
        k = task_key(task["title"], task["objective"]) + time.strftime(":%Y%m%d", time.gmtime())
        with self.lock:
            if k in self.sent: return False
            self.sent[k] = time.time()
        body = {"client": self.client, "app": app_version, "task": task}
        if tr: body["tr"] = tr

        def go():
            try:
                req = urllib.request.Request(self.url + "/v1/tasks", data=json.dumps(body).encode(), method="POST",
                                             headers={"content-type": "application/json", "user-agent": f"TD2LootAdvisor/{app_version}"})
                with self.opener(req, timeout=10) as r: r.read()
                self.last_error = None
            except Exception as e:
                self.last_error = str(e)
                with self.lock: self.sent.pop(k, None)               # başarısız: bir dahaki görüşte yeniden denenir
            with self.lock: self._save()
        if wait: go()
        else: threading.Thread(target=go, daemon=True).start()
        return True


# ---------------------------------------------------------------- canlı liste
def validate_feed(d):
    if not isinstance(d, dict) or not isinstance(d.get("tasks"), list): raise ValueError("bad feed")
    out = []
    for x in d["tasks"][:300]:
        if not isinstance(x, dict): continue
        if not isinstance(x.get("title"), str) or not isinstance(x.get("objective"), str): continue
        t = {k: str(x[k])[:LIMITS[k] * 2] for k in LIMITS if isinstance(x.get(k), str)}
        t["key"] = str(x.get("key", ""))[:16] or task_key(t["title"], t["objective"])
        for k in ("category", "period"): t[k] = str(x.get(k) or "other")[:20]
        for k in ("expires_at", "first_seen", "last_seen", "reporters", "total"):
            if isinstance(x.get(k), int): t[k] = x[k]
        if isinstance(x.get("rewards"), list): t["rewards"] = [str(r)[:60] for r in x["rewards"][:8]]
        if isinstance(x.get("tr"), dict):
            t["tr"] = {k: str(v)[:LIMITS[k] * 2] for k, v in x["tr"].items() if k in LIMITS and isinstance(v, str)}
        out.append(t)
    lines = []
    for x in (d.get("lines") or [])[:2000] if isinstance(d.get("lines"), list) else []:
        if isinstance(x, dict) and isinstance(x.get("en"), str) and isinstance(x.get("tr"), str):
            lines.append({"en": x["en"][:420], "tr": x["tr"][:840]})
    return {"version": str(d.get("version", ""))[:24], "generated": d.get("generated"), "tasks": out, "lines": lines}


def fetch_live(url, raw_url=None, opener=None, timeout=10, app_version=None, start=False):
    """Önce sunucudan (taze), olmazsa GitHub'daki kopyadan. Dönüş: (feed, kaynak).

    Sunucuya yalnız program sürümü (User-Agent) ve açılıştaki ilk istek olduğu bilgisi gider; sunucu bunları kimliksiz,
    günlük sayaç olarak tutar (hangi sürüm kaç kez açıldı). Kimlik, IP ya da cihaz bilgisi gönderilmez/saklanmaz.
    """
    opener = opener or urllib.request.urlopen
    last = None
    ua = "TD2LootAdvisor/" + app_version if app_version and re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{1,3}", app_version) else "TD2LootAdvisor"
    for u in [x for x in ((url or "").rstrip("/") + "/v1/tasks/live" if url else None, raw_url) if x]:
        try:
            h = {"user-agent": ua}
            if start and u != raw_url: h["x-td2-run"] = "start"
            req = urllib.request.Request(u, headers=h)
            with opener(req, timeout=timeout) as r:
                return validate_feed(json.loads(r.read().decode("utf-8"))), u
        except Exception as e:
            last = e
    raise last or ValueError("no source")


def to_feed_tasks(feed, now=None):
    """Görevler sekmesi için (meta_sync.merge_tasks scope="community" biçimi)."""
    now = now or int(time.time())
    out = []
    kind = {"daily": "daily", "weekly": "weekly", "season": "seasonal"}
    for x in feed.get("tasks", []):
        until = x.get("expires_at") or (x.get("last_seen", now) + 8 * 86400)
        en = x["title"] + (f" – {x['subtitle']}" if x.get("subtitle") else "") + ": " + x["objective"]
        texts = {"en": en}
        tr = x.get("tr") or {}
        if tr.get("objective"):
            texts["tr"] = (tr.get("title") or x["title"]) + (f" – {tr['subtitle']}" if tr.get("subtitle") else "") + ": " + tr["objective"]
        how = {}
        if x.get("desc"): how["en"] = x["desc"] + (("\n🎁 " + ", ".join(x["rewards"])) if x.get("rewards") else "")
        if tr.get("desc"): how["tr"] = tr["desc"] + (("\n🎁 " + ", ".join(x["rewards"])) if x.get("rewards") else "")
        out.append({"feed_id": "cm-" + x["key"], "cat": "projects", "kind": kind.get(x.get("period"), ""), "texts": texts,
                    "how": how, "until": datetime.fromtimestamp(until, timezone.utc).isoformat(timespec="seconds"),
                    "source": ""})
    return {"tasks": out}


class Memory:
    """Canlı listedeki görevlerin satırları: İngilizce (normalize) → Türkçe. Translator önce buraya bakar."""

    def __init__(self, feed=None):
        self.map = {}; self.version = ""
        if feed: self.load(feed)

    def load(self, feed):
        self.version = str(feed.get("version", ""))[:20]
        m = {}
        for x in feed.get("tasks", []):
            tr = x.get("tr") or {}
            for k in LIMITS:
                if x.get(k) and tr.get(k): m[norm(x[k])] = tr[k]
        for ln in feed.get("lines", []):                  # yöneticinin onayladığı topluluk düzeltmeleri (öncelikli)
            m[norm(ln["en"])] = ln["tr"]
        self.map = m

    def __len__(self): return len(self.map)

    def get(self, text):
        return self.map.get(norm(text)) if self.map else None


def suggest(url, client, en, old, new, app_version=None, opener=None, timeout=10):
    """Çeviri satırı için daha iyi Türkçe önerisi (yönetici onaylarsa herkesin çeviri hafızasına girer). Dönüş: gönderildi mi."""
    if not url or not client: return False
    import reports
    body = {"client": client, "app": app_version, "en": reports.scrub(en), "old": reports.scrub(old), "new": reports.scrub(new)}
    try:
        req = urllib.request.Request(url.rstrip("/") + "/v1/suggest", data=json.dumps(body).encode(), method="POST",
                                     headers={"content-type": "application/json", "user-agent": f"TD2LootAdvisor/{app_version}"})
        with (opener or urllib.request.urlopen)(req, timeout=timeout) as r: r.read()
        return True
    except Exception:
        return False
