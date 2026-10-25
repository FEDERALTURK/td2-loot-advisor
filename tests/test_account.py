"""Hesap istemcisi ↔ yerel worker uçtan uca testi (node server/dev_server.mjs gerekir).
    python tests/test_account.py
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import account  # noqa: E402
import features  # noqa: E402

fails = 0


def ok(c, msg):
    global fails
    print(("OK   " if c else "FAIL ") + msg)
    if not c: fails += 1


port = 8790 + os.getpid() % 100
srv = subprocess.Popen(["node", str(ROOT / "server" / "dev_server.mjs"), str(port)], stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL, text=True)
try:
    line = srv.stdout.readline().split()
    assert line and line[0] == "READY", line
    _, _, ADMIN, PUB = line
    URL = f"http://127.0.0.1:{port}"

    def admin(path, body=None):
        req = urllib.request.Request(URL + "/v1/admin/" + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": "Admin " + ADMIN, "Content-Type": "application/json"},
                                     method="POST" if body is not None else "GET")
        with urllib.request.urlopen(req) as r: return json.loads(r.read())

    def browser(user):
        """Tarayıcı + Discord onayı yerine: sahte onay → worker dönüşü → yerel programa yönlendirme."""
        def open_url(u):
            st = parse_qs(urlparse(u).query)["state"][0]
            ok(u.startswith("https://discord.com/"), "giriş bağlantısı Discord'a gidiyor")
            def go():
                with urllib.request.urlopen(f"{URL}/fake/discord?state={st}&user={user}") as r:
                    ok(r.status == 200 and "Signed in" in r.read().decode(), "tarayıcıda 'giriş tamamlandı' sayfası")
            threading.Thread(target=go, daemon=True).start()
        return open_url

    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "account.dat")
    acc = account.Account(path, URL)
    ok(not acc.signed_in, "başlangıçta girişsiz")
    j = acc.login(open_url=browser("Soner"), timeout=20)
    ok(acc.signed_in and acc.username == "Soner" and j["tier"] == "free", "Discord ile giriş → ücretsiz hesap")
    raw = open(path, encoding="utf-8").read()
    ok(acc.token not in raw or sys.platform != "win32", "belirteç diskte şifreli (Windows DPAPI)")

    acc2 = account.Account(path, URL)
    ok(acc2.signed_in and acc2.username == "Soner", "yeniden açılışta oturum hatırlandı")

    key = admin("licenses", {"count": 1, "days": 30})["keys"][0]
    try:
        acc.redeem("TD2K-XXXX-XXXX-XXXX-XXXX"); ok(False, "geçersiz anahtar")
    except account.AuthError as e:
        ok(e.code == "invalid", "geçersiz anahtar reddedildi")
    j = acc.redeem(key)
    ok(j["tier"] == "premium" and acc.entitlement.startswith("TD2E-"), "anahtar kullanıldı → premium")

    ent = features.Entitlements("")
    ok(ent.set_entitlement(acc.entitlement, account.device_pub(), PUB) and ent.tier == "premium" and ent.source == "account",
       "program yetki belgesini internetsiz doğruladı")
    ok(ent.has("recal_advisor") and ent.server_auth().startswith("TD2 TD2E-"), "premium özellik açık, sunucu başlığı hazır")
    ok(not features.Entitlements("").set_entitlement(acc.entitlement, account.device_pub("başka-bilgisayar"), PUB),
       "başka bilgisayara kopyalanan belge geçersiz")
    ok(not features.Entitlements("").set_entitlement(acc.entitlement, account.device_pub(), "11" * 32),
       "yanlış açık anahtarla doğrulanmaz")
    import time as _t
    ok(not features.Entitlements("").set_entitlement(acc.entitlement, account.device_pub(), PUB, now=_t.time() + 8 * 86400),
       "7 gün sonra internetsiz süre biter")

    # premium uç nokta belgeyle açılıyor
    req = urllib.request.Request(URL + "/v1/stats", headers={"Authorization": ent.server_auth()})
    with urllib.request.urlopen(req) as r: ok(r.status == 200, "topluluk istatistikleri belgeyle açıldı")

    # davet kodu ikinci hesapta
    inv = admin("invites", {"uses": 5, "days": 7})["code"]
    other = account.Account(os.path.join(tmp, "b.dat"), URL)
    other.login(open_url=browser("Ali"), timeout=20)
    j = other.redeem(inv.lower())
    ok(j["tier"] == "premium" and j["license"]["source"] == "invite", "davet kodu (küçük harf) çalıştı")
    try:
        other.redeem(key); ok(False, "başkasının anahtarı")
    except account.AuthError as e:
        ok(e.code == "used", "başkasının kullandığı anahtar reddedildi")

    # iptal → yenilemede premium düşer
    lic = next(l for l in admin("licenses")["licenses"] if l["username"] == "Soner")
    admin(f"licenses/{lic['id']}/revoke", {})
    j = acc.refresh()
    ok(j["tier"] == "free" and not acc.entitlement, "yönetici iptal edince yenilemede premium kapandı")

    # engellenen hesap → yerel oturum silinir
    a = next(x for x in admin("accounts")["accounts"] if x["username"] == "Ali")
    admin(f"accounts/{a['id']}/ban", {"banned": True})
    try:
        other.refresh(); ok(False, "engel")
    except account.AuthError as e:
        ok(e.code == "unauthorized" and not other.signed_in and not os.path.exists(os.path.join(tmp, "b.dat")),
           "engellenen hesabın yerel oturumu silindi")

    acc.logout()
    ok(not acc.signed_in and not os.path.exists(path), "çıkış yapıldı, yerel veri silindi")

    # sunucuya ulaşılamıyor
    off = account.Account(os.path.join(tmp, "c.dat"), "http://127.0.0.1:1")
    try:
        off.login(open_url=lambda u: None, timeout=1); ok(False, "offline")
    except account.AuthError as e:
        ok(e.code == "offline", "sunucu yoksa anlaşılır hata")
finally:
    srv.terminate()

print("RESULT: " + ("PASS" if not fails else f"FAIL ({fails})"))
sys.exit(1 if fails else 0)
