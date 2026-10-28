"""Nihai sürüm sertleştirme testleri.
    python tests/test_hardening.py [--model models/en-tr]
"""
import io
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import safeio  # noqa: E402
import reports  # noqa: E402
import updater  # noqa: E402
import livetranslate  # noqa: E402
import localapi  # noqa: E402
import winpath  # noqa: E402

fails = 0


def ok(c, m):
    global fails
    print(("OK   " if c else "FAIL ") + m, flush=True)
    if not c: fails += 1


tmp = Path(tempfile.mkdtemp())

# --- atomik, kilitli kayıt: 8 iş parçacığı aynı dosyaya aynı anda yazarken sözlük de değişiyor
cfg = {"builds": [], "settings": {"n": 0}}
path = tmp / "builds.json"
errors = []


def writer(k):
    for i in range(60):
        cfg["settings"][f"k{k}_{i % 7}"] = i
        try: safeio.write_json(path, cfg)
        except Exception as e: errors.append(repr(e))


th = [threading.Thread(target=writer, args=(k,)) for k in range(8)]
[t.start() for t in th]; [t.join() for t in th]
ok(not errors and json.loads(path.read_text(encoding="utf-8"))["builds"] == [], "eşzamanlı kayıtta dosya hep sağlam (%d hata)" % len(errors))
ok(not list(tmp.glob("*.tmp")), "geçici dosya kalmadı")
(path.with_name("builds.json.bak")).write_text(json.dumps({"builds": [{"name": "yedek"}], "settings": {}}), encoding="utf-8")
path.write_text("{bozuk", encoding="utf-8")
ok(safeio.read_json(path)["builds"][0]["name"] == "yedek", "bozuk dosyada günlük yedekten okundu")

# --- gizli ayarlar
c2 = {"settings": {"claude_api_key": "sk-ant-api03-SECRETSECRETSECRET", "push_webhook": "https://discord.com/api/webhooks/1/abc", "other": "x"}}
sealed = safeio.seal_settings(c2)
ok(c2["settings"]["claude_api_key"].startswith("sk-ant"), "bellekteki ayar değişmedi")
if os.name == "nt":
    ok(sealed["settings"]["claude_api_key"].startswith("dpapi:") and "SECRET" not in json.dumps(sealed), "dosyaya şifreli yazılıyor (DPAPI)")
    back = safeio.open_settings(json.loads(json.dumps(sealed)))
    ok(back["settings"]["claude_api_key"] == "sk-ant-api03-SECRETSECRETSECRET" and back["settings"]["other"] == "x", "geri açıldı")
    ok(safeio.unprotect("dpapi:AAAA") == "", "başka bilgisayarın şifresi boş döner (çökmez)")

# --- güncelleyici: zorunlu doğrulama
bad = [({"setup": "https://evil.example/TD2LootAdvisor_Setup_9.9.9.exe", "sha_url": "https://evil.example/x.sha256"}, "başka sunucu"),
       ({"setup": updater.DOWNLOAD_PREFIX + "v9/TD2LootAdvisor_Setup_9.9.9.exe", "sha_url": None}, "özet yok"),
       ({"setup": updater.DOWNLOAD_PREFIX + "v9/evil.exe", "sha_url": updater.DOWNLOAD_PREFIX + "v9/SHA256SUMS.sha256"}, "beklenmeyen dosya adı")]
for info, why in bad:
    try: updater.install_frozen(info); ok(False, "güncelleyici reddetmeli: " + why)
    except RuntimeError: ok(True, "güncelleyici reddetti: " + why)
orig = updater._get
updater._get = lambda url, timeout=15, binary=False, progress=None: b"abc  TD2LootAdvisor_Setup_9.9.9.exe.bak\nffff  other.exe\n"
ok(updater._expected_sha({"sha_url": "x"}, "TD2LootAdvisor_Setup_9.9.9.exe") is None, "özet satırı tam ad eşleşmeli")
updater._get = orig

# --- zip yol kaçışı
for evil in ("../evil.txt", "..\\evil.txt", "C:/Windows/evil.txt", "/etc/evil", "en-tr/../../evil"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z: z.writestr(evil, "x"); z.writestr("en-tr/model.bin", "x")
    data = buf.getvalue()

    class R(io.BytesIO):
        headers = {"Content-Length": str(len(data))}
        def __enter__(self): return self
        def __exit__(self, *a): return False
    d = Path(tempfile.mkdtemp())
    try:
        livetranslate.download_model(d, url="http://x/m.zip", sha256="", opener=lambda req, timeout=60, _d=data: R(_d))
        ok(False, "zip yol kaçışı reddedilmeli: " + evil)
    except RuntimeError:
        ok(True, "zip yol kaçışı reddedildi: " + evil)

# --- rapor temizliği
s = reports.scrub("sk-ant-api03-abcdefghijklmnopqrst https://discord.com/api/webhooks/123/abc TD2K-ABCD-EFGH http://192.168.1.5:8767/tr?t=TOKEN C:/Users/Ali/x ntfy.sh/gizli")
ok(all(x not in s for x in ("abcdefghijk", "webhooks/123", "TD2K-ABCD", "192.168", "TOKEN", "Ali", "gizli")), "rapor temizliği: " + s)

# --- yerel sunucu: yarım bağlantı iş parçacığını kilitlemez, diğer istekler cevaplanır
api = localapi.LocalAPI(lambda: {"ok": 1}, None, port=8798, token="t0k3n-123456")
api.start()
socks = [socket.create_connection(("127.0.0.1", 8798)) for _ in range(20)]       # hiçbir şey göndermeyen bağlantılar
import urllib.request  # noqa: E402
t0 = time.time()
r = json.loads(urllib.request.urlopen("http://127.0.0.1:8798/api/state?t=t0k3n-123456", timeout=5).read())
ok(r.get("ok") == 1 and time.time() - t0 < 3, "yarım bağlantılar varken istek cevaplandı")
try: urllib.request.urlopen("http://127.0.0.1:8798/api/state?t=yanlis", timeout=5); ok(False, "yanlış belirteç")
except urllib.error.HTTPError as e: ok(e.code == 403, "yanlış belirteç reddedildi")
socks[0].settimeout(25)
t0 = time.time()
try: closed = socks[0].recv(10) == b""
except (socket.timeout, OSError): closed = False
ok(closed and time.time() - t0 < 20, "boşta bağlantı zaman aşımıyla kapandı (%.0f sn)" % (time.time() - t0))
[x.close() for x in socks]; api.stop()

# --- Türkçe kullanıcı adı: ASCII dışı klasörden model yükleme
if "--model" in sys.argv and os.name == "nt":
    md = Path(sys.argv[sys.argv.index("--model") + 1])
    tr_dir = tmp / "Kullanıcı Şükrü Öğün" / "en-tr"
    shutil.copytree(md, tr_dir)
    try:
        import ctranslate2
        ctranslate2.Translator(str(tr_dir), device="cpu", compute_type="int8"); direct = "açılıyor"
    except Exception as e:
        direct = f"AÇILMIYOR ({type(e).__name__})"
    print("     doğrudan ASCII dışı yol:", direct, "| güvenli yol:", winpath.safe_dir(tr_dir, "mt-test"))
    m = livetranslate.LocalMT(tr_dir)
    out = m.translate(["Head to the safe house."])[0]
    ok(bool(out) and out != "Head to the safe house.", "ASCII dışı klasördeki model çalıştı: " + out)
    m.unload(); ok(m.tr is None, "model bellekten çıkarıldı")

print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
sys.exit(1 if fails else 0)
