"""Konuşma çevirisi: altyazısı olmayan oyun konuşmalarını yazıya döker (sonra canlı çeviri Türkçeye çevirir).

Kaynaklar
  - "captions": Windows 11 Canlı Altyazı (LiveCaptions.exe). Windows sesi yazıya döker; program yalnız o pencerenin
    metnini UI Automation ile okur. Ek indirme yok, yük çok düşük. (Windows 11 22H2+)
  - "whisper": Windows 10 (ve 11) için yerel Whisper (OpenAI, MIT) — CTranslate2 ile, programdaki çeviri altyapısıyla
    aynı. Bilgisayarın ses çıkışı (loopback) dinlenir, yalnız konuşma algılanınca model çalışır. Model ilk kullanımda
    sabit bir sürümden indirilir ve SHA-256 ile doğrulanır. İsteğe bağlıdır, varsayılan kapalıdır.
Oyunun belleğine / dosyalarına dokunulmaz; yalnız Windows'un ses çıkışı ve Canlı Altyazı penceresinin yazısı okunur.
Not: ses çıkışını dinlediği için sesli sohbet (Discord) de yazıya dökülebilir. Konuşma tanıma yereldir;
çeviri seçilen motora bağlıdır ve çevrimiçi sağlayıcı seçildiyse döküm o sağlayıcıya gönderilir.
"""
import hashlib
import json
import logging
import os
import re
import sys
import threading
import time
import urllib.request
from pathlib import Path

log = logging.getLogger("td2.speech")

# ---------------------------------------------------------------- Whisper modeli (sabit sürüm + SHA-256)
WHISPER_REPO = "https://huggingface.co/Systran/faster-whisper-base.en/resolve/3d3d5dee26484f91867d81cb899cfcf72b96be6c/"
WHISPER_FILES = {
    "config.json": "f3bc3821e9fc76a27bae538e11ae5b677dcdd352b4600429ce7951d398569aeb",
    "model.bin": "2a166925539a16005f14ff328359f9b9adb9dc4fb631bb3b227526862e93e2ef",
    "vocabulary.txt": "ff77588746d3a2595d32ab5b69ffd7b95ce2441ac57533cb66fc3eb575a115cf",
}
WHISPER_MB = 146
SR = 16000


def whisper_installed(d):
    return all((Path(d) / f).exists() for f in WHISPER_FILES)


def download_whisper(dest, progress=None, opener=None, base=None, files=None):
    """Model dosyalarını indirir ve doğrular. progress(alınan, toplam)."""
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True)
    files = files or WHISPER_FILES
    opener = opener or urllib.request.urlopen
    total_est = WHISPER_MB * 1024 * 1024; got = 0
    for name, sha in files.items():
        tmp = dest / (name + ".part")
        h = hashlib.sha256()
        req = urllib.request.Request((base or WHISPER_REPO) + name, headers={"user-agent": "TD2LootAdvisor"})
        with opener(req, timeout=60) as r, open(tmp, "wb") as f:
            while True:
                b = r.read(1 << 16)
                if not b: break
                f.write(b); h.update(b); got += len(b)
                if progress: progress(got, total_est)
        if h.hexdigest() != sha:
            tmp.unlink(missing_ok=True)
            raise ValueError(f"checksum mismatch: {name}")
        os.replace(tmp, dest / name)
    return str(dest)


# ---------------------------------------------------------------- log-mel (Whisper ile aynı; numpy)
_MEL = {}


