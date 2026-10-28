"""Hizmet: oyun algılama olayları, oturum günlüğü, Discord RPC (sahte IPC), bildirimler (sahte HTTP).
    python tests/test_service.py"""
import json, os, socket, struct, sys, tempfile, threading, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import service, notify, presence  # noqa: E402

fails = 0
def ok(c, m):
    global fails
    print(("OK   " if c else "FAIL ") + m)
    if not c: fails += 1

# ---- oyun algılama
seq = iter([False, True, True, True, False])
focus = {"v": False}
ev = []
w = service.GameWatcher(lambda k, v: ev.append((k, v)), probe=lambda: next(seq), focus_probe=lambda: focus["v"])
w.tick(); ok(ev == [], "oyun kapalı: olay yok")
w.tick(); ok(ev == [("game", "started")] and w.started_at, "oyun açıldı olayı")
focus["v"] = True; w.tick(); ok(ev[-1] == ("focus", True), "oyun öne geldi")
w.tick(); ok(len(ev) == 2, "değişiklik yokken tekrar olay yok")
w.tick(); ok(ev[-2:] == [("game", "stopped"), ("focus", False)], "oyun kapandı + odak bitti")

# ---- oturum günlüğü
p = os.path.join(tempfile.mkdtemp(), "sessions.json")
sl = service.SessionLog(p)
sl.begin(now=1000)
sl.add_scan("KEEP", {"name": "Ninjabike", "rarity": ["EXOTIC"]})
sl.add_scan("DISMANTLE", {"name": "Walker", "rarity": ["HIGH-END"]})
sl.add_scan("KEEP", {"name": "The Sacrifice", "rarity": ["NAMED"]})
sl.add_upgrade("Striker Chest")
st = sl.stats()
ok(st["scanned"] == 3 and st["keep"] == 2 and st["dismantle"] == 1 and st["exotic"] == 1 and st["named"] == 1, "oturum sayaçları")
c = sl.end(now=1000 + 3600)
ok(c["highlights"] == ["Ninjabike", "The Sacrifice", "⬆ Striker Chest"], "öne çıkanlar")
ok(service.SessionLog(p).sessions[-1]["scanned"] == 3, "oturum dosyaya yazıldı")
sl.begin(now=5000); ok(sl.end(now=5060) and len(service.SessionLog(p).sessions) == 1, "boş, kısa oturum saklanmadı")
tot = service.SessionLog(p).totals(days=7, now=1000 + 3600 + 10)
ok(tot["sessions"] == 1 and tot["seconds"] == 3600 and tot["exotic"] == 1, "haftalık toplam")

# ---- Discord RPC (sahte IPC soketi)
if sys.platform != "win32":
    d = tempfile.mkdtemp(); os.environ["XDG_RUNTIME_DIR"] = d
    srv = socket.socket(socket.AF_UNIX); srv.bind(os.path.join(d, "discord-ipc-0")); srv.listen(1)
    got = []
    def fake_discord():
        c, _ = srv.accept()
        def rd():
            h = c.recv(8)
            if len(h) < 8: return None, None
            op, n = struct.unpack("<II", h); b = b""
            while len(b) < n: b += c.recv(n - len(b))
            return op, json.loads(b)
        def wr(op, o): b = json.dumps(o).encode(); c.sendall(struct.pack("<II", op, len(b)) + b)
        op, hs = rd(); got.append(("hs", hs))
        wr(1, {"cmd": "DISPATCH", "evt": "READY", "data": {"user": {"username": "soner"}}})
        while True:
            op, m = rd()
            if op is None or op == 2: break
            got.append(("frame", m)); wr(1, {"cmd": m.get("cmd"), "evt": None, "nonce": m.get("nonce"), "data": {}})
    threading.Thread(target=fake_discord, daemon=True).start()
    pr = presence.Presence("123456789012345678", buttons=[("TD2 Loot Advisor", "https://github.com/FEDERALTURK/td2-loot-advisor")])
    ok(pr.update("Envanter düzenliyor", "23 eşya · 2 egzotik", start=1700000000), "Discord'a etkinlik gönderildi")
    ok(got[0] == ("hs", {"v": 1, "client_id": "123456789012345678"}), "el sıkışma: uygulama kimliği")
    act = got[1][1]["args"]["activity"]
    ok(act["details"] == "Envanter düzenliyor" and act["state"].startswith("23") and act["timestamps"]["start"] == 1700000000
       and act["buttons"][0]["url"].startswith("https://github.com/"), "etkinlik içeriği")
    n_before = len(got)
    pr.update("Dünyada", "x"); ok(len(got) == n_before and pr.pending, "Discord sınırı: 15 sn içinde ikinci güncelleme bekletildi")
    pr.last_sent -= 20; pr.flush(); ok(len(got) == n_before + 1 and got[-1][1]["args"]["activity"]["details"] == "Dünyada", "bekleyen güncelleme gönderildi")
    pr.close(); time.sleep(0.2)
    ok(got[-1][1]["args"]["activity"] is None, "kapatınca etkinlik temizlendi")
    ok(not presence.Presence("abc").update("x"), "geçersiz uygulama kimliği: bağlanmaz")
    os.environ["XDG_RUNTIME_DIR"] = tempfile.mkdtemp()
    ok(not presence.Presence("123456789012345678").update("x", force=True), "Discord kapalıyken sessizce başarısız")

# ---- bildirimler
reqs = []
class R:
    status = 204
    def __enter__(self): return self
    def __exit__(self, *a): pass
def opener(req, timeout=10): reqs.append(req); return R()
n = notify.Notifier(opener=opener)
ok(not n.configure("kısa", "https://evil.com/api/webhooks/1/x"), "geçersiz konu ve webhook reddedildi")
topic = notify.new_topic()
ok(notify.valid_topic(topic) and len(topic) >= 20, "rastgele, uzun ntfy konusu: " + topic)
hook = "https://discord.com/api/webhooks/123456789012/" + "a" * 60
ok(n.configure(topic, hook) and n.subscribe_url == "https://ntfy.sh/" + topic, "ntfy + Discord webhook ayarlandı")
r = n.send_now("Egzotik düştü", "Ninjabike · SAKLA", kind="drop")
ok(r == (True, True) and len(reqs) == 2, "ikisine de gönderildi")
nt, dc = reqs
ok(nt.full_url == "https://ntfy.sh/" + topic and nt.get_header("Title").startswith("=?UTF-8?B?") and nt.data.decode() == "Ninjabike · SAKLA",
   "ntfy: Türkçe başlık kodlandı, gövde UTF-8")
body = json.loads(dc.data)
ok(body["embeds"][0]["title"] == "Egzotik düştü" and body["allowed_mentions"] == {"parse": []}, "Discord: embed, @everyone engelli")
notify.MIN_GAP = 0.05
reqs.clear()
for i in range(3): n.send(f"t{i}", "b", kind="vendor")
time.sleep(1.0)
ok(len(reqs) == 6, f"kuyruktaki bildirimler sırayla gitti ({len(reqs)})")
print("RESULT:", "PASS" if not fails else f"FAIL ({fails})"); sys.exit(1 if fails else 0)
