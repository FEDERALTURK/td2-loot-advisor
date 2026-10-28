"""Ücretsiz / premium özellikler ve lisans anahtarı.

Lisans anahtarı = imzalı küçük bir JSON: {"id", "name", "tier", "exp", "iat"}.
İmza Ed25519 (RFC 8032); doğrulama burada saf Python ile yapılır (ek paket yok, internet gerekmez).
Özel anahtar YALNIZCA yayıncıda durur (scripts/license_tool.py ile üretilir, depoya girmez);
uygulamada yalnız açık anahtar vardır.

Not: Program açık kaynak (MIT) olduğu için yerel kontrol kararlı bir kullanıcı tarafından kod değiştirilerek
atlanabilir. Asıl korunan premium özellikler sunucu tarafında olanlardır (ortak düşüş istatistiği, bulut eşitleme,
satıcı bildirimleri); anahtar onların erişim belirtecidir.
"""
import base64
import hashlib
import json
import time

# ---------------------------------------------------------------- özellik listesi
# tier: "free" herkese açık, "premium" lisans ister. Yeni özellik eklerken buraya yaz.
FEATURES = {
    "scan":            "free",     # eşya okuma ve karar
    "builds":          "free",     # build'ler, build ayrıntısı, eksik parça
    "tasks":           "free",     # görevler, Claude ile getir
    "stash":           "free",     # sandık envanteri ve denetim raporu
    "optimizer":       "free",     # aktif build için en iyi parça seçimi
    "drop_stats_share": "free",    # anonim düşüş istatistiği gönderme (gönüllü)
    "optimizer_all":   "premium",  # tüm build'leri sandığa göre karşılaştırma ve sıralama
    "recal_advisor":   "premium",  # kalibrasyon danışmanı (hangi attribute hangi eşyadan)
    "stash_export":    "premium",  # sandık raporunu CSV / HTML dışa aktarma
    "drop_stats_view": "premium",  # topluluk düşüş istatistikleri (hangi aktivitede ne düşüyor)
    "vendor_watch":    "premium",  # haftalık satıcı / hedefli loot bildirimleri
    "companion":       "premium",  # telefon arkadaşı (yerel web + QR)
    "game_service":    "free",     # oyunla birlikte başlat/durdur, tepsi, oturum günlüğü
    "smart_scan":      "free",     # ekran durumu (menü / dünya / yükleme) ile akıllı tarama
    "discord_presence": "free",    # Discord'da "TD2 Loot Advisor — envanter düzenliyor"
    "local_api":       "premium",  # yerel WebSocket API: OBS kaplaması, Stream Deck, telefon
    "push_notify":     "premium",  # telefon bildirimleri (ntfy / Discord webhook)
    "cloud_sync":      "premium",  # build / sandık bulut eşitleme
}
TIERS = ("free", "premium")
# Henüz yapım aşamasında olanlar (arayüzde "yakında" görünür; yapılınca buradan çıkar)
COMING = {"cloud_sync"}

# Yayıncının açık anahtarı (32 bayt, hex). scripts/license_tool.py init ile üretilir.
PUBLIC_KEY_HEX = "d70b17497241261ca45bcd05bbaedcd0fdeb3d866de4993d23db3c25274f633a"
KEY_PREFIX = "TD2P-"
# Hesap sunucusunun yetki belgesi açık anahtarı (Discord girişi + anahtar/davet/satış → TD2E belgesi).
# scripts/account_keys.mjs ile kullanıcının KENDİ bilgisayarında üretilir; özel yarısı yalnız Cloudflare gizlisinde durur.
ENT_PUBLIC_KEY_HEX = "06da3593d93eebb1a2df46d28577eca8b5c96364973194c900b337c1d74288a0"
ENT_PREFIX = "TD2E-"