def mel_filters(sr=SR, n_fft=400, n_mels=80):
    """librosa.filters.mel(sr, n_fft, n_mels) — Slaney ölçeği ve normalizasyonu."""
    import numpy as np
    key = (sr, n_fft, n_mels)
    if key in _MEL: return _MEL[key]
    f_sp, min_log_hz = 200.0 / 3, 1000.0
    min_log_mel = min_log_hz / f_sp; logstep = np.log(6.4) / 27.0

    def hz_to_mel(f):
        f = np.asanyarray(f, dtype=np.float64); m = f / f_sp
        return np.where(f >= min_log_hz, min_log_mel + np.log(np.maximum(f, 1e-10) / min_log_hz) / logstep, m)

    def mel_to_hz(m):
        m = np.asanyarray(m, dtype=np.float64); f = f_sp * m
        return np.where(m >= min_log_mel, min_log_hz * np.exp(logstep * (m - min_log_mel)), f)

    fft = np.linspace(0, sr / 2, 1 + n_fft // 2)
    mel_f = mel_to_hz(np.linspace(hz_to_mel(0.0), hz_to_mel(sr / 2), n_mels + 2))
    fdiff = np.diff(mel_f); ramps = mel_f[:, None] - fft[None, :]
    w = np.zeros((n_mels, len(fft)))
    for i in range(n_mels):
        lower = -ramps[i] / fdiff[i]; upper = ramps[i + 2] / fdiff[i + 1]
        w[i] = np.maximum(0, np.minimum(lower, upper))
    w *= (2.0 / (mel_f[2:n_mels + 2] - mel_f[:n_mels]))[:, None]
    _MEL[key] = w.astype(np.float32)
    return _MEL[key]


def log_mel(audio, n_frames=3000):
    """16 kHz mono float32 → [80, 3000] Whisper girişi (30 sn'ye doldurulur)."""
    import numpy as np
    n_fft, hop = 400, 160
    a = np.zeros(n_frames * hop, dtype=np.float32)
    x = np.asarray(audio, dtype=np.float32)[: len(a)]; a[: len(x)] = x
    a = np.pad(a, (n_fft // 2, n_fft // 2), mode="reflect")
    win = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n_fft) / n_fft)).astype(np.float32)   # periyodik Hann
    idx = np.arange(n_fft)[None, :] + hop * np.arange(n_frames + 1)[:, None]
    spec = np.fft.rfft(a[idx] * win, axis=1)
    mag = (np.abs(spec) ** 2).T[:, :-1]
    mel = mel_filters() @ mag
    lg = np.log10(np.maximum(mel, 1e-10))
    lg = np.maximum(lg, lg.max() - 8.0)
    return ((lg + 4.0) / 4.0).astype(np.float32)


# ---------------------------------------------------------------- GPT-2 bayt düzeyi çözümleme (tokenizers gerekmez)
def _bytes_to_unicode():
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]; n = 0
    for b in range(256):
        if b not in bs: bs.append(b); cs.append(256 + n); n += 1
    return {chr(c): b for b, c in zip(bs, cs)}


_BYTE = _bytes_to_unicode()


def detok(tokens):
    data = bytearray()
    for t in tokens:
        if t.startswith("<|") and t.endswith("|>"): continue
        for ch in t: data.append(_BYTE.get(ch, 32))
    return data.decode("utf-8", errors="replace").strip()


