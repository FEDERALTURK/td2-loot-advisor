"""Panel kilidi: Windows şifresi gerekmeden, panelin KENDİ PIN'i.

- PIN hiçbir yerde saklanmaz. PBKDF2-HMAC-SHA256 (300 000 tur, rastgele tuz) ile iki anahtar türetilir:
  biri doğrulama için (diskte yalnız SHA-256 özeti), biri gizli ayarları (GitHub token, yönetici belirteci) şifrelemek için.
- Gizli ayarlar diskte iki katmanlıdır: önce PIN anahtarıyla (HMAC-SHA256 akış şifresi + HMAC etiketi, şifrele-sonra-doğrula),
  sonra Windows DPAPI ile. Ayar dosyası kopyalansa da, bilgisayar açıkken başkası paneli açsa da PIN olmadan belirteçler
  çözülemez.
- Yanlış denemeler sayılır ve diske yazılır: 5 hatadan sonra 30 sn, her yeni hatada iki katı (en çok 15 dk) bekleme.
- PIN unutulursa: "PIN'i sıfırla" yalnız şifreli belirteçleri siler; GitHub token ve yönetici belirteci yeniden girilir.
"""
import base64
import hashlib
import hmac
import os
import time

ITER = 300_000
PREFIX = "pin1:"
MIN_LEN = 6
FREE_TRIES = 5
MAX_WAIT = 15 * 60


def _derive(pin, salt, iters=ITER):
    raw = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, iters, dklen=64)
    return raw[:32], raw[32:]


def _sub(key, label):
    return hmac.new(key, label, hashlib.sha256).digest()


def _stream(key, nonce, n):
    out = bytearray()
    ctr = 0
    while len(out) < n:
        out += hmac.new(key, nonce + ctr.to_bytes(8, "big"), hashlib.sha256).digest()
        ctr += 1
    return bytes(out[:n])


def encrypt(key, text):
    data = text.encode("utf-8")
    nonce = os.urandom(16)
    ek, mk = _sub(key, b"enc"), _sub(key, b"mac")
    ct = bytes(a ^ b for a, b in zip(data, _stream(ek, nonce, len(data))))
    tag = hmac.new(mk, nonce + ct, hashlib.sha256).digest()
    return PREFIX + base64.b64encode(nonce + ct + tag).decode()


def decrypt(key, value):
    if not isinstance(value, str) or not value.startswith(PREFIX): raise ValueError("not sealed")
    raw = base64.b64decode(value[len(PREFIX):])
    if len(raw) < 48: raise ValueError("short")
    nonce, ct, tag = raw[:16], raw[16:-32], raw[-32:]
    ek, mk = _sub(key, b"enc"), _sub(key, b"mac")
    if not hmac.compare_digest(tag, hmac.new(mk, nonce + ct, hashlib.sha256).digest()): raise ValueError("bad tag")
    return bytes(a ^ b for a, b in zip(ct, _stream(ek, nonce, len(ct)))).decode("utf-8")


def valid_pin(pin):
    return isinstance(pin, str) and len(pin.strip()) >= MIN_LEN and pin == pin.strip()


def make(pin):
    """Yeni PIN: (ayarlara yazılacak kayıt, şifreleme anahtarı)."""
    if not valid_pin(pin): raise ValueError("PIN en az %d karakter olmalı" % MIN_LEN)
    salt = os.urandom(16)
    vk, ek = _derive(pin, salt)
    rec = {"salt": base64.b64encode(salt).decode(), "iter": ITER, "check": hashlib.sha256(vk).hexdigest(), "fails": 0, "until": 0}
    return rec, ek


def wait_left(rec, now=None):
    now = time.time() if now is None else now
    return max(0, int((rec or {}).get("until", 0) - now))


def check(rec, pin, now=None):
    """(şifreleme anahtarı | None, bekleme saniyesi). Kaydı (fails/until) yerinde günceller; çağıran diske yazmalı."""
    now = time.time() if now is None else now
    left = wait_left(rec, now)
    if left: return None, left
    try:
        vk, ek = _derive(pin or "", base64.b64decode(rec["salt"]), int(rec.get("iter", ITER)))
    except Exception:
        return None, 0
    if hmac.compare_digest(hashlib.sha256(vk).hexdigest(), rec.get("check", "")):
        rec["fails"], rec["until"] = 0, 0
        return ek, 0
    rec["fails"] = int(rec.get("fails", 0)) + 1
    extra = rec["fails"] - FREE_TRIES
    if extra >= 0:
        rec["until"] = now + min(MAX_WAIT, 30 * (2 ** extra))
    return None, wait_left(rec, now)