# ---------------------------------------------------------------- Ed25519 (RFC 8032, saf Python)
_p = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _p - 2, _p) % _p
_I = pow(2, (_p - 1) // 4, _p)


def _H(m):
    return hashlib.sha512(m).digest()


def _xrecover(y):
    xx = (y * y - 1) * pow(_d * y * y + 1, _p - 2, _p)
    x = pow(xx, (_p + 3) // 8, _p)
    if (x * x - xx) % _p != 0: x = x * _I % _p
    if x % 2 != 0: x = _p - x
    return x


_By = 4 * pow(5, _p - 2, _p) % _p
_B = (_xrecover(_By) % _p, _By % _p, 1, _xrecover(_By) * _By % _p)   # genişletilmiş koordinatlar (X, Y, Z, T)


def _add(P, Q):
    x1, y1, z1, t1 = P; x2, y2, z2, t2 = Q
    a = (y1 - x1) * (y2 - x2) % _p; b = (y1 + x1) * (y2 + x2) % _p
    c = 2 * t1 * t2 * _d % _p; dd = 2 * z1 * z2 % _p
    e, f, g, h = b - a, dd - c, dd + c, b + a
    return (e * f % _p, g * h % _p, f * g % _p, e * h % _p)


def _mul(s, P):
    Q = (0, 1, 1, 0)
    while s > 0:
        if s & 1: Q = _add(Q, P)
        P = _add(P, P); s >>= 1
    return Q


def _enc(P):
    x, y, z, _ = P
    zi = pow(z, _p - 2, _p); x, y = x * zi % _p, y * zi % _p
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _dec(b):
    if len(b) != 32: raise ValueError("bad point")
    y = int.from_bytes(b, "little"); sign = y >> 255; y &= (1 << 255) - 1
    if y >= _p: raise ValueError("bad point")
    x = _xrecover(y)
    if (x & 1) != sign: x = _p - x
    P = (x, y, 1, x * y % _p)
    if (-x * x + y * y - 1 - _d * x * x * y * y) % _p != 0: raise ValueError("not on curve")
    return P


def _eq(P, Q):
    return (P[0] * Q[2] - Q[0] * P[2]) % _p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % _p == 0


def _secret_scalar(seed):
    h = _H(seed)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8; a |= 1 << 254
    return a, h[32:]


def public_key(seed):
    a, _ = _secret_scalar(seed)
    return _enc(_mul(a, _B))


def sign(seed, msg):
    a, prefix = _secret_scalar(seed)
    A = _enc(_mul(a, _B))
    r = int.from_bytes(_H(prefix + msg), "little") % _L
    R = _enc(_mul(r, _B))
    k = int.from_bytes(_H(R + A + msg), "little") % _L
    return R + ((r + k * a) % _L).to_bytes(32, "little")


def verify(pub, msg, sig):
    try:
        if len(sig) != 64: return False
        A = _dec(pub); R = _dec(sig[:32])
        s = int.from_bytes(sig[32:], "little")
        if s >= _L: return False
        k = int.from_bytes(_H(sig[:32] + pub + msg), "little") % _L
        return _eq(_mul(s, _B), _add(R, _mul(k, A)))
    except Exception:
        return False


# ---------------------------------------------------------------- lisans anahtarı
def _b64e(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_key(seed, payload):
    """Yayıncı aracı için: payload (dict) -> 'TD2P-<veri>.<imza>'."""
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return KEY_PREFIX + _b64e(body) + "." + _b64e(sign(seed, body))


def check_key(key, pub_hex=None, now=None):
    """Anahtarı doğrula. Dönüş: (geçerli mi, payload ya da {}, sebep: ok|empty|format|signature|expired)."""
    key = (key or "").strip().replace("\n", "").replace(" ", "")
    if not key: return False, {}, "empty"
    if not key.startswith(KEY_PREFIX) or "." not in key: return False, {}, "format"
    try:
        body_s, sig_s = key[len(KEY_PREFIX):].split(".", 1)
        body, sig = _b64d(body_s), _b64d(sig_s)
        payload = json.loads(body.decode())
    except Exception:
        return False, {}, "format"
    if not verify(bytes.fromhex(pub_hex or PUBLIC_KEY_HEX), body, sig):
        return False, {}, "signature"
    exp = payload.get("exp")
    if exp and (now or time.time()) > float(exp):
        return False, payload, "expired"
    return True, payload, "ok"


def check_entitlement(token, device_pub, pub_hex=None, now=None):
    """Hesap yetki belgesi (TD2E) — imza, süre (en çok 7 gün, internetsiz) ve BU bilgisayara bağlılık.
    Dönüş: (geçerli mi, payload ya da {}, sebep: ok|empty|nokey|format|signature|expired|device)."""
    token = (token or "").strip()
    if not token: return False, {}, "empty"
    pub_hex = pub_hex if pub_hex is not None else ENT_PUBLIC_KEY_HEX
    if not pub_hex: return False, {}, "nokey"
    if not token.startswith(ENT_PREFIX) or "." not in token: return False, {}, "format"
    try:
        body_s, sig_s = token[len(ENT_PREFIX):].split(".", 1)
        body, sig = _b64d(body_s), _b64d(sig_s)
        payload = json.loads(body.decode())
    except Exception:
        return False, {}, "format"
    if not verify(bytes.fromhex(pub_hex), body, sig): return False, {}, "signature"
    t = now or time.time()
    if not payload.get("exp") or t > float(payload["exp"]) or t + 300 < float(payload.get("iat", 0)):
        return False, payload, "expired"
    if not device_pub or payload.get("dev") != device_pub: return False, payload, "device"
    return True, payload, "ok"


class Entitlements:
    """Uygulamanın tek soru noktası: ent.has("recal_advisor").
    Premium iki yoldan gelir: yayıncının imzalı anahtarı (TD2P, eski yol) ya da hesap yetki belgesi (TD2E)."""

    def __init__(self, key="", pub_hex=None):
        self.ent_token, self.ent_payload, self.ent_reason = "", {}, "empty"
        self.set_key(key, pub_hex)

    def _recompute(self):
        if self.valid: self.tier = self.payload.get("tier", "premium")
        elif self.ent_reason == "ok": self.tier = self.ent_payload.get("tier", "premium")
        else: self.tier = "free"

    def set_key(self, key, pub_hex=None):
        self.key = key or ""
        self.valid, self.payload, self.reason = check_key(self.key, pub_hex)
        self._recompute()
        return self.valid

    def set_entitlement(self, token, device_pub, pub_hex=None, now=None):
        ok, self.ent_payload, self.ent_reason = check_entitlement(token, device_pub, pub_hex, now)
        self.ent_token = token if ok else ""
        self._recompute()
        return ok

    @property
    def source(self):
        """premium nereden geliyor: key | account | None"""
        if self.valid: return "key"
        if self.ent_reason == "ok": return "account"
        return None

    def server_auth(self):
        """Sunucunun premium uç noktaları için Authorization başlığı (yoksa "")."""
        if self.valid: return "TD2 " + self.key.strip()
        if self.ent_token: return "TD2 " + self.ent_token
        return ""

    def has(self, feature):
        need = FEATURES.get(feature, "free")
        return need == "free" or (self.tier == "premium")

    def locked(self):
        return [f for f in FEATURES if not self.has(f)]

    def expires(self):
        exp = self.payload.get("exp") if self.valid else self.ent_payload.get("lic_exp")
        return time.strftime("%Y-%m-%d", time.localtime(float(exp))) if exp else None