class Whisper:
    """CTranslate2 Whisper (int8, işlemci). transcribe(ses) → metin."""

    def __init__(self, model_dir, threads=None):
        self.dir = str(model_dir); self.m = None
        self.threads = threads or max(1, min(4, (os.cpu_count() or 2) // 2))
        self.lock = threading.Lock()

    @staticmethod
    def available():
        try:
            import ctranslate2, numpy  # noqa: F401
            return True
        except Exception:
            return False

    def load(self):
        if self.m: return
        import ctranslate2
        import winpath
        self.m = ctranslate2.models.Whisper(winpath.safe_dir(self.dir, "whisper"), device="cpu", compute_type="int8", intra_threads=self.threads)

    def transcribe(self, audio):
        import ctranslate2, numpy as np
        with self.lock:
            self.load()
            feats = ctranslate2.StorageView.from_array(np.ascontiguousarray(log_mel(audio)[None]))
            prompt = ["<|startoftranscript|>", "<|notimestamps|>"]          # .en modeli: dil / görev belirteci yok
            res = self.m.generate(feats, [prompt], beam_size=1, max_length=224, suppress_blank=True,
                                  no_repeat_ngram_size=3, return_no_speech_prob=True)
            r = res[0]
            if getattr(r, "no_speech_prob", 0) > 0.6: return ""
            return clean_text(detok(r.sequences[0]))


HALLUCINATIONS = {"thank you.", "thanks for watching!", "thank you for watching.", "you", "bye.", "[music]", "(music)", "[blank_audio]"}


# Whisper oyun adlarını sesteş sözcüklerle yazabilir: oyunda geçen biçime düzelt
GAME_FIX = [
    (r"\bcapital building\b", "Capitol Building"), (r"\bthe capital\b", "the Capitol"), (r"\bblack (?:task|tasks|tusks)\b", "Black Tusk"),
    (r"\b(?:isaac|isack|eisack|i sack)\b", "ISAC"), (r"\bs\.? ?h\.? ?d\.?(?=\s|$|[,.!?])", "SHD"), (r"\bdark zone\b", "Dark Zone"),
    (r"\btrue suns\b", "True Sons"), (r"\bhyena's\b", "Hyenas"), (r"\bkenley\b", "Kenly"), (r"\bfaye lao\b", "Faye Lau"),
    (r"\bwhite house\b", "White House"), (r"\bmanhunt\b", "Manhunt"), (r"\bkeener\b", "Keener"),
]


def clean_text(s):
    s = re.sub(r"\s+", " ", s).strip()
    for pat, rep in GAME_FIX: s = re.sub(pat, rep, s, flags=re.I)
    if s.lower() in HALLUCINATIONS or len(re.findall(r"[A-Za-z]", s)) < 3: return ""
    return s


# ---------------------------------------------------------------- konuşma parçalama (enerji eşiği, gürültü tabanı)
class Segmenter:
    """0,1 sn'lik ses parçalarından konuşma bölümleri çıkarır: sessizlik 0,6 sn ya da en çok 8 sn olunca bölümü verir."""

    def __init__(self, sr=SR, min_s=0.6, max_s=8.0, silence_s=0.6):
        import numpy as np
        self.np = np
        self.sr, self.min_s, self.max_s, self.silence_s = sr, min_s, max_s, silence_s
        self.noise = 0.004; self.buf = []; self.voiced = 0.0; self.quiet = 0.0

    def feed(self, chunk):
        np = self.np
        x = np.asarray(chunk, dtype=np.float32)
        rms = float(np.sqrt(np.mean(x * x))) if len(x) else 0.0
        dur = len(x) / self.sr
        speech = rms > max(0.012, self.noise * 3.0)
        if not speech: self.noise = 0.95 * self.noise + 0.05 * rms             # gürültü tabanını izle
        if speech or self.buf:
            self.buf.append(x)
            if speech: self.voiced += dur; self.quiet = 0.0
            else: self.quiet += dur
        total = sum(len(b) for b in self.buf) / self.sr
        if self.buf and (self.quiet >= self.silence_s or total >= self.max_s):
            seg = np.concatenate(self.buf); ok = self.voiced >= self.min_s
            self.buf, self.voiced, self.quiet = [], 0.0, 0.0
            return seg if ok else None
        return None


# ---------------------------------------------------------------- Canlı Altyazı metninden yeni cümleler
class CaptionDiff:
    """Canlı Altyazı penceresi kayan bir metin gösterir. Tamamlanan (noktalı ya da 1,5 sn değişmeyen) yeni cümleleri verir."""

    def __init__(self, stable_s=1.5, keep=200):
        self.seen = []; self.pending = ""; self.pending_t = 0.0; self.stable_s = stable_s; self.keep = keep

    def feed(self, text, now=None):
        now = now or time.time()
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text: return []
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
        out = []
        done, last = parts[:-1], parts[-1] if parts else ""
        if last and re.search(r"[.!?]$", last): done, last = parts, ""
        for p in done:
            if p not in self.seen:
                self.seen.append(p); out.append(p)
        if last:
            if last != self.pending: self.pending, self.pending_t = last, now
            elif now - self.pending_t >= self.stable_s and last not in self.seen:
                self.seen.append(last); out.append(last)
        self.seen = self.seen[-self.keep:]
        return [clean_text(o) for o in out if clean_text(o)]


# ---------------------------------------------------------------- kaynaklar
def windows_build():
    try: return sys.getwindowsversion().build if os.name == "nt" else 0
    except Exception: return 0


def captions_available():
    return os.name == "nt" and windows_build() >= 22621 and Path(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "LiveCaptions.exe").exists()


class _Source:
    def __init__(self, on_text, on_status=None):
        self.on_text, self.on_status = on_text, on_status or (lambda *a: None)
        self.stop_ev = threading.Event(); self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive(): return
        self.stop_ev.clear()
        self.thread = threading.Thread(target=self._run_safe, daemon=True, name=type(self).__name__); self.thread.start()

    def stop(self): self.stop_ev.set()

    def _run_safe(self):
        try: self.run()
        except Exception as e:
            log.exception("speech source"); self.on_status("error", str(e))


class LiveCaptionsSource(_Source):
    """Windows 11 Canlı Altyazı penceresinin metnini okur (UI Automation, AutomationId=CaptionsTextBlock)."""
    CLASS = "LiveCaptionsDesktopWindow"

    def __init__(self, on_text, on_status=None, hide=True):
        super().__init__(on_text, on_status); self.hide = hide

    def run(self):
        import ctypes
        import subprocess
        import comtypes
        import comtypes.client
        comtypes.CoInitialize()
        try:
            u = ctypes.windll.user32
            hwnd = u.FindWindowW(self.CLASS, None)
            if not hwnd:
                subprocess.Popen([str(Path(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "LiveCaptions.exe"))])
                for _ in range(40):
                    if self.stop_ev.wait(0.25): return
                    hwnd = u.FindWindowW(self.CLASS, None)
                    if hwnd: break
            if not hwnd: return self.on_status("error", "no-window")
            if self.hide:                                          # ekranın dışına taşı (Canlı Altyazı çalışmaya devam eder)
                u.SetWindowPos(hwnd, 0, -32000, -32000, 0, 0, 0x0001 | 0x0004 | 0x0010)
            comtypes.client.GetModule("UIAutomationCore.dll")
            from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation, TreeScope_Descendants, UIA_AutomationIdPropertyId
            uia = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
            root = uia.ElementFromHandle(hwnd)
            cond = uia.CreatePropertyCondition(UIA_AutomationIdPropertyId, "CaptionsTextBlock")
            el = None; diff = CaptionDiff()
            self.on_status("running", "captions")
            while not self.stop_ev.wait(0.3):
                try:
                    if el is None: el = root.FindFirst(TreeScope_Descendants, cond)
                    txt = el.CurrentName if el is not None else ""
                except Exception:
                    el = None; txt = ""
                    if not u.IsWindow(hwnd): return self.on_status("error", "closed")
                for s in diff.feed(txt): self.on_text(s)
        finally:
            try: comtypes.CoUninitialize()
            except Exception: pass


class WhisperSource(_Source):
    """Ses çıkışını (loopback) dinler → konuşma bölümleri → Whisper → metin. Ses yalnız bellekte işlenir, kaydedilmez."""

    def __init__(self, on_text, model_dir, on_status=None):
        super().__init__(on_text, on_status); self.model = Whisper(model_dir)

    @staticmethod
    def capture_available():
        try:
            import soundcard  # noqa: F401
            return True
        except Exception:
            return False

    def run(self):
        import numpy as np
        import soundcard as sc
        spk = sc.default_speaker()
        mic = sc.get_microphone(id=str(spk.name), include_loopback=True)
        seg = Segmenter()
        q, worker_busy = [], threading.Event()

        def work():
            while not self.stop_ev.is_set():
                if not q: time.sleep(0.05); continue
                audio = q.pop(0); worker_busy.set()
                try:
                    t0 = time.time(); txt = self.model.transcribe(audio)
                    log.debug("whisper %.1fs audio in %.2fs: %r", len(audio) / SR, time.time() - t0, txt)
                    if txt: self.on_text(txt)
                except Exception:
                    log.exception("whisper")
                finally:
                    worker_busy.clear()
        threading.Thread(target=work, daemon=True, name="whisper").start()
        self.on_status("running", "whisper")
        with mic.recorder(samplerate=48000, channels=2, blocksize=4800) as rec:
            while not self.stop_ev.is_set():
                data = rec.record(numframes=4800)                    # 0,1 sn
                mono = data.mean(axis=1) if data.ndim > 1 else data
                x16 = mono[: len(mono) // 3 * 3].reshape(-1, 3).mean(axis=1).astype(np.float32)   # 48 → 16 kHz (ortalama = basit alçak geçiren)
                s = seg.feed(x16)
                if s is not None and len(q) < 3: q.append(s)          # geride kalırsa eskiyi atla (gecikme birikmesin)
