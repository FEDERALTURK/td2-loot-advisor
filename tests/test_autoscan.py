"""Otomatik tarama yük kuralları (Windows CI; app modülünü yükler).

    python tests/test_autoscan.py
- Tüm ekranda eşya kartı yoksa ekranın tamamı tam çözünürlükte OCR'lanmaz, kart görüntüsü diske yazılmaz
- Oyun dünyasında kart çıkmadıkça okuma aralığı uzar (4 → 8 → 16 → 30 sn)
- Bölge modunda (küçük görüntü) eski davranış korunur
"""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("TD2_NO_WELCOME", "1")
from PIL import Image  # noqa: E402
import app  # noqa: E402

fails = 0


def ok(c, msg):
    global fails
    print(("OK   " if c else "FAIL ") + msg)
    if not c: fails += 1


ok([app.world_wait(i) for i in range(6)] == [4.0, 8.0, 16.0, 30.0, 30.0, 30.0], "dünya okuma aralığı uzuyor")

calls = {"read": 0}
app.find_card = lambda img: None


def fake_read(card, scale=None):
    calls["read"] += 1
    return "", []


app.read_card = fake_read


class Fake:
    cfg = {"settings": {}}
    card_box = None
    last_sig = None
    last_time = 0


f = Fake()
big = Image.new("RGB", (3440, 1440))
r = app.App.scan_image(f, big, auto=True)
ok(r is False and calls["read"] == 0, "tam ekranda kart yok: tam çözünürlükte okuma yapılmadı")
ok(f.card_box is None, "kart kutusu sıfırlandı")

# manuel (kısayol) taramada okuma yine yapılır
calls["read"] = 0
try:
    app.App.scan_image(f, big, auto=False)
except Exception:
    pass                                    # sahte nesnede sonraki adımlar eksik olabilir; yalnız okuma denendi mi bakılır
ok(calls["read"] >= 1, "kısayolla taramada okuma yapıldı")

# küçük bölge (kullanıcının seçtiği kart bölgesi): kart araması başarısız olsa da okunur
calls["read"] = 0
try:
    app.App.scan_image(f, Image.new("RGB", (700, 900)), auto=True)
except Exception:
    pass
ok(calls["read"] >= 1, "küçük bölgede eski davranış (okuma yapıldı)")

t0 = time.perf_counter()
for _ in range(50): app.App.scan_image(f, big, auto=True)
ok((time.perf_counter() - t0) / 50 < 0.01, "kartsız ekran atlaması anında")

import service  # noqa: E402
if os.name == "nt":
    ok(service.set_low_priority(True) and service.get_priority() == 0x4000, "oyun açıkken öncelik: normalin altı")
    ok(service.set_low_priority(False) and service.get_priority() == 0x20, "oyun kapanınca öncelik: normal")

import display  # noqa: E402
if os.name == "nt":
    display._EXE_CACHE.clear()
    t0 = time.perf_counter(); display.find_game_hwnd(); cold = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(10): display.find_game_hwnd()
    warm = (time.perf_counter() - t0) / 10
    print(f"     pencere taraması: ilk {cold*1000:.1f} ms, önbellekli {warm*1000:.1f} ms")
    ok(warm <= cold * 1.5 + 0.002, "süreç adı önbelleği taramayı hızlandırıyor")
t0 = time.perf_counter()
for _ in range(20): app.monitors()
ok((time.perf_counter() - t0) / 20 < 0.005, "monitör listesi önbellekten")

print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
sys.exit(1 if fails else 0)
