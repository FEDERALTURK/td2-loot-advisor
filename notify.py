"""Telefon bildirimleri: ntfy (ücretsiz uygulama, hesap gerekmez) ve/veya kendi Discord sunucuna webhook.

    n = Notifier(); n.configure(ntfy_topic="td2-ab12...", webhook=""); n.send("Egzotik düştü", "Ninjabike · SAKLA", kind="drop")

Gizlilik: yalnız kullanıcının seçtiği olaylar gönderilir (eşya adı, karar, build adı). Konu adı rastgele ve uzundur;
tahmin edilemez. Webhook adresi yalnız discord.com / discordapp.com olabilir.
"""
import json
import logging
import queue
import re
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger("td2.notify")
NTFY_DEFAULT = "https://ntfy.sh"
WEBHOOK_RE = re.compile(r"^https://(?:ptb\.|canary\.)?(?:discord|discordapp)\.com/api/webhooks/\d{5,25}/[A-Za-z0-9_\-]{20,100}$")
TOPIC_RE = re.compile(r"^[A-Za-z0-9_\-]{12,64}$")
MIN_GAP = 4.0                       # iki bildirim arası en az (sn)
MAX_PER_HOUR = 40
COLORS = {"drop": 0x2FBF71, "build": 0xFF6D10, "vendor": 0x5B8DEF, "session": 0x8B9098, "test": 0xFF6D10}
TAGS = {"drop": "star", "build": "jigsaw", "vendor": "shopping_cart", "session": "video_game", "test": "white_check_mark"}


def new_topic():
    return "td2-" + secrets.token_urlsafe(15).replace("_", "x").replace("-", "y")


def valid_webhook(url):
    return bool(WEBHOOK_RE.match((url or "").strip()))


def valid_topic(t):
    return bool(TOPIC_RE.match((t or "").strip()))


class Notifier:
    def __init__(self, opener=None):
        self._open = opener or urllib.request.urlopen
        self.topic = self.webhook = ""
        self.server = NTFY_DEFAULT
        self.q = queue.Queue(maxsize=50)
        self.sent, self.last = [], 0.0
        self.thread = None
        self.last_error = None

    def configure(self, ntfy_topic="", webhook="", server=None):
        self.topic = ntfy_topic.strip() if valid_topic(ntfy_topic) else ""
        self.webhook = webhook.strip() if valid_webhook(webhook) else ""
        s = (server or NTFY_DEFAULT).strip().rstrip("/")
        self.server = s if s.startswith("https://") else NTFY_DEFAULT
        return bool(self.topic or self.webhook)

    @property
    def enabled(self):
        return bool(self.topic or self.webhook)

    @property
    def subscribe_url(self):
        return f"{self.server}/{self.topic}" if self.topic else ""

    def send(self, title, body, kind="drop", link=None):
        if not self.enabled: return False
        try: self.q.put_nowait((str(title)[:120], str(body)[:900], kind, link))
        except queue.Full: return False
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run, daemon=True); self.thread.start()
        return True

    def send_now(self, title, body, kind="test"):
        """Eşzamanlı gönderim (Ayarlar'daki "dene" düğmesi). Dönüş: (ntfy sonucu, webhook sonucu) — None: kapalı."""
        return (self._ntfy(title, body, kind) if self.topic else None,
                self._discord(title, body, kind) if self.webhook else None)

    def _run(self):
        while True:
            try: title, body, kind, link = self.q.get(timeout=30)
            except queue.Empty: return
            now = time.time()
            self.sent = [t for t in self.sent if now - t < 3600]
            if len(self.sent) >= MAX_PER_HOUR: continue
            wait = MIN_GAP - (now - self.last)
            if wait > 0: time.sleep(wait)
            if self.topic: self._ntfy(title, body, kind, link)
            if self.webhook: self._discord(title, body, kind)
            self.last = time.time(); self.sent.append(self.last)

    def _post(self, req):
        try:
            with self._open(req, timeout=10) as r:
                ok = 200 <= r.status < 300
            self.last_error = None if ok else str(r.status)
            return ok
        except (urllib.error.URLError, OSError) as e:
            self.last_error = str(e); log.info("notify failed: %s", e); return False

    def _ntfy(self, title, body, kind, link=None):
        h = {"Title": _hdr(title),
             "Tags": TAGS.get(kind, "bell"), "Priority": "high" if kind in ("drop", "vendor") else "default",
             "User-Agent": "TD2LootAdvisor"}
        if link: h["Click"] = link
        return self._post(urllib.request.Request(f"{self.server}/{self.topic}", data=body.encode("utf-8"), headers=h, method="POST"))

    def _discord(self, title, body, kind):
        payload = {"username": "TD2 Loot Advisor", "allowed_mentions": {"parse": []},
                   "embeds": [{"title": title, "description": body, "color": COLORS.get(kind, 0xFF6D10)}]}
        return self._post(urllib.request.Request(self.webhook, data=json.dumps(payload).encode(),
                                                 headers={"Content-Type": "application/json", "User-Agent": "TD2LootAdvisor"},
                                                 method="POST"))


def _hdr(text):
    """HTTP başlıkları latin-1 olmalı: Türkçe vb. karakterler RFC 2047 ile kodlanır (ntfy destekler)."""
    try:
        text.encode("latin-1"); return text
    except UnicodeEncodeError:
        import base64
        return "=?UTF-8?B?" + base64.b64encode(text.encode("utf-8")).decode() + "?="
