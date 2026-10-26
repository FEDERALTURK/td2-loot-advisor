"""Ajan sesi: kararları özgün "taktik asistan" cümleleriyle söyler, isteğe bağlı telsiz efektiyle.

Cümleler meta/voice_lines.json'dadır (10 dil × 3 paket; topluluk yeni dil/paket ekleyebilir). Ses Windows'un
kendi konuşma motoruyla (SAPI) üretilir; telsiz efekti üretilen sese burada uygulanır (bant geçiren süzgeç,
hafif doyum, başta/sonda cızırtı). Hiçbir oyun sesi ya da başka bir yapımın sesi kullanılmaz.
"""
import json
import random
import struct
import wave
from pathlib import Path

PACKS = ("classic", "tactical", "operator", "brief")


class Lines:
    def __init__(self, *paths):
        self.data = {}
        for p in paths:
            try:
                self.data = json.loads(Path(p).read_text(encoding="utf-8")); break
            except (OSError, ValueError):
                continue
        self.rng = random.Random()

    def available(self, lang):
        return [p for p in self.data.get("lines", {}).get(lang, self.data.get("lines", {}).get("en", {}))]

    def line(self, lang, pack, event, **kw):
        L = self.data.get("lines", {})
        p = (L.get(lang) or L.get("en") or {}).get(pack) or (L.get("en") or {}).get(pack) or {}
        opts = p.get(event) or []
        if not opts: return ""
        s = self.rng.choice(opts)
        try: return s.format(**kw)
        except (KeyError, IndexError, ValueError): return s

    def compose(self, lang, pack, verdict, rarity="", build=None, pct=None, note=None):
        """Karar cümlesi: [egzotik/adlı uyarısı] + karar + [build uyumu] + [boşluk / yükseltme]."""
        parts = []
        r = (rarity or "").upper()
        if verdict in ("KEEP", "REVIEW", "CONSIDER"):
            if "EXOTIC" in r: parts.append(self.line(lang, pack, "exotic"))
            elif "NAMED" in r: parts.append(self.line(lang, pack, "named"))
        ev = {"KEEP": "keep", "CONSIDER": "consider", "DISMANTLE": "dismantle", "REVIEW": "review"}.get(verdict)
        if ev: parts.append(self.line(lang, pack, ev))
        if build and pct and verdict in ("KEEP", "CONSIDER"):
            parts.append(self.line(lang, pack, "build", build=build, pct=int(pct)))
        if note in ("fills_gap", "upgrade"): parts.append(self.line(lang, pack, note))
        return " ".join(p for p in parts if p)


# ---------------------------------------------------------------- telsiz efekti
def radio_fx(src, dst, seed=None):
    """WAV dosyasına telsiz efekti uygula. numpy yoksa dosyayı olduğu gibi kopyalar. Dönüş: dst yolu."""
    with wave.open(str(src), "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    try:
        import numpy as np
    except ImportError:
        Path(dst).write_bytes(Path(src).read_bytes()); return str(dst)
    if sw != 2:
        Path(dst).write_bytes(Path(src).read_bytes()); return str(dst)
    x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1: x = x.reshape(-1, ch).mean(axis=1)
    rng = np.random.default_rng(seed)
    # bant geçiren (300–3400 Hz) — FFT maskesi, yumuşak kenarlı
    N = 1 << int(np.ceil(np.log2(max(len(x), 2))))
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1.0 / sr)
    mask = np.clip((f - 250) / 150, 0, 1) * np.clip((3600 - f) / 400, 0, 1)
    y = np.fft.irfft(X * mask, N)[:len(x)]
    peak = float(np.max(np.abs(y))) or 1.0
    y = np.tanh(y / peak * 2.2) * 0.8                              # doyum (telsiz sertliği)
    y += rng.normal(0, 0.012, len(y)).astype(np.float32)           # hafif hışırtı
    def squelch(ms, amp):
        k = int(sr * ms / 1000)
        burst = rng.normal(0, amp, k).astype(np.float32)
        env = np.linspace(1, 0, k) ** 2
        return burst * env
    pre, post = squelch(70, 0.35), squelch(110, 0.3)
    gap = np.zeros(int(sr * 0.04), dtype=np.float32)
    out = np.concatenate([pre, gap, y.astype(np.float32), gap, post])
    pcm = (np.clip(out, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm)
    return str(dst)


def tone_wav(path, seconds=1.0, sr=22050, freq=440.0):
    """Test için basit bir sinüs WAV'ı (konuşma motoru olmayan ortamlarda)."""
    import math
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(12000 * math.sin(2 * math.pi * freq * i / sr))) for i in range(int(sr * seconds))))
    return str(path)
