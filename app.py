"""
TD2 Loot Advisor v5 — The Division 2 item / build / project assistant.
TD2 Loot Advisor v5 — The Division 2 için eşya, build ve görev asistanı.

Multi-language: the interface language is chosen in Settings and lives in
`lang/<code>.json`. See i18n.py to add a new language.

IMPORTANT / ÖNEMLİ: this program never touches the game process or its
memory — no offsets, no injection. It only reads text from screenshots via
OCR and runs in its own windows. Even so, do not assume zero risk with
respect to Ubisoft's stance on overlay/automation tools.

See README.md for setup and usage.
"""
import csv, ctypes, json, logging, logging.handlers, os, queue, re, shutil, sys, threading, time
import urllib.error, urllib.request
import tkinter as tk
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher, get_close_matches
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

import mss
import pytesseract
from PIL import Image, ImageOps, ImageTk

import i18n
import ui_theme
import ui_art
import meta_sync
from i18n import t

APP_NAME = "TD2 Loot Advisor"
APP_VERSION = "5.0"
FROZEN = getattr(sys, "frozen", False)
BASE = Path(sys.executable).parent if FROZEN else Path(__file__).resolve().parent
TASKS_CACHE = BASE / "tasks_cache.json"  # son indirilen görev listesi
META_CACHE = BASE / "meta_cache.json"   # son indirilen meta listesi (çevrimdışı kullanım)
ART_DIR = BASE / "art"   # arka planlar / amblemler / bayraklar (kullanıcı kendi görsellerini ekleyebilir)
BUNDLE = Path(getattr(sys, "_MEIPASS", BASE))
CFG_PATH, LOG_PATH, DEBUG_PATH, PROG_PATH = (BASE / n for n in ("builds.json", "loot_log.csv", "last_crop.png", "progress.json"))
APPLOG_DIR = BASE / "logs"
APPLOG_PATH = APPLOG_DIR / "app.log"
LOG_HEADER = ["time", "item", "verdict", "best_build", "score", "slot", "rarity"]
ALL_SLOTS = ["Mask", "Backpack", "Chest", "Gloves", "Holster", "Kneepads", "Weapon", "Sidearm"]
SLOT_WORDS = {"mask": "Mask", "backpack": "Backpack", "chest": "Chest", "vest": "Chest", "gloves": "Gloves",
              "holster": "Holster", "kneepads": "Kneepads", "kneepad": "Kneepads", "knee pads": "Kneepads",
              # Silah tipleri: tooltip'te "Primary/Secondary" yazmaz, bu yüzden tek bir "Weapon" slotuna toplanır.
              # Tabanca ayrı "Sidearm" sayılır çünkü oyunda kendi slotu vardır; diğer tüm silahlar "Weapon" sayılır.
              "assault rifle": "Weapon", "submachine gun": "Weapon", "light machine gun": "Weapon",
              "marksman rifle": "Weapon", "sniper rifle": "Weapon", "shotgun": "Weapon", "rifle": "Weapon",
              "smg": "Weapon", "lmg": "Weapon", "pistol": "Sidearm"}
DEFAULTS = {"scan_mode": "hotkey", "auto_interval_ms": 700, "auto_record": True, "track_progress": True,
            "sound": True, "save_debug_crop": True, "log_csv": True, "overlay_corner": "top_right",
            "overlay_seconds": 8, "keep_threshold": 70, "consider_threshold": 40, "hotkey": "<f8>", "ocr_lang": "eng",
            "daily_reset_hour": 2, "weekly_reset_day": 1, "weekly_reset_hour": 2,  # weekly_reset_day: 0=Monday
            "chatgpt_window_title": "ChatGPT", "chatgpt_hotkey": "<f10>", "chatgpt_wait_seconds": 15,
            "language": "", "log_level": "INFO", "log_max_kb": 1024, "log_backups": 3,
            "ui_theme": "dark", "ui_sounds": True, "bg_interval": 15,
            "meta_sync": True, "meta_feed_url": "", "meta_last_try": 0, "meta_last_sync": "", "meta_version": "",
            "meta_hidden": [], "tasks_sync": True, "auto_reset_times": True}
AUTO_STABLE, AUTO_CHANGE, DEDUP_SECONDS, UPGRADE_MARGIN = 4, 8, 30, 3

if not CFG_PATH.exists() and (BUNDLE / "builds.json").exists():
    shutil.copy(BUNDLE / "builds.json", CFG_PATH)
if not (BASE / "lang").is_dir() and (BUNDLE / "lang").is_dir():
    shutil.copytree(BUNDLE / "lang", BASE / "lang")  # .exe içinden ilk açılışta dilleri çıkar

# ───────────── Günlük kayıt / application log ─────────────
log = logging.getLogger("td2")

def setup_logging(level="INFO", max_kb=1024, backups=3):
    """Dönen dosyalı günlük kayıt. Aynı anda konsola da yazar."""
    try:
        APPLOG_DIR.mkdir(exist_ok=True)
    except Exception:
        pass
    log.setLevel(getattr(logging, str(level).upper(), logging.INFO))
    for h in list(log.handlers):
        log.removeHandler(h)
        try: h.close()
        except Exception: pass
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S")
    try:
        fh = logging.handlers.RotatingFileHandler(APPLOG_PATH, maxBytes=int(max_kb) * 1024,
                                                  backupCount=int(backups), encoding="utf-8")
        fh.setFormatter(fmt); log.addHandler(fh)
    except Exception as e:
        print(f"[log] dosyaya yazilamiyor / cannot write log file: {e}")
    sh = logging.StreamHandler(); sh.setFormatter(fmt); log.addHandler(sh)
    log.propagate = False
    return log


