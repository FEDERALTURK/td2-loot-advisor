"""TR/EN Neural recordings, optional online speech, and legacy SAPI helpers.

Fixed recordings in meta/voices play offline. Dynamic text is sent to the
Microsoft Edge speech service only when online voice is enabled. Legacy voice
lines, SAPI and radio filtering remain available for fallback and compatibility.
"""
import json
import random
import struct
import wave
import threading
from pathlib import Path

PACKS = ("classic", "tactical", "operator", "brief")
NATURAL_PACKS = ("natural_tr", "natural_en")
NATURAL_VOICES = {"natural_tr": "tr-TR-EmelNeural", "natural_en": "en-US-AriaNeural"}
_PLAYBACK_LOCK = threading.Lock()
_PLAYBACK_ALIAS = None


def stop_audio():
    """Stop current file playback; synthesis results are invalidated by Speaker."""
    import os
    if os.name != "nt": return
    import ctypes, winsound
    with _PLAYBACK_LOCK: alias = _PLAYBACK_ALIAS
    if alias: ctypes.windll.winmm.mciSendStringW(f"stop {alias}", None, 0, None)
    try: winsound.PlaySound(None, 0)
    except RuntimeError: pass


def natural_pack(pack, lang="tr"):
    return pack if pack in NATURAL_PACKS else ("natural_tr" if lang == "tr" else "natural_en")


class Recordings:
    """Fixed notifications shipped in meta; no service calls at runtime."""
    EVENTS = frozenset({"keep", "consider", "dismantle", "review", "exotic", "named", "build", "fills_gap", "upgrade", "demo"})

    def __init__(self, *meta_dirs):
        self.roots = [Path(p) for p in meta_dirs]

    def event(self, pack, event):
        if pack not in NATURAL_PACKS or event not in self.EVENTS: return None
        for root in self.roots:
            p = root / "voices" / pack / (event + ".wav")
            if p.is_file() and p.stat().st_size > 1000: return p
        return None

    def verdict(self, pack, verdict, rarity=(), build=False, note=None):
        events = []
        tags = set(rarity or [])
        if verdict in ("KEEP", "CONSIDER", "REVIEW"):
            if "EXOTIC" in tags: events.append("exotic")
            elif "NAMED" in tags: events.append("named")
        event = {"KEEP": "keep", "CONSIDER": "consider", "DISMANTLE": "dismantle", "REVIEW": "review"}.get(verdict)
        if event: events.append(event)
        if note in ("fills_gap", "upgrade"): events.append(note)
        elif build and verdict in ("KEEP", "CONSIDER"): events.append("build")
        return [p for event in events if (p := self.event(pack, event))]


def neural_audio(text, pack, cache_dir, rate_wpm=185):
    """Opt-in online speech. Cache stores hashed filenames, never text metadata.

    Uses Edge's online speech service through edge-tts, not a local model or an
    Azure subscription. Call only from the speaker worker after user opt-in.
    """
    import asyncio
    import hashlib
    import tempfile
    import time
    if pack not in NATURAL_VOICES: raise ValueError("Unknown voice pack")
    if not isinstance(text, str) or not text.strip() or len(text) > 5000: raise ValueError("Invalid speech text")
    rate = max(-35, min(35, round((float(rate_wpm) / 185 - 1) * 100 - 5)))
    voice = NATURAL_VOICES[pack]
    key = hashlib.sha256(json.dumps([voice, rate, text], ensure_ascii=False).encode("utf-8")).hexdigest()
    cache = Path(cache_dir); cache.mkdir(parents=True, exist_ok=True)
    target = cache / (key + ".mp3")
    if target.exists() and target.stat().st_size > 1000:
        target.touch()
        return target
    import edge_tts
    async def synth(path):
        await edge_tts.Communicate(text, voice, rate=f"{rate:+d}%", pitch="+0Hz",
                                   connect_timeout=10, receive_timeout=25).save(str(path))
    with tempfile.NamedTemporaryFile(dir=cache, suffix=".part", delete=False) as tmp:
        part = Path(tmp.name)
    try:
        asyncio.run(synth(part))
        data = part.read_bytes()
        if len(data) <= 1000 or not (data.startswith(b"ID3") or data[0] == 0xff):
            raise RuntimeError("Speech service returned invalid audio")
        part.replace(target)
    finally:
        part.unlink(missing_ok=True)
    # Bounded disk use: newest 128 clips, at most 32 MiB. Incomplete files are
    # cleaned separately and never treated as playable cache entries.
    files = sorted(cache.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    total = 0
    for index, path in enumerate(files):
        total += path.stat().st_size
        if index >= 128 or total > 32 * 1024 * 1024:
            if path != target: path.unlink(missing_ok=True)
    for path in cache.glob("*.part"):
        if time.time() - path.stat().st_mtime > 3600: path.unlink(missing_ok=True)
    return target


def play_audio(path):
    """Blocking playback on the speech worker; PCM WAV or cached neural MP3."""
    import ctypes
    import uuid
    global _PLAYBACK_ALIAS
    path = Path(path).resolve()
    if path.suffix.lower() == ".wav":
        import winsound
        winsound.PlaySound(str(path), winsound.SND_FILENAME)
        return
    alias = "td2voice" + uuid.uuid4().hex
    send = ctypes.windll.winmm.mciSendStringW
    def command(text):
        error = send(text, None, 0, None)
        if error: raise RuntimeError(f"Audio playback error {error}")
    try:
        command(f'open "{path}" type mpegvideo alias {alias}')
        with _PLAYBACK_LOCK: _PLAYBACK_ALIAS = alias
        command(f"play {alias} wait")
    finally:
        with _PLAYBACK_LOCK:
            if _PLAYBACK_ALIAS == alias: _PLAYBACK_ALIAS = None
        send(f"close {alias}", None, 0, None)


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


# ---------------------------------------------------------------- Windows konuşma motoru → WAV
def sapi_to_wav(text, path, rate_wpm=185, hints=()):
    """Metni Windows SAPI ile doğrudan WAV dosyasına söyletir (pyttsx3'ün dosyaya yazma hatasından kaçınır).
    Çağıran iş parçacığında COM başlatılır. Başarılıysa True."""
    import math
    import comtypes
    import comtypes.client
    comtypes.CoInitialize()
    try:
        voice = comtypes.client.CreateObject("SAPI.SpVoice")
        stream = comtypes.client.CreateObject("SAPI.SpFileStream")
        toks = voice.GetVoices()
        for h in [x.lower() for x in hints if x]:
            pick = next((toks.Item(i) for i in range(toks.Count) if h in (toks.Item(i).GetDescription() + " " + toks.Item(i).Id).lower()), None)
            if pick is not None:
                voice.Voice = pick; break
        voice.Rate = max(-10, min(10, int(round(math.log(max(rate_wpm, 50) / 200.0, 1.1)))))
        stream.Open(str(path), 3, False)                 # SSFMCreateForWrite
        voice.AudioOutputStream = stream
        voice.Speak(text, 0)
        stream.Close()
        return Path(path).exists() and Path(path).stat().st_size > 1000
    finally:
        try: comtypes.CoUninitialize()
        except Exception: pass


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
