"""Konuşma çevirisi.
    python tests/test_speech.py              # birim (parçalama, Canlı Altyazı farkı, çözümleme, mel)
    python tests/test_speech.py --model DIR  # gerçek Whisper: Windows SAPI ile konuşturulan cümle → metin (Windows)
"""
import math
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402
import speech  # noqa: E402

fails = 0


def ok(c, m):
    global fails
    print(("OK   " if c else "FAIL ") + m)
    if not c: fails += 1


# --- parçalama
seg = speech.Segmenter()
sr = speech.SR
tone = lambda s, a=0.2: (a * np.sin(2 * np.pi * 220 * np.arange(int(sr * s)) / sr)).astype(np.float32)
quiet = lambda s: (np.random.default_rng(1).normal(0, 0.002, int(sr * s))).astype(np.float32)
outs = []
for chunk in [quiet(0.1)] * 10 + [tone(0.1)] * 15 + [quiet(0.1)] * 8:
    r = seg.feed(chunk)
    if r is not None: outs.append(r)
ok(len(outs) == 1 and 1.5 <= len(outs[0]) / sr <= 2.3, "konuşma bölümü sessizlikte kapandı (%.1f sn)" % (len(outs[0]) / sr if outs else 0))
outs = [r for r in (seg.feed(c) for c in [tone(0.1)] * 2 + [quiet(0.1)] * 8) if r is not None]
ok(outs == [], "çok kısa ses (öksürük, tık) bölüm sayılmadı")
outs = [r for r in (seg.feed(c) for c in [tone(0.1)] * 100) if r is not None]
ok(len(outs) >= 1 and len(outs[0]) / sr <= 8.1, "uzun konuşma 8 sn'de bölündü")

# --- Canlı Altyazı farkı
d = speech.CaptionDiff(stable_s=1.0)
ok(d.feed("Agent, the Black", 0) == [], "yarım cümle beklenir")
ok(d.feed("Agent, the Black Tusk have taken the Capitol.", 0.5) == ["Agent, the Black Tusk have taken the Capitol."], "nokta gelince cümle verildi")
ok(d.feed("Agent, the Black Tusk have taken the Capitol. Head to the", 0.8) == [], "eski cümle tekrar verilmez")
ok(d.feed("Agent, the Black Tusk have taken the Capitol. Head to the White House", 1.0) == [], "değişen yarım cümle beklenir")
ok(d.feed("Agent, the Black Tusk have taken the Capitol. Head to the White House", 2.2) == ["Head to the White House"], "1 sn değişmeyen yarım cümle verildi")
ok(d.feed("Thank you.", 3) == [], "sahte (halüsinasyon) metin atıldı")
ok(speech.clean_text("the black task have taken the capital building, isaac says") == "the Black Tusk have taken the Capitol Building, ISAC says", "oyun adları düzeltildi")

# --- çözümleme ve mel
ok(speech.detok(["<|startoftranscript|>", "ĠAgent", ",", "Ġhead", "Ġto", "Ġthe", "ĠWhite", "ĠHouse", ".", "<|endoftext|>"]) == "Agent, head to the White House.", "bayt düzeyi çözümleme")
m = speech.log_mel(tone(1.0))
ok(m.shape == (80, 3000) and m.dtype == np.float32 and -2 < float(m.min()) and float(m.max()) <= 2.5, "log-mel biçimi")
fb = speech.mel_filters()
ok(fb.shape == (80, 201) and abs(float(fb.sum()) - 0.0) > 0 and float(fb[0].max()) > 0, "mel süzgeçleri")

# --- indirme doğrulaması
import hashlib, io  # noqa: E402


class R(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False


blob = b"x" * 1000
files = {"a.bin": hashlib.sha256(blob).hexdigest()}
dd = tempfile.mkdtemp()
speech.download_whisper(dd, files=files, opener=lambda req, timeout=60: R(blob), base="http://x/")
ok((Path(dd) / "a.bin").read_bytes() == blob, "model indirildi ve doğrulandı")
try:
    speech.download_whisper(tempfile.mkdtemp(), files={"a.bin": "0" * 64}, opener=lambda req, timeout=60: R(blob), base="http://x/")
    ok(False, "yanlış özet")
except ValueError:
    ok(True, "yanlış SHA-256 reddedildi")

# --- gerçek model (Windows: SAPI ile konuştur → Whisper)
if "--model" in sys.argv:
    md = sys.argv[sys.argv.index("--model") + 1]
    if not speech.whisper_installed(md):
        speech.download_whisper(md)
    import wave
    import voicepack
    wav = os.path.join(tempfile.mkdtemp(), "s.wav")
    said = "Agent, the Black Tusk have taken control of the Capitol Building. Head to the White House."
    ok(voicepack.sapi_to_wav(said, wav, 170, ["en-us", "david", "zira"]), "SAPI ile konuşma üretildi")
    with wave.open(wav) as w:
        ch, sw, fr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1: x = x.reshape(-1, ch).mean(axis=1)
    x16 = np.interp(np.arange(0, len(x), fr / 16000), np.arange(len(x)), x).astype(np.float32)
    # gerçek akış: 0,1 sn parçalar → bölümler → Whisper
    seg = speech.Segmenter(); w = speech.Whisper(md); texts = []
    pad = np.zeros(int(sr * 1.0), dtype=np.float32)
    stream = np.concatenate([pad, x16, pad])
    t0 = time.time()
    for i in range(0, len(stream), 1600):
        s = seg.feed(stream[i:i + 1600])
        if s is not None: texts.append(w.transcribe(s))
    text = " ".join(texts)
    print("     whisper:", repr(text), f"({time.time() - t0:.1f} s, {len(x16) / sr:.1f} s ses)")
    low = text.lower()
    ok("black tusk" in low and "white house" in low and "capitol" in low, "Whisper konuşmayı doğru yazdı")
    tr_needed = time.time() - t0
    ok(tr_needed < len(x16) / sr * 3 + 10, "gerçek zamana yakın")

print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
sys.exit(1 if fails else 0)