# ───────────── dosyalar ─────────────
def load_cfg():
    with open(CFG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    for k, v in DEFAULTS.items():
        cfg["settings"].setdefault(k, v)
    return cfg

def save_cfg(cfg):
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def load_progress():
    try:
        return json.loads(PROG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_progress(p):
    PROG_PATH.write_text(json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")

def ensure_log():
    """Eski 5 sütunlu geçmişi 7 sütuna çevirir."""
    if not LOG_PATH.exists():
        return
    with open(LOG_PATH, encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if rows and len(rows[0]) < len(LOG_HEADER):
        with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(LOG_HEADER)
            for r in rows[1:]:
                w.writerow(r + [""] * (len(LOG_HEADER) - len(r)))

def read_log():
    ensure_log()
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, encoding="utf-8") as f:
        return [dict(zip(LOG_HEADER, r + [""] * 7)) for r in list(csv.reader(f))[1:]]

def find_tesseract(cfg):
    for c in (cfg["settings"].get("tesseract_cmd", ""), shutil.which("tesseract") or "",
              r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
        if c and os.path.exists(c):
            pytesseract.pytesseract.tesseract_cmd = c
            return c
    return None


# ───────────── OCR / ayrıştırma / skor ─────────────
RARITY_WORDS = {"exotic": "EXOTIC", "named": "NAMED", "prototype": "PROTOTYPE",
                "high-end": "HIGH-END", "high end": "HIGH-END", "superior": "SUPERIOR", "gear set": "GEAR SET"}
NUM = re.compile(r"(\d+(?:[.,]\d+)?)")

def norm(s):
    return re.sub(r"[^a-z0-9&' ]+", " ", s.lower()).strip()

def grab(region):
    with mss.mss() as sct:
        s = sct.grab(region)
        return Image.frombytes("RGB", s.size, s.rgb)

def preprocess(img):
    g = ImageOps.grayscale(img)
    g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
    g = ImageOps.autocontrast(g)
    if sum(g.resize((32, 32)).getdata()) / 1024 < 128:
        g = ImageOps.invert(g)
    return g

def ocr(img, lang):
    return pytesseract.image_to_string(preprocess(img), lang=lang, config="--psm 6")

def thumb(img):
    return list(ImageOps.grayscale(img).resize((24, 24)).getdata())

def dist(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)

def find_talent(talent, low, lines):
    tl = talent.lower()
    body = re.escape(tl).replace("\\ ", r"\s+")
    pat = r"\b" + body + r"\b" if tl.startswith("perfect") else r"(?<!perfect )(?<!perfectly )\b" + body + r"\b"
    return bool(re.search(pat, low)) or any(SequenceMatcher(None, norm(l), tl).ratio() >= 0.88 for l in lines)

def detect_slot(lines):
    head = norm(" ".join(lines[:4]))
    for w, slot in SLOT_WORDS.items():
        if re.search(r"\b" + w + r"\b", head):
            return slot
    return None

def parse_item(text, cfg):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    low = text.lower()
    item = {"name": lines[0] if lines else "?", "rarity": [], "attrs": {}, "talents": [], "slot": detect_slot(lines)}
    for w, tag in RARITY_WORDS.items():
        if w in low and tag not in item["rarity"]:
            item["rarity"].append(tag)
    alias_map = {a: k for k, al in cfg["attributes"].items() for a in al}
    for line in lines:
        m = NUM.search(line)
        if not m:
            continue
        val = float(m.group(1).replace(",", "."))
        label = norm(NUM.sub(" ", line))
        hit = get_close_matches(label, alias_map.keys(), n=1, cutoff=0.78) or [a for a in alias_map if a in label][:1]
        if hit:
            k = alias_map[hit[0]]
            item["attrs"][k] = max(val, item["attrs"].get(k, 0))
    known = {tal for b in cfg["builds"] for tal in b["talents"]}
    item["talents"] = [tal for tal in sorted(known, key=len, reverse=True) if find_talent(tal, low, lines)]
    return item

def signature(item):
    return item["name"].lower() + "|" + ",".join(f"{k}={v:g}" for k, v in sorted(item["attrs"].items())) + "|" + ",".join(sorted(item["talents"]))

def valid_item(item):
    letters = sum(c.isalpha() for c in item["name"])
    return letters >= 4 and (len(item["attrs"]) >= 1 or item["rarity"])

def score_build(item, b, low):
    raw, why = 0.0, []
    maxp = b.get("set_bonus", 0)
    if b["sets_or_brands"] and any(n.lower() in low for n in b["sets_or_brands"]):
        raw += b["set_bonus"]; why.append(t("why.set_match"))
    aw = sorted((a["weight"] for a in b["attributes"].values()), reverse=True)
    tw = sorted(b["talents"].values(), reverse=True)
    maxp += sum(aw[:4]) * 10 + (tw[0] * 10 if tw else 0)
    for k, r in b["attributes"].items():
        if k in item["attrs"]:
            v, good = item["attrs"][k], r["good_at"]
            ratio = v / good if good else 1
            raw += r["weight"] * 10 * min(ratio, 1.0)
            why.append(f"{k} {v:g} [" + (t("rate.good") if ratio >= 1 else t("rate.ok") if ratio >= .6 else t("rate.low")) + "]")
    for tal, w in b["talents"].items():
        if tal in item["talents"]:
            raw += w * 10; why.append(f"talent: {tal}")
    return (round(min(100, raw / maxp * 100)) if maxp else 0), why

def evaluate(text, cfg):
    item, low = parse_item(text, cfg), text.lower()
    res = []
    for b in cfg["builds"]:
        pct, why = score_build(item, b, low)
        res.append((pct, b["name"], why))
    res.sort(key=lambda r: r[0], reverse=True)
    st, best = cfg["settings"], (res[0][0] if res else 0)
    if {"EXOTIC", "NAMED", "PROTOTYPE"} & set(item["rarity"]):
        verdict = "REVIEW"
    elif best >= st["keep_threshold"]:
        verdict = "KEEP"
    elif best >= st["consider_threshold"]:
        verdict = "CONSIDER"
    else:
        verdict = "DISMANTLE"
    return item, verdict, res

def build_slots(cfg, name):
    for b in cfg["builds"]:
        if b["name"] == name:
            return b.get("slots") or ALL_SLOTS
    return ALL_SLOTS

def roll_diff(old_attrs, new_attrs):
    """İki eşyanın attribute rulolarını karşılaştırır: her satır bir attribute'taki farkı gösterir."""
    old_attrs, new_attrs = old_attrs or {}, new_attrs or {}
    lines = []
    for k in sorted(set(old_attrs) | set(new_attrs)):
        o, n = old_attrs.get(k), new_attrs.get(k)
        if o is None:
            lines.append(t("roll.only_new", k=k, n=f"{n:g}"))
        elif n is None:
            lines.append(t("roll.only_old", k=k, o=f"{o:g}"))
        elif abs(n - o) >= 0.05:
            lines.append(f"{k}: {o:g} → {n:g} ({'↑' if n > o else '↓'}{abs(n - o):.1f})")
    return lines

def apply_progress(cfg, progress, item, verdict, res):
    """Eksik parça / yükseltme / rulo karşılaştırması. (verdict, not, aksiyon, rulo_farki) döner."""
    if verdict not in ("KEEP", "CONSIDER") or not item["slot"] or not res:
        return verdict, None, None, None
    score, bname = res[0][0], res[0][1]
    slot = item["slot"]
    if slot not in build_slots(cfg, bname):
        return verdict, None, None, None
    cur = progress.get(bname, {}).get(slot)
    act = (bname, slot, score)
    if not cur:
        return verdict, t("note.fills_gap", build=bname, slot=slot_name(slot)), act, None
    if signature(item) == cur.get("sig"):
        return verdict, t("note.already", build=bname, slot=slot_name(slot)), None, None
    diff = roll_diff(cur.get("attrs"), item["attrs"])
    if score > cur["score"] + UPGRADE_MARGIN:
        return verdict, t("note.upgrade", build=bname, slot=slot_name(slot), old=cur["score"], new=score), act, diff
    return ("CONSIDER" if verdict == "KEEP" else verdict), t("note.yours_better", build=bname, slot=slot_name(slot), pct=cur["score"]), None, diff


# ───────────── UI sabitleri ─────────────
# Renkler seçili temadan gelir (ui_theme.py). App açılışta PAL/COLORS/VFG'yi günceller.
PAL = dict(ui_theme.PALETTES["dark"], mode="dark")
COLORS = dict(PAL["verdict"])      # karar kartı arka planları (beyaz yazı)
VFG = dict(PAL["verdict_fg"])      # karar renkleri yazı olarak (tablolar, sohbet)

def set_palette(p):
    PAL.clear(); PAL.update(p)
    COLORS.clear(); COLORS.update(p["verdict"])
    VFG.clear(); VFG.update(p["verdict_fg"])

def verdict_label(v):
    """Karar etiketinin o anki dildeki karşılığı (SAKLA / KEEP / BEHALTEN ...)."""
    return t(f"verdict.{v.lower()}")

def slot_name(slot):
    """Slot adının çevirisi; bilinmeyen slot olduğu gibi döner."""
    return t(f"slot.{slot.lower()}") if slot else ""

def click_through(win):
    if os.name != "nt":
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        st = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, st | 0x80000 | 0x20)
    except Exception:
        pass

def beep(verdict):
    try:
        import winsound
        winsound.Beep({"KEEP": 1200, "CONSIDER": 800, "REVIEW": 1000, "DISMANTLE": 400}.get(verdict, 600), 120)
    except Exception:
        pass

def draw_bars(cv, title, data, empty=None):
    empty = empty or t("word.no_data")
    cv.delete("all")
    w = max(cv.winfo_width(), 380)
    cv.create_text(14, 16, anchor="w", text=title, fill=PAL["fg"], font=(ui_theme.FONT_SEMI, 11))
    if not data or max(v for _, v, _ in data) == 0:
        cv.create_text(w // 2, 110, text=empty, fill=PAL["muted"], font=(ui_theme.FONT, 10)); return
    top, row = 38, min(28, 190 // max(len(data), 1))
    mx = max(v for _, v, _ in data)
    full = w - 230
    for i, (lab, val, col) in enumerate(data):
        y = top + i * row
        cv.create_text(14, y + row // 2 - 2, anchor="w", text=lab[:22], fill=PAL["muted"], font=(ui_theme.FONT, 9))
        cv.create_rectangle(150, y + 3, 150 + full, y + row - 7, fill=PAL["surface2"], outline="")   # iz
        bw = max(3, int(full * val / mx)) if val else 0
        if bw: cv.create_rectangle(150, y + 3, 150 + bw, y + row - 7, fill=col, outline="")
        cv.create_text(158 + full, y + row // 2 - 2, anchor="w", text=str(val), fill=PAL["fg"], font=(ui_theme.FONT_SEMI, 9))


# ───────────── Asistan yardımcıları ─────────────
DEFAULTS.update({
    "ai_provider": "ollama", "ollama_url": "http://localhost:11434", "ollama_model": "gemma3:12b",
    "claude_model": "claude-haiku-5-5", "claude_api_key": "", "claude_code_model": "haiku", "openai_model": "gpt-4o-mini", "openai_api_key": "",
    "stt_model": "small", "stt_device": "cpu",
    "tts_rate": 185, "tts_voice": "", "voice_hotkey": "<f9>", "speak_verdict": True, "speak_chat": True})
PROVIDER_KEYS = ["ollama", "claude_code", "claude", "openai", "builtin"]

def provider_label(pid):
    return t(f"provider.{pid}")
def system_prompt():
    """Asistan istemi; yanıt dili seçili arayüz diline göre belirlenir."""
    lang = i18n.english_name()
    return (f"You are a local item and build assistant for Tom Clancy's The Division 2. "
            f"The user writes in {lang}; always answer in {lang}. "
            f"Your answer may be read aloud: be short and clear, at most 3 sentences, "
            f"no bullet points and no markdown. "
            f"Rely only on the CONTEXT data below. If something is not in the context — other game "
            f"knowledge or the current meta — say you are not sure rather than inventing it. "
            f"Base keep/dismantle advice on the scores and empty slots in the context. "
            f"Warn before dismantling Exotic, Named or Prototype items. "
            f"Do not help with reading game memory, cheats or bot software.")


class Speaker:
    """Çevrimdışı konuşma (Windows SAPI, pyttsx3). Kendi iş parçacığında çalışır."""
    def __init__(self):
        self.q, self.err = queue.Queue(), None
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        eng = None
        try:
            import pyttsx3
            eng = pyttsx3.init()
        except Exception as e:
            self.err = f"{type(e).__name__}: {e}"
        while True:
            job = self.q.get()
            if job is None:
                break
            if not eng:
                continue
            text, rate, hint = job
            try:
                voices = eng.getProperty("voices")
                pick = None
                for key in ([hint.lower()] if hint else []) + ["turk", "tr-tr", "tolga", "emel"]:
                    pick = next((v for v in voices if key in (v.name + " " + v.id).lower()), None)
                    if pick: break
                if pick: eng.setProperty("voice", pick.id)
                eng.setProperty("rate", rate)
                eng.say(text); eng.runAndWait()
            except Exception as e:
                self.err = f"{type(e).__name__}: {e}"

    def say(self, text, rate=185, hint="", interrupt=True):
        if interrupt:
            try:
                while True: self.q.get_nowait()
            except queue.Empty:
                pass
        self.q.put((text, rate, hint))

    def close(self):
        self.q.put(None)


class Recorder:
    """Mikrofon kaydı (sounddevice, 16 kHz mono)."""
    def __init__(self):
        self.frames, self.stream, self.active = [], None, False

    def start(self):
        import sounddevice as sd
        self.frames = []
        self.stream = sd.InputStream(samplerate=16000, channels=1, dtype="float32",
                                     callback=lambda indata, n, tm, s: self.frames.append(indata.copy()))
        self.stream.start(); self.active = True

    def stop(self):
        import numpy as np
        self.active = False
        if self.stream:
            self.stream.stop(); self.stream.close(); self.stream = None
        return np.concatenate(self.frames)[:, 0] if self.frames else np.zeros(0, dtype="float32")


_WHISPER = {"key": None, "model": None}

def transcribe(audio, cfg):
    """Yerel konuşma tanıma (faster-whisper). İlk çalıştırmada model bir kez indirilir."""
    from faster_whisper import WhisperModel
    st = cfg["settings"]
    key = (st["stt_model"], st["stt_device"])
    if _WHISPER["key"] != key:
        _WHISPER["model"] = WhisperModel(st["stt_model"], device=st["stt_device"],
                                         compute_type="float16" if st["stt_device"] == "cuda" else "int8")
        _WHISPER["key"] = key
    segs, _ = _WHISPER["model"].transcribe(audio, language="tr", vad_filter=True)
    return " ".join(s.text.strip() for s in segs).strip()


def http_json(url, body, headers=None, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}")
    except urllib.error.URLError as e:
        raise RuntimeError(t("err.no_connection", reason=e.reason))

def ask_ollama(url, model, system, history):
    j = http_json(url.rstrip("/") + "/api/chat", {"model": model, "stream": False,
                  "messages": [{"role": "system", "content": system}] + history}, timeout=180)
    return j["message"]["content"].strip()

def ask_claude(key, model, system, history):
    j = http_json("https://api.anthropic.com/v1/messages",
                  {"model": model, "max_tokens": 400, "system": system, "messages": history},
                  headers={"x-api-key": key, "anthropic-version": "2023-06-01"}, timeout=60)
    return "".join(b.get("text", "") for b in j["content"] if b.get("type") == "text").strip()

def ask_openai(key, model, system, history):
    j = http_json("https://api.openai.com/v1/chat/completions",
                  {"model": model, "max_tokens": 400, "messages": [{"role": "system", "content": system}] + history},
                  headers={"Authorization": f"Bearer {key}"}, timeout=60)
    return j["choices"][0]["message"]["content"].strip()


# ───────────── Claude Code (abonelik ile, API anahtarsız) ─────────────
# Resmi `claude` komut satırı aracını `claude -p` ile çağırır. Giriş, kullanıcının
# kendi Claude aboneliğiyle (Pro/Max) Claude Code içinde yapılır; bu program hiçbir
# giriş bilgisini okumaz veya saklamaz. Kullanım aboneliğin limitinden düşer.
# Calls the official `claude` CLI in print mode. Sign-in lives inside Claude Code;
# this app never reads or stores credentials.
CLAUDE_CODE_TIMEOUT = 150

def find_claude_cli():
    """claude.exe yolunu bulur: PATH, yerel kurulum (~/.local/bin), npm."""
    found = shutil.which("claude")
    if found:
        return found
    candidates = [Path.home() / ".local" / "bin" / "claude.exe",
                  Path.home() / ".local" / "bin" / "claude"]
    if os.environ.get("APPDATA"):
        candidates.append(Path(os.environ["APPDATA"]) / "npm" / "claude.cmd")
    for c in candidates:
        if c.exists():
            return str(c)
    return None

def _history_as_prompt(history):
    """Sohbet geçmişini tek bir metin istemine çevirir (claude -p tek mesaj alır)."""
    if len(history) == 1:
        return history[0]["content"]
    names = {"user": "User", "assistant": "Assistant"}
    lines = [f"{names.get(m['role'], m['role'])}: {m['content']}" for m in history[:-1]]
    return ("Conversation so far:\n" + "\n".join(lines) +
            "\n\nReply only to this latest user message:\n" + history[-1]["content"])

def ask_claude_code(model, system, history, timeout=CLAUDE_CODE_TIMEOUT):
    import subprocess
    exe = find_claude_cli()
    if not exe:
        raise RuntimeError(t("ai.cc_missing"))
    # Ayrı, boş bir çalışma klasörü: kullanıcının projelerindeki CLAUDE.md vb. yüklenmez.
    work = BASE / "logs" / "claude_code"
    work.mkdir(parents=True, exist_ok=True)
    sys_file = work / "system_prompt.txt"
    sys_file.write_text(system, encoding="utf-8")
    args = [exe, "-p", "--output-format", "json",
            "--system-prompt-file", str(sys_file),
            "--tools", "",                  # dosya/komut aracı yok: sadece cevap yazar
            "--disallowedTools", "mcp__*",
            "--strict-mcp-config",
            "--no-session-persistence",
            "--max-turns", "1"]
    if model:
        args += ["--model", model]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        proc = subprocess.run(args, input=_history_as_prompt(history), capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, cwd=str(work), creationflags=flags)
    except subprocess.TimeoutExpired:
        raise RuntimeError(t("ai.cc_timeout", s=timeout))
    out = (proc.stdout or "").strip()
    try:
        data = json.loads(out.splitlines()[-1]) if out else {}
    except (ValueError, IndexError):
        data = {}
    result = str(data.get("result", "")).strip()
    if proc.returncode != 0 or data.get("is_error") or not result:
        detail = result or (proc.stderr or out or f"exit {proc.returncode}").strip()[:300]
        log.warning("Claude Code call failed (exit %s): %s", proc.returncode, detail)
        if re.search(r"log ?in|logged|auth|credential|/login", detail, re.I):
            raise RuntimeError(t("ai.cc_login"))
        raise RuntimeError(detail)
    return result


# ───────────── Görev takibi / project tracking ─────────────
# Kategoriler diskte SABİT İNGİLİZCE KİMLİKLE saklanır, ekranda t() ile çevrilir;
# böylece dil değişince kayıtlı görevler yerinde kalır.
# Category IDs are stored on disk and never translated.
TASK_PATH = BASE / "tasks.json"
TASK_CATS = ["daily", "weekly", "journey", "global_event", "manhunt", "other"]
AUTO_RESET_CATS = {"daily", "weekly"}  # reset sınırı geçince otomatik temizlenir
# v4 ve öncesi Türkçe adlar kullanıyordu; eski tasks.json dosyaları taşınır.
LEGACY_CATS = {"Günlük": "daily", "Haftalık": "weekly", "Journey": "journey",
               "Global Event": "global_event", "Manhunt": "manhunt", "Diğer": "other"}

def cat_name(cid):
    """Kategori kimliğinin o anki dildeki görünen adı."""
    return t(f"cat.{cid}")

def weekday_names():
    return [t(f"weekday.{i}") for i in range(7)]

def load_tasks():
    try:
        d = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    items = d.get("items") or {}
    migrated = {}
    for key, val in items.items():                   # eski Türkçe adları kimliğe taşı
        migrated.setdefault(LEGACY_CATS.get(key, key), []).extend(val or [])
    d["items"] = {c: migrated.get(c, []) for c in TASK_CATS}
    for c, v in migrated.items():                    # tanınmayan kategori kaybolmasın
        if c not in d["items"]:
            d["items"]["other"].extend(v)
    d.setdefault("last_daily_key", ""); d.setdefault("last_weekly_key", "")
    return d

def save_tasks(d):
    TASK_PATH.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

def daily_period_key(now, reset_hour):
    return (now - timedelta(hours=reset_hour)).date().isoformat()

def weekly_period_key(now, reset_weekday, reset_hour):
    shifted = now - timedelta(hours=reset_hour)
    back = (shifted.weekday() - reset_weekday) % 7
    return (shifted - timedelta(days=back)).date().isoformat()

def next_daily_reset(now, reset_hour):
    cand = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
    return cand if cand > now else cand + timedelta(days=1)

def next_weekly_reset(now, reset_weekday, reset_hour):
    cand = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
    days = (reset_weekday - cand.weekday()) % 7
    cand = cand + timedelta(days=days)
    if cand <= now:
        cand += timedelta(days=7)
    return cand

def fmt_remaining(target, now):
    s = max(0, int((target - now).total_seconds()))
    h, s = divmod(s, 3600); m, _ = divmod(s, 60)
    d, h = divmod(h, 24)
    return (t("time.days", n=d) + " " if d else "") + t("time.hm", h=f"{h:02d}", m=f"{m:02d}")

def builtin_task_translate(text):
    """Sözlükle kaba çeviri. Seçili dilin __task_dict__ girdisi yoksa metni olduğu
    gibi döndürür — uydurma çeviri yapmaktansa orijinali göstermek daha dürüst."""
    pairs = i18n.task_dictionary()
    if not pairs:
        return text
    out = text
    for en, tr in sorted(pairs, key=lambda x: -len(x[0])):
        out = re.sub(re.escape(en), tr, out, flags=re.IGNORECASE)
    return out

def task_system_prompt():
    """Çeviri istemi, seçili dile göre kurulur."""
    lang = i18n.english_name()
    return (f"You translate The Division 2 project/mission texts from English into {lang}. "
            f"Write natural, short wording that players of the game would recognise. "
            f"Reply with the {lang} translation only — no explanation, no quotes, no extra comment. "
            f"Use the game's own {lang} terminology for things like Control Point, Stronghold, "
            f"Supply Drop, Dark Zone, Bounty, Seasonal Journey and Global Event where it exists.")

def translate_task_text(app, text):
    """AI varsa onunla, yoksa/başarısızsa sözlükle çevirir. (çeviri, kaynak) döner."""
    st = app.cfg["settings"]
    prov = st.get("ai_provider", "builtin")
    prompt, msg = task_system_prompt(), [{"role": "user", "content": text}]
    try:
        if prov == "ollama":
            return ask_ollama(st["ollama_url"], st["ollama_model"], prompt, msg), t("src.ai")
        if prov == "claude_code":
            return ask_claude_code(st.get("claude_code_model", ""), prompt, msg), t("src.ai")
        if prov == "claude":
            key = st.get("claude_api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
            if key: return ask_claude(key, st["claude_model"], prompt, msg), t("src.ai")
        if prov == "openai":
            key = st.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
            if key: return ask_openai(key, st["openai_model"], prompt, msg), t("src.ai")
    except Exception as e:
        log.warning("Task translation via %s failed: %s", prov, e)
    return builtin_task_translate(text), t("src.dict")


# ───────────── ChatGPT otomasyonu ─────────────
# NOT: Bu, kurulu ChatGPT uygulamana senin yerine yazıp Enter'a basan ve ekrandaki
# yanıtı OCR ile okuyan bir masaüstü makrosudur (klavye/pencere otomasyonu).
# ChatGPT'nin API'sine veya hesabına dokunmaz, OpenAI'ın sunucusuna bağlanmaz.
# Doğruluk tamamen ChatGPT'nin o an verdiği yanıta bağlıdır: model internete
# bakmıyorsa ya da TD2'nin güncel içeriğini bilmiyorsa EMİN OLMADIĞI BİLGİYİ
# UYDURABİLİR. Bu yüzden önemli görevlerde oyun içi metinle karşılaştır.
# Başlıklar her dilde SABİT İNGİLİZCE istenir, sadece görev metni çevrilir;
# böylece ayrıştırma dilden bağımsız çalışır.
# Headings are always requested in English so parsing works in every language.
GPT_HEADINGS = {"DAILY": "daily", "WEEKLY": "weekly", "JOURNEY": "journey",
                "GLOBAL EVENT": "global_event", "MANHUNT": "manhunt", "OTHER": "other"}
GPT_EMPTY_MARKERS = {"none", "-", "n/a", "yok", "aucun", "keine", "ninguno",
                     "nessuno", "nenhum", "нет", "brak", "なし", "没有", "없음"}

def default_gpt_prompt():
    """ChatGPT'ye gönderilecek hazır istek; yanıt kullanıcının dilinde istenir."""
    lang = i18n.english_name()
    return (
        "List the daily projects, weekly projects, current Season / Seasonal Journey steps, "
        "active Global Event objectives and any active Manhunt objectives that are live in "
        "Tom Clancy's The Division 2 today ({date}). For each one add a short note on how to complete it.\n"
        "Do not invent anything: if you cannot access current information or are unsure, write "
        "\"not sure about this\" instead of guessing.\n"
        f"Write the task text and the how-to notes in {lang}.\n"
        "Keep the section headings EXACTLY as below — English, capitals. "
        "Reply in this format only, with no other commentary:\n"
        "DAILY:\n- <task>: <how to do it>\n"
        "WEEKLY:\n- <task>: <how to do it>\n"
        "JOURNEY:\n- <task>: <how to do it>\n"
        "GLOBAL EVENT:\n- <task>: <how to do it>\n"
        "MANHUNT:\n- <task>: <how to do it>\n"
        "If a section has nothing active, put '- none' under it.")

def parse_gpt_answer(text):
    """Yanıtı kategori kimliklerine ayırır. Başlıkların İngilizce olması beklenir."""
    cur, out = "other", {c: [] for c in TASK_CATS}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        head = line.rstrip(":").strip().upper()
        hit = next((v for k, v in GPT_HEADINGS.items() if head == k or head.startswith(k + " ")), None)
        if hit:
            cur = hit; continue
        item = re.sub(r"^[-•*]\s*", "", line)
        item = re.sub(r"^\d+[.)]\s+", "", item).strip()
        if item and item.lower() not in GPT_EMPTY_MARKERS:
            out[cur].append(item)
    return out

def find_and_focus_window(title_hint):
    import pygetwindow as gw
    wins = [w for w in gw.getAllWindows() if title_hint.lower() in w.title.lower() and w.title.strip()]
    if not wins:
        raise RuntimeError(t("gpt.err.nowindow", title=title_hint))
    win = wins[0]
    try:
        if win.isMinimized: win.restore()
        win.activate()
    except Exception:
        pass
    return win

def type_and_send(text):
    from pynput.keyboard import Controller, Key
    kb = Controller()
    time.sleep(0.6)  # pencere odaklanması için kısa bekleme
    kb.type(text)
    time.sleep(0.2)
    kb.tap(Key.enter)


# ───────────── Uygulama ─────────────
class App:
    def __init__(self):
        if os.name == "nt":
            try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception: pass
        self.cfg = load_cfg()
        stg = self.cfg["settings"]
        setup_logging(stg.get("log_level", "INFO"), stg.get("log_max_kb", 1024), stg.get("log_backups", 3))
        log.info("=== %s v%s starting ===", APP_NAME, APP_VERSION)
        # Dil: ayarlardaki seçim, yoksa işletim sisteminin dili, o da yoksa İngilizce.
        i18n.init(BASE)
        chosen = stg.get("language") or i18n.detect_language()
        active = i18n.set_language(chosen)
        if active != chosen:
            log.warning("Language %r not found, using %r", chosen, active)
        if not stg.get("language"):
            stg["language"] = active; save_cfg(self.cfg)
        log.info("Language: %s (%s)", active, i18n.language_name(active))
        self.progress, self.tasks = load_progress(), load_tasks()
        self.tess = find_tesseract(self.cfg)
        self.listener, self.auto_stop, self.running = None, None, False
        self.lock, self.results = threading.Lock(), queue.Queue()
        self.counts = {"KEEP": 0, "CONSIDER": 0, "DISMANTLE": 0, "REVIEW": 0}
        self.overlay = self.overlay_job = self.cur = self.last_scan = None
        self.root_after_resets = None
        self.last_sig, self.last_time, self.last_err = None, 0, ""
        self.speaker, self.rec, self.voice_busy, self.chat_hist = Speaker(), Recorder(), False, []

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}"); self.root.geometry("1040x840"); self.root.minsize(880, 700)
        self.sounds = ui_theme.Sounds(BASE / "sounds", enabled=bool(stg.get("ui_sounds", True)))
        ui_theme.bind_click_sounds(self.root, self.sounds)
        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.meta_busy = False
        self.poll(); self.check_resets()
        self.root.after(2500, self.meta_sync_start)     # açılışı bekletmeden, günde bir
        log.info("UI ready — language=%s, tesseract=%s", i18n.current_language(), self.tess or "NOT FOUND")
        if not self.tess:
            messagebox.showwarning(APP_NAME, t("msg.no_tesseract"))

    def build_ui(self):
        """Tema + başlık bandı + tüm sekmeler. Tema/dil değişince rebuild_ui() ile yeniden kurulur."""
        set_palette(ui_theme.apply(self.root, self.cfg["settings"].get("ui_theme", "dark")))
        self.build_header()
        nb = self.nb = ttk.Notebook(self.root); nb.pack(fill="both", expand=True, padx=10, pady=(6, 10))
        # Sekmeler sabit kimliklerle tutulur, başlıkları t() ile çevrilir.
        self.tab_keys = ("dash", "builds", "progress", "stats", "tasks", "assistant", "settings", "history", "log", "help")
        self.tabs = {k: ttk.Frame(nb) for k in self.tab_keys}
        for k in self.tab_keys: nb.add(self.tabs[k], text=ui_theme.with_icon(t(f"tab.{k}"), ui_theme.TAB_ICONS.get(k, "")))
        self.build_dash(); self.build_builds(); self.build_prog(); self.build_stats(); self.build_gorevler(); self.build_asistan()
        self.build_settings(); self.build_hist(); self.build_logtab(); self.build_help()
        nb.bind("<<NotebookTabChanged>>", self.on_tab)

    def rebuild_ui(self, tab=None):
        """Yeniden başlatmadan arayüzü yeni tema/dille kurar.
        Tarama durumu, sayaçlar, son eşya ve sohbet korunur."""
        tab = tab or self.current_tab()
        was_running = self.running
        if was_running: self.stop(quiet=True)
        if self.overlay_job:
            try: self.root.after_cancel(self.overlay_job)
            except Exception: pass
            self.overlay_job = None
        if self.overlay:
            try: self.overlay.destroy()
            except Exception: pass
            self.overlay = None
        try: self.banner.destroy()
        except Exception: pass
        self.nb.destroy()
        # Yok edilen eski widget referanslarını temizle (hasattr kontrolleri yeni widget'ı beklesin)
        for k, v in list(vars(self).items()):
            if isinstance(v, tk.Misc) and v is not self.root:
                delattr(self, k)
        self.build_ui()
        if tab in self.tab_keys:
            self.nb.select(self.tab_keys.index(tab))
        if was_running: self.start(quiet=True)
        log.info("UI rebuilt (theme=%s, language=%s)", self.cfg["settings"].get("ui_theme"), i18n.current_language())

    def current_tab(self):
        """Seçili sekmenin kimliği (görünen adı değil)."""
        try:
            return self.tab_keys[self.nb.index(self.nb.select())]
        except Exception:
            return ""

    def build_header(self):
        """Üst bant: dönen arka planlar, marka ve durum rozetleri (ui_art.Banner)."""
        st = self.cfg["settings"]
        self.banner = ui_art.Banner(self.root, PAL, ART_DIR / "backgrounds", interval_s=st.get("bg_interval", 15),
                                    title="◆ TD2 LOOT ADVISOR", subtitle=f"v{APP_VERSION}")
        self.refresh_header()

    def toast(self, text):
        """Kısa onay mesajı (başlık bandında, pencere açmadan)."""
        try: self.banner.toast("✔ " + text)
        except Exception: messagebox.showinfo(APP_NAME, text)

    def flash_build(self, b):
        """Seçilen build'in amblemini bantta 5 sn gösterir."""
        try:
            sets = b.get("sets_or_brands", []) or []
            img = ui_art.emblem(b["name"], sets, ART_DIR / "emblems", size=320)
            self.banner.flash(img, b["name"], ", ".join(sets[:3]), ui_art.role_color(b["name"], sets), seconds=5)
        except Exception as e:
            log.debug("Emblem flash failed: %s", e)

    def flash_language(self, code):
        """Seçilen dilin bayrağını bantta 5 sn gösterir."""
        try:
            img = ui_art.flag(code, ART_DIR / "flags", height=240)
            if img is None: return
            self.banner.flash(img, i18n.language_name(code), code.upper(), PAL["accent"], seconds=5)
        except Exception as e:
            log.debug("Flag flash failed: %s", e)

    def refresh_header(self):
        if not hasattr(self, "banner"): return
        st = self.cfg["settings"]
        prov = st.get("ai_provider", "builtin")
        self.banner.set_chips([(("● " + t("state.running")) if self.running else ("○ " + t("state.stopped")),
                                "on" if self.running else "off"),
                               ("🤖 " + provider_label(prov if prov in PROVIDER_KEYS else "builtin"), "off")])

    def on_tab(self, _=None):
        if hasattr(self, "sounds"): self.sounds.play("tab")
        k = self.current_tab()
        if k == "history": self.load_history()
        elif k == "stats": self.root.after(50, self.refresh_stats_tab)
        elif k == "progress": self.refresh_prog()
        elif k == "log": self.refresh_logtab()

    # ---------- Panel ----------
    def build_dash(self):
        f = self.tabs["dash"]
        top = ttk.Frame(f); top.pack(fill="x", padx=12, pady=(14, 6))
        self.btn_run = ttk.Button(top, text=t("btn.start"), command=self.toggle, style="Success.TButton"); self.btn_run.pack(side="left")
        ttk.Button(top, text=t("btn.scan_now") if not t("btn.scan_now")[:1].isalnum() else "🔍 " + t("btn.scan_now"),
                   command=self.trigger, style="Accent.TButton").pack(side="left", padx=8)
        ttk.Button(top, text=ui_theme.with_icon(t("btn.pick_region"), "⛶"), command=self.calibrate).pack(side="left")
        ttk.Button(top, text=ui_theme.with_icon(t("btn.test_image"), "🖼"), command=self.test_image).pack(side="left", padx=8)
        mode = ttk.Frame(f); mode.pack(fill="x", padx=12, pady=(2, 0))
        ttk.Label(mode, text=t("panel.scan_mode"), foreground=PAL["muted"]).pack(side="left")
        self.mode_var = tk.StringVar(value=self.cfg["settings"]["scan_mode"])
        for txt, val in ((t("mode.hotkey"), "hotkey"), (t("mode.auto"), "auto")):
            ttk.Radiobutton(mode, text=txt, value=val, variable=self.mode_var, command=self.change_mode).pack(side="left", padx=8)
        self.status = ttk.Label(f, foreground=PAL["muted"]); self.status.pack(anchor="w", padx=14, pady=(4, 2))
        # Karar kartı
        card = ttk.Frame(f, style="Card.TFrame", padding=(0, 0, 0, 12)); card.pack(fill="x", padx=12, pady=(6, 8))
        self.verdict_lbl = tk.Label(card, text=verdict_label("IDLE"), bg=COLORS["IDLE"], fg="white",
                                    font=(ui_theme.FONT_SEMI, 30), pady=18)
        self.verdict_lbl.pack(fill="x")
        self.item_lbl = ttk.Label(card, text="—", style="Item.TLabel"); self.item_lbl.pack(anchor="w", padx=16, pady=(10, 0))
        self.note_lbl = ttk.Label(card, text="", style="Note.TLabel"); self.note_lbl.pack(anchor="w", padx=16)
        # Oturum sayaçları (renkli rozetler)
        chips = ttk.Frame(f); chips.pack(fill="x", padx=12, pady=(0, 4))
        self.count_chips = {}
        for v in ("KEEP", "CONSIDER", "DISMANTLE", "REVIEW"):
            lb = tk.Label(chips, bg=PAL["surface"], fg=VFG[v], font=(ui_theme.FONT_SEMI, 10), padx=12, pady=5)
            lb.pack(side="left", padx=(0, 8)); self.count_chips[v] = lb
        self.out = tk.Text(f, height=11, state="disabled", font=("Consolas", 10), wrap="word"); self.out.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.stats = ttk.Label(f)   # eski sayaç satırı (artık rozetlerde gösteriliyor)
        self.refresh_counts(); self.refresh_status()

    def refresh_status(self):
        r = self.cfg["settings"].get("region")
        st = self.cfg["settings"]
        mode = t("state.auto") if st["scan_mode"] == "auto" else t("state.key", key=st["hotkey"])
        self.status.config(text=t("status.line",
                                  state=t("state.running") if self.running else t("state.stopped"),
                                  mode=mode,
                                  region=f"{r['width']}x{r['height']}" if r else t("state.not_set")))
        self.refresh_header()

    def refresh_counts(self):
        c = self.counts
        self.stats.config(text=t("status.counts", keep=c["KEEP"], consider=c["CONSIDER"],
                                  dismantle=c["DISMANTLE"], review=c["REVIEW"]))
        for v, lb in getattr(self, "count_chips", {}).items():
            lb.config(text=f"{verdict_label(v)}  {c[v]}")

    def show_result(self, text, item, verdict, res, note=None, debug=False, diff=None):
        self.verdict_lbl.config(text=verdict_label(verdict), bg=COLORS[verdict])
        self.item_lbl.config(text=item["name"] + ("  [" + ", ".join(item["rarity"]) + "]" if item["rarity"] else "") +
                             (f"  ({item['slot']})" if item.get("slot") else ""))
        self.note_lbl.config(text=note or "")
        body = "\n".join(f"{p:3d}%  {n}\n        {', '.join(w) if w else '-'}" for p, n, w in res[:5])
        if diff:
            body += t("panel.roll_header") + "\n".join("  " + d for d in diff)
        if debug:
            body += t("panel.ocr_text") + text + t("panel.parsed") + json.dumps(item, ensure_ascii=False, indent=1)
        self.out.config(state="normal"); self.out.delete("1.0", "end"); self.out.insert("end", body); self.out.config(state="disabled")

    # ---------- çalıştırma ----------
    def change_mode(self):
        self.cfg["settings"]["scan_mode"] = self.mode_var.get(); save_cfg(self.cfg)
        if self.running:
            self.stop(); self.start()
        self.refresh_status()

    def toggle(self):
        self.stop() if self.running else self.start()

    def start(self, quiet=False):
        if not self.cfg["settings"].get("region"):
            return messagebox.showinfo(APP_NAME, t("msg.pick_region_first"))
        try:
            from pynput import keyboard
            hk = {self.cfg["settings"]["hotkey"]: self.trigger}
            vh = self.cfg["settings"].get("voice_hotkey")
            if vh and vh not in hk: hk[vh] = self.toggle_voice
            gh = self.cfg["settings"].get("chatgpt_hotkey")
            if gh and gh not in hk: hk[gh] = self.run_gpt_fetch
            self.listener = keyboard.GlobalHotKeys(hk)
            self.listener.start()
        except Exception as e:
            self.listener = None
            if self.cfg["settings"]["scan_mode"] == "hotkey":
                return messagebox.showerror(APP_NAME, t("err.hotkey_listener", e=e))
        if self.cfg["settings"]["scan_mode"] == "auto":
            self.auto_stop = threading.Event()
            threading.Thread(target=self.auto_loop, args=(self.auto_stop,), daemon=True).start()
        self.running = True; self.btn_run.config(text=t("btn.stop"), style="Danger.TButton"); self.refresh_status()
        if not quiet: self.sounds.play("start")
        log.info("Scanning started (mode=%s)", self.cfg["settings"]["scan_mode"])

    def stop(self, quiet=False):
        if self.listener: self.listener.stop(); self.listener = None
        if self.auto_stop: self.auto_stop.set(); self.auto_stop = None
        self.running = False; self.btn_run.config(text=t("btn.start"), style="Success.TButton"); self.refresh_status()
        if hasattr(self, "sounds") and not quiet: self.sounds.play("stop")
        log.info("Scanning stopped")

    def trigger(self):  # pynput thread'inden de çağrılır: tk'ya dokunma
        region = self.cfg["settings"].get("region")
        if region and not self.lock.locked():
            threading.Thread(target=self.manual_scan, args=(region,), daemon=True).start()

    def manual_scan(self, region):
        with self.lock:
            try:
                self.scan_image(grab(region), auto=False)
            except Exception as e:
                log.exception("Manual scan failed")
                self.results.put(("err", f"{type(e).__name__}: {e}"))

    def scan_image(self, img, auto):
        s = self.cfg["settings"]
        if s.get("save_debug_crop"):
            img.save(DEBUG_PATH)
        text = ocr(img, s["ocr_lang"])
        item, verdict, res = evaluate(text, self.cfg)
        sig = signature(item)
        if auto:
            if not valid_item(item): return
            if sig == self.last_sig and time.time() - self.last_time < DEDUP_SECONDS: return
        self.last_sig, self.last_time = sig, time.time()
        self.results.put(("ok", text, item, verdict, res, sig))

    def auto_loop(self, stop):
        prev = last_done = None; stable = 0
        while not stop.is_set():
            try:
                region = self.cfg["settings"].get("region")
                if region:
                    img = grab(region); h = thumb(img)
                    stable = stable + 1 if prev is not None and dist(h, prev) < AUTO_STABLE else 0
                    prev = h
                    if stable == 1 and (last_done is None or dist(h, last_done) >= AUTO_CHANGE):
                        last_done = h
                        with self.lock:
                            self.scan_image(img, auto=True)
            except Exception as e:
                msg = f"{type(e).__name__}: {e}"
                if msg != self.last_err:
                    self.last_err = msg; self.results.put(("err", msg))
            stop.wait(max(0.2, float(self.cfg["settings"]["auto_interval_ms"]) / 1000))

    def poll(self):
        try:
            while True:
                r = self.results.get_nowait()
                if r[0] == "err":
                    it = {"name": r[1][:60], "rarity": [], "attrs": {}, "talents": [], "slot": None}
                    self.show_result("", it, "ERROR", []); self.popup("ERROR", it, [], None)
                    continue
                if r[0] == "chat":
                    self.chat_add(r[1], r[2])
                    if r[1] == "asistan" and self.cfg["settings"].get("speak_chat"): self.speak(r[2])
                    continue
                if r[0] == "vstatus":
                    self.vstatus.config(text=r[1]); continue
                if r[0] == "voice":
                    self.vstatus.config(text=""); self.ask(r[1], voice=True); continue
                if r[0] == "tasks_added":
                    self.tasks["items"].setdefault(r[1], []).extend(r[2]); save_tasks(self.tasks)
                    self.task_in.delete("1.0", "end"); self.tr_status.config(text=t("task.added_src", n=len(r[2]), src=r[2][0]["src"]))
                    if self.selected_add_cat() == r[1] or self.selected_list_cat() == r[1]: self.refresh_tasks()
                    continue
                if r[0] == "gpt_status":
                    self.gpt_status.config(text=r[1]); continue
                if r[0] == "gpt_raw":
                    self.gpt_raw.config(state="normal"); self.gpt_raw.delete("1.0", "end"); self.gpt_raw.insert("end", r[1]); self.gpt_raw.config(state="disabled")
                    continue
                self.handle_result(*r[1:])
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def handle_result(self, text, item, verdict, res, sig):
        s, note, act, diff = self.cfg["settings"], None, None, None
        if s.get("track_progress"):
            verdict, note, act, diff = apply_progress(self.cfg, self.progress, item, verdict, res)
        self.last_scan = (item, res, sig)
        if act and s.get("auto_record"):
            self.record(act[0], act[1], act[2], item, sig)
            log.info("Progress: %s / %s <- %r (%s%%)", act[0], act[1], item["name"][:40], act[2])
        self.counts[verdict] += 1; self.refresh_counts()
        self.show_result(text, item, verdict, res, note, diff=diff)
        self.popup(verdict, item, res, note)
        if s.get("speak_verdict"): self.speak_verdict(verdict, item, res, note)
        elif s.get("sound"): self.sounds.play(verdict, force=True)
        if s.get("log_csv"): self.log(item, verdict, res)
        log.info("Scan: %r -> %s (%s %s%%) slot=%s", item["name"][:50], verdict,
                 res[0][1] if res else "-", res[0][0] if res else 0, item.get("slot") or "-")

    def record(self, bname, slot, score, item, sig):
        self.progress.setdefault(bname, {})[slot] = {"item": item["name"], "score": score, "sig": sig, "attrs": item.get("attrs", {}),
                                                     "time": datetime.now().isoformat(timespec="seconds")}
        save_progress(self.progress)
        if self.current_tab() == "progress": self.refresh_prog()

    def log(self, item, verdict, res):
        ensure_log()
        new = not LOG_PATH.exists()
        with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new: w.writerow(LOG_HEADER)
            b = res[0] if res else (0, "-", [])
            w.writerow([datetime.now().isoformat(timespec="seconds"), item["name"], verdict, b[1], b[0],
                        item.get("slot") or "", "/".join(item["rarity"])])

    # ---------- overlay ----------
    def popup(self, verdict, item, res, note):
        if self.overlay: self.overlay.destroy()
        w = self.overlay = tk.Toplevel(self.root)
        w.overrideredirect(True); w.attributes("-topmost", True, "-alpha", 0.94)
        col = COLORS[verdict]
        dark, fg, mu = "#14161b", "#eceef2", "#9aa1ae"   # oyun üstünde hep koyu kart
        w.configure(bg=dark)
        tk.Frame(w, bg=col, width=7).pack(side="left", fill="y")              # renkli şerit
        body = tk.Frame(w, bg=dark, padx=16, pady=12); body.pack(side="left", fill="both")
        tk.Label(body, text=verdict_label(verdict), fg=ui_theme.PALETTES["dark"]["verdict_fg"].get(verdict, fg),
                 bg=dark, font=(ui_theme.FONT_SEMI, 18)).pack(anchor="w")
        tk.Label(body, text=item["name"][:42], fg=fg, bg=dark, font=(ui_theme.FONT_SEMI, 11)).pack(anchor="w")
        L = []
        if item["rarity"]: L.append("[" + ", ".join(item["rarity"]) + "]")
        if note: L.append("» " + note)
        if verdict == "REVIEW": L.append(t("panel.rare_warning"))
        for p, n, _ in res[:3]:
            if p > 0: L.append(f"▸ {n}: {p}%")
        if res and res[0][2]: L.append("  " + ", ".join(res[0][2][:4]))
        if verdict == "DISMANTLE": L.append(t("panel.no_build_match"))
        if L:
            tk.Label(body, text="\n".join(L), justify="left", fg=mu, bg=dark, font=(ui_theme.FONT, 10)).pack(anchor="w", pady=(6, 0))
        w.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        c = self.cfg["settings"]["overlay_corner"]
        w.geometry(f"+{sw - w.winfo_width() - 30 if 'right' in c else 30}+{60 if 'top' in c else sh - w.winfo_height() - 80}")
        click_through(w)
        if self.overlay_job: self.root.after_cancel(self.overlay_job)
        self.overlay_job = self.root.after(int(float(self.cfg["settings"]["overlay_seconds"]) * 1000), w.destroy)

    # ---------- kalibrasyon / test ----------
    def calibrate(self):
        if not messagebox.askokcancel(APP_NAME, t("calib.ask_item")):
            return
        self.root.withdraw(); self.root.after(5000, self._calib_capture)

    def _calib_capture(self):
        with mss.mss() as sct:
            mon = sct.monitors[1]; s = sct.grab(mon); img = Image.frombytes("RGB", s.size, s.rgb)
        self.root.deiconify()
        w = tk.Toplevel(self.root); w.attributes("-fullscreen", True, "-topmost", True)
        cv = tk.Canvas(w, highlightthickness=0, cursor="crosshair"); cv.pack(fill="both", expand=True)
        w.update_idletasks()
        sw, sh = w.winfo_width(), w.winfo_height()
        scale = min(sw / img.width, sh / img.height)
        w._photo = ImageTk.PhotoImage(img.resize((int(img.width * scale), int(img.height * scale))))
        cv.create_image(0, 0, image=w._photo, anchor="nw")
        cv.create_text(sw // 2, 30, fill="yellow", font=("Segoe UI", 18, "bold"), text=t("calib.item_hint"))
        st = {}
        def down(e): st.update(x0=e.x, y0=e.y, r=cv.create_rectangle(e.x, e.y, e.x, e.y, outline="lime", width=3))
        def move(e): cv.coords(st["r"], st["x0"], st["y0"], e.x, e.y)
        def up(e):
            x1, x2 = sorted((st["x0"], e.x)); y1, y2 = sorted((st["y0"], e.y))
            if x2 - x1 < 30 or y2 - y1 < 30: return
            self.cfg["settings"]["region"] = {"left": mon["left"] + int(x1 / scale), "top": mon["top"] + int(y1 / scale),
                                              "width": int((x2 - x1) / scale), "height": int((y2 - y1) / scale)}
            save_cfg(self.cfg); w.destroy(); self.refresh_status()
        cv.bind("<ButtonPress-1>", down); cv.bind("<B1-Motion>", move); cv.bind("<ButtonRelease-1>", up)
        w.bind("<Escape>", lambda e: w.destroy()); w.focus_force()

    def test_image(self):
        p = filedialog.askopenfilename(filetypes=[(t("word.image"), "*.png *.jpg *.jpeg *.bmp")])
        if not p: return
        try:
            text = ocr(Image.open(p).convert("RGB"), self.cfg["settings"]["ocr_lang"])
            item, verdict, res = evaluate(text, self.cfg)
            self.show_result(text, item, verdict, res, debug=True)
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    # ---------- Build editörü ----------
    def build_builds(self):
        f = self.tabs["builds"]
        left = ttk.Frame(f); left.pack(side="left", fill="y", padx=8, pady=8)
        self.lb = tk.Listbox(left, width=30, exportselection=False); self.lb.pack(fill="y", expand=True)
        self.lb.bind("<<ListboxSelect>>", self.on_pick)
        ttk.Button(left, text=ui_theme.with_icon(t("build.new"), "➕"), command=self.new_build).pack(fill="x", pady=2)
        ttk.Button(left, text=ui_theme.with_icon(t("build.delete"), "🗑"), command=self.del_build).pack(fill="x")
        ttk.Separator(left).pack(fill="x", pady=6)
        ttk.Button(left, text=t("build.export"), command=self.export_builds).pack(fill="x")
        ttk.Button(left, text=t("build.import"), command=self.import_builds).pack(fill="x", pady=2)
        ttk.Separator(left).pack(fill="x", pady=6)
        ttk.Button(left, text=ui_theme.with_icon(t("meta.sync_now"), "⭐"), command=lambda: self.meta_sync_start(force=True, what=("builds",)),
                   style="Accent.TButton").pack(fill="x")
        self.meta_info = ttk.Label(left, text=self.meta_status_text(), foreground=PAL["muted"], wraplength=220, justify="left")
        self.meta_info.pack(fill="x", pady=(4, 0))
        r = ttk.Frame(f); r.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        self.v_name, self.v_sets, self.v_bonus, self.v_slots = (tk.StringVar() for _ in range(4))
        for i, (lab, var) in enumerate((("Ad", self.v_name), (t("build.sets"), self.v_sets), (t("build.set_bonus"), self.v_bonus),
                                        (t("build.slots"), self.v_slots))):
            ttk.Label(r, text=lab).grid(row=i, column=0, sticky="w"); ttk.Entry(r, textvariable=var, width=42).grid(row=i, column=1, sticky="w", pady=2)
        ttk.Label(r, text=t("build.attr_rules")).grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.ta = ttk.Treeview(r, columns=("k", "w", "g"), show="headings", height=6)
        for c, hd in (("k", t("build.attr")), ("w", t("build.weight")), ("g", t("build.goodval"))): self.ta.heading(c, text=hd); self.ta.column(c, width=110)
        self.ta.grid(row=5, column=0, columnspan=2, sticky="ew"); self.ta.bind("<<TreeviewSelect>>", self.pick_attr)
        af = ttk.Frame(r); af.grid(row=6, column=0, columnspan=2, sticky="w", pady=3)
        self.v_ak, self.v_aw, self.v_ag = tk.StringVar(), tk.StringVar(value="1"), tk.StringVar(value="5")
        ttk.Combobox(af, textvariable=self.v_ak, width=18, values=list(self.cfg["attributes"])).pack(side="left")
        ttk.Entry(af, textvariable=self.v_aw, width=6).pack(side="left", padx=4); ttk.Entry(af, textvariable=self.v_ag, width=6).pack(side="left")
        ttk.Button(af, text=ui_theme.with_icon(t("btn.add_update"), "✚"), command=self.set_attr).pack(side="left", padx=4); ttk.Button(af, text=ui_theme.with_icon(t("btn.delete"), "🗑"), command=self.del_attr).pack(side="left")
        ttk.Label(r, text=t("build.talents")).grid(row=7, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.tt = ttk.Treeview(r, columns=("n", "w"), show="headings", height=5)
        self.tt.heading("n", text=t("build.talent")); self.tt.heading("w", text=t("build.weight")); self.tt.column("n", width=220); self.tt.column("w", width=80)
        self.tt.grid(row=8, column=0, columnspan=2, sticky="ew"); self.tt.bind("<<TreeviewSelect>>", self.pick_tal)
        tf = ttk.Frame(r); tf.grid(row=9, column=0, columnspan=2, sticky="w", pady=3)
        self.v_tn, self.v_tw = tk.StringVar(), tk.StringVar(value="2")
        ttk.Entry(tf, textvariable=self.v_tn, width=26).pack(side="left"); ttk.Entry(tf, textvariable=self.v_tw, width=6).pack(side="left", padx=4)
        ttk.Button(tf, text=ui_theme.with_icon(t("btn.add_update"), "✚"), command=self.set_tal).pack(side="left"); ttk.Button(tf, text=ui_theme.with_icon(t("btn.delete"), "🗑"), command=self.del_tal).pack(side="left", padx=4)
        ttk.Button(r, text=t("btn.save"), command=self.save_build, style="Accent.TButton").grid(row=10, column=0, sticky="w", pady=12)
        self.meta_detail = ttk.Label(r, text="", foreground=PAL["muted"], wraplength=560, justify="left")
        self.meta_detail.grid(row=11, column=0, columnspan=2, sticky="w")
        self.refresh_builds()

    def export_builds(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="td2_builds_export.json", filetypes=[("JSON", "*.json")])
        if not path: return
        try:
            Path(path).write_text(json.dumps({"builds": self.cfg["builds"]}, indent=2, ensure_ascii=False), encoding="utf-8")
            messagebox.showinfo(APP_NAME, t("build.exported", n=len(self.cfg["builds"]), path=path))
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    def import_builds(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path: return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            incoming = data.get("builds", data) if isinstance(data, dict) else data
            if not isinstance(incoming, list): raise ValueError(t("build.import_bad"))
        except Exception as e:
            return messagebox.showerror(APP_NAME, t("err.file_read", e=e))
        existing = {b["name"] for b in self.cfg["builds"]}
        for b in incoming:
            b.setdefault("sets_or_brands", []); b.setdefault("set_bonus", 0); b.setdefault("attributes", {}); b.setdefault("talents", {})
            base, i, name = b.get("name", t("word.unnamed")), 2, b.get("name", t("word.unnamed"))
            while name in existing:
                name = f"{base} ({i})"; i += 1
            b["name"] = name; existing.add(name); self.cfg["builds"].append(b)
        save_cfg(self.cfg); self.refresh_builds(len(self.cfg["builds"]) - 1)
        messagebox.showinfo(APP_NAME, t("build.imported", n=len(incoming)))

    def refresh_builds(self, select=0):
        self.lb.delete(0, "end")
        for b in self.cfg["builds"]: self.lb.insert("end", self.build_label(b))
        if self.cfg["builds"]:
            self.lb.selection_set(min(select, len(self.cfg["builds"]) - 1)); self.on_pick()
        if hasattr(self, "pb"): self.pb["values"] = [b["name"] for b in self.cfg["builds"]]

    @staticmethod
    def build_label(b):
        """Listede görünen ad: ⭐ meta, 🔒 düzenlenmiş meta, 🔥 popülerlik."""
        if not b.get("meta_id"): return b["name"]
        pop = b.get("meta", {}).get("popularity", 0)
        return f"{'🔒' if b.get('meta_locked') else '⭐'} {b['name']}" + (f"  🔥{pop}" if pop else "")

    def on_pick(self, event=None):
        s = self.lb.curselection()
        if not s: return
        self.cur = self.cfg["builds"][s[0]]
        if event is not None: self.flash_build(self.cur)   # kullanıcı tıkladıysa amblem 5 sn
        self.v_name.set(self.cur["name"]); self.v_sets.set(", ".join(self.cur["sets_or_brands"]))
        self.v_bonus.set(str(self.cur.get("set_bonus", 0))); self.v_slots.set(", ".join(self.cur.get("slots", [])))
        self.refresh_trees()
        if hasattr(self, "meta_detail"): self.meta_detail.config(text=self.meta_detail_text(self.cur))

    def meta_detail_text(self, b):
        if not b.get("meta_id"): return ""
        m = b.get("meta", {})
        lang = i18n.current_language()
        summ = m.get("summary", {})
        line = summ.get(lang) or summ.get("en") or ""
        src = ", ".join(x["title"] or x["url"] for x in m.get("sources", [])[:3])
        parts = [t("meta.detail", mode=m.get("mode") or "—", pop=m.get("popularity", 0))]
        if line: parts.append(line)
        if src: parts.append(t("meta.sources", src=src))
        if b.get("meta_locked"): parts.append(t("meta.locked"))
        return "\n".join(parts)

    def refresh_trees(self):
        self.ta.delete(*self.ta.get_children()); self.tt.delete(*self.tt.get_children())
        for k, r in self.cur["attributes"].items(): self.ta.insert("", "end", values=(k, r["weight"], r["good_at"]))
        for n, w in self.cur["talents"].items(): self.tt.insert("", "end", values=(n, w))

    def pick_attr(self, _=None):
        s = self.ta.selection()
        if s:
            v = self.ta.item(s[0])["values"]; self.v_ak.set(v[0]); self.v_aw.set(v[1]); self.v_ag.set(v[2])

    def pick_tal(self, _=None):
        s = self.tt.selection()
        if s: self.v_tn.set(self.tt.item(s[0])["values"][0]); self.v_tw.set(self.tt.item(s[0])["values"][1])

    def set_attr(self):
        try: self.cur["attributes"][self.v_ak.get()] = {"weight": float(self.v_aw.get()), "good_at": float(self.v_ag.get())}
        except ValueError: return messagebox.showerror(APP_NAME, t("build.err_weight_val"))
        self.refresh_trees()

    def del_attr(self):
        self.cur["attributes"].pop(self.v_ak.get(), None); self.refresh_trees()

    def set_tal(self):
        try: self.cur["talents"][self.v_tn.get().strip()] = float(self.v_tw.get())
        except ValueError: return messagebox.showerror(APP_NAME, t("build.err_weight"))
        self.refresh_trees()

    def del_tal(self):
        self.cur["talents"].pop(self.v_tn.get().strip(), None); self.refresh_trees()

    def new_build(self):
        self.cfg["builds"].append({"name": t("build.new_name"), "sets_or_brands": [], "set_bonus": 0, "attributes": {}, "talents": {}})
        self.refresh_builds(len(self.cfg["builds"]) - 1)

    def del_build(self):
        s = self.lb.curselection()
        if s and messagebox.askyesno(APP_NAME, t("build.delete_confirm")):
            mid = self.cfg["builds"][s[0]].get("meta_id")
            if mid:   # silinen meta build bir sonraki senkronda geri gelmesin
                hid = self.cfg["settings"].setdefault("meta_hidden", [])
                if mid not in hid: hid.append(mid)
            del self.cfg["builds"][s[0]]; save_cfg(self.cfg); self.refresh_builds()

    def save_build(self):
        s = self.lb.curselection()
        if not s: return
        try: bonus = float(self.v_bonus.get() or 0)
        except ValueError: return messagebox.showerror(APP_NAME, t("build.err_bonus"))
        slots = [x.strip().capitalize() for x in self.v_slots.get().split(",") if x.strip()]
        bad = [x for x in slots if x not in ALL_SLOTS]
        if bad: return messagebox.showerror(APP_NAME, t("build.bad_slot", bad=bad, valid=", ".join(ALL_SLOTS)))
        old = self.cur["name"]; new = self.v_name.get().strip() or t("word.unnamed")
        self.cur.update(name=new, set_bonus=bonus, sets_or_brands=[x.strip() for x in self.v_sets.get().split(",") if x.strip()])
        if slots: self.cur["slots"] = slots
        else: self.cur.pop("slots", None)
        if self.cur.get("meta_id"): self.cur["meta_locked"] = True   # artık senkron bu build'i değiştirmez
        if old != new and old in self.progress:
            self.progress[new] = self.progress.pop(old); save_progress(self.progress)
        save_cfg(self.cfg); self.refresh_builds(s[0]); messagebox.showinfo(APP_NAME, t("msg.saved"))

    # ---------- Eksik parça takibi ----------
    def build_prog(self):
        f = self.tabs["progress"]
        bar = ttk.Frame(f); bar.pack(fill="x", padx=10, pady=10)
        ttk.Label(bar, text=t("label.build")).pack(side="left")
        self.pb = ttk.Combobox(bar, state="readonly", width=40, values=[b["name"] for b in self.cfg["builds"]])
        self.pb.pack(side="left", padx=6); self.pb.bind("<<ComboboxSelected>>", lambda e: self.refresh_prog())
        if self.cfg["builds"]: self.pb.current(0)
        self.pg_lbl = ttk.Label(f, style="Section.TLabel"); self.pg_lbl.pack(anchor="w", padx=12)
        self.pbar = ttk.Progressbar(f, maximum=100); self.pbar.pack(fill="x", padx=12, pady=6)
        self.tp = ttk.Treeview(f, columns=("s", "d", "i", "k"), show="headings", height=8)
        for c, hd, w in (("s", t("col.slot"), 100), ("d", t("col.status"), 100), ("i", t("col.item"), 320), ("k", t("col.score"), 70)): self.tp.heading(c, text=hd); self.tp.column(c, width=w)
        self.tp.tag_configure("miss", foreground=PAL["danger"]); self.tp.tag_configure("ok", foreground=PAL["success"])
        self.tp.pack(fill="x", padx=12)
        b2 = ttk.Frame(f); b2.pack(fill="x", padx=12, pady=8)
        ttk.Button(b2, text=ui_theme.with_icon(t("prog.save_last"), "📥"), command=self.save_last_scan).pack(side="left")
        ttk.Button(b2, text=ui_theme.with_icon(t("prog.clear_slot"), "✖"), command=self.clear_slot).pack(side="left", padx=6)
        ttk.Button(b2, text=ui_theme.with_icon(t("prog.reset_build"), "↺"), command=self.reset_build_prog).pack(side="left")
        self.miss_lbl = tk.Text(f, height=9, state="disabled", font=("Segoe UI", 10)); self.miss_lbl.pack(fill="both", expand=True, padx=12, pady=(4, 10))
        self.refresh_prog()

    def refresh_prog(self):
        self.tp.delete(*self.tp.get_children())
        name = self.pb.get()
        if not name: return
        slots = build_slots(self.cfg, name); prog = self.progress.get(name, {}); have = 0
        for s in slots:
            d = prog.get(s)
            have += bool(d)
            self.tp.insert("", "end", iid=s, values=(slot_name(s), t("prog.filled") if d else t("prog.empty"), d["item"] if d else "—", f"{d['score']}%" if d else ""),
                           tags=("ok" if d else "miss",))
        self.pg_lbl.config(text=t("prog.completed", have=have, total=len(slots)))
        self.pbar["value"] = 100 * have / max(len(slots), 1)
        lines = []
        for b in self.cfg["builds"]:
            sl = build_slots(self.cfg, b["name"]); miss = [s for s in sl if s not in self.progress.get(b["name"], {})]
            lines.append(f"{b['name']}: " + (", ".join(slot_name(x) for x in miss) if miss else t("prog.done_all")) + f"   ({len(sl) - len(miss)}/{len(sl)})")
        self.miss_lbl.config(state="normal"); self.miss_lbl.delete("1.0", "end")
        self.miss_lbl.insert("end", t("prog.all_missing") + "\n".join(lines)); self.miss_lbl.config(state="disabled")

    def save_last_scan(self):
        if not self.last_scan: return messagebox.showinfo(APP_NAME, t("prog.no_scan_yet"))
        item, res, sig = self.last_scan
        name = self.pb.get()
        if not item.get("slot"): return messagebox.showinfo(APP_NAME, t("prog.no_slot"))
        sc = next((p for p, n, _ in res if n == name), 0)
        self.record(name, item["slot"], sc, item, sig); self.refresh_prog()

    def clear_slot(self):
        s = self.tp.selection()
        if s and self.progress.get(self.pb.get(), {}).pop(s[0], None) is not None:
            save_progress(self.progress); self.refresh_prog()

    def reset_build_prog(self):
        if messagebox.askyesno(APP_NAME, t("prog.reset_confirm")):
            self.progress.pop(self.pb.get(), None); save_progress(self.progress); self.refresh_prog()

    # ---------- İstatistik ----------
    def build_stats(self):
        f = self.tabs["stats"]
        bar = ttk.Frame(f); bar.pack(fill="x", padx=10, pady=10)
        ttk.Label(bar, text=t("label.period")).pack(side="left")
        self.sp = ttk.Combobox(bar, state="readonly", width=14, values=[t("period.today"), t("period.7d"), t("period.30d"), t("period.all")]); self.sp.current(1)
        self.sp.pack(side="left", padx=6); self.sp.bind("<<ComboboxSelected>>", lambda e: self.refresh_stats_tab())
        ttk.Button(bar, text=ui_theme.with_icon(t("btn.refresh"), "⟳"), command=self.refresh_stats_tab).pack(side="left")
        self.sum_lbl = ttk.Label(f, style="Section.TLabel"); self.sum_lbl.pack(anchor="w", padx=12)
        grid = ttk.Frame(f); grid.pack(fill="both", expand=True, padx=8, pady=6)
        self.cvs = []
        for i in range(4):
            cv = tk.Canvas(grid, height=230, bg=PAL["surface"], highlightthickness=1, highlightbackground=PAL["border"])
            cv.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4); self.cvs.append(cv)
        for c in (0, 1): grid.columnconfigure(c, weight=1)
        for r in (0, 1): grid.rowconfigure(r, weight=1)

    def refresh_stats_tab(self):
        rows, per = read_log(), self.sp.get()
        days = {t("period.today"): 0, t("period.7d"): 6, t("period.30d"): 29}.get(per)
        if days is not None:
            since = (datetime.now() - timedelta(days=days)).replace(hour=0, minute=0, second=0)
            rows = [r for r in rows if r["time"] and datetime.fromisoformat(r["time"]) >= since]
        n = len(rows); keep = sum(r["verdict"] == "KEEP" for r in rows)
        scores = [float(r["score"]) for r in rows if r["score"]]
        rare = sum(bool({"EXOTIC", "NAMED", "PROTOTYPE"} & set(r["rarity"].split("/"))) for r in rows)
        self.sum_lbl.config(text=t("stats.summary", total=n,
                                   keep_pct=round(100 * keep / n) if n else 0,
                                   avg=round(sum(scores) / len(scores)) if scores else 0,
                                   rare=rare))
        vc = Counter(r["verdict"] for r in rows)
        draw_bars(self.cvs[0], t("stats.verdicts"), [(verdict_label(v), vc.get(v, 0), COLORS[v]) for v in ("KEEP", "CONSIDER", "DISMANTLE", "REVIEW")])
        bc = Counter(r["best_build"] for r in rows if r["verdict"] == "KEEP").most_common(6)
        draw_bars(self.cvs[1], t("stats.by_build"), [(b, c, PAL["success"]) for b, c in bc])
        today = datetime.now().date(); dc = Counter(r["time"][:10] for r in rows if r["time"])
        draw_bars(self.cvs[2], t("stats.daily_scans"), [((today - timedelta(days=d)).strftime("%d.%m"), dc.get(str(today - timedelta(days=d)), 0), PAL["info"]) for d in range(6, -1, -1)])
        sc_ = Counter(r["slot"] for r in rows if r["slot"])
        draw_bars(self.cvs[3], t("stats.by_slot"), [(s, sc_.get(s, 0), PAL["accent"]) for s in ALL_SLOTS])

    # ---------- Asistan ----------
    def build_asistan(self):
        f, st = ui_theme.scrollable(self.tabs["assistant"], PAL["bg"]), self.cfg["settings"]
        self.chat = tk.Text(f, height=13, state="disabled", wrap="word", font=("Segoe UI", 10))
        self.chat.tag_configure("user", foreground=PAL["accent"], font=(ui_theme.FONT_SEMI, 10))
        self.chat.tag_configure("asistan", foreground=PAL["fg"], spacing3=4)
        self.chat.tag_configure("sys", foreground=PAL["muted"])
        self.chat.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        row = ttk.Frame(f); row.pack(fill="x", padx=10)
        self.chat_in = ttk.Entry(row); self.chat_in.pack(side="left", fill="x", expand=True)
        self.chat_in.bind("<Return>", lambda e: self.send_chat())
        ttk.Button(row, text=ui_theme.with_icon(t("btn.send"), "➤"), command=self.send_chat, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(row, text=t("ai.talk"), command=self.toggle_voice).pack(side="left")
        ttk.Button(row, text=ui_theme.with_icon(t("btn.clear"), "🧹"), command=self.clear_chat).pack(side="left", padx=4)
        self.vstatus = ttk.Label(f, text="", foreground=PAL["warning"]); self.vstatus.pack(anchor="w", padx=12)

        box = ttk.LabelFrame(f, text=t("ai.settings")); box.pack(fill="x", padx=10, pady=8)
        self.av = {k: tk.StringVar(value=str(st.get(k, ""))) for k in
                   ("ollama_url", "ollama_model", "claude_code_model", "claude_model", "claude_api_key", "openai_model", "openai_api_key",
                    "stt_model", "stt_device", "tts_rate", "tts_voice", "voice_hotkey")}
        self.av["ai_provider"] = tk.StringVar(value=provider_label(st["ai_provider"] if st["ai_provider"] in PROVIDER_KEYS else "ollama"))
        self.abv = {k: tk.BooleanVar(value=bool(st.get(k, True))) for k in ("speak_verdict", "speak_chat")}
        ttk.Label(box, text=t("ai.provider")).grid(row=0, column=0, sticky="w", padx=8, pady=3)
        ttk.Combobox(box, textvariable=self.av["ai_provider"], values=[provider_label(k) for k in PROVIDER_KEYS], state="readonly", width=30).grid(row=0, column=1, sticky="w")
        fields = [(t("ai.ollama_url"), "ollama_url", 30), (t("ai.ollama_model"), "ollama_model", 30),
                  (t("ai.cc_model"), "claude_code_model", 30), (t("ai.claude_model"), "claude_model", 30),
                  (t("ai.claude_key"), "claude_api_key", 30), (t("ai.openai_model"), "openai_model", 30), (t("ai.openai_key"), "openai_api_key", 30),
                  (t("ai.stt_model"), "stt_model", 12), (t("ai.stt_device"), "stt_device", 12),
                  (t("ai.tts_rate"), "tts_rate", 12), (t("ai.tts_voice"), "tts_voice", 12), (t("ai.voice_hotkey"), "voice_hotkey", 12)]
        for i, (lab, k, w) in enumerate(fields, start=1):
            ttk.Label(box, text=lab).grid(row=i, column=0, sticky="w", padx=8, pady=2)
            ttk.Entry(box, textvariable=self.av[k], width=w, show="*" if k in ("claude_api_key", "openai_api_key") else "").grid(row=i, column=1, sticky="w")
        ttk.Checkbutton(box, text=t("ai.speak_verdict"), variable=self.abv["speak_verdict"]).grid(row=1, column=2, sticky="w", padx=16)
        ttk.Checkbutton(box, text=t("ai.speak_chat"), variable=self.abv["speak_chat"]).grid(row=2, column=2, sticky="w", padx=16)
        ttk.Button(box, text=t("ai.test_voice"), command=lambda: self.speak(t("ai.voice_test"))).grid(row=3, column=2, sticky="w", padx=16)
        ttk.Button(box, text=t("btn.save"), command=self.save_ai_settings, style="Accent.TButton").grid(row=4, column=2, sticky="w", padx=16)
        ttk.Label(box, text=t("ai.key_warning"),
                 foreground=PAL["muted"]).grid(row=len(fields) + 1, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 0))
        self.chat_add("sys", t("ai.examples"))
        for m in getattr(self, "chat_hist", []):           # arayüz yeniden kurulduysa sohbeti geri yaz
            self.chat_add("user" if m["role"] == "user" else "asistan", m["content"])

    def chat_add(self, role, text):
        self.chat.config(state="normal")
        who = {"user": "Sen", "asistan": "Asistan", "sys": "•"}[role]
        self.chat.insert("end", f"{who}: {text}\n\n", role)
        self.chat.see("end"); self.chat.config(state="disabled")

    def clear_chat(self):
        self.chat_hist = []
        self.chat.config(state="normal"); self.chat.delete("1.0", "end"); self.chat.config(state="disabled")

    def send_chat(self):
        txt = self.chat_in.get().strip()
        if txt:
            self.chat_in.delete(0, "end"); self.ask(txt)

    def speak(self, text):
        st = self.cfg["settings"]
        try: rate = int(float(st.get("tts_rate", 185)))
        except ValueError: rate = 185
        self.speaker.say(text, rate, st.get("tts_voice", ""))

    def speak_verdict(self, verdict, item, res, note):
        if verdict == "ERROR": return
        parts = [verdict_label(verdict).capitalize()]
        if verdict == "REVIEW":
            parts.append(t("speak.rare"))
        elif res and res[0][0] > 0:
            parts.append(t("speak.build_pct", build=res[0][1].split(" (")[0], pct=res[0][0]))
        if item.get("slot") and verdict in ("KEEP", "CONSIDER"):
            parts.append(slot_name(item["slot"]))
        if note:
            parts.append({t("prog.fills_gap"): t("speak.fills_gap"), t("prog.upgrade"): t("speak.upgrade"),
                          t("prog.yours_better"): t("speak.yours_better"), t("prog.already"): t("speak.already")}.get(note.split(":")[0], ""))
        self.speak(". ".join(p for p in parts if p))

    def build_context(self):
        builds = [{"ad": b["name"], "set": b["sets_or_brands"], "slotlar": b.get("slots") or ALL_SLOTS,
                   "attribute_agirlik": {k: v["weight"] for k, v in b["attributes"].items()}, "talent": b["talents"]} for b in self.cfg["builds"]]
        prog = {b["name"]: {s: {"esya": d["item"], "skor": d["score"], "attribute": d.get("attrs", {})} for s, d in self.progress.get(b["name"], {}).items()} for b in self.cfg["builds"]}
        eksik = {b["name"]: [s for s in build_slots(self.cfg, b["name"]) if s not in self.progress.get(b["name"], {})] for b in self.cfg["builds"]}
        last = None
        if self.last_scan:
            it, res, _ = self.last_scan
            last = {"ad": it["name"], "slot": it.get("slot"), "nadirlik": it["rarity"], "attribute": it["attrs"], "talent": it["talents"],
                    "en_uyumlu": [{"build": n, "skor": p} for p, n, _ in res[:3]]}
        hist = [{"esya": r["item"], "karar": r["verdict"], "build": r["best_build"], "skor": r["score"], "slot": r["slot"]} for r in read_log()[-15:]]
        return json.dumps({"buildler": builds, "kayitli_parcalar": prog, "eksik_slotlar": eksik, "son_taranan_esya": last,
                           "son_taramalar": hist, "oturum_sayaclari": self.counts}, ensure_ascii=False, separators=(",", ":"))

    def quick_answer(self, text):
        """Yapay zeka yokken çalışan basit yanıtlar. Anahtar kelimeler dil
        dosyasından gelir (kw.missing / kw.stats / kw.last), böylece her dilde çalışır."""
        low = text.lower()
        def hit(key):
            return any(w.strip() and w.strip() in low for w in t(key).split("|"))
        if hit("kw.missing"):
            out = []
            for b in self.cfg["builds"]:
                miss = [slot_name(s) for s in build_slots(self.cfg, b["name"])
                        if s not in self.progress.get(b["name"], {})]
                out.append(f"{b['name'].split(' (')[0]}: " + (", ".join(miss) if miss else t("word.complete")))
            return ". ".join(out)
        if hit("kw.stats"):
            rows = read_log()
            return t("quick.stats", total=len(rows), keep=sum(r["verdict"] == "KEEP" for r in rows))
        if hit("kw.last") and self.last_scan:
            it, res, _ = self.last_scan
            if res:
                return t("quick.last", item=it["name"], build=res[0][1].split(" (")[0], pct=res[0][0])
            return t("quick.last_plain", item=it["name"])
        return t("quick.help")

    def ask(self, text, voice=False):
        self.chat_add("user", text)
        st, ctx = self.cfg["settings"], self.build_context()
        self.chat_hist = (getattr(self, "chat_hist", []) + [{"role": "user", "content": text}])[-10:]
        hist, prov = list(self.chat_hist), st["ai_provider"]
        system = system_prompt() + t("ai.context_header") + ctx
        def work():
            try:
                if prov == "ollama":
                    ans = ask_ollama(st["ollama_url"], st["ollama_model"], system, hist)
                elif prov == "claude_code":
                    ans = ask_claude_code(st.get("claude_code_model", ""), system, hist)
                elif prov == "claude":
                    key = st.get("claude_api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
                    if not key: raise RuntimeError(t("ai.no_key"))
                    ans = ask_claude(key, st["claude_model"], system, hist)
                elif prov == "openai":
                    key = st.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
                    if not key: raise RuntimeError(t("ai.no_key"))
                    ans = ask_openai(key, st["openai_model"], system, hist)
                else:
                    ans = self.quick_answer(text)
                self.chat_hist.append({"role": "assistant", "content": ans})
            except Exception as e:
                self.results.put(("chat", "sys", t("ai.failed", e=e)))
                ans = self.quick_answer(text)
            self.results.put(("chat", "asistan", ans))
        threading.Thread(target=work, daemon=True).start()

    # ---------- sesli komut ----------
    def toggle_voice(self):  # pynput thread'inden de çağrılır: tk'ya dokunma
        try:
            if not self.rec.active:
                self.rec.start()
                self.results.put(("vstatus", t("ai.listening")))
                threading.Timer(15, lambda: self.rec.active and self.finish_voice()).start()
            else:
                self.finish_voice()
        except Exception as e:
            self.results.put(("vstatus", t("err.mic", e=e)))

    def finish_voice(self):
        if self.voice_busy: return
        self.voice_busy = True
        def work():
            try:
                audio = self.rec.stop()
                if len(audio) < 8000:
                    return self.results.put(("vstatus", t("ai.too_short")))
                self.results.put(("vstatus", t("ai.transcribing")))
                text = transcribe(audio, self.cfg)
                self.results.put(("voice", text) if text else ("vstatus", t("ai.not_understood")))
            except Exception as e:
                self.results.put(("vstatus", t("err.stt", e=e)))
            finally:
                self.voice_busy = False
        threading.Thread(target=work, daemon=True).start()

    def save_ai_settings(self):
        st = self.cfg["settings"]
        try:
            from pynput import keyboard
            keyboard.HotKey.parse(self.av["voice_hotkey"].get())
            st["tts_rate"] = int(float(self.av["tts_rate"].get()))
        except Exception as e:
            return messagebox.showerror(APP_NAME, t("err.bad_setting", e=e))
        st["ai_provider"] = next((k for k in PROVIDER_KEYS if provider_label(k) == self.av["ai_provider"].get()), "ollama")
        for k in ("ollama_url", "ollama_model", "claude_code_model", "claude_model", "claude_api_key", "openai_model", "openai_api_key",
                  "stt_model", "stt_device", "tts_voice", "voice_hotkey"):
            st[k] = self.av[k].get().strip()
        for k, v in self.abv.items(): st[k] = v.get()
        save_cfg(self.cfg)
        if self.running: self.stop(quiet=True); self.start(quiet=True)
        self.refresh_header()
        self.toast(t("ai.saved"))

    # ---------- Görevler (Günlük/Haftalık/Journey/Global Event/Manhunt) ----------
    def build_gorevler(self):
        f, st = ui_theme.scrollable(self.tabs["tasks"], PAL["bg"]), self.cfg["settings"]
        top = ttk.LabelFrame(f, text=t("task.reset_box")); top.pack(fill="x", padx=10, pady=10)
        self.reset_lbl = ttk.Label(top, style="Section.TLabel"); self.reset_lbl.pack(anchor="w", padx=8, pady=4)
        rr = ttk.Frame(top); rr.pack(fill="x", padx=8, pady=(0, 6))
        self.rv = {"daily_reset_hour": tk.StringVar(value=str(st["daily_reset_hour"])),
                   "weekly_reset_day": tk.StringVar(value=weekday_names()[st["weekly_reset_day"]]),
                   "weekly_reset_hour": tk.StringVar(value=str(st["weekly_reset_hour"]))}
        ttk.Label(rr, text=t("task.daily_hour")).pack(side="left")
        ttk.Entry(rr, textvariable=self.rv["daily_reset_hour"], width=4).pack(side="left", padx=(2, 12))
        ttk.Label(rr, text=t("task.weekly_day")).pack(side="left")
        ttk.Combobox(rr, textvariable=self.rv["weekly_reset_day"], values=weekday_names(), width=10, state="readonly").pack(side="left", padx=2)
        ttk.Label(rr, text=t("task.hour")).pack(side="left")
        ttk.Entry(rr, textvariable=self.rv["weekly_reset_hour"], width=4).pack(side="left", padx=2)
        ttk.Button(rr, text=ui_theme.with_icon(t("btn.save_short"), "💾"), command=self.save_reset_settings, style="Accent.TButton").pack(side="left", padx=8)
        ttk.Label(top, text=t("task.reset_note"),
                 foreground=PAL["muted"]).pack(anchor="w", padx=8, pady=(0, 4))

        fb = ttk.LabelFrame(f, text=t("tasks.feed_box")); fb.pack(fill="x", padx=10, pady=(0, 8))
        fr = ttk.Frame(fb); fr.pack(fill="x", padx=8, pady=6)
        ttk.Button(fr, text=ui_theme.with_icon(t("tasks.sync_now"), "🌐"), style="Accent.TButton",
                   command=lambda: self.meta_sync_start(force=True, what=("tasks",))).pack(side="left")
        self.bv_tasks = {k: tk.BooleanVar(value=bool(st.get(k, True))) for k in ("tasks_sync", "auto_reset_times")}
        ttk.Checkbutton(fr, text=t("tasks.enable"), variable=self.bv_tasks["tasks_sync"],
                        command=self.save_task_feed_flags).pack(side="left", padx=(14, 0))
        ttk.Checkbutton(fr, text=t("tasks.auto_resets"), variable=self.bv_tasks["auto_reset_times"],
                        command=self.save_task_feed_flags).pack(side="left", padx=(14, 0))
        self.tasks_info = ttk.Label(fb, text=self.tasks_status_text(), foreground=PAL["muted"], wraplength=820, justify="left")
        self.tasks_info.pack(anchor="w", padx=8)
        ttk.Label(fb, text=t("tasks.feed_note"), foreground=PAL["muted"], wraplength=820,
                  justify="left").pack(anchor="w", padx=8, pady=(0, 6))

        add = ttk.LabelFrame(f, text=t("task.add_box"))
        add.pack(fill="x", padx=10, pady=(0, 8))
        row = ttk.Frame(add); row.pack(fill="x", padx=8, pady=4)
        ttk.Label(row, text=t("label.category")).pack(side="left")
        self.cat_var = tk.StringVar(value=cat_name(TASK_CATS[0]))
        ttk.Combobox(row, textvariable=self.cat_var, values=[cat_name(c) for c in TASK_CATS],
                     width=16, state="readonly").pack(side="left", padx=4)
        ttk.Button(row, text=t("task.read_screen"), command=self.capture_task_region).pack(side="left", padx=8)
        self.task_in = tk.Text(add, height=4, wrap="word"); self.task_in.pack(fill="x", padx=8, pady=(0, 4))
        row2 = ttk.Frame(add); row2.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Button(row2, text=t("task.translate_add"), command=self.translate_and_add, style="Accent.TButton").pack(side="left")
        self.tr_status = ttk.Label(row2, text=""); self.tr_status.pack(side="left", padx=10)

        lst = ttk.Frame(f); lst.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left = ttk.Frame(lst); left.pack(side="left", fill="y")
        ttk.Label(left, text=t("label.categories")).pack(anchor="w")
        self.cat_lb = tk.Listbox(left, width=16, exportselection=False)
        for c in TASK_CATS: self.cat_lb.insert("end", cat_name(c))
        self.cat_lb.selection_set(0); self.cat_lb.pack(fill="y", expand=True)
        self.cat_lb.bind("<<ListboxSelect>>", lambda e: self.refresh_tasks())
        right = ttk.Frame(lst); right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.task_tv = ttk.Treeview(right, columns=("done", "tr", "en", "src"), show="headings", height=10)
        for c, hd, w in (("done", "✔", 40), ("tr", t("col.translated"), 320), ("en", t("col.original"), 320), ("src", t("col.source"), 70)):
            self.task_tv.heading(c, text=hd); self.task_tv.column(c, width=w, anchor="center" if c in ("done", "src") else "w")
        self.task_tv.pack(fill="both", expand=True)
        self.task_tv.bind("<Double-1>", lambda e: self.toggle_task_done())
        tb = ttk.Frame(right); tb.pack(fill="x", pady=6)
        ttk.Button(tb, text=t("task.toggle_done"), command=self.toggle_task_done).pack(side="left")
        ttk.Button(tb, text=ui_theme.with_icon(t("btn.delete"), "🗑"), command=self.delete_task).pack(side="left", padx=6)
        ttk.Button(tb, text=ui_theme.with_icon(t("task.clear_done"), "✔"), command=self.clear_done_tasks).pack(side="left")
        ttk.Button(tb, text=ui_theme.with_icon(t("task.clear_cat"), "🧹"), command=self.clear_all_tasks).pack(side="left", padx=6)
        self.refresh_tasks(); self.update_reset_label()

        gpt = ttk.LabelFrame(f, text=t("gpt.box"))
        gpt.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(gpt, text=t("gpt.warning"), foreground=PAL["warning"], wraplength=760, justify="left").pack(anchor="w", padx=8, pady=4)
        gr = ttk.Frame(gpt); gr.pack(fill="x", padx=8, pady=2)
        self.gv = {k: tk.StringVar(value=str(self.cfg["settings"].get(k, ""))) for k in
                   ("chatgpt_window_title", "chatgpt_hotkey", "chatgpt_wait_seconds")}
        ttk.Label(gr, text=t("gpt.window_title")).pack(side="left")
        ttk.Entry(gr, textvariable=self.gv["chatgpt_window_title"], width=14).pack(side="left", padx=4)
        ttk.Label(gr, text=t("gpt.hotkey")).pack(side="left")
        ttk.Entry(gr, textvariable=self.gv["chatgpt_hotkey"], width=8).pack(side="left", padx=4)
        ttk.Label(gr, text=t("gpt.wait")).pack(side="left")
        ttk.Entry(gr, textvariable=self.gv["chatgpt_wait_seconds"], width=5).pack(side="left", padx=4)
        ttk.Button(gr, text=t("btn.save"), command=self.save_gpt_settings, style="Accent.TButton").pack(side="left", padx=8)
        gr2 = ttk.Frame(gpt); gr2.pack(fill="x", padx=8, pady=4)
        ttk.Button(gr2, text=ui_theme.with_icon(t("gpt.pick_region"), "⛶"), command=self.capture_gpt_region).pack(side="left")
        ttk.Button(gr2, text=t("gpt.run"), command=self.run_gpt_fetch, style="Accent.TButton").pack(side="left", padx=6)
        ttk.Button(gr2, text=t("gpt.read_only"), command=self.read_gpt_region_only).pack(side="left")
        self.gpt_status = ttk.Label(gpt, text=""); self.gpt_status.pack(anchor="w", padx=8)
        ttk.Label(gpt, text=t("gpt.prompt_label")).pack(anchor="w", padx=8, pady=(6, 0))
        self.gpt_prompt = tk.Text(gpt, height=4, wrap="word"); self.gpt_prompt.pack(fill="x", padx=8, pady=(0, 4))
        self.gpt_prompt.insert("end", self.cfg["settings"].get("chatgpt_prompt") or default_gpt_prompt())
        ttk.Button(gpt, text=t("gpt.save_prompt"), command=self.save_gpt_prompt).pack(anchor="w", padx=8, pady=(0, 4))
        ttk.Label(gpt, text=t("gpt.raw_label")).pack(anchor="w", padx=8)
        self.gpt_raw = tk.Text(gpt, height=5, state="disabled", wrap="word", font=("Consolas", 9)); self.gpt_raw.pack(fill="x", padx=8, pady=(0, 8))

    def save_gpt_settings(self):
        st = self.cfg["settings"]
        try:
            ws = float(self.gv["chatgpt_wait_seconds"].get())
            from pynput import keyboard
            keyboard.HotKey.parse(self.gv["chatgpt_hotkey"].get())
        except Exception as e:
            return messagebox.showerror(APP_NAME, t("err.bad_setting", e=e))
        st["chatgpt_window_title"] = self.gv["chatgpt_window_title"].get().strip() or "ChatGPT"
        st["chatgpt_hotkey"] = self.gv["chatgpt_hotkey"].get().strip()
        st["chatgpt_wait_seconds"] = ws
        save_cfg(self.cfg)
        if self.running: self.stop(); self.start()
        messagebox.showinfo(APP_NAME, t("msg.settings_saved"))

    def save_gpt_prompt(self):
        self.cfg["settings"]["chatgpt_prompt"] = self.gpt_prompt.get("1.0", "end").strip()
        save_cfg(self.cfg); messagebox.showinfo(APP_NAME, t("gpt.prompt_saved"))

    def capture_gpt_region(self):
        if not messagebox.askokcancel(APP_NAME, t("calib.ask_gpt")):
            return
        self.root.withdraw(); self.root.after(5000, self._gpt_region_capture)

    def _gpt_region_capture(self):
        with mss.mss() as sct:
            mon = sct.monitors[1]; s = sct.grab(mon); img = Image.frombytes("RGB", s.size, s.rgb)
        self.root.deiconify()
        w = tk.Toplevel(self.root); w.attributes("-fullscreen", True, "-topmost", True)
        cv = tk.Canvas(w, highlightthickness=0, cursor="crosshair"); cv.pack(fill="both", expand=True)
        w.update_idletasks()
        sw, sh = w.winfo_width(), w.winfo_height()
        scale = min(sw / img.width, sh / img.height)
        w._photo = ImageTk.PhotoImage(img.resize((int(img.width * scale), int(img.height * scale))))
        cv.create_image(0, 0, image=w._photo, anchor="nw")
        cv.create_text(sw // 2, 30, fill="yellow", font=("Segoe UI", 18, "bold"), text=t("gpt.calib_hint"))
        st = {}
        def down(e): st.update(x0=e.x, y0=e.y, r=cv.create_rectangle(e.x, e.y, e.x, e.y, outline="lime", width=3))
        def move(e): cv.coords(st["r"], st["x0"], st["y0"], e.x, e.y)
        def up(e):
            x1, x2 = sorted((st["x0"], e.x)); y1, y2 = sorted((st["y0"], e.y))
            if x2 - x1 < 30 or y2 - y1 < 30: return
            self.cfg["settings"]["chatgpt_region"] = {"left": mon["left"] + int(x1 / scale), "top": mon["top"] + int(y1 / scale),
                                                       "width": int((x2 - x1) / scale), "height": int((y2 - y1) / scale)}
            save_cfg(self.cfg); w.destroy()
        cv.bind("<ButtonPress-1>", down); cv.bind("<B1-Motion>", move); cv.bind("<ButtonRelease-1>", up)
        w.bind("<Escape>", lambda e: w.destroy()); w.focus_force()

    def run_gpt_fetch(self):  # pynput thread'inden de çağrılır: tk'ya dokunma
        st = self.cfg["settings"]
        if not st.get("chatgpt_region"):
            return self.results.put(("gpt_status", t("gpt.need_region")))
        threading.Thread(target=self._gpt_fetch_work, daemon=True).start()

    def _gpt_fetch_work(self):
        st = self.cfg["settings"]
        try:
            self.results.put(("gpt_status", t("gpt.finding_window")))
            find_and_focus_window(st.get("chatgpt_window_title", "ChatGPT"))
            raw = st.get("chatgpt_prompt") or default_gpt_prompt()
            try:
                prompt = raw.format(date=datetime.now().strftime("%Y-%m-%d"))
            except (KeyError, IndexError, ValueError):
                prompt = raw   # kullanıcı kendi metninde başka bir yer tutucu kullanmışsa bozma
            type_and_send(prompt)
            wait = float(st.get("chatgpt_wait_seconds", 15))
            for left in range(int(wait), 0, -1):
                self.results.put(("gpt_status", t("gpt.waiting", left=left)))
                time.sleep(1)
            self._gpt_read_and_add()
        except Exception as e:
            log.exception("ChatGPT automation failed")
            self.results.put(("gpt_status", t("err.generic", e=e)))

    def read_gpt_region_only(self):
        if not self.cfg["settings"].get("chatgpt_region"):
            return messagebox.showinfo(APP_NAME, t("gpt.need_region_short"))
        threading.Thread(target=self._gpt_read_and_add, daemon=True).start()

    def _gpt_read_and_add(self):
        try:
            text = ocr(grab(self.cfg["settings"]["chatgpt_region"]), "eng+tur" if "+tur" in (pytesseract.pytesseract.tesseract_cmd or "") else self.cfg["settings"]["ocr_lang"])
            parsed = parse_gpt_answer(text)
            self.results.put(("gpt_raw", text))
            total = 0
            for cat, items in parsed.items():
                if not items: continue
                add = [{"en": "", "tr": it, "src": "ChatGPT", "done": False, "time": datetime.now().isoformat(timespec="seconds")} for it in items]
                self.results.put(("tasks_added", cat, add)); total += len(add)
            self.results.put(("gpt_status", t("task.added", n=total) if total else t("gpt.no_parse")))
        except Exception as e:
            log.exception("Reading ChatGPT answer failed")
            self.results.put(("gpt_status", t("err.read", e=e)))


    def save_task_feed_flags(self):
        st = self.cfg["settings"]
        for k, v in self.bv_tasks.items(): st[k] = bool(v.get())
        save_cfg(self.cfg)

    def save_reset_settings(self):
        st = self.cfg["settings"]
        try:
            dh = int(self.rv["daily_reset_hour"].get()); wh = int(self.rv["weekly_reset_hour"].get())
            if not (0 <= dh <= 23 and 0 <= wh <= 23): raise ValueError
        except ValueError:
            return messagebox.showerror(APP_NAME, t("task.err_hour"))
        st["daily_reset_hour"], st["weekly_reset_hour"] = dh, wh
        st["weekly_reset_day"] = weekday_names().index(self.rv["weekly_reset_day"].get())
        st["auto_reset_times"] = False      # elle ayarladı: ortak liste artık saatleri değiştirmesin
        if hasattr(self, "bv_tasks"): self.bv_tasks["auto_reset_times"].set(False)
        save_cfg(self.cfg); self.update_reset_label(); messagebox.showinfo(APP_NAME, t("task.reset_saved"))

    def update_reset_label(self):
        st, now = self.cfg["settings"], datetime.now()
        nd = next_daily_reset(now, st["daily_reset_hour"]); nw = next_weekly_reset(now, st["weekly_reset_day"], st["weekly_reset_hour"])
        self.reset_lbl.config(text=t("task.reset_line",
                                     daily=fmt_remaining(nd, now),
                                     day=weekday_names()[st["weekly_reset_day"]],
                                     weekly=fmt_remaining(nw, now)))

    # ---------- Meta build senkronu ----------
    def meta_sync_start(self, force=False, quiet=False, what=("builds", "tasks")):
        """Arka planda meta build + görev listelerini indirir (günde bir; force=True ise hemen)."""
        st = self.cfg["settings"]
        if self.meta_busy or (not force and not meta_sync.due(st)): return
        if not meta_sync.configured_urls(st.get("meta_feed_url", "")):
            if force and not quiet: self.toast(t("meta.not_configured"))
            log.info("Meta sync skipped: feed URL not configured")
            return
        do_b = "builds" in what and st.get("meta_sync", True)
        do_t = "tasks" in what and st.get("tasks_sync", True)
        if not (do_b or do_t): return
        self.meta_busy = True
        st["meta_last_try"] = time.time(); save_cfg(self.cfg)
        if force and not quiet: self.toast(t("meta.syncing"))
        verbose = force and not quiet

        def work():
            out = {}
            for kind, fn, cache, on in (("builds", meta_sync.run, META_CACHE, do_b),
                                        ("tasks", meta_sync.run_tasks, TASKS_CACHE, do_t)):
                if not on: continue
                try: out[kind] = (fn(self.cfg, cache, APP_VERSION, force=force), None)
                except Exception as e: out[kind] = (None, e)
            self.root.after(0, lambda: self.sync_done(out, verbose))
        threading.Thread(target=work, daemon=True).start()

    def sync_done(self, out, verbose):
        self.meta_busy = False
        msgs = []
        if "builds" in out:
            m = self.meta_sync_done(*out["builds"], verbose)
            if m: msgs.append(m)
        if "tasks" in out:
            m = self.tasks_sync_done(*out["tasks"], verbose)
            if m: msgs.append(m)
        if msgs: self.toast("  ·  ".join(msgs))

    def tasks_sync_done(self, res, err, verbose):
        if err is not None:
            log.warning("Tasks sync failed: %s", err)
            return t("meta.failed") if verbose else ""
        feed, source = res
        st = self.cfg["settings"]
        summary = meta_sync.merge_tasks(self.tasks, feed)
        save_tasks(self.tasks)
        if feed.get("resets") and st.get("auto_reset_times", True):     # resmî sıfırlama saatleri → yerel saat
            dh, wd, wh = meta_sync.local_resets(feed["resets"])
            if (st["daily_reset_hour"], st["weekly_reset_day"], st["weekly_reset_hour"]) != (dh, wd, wh):
                st["daily_reset_hour"], st["weekly_reset_day"], st["weekly_reset_hour"] = dh, wd, wh
                save_cfg(self.cfg)
                if hasattr(self, "rv"):
                    self.rv["daily_reset_hour"].set(str(dh)); self.rv["weekly_reset_hour"].set(str(wh))
                    self.rv["weekly_reset_day"].set(weekday_names()[wd])
        st["tasks_version"] = feed.get("version", ""); save_cfg(self.cfg)
        log.info("Tasks sync from %s: version=%s added=%d removed=%d", source, feed.get("version"), summary["added"], summary["removed"])
        try: self.refresh_tasks(); self.update_reset_label()
        except Exception: pass
        if hasattr(self, "tasks_info"): self.tasks_info.config(text=self.tasks_status_text())
        if summary["added"] or summary["removed"] or verbose:
            return t("tasks.synced", added=summary["added"], removed=summary["removed"])
        return ""

    def tasks_status_text(self):
        n = sum(1 for c in self.tasks["items"].values() for x in c if x.get("feed_id"))
        return t("tasks.status", n=n, version=self.cfg["settings"].get("tasks_version") or "—")

    def meta_sync_done(self, res, err, force):
        if err is not None:
            log.warning("Meta sync failed: %s", err)
            return t("meta.failed") if force else ""
        feed, source = res
        cur_name = self.cur["name"] if self.cur else None
        summary = meta_sync.apply(self.cfg, feed, source)
        for old, new in summary["renames"].items():         # ilerleme kayıtlarını yeni ada taşı
            if old in self.progress and new not in self.progress:
                self.progress[new] = self.progress.pop(old)
        if summary["renames"]: save_progress(self.progress)
        save_cfg(self.cfg)
        log.info("Meta sync from %s: version=%s added=%d updated=%d removed=%d", source, summary["version"],
                 summary["added"], summary["updated"], summary["removed"])
        names = [b["name"] for b in self.cfg["builds"]]
        try: self.refresh_builds(names.index(cur_name) if cur_name in names else 0)
        except Exception: pass
        if hasattr(self, "meta_info"): self.meta_info.config(text=self.meta_status_text())
        changed = summary["added"] + summary["updated"] + summary["removed"]
        if changed or force:
            return (t("meta.synced", added=summary["added"], updated=summary["updated"], removed=summary["removed"])
                    if changed else t("meta.up_to_date"))
        return ""

    def meta_status_text(self):
        st = self.cfg["settings"]
        n = sum(1 for b in self.cfg["builds"] if b.get("meta_id"))
        try:   # UTC kaydedilir, yerel saatle gösterilir
            from datetime import datetime as _dt
            when = _dt.fromisoformat(st.get("meta_last_sync")).astimezone().strftime("%Y-%m-%d %H:%M")
        except Exception:
            when = ""
        return t("meta.status", n=n, version=st.get("meta_version") or "—", when=when or "—")

    def check_resets(self):
        st, now = self.cfg["settings"], datetime.now()
        dk, wk = daily_period_key(now, st["daily_reset_hour"]), weekly_period_key(now, st["weekly_reset_day"], st["weekly_reset_hour"])
        changed = False
        if self.tasks["last_daily_key"] and self.tasks["last_daily_key"] != dk:
            self.tasks["items"]["daily"] = []; changed = True
        if self.tasks["last_weekly_key"] and self.tasks["last_weekly_key"] != wk:
            self.tasks["items"]["weekly"] = []; changed = True
        reset_happened = changed
        for c, lst in self.tasks["items"].items():          # süresi dolan ortak görevler
            keep = [x for x in lst if not meta_sync.task_expired(x)]
            if len(keep) != len(lst): self.tasks["items"][c] = keep; changed = True
        if reset_happened and self.cfg["settings"].get("tasks_sync", True):
            self.root.after(90_000, lambda: self.meta_sync_start(force=True, quiet=True, what=("tasks",)))
        self.tasks["last_daily_key"], self.tasks["last_weekly_key"] = dk, wk
        if changed:
            save_tasks(self.tasks); self.refresh_tasks()
        self.update_reset_label()
        self.root.after(60000, self.check_resets)

    def selected_list_cat(self):
        """Soldaki kategori listesinde seçili olanın kimliği."""
        s = self.cat_lb.curselection()
        return TASK_CATS[s[0]] if s else TASK_CATS[0]

    def refresh_tasks(self):
        self.task_tv.delete(*self.task_tv.get_children())
        cat = self.selected_list_cat()
        lang = i18n.current_language()
        for i, task in enumerate(self.tasks["items"].get(cat, [])):
            shown = task.get("texts", {}).get(lang) or task.get("tr") or task["en"]
            self.task_tv.insert("", "end", iid=str(i), values=("✔" if task["done"] else "—", shown, task["en"], task.get("src", "")))

    def capture_task_region(self):
        if not messagebox.askokcancel(APP_NAME, t("calib.ask_tasks")):
            return
        self.root.withdraw(); self.root.after(5000, self._task_region_capture)

    def _task_region_capture(self):
        with mss.mss() as sct:
            mon = sct.monitors[1]; s = sct.grab(mon); img = Image.frombytes("RGB", s.size, s.rgb)
        self.root.deiconify()
        w = tk.Toplevel(self.root); w.attributes("-fullscreen", True, "-topmost", True)
        cv = tk.Canvas(w, highlightthickness=0, cursor="crosshair"); cv.pack(fill="both", expand=True)
        w.update_idletasks()
        sw, sh = w.winfo_width(), w.winfo_height()
        scale = min(sw / img.width, sh / img.height)
        w._photo = ImageTk.PhotoImage(img.resize((int(img.width * scale), int(img.height * scale))))
        cv.create_image(0, 0, image=w._photo, anchor="nw")
        cv.create_text(sw // 2, 30, fill="yellow", font=("Segoe UI", 18, "bold"), text=t("task.calib_hint"))
        st = {}
        def down(e): st.update(x0=e.x, y0=e.y, r=cv.create_rectangle(e.x, e.y, e.x, e.y, outline="lime", width=3))
        def move(e): cv.coords(st["r"], st["x0"], st["y0"], e.x, e.y)
        def up(e):
            x1, x2 = sorted((st["x0"], e.x)); y1, y2 = sorted((st["y0"], e.y))
            if x2 - x1 < 30 or y2 - y1 < 30: return
            region = {"left": mon["left"] + int(x1 / scale), "top": mon["top"] + int(y1 / scale),
                      "width": int((x2 - x1) / scale), "height": int((y2 - y1) / scale)}
            w.destroy()
            try:
                text = ocr(grab(region), self.cfg["settings"]["ocr_lang"])
                self.task_in.delete("1.0", "end"); self.task_in.insert("end", text.strip())
            except Exception as e:
                messagebox.showerror(APP_NAME, t("err.read", e=e))
        cv.bind("<ButtonPress-1>", down); cv.bind("<B1-Motion>", move); cv.bind("<ButtonRelease-1>", up)
        w.bind("<Escape>", lambda e: w.destroy()); w.focus_force()

    def translate_and_add(self):
        raw = self.task_in.get("1.0", "end").strip()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        if not lines:
            return messagebox.showinfo(APP_NAME, t("task.paste_first"))
        cat = self.selected_add_cat()
        self.tr_status.config(text=t("task.translating"))
        def work():
            added = []
            for line in lines:
                tr, src = translate_task_text(self, line)
                added.append({"en": line, "tr": tr.strip(), "src": src, "done": False,
                             "time": datetime.now().isoformat(timespec="seconds")})
            self.results.put(("tasks_added", cat, added))
        threading.Thread(target=work, daemon=True).start()

    def selected_add_cat(self):
        """Ekleme kutusundaki açılır listede seçili kategorinin kimliği."""
        label = self.cat_var.get()
        return next((c for c in TASK_CATS if cat_name(c) == label), TASK_CATS[0])

    def toggle_task_done(self):
        s, idx = self.cat_lb.curselection(), self.task_tv.selection()
        if not s or not idx: return
        cat, i = TASK_CATS[s[0]], int(idx[0])
        self.tasks["items"][cat][i]["done"] = not self.tasks["items"][cat][i]["done"]
        save_tasks(self.tasks); self.refresh_tasks()

    def delete_task(self):
        s, idx = self.cat_lb.curselection(), self.task_tv.selection()
        if not s or not idx: return
        cat, i = TASK_CATS[s[0]], int(idx[0])
        del self.tasks["items"][cat][i]; save_tasks(self.tasks); self.refresh_tasks()

    def clear_done_tasks(self):
        s = self.cat_lb.curselection()
        if not s: return
        cat = TASK_CATS[s[0]]
        self.tasks["items"][cat] = [x for x in self.tasks["items"][cat] if not x["done"]]
        save_tasks(self.tasks); self.refresh_tasks()

    def clear_all_tasks(self):
        s = self.cat_lb.curselection()
        if not s: return
        cat = TASK_CATS[s[0]]
        if messagebox.askyesno(APP_NAME, t("task.clear_cat_confirm", cat=cat_name(cat))):
            self.tasks["items"][cat] = []; save_tasks(self.tasks); self.refresh_tasks()

    # ---------- Ayarlar ----------
    def build_settings(self):
        f, st = ui_theme.scrollable(self.tabs["settings"], PAL["bg"]), self.cfg["settings"]
        keys = ("hotkey", "keep_threshold", "consider_threshold", "overlay_seconds", "auto_interval_ms",
                "ocr_lang", "tesseract_cmd", "log_max_kb", "log_backups")
        self.sv = {k: tk.StringVar(value=str(st.get(k, ""))) for k in keys + ("overlay_corner", "log_level")}
        self.bv = {k: tk.BooleanVar(value=bool(st.get(k, True)))
                   for k in ("sound", "save_debug_crop", "log_csv", "track_progress", "auto_record")}

        # ---- Dil / language ----
        langs = i18n.available_languages()
        self.lang_codes = [c for c, _ in langs]
        cur = i18n.current_language()
        self.lang_var = tk.StringVar(value=i18n.language_name(cur))
        lb = ttk.LabelFrame(f, text=t("set.language_box")); lb.pack(fill="x", padx=10, pady=(10, 6))
        r0 = ttk.Frame(lb); r0.pack(fill="x", padx=8, pady=6)
        ttk.Label(r0, text=t("set.language")).pack(side="left")
        lcb = ttk.Combobox(r0, textvariable=self.lang_var, values=[n for _, n in langs], width=24, state="readonly")
        lcb.pack(side="left", padx=6)
        lcb.bind("<<ComboboxSelected>>", lambda e: self.flash_language(self._selected_lang_code()))
        ttk.Button(r0, text=ui_theme.with_icon(t("set.apply_language"), "✔"), command=self.apply_language).pack(side="left")
        ttk.Label(lb, text=t("set.language_note"), foreground=PAL["muted"], wraplength=820,
                  justify="left").pack(anchor="w", padx=8, pady=(0, 6))

        # ---- Meta build senkronu ----
        mb = ttk.LabelFrame(f, text=t("meta.box")); mb.pack(fill="x", padx=10, pady=6)
        rm = ttk.Frame(mb); rm.pack(fill="x", padx=8, pady=6)
        self.bv["meta_sync"] = tk.BooleanVar(value=bool(st.get("meta_sync", True)))
        ttk.Checkbutton(rm, text=t("meta.enable"), variable=self.bv["meta_sync"]).pack(side="left")
        ttk.Button(rm, text=ui_theme.with_icon(t("meta.sync_now"), "⭐"), command=lambda: self.meta_sync_start(force=True, what=("builds",))).pack(side="left", padx=12)
        if st.get("meta_hidden"):
            ttk.Button(rm, text=t("meta.restore_hidden"), command=self.meta_restore_hidden).pack(side="left")
        rm2 = ttk.Frame(mb); rm2.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Label(rm2, text=t("meta.url")).pack(side="left")
        self.sv["meta_feed_url"] = tk.StringVar(value=st.get("meta_feed_url", ""))
        ttk.Entry(rm2, textvariable=self.sv["meta_feed_url"], width=60).pack(side="left", padx=6)
        ttk.Label(mb, text=t("meta.note"), foreground=PAL["muted"], wraplength=820,
                  justify="left").pack(anchor="w", padx=8, pady=(0, 6))

        # ---- Görünüm / appearance ----
        ap = ttk.LabelFrame(f, text=t("set.appearance_box")); ap.pack(fill="x", padx=10, pady=6)
        ra = ttk.Frame(ap); ra.pack(fill="x", padx=8, pady=6)
        ttk.Label(ra, text=t("set.theme")).pack(side="left")
        self.theme_var = tk.StringVar(value=t("theme." + (st.get("ui_theme") if st.get("ui_theme") in ui_theme.THEME_MODES else "dark")))
        ttk.Combobox(ra, textvariable=self.theme_var, values=[t("theme." + m) for m in ui_theme.THEME_MODES],
                     width=18, state="readonly").pack(side="left", padx=6)
        self.bv["ui_sounds"] = tk.BooleanVar(value=bool(st.get("ui_sounds", True)))
        ttk.Checkbutton(ra, text=t("set.ui_sounds"), variable=self.bv["ui_sounds"]).pack(side="left", padx=(18, 0))
        rb = ttk.Frame(ap); rb.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Label(rb, text=t("set.bg_interval")).pack(side="left")
        self.sv["bg_interval"] = tk.StringVar(value=str(st.get("bg_interval", 15)))
        ttk.Entry(rb, textvariable=self.sv["bg_interval"], width=6).pack(side="left", padx=6)
        ttk.Button(rb, text=ui_theme.with_icon(t("set.open_art"), "📂"), command=self.open_art_folder).pack(side="left", padx=(12, 0))
        ttk.Label(ap, text=t("set.theme_note") + "\n" + t("set.art_note"), foreground=PAL["muted"], wraplength=820,
                  justify="left").pack(anchor="w", padx=8, pady=(0, 6))

        # ---- Tarama / scanning ----
        gb = ttk.LabelFrame(f, text=t("set.scan_box")); gb.pack(fill="x", padx=10, pady=6)
        rows = [(t("mode.hotkey"), "hotkey"), (t("set.keep_threshold"), "keep_threshold"),
                (t("set.consider_threshold"), "consider_threshold"), (t("set.overlay_seconds"), "overlay_seconds"),
                (t("set.auto_interval"), "auto_interval_ms"), (t("set.ocr_lang"), "ocr_lang"),
                (t("set.tesseract_path"), "tesseract_cmd")]
        for i, (lab, k) in enumerate(rows):
            ttk.Label(gb, text=lab).grid(row=i, column=0, sticky="w", padx=10, pady=4)
            ttk.Entry(gb, textvariable=self.sv[k], width=46).grid(row=i, column=1, sticky="w")
        ttk.Button(gb, text=ui_theme.with_icon(t("set.capture_key"), "⌨"), command=self.capture_key).grid(row=0, column=2, padx=6)
        ttk.Button(gb, text=t("btn.browse"),
                   command=lambda: self.sv["tesseract_cmd"].set(filedialog.askopenfilename() or self.sv["tesseract_cmd"].get())
                   ).grid(row=6, column=2, padx=6)
        ttk.Label(gb, text=t("set.overlay_corner")).grid(row=7, column=0, sticky="w", padx=10, pady=4)
        ttk.Combobox(gb, textvariable=self.sv["overlay_corner"],
                     values=["top_right", "top_left", "bottom_right", "bottom_left"],
                     width=20, state="readonly").grid(row=7, column=1, sticky="w")
        for i, (lab, k) in enumerate(((t("set.sound"), "sound"), (t("set.track_progress"), "track_progress"),
                                      (t("set.auto_record"), "auto_record"),
                                      (t("set.save_crop"), "save_debug_crop"), (t("set.log_csv"), "log_csv"))):
            ttk.Checkbutton(gb, text=lab, variable=self.bv[k]).grid(row=8 + i, column=0, columnspan=2, sticky="w", padx=10)

        # ---- Günlük kayıt / logging ----
        lg = ttk.LabelFrame(f, text=t("set.log_box")); lg.pack(fill="x", padx=10, pady=6)
        r1 = ttk.Frame(lg); r1.pack(fill="x", padx=8, pady=6)
        ttk.Label(r1, text=t("set.log_level")).pack(side="left")
        ttk.Combobox(r1, textvariable=self.sv["log_level"], values=["DEBUG", "INFO", "WARNING", "ERROR"],
                     width=10, state="readonly").pack(side="left", padx=6)
        ttk.Label(r1, text=t("set.log_size")).pack(side="left", padx=(12, 2))
        ttk.Entry(r1, textvariable=self.sv["log_max_kb"], width=7).pack(side="left")
        ttk.Label(r1, text=t("set.log_backups")).pack(side="left", padx=(12, 2))
        ttk.Entry(r1, textvariable=self.sv["log_backups"], width=5).pack(side="left")

        ttk.Button(f, text=t("set.save"), command=self.save_settings, style="Accent.TButton").pack(anchor="w", padx=12, pady=12)

    def _selected_lang_code(self):
        names = [n for _, n in i18n.available_languages()]
        try: return self.lang_codes[names.index(self.lang_var.get())]
        except ValueError: return i18n.current_language()

    def apply_language(self):
        """Dili kaydeder ve arayüzü yeniden başlatmadan yeni dilde kurar."""
        code = self._selected_lang_code()
        self.cfg["settings"]["language"] = code
        save_cfg(self.cfg)
        log.info("Language set to %s", code)
        i18n.set_language(code)
        self.rebuild_ui(tab="settings")
        self.flash_language(code)
        self.toast(t("set.language_changed", lang=i18n.language_name(code)))

    def capture_key(self):
        self.sv["hotkey"].set(t("set.press_key"))
        def on_key(e):
            if e.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"): return
            mods = (["<ctrl>"] if e.state & 0x4 else []) + (["<shift>"] if e.state & 0x1 else []) + (["<alt>"] if e.state & 0x20000 else [])
            k = e.keysym.lower()
            self.sv["hotkey"].set("+".join(mods + [k if len(k) == 1 else f"<{k}>"])); self.root.unbind("<Key>")
        self.root.bind("<Key>", on_key)

    def save_settings(self):
        st = self.cfg["settings"]
        try:
            from pynput import keyboard
            keyboard.HotKey.parse(self.sv["hotkey"].get())
            for k in ("keep_threshold", "consider_threshold", "overlay_seconds", "auto_interval_ms"): st[k] = float(self.sv[k].get())
            st["log_max_kb"] = max(16, int(float(self.sv["log_max_kb"].get())))
            st["log_backups"] = max(0, int(float(self.sv["log_backups"].get())))
            st["bg_interval"] = max(0, int(float(self.sv["bg_interval"].get() or 0)))
        except Exception as e:
            return messagebox.showerror(APP_NAME, t("err.bad_setting", e=e))
        for k in ("hotkey", "overlay_corner", "ocr_lang", "tesseract_cmd", "log_level", "meta_feed_url"): st[k] = self.sv[k].get().strip()
        for k, v in self.bv.items(): st[k] = v.get()
        old_theme = st.get("ui_theme", "dark")
        st["ui_theme"] = next((m for m in ui_theme.THEME_MODES if t("theme." + m) == self.theme_var.get()), old_theme)
        self.sounds.enabled = bool(st.get("ui_sounds", True))
        save_cfg(self.cfg); self.tess = find_tesseract(self.cfg)
        setup_logging(st["log_level"], st["log_max_kb"], st["log_backups"])
        log.info("Settings saved (log level %s)", st["log_level"])
        if self.running: self.stop(quiet=True); self.start(quiet=True)
        if st["ui_theme"] != old_theme:
            self.rebuild_ui(tab="settings")          # tema anında uygulanır, yeniden başlatma yok
        else:
            self.banner.set_interval(st["bg_interval"])
            self.refresh_status()
        self.toast(t("msg.settings_saved"))

    def meta_restore_hidden(self):
        self.cfg["settings"]["meta_hidden"] = []; save_cfg(self.cfg)
        self.meta_sync_start(force=True, what=("builds",))

    def open_art_folder(self):
        for sub in ("backgrounds", "emblems", "flags"):
            (ART_DIR / sub).mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(ART_DIR)
        else:
            self.toast(str(ART_DIR))

    # ---------- Geçmiş ----------
    def build_hist(self):
        f = self.tabs["history"]
        bar = ttk.Frame(f); bar.pack(fill="x", padx=8, pady=8)
        ttk.Button(bar, text=ui_theme.with_icon(t("btn.refresh"), "⟳"), command=self.load_history).pack(side="left")
        ttk.Button(bar, text=ui_theme.with_icon(t("btn.open_folder"), "📂"), command=lambda: os.startfile(BASE) if os.name == "nt" else None).pack(side="left", padx=6)
        ttk.Button(bar, text=ui_theme.with_icon(t("hist.clear"), "🗑"), command=self.clear_history).pack(side="left")
        cols = (("time", t("col.time"), 140), ("item", t("col.item"), 230), ("verdict", t("col.verdict"), 90),
                ("best_build", t("col.best_build"), 190), ("score", t("col.score"), 50), ("slot", t("col.slot"), 80))
        self.th = ttk.Treeview(f, columns=[c[0] for c in cols], show="headings")
        for c, hd, w in cols: self.th.heading(c, text=hd); self.th.column(c, width=w)
        for v, col in VFG.items(): self.th.tag_configure(v, foreground=col)
        self.th.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def load_history(self):
        self.th.delete(*self.th.get_children())
        for r in read_log()[::-1][:500]:
            self.th.insert("", "end", values=[r[c] for c in ("time", "item", "verdict", "best_build", "score", "slot")], tags=(r["verdict"],))

    def clear_history(self):
        if messagebox.askyesno(APP_NAME, t("hist.clear_confirm")):
            LOG_PATH.unlink(missing_ok=True); self.load_history()

    # ---------- Log sekmesi / application log ----------
    def build_logtab(self):
        f = self.tabs["log"]
        bar = ttk.Frame(f); bar.pack(fill="x", padx=10, pady=8)
        ttk.Button(bar, text=ui_theme.with_icon(t("btn.refresh"), "⟳"), command=self.refresh_logtab).pack(side="left")
        ttk.Button(bar, text=t("btn.open_folder"),
                   command=lambda: os.startfile(APPLOG_DIR) if os.name == "nt" else None).pack(side="left", padx=6)
        ttk.Button(bar, text=ui_theme.with_icon(t("log.save_as"), "💾"), command=self.export_log).pack(side="left")
        ttk.Button(bar, text=ui_theme.with_icon(t("log.clear"), "🧹"), command=self.clear_applog).pack(side="left", padx=6)
        self.log_filter = tk.StringVar(value="ALL")
        ttk.Label(bar, text=t("log.level_filter")).pack(side="left", padx=(12, 2))
        cb = ttk.Combobox(bar, textvariable=self.log_filter, width=9, state="readonly",
                          values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"])
        cb.pack(side="left"); cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_logtab())
        self.log_auto = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text=t("log.autoscroll"), variable=self.log_auto).pack(side="left", padx=10)
        self.log_info = ttk.Label(f, foreground=PAL["muted"]); self.log_info.pack(anchor="w", padx=12)
        wrap = ttk.Frame(f); wrap.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.log_box = tk.Text(wrap, wrap="none", font=("Consolas", 9), state="disabled")
        ysb = ttk.Scrollbar(wrap, orient="vertical", command=self.log_box.yview)
        xsb = ttk.Scrollbar(f, orient="horizontal", command=self.log_box.xview)
        self.log_box.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        ysb.pack(side="right", fill="y"); self.log_box.pack(side="left", fill="both", expand=True)
        xsb.pack(fill="x", padx=10, pady=(0, 8))
        for lvl, col in (("DEBUG", PAL["muted"]), ("INFO", PAL["info"]), ("WARNING", PAL["warning"]), ("ERROR", PAL["danger"])):
            self.log_box.tag_configure(lvl, foreground=col)
        self.refresh_logtab()

    def refresh_logtab(self, limit=800):
        """Günlük dosyasının son satırlarını gösterir."""
        want = self.log_filter.get() if hasattr(self, "log_filter") else "ALL"
        try:
            lines = APPLOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
        except FileNotFoundError:
            lines = []
        except Exception as e:
            lines = [f"({e})"]
        shown = [l for l in lines if want == "ALL" or f"| {want:<7} |" in l][-limit:]
        self.log_box.config(state="normal"); self.log_box.delete("1.0", "end")
        for l in shown:
            lvl = next((x for x in ("ERROR", "WARNING", "DEBUG", "INFO") if f"| {x:<7} |" in l), "INFO")
            self.log_box.insert("end", l + "\n", lvl)
        self.log_box.config(state="disabled")
        if getattr(self, "log_auto", None) and self.log_auto.get():
            self.log_box.see("end")
        size = APPLOG_PATH.stat().st_size / 1024 if APPLOG_PATH.exists() else 0
        self.log_info.config(text=t("log.info", shown=len(shown), total=len(lines),
                                    kb=f"{size:.0f}", path=str(APPLOG_PATH)))

    def export_log(self):
        dest = filedialog.asksaveasfilename(defaultextension=".log", initialfile="td2_advisor.log",
                                            filetypes=[("Log", "*.log"), ("Text", "*.txt")])
        if not dest: return
        try:
            shutil.copy(APPLOG_PATH, dest)
            messagebox.showinfo(APP_NAME, t("log.saved", path=dest))
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    def clear_applog(self):
        if not messagebox.askyesno(APP_NAME, t("log.clear_confirm")): return
        for h in list(log.handlers):            # dosyayı bırak ki Windows'ta silinebilsin
            log.removeHandler(h)
            try: h.close()
            except Exception: pass
        for p in [APPLOG_PATH] + list(APPLOG_DIR.glob("app.log.*")):
            try: p.unlink()
            except Exception: pass
        st = self.cfg["settings"]
        setup_logging(st.get("log_level", "INFO"), st.get("log_max_kb", 1024), st.get("log_backups", 3))
        log.info("Log cleared by user")
        self.refresh_logtab()

    # ---------- Yardım / help ----------
    def build_help(self):
        """Yardım metni dil dosyasındaki help.body anahtarından gelir."""
        f = self.tabs["help"]
        box = tk.Text(f, wrap="word", font=("Segoe UI", 10))
        sb = ttk.Scrollbar(f, orient="vertical", command=box.yview); box.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=10); box.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        body = t("help.body")
        if body == "help.body":          # dil dosyasında yoksa İngilizceye düşülmüş olmalı
            body = "Help text is missing from this language file."
        box.insert("end", body)
        box.config(state="disabled")

    def on_close(self):
        self.stop(); self.speaker.close(); self.root.destroy()


if __name__ == "__main__":
    try:
        App().root.mainloop()
    except Exception:
        log.exception("Fatal error — application stopped")
        raise
    finally:
        log.info("=== %s stopped ===", APP_NAME)
