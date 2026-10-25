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
import csv, ctypes, json, math, logging, logging.handlers, os, queue, re, shutil, subprocess, sys, threading, time
import urllib.error, urllib.parse, urllib.request
import tkinter as tk
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher, get_close_matches
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

import mss
import pytesseract
from PIL import Image, ImageDraw, ImageOps, ImageTk

import i18n
import ui_theme
import ui_art
import meta_sync
import wiki_sync
import gamedata
import engine
import display
import view3d
import fx
import bgvideo
import ocr_backend
import features
import stash
import vendor
import companion
import share
import dropstats
import updater
from i18n import t

APP_NAME = "TD2 Loot Advisor"
APP_VERSION = "5.0.3"
FROZEN = getattr(sys, "frozen", False)
BASE = Path(sys.executable).parent if FROZEN else Path(__file__).resolve().parent
TASKS_CACHE = BASE / "tasks_cache.json"  # son indirilen görev listesi
META_CACHE = BASE / "meta_cache.json"   # son indirilen meta listesi (çevrimdışı kullanım)
ART_DIR = BASE / "art"   # arka planlar / amblemler / bayraklar (kullanıcı kendi görsellerini ekleyebilir)
BUNDLE = Path(getattr(sys, "_MEIPASS", BASE))
CFG_PATH, LOG_PATH, DEBUG_PATH, PROG_PATH = (BASE / n for n in ("builds.json", "loot_log.csv", "last_crop.png", "progress.json"))
STASH_PATH = BASE / "stash.json"
VENDOR_CACHE = BASE / "vendor_cache.json"
DROPQ_PATH = BASE / "drop_queue.json"
REPORTS_DIR = BASE / "reports"
ISSUES_URL = "https://github.com/FEDERALTURK/td2-loot-advisor/issues/new"
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
            "tasks_hotkey": "<f10>",
            "language": "", "log_level": "INFO", "log_max_kb": 1024, "log_backups": 3,
            "ui_theme": "dark", "ui_sounds": True, "bg_interval": 15,
            "fx_cursor": True, "fx_cursor_style": "crosshair", "fx_cursor_color": "#ff6d10", "fx_cursor_custom": "",
            "fx_trail": True, "fx_trail_color": "#ff6d10", "fx_trail_len": 18, "fx_transitions": True,
            "fx_video": True, "fx_video_dim": 0.35, "fx_transition_ms": 650, "fx_bgwatch": True, "fx_bgwatch_dim": 0.0,
            "res_profile": "auto", "ocr_engine": "auto", "license_key": "", "update_check": True, "update_last": 0, "update_skip": "", "stash_record": True, "vendor_mode": False, "vendor_auto": True, "drop_share": False, "drop_asked": False, "drop_activity": "none", "drop_server": "", "drop_client": "", "vision_ok": False, "vendor_notified": "", "companion_port": 8765, "ocr_threshold": 170, "ocr_scale": "auto", "ocr_psm": 6, "ocr_passes": 3,
            "overlay_mode": "card", "overlay_alpha": 0.94, "overlay_size": 1.0, "ui_depth": True,
            "meta_sync": True, "meta_feed_url": "", "meta_last_try": 0, "meta_last_sync": "", "meta_version": "",
            "meta_hidden": [], "tasks_sync": True, "auto_reset_times": True,
            "wiki_sync": True, "wiki_last_try": 0, "only_game_active": True, "scan_source": "screen"}
AUTO_STABLE, AUTO_CHANGE, DEDUP_SECONDS, UPGRADE_MARGIN = 4, 8, 30, 3

if not CFG_PATH.exists() and (BUNDLE / "builds.json").exists():
    shutil.copy(BUNDLE / "builds.json", CFG_PATH)
if (BUNDLE / "lang").is_dir() and BUNDLE != BASE:      # .exe: dilleri çıkar; güncellemede paketteki yeni sürümle yenile
    (BASE / "lang").mkdir(exist_ok=True)              # (kullanıcının eklediği yeni dil dosyalarına dokunulmaz)
    for _src in (BUNDLE / "lang").glob("*.json"):
        _dst = BASE / "lang" / _src.name
        try:
            if not _dst.exists() or _dst.read_bytes() != _src.read_bytes():
                shutil.copy(_src, _dst)
        except OSError:
            pass

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
OBSOLETE_SETTINGS = ("chatgpt_window_title", "chatgpt_wait_seconds", "chatgpt_region", "chatgpt_prompt", "chatgpt_hotkey")


def load_cfg():
    """builds.json'u okur; bozuksa yedekleyip varsayılanla başlar, eski ayarları taşır."""
    try:
        with open(CFG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        if not isinstance(cfg, dict) or "builds" not in cfg: raise ValueError("bad config")
    except Exception as e:
        bak = CFG_PATH.with_suffix(f".broken-{int(time.time())}.json")
        try: shutil.copy(CFG_PATH, bak)
        except Exception: pass
        src = BUNDLE / "builds.json"
        cfg = json.loads(src.read_text(encoding="utf-8")) if src.exists() and src != CFG_PATH else {"builds": [], "attributes": {}, "settings": {}}
        logging.getLogger("td2").warning("builds.json unreadable (%s); backup %s, starting from defaults", e, bak.name)
    cfg.setdefault("settings", {}); cfg.setdefault("builds", []); cfg.setdefault("attributes", {})
    st = cfg["settings"]
    if st.get("chatgpt_hotkey") and "tasks_hotkey" not in st:      # eski ChatGPT kısayolu → Claude görev getirme
        st["tasks_hotkey"] = st["chatgpt_hotkey"]
    for k in OBSOLETE_SETTINGS: st.pop(k, None)
    for k, v in DEFAULTS.items():
        st.setdefault(k, v)
    for b in cfg["builds"]:
        b.setdefault("sets_or_brands", []); b.setdefault("attributes", {}); b.setdefault("talents", {})
    return cfg

def save_cfg(cfg):
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def check_hotkey(spec):
    """Kısayol biçimini doğrular (pynput yoksa doğrulama atlanır, kayıt engellenmez)."""
    try:
        from pynput import keyboard
    except Exception:
        return
    keyboard.HotKey.parse(spec)


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

GAME_DATA_CACHE = BASE / "game_data_cache.json"
LEARNED_LIB = BASE / "learned_library.json"      # kartlardan öğrenilen markalar / setler / parça adları
GAME = gamedata.GameData(GAME_DATA_CACHE, BASE / "meta" / "game_data.json", BUNDLE / "meta" / "game_data.json").attach_learned(LEARNED_LIB)

SLOT_ICONS = {"Mask": "🎭", "Chest": "🦺", "Backpack": "🎒", "Gloves": "🧤", "Holster": "🔫", "Kneepads": "🦵",
              "Weapon": "🔫", "Sidearm": "🔫"}

def attr_name(k):
    """Attribute anahtarının okunur adı (oyundaki İngilizce ad)."""
    if k == "weapon_type_damage": return "Weapon Type Damage"
    if GAME.ok:
        al = GAME.data.get("attributes", {}).get(k, {}).get("aliases")
        if al: return al[0].title()
    return k.replace("_", " ").title()

def elevated(parent, row, column, depth=True):
    """Gölgeli, üzerine gelince kalkan kart (grid ile). Dönüş: iç çerçeve."""
    outer = tk.Frame(parent, bg=PAL["bg"])
    outer.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
    if depth:
        sh = tk.Frame(outer, bg="#b9bdc6" if PAL.get("mode") == "light" else "#06070a")
        sh.place(x=5, y=6, relwidth=1, relheight=1, width=-5, height=-6)
    box = tk.Frame(outer, bg=PAL["surface"], highlightthickness=2, highlightbackground=PAL["border"], padx=12, pady=10)
    box.pack(fill="both", expand=True, padx=(0, 5 if depth else 0), pady=(0, 6 if depth else 0))
    box._base_border = PAL["border"]
    if depth:
        def lift(_=None): box.pack_configure(padx=(0, 5), pady=(0, 6)); box.config(bg=PAL["surface2"]); _tint(box, PAL["surface2"])
        def drop(_=None):
            x, y = outer.winfo_pointerxy(); wdg = outer.winfo_containing(x, y)
            while wdg is not None and wdg is not outer: wdg = wdg.master
            if wdg is outer: return
            box.config(bg=PAL["surface"]); _tint(box, PAL["surface"])
        outer.bind("<Enter>", lift); outer.bind("<Leave>", drop); box.bind("<Leave>", drop)
    return box


def _tint(w, bg):
    for c in w.winfo_children():
        if isinstance(c, (tk.Label, tk.Frame)):
            try: c.config(bg=bg)
            except tk.TclError: pass
            _tint(c, bg)


_PROFILE_NOTE = {}


def game_size(st=None):
    """Oyunun gerçek boyutu: açık oyun penceresi, yoksa oyunun ayar dosyası (state.cfg), yoksa oyunun monitörü."""
    g = display.game_window()
    if g: return g["width"], g["height"], "window"
    gs = getattr(display, "_last_game_settings", None)
    if gs is None:
        try: gs = display.read_game_settings() if hasattr(display, "read_game_settings") else None
        except Exception: gs = None
        display._last_game_settings = gs or {}
    if gs and gs.get("width") and gs.get("height") and gs.get("display_mode", "").lower() != "windowed":
        return int(gs["width"]), int(gs["height"]), "state.cfg"
    w, h = display.monitor_size()
    return w, h, "monitor"


def active_profile(st):
    """(anahtar, profil). 'auto': oyunun gerçek boyutundan (pencere / ayar dosyası) — her çözünürlükte hesaplanır.
    Elle seçilmiş profil oyunun boyutuna uymuyorsa (başka bilgisayar, monitör değişti) otomatiğe dönülür."""
    w, h, src = game_size(st)
    key = st.get("res_profile", "auto")
    if key in display.PROFILES and not st.get("res_profile_lock"):
        pw, ph = map(int, key.split("x"))
        if abs(ph - h) > 100 or abs(pw / ph - w / max(1, h)) > 0.25:
            note = (key, w, h)
            if _PROFILE_NOTE.get("last") != note:
                _PROFILE_NOTE["last"] = note
                log.warning("Profile %s does not match the game (%dx%d from %s): using automatic profile", key, w, h, src)
            key = "auto"
    if key in display.PROFILES:
        return key, display.PROFILES[key]
    return display.profile_for(w, h)


def apply_ocr_settings(st):
    """Eşik / ölçek ayarlarını OCR ön işlemine uygular (profil + kullanıcı ince ayarı)."""
    _, prof = active_profile(st)
    # elle ince ayar yapılmadıysa eşik profilden gelir (eski sürümlerde kayıtlı sabit 170 her bilgisayarda kalıyordu)
    try: gamedata.THRESHOLD = int(float(st.get("ocr_threshold"))) if st.get("ocr_tuned") else prof["threshold"]
    except (TypeError, ValueError): gamedata.THRESHOLD = prof["threshold"]
    sc = st.get("ocr_scale", "auto")
    try: gamedata.SCALE = None if sc in ("auto", "", None) else float(sc)
    except (TypeError, ValueError): gamedata.SCALE = None
    make_ocr(st)


OCR = None


def make_ocr(st):
    """Seçili OCR motoru (otomatik: RapidOCR kuruluysa o, yoksa Tesseract)."""
    global OCR
    rec = ocr_backend.GAME_LANG_TO_REC.get(st.get("game_lang", "en"), "en")
    OCR = ocr_backend.Engine(st.get("ocr_engine", "auto"), rec_lang=rec, tess_lang=st.get("ocr_lang", "eng"),
                             tess_config=ocr_config(st), preprocess=gamedata.text_image)
    return OCR


def ocr_scale():
    """Kullanıcı ölçeği sabitlediyse o, yoksa motorun kendi otomatik ölçeği."""
    return gamedata.SCALE


def read_card(img, scale=None):
    """Kart metni ve satır kutuları: (metin, [(satır, kutu, güven)])."""
    lines = OCR.lines(img, ocr_scale() if scale is None else scale)
    return "\n".join(l for l, _, _ in lines), lines


def find_card(img):
    return engine.find_card(img, OCR.data, preprocess=OCR.name == "tesseract")


def color_hints(card, lines, item, verdict):
    """Simge/şerit renkleri (yalnız RapidOCR satır kutularıyla): nadirlik ipucu ve güvenlik ağı.
    Kart rengi egzotik gösterip yazı egzotik demiyorsa asla KIR denmez (KONTROL ET)."""
    if not lines or not any(b != (0, 0, 0, 0) for _, b, _ in lines) or not isinstance(item, dict):
        return verdict
    try:
        rc = ocr_backend.rarity_color(card, lines)
        icons = [c for _, c in ocr_backend.icon_colors(card, lines) if c]
    except Exception:
        log.debug("color hints failed", exc_info=True); return verdict
    item["_rarity_color"], item["_icons"] = rc, icons
    log.debug("Color hints: rarity=%s icons=%s", rc, icons)
    if rc == "EXOTIC" and "EXOTIC" not in (item.get("rarity") or []) and verdict == "DISMANTLE":
        item["_note"] = ((item.get("_note") or "") + " " + t("note.color_exotic")).strip()
        return "REVIEW"
    return verdict


def ocr_config(st):
    try: psm = int(st.get("ocr_psm", 6))
    except (TypeError, ValueError): psm = 6
    return f"--psm {psm if psm in (3, 4, 6, 11) else 6}"


def ocr_quality(text):
    """Kalibrasyon puanı: tanınan ad/set/attribute/talent sayısı + güven."""
    if not GAME.ok: return len(text.strip()) / 100
    r = GAME.recognize(text)
    return (r.get("confidence", 0) * 10 + len(r.get("attrs", {})) * 2 + len(r.get("talents", [])) * 1.5 +
            (2 if r.get("known") else 0) + (1 if r.get("brand") or r.get("gear_set") else 0))


def ocr_data(img):
    return OCR.data(img)

def foreground_title():
    """Öndeki pencerenin başlığı (yalnız Windows; başka sistemde boş)."""
    if os.name != "nt": return ""
    try:
        u = ctypes.windll.user32
        h = u.GetForegroundWindow(); n = u.GetWindowTextLengthW(h)
        buf = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, buf, n + 1)
        return buf.value
    except Exception:
        return ""

def game_active():
    """Sadece oyun öndeyken tara: program kendi penceresini ya da başka uygulamaları okumasın."""
    if os.name != "nt": return True
    title = foreground_title().lower()
    return "division" in title and "loot advisor" not in title

def grab(region):
    with mss.mss() as sct:
        s = sct.grab(region)
        img = Image.frombytes("RGB", s.size, s.rgb)
    if CAPTURE_MASK:
        from PIL import ImageDraw
        dr = ImageDraw.Draw(img); L, T = region["left"], region["top"]
        for x0, y0, x1, y1 in list(CAPTURE_MASK.values()):
            if x1 > L and y1 > T and x0 < L + region["width"] and y0 < T + region["height"]:
                dr.rectangle((x0 - L, y0 - T, x1 - L, y1 - T), fill=(0, 0, 0))
    return img

def ocr(img, lang=None):
    return OCR.text(img)

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
    """Oyun verisi varsa onunla tanır (bilinen ad/marka/set/talent + rulo kalitesi), yoksa eski yöntem."""
    if GAME.ok:
        item = GAME.recognize(text)
        known = {tal for b in cfg["builds"] for tal in b["talents"]}      # build'deki özel adlar da sayılsın
        low = text.lower()
        for tal in known:
            if tal not in item["talents"] and find_talent(tal, low, [l for l in text.splitlines() if l.strip()]):
                item["talents"].append(tal)
        return item
    return parse_item_legacy(text, cfg)

def parse_item_legacy(text, cfg):
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
    if "confidence" in item:                      # oyun verisiyle tanındıysa: güven eşiği
        return item["confidence"] >= 0.5 and item["name"] != "?"
    letters = sum(c.isalpha() for c in item["name"])
    return letters >= 4 and (len(item["attrs"]) >= 1 or item["rarity"])

def set_matches(item, names, low):
    """Build'in set/marka adı eşyada var mı? Önce tanınan marka/set, yoksa metinde arar."""
    have = [gamedata.nrm(x) for x in (item.get("brand"), item.get("gear_set"), item.get("name")) if x]
    for n in names:
        nn = gamedata.nrm(n)
        if not nn: continue
        if any(nn == h or (len(nn) >= 5 and (nn in h or h in nn)) or gamedata.ratio(nn, h) >= 0.86 for h in have):
            return True
        if nn in gamedata.nrm(low): return True
    return False

def score_build(item, b, low):
    raw, why = 0.0, []
    maxp = b.get("set_bonus", 0)
    if b["sets_or_brands"] and set_matches(item, b["sets_or_brands"], low):
        raw += b["set_bonus"]; why.append(t("why.set_match"))
    aw = sorted((a["weight"] for a in b["attributes"].values()), reverse=True)
    tw = sorted(b["talents"].values(), reverse=True)
    maxp += sum(aw[:4]) * 10 + (tw[0] * 10 if tw else 0)
    for k, r in b["attributes"].items():
        if k in item["attrs"]:
            v, good = item["attrs"][k], r["good_at"]
            ratio = v / good if good else (item.get("quality", {}).get(k, 100) / 100)
            raw += r["weight"] * 10 * min(ratio, 1.0)
            why.append(f"{k} {v:g} [" + (t("rate.good") if ratio >= 1 else t("rate.ok") if ratio >= .6 else t("rate.low")) + "]")
    have_tal = {gamedata.nrm(x) for x in item["talents"]}
    for tal, w in b["talents"].items():
        if gamedata.nrm(tal) in have_tal:
            raw += w * 10; why.append(f"talent: {tal}")
    return (round(min(100, raw / maxp * 100)) if maxp else 0), why

def evaluate(text, cfg):
    if GAME.ok:
        item = parse_item(text, cfg)
        item["_text"] = text
        res = engine.evaluate(item, text, cfg, GAME)
        verdict, nk, npar = engine.decide(item, res, cfg)
        item["_note"] = t(nk, **npar) if nk else ""
        return item, verdict, res
    return evaluate_legacy(text, cfg)

def evaluate_legacy(text, cfg):
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

def build_by_name(cfg, name):
    return next((b for b in cfg["builds"] if b["name"] == name), None)


def active_build(cfg):
    """Aktif build (Panel, Build'ler ve Eksik Parça bunu ortak kullanır)."""
    b = build_by_name(cfg, cfg["settings"].get("active_build", ""))
    return b or (cfg["builds"][0] if cfg["builds"] else None)


def req_lines_short(req):
    """Yuva şartının tek satırlık özeti: 'Striker's Battlegear · Weapon Damage · Critical Hit Chance'."""
    if not req or req.get("kind") == "off": return ""
    parts = list(req.get("source") or []) + list(req.get("types") or [])
    if req.get("core"): parts.append(attr_name(req["core"]))
    parts += [attr_name(a) for a in req.get("attrs") or []]
    if req.get("talent"): parts.append("★ " + req["talent"])
    return " · ".join(parts) or t("plan.any")


def plan_of(build):
    try:
        return engine.build_plan(build, GAME) if build else {}
    except Exception:
        log.exception("build plan failed")
        return {}


def req_lines(req):
    """Bir yuvanın şartlarını okunur satırlara çevirir."""
    if not req or req.get("kind") == "off": return [t("plan.off")]
    L = []
    k = req.get("kind")
    if k == "item": L.append("★ " + t("plan.item", item=req.get("item")))
    elif k == "set": L.append("🧩 " + t("plan.set", s=", ".join(req.get("source", []))))
    elif k == "weapon": L.append("🔫 " + t("plan.weapon", types=", ".join(req.get("types", [])) or "—"))
    else: L.append("🏷 " + (t("plan.brand", s=", ".join(req["source"])) if req.get("source") else t("plan.any")))
    if req.get("core"): L.append(t("plan.core", a=attr_name(req["core"])))
    if req.get("attrs"): L.append(t("plan.attrs", a=", ".join(attr_name(x) for x in req["attrs"])))
    if req.get("talent"): L.append(t("plan.talent", t=req["talent"]))
    return L


def check_lines(checks):
    sym = {True: "✔", False: "✖", None: "?"}
    lab = {"source": t("plan.c_source"), "type": t("plan.c_type"), "core": t("plan.c_core"), "attr": t("plan.c_attr"), "talent": t("plan.c_talent")}
    out = []
    for kind, ok, detail in checks:
        d = detail
        if kind in ("core", "attr"):
            parts = detail.split(" ", 1)
            d = attr_name(parts[0]) + (" " + parts[1] if len(parts) > 1 else "")
        out.append(f"{sym[ok]} {lab.get(kind, kind)}: {d}")
    return out


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
    """Eksik parça / yükseltme / rulo karşılaştırması — önce AKTİF build'e göre.
    (verdict, not, aksiyon, rulo_farki) döner; not içinde yuvanın şartları (✔/✖) da yazılır."""
    if not item.get("slot") or not res or item.get("kind") not in ("gear", "weapon"):
        return verdict, None, None, None
    st = cfg["settings"]
    act_b = active_build(cfg)
    scores = {n: p for p, n, _ in res}
    if act_b and scores.get(act_b["name"], 0) >= st["consider_threshold"]:
        bname, score = act_b["name"], scores[act_b["name"]]
    elif verdict in ("KEEP", "CONSIDER"):
        score, bname = res[0][0], res[0][1]
    else:
        return verdict, None, None, None
    slot = item["slot"]
    if slot not in build_slots(cfg, bname):
        return verdict, None, None, None
    b = build_by_name(cfg, bname)
    checks = engine.check_slot(item, plan_of(b).get(slot), GAME)
    done = engine.slot_done(checks)
    tail = ("  ·  " + "  ".join(check_lines(checks))) if checks else ""
    cur = progress.get(bname, {}).get(slot)
    act = (bname, slot, score)
    if verdict == "DISMANTLE" and bname == (act_b or {}).get("name"):
        verdict = "CONSIDER"
    if not cur:
        key = "note.fills_gap_done" if done else "note.fills_gap"
        return verdict, t(key, build=bname, slot=slot_name(slot)) + tail, act, None
    if signature(item) == cur.get("sig"):
        return verdict, t("note.already", build=bname, slot=slot_name(slot)), None, None
    diff = roll_diff(cur.get("attrs"), item["attrs"])
    if score > cur["score"] + UPGRADE_MARGIN:
        return verdict, t("note.upgrade", build=bname, slot=slot_name(slot), old=cur["score"], new=score) + tail, act, diff
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

# Programın kendi pencereleri (bindirme kartı) ekran okumasına girmesin: önceki kararın yazıları
# yeni kartın başlığını kapatıp "Iron Will Hotshot …" gibi kendi metnini okutuyordu.
CAPTURE_MASK = {}          # pencere adı -> (x0, y0, x1, y1) ekran; yalnız Windows dışlama çalışmadıysa boyanır

def exclude_from_capture(win, key="overlay"):
    """Windows 10 2004+: WDA_EXCLUDEFROMCAPTURE — oyuncu pencereyi görür, ekran görüntüsünde altındaki oyun görünür.
    Desteklenmezse pencerenin yeri kaydedilir ve okunan görüntüde siyaha boyanır."""
    ok = False
    if os.name == "nt":
        try:
            hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
            ok = bool(ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x11))
        except Exception:
            ok = False
    if ok:
        CAPTURE_MASK.pop(key, None)
    else:
        try:
            win.update_idletasks()
            CAPTURE_MASK[key] = (win.winfo_rootx(), win.winfo_rooty(),
                                 win.winfo_rootx() + win.winfo_width(), win.winfo_rooty() + win.winfo_height())
        except Exception:
            pass
    return ok

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
STT_LANGS = {"tr": "tr", "en": "en", "de": "de", "fr": "fr", "es": "es", "it": "it", "pt": "pt", "ru": "ru", "pl": "pl", "nl": "nl"}


def transcribe(audio, cfg):
    """Konuşma tanıma. 1) faster-whisper (yerel, en iyi), 2) yoksa Windows'un kendi konuşma tanıması (System.Speech).
    Dil arayüz dilini izler. Hata ayrıntısı logs/app.log'a yazılır."""
    lang = STT_LANGS.get(i18n.current_language(), "en")
    try:
        from faster_whisper import WhisperModel
    except Exception as e:
        log.warning("faster-whisper not available (%s: %s) — Python %s; trying Windows speech recognition",
                    type(e).__name__, e, sys.version.split()[0])
        return windows_stt(audio, lang)
    st = cfg["settings"]
    key = (st["stt_model"], st["stt_device"])
    if _WHISPER["key"] != key:
        log.info("Loading Whisper model %s on %s (first time downloads the model)", *key)
        try:
            _WHISPER["model"] = WhisperModel(st["stt_model"], device=st["stt_device"],
                                             compute_type="float16" if st["stt_device"] == "cuda" else "int8")
        except Exception as e:
            if st["stt_device"] != "cpu":                  # CUDA/cuDNN yoksa CPU'ya düş
                log.warning("Whisper on %s failed (%s); falling back to CPU", st["stt_device"], e)
                _WHISPER["model"] = WhisperModel(st["stt_model"], device="cpu", compute_type="int8")
            else:
                raise
        _WHISPER["key"] = key
    segs, _ = _WHISPER["model"].transcribe(audio, language=lang, vad_filter=True)
    return " ".join(s.text.strip() for s in segs).strip()


def windows_stt(audio, lang):
    """Windows'ta kurulu konuşma tanıyıcı ile (çevrimdışı) metne çevirir. Ek paket gerekmez."""
    if os.name != "nt":
        raise RuntimeError(t("err.no_stt"))
    import tempfile, wave
    import numpy as np
    path = Path(tempfile.gettempdir()) / "td2_voice.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    ps = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; Add-Type -AssemblyName System.Speech; "
          "$rs=[System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers(); "
          f"$p=$rs | Where-Object {{ $_.Culture.Name -like '{lang}*' }} | Select-Object -First 1; "
          "if(-not $p){$p=$rs | Select-Object -First 1}; if(-not $p){Write-Output '__NONE__'; exit}; "
          "$e=New-Object System.Speech.Recognition.SpeechRecognitionEngine($p); "
          "$e.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar)); "
          f"$e.SetInputToWaveFile('{path}'); $o=@(); while($r=$e.Recognize()){{$o+=$r.Text}}; "
          "Write-Output ('__CULTURE__'+$p.Culture.Name); Write-Output ($o -join ' ')")
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True,
                       timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    out = r.stdout.decode("utf-8", "replace").strip().splitlines()
    if r.returncode != 0 or not out:
        raise RuntimeError("Windows speech: " + r.stderr.decode("utf-8", "replace").strip()[:200])
    if out[0].strip() == "__NONE__":
        raise RuntimeError(t("err.no_stt"))
    culture = out[0].replace("__CULTURE__", "").strip()
    if not culture.lower().startswith(lang):
        log.warning("Windows speech recognizer for %r not installed; used %s", lang, culture)
    return " ".join(out[1:]).strip()


def voice_diagnostics(cfg):
    """Sesli komut bileşenlerini tek tek dener; satır listesi döner (Asistan → Ses testi)."""
    rows = [f"Python {sys.version.split()[0]} ({sys.executable})"]
    for mod in ("pyttsx3", "sounddevice", "numpy", "faster_whisper"):
        try:
            m = __import__(mod); rows.append(f"✔ {mod} {getattr(m, '__version__', '')}")
        except Exception as e:
            rows.append(f"✖ {mod}: {type(e).__name__}: {e}")
    try:
        import sounddevice as sd
        dev = sd.query_devices(kind="input"); rows.append(f"✔ mic: {dev['name']}")
    except Exception as e:
        rows.append(f"✖ mic: {e}")
    if os.name == "nt":
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-Command",
                                "Add-Type -AssemblyName System.Speech; [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | % { $_.Culture.Name }"],
                               capture_output=True, timeout=30, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            names = r.stdout.decode("utf-8", "replace").split()
            rows.append(("✔ " if names else "✖ ") + "Windows speech: " + (", ".join(names) or "—"))
        except Exception as e:
            rows.append(f"✖ Windows speech: {e}")
    if "faster_whisper" not in " ".join(r for r in rows if r.startswith("✔")) and sys.version_info >= (3, 14):
        rows.append(t("ai.diag_py"))
    for r in rows: log.info("Voice diag: %s", r)
    return rows


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

VISION_SYSTEM = ("You transcribe Tom Clancy's The Division 2 item tooltip screenshots. Read the image file with the Read tool. "
                 "Output ONLY the card text, line by line, top to bottom, exactly as written in the game (keep section headers like "
                 "'Core Attribute', 'Attributes', 'Talents', keep numbers and % signs). No commentary, no markdown.")


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

def ask_claude_code(model, system, history, timeout=CLAUDE_CODE_TIMEOUT, tools="", max_turns=1):
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
            "--tools", tools,               # varsayılan: hiç araç yok (yalnızca cevap). Görev getirme: WebSearch,WebFetch
            "--disallowedTools", "mcp__*",
            "--strict-mcp-config",
            "--no-session-persistence",
            "--max-turns", str(max_turns)]
    if tools:
        args += ["--allowedTools", tools.replace(",", " ")]
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
# Oyundaki menülere göre: Projeler (günlük/haftalık/yerleşim/sezonluk), Yolculuk (sezon sekmesi), Manhunt.
TASK_CATS = ["projects", "journey", "manhunt"]
PROJECT_KINDS = ["daily", "weekly", "settlement", "seasonal"]
AUTO_RESET_KINDS = {"daily", "weekly"}  # sıfırlama sınırı geçince o türdeki projeler temizlenir
# Eski sürümlerin kategorileri (v4 Türkçe adlar, v5.0 daily/weekly/global_event/other) taşınır.
LEGACY_CATS = {"Günlük": "daily", "Haftalık": "weekly", "Journey": "journey",
               "Global Event": "global_event", "Manhunt": "manhunt", "Diğer": "other"}

def split_cat(c):
    """Eski/ham kategori → (kategori, proje türü)."""
    c = LEGACY_CATS.get(c, c)
    if c in PROJECT_KINDS: return "projects", c
    if c in ("journey", "manhunt", "projects"): return c, ""
    return "projects", ""          # global_event / other / bilinmeyen → Projeler (türsüz)

ADD_CHOICES = [("projects", k) for k in PROJECT_KINDS] + [("journey", ""), ("manhunt", "")]

def add_choice_name(cat, kind):
    return f"{cat_name(cat)} – {cat_name(kind)}" if kind else cat_name(cat)

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
    d["items"] = {c: [] for c in TASK_CATS}
    for key, val in items.items():                   # eski kategorileri yeni yapıya taşı
        cat, kind = split_cat(key)
        for it in val or []:
            if kind and not it.get("kind"): it["kind"] = kind
            d["items"][cat].append(it)
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

def task_text(task, lang=None):
    """Görevin yalnızca seçili dildeki metni: (metin, çevrili mi)."""
    lang = lang or i18n.current_language()
    tx = task.get("texts") or {}
    if tx.get(lang): return tx[lang].replace("**", "").strip(), True
    if lang == "tr" and task.get("tr"): return task["tr"], True
    if lang == "en": return task.get("en") or tx.get("en", ""), True
    return task.get("en") or tx.get("en") or task.get("tr", ""), False


def split_title(text):
    """'Red Horizon Yolculuğu – Görev 3: 10 düşmanı yak' → ('Görev 3', '10 düşmanı yak')."""
    text = (text or "").strip()
    m = re.match(r"^(.{3,70}?):\s+(.+)$", text)
    if not m: return "", text
    group, rest = m.group(1).strip(), m.group(2).strip()
    if " – " in group: group = group.split(" – ")[-1].strip()
    elif " - " in group: group = group.split(" - ")[-1].strip()
    return group, rest[:1].upper() + rest[1:]


def task_group(task, cat):
    """Grup anahtarı ve arayüz dilinde grup adı (İngilizce metinden; çeviriler farklı olsa da aynı grup)."""
    en = task.get("en") or (task.get("texts") or {}).get("en", "")
    g_en, _ = split_title(en)
    low = g_en.lower()
    m = re.search(r"(?:mission|görev|scout|sector)\s*(\d+)", low)
    if "classified" in low:
        return "classified", t("grp.classified")
    if "scout" in low and m:
        return f"scout{m.group(1)}", t("grp.scout", n=m.group(1))
    if ("journey" in low or "mission" in low) and m:
        return f"mission{m.group(1)}", t("grp.mission", n=m.group(1))
    loc, _ = split_title(task_text(task)[0])
    return (low or "other"), (loc or g_en or t("tasks.other_group"))


def task_dedupe_key(task):
    """Aynı görevin farklı kaynaklardan gelen kopyaları (ör. ortak liste + wiki) için anahtar."""
    en = task.get("en") or (task.get("texts") or {}).get("en", "")
    g, rest = split_title(en)
    head = re.split(r"\s+[–-]\s+|\s*\(", rest)[0]
    return gamedata.nrm(g.split(" – ")[-1] + "|" + head)[:60]


TASK_KEYWORDS = ["Control Point", "Public Execution", "Stronghold", "Bounty", "Dark Zone", "Countdown", "Summit", "Descent",
                 "Incursion", "Raid", "Manhunt", "Supply Drop", "Convoy", "Hostage", "Propaganda Broadcast", "Resource Transport",
                 "Territory Control", "Global Event", "Legendary", "Heroic", "Expedition", "Kenly College", "Conflict",
                 "Fiery Aura", "Hunter", "Rogue", "Landmark", "Side Mission", "Main Mission", "Classified Assignment",
                 "Settlement", "Castle", "Theater", "Campus", "Brooklyn", "Coney Island", "Battleship"]


def task_image_query(task):
    """Görsel için (wiki sayfası, arama terimi)."""
    title = None
    url = task.get("url") or ""
    if "/wiki/" in url:
        title = urllib.parse.unquote(url.split("/wiki/", 1)[1].split("#")[0]).replace("_", " ")
    en = task.get("en") or (task.get("texts") or {}).get("en", "")
    kw = next((k for k in TASK_KEYWORDS if k.lower() in en.lower()), None)
    return title, kw or (split_title(en)[1][:60] if en else None)


TASK_IMG_DIR = BASE / "cache" / "task_images"


def load_task_images(task, n=3):
    """Wiki'den görevle ilgili görseller (diskte önbellekli). [(PIL.Image, başlık)]."""
    import hashlib
    title, search = task_image_query(task)
    key = hashlib.sha1(f"{title}|{search}".encode("utf-8")).hexdigest()[:16]
    TASK_IMG_DIR.mkdir(parents=True, exist_ok=True)
    idx = TASK_IMG_DIR / f"{key}.json"
    out = []
    try:
        meta = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else None
        if meta is None:
            meta = []
            for k, (url, page) in enumerate(wiki_sync.images_for(title, search, n=n, app_version=APP_VERSION)):
                f = TASK_IMG_DIR / f"{key}_{k}.img"
                f.write_bytes(wiki_sync.fetch_bytes(url, APP_VERSION))
                meta.append({"file": f.name, "page": page})
            idx.write_text(json.dumps(meta), encoding="utf-8")
        for m in meta:
            try: out.append((Image.open(TASK_IMG_DIR / m["file"]).convert("RGB"), m["page"]))
            except Exception: pass
    except Exception as e:
        log.info("Task images unavailable (%s)", e)
    return out


def claude_tasks_prompt():
    lang = i18n.english_name()
    return ("You are a research assistant for the game Tom Clancy's The Division 2. Use web search to find what is CURRENT "
            f"today ({datetime.now().strftime('%Y-%m-%d')}): the running season's Journey missions, Manhunt scout tasks, "
            "and active daily/weekly projects or global events. Prefer official Ubisoft news, patch notes and The Division Wiki. "
            "Do not invent anything; skip what you cannot confirm. Reply with ONLY one JSON object, no prose, in this shape: "
            '{"season": "...", "tasks": [{"cat": "projects|journey|manhunt", "kind": "daily|weekly|seasonal|settlement (projects only, else empty)", '
            '"en": "short English task, e.g. Journey 3: burn 10 enemies with one Fiery Aura (5x)", '
            f'"text": "the same task in {lang}", "how_en": "1-2 sentence English how-to", "how": "the same how-to in {lang}", '
            '"url": "https source"}]}. At most 30 tasks. Keep each task under 120 characters.')


def parse_claude_tasks(raw):
    """Claude'un JSON yanıtını görev kayıtlarına çevirir: {kategori: [görev]}."""
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m: return {}, ""
    data = json.loads(m.group(0))
    lang = i18n.current_language()
    out = {}
    for x in data.get("tasks", [])[:40]:
        cat, kind = split_cat(str(x.get("cat", "")).lower())
        if cat not in TASK_CATS: continue
        en = str(x.get("en", "")).strip()[:200]
        if not en: continue
        kind = (str(x.get("kind", "")).lower() if cat == "projects" else "") or kind
        task = {"en": en, "texts": {"en": en}, "src": "Claude", "done": False, "time": datetime.now().isoformat(timespec="seconds")}
        if x.get("text"): task["texts"][lang] = str(x["text"]).strip()[:200]
        how = {}
        if x.get("how_en"): how["en"] = str(x["how_en"]).strip()[:500]
        if x.get("how"): how[lang] = str(x["how"]).strip()[:500]
        if how: task["how"] = how
        if str(x.get("url", "")).startswith("https://"): task["url"] = str(x["url"])[:300]
        if cat == "projects" and kind in PROJECT_KINDS: task["kind"] = kind
        out.setdefault(cat, []).append(task)
    return out, str(data.get("season", ""))[:60]


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


# ───────────── Uygulama ─────────────
class App:
    def __init__(self):
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
        self.normalize_builds()
        self.ent = features.Entitlements(stg.get("license_key", ""))
        log.info("Tier: %s (%s)", self.ent.tier, self.ent.reason)
        self.stash = stash.Stash(STASH_PATH)
        self.vendor_week = vendor.load_cache(VENDOR_CACHE)
        self.vendor_scans, self.vendor_hits, self.vendor_busy = [], [], False
        self.companion, self.comp_state = None, {}
        self.dropq = dropstats.Queue(DROPQ_PATH)
        if not stg.get("drop_client"):
            stg["drop_client"] = dropstats.new_client_id(); save_cfg(self.cfg)
        self.last_text, self.drops_busy = "", False
        if not self.stash.data.get("imported_progress"):          # eski sürümün kayıtları bir kez aktarılır
            try:
                n = self.stash.import_progress(self.progress, GAME) if GAME.ok else 0
                self.stash.data["imported_progress"] = True; self.stash.save()
                if n: log.info("Stash: imported %d items from progress.json", n)
            except Exception:
                log.exception("Stash import failed")
        apply_ocr_settings(stg)
        self._prof_key = active_profile(stg)[0]
        log.info("Display profile: %s, OCR threshold %s, scale %s", self._prof_key, gamedata.THRESHOLD, gamedata.SCALE or "auto")
        self.tess = find_tesseract(self.cfg)
        self.listener, self.auto_stop, self.running = None, None, False
        self.lock, self.results = threading.Lock(), queue.Queue()
        self.counts = {"KEEP": 0, "CONSIDER": 0, "DISMANTLE": 0, "REVIEW": 0}
        self.overlay = self.overlay_job = self.cur = self.last_scan = None
        self.root_after_resets = None
        self.last_sig, self.last_time, self.last_err = None, 0, ""
        self.speaker, self.rec, self.voice_busy, self.chat_hist = Speaker(), Recorder(), False, []

        display.set_dpi_aware()                         # %125/%150 Windows ölçeğinde koordinatlar kaymasın
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.set_app_icon()
        self._base_scaling = float(self.root.tk.call("tk", "scaling"))
        self.apply_window_profile(initial=True)
        self.sounds = ui_theme.Sounds(BASE / "sounds", enabled=bool(stg.get("ui_sounds", True)))
        ui_theme.bind_click_sounds(self.root, self.sounds)
        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.meta_busy = False
        self.poll(); self.check_resets()
        self.root.after(2500, self.meta_sync_start)     # açılışı bekletmeden, günde bir
        self.root.after(6000, lambda: self.vendor_refresh(auto=True))
        self.root.after(4000, self.ask_drop_consent)
        self.root.after(9000, lambda: self.check_update(auto=True))
        self.root.after(20000, self._drops_tick)
        log.info("UI ready — language=%s, OCR=%s, tesseract=%s", i18n.current_language(), OCR.name, self.tess or "NOT FOUND")
        OCR.warm_up()
        if OCR.name == "tesseract" and not self.tess:
            messagebox.showwarning(APP_NAME, t("msg.no_tesseract"))

    def set_app_icon(self):
        """Pencere ve görev çubuğu simgesi (icon/td2.ico, td2.png). Windows'ta görev çubuğunda Python simgesi yerine
        uygulamanın kendi simgesi görünsün diye ayrı bir AppUserModelID verilir."""
        if os.name == "nt":
            try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FEDERALTURK.TD2LootAdvisor")
            except Exception: pass
        for folder in (BASE / "icon", BUNDLE / "icon"):
            try:
                if os.name == "nt" and (folder / "td2.ico").exists():
                    self.root.iconbitmap(default=str(folder / "td2.ico"))
                if (folder / "td2.png").exists():
                    self._icon_img = ImageTk.PhotoImage(Image.open(folder / "td2.png").resize((64, 64), Image.LANCZOS))
                    self.root.iconphoto(True, self._icon_img)
                    return
            except Exception:
                log.debug("icon failed", exc_info=True)

    def restart_app(self, tab=None, page=None):
        """Programı aynı ayarlarla yeniden açar (pencere/yazı ölçeği değişince)."""
        st = self.cfg["settings"]
        st["_start_tab"], st["_start_page"] = tab or "", page or ""
        save_cfg(self.cfg)
        if getattr(sys, "frozen", False):
            args = [sys.executable] + sys.argv[1:]
        else:
            args = [sys.executable, str(Path(__file__).resolve())] + sys.argv[1:]
        log.info("Restarting: %s", args)
        try:
            subprocess.Popen(args, cwd=str(BASE), creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        except Exception as e:
            log.warning("Restart failed: %s", e); return
        self.on_close()

    def apply_window_profile(self, initial=False):
        """Pencereyi seçilen çözünürlük profiline göre boyutlandırır: 240p'den 4K'ya kadar her ekranda sığar.
        Küçük ekranlarda yazılar/boşluklar küçülür (tk scaling), başlık bandı incelir (kompakt mod)."""
        st = self.cfg["settings"]
        key, prof = active_profile(st)
        try: pw, ph = map(int, key.split("x"))
        except ValueError: pw, ph = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        tw, th = min(pw, sw), min(ph, sh)                 # profil ekrandan büyükse ekran sınırı
        # yazı ölçeği: 1080p = 1.0 → 720p ≈ 0.8, 480p ≈ 0.62, 240p ≈ 0.5, 1440p ≈ 1.1, 4K ≈ 1.3
        f = max(0.5, min(1.35, (th / 1080) ** 0.55))
        self.ui_factor = f
        self.compact = th < 800
        try: self.root.tk.call("tk", "scaling", self._base_scaling * f)
        except tk.TclError: pass
        ww, wh = (int(tw * 0.98), int(th * 0.92)) if self.compact else \
                 ((1700, 1080) if tw >= 3000 and th >= 1300 else (1360, 900) if tw >= 1900 else (min(1240, tw - 40), min(860, th - 60)))
        self.root.minsize(min(880, max(320, ww - 20)), min(640, max(200, wh - 20)))
        x = max(0, (sw - ww) // 2); y = max(0, (sh - wh) // 3)
        self.root.geometry(f"{ww}x{wh}+{x}+{y}")
        log.info("Window profile %s: %dx%d, ui scale %.2f, compact=%s", key, ww, wh, f, self.compact)

    def apply_fx(self):
        """İmleç, fare izi ve arka plan videosunu ayarlara göre aç/kapat."""
        st = self.cfg["settings"]
        if not hasattr(self, "cursor_fx"): self.cursor_fx = fx.CursorFX(self.root, ART_DIR / "cursors")
        ok = self.cursor_fx.apply(st.get("fx_cursor", True), st.get("fx_cursor_style", "crosshair"),
                                  st.get("fx_cursor_color", "#ff6d10"), st.get("fx_cursor_custom", ""), getattr(self, "ui_factor", 1.0))
        if not ok: log.warning("Custom cursor could not be applied")
        tr = getattr(self, "trail_fx", None)
        if st.get("fx_trail", True):
            if tr and (tr.color != st.get("fx_trail_color") or tr.length != int(st.get("fx_trail_len", 18))):
                tr.stop(); tr = None
            if not tr or not tr.alive:
                self.trail_fx = fx.TrailFX(self.root, st.get("fx_trail_color", "#ff6d10"), st.get("fx_trail_len", 18), click_through)
                self.trail_fx.start()
        elif tr:
            tr.stop(); self.trail_fx = None
        if float(st.get("fx_video_dim", 0.35)) > 0.7: st["fx_video_dim"] = 0.35     # eski sürümden kalan çok koyu ayar
        # tüm pencere arka planı: ajan saati (Windows, koyu temalar)
        wb = getattr(self, "watch_bg", None)
        want = bool(st.get("fx_bgwatch", True)) and os.name == "nt" and PAL.get("mode") != "light"
        if wb and (not want or wb.bgc != PAL["bg"] or wb.color != PAL["accent"] or wb.dim != float(st.get("fx_bgwatch_dim", 0.0))):
            wb.stop(); self.watch_bg = wb = None
        if want and not wb:
            self.watch_bg = fx.WatchBackground(self.root, PAL["bg"], PAL["accent"], float(st.get("fx_bgwatch_dim", 0.0)))
            if not self.watch_bg.start():
                log.info("Agent watch background unavailable"); self.watch_bg = None
        watch_on = bool(getattr(self, "watch_bg", None))
        if hasattr(self, "banner"): self.banner.set_transparent(watch_on)
        v = getattr(self, "video", None)
        if v: v.stop(); self.video = None
        if hasattr(self, "banner"):
            self.banner.stop_video() if self.banner.video_on else None
            if st.get("fx_video", True) and not watch_on:
                (ART_DIR / "videos").mkdir(parents=True, exist_ok=True)
                self.video = fx.VideoFX(ART_DIR / "videos", self.banner.push_video, self.banner.video_size,
                                        dim=min(0.7, float(st.get("fx_video_dim", 0.35))))
                if self.video.start():
                    self.banner.start_video(); log.info("Background video on (%s)", fx.video_backend())
                else:
                    log.info("Background video off: %s", self.video.error)
                    if self.video.error == "no_videos":
                        self.make_videos()                         # ilk açılış: özgün arka plan videolarını üret
                    self.video = None

    def normalize_builds(self):
        """Build'lerdeki talent/eşya karışıklığını oyun kütüphanesine göre düzeltir (Equalizer → items)."""
        changed = False
        for b in self.cfg["builds"]:
            ch, unk = engine.normalize_build(b, GAME)
            changed |= ch
            if unk: log.warning("Build %r: unknown talents %s (not in game library)", b["name"], unk)
        if changed:
            save_cfg(self.cfg); log.info("Builds normalized against game library")

    def build_ui(self):
        """Tema + başlık bandı + tüm sekmeler. Tema/dil değişince rebuild_ui() ile yeniden kurulur."""
        set_palette(ui_theme.apply(self.root, self.cfg["settings"].get("ui_theme", "dark")))
        self.build_header()
        self.fxbar = fx.Transition(self.root, self.root, color=PAL["accent"], bg=PAL["bg"],
                                   duration_ms=int(self.cfg["settings"].get("fx_transition_ms", 650)))
        nb = self.nb = ttk.Notebook(self.root); nb.pack(fill="both", expand=True, padx=10, pady=(6, 10))
        # Sekmeler sabit kimliklerle tutulur, başlıkları t() ile çevrilir.
        self.tab_keys = ("dash", "builds", "progress", "stash", "stats", "tasks", "assistant", "settings", "history", "log", "help")
        self.tabs = {k: ttk.Frame(nb) for k in self.tab_keys}
        for k in self.tab_keys: nb.add(self.tabs[k], text=ui_theme.with_icon(t(f"tab.{k}"), ui_theme.TAB_ICONS.get(k, "")))
        self.build_dash(); self.build_builds(); self.build_prog(); self.build_stash(); self.build_stats(); self.build_gorevler(); self.build_asistan()
        self.build_settings(); self.build_hist(); self.build_logtab(); self.build_help()
        nb.bind("<<NotebookTabChanged>>", self.on_tab)
        self.root.after(300, self.apply_fx)
        st = self.cfg["settings"]
        if st.get("_start_tab") in self.tab_keys:                       # yeniden açılıştan sonra kaldığı yere dön
            self.nb.select(self.tab_keys.index(st["_start_tab"]))
            if st.get("_start_page") in getattr(self, "_set_keys", []):
                self.set_nb.select(self._set_keys.index(st["_start_page"]))
            st["_start_tab"] = st["_start_page"] = ""; save_cfg(self.cfg)

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
        if getattr(self, "video", None): self.video.stop(); self.video = None
        try: self.banner.destroy()
        except Exception: pass
        try: self.fxbar.destroy()
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
                                    title="◆ TD2 LOOT ADVISOR", subtitle=f"v{APP_VERSION}",
                                    height=max(44, int(118 * getattr(self, "ui_factor", 1.0) * (0.6 if getattr(self, "compact", False) else 1.0))))
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
        if self.cfg["settings"].get("fx_transitions", True) and hasattr(self, "fxbar"): self.fxbar.play()
        k = self.current_tab()
        if k == "history": self.load_history()
        elif k == "stats": self.root.after(50, self.refresh_stats_tab)
        elif k == "progress": self.refresh_prog()
        elif k == "stash": self.refresh_stash()
        elif k == "log": self.refresh_logtab()

    # ---------- Panel ----------
    def build_dash(self):
        """Panel v2 — geniş ekran (21:9) için iki sütun: solda kontrol + karar, sağda eşya kartı ve build eşleşmeleri."""
        f = self.tabs["dash"]
        st = self.cfg["settings"]
        paned = ttk.Panedwindow(f, orient="horizontal"); paned.pack(fill="both", expand=True, padx=10, pady=10)
        left, right = ttk.Frame(paned), ttk.Frame(paned)
        paned.add(left, weight=2); paned.add(right, weight=3)

        top = ttk.Frame(left); top.pack(fill="x")
        self.btn_run = ttk.Button(top, text=t("btn.start"), command=self.toggle, style="Success.TButton"); self.btn_run.pack(side="left")
        ttk.Button(top, text="🔍 " + t("btn.scan_now"), command=self.trigger, style="Accent.TButton").pack(side="left", padx=6)
        ttk.Button(top, text=ui_theme.with_icon(t("btn.pick_region"), "⛶"), command=self.calibrate).pack(side="left")
        ttk.Button(top, text=ui_theme.with_icon(t("btn.test_image"), "🖼"), command=self.test_image).pack(side="left", padx=6)

        src = ttk.Frame(left); src.pack(fill="x", pady=(8, 0))
        ttk.Label(src, text=t("panel.source"), foreground=PAL["muted"]).pack(side="left")
        self.src_var = tk.StringVar(value=st.get("scan_source", "screen"))
        for txt, val in ((t("panel.src_screen"), "screen"), (t("panel.src_region"), "region")):
            ttk.Radiobutton(src, text=txt, value=val, variable=self.src_var, command=self.change_source).pack(side="left", padx=6)
        mode = ttk.Frame(left); mode.pack(fill="x", pady=(2, 0))
        ttk.Label(mode, text=t("panel.scan_mode"), foreground=PAL["muted"]).pack(side="left")
        self.mode_var = tk.StringVar(value=st["scan_mode"])
        for txt, val in ((t("mode.hotkey"), "hotkey"), (t("mode.auto"), "auto")):
            ttk.Radiobutton(mode, text=txt, value=val, variable=self.mode_var, command=self.change_mode).pack(side="left", padx=6)
        ab = ttk.Frame(left); ab.pack(fill="x", pady=(4, 0))
        ttk.Label(ab, text="⭐ " + t("plan.active"), foreground=PAL["accent"]).pack(side="left")
        self.act_cb = ttk.Combobox(ab, state="readonly", width=44, values=[b["name"] for b in self.cfg["builds"]])
        a0 = active_build(self.cfg)
        if a0: self.act_cb.set(a0["name"])
        self.act_cb.pack(side="left", padx=6)
        self.act_cb.bind("<<ComboboxSelected>>", lambda e: self.set_active_build(self.act_cb.get()))
        self.act_prog = ttk.Label(ab, text="", foreground=PAL["muted"]); self.act_prog.pack(side="left", padx=6)
        ac = ttk.Frame(left); ac.pack(fill="x", pady=(4, 0))
        ttk.Label(ac, text="🎮 " + t("drops.activity")).pack(side="left")
        self._acts = {k: t("act." + k) for k in dropstats.ACTIVITIES}
        self.drop_act = ttk.Combobox(ac, state="readonly", width=22, values=list(self._acts.values()))
        self.drop_act.set(self._acts.get(st.get("drop_activity", "none"), self._acts["none"]))
        self.drop_act.pack(side="left", padx=6)
        self.drop_act.bind("<<ComboboxSelected>>", lambda e=None: self._set_activity())
        ttk.Label(ac, text=t("drops.activity_hint"), foreground=PAL["muted"]).pack(side="left", padx=4)
        tb = ttk.Frame(left); tb.pack(fill="x", pady=(4, 0))
        ttk.Button(tb, text="🤖 " + t("ai.ask_item"), command=self.ask_about_item).pack(side="left")
        ttk.Button(tb, text="👁 " + t("ai.vision_read"), command=self.vision_read).pack(side="left", padx=6)
        ttk.Button(tb, text="⚑ " + t("report.wrong"), command=self.report_wrong).pack(side="left")
        self.status = ttk.Label(left, foreground=PAL["muted"], wraplength=560, justify="left"); self.status.pack(anchor="w", pady=(4, 2))

        card = ttk.Frame(left, style="Card.TFrame", padding=(0, 0, 0, 12)); card.pack(fill="x", pady=(6, 8))
        self.verdict_lbl = tk.Label(card, text=verdict_label("IDLE"), bg=COLORS["IDLE"], fg="white",
                                    font=(ui_theme.FONT_SEMI, 34), pady=20)
        self.verdict_lbl.pack(fill="x")
        self.item_lbl = ttk.Label(card, text="—", style="Item.TLabel", wraplength=560); self.item_lbl.pack(anchor="w", padx=16, pady=(10, 0))
        self.note_lbl = ttk.Label(card, text="", style="Note.TLabel", wraplength=560, justify="left"); self.note_lbl.pack(anchor="w", padx=16)
        self.fit_lbl = tk.Label(card, text="", wraplength=560, justify="left", bg=PAL["surface"], fg=PAL["muted"],
                                font=(ui_theme.FONT, 10)); self.fit_lbl.pack(anchor="w", padx=16, pady=(4, 0))
        chips = ttk.Frame(left); chips.pack(fill="x", pady=(0, 6))
        self.count_chips = {}
        for v in ("KEEP", "CONSIDER", "DISMANTLE", "REVIEW"):
            lb = tk.Label(chips, bg=PAL["surface"], fg=VFG[v], font=(ui_theme.FONT_SEMI, 10), padx=12, pady=5)
            lb.pack(side="left", padx=(0, 8)); self.count_chips[v] = lb
        ttk.Label(left, text=t("panel.card_preview"), style="Section.TLabel").pack(anchor="w", pady=(6, 2))
        self.card_img_lbl = tk.Label(left, bg=PAL["surface"], text=t("panel.no_card"), fg=PAL["muted"], height=12)
        self.card_img_lbl.pack(fill="both", expand=True)

        ttk.Label(right, text=t("panel.item_box"), style="Section.TLabel").pack(anchor="w")
        self.item_tv = ttk.Treeview(right, columns=("a", "v", "m", "q"), show="headings", height=8)
        for c, hd, w in (("a", t("panel.col_attr"), 220), ("v", t("panel.col_value"), 110), ("m", t("panel.col_max"), 110), ("q", t("panel.col_quality"), 220)):
            self.item_tv.heading(c, text=hd); self.item_tv.column(c, width=w, anchor="w" if c in ("a", "q") else "center")
        self.item_tv.pack(fill="x", pady=(2, 4))
        self.tal_lbl = ttk.Label(right, text="", wraplength=900, justify="left"); self.tal_lbl.pack(anchor="w", pady=(0, 8))
        ttk.Label(right, text=t("panel.matches"), style="Section.TLabel").pack(anchor="w")
        self.match_tv = ttk.Treeview(right, columns=("p", "b", "w"), show="headings", height=8)
        for c, hd, w in (("p", "%", 60), ("b", t("panel.col_build"), 280), ("w", t("panel.col_why"), 560)):
            self.match_tv.heading(c, text=hd); self.match_tv.column(c, width=w, anchor="center" if c == "p" else "w")
        self.match_tv.pack(fill="x", pady=(2, 6))
        dbg = ttk.Frame(right); dbg.pack(fill="x")
        self.dbg_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dbg, text=t("panel.show_ocr"), variable=self.dbg_var, command=lambda: self.last_shown and self.show_result(*self.last_shown)).pack(side="left")
        self.out = tk.Text(right, height=8, state="disabled", font=("Consolas", 10), wrap="word"); self.out.pack(fill="both", expand=True, pady=(4, 0))
        self.stats = ttk.Label(f)
        self.last_shown = None
        self.refresh_counts(); self.refresh_status()

    def show_fit(self, item):
        """Panel: bu eşya aktif build'in ilgili yuvasının şartlarını karşılıyor mu?"""
        if not hasattr(self, "fit_lbl"): return
        b = active_build(self.cfg)
        stt = self.build_status(b) if b else {}
        have = sum(1 for v in stt.values() if v[0] in ("done", "partial")); tot = sum(1 for v in stt.values() if v[0] != "off")
        if hasattr(self, "act_prog"): self.act_prog.config(text=t("prog.completed", have=have, total=tot) if tot else "")
        slot = item.get("slot")
        if not b or not slot or item.get("kind") not in ("gear", "weapon"):
            self.fit_lbl.config(text=""); return
        req = plan_of(b).get(slot)
        checks = engine.check_slot(item, req, GAME)
        if not checks:
            self.fit_lbl.config(text=t("plan.not_in_build", slot=slot_name(slot)), fg=PAL["muted"]); return
        ok = engine.slot_done(checks)
        head = t("plan.fit_ok" if ok else "plan.fit_no", build=b["name"], slot=slot_name(slot))
        self.fit_lbl.config(text=head + "\n" + "\n".join(check_lines(checks)), fg=PAL["success"] if ok else PAL["warning"])

    def change_source(self):
        self.cfg["settings"]["scan_source"] = self.src_var.get(); save_cfg(self.cfg)
        self.card_box = None; self.refresh_status()

    def show_result(self, text, item, verdict, res, note=None, debug=False, diff=None):
        self.last_shown = (text, item, verdict, res, note, debug, diff)
        self.verdict_lbl.config(text=verdict_label(verdict), bg=COLORS[verdict])
        kind = t("kind." + item["kind"]) if item.get("kind") else ""
        self.item_lbl.config(text=item["name"] + ("  [" + ", ".join(item["rarity"]) + "]" if item["rarity"] else "") +
                             (f"  ·  {slot_name(item['slot'])}" if item.get("slot") else "") + (f"  ·  {kind}" if kind else ""))
        notes = [n for n in (item.get("_note"), note) if n and "  ·  " not in n]
        notes += [n.split("  ·  ")[0] for n in (note,) if n and "  ·  " in n]
        self.note_lbl.config(text="\n".join("» " + n for n in notes))
        self.show_fit(item)
        self.item_tv.delete(*self.item_tv.get_children())
        proto = "PROTOTYPE" in item.get("rarity", [])
        for k, v in item.get("attrs", {}).items():
            mx = GAME.max_of(k, proto) if GAME.ok else None
            q = item.get("quality", {}).get(k)
            bar = ("█" * round((q or 0) / 10)).ljust(10, "░") + f"  {q}%" if q is not None else "—"
            self.item_tv.insert("", "end", values=(attr_name(k), f"{v:g}", f"{mx:g}" if mx else "—", bar))
        bits = []
        if item.get("gear_set") or item.get("brand"):
            bits.append("🏷 " + " / ".join(x for x in (item.get("gear_set"), item.get("brand")) if x))
        if item.get("talents"): bits.append("✦ " + ", ".join(item["talents"]))
        if "confidence" in item: bits.append(t("panel.confidence", pct=round(item["confidence"] * 100)))
        self.tal_lbl.config(text="     ".join(bits))
        self.match_tv.delete(*self.match_tv.get_children())
        for p, n, w in res[:8]:
            self.match_tv.insert("", "end", values=(p, n, ", ".join(w) if w else "—"))
        body = ""
        if diff: body += t("panel.roll_header").strip() + "\n" + "\n".join("  " + d for d in diff) + "\n"
        if debug or (hasattr(self, "dbg_var") and self.dbg_var.get()):
            body += t("panel.ocr_text") + text + t("panel.parsed") + json.dumps(item, ensure_ascii=False, indent=1)
        self.out.config(state="normal"); self.out.delete("1.0", "end"); self.out.insert("end", body); self.out.config(state="disabled")
        img = getattr(self, "last_card_img", None)
        if img is not None:
            try:
                th = img.copy(); th.thumbnail((520, 640))
                self._card_photo = ImageTk.PhotoImage(th)
                self.card_img_lbl.config(image=self._card_photo, text="", height=0)
            except Exception:
                pass

    def refresh_status(self):
        r = self.cfg["settings"].get("region")
        st = self.cfg["settings"]
        mode = t("state.auto") if st["scan_mode"] == "auto" else t("state.key", key=st["hotkey"])
        self.status.config(text=t("status.line",
                                  state=t("state.running") if self.running else t("state.stopped"),
                                  mode=mode,
                                  region=(t("panel.src_screen_short") if st.get("scan_source", "screen") == "screen"
                                          else (f"{r['width']}x{r['height']}" if r else t("state.not_set")))))
        self.refresh_header()

    def refresh_counts(self):
        c = self.counts
        self.stats.config(text=t("status.counts", keep=c["KEEP"], consider=c["CONSIDER"],
                                  dismantle=c["DISMANTLE"], review=c["REVIEW"]))
        for v, lb in getattr(self, "count_chips", {}).items():
            lb.config(text=f"{verdict_label(v)}  {c[v]}")

    # ---------- çalıştırma ----------
    def change_mode(self):
        self.cfg["settings"]["scan_mode"] = self.mode_var.get(); save_cfg(self.cfg)
        if self.running:
            self.stop(); self.start()
        self.refresh_status()

    def toggle(self):
        self.stop() if self.running else self.start()

    def start(self, quiet=False):
        if self.cfg["settings"].get("scan_source", "screen") == "region" and not self.cfg["settings"].get("region"):
            return messagebox.showinfo(APP_NAME, t("msg.pick_region_first"))
        try:
            from pynput import keyboard
            hk = {self.cfg["settings"]["hotkey"]: self.trigger}
            vh = self.cfg["settings"].get("voice_hotkey")
            if vh and vh not in hk: hk[vh] = self.toggle_voice
            gh = self.cfg["settings"].get("tasks_hotkey")
            if gh and gh not in hk: hk[gh] = self.run_claude_fetch
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
        self.card_x = None; self.card_box = None
        if self.window_overlaps_region():
            log.info("Main window overlaps the scan region: minimizing")
            self.toast(t("scan.minimized"))
            self.root.after(1200, self.root.iconify)
        log.info("Scanning started (mode=%s)", self.cfg["settings"]["scan_mode"])

    def stop(self, quiet=False):
        if self.listener: self.listener.stop(); self.listener = None
        if self.auto_stop: self.auto_stop.set(); self.auto_stop = None
        self.running = False; self.btn_run.config(text=t("btn.start"), style="Success.TButton"); self.refresh_status()
        if hasattr(self, "sounds") and not quiet: self.sounds.play("stop")
        log.info("Scanning stopped")

    def region_rect(self):
        r = self.scan_area() or {}
        return (r.get("left", 0), r.get("top", 0), r.get("left", 0) + r.get("width", 0), r.get("top", 0) + r.get("height", 0))

    @staticmethod
    def rects_overlap(a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    def window_overlaps_region(self):
        try:
            self.root.update_idletasks()
            x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
            return self.rects_overlap((x, y, x + self.root.winfo_width(), y + self.root.winfo_height()), self.region_rect())
        except Exception:
            return False

    def trigger(self):  # pynput thread'inden de çağrılır: tk'ya dokunma
        region = self.scan_area()
        if region and self.cfg["settings"].get("only_game_active", True) and not game_active():
            return log.info("Hotkey ignored: game window is not in front")
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
        box = getattr(self, "card_box", None)
        tried_fresh = False
        if box is None:
            box = find_card(img); tried_fresh = True
        card = img.crop(box) if box else img
        t_ocr = time.perf_counter()
        text, lines = read_card(card)
        self._note_ocr_time(time.perf_counter() - t_ocr)
        item, verdict, res = evaluate(text, self.cfg)
        if not valid_item(item) and not tried_fresh:                  # kart yer değiştirmiş: yeniden bul
            box = find_card(img)
            card = img.crop(box) if box else img
            text, lines = read_card(card)
            item, verdict, res = evaluate(text, self.cfg)
        self.card_box = box if valid_item(item) else None
        if s.get("ocr_passes_auto", True):
            passes = self.auto_passes()                      # bilgisayarın hızına göre 1-3 okuma
        else:
            try: passes = max(1, min(3, int(s.get("ocr_passes", 3))))
            except (TypeError, ValueError): passes = 3
        fresh = not (auto and signature(item) == self.last_sig and time.time() - self.last_time < DEDUP_SECONDS)
        if passes > 1 and valid_item(item) and fresh:
            # çoklu geçiş: aynı kart farklı eşik (Tesseract) ya da ölçekle (RapidOCR) yeniden okunur,
            # en çok bilgi tanınan metin seçilir (gerçek 3440×1440 kartta tek okuma bazen bir satırı kaçırıyor)
            best_q, best_t = ocr_quality(text), text
            base = gamedata.THRESHOLD
            try:
                if OCR.name == "rapidocr":
                    a = ocr_scale() or ocr_backend.Engine.auto_scale(card)
                    for sc in [x for x in (2.0, 1.0, 1.5) if abs(x - a) > 0.1][:passes - 1]:
                        tx, _ = read_card(card, scale=sc)
                        q = ocr_quality(tx)
                        if q > best_q: best_q, best_t = q, tx
                else:
                    for th in (base + 10, base - 40)[:passes - 1]:
                        gamedata.THRESHOLD = max(90, min(235, th))
                        tx, _ = read_card(card)
                        q = ocr_quality(tx)
                        if q > best_q: best_q, best_t = q, tx
            finally:
                gamedata.THRESHOLD = base
            if best_t is not text:
                text = best_t
                item, verdict, res = evaluate(text, self.cfg)
            log.debug("OCR multi-pass: %d passes, quality %.1f", passes, best_q)
        try:
            card.save(BASE / "last_card.png")
            (APPLOG_DIR / "last_ocr.txt").write_text(text, encoding="utf-8")
        except Exception:
            pass
        text, item, verdict, res = self.merge_scrolled(text, item, verdict, res)
        try:
            learned = GAME.learn(item) if GAME.ok else []
            if learned:
                log.info("Library learned: %s", "; ".join(learned))
                item, verdict, res = evaluate(text, self.cfg)      # yeni bilgiyle yeniden değerlendir
                self.root.after(0, lambda m="; ".join(learned): self.toast("📚 " + m))
        except Exception:
            log.debug("library learn failed", exc_info=True)
        verdict = color_hints(card, lines, item, verdict)
        self.save_ocr_history(text, item, verdict)
        sig = signature(item)
        if auto:
            if not valid_item(item): return
            if sig == self.last_sig and time.time() - self.last_time < DEDUP_SECONDS: return
        self.last_card_img = card
        try:                                              # kartın ekrandaki yeri: bindirme yanına konur
            a = self.scan_area()
            bx = box or (0, 0, img.width, img.height)
            self.last_card_screen = (a["left"] + bx[0], a["top"] + bx[1], a["left"] + bx[2], a["top"] + bx[3])
        except Exception:
            self.last_card_screen = None
        self.last_sig, self.last_time = sig, time.time()
        self.results.put(("ok", text, item, verdict, res, sig))

    def save_ocr_history(self, text, item, verdict):
        """Tanı için son 200 okuma: logs/ocr_history/<zaman>.txt (okunan metin + programın yorumu).
        Yalnız kart metni; ekran görüntüsü ya da kişisel bilgi yok."""
        try:
            d = APPLOG_DIR / "ocr_history"; d.mkdir(parents=True, exist_ok=True)
            sig = signature(item)
            if sig == getattr(self, "_hist_sig", None): return
            self._hist_sig = sig
            v = verdict[0] if isinstance(verdict, (tuple, list)) else verdict
            head = (f"name={item.get('name')} kind={item.get('kind')} slot={item.get('slot')} rarity={item.get('rarity')} "
                    f"partial={item.get('partial')} merged={item.get('_merged', False)} verdict={v}\n"
                    f"attrs={item.get('attrs')} talents={item.get('talents')}\n----\n")
            (d / (time.strftime("%Y%m%d_%H%M%S") + f"_{int(time.time()*1000)%1000:03d}.txt")).write_text(head + text, encoding="utf-8")
            files = sorted(d.glob("*.txt"))
            for f in files[:-200]: f.unlink()
        except Exception:
            log.debug("ocr history save failed", exc_info=True)

    # ---------- bilgisayar hızına uyum ----------
    def _note_ocr_time(self, dt):
        """Tek kart okumasının süresi (sn): kayan ortalama. Zayıf işlemcide okuma sayısı azaltılır."""
        ema = getattr(self, "ocr_ema", None)
        self.ocr_ema = dt if ema is None else ema * 0.7 + dt * 0.3

    def auto_passes(self):
        ema = getattr(self, "ocr_ema", None)
        if ema is None: n = 2
        elif ema <= 0.7: n = 3
        elif ema <= 1.5: n = 2
        else: n = 1
        if n != getattr(self, "_passes_logged", None):
            self._passes_logged = n
            log.info("OCR speed: %s per read -> %d pass(es)", f"{ema:.2f}s" if ema is not None else "unknown", n)
        return n

    def merge_scrolled(self, text, item, verdict, res):
        """Uzun kartlar ekrana sığmaz; oyuncu kartı kaydırır. Aynı eşyanın ardışık okumaları birleştirilir:
        önce üst kısım (ad, set, çekirdek), sonra alt kısım (attribute, mod, talent) okunur → tek eşya."""
        now = time.time()
        prev = getattr(self, "card_session", None)
        kind_ok = item.get("kind") in ("gear", "weapon")
        if prev and now - prev["t"] < 60 and kind_ok:
            # aynı set/markanın farklı parçaları aynı adla okunur (ör. Striker eldiveni ve dizliği): yuva farklıysa ayrı eşya
            slot_ok = item.get("slot") == prev["item"].get("slot") or (item.get("partial") and not item.get("slot"))
            kind_same = item.get("kind") == prev["item"].get("kind")
            same = item["name"] not in ("?", "") and gamedata.nrm(item["name"]) == gamedata.nrm(prev["item"]["name"])
            # devam parçası: adı görünmeyen alt kısım. Aynı türde olmalı (silah ≠ zırh) ve kendi başlığı
            # (nadirlik satırı: Exotic / High-End …) görünmemeli — başlık varsa bu yeni bir kartın üstüdür.
            cont = item.get("partial") and not prev["item"].get("partial") and not item.get("rarity")
            if (same or cont) and kind_same and slot_ok and prev["text"].strip() != text.strip():
                merged_text = prev["text"] + "\n" + text
                item2, verdict2, res2 = evaluate(merged_text, self.cfg)
                if item2["name"] not in ("?", ""):
                    item2["_merged"] = True
                    item2["_note"] = "; ".join(x for x in (item2.get("_note"), t("note.merged")) if x)
                    log.info("Scrolled card merged: %r (%d attrs)", item2["name"], len(item2.get("attrs", {})))
                    text, item, verdict, res = merged_text, item2, verdict2, res2
        if kind_ok and item["name"] not in ("?", "") and not item.get("partial"):
            self.card_session = {"t": now, "item": item, "text": text}
        return text, item, verdict, res

    def scan_area(self):
        """Taranacak alan: oyun penceresinin kendisi (hangi monitörde / modda olursa olsun), seçilmiş bölge,
        ya da oyun bulunamazsa ana monitör. Oyunun boyutu değişince okuma ayarları yeniden uygulanır."""
        st = self.cfg["settings"]
        if st.get("scan_source", "screen") == "region" and st.get("region"):
            return st["region"]
        g = display.game_window()
        with mss.mss() as sct:
            mons = sct.monitors
            area = display.clamp_to_screen(g, mons) if g else None
            if not area:
                m = mons[1]
                area = {"left": m["left"], "top": m["top"], "width": m["width"], "height": m["height"]}
        sig = (area["left"], area["top"], area["width"], area["height"], bool(g))
        if sig != getattr(self, "_area_sig", None):
            self._area_sig = sig
            src = "game window" if g else "primary monitor (game not found)"
            log.info("Capture area: %s %dx%d at (%d,%d)", src, area["width"], area["height"], area["left"], area["top"])
            size = (area["width"], area["height"]) if g else None
            if g and size != getattr(self, "_area_size", None):    # yalnız boyut değişince (taşımak yetmez)
                first = getattr(self, "_area_size", None) is None
                self._area_size = size
                k0 = getattr(self, "_prof_key", None)
                k1 = active_profile(st)[0]
                self._prof_key = k1
                if k0 != k1 or not first:
                    apply_ocr_settings(st)
                log.info("Display profile: %s, OCR threshold %s, scale %s", k1, gamedata.THRESHOLD, gamedata.SCALE or "auto")
        return area

    def screen_monitor(self):
        """Tam ekran seçimleri (kalibrasyon, görev bölgesi) için oyunun bulunduğu monitör."""
        with mss.mss() as sct:
            g = display.game_window()
            return dict(display.monitor_of(g, sct.monitors) if g else sct.monitors[1])

    def auto_loop(self, stop):
        prev = last_done = None; stable = 0
        while not stop.is_set():
            try:
                region = self.scan_area()
                if region and self.cfg["settings"].get("only_game_active", True) and not game_active():
                    prev = None; stable = 0                     # oyun önde değil: okuma yapma
                elif region:
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
                    cat, kind = r[1] if isinstance(r[1], tuple) else split_cat(r[1])
                    for it in r[2]:
                        if kind and not it.get("kind"): it["kind"] = kind
                    self.tasks["items"].setdefault(cat, []).extend(r[2]); save_tasks(self.tasks)
                    self.task_in.delete("1.0", "end"); self.tr_status.config(text=t("task.added_src", n=len(r[2]), src=r[2][0]["src"]))
                    self.refresh_tasks()
                    continue
                if r[0] == "cl_status":
                    self.cl_status.config(text=r[1]); continue
                if r[0] == "claude_tasks":
                    self.apply_claude_tasks(r[1], r[2]); continue
                if r[0] == "cl_raw":
                    self.cl_raw.config(state="normal"); self.cl_raw.delete("1.0", "end"); self.cl_raw.insert("end", r[1]); self.cl_raw.config(state="disabled")
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
        self.last_text = text
        self.show_result(text, item, verdict, res, note, diff=diff)
        self.popup(verdict, item, res, note)
        if s.get("speak_verdict"): self.speak_verdict(verdict, item, res, note)
        elif s.get("sound"): self.sounds.play(verdict, force=True)
        if s.get("log_csv"): self.log(item, verdict, res)
        self._companion_update(item, verdict, res, note)
        if s.get("vendor_mode") and valid_item(item) and item.get("kind") in ("gear", "weapon"):
            it = dict(item, vendor=t("vend.ingame"), id="s:" + str(len(self.vendor_scans)))
            self.vendor_scans.append(it)
            if self.current_tab() == "stash": self.refresh_stash()
        elif s.get("stash_record", True) and valid_item(item):
            try:
                rec, new = self.stash.add(item, verdict, res[0][1] if res else None, res[0][0] if res else None, GAME)
                if new: self._drop_report(item)
                if rec:
                    self.stash.save()
                    if self.current_tab() == "stash": self.refresh_stash()
            except Exception:
                log.exception("Stash add failed")
        log.info("Scan: %r -> %s (%s %s%%) slot=%s", item["name"][:50], verdict,
                 res[0][1] if res else "-", res[0][0] if res else 0, item.get("slot") or "-")

    def _set_activity(self):
        key = next((k for k, v in self._acts.items() if v == self.drop_act.get()), "none")
        st = self.cfg["settings"]; st["drop_activity"] = key; save_cfg(self.cfg)
        if key != "none" and not st.get("drop_share"):
            self.toast(t("drops.share_off"))

    # ---------- Yapay zekâ / hata bildirimi ----------
    def _last_item(self):
        return (self.last_scan or (None,))[0] if getattr(self, "last_scan", None) else None

    def ask_about_item(self):
        it = self._last_item()
        if not it: return messagebox.showinfo(APP_NAME, t("ai.no_item"))
        b = active_build(self.cfg)
        req = plan_of(b).get(it.get("slot")) if b and it.get("slot") else None
        attrs = ", ".join(f"{attr_name(k)} {v:g}" + (f" ({(it.get('quality') or {}).get(k)}%)" if (it.get("quality") or {}).get(k) is not None else "")
                          for k, v in (it.get("attrs") or {}).items())
        q = t("ai.item_prompt", name=it.get("name"), slot=slot_name(it.get("slot") or "") if it.get("slot") else "?",
              src=it.get("gear_set") or it.get("brand") or "-", attrs=attrs or "-", talents=", ".join(it.get("talents") or []) or "-",
              build=(b or {}).get("name", "-"), req=req_lines_short(req) or "-")
        self.nb.select(self.tab_keys.index("assistant"))
        self.ask(q)

    def vision_read(self):
        """Okunamayan kartı Claude Code'a resim olarak okut (isteğe bağlı; kart görüntüsü Anthropic'e gider)."""
        img = getattr(self, "last_card_img", None)
        if img is None: return messagebox.showinfo(APP_NAME, t("ocr.need_card"))
        st = self.cfg["settings"]
        if not find_claude_cli(): return messagebox.showwarning(APP_NAME, t("ai.cc_missing"))
        if not st.get("vision_ok"):
            if not messagebox.askyesno(APP_NAME, t("ai.vision_consent")): return
            st["vision_ok"] = True; save_cfg(self.cfg)
        work = BASE / "logs" / "claude_code"; work.mkdir(parents=True, exist_ok=True)
        path = work / "card.png"; img.save(path)
        self.toast(t("ai.vision_busy"))

        def go():
            try:
                txt = ask_claude_code(st.get("claude_code_model", ""), VISION_SYSTEM,
                                      [{"role": "user", "content": t("ai.vision_prompt", path=str(path))}],
                                      tools="Read", max_turns=3)
                txt = re.sub(r"^```[a-z]*\n?|```$", "", (txt or "").strip(), flags=re.M).strip()
                item, verdict, res = evaluate(txt, self.cfg)
                self.results.put(("ok", txt, item, verdict, res, signature(item)))
            except Exception as e:
                log.exception("vision read failed")
                self.results.put(("err", f"{type(e).__name__}: {e}"))
        threading.Thread(target=go, daemon=True).start()

    def report_wrong(self):
        """Yanlış okunan kartı kaydet (test setine eklensin diye) ve GitHub'da hata bildirimi aç."""
        img = getattr(self, "last_card_img", None)
        if img is None: return messagebox.showinfo(APP_NAME, t("ocr.need_card"))
        it = self._last_item() or {}
        d = REPORTS_DIR / datetime.now().strftime("%Y%m%d_%H%M%S"); d.mkdir(parents=True, exist_ok=True)
        img.save(d / "card.png")
        info = {"read_as": {k: it.get(k) for k in ("name", "kind", "slot", "brand", "gear_set", "rarity", "attrs", "talents")},
                "ocr_text": self.last_text, "engine": OCR.name, "app": APP_VERSION,
                "resolution": active_profile(self.cfg["settings"])[0]}
        (d / "report.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        import webbrowser
        title = f"OCR: {it.get('name') or '?'} read wrong"
        body = (f"Engine: {OCR.name} · App {APP_VERSION} · {info['resolution']}\n\nRead as: `{json.dumps(info['read_as'], ensure_ascii=False)}`\n\n"
                "Correct values: (please write them here)\n\nPlease attach card.png from: " + str(d))
        webbrowser.open(ISSUES_URL + "?" + urllib.parse.urlencode({"title": title, "body": body, "labels": "ocr"}))
        try: os.startfile(str(d))                  # Windows: klasörü aç, kart sürüklenip eklensin
        except Exception: pass
        self.toast(t("report.saved"))

    def _drop_report(self, item):
        """Sandığa ilk kez giren eşya, oyuncu bir aktivite seçtiyse o aktivitenin düşüşü sayılır (gönüllü)."""
        st = self.cfg["settings"]
        if not st.get("drop_share") or st.get("drop_activity", "none") == "none": return
        if self.dropq.add(dropstats.record(item, st["drop_activity"])) and hasattr(self, "drop_lbl"):
            self._drops_label()

    def _drops_tick(self):
        st = self.cfg["settings"]
        if st.get("drop_share") and len(self.dropq) and (st.get("drop_server") or dropstats.DEFAULT_URL):
            self.drops_flush(quiet=True)
        self.root.after(10 * 60 * 1000, self._drops_tick)

    def drops_flush(self, quiet=False):
        if self.drops_busy: return
        st = self.cfg["settings"]
        url = st.get("drop_server") or dropstats.DEFAULT_URL
        if not url:
            if not quiet: messagebox.showinfo(APP_NAME, t("drops.no_server"))
            return
        self.drops_busy = True

        def work():
            n, err = self.dropq.flush(url, st["drop_client"])
            self.root.after(0, lambda: self._drops_done(n, err, quiet))
        threading.Thread(target=work, daemon=True).start()

    def _drops_done(self, n, err, quiet):
        self.drops_busy = False
        log.info("Drop stats: sent %d (%s)", n, err or "ok")
        if not quiet:
            if err: messagebox.showwarning(APP_NAME, t("drops.send_failed", e=err))
            else: self.toast(t("drops.sent", n=n))
        self._drops_label()

    def _drops_label(self):
        if hasattr(self, "drop_lbl"):
            self.drop_lbl.config(text=t("drops.pending", n=len(self.dropq), sent=self.dropq.sent_total))

    def ask_drop_consent(self):
        st = self.cfg["settings"]
        if st.get("drop_asked"): return
        st["drop_share"] = bool(messagebox.askyesno(t("drops.ask_title"), t("drops.ask")))
        st["drop_asked"] = True; save_cfg(self.cfg)
        if hasattr(self, "drop_var"): self.drop_var.set(st["drop_share"])

    def record(self, bname, slot, score, item, sig):
        self.progress.setdefault(bname, {})[slot] = {"item": item["name"], "score": score, "sig": sig, "attrs": item.get("attrs", {}),
                                                     "quality": item.get("quality", {}), "brand": item.get("brand"),
                                                     "gear_set": item.get("gear_set"), "talents": item.get("talents", []),
                                                     "rarity": item.get("rarity", []),
                                                     "time": datetime.now().isoformat(timespec="seconds")}
        save_progress(self.progress)
        self.check_build_complete(bname)
        if self.current_tab() == "progress": self.refresh_prog()
        if self.current_tab() == "builds" and getattr(self, "cur", None) and self.cur.get("name") == bname: self.draw_sheet()

    def build_status(self, b):
        """{slot: ("done"|"partial"|"missing"|"off", kayıt, şartlar)} — Build'ler, Eksik Parça ve Panel ortak kullanır."""
        plan = plan_of(b)
        prog = self.progress.get(b["name"], {})
        out = {}
        for slot in engine.ALL_SLOTS:
            req = plan.get(slot, {"kind": "off"})
            if req.get("kind") == "off":
                out[slot] = ("off", None, []); continue
            rec = prog.get(slot)
            if not rec:
                out[slot] = ("missing", None, []); continue
            checks = engine.check_slot(dict(rec, name=rec.get("item")), req, GAME)
            out[slot] = ("done" if engine.slot_done(checks) else "partial", rec, checks)
        return out

    def check_build_complete(self, bname):
        b = build_by_name(self.cfg, bname)
        if not b: return
        stt = self.build_status(b)
        act = [v for v in stt.values() if v[0] != "off"]
        if act and all(v[0] in ("done", "partial") for v in act):
            full = all(v[0] == "done" for v in act)
            self.toast(t("build.complete_full" if full else "build.complete", build=bname))
            log.info("Build complete: %s (all requirements: %s)", bname, full)
            try: self.sounds.play("KEEP", force=True)
            except Exception: pass

    def set_active_build(self, name, refresh=True):
        if not build_by_name(self.cfg, name): return
        self.cfg["settings"]["active_build"] = name; save_cfg(self.cfg)
        log.info("Active build: %s", name)
        if not refresh: return
        if hasattr(self, "act_cb"): self.act_cb.set(name)
        if hasattr(self, "pb") and self.pb.get() != name:
            self.pb.set(name); self.refresh_prog()
        if hasattr(self, "sheet_box"): self.draw_sheet()

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
        """Oyun üstü bilgi kartı: kartın hemen yanında (ya da seçilen köşede), rulo çubukları ve en iyi build ile."""
        if self.overlay: self.overlay.destroy()
        st = self.cfg["settings"]
        w = self.overlay = tk.Toplevel(self.root)
        try: alpha = max(0.4, min(1.0, float(st.get("overlay_alpha", 0.94))))
        except (TypeError, ValueError): alpha = 0.94
        w.overrideredirect(True); w.attributes("-topmost", True, "-alpha", alpha)
        _, prof = active_profile(st)
        try: k = prof.get("ui", 1.0) * float(st.get("overlay_size", 1.0))
        except (TypeError, ValueError): k = prof.get("ui", 1.0)
        fz = lambda n: max(7, int(round(n * k)))
        col = COLORS[verdict]
        dark, dark2, fg, mu = "#14161b", "#1e2129", "#eceef2", "#9aa1ae"   # oyun üstünde hep koyu kart
        w.configure(bg="#000000")
        shell = tk.Frame(w, bg=dark, highlightthickness=1, highlightbackground="#2c313d"); shell.pack(fill="both", expand=True)
        tk.Frame(shell, bg=col, width=max(5, int(7 * k))).pack(side="left", fill="y")      # renkli şerit
        body = tk.Frame(shell, bg=dark, padx=int(16 * k), pady=int(12 * k)); body.pack(side="left", fill="both")
        tk.Label(body, text=verdict_label(verdict), fg=ui_theme.PALETTES["dark"]["verdict_fg"].get(verdict, fg),
                 bg=dark, font=(ui_theme.FONT_SEMI, fz(18))).pack(anchor="w")
        sub = item["name"][:42] + ("  ·  " + ", ".join(item["rarity"]) if item.get("rarity") else "")
        tk.Label(body, text=sub, fg=fg, bg=dark, font=(ui_theme.FONT_SEMI, fz(11))).pack(anchor="w")
        tag = " / ".join(x for x in (item.get("gear_set"), item.get("brand")) if x)
        if tag: tk.Label(body, text="🏷 " + tag, fg=mu, bg=dark, font=(ui_theme.FONT, fz(10))).pack(anchor="w")
        # rulo kalitesi çubukları (oyundaki en yüksek değere göre)
        q = item.get("quality", {})
        if q:
            bars = tk.Canvas(body, bg=dark, highlightthickness=0, width=int(340 * k), height=int(20 * k) * min(4, len(q)) + 4)
            bars.pack(anchor="w", pady=(int(8 * k), 0))
            for r, (a, v) in enumerate(list(q.items())[:4]):
                y = r * int(20 * k) + 2; bw = int(120 * k); x0 = int(170 * k)
                bars.create_text(0, y + int(8 * k), text=f"{attr_name(a)[:20]}", fill=mu, anchor="w", font=(ui_theme.FONT, fz(9)))
                bars.create_rectangle(x0, y + 3, x0 + bw, y + int(14 * k), fill=dark2, outline="")
                c = "#22c55e" if v >= 85 else "#eab308" if v >= 60 else "#ef4444"
                bars.create_rectangle(x0, y + 3, x0 + bw * min(100, v) / 100, y + int(14 * k), fill=c, outline="")
                bars.create_text(x0 + bw + 6, y + int(8 * k), text=f"{v}%", fill=fg, anchor="w", font=(ui_theme.FONT, fz(9)))
        L = []
        if item.get("_note"): L.append("» " + item["_note"])
        if note: L.append("» " + note)
        if verdict == "REVIEW": L.append(t("panel.rare_warning"))
        for p, n, _ in res[:3]:
            if p > 0: L.append(f"▸ {n}: {p}%")
        if res and res[0][2]: L.append("  " + ", ".join(res[0][2][:4]))
        if verdict == "DISMANTLE": L.append(t("panel.no_build_match"))
        if L:
            tk.Label(body, text="\n".join(L), justify="left", fg=mu, bg=dark, font=(ui_theme.FONT, fz(10)),
                     wraplength=int(420 * k)).pack(anchor="w", pady=(6, 0))
        w.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        ww, wh = w.winfo_width(), w.winfo_height()
        x = y = None
        card = getattr(self, "last_card_screen", None)
        if st.get("overlay_mode", "card") == "card" and card:
            gap = int(14 * k)
            if card[2] + gap + ww <= sw: x = card[2] + gap                       # kartın sağı
            elif card[0] - gap - ww >= 0: x = card[0] - gap - ww                 # yer yoksa solu
            if x is not None:
                y = max(10, min(sh - wh - 10, card[1] + int(40 * k)))
        if x is None:
            pos = lambda c: (sw - ww - 30 if "right" in c else 30, 60 if "top" in c else sh - wh - 80)
            want = st["overlay_corner"]
            corners = [want] + [c for c in ("top_left", "bottom_left", "bottom_right", "top_right") if c != want]
            reg = card or self.region_rect()
            c = next((c for c in corners if not self.rects_overlap((*pos(c), pos(c)[0] + ww, pos(c)[1] + wh), reg)), want)
            x, y = pos(c)                                     # kart, okunan bölgenin üstüne düşmesin
        w.geometry(f"+{int(x)}+{int(y)}")
        click_through(w)
        if not exclude_from_capture(w):
            log.debug("Overlay capture exclusion unavailable: masking %s", CAPTURE_MASK.get("overlay"))
        w.bind("<Destroy>", lambda e, w=w: CAPTURE_MASK.pop("overlay", None) if e.widget is w else None)
        if self.overlay_job: self.root.after_cancel(self.overlay_job)
        self.overlay_job = self.root.after(int(float(st["overlay_seconds"]) * 1000), w.destroy)

    # ---------- kalibrasyon / test ----------
    def calibrate(self):
        if not messagebox.askokcancel(APP_NAME, t("calib.ask_item")):
            return
        self.root.withdraw(); self.root.after(5000, self._calib_capture)

    def _calib_capture(self):
        mon = self.screen_monitor()
        with mss.mss() as sct:
            s = sct.grab(mon); img = Image.frombytes("RGB", s.size, s.rgb)
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
            img = Image.open(p).convert("RGB")
            box = find_card(img)                                  # taramayla aynı yol: kartı bul, kırp, oku
            card = img.crop(box) if box else img
            text, lines = read_card(card)
            item, verdict, res = evaluate(text, self.cfg)
            verdict = color_hints(card, lines, item, verdict)
            self.last_card_img = card
            self.show_result(text, item, verdict, res, debug=True)
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    # ---------- Build editörü (v2) ----------
    def build_builds(self):
        """Build'ler v2: oyun verisinden seçmeli set/marka, attribute (oyun max'ı ile), talent ve silah türü."""
        f = self.tabs["builds"]
        paned = ttk.Panedwindow(f, orient="horizontal"); paned.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(paned); paned.add(left, weight=1)
        self.b_search = tk.StringVar()
        se = ttk.Entry(left, textvariable=self.b_search); se.pack(fill="x", pady=(0, 4))
        se.bind("<KeyRelease>", lambda e: self.refresh_builds(keep=True))
        self.lb = tk.Listbox(left, exportselection=False, font=(ui_theme.FONT, 11))
        self.lb.pack(fill="both", expand=True); self.lb.bind("<<ListboxSelect>>", self.on_pick)
        bb = ttk.Frame(left); bb.pack(fill="x", pady=4)
        ttk.Button(bb, text=ui_theme.with_icon(t("build.new"), "➕"), command=self.new_build).pack(side="left", fill="x", expand=True)
        ttk.Button(bb, text=ui_theme.with_icon(t("build.duplicate"), "⧉"), command=self.dup_build).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(bb, text=ui_theme.with_icon(t("build.delete"), "🗑"), command=self.del_build).pack(side="left", fill="x", expand=True)
        bb2 = ttk.Frame(left); bb2.pack(fill="x")
        ttk.Button(bb2, text=t("build.export"), command=self.export_builds).pack(side="left", fill="x", expand=True)
        ttk.Button(bb2, text=t("build.import"), command=self.import_builds).pack(side="left", fill="x", expand=True, padx=(4, 0))
        bb3 = ttk.Frame(left); bb3.pack(fill="x", pady=(4, 0))
        ttk.Button(bb3, text="🔗 " + t("share.share"), command=self.share_build).pack(side="left", fill="x", expand=True)
        ttk.Button(bb3, text="📥 " + t("share.paste"), command=self.import_build_code).pack(side="left", fill="x", expand=True, padx=(4, 0))
        ttk.Button(left, text=ui_theme.with_icon(t("meta.sync_now"), "⭐"), command=lambda: self.meta_sync_start(force=True, what=("builds",)),
                   style="Accent.TButton").pack(fill="x", pady=(6, 0))
        self.meta_info = ttk.Label(left, text=self.meta_status_text(), foreground=PAL["muted"], wraplength=300, justify="left")
        self.meta_info.pack(fill="x", pady=(4, 0))

        right = ttk.Frame(paned); paned.add(right, weight=3)
        self.b_nb = ttk.Notebook(right); self.b_nb.pack(fill="both", expand=True)
        sh = ttk.Frame(self.b_nb); self.b_nb.add(sh, text=" 📋 " + t("plan.tab_sheet") + " ")
        holder = ttk.Frame(self.b_nb); self.b_nb.add(holder, text=" ✏ " + t("plan.tab_edit") + " ")
        self.sheet_box = ui_theme.scrollable(sh, PAL["bg"])
        r = ui_theme.scrollable(holder, PAL["bg"])
        names = (GAME.data.get("gear_sets", []) + GAME.data.get("brands", [])) if GAME.ok else []

        g = ttk.LabelFrame(r, text=t("build.sec_general")); g.pack(fill="x", padx=6, pady=(0, 8))
        self.v_name, self.v_bonus = tk.StringVar(), tk.StringVar()
        ttk.Label(g, text=t("build.name")).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(g, textvariable=self.v_name, width=48).grid(row=0, column=1, columnspan=3, sticky="w", pady=4)
        ttk.Label(g, text=t("build.sets")).grid(row=1, column=0, sticky="nw", padx=8, pady=4)
        self.sets_lb = tk.Listbox(g, height=4, width=34, exportselection=False); self.sets_lb.grid(row=1, column=1, rowspan=2, sticky="w", pady=4)
        self.v_setpick = tk.StringVar()
        ttk.Combobox(g, textvariable=self.v_setpick, values=names, width=30).grid(row=1, column=2, sticky="w", padx=6)
        sb = ttk.Frame(g); sb.grid(row=2, column=2, sticky="w", padx=6)
        ttk.Button(sb, text="✚", width=3, command=self.add_set).pack(side="left")
        ttk.Button(sb, text="🗑", width=3, command=self.del_set).pack(side="left", padx=4)
        ttk.Label(g, text=t("build.set_bonus")).grid(row=3, column=0, sticky="w", padx=8, pady=4)
        ttk.Spinbox(g, textvariable=self.v_bonus, from_=0, to=50, width=6).grid(row=3, column=1, sticky="w")
        ttk.Label(g, text=t("plan.items")).grid(row=5, column=0, sticky="nw", padx=8, pady=4)
        self.items_lb = tk.Listbox(g, height=3, width=34, exportselection=False); self.items_lb.grid(row=5, column=1, sticky="w", pady=4)
        self.v_itempick = tk.StringVar()
        ip = ttk.Frame(g); ip.grid(row=5, column=2, sticky="w", padx=6)
        ttk.Combobox(ip, textvariable=self.v_itempick, width=30,
                     values=sorted(set(GAME.data.get("exotics", []) + GAME.data.get("named", []))) if GAME.ok else []).pack(side="left")
        ttk.Button(ip, text="✚", width=3, command=lambda: self.v_itempick.get().strip() and self.v_itempick.get().strip() not in self.items_lb.get(0, "end")
                   and self.items_lb.insert("end", self.v_itempick.get().strip())).pack(side="left", padx=4)
        ttk.Button(ip, text="🗑", width=3, command=lambda: [self.items_lb.delete(x) for x in reversed(self.items_lb.curselection())]).pack(side="left")
        ttk.Label(g, text=t("build.slots")).grid(row=4, column=0, sticky="nw", padx=8, pady=4)
        slf = ttk.Frame(g); slf.grid(row=4, column=1, columnspan=3, sticky="w")
        self.v_slots = {}
        for i, s in enumerate(engine.ALL_SLOTS):
            self.v_slots[s] = tk.BooleanVar(value=True)
            ttk.Checkbutton(slf, text=slot_name(s), variable=self.v_slots[s]).grid(row=i // 4, column=i % 4, sticky="w", padx=(0, 14))

        a = ttk.LabelFrame(r, text=t("build.attr_rules")); a.pack(fill="x", padx=6, pady=8)
        self.ta = ttk.Treeview(a, columns=("k", "w", "g", "m"), show="headings", height=7)
        for c, hd, w in (("k", t("build.attr"), 240), ("w", t("build.weight"), 90), ("g", t("build.goodval"), 110), ("m", t("panel.col_max"), 110)):
            self.ta.heading(c, text=hd); self.ta.column(c, width=w, anchor="w" if c == "k" else "center")
        self.ta.pack(fill="x", padx=8, pady=(6, 2)); self.ta.bind("<<TreeviewSelect>>", self.pick_attr)
        af = ttk.Frame(a); af.pack(fill="x", padx=8, pady=(2, 8))
        self.attr_keys = list(GAME.data.get("attributes", {}).keys()) if GAME.ok else list(self.cfg["attributes"])
        self.v_ak, self.v_aw, self.v_ag = tk.StringVar(), tk.StringVar(value="2"), tk.StringVar()
        ak = ttk.Combobox(af, textvariable=self.v_ak, width=32, state="readonly", values=[attr_name(k) for k in self.attr_keys])
        ak.pack(side="left"); ak.bind("<<ComboboxSelected>>", self.attr_default_good)
        ttk.Label(af, text=t("build.weight")).pack(side="left", padx=(10, 2))
        ttk.Spinbox(af, textvariable=self.v_aw, from_=0, to=5, increment=0.5, width=5).pack(side="left")
        ttk.Label(af, text=t("build.goodval")).pack(side="left", padx=(10, 2))
        ttk.Entry(af, textvariable=self.v_ag, width=9).pack(side="left")
        ttk.Button(af, text=ui_theme.with_icon(t("btn.add_update"), "✚"), command=self.set_attr).pack(side="left", padx=6)
        ttk.Button(af, text=ui_theme.with_icon(t("btn.delete"), "🗑"), command=self.del_attr).pack(side="left")

        tl = ttk.LabelFrame(r, text=t("build.talents")); tl.pack(fill="x", padx=6, pady=8)
        self.tt = ttk.Treeview(tl, columns=("n", "k", "w"), show="headings", height=6)
        for c, hd, w in (("n", t("build.talent"), 260), ("k", t("build.talent_kind"), 120), ("w", t("build.weight"), 90)):
            self.tt.heading(c, text=hd); self.tt.column(c, width=w, anchor="w" if c == "n" else "center")
        self.tt.pack(fill="x", padx=8, pady=(6, 2)); self.tt.bind("<<TreeviewSelect>>", self.pick_tal)
        tf = ttk.Frame(tl); tf.pack(fill="x", padx=8, pady=(2, 8))
        tal_names = []
        if GAME.ok:
            for n in GAME.data.get("gear_talents", []) + GAME.data.get("weapon_talents", []):
                tal_names += [n, "Perfect " + n]
        self.v_tn, self.v_tw = tk.StringVar(), tk.StringVar(value="2")
        ttk.Combobox(tf, textvariable=self.v_tn, width=32, values=sorted(set(tal_names))).pack(side="left")
        ttk.Label(tf, text=t("build.weight")).pack(side="left", padx=(10, 2))
        ttk.Spinbox(tf, textvariable=self.v_tw, from_=0, to=10, increment=0.5, width=5).pack(side="left")
        ttk.Button(tf, text=ui_theme.with_icon(t("btn.add_update"), "✚"), command=self.set_tal).pack(side="left", padx=6)
        ttk.Button(tf, text=ui_theme.with_icon(t("btn.delete"), "🗑"), command=self.del_tal).pack(side="left")

        wp = ttk.LabelFrame(r, text=t("build.weapons")); wp.pack(fill="x", padx=6, pady=8)
        wf = ttk.Frame(wp); wf.pack(fill="x", padx=8, pady=6)
        self.v_wtypes = {}
        for i, (key, label) in enumerate(engine.TYPE_LABEL.items()):
            self.v_wtypes[key] = tk.BooleanVar(value=False)
            ttk.Checkbutton(wf, text=label, variable=self.v_wtypes[key]).grid(row=i // 4, column=i % 4, sticky="w", padx=(0, 16))
        self.wtype_hint = ttk.Label(wp, text="", foreground=PAL["muted"]); self.wtype_hint.pack(anchor="w", padx=8, pady=(0, 6))

        act = ttk.Frame(r); act.pack(fill="x", padx=6, pady=(4, 6))
        ttk.Button(act, text=t("btn.save"), command=self.save_build, style="Accent.TButton").pack(side="left")
        ttk.Button(act, text=ui_theme.with_icon(t("build.test_last"), "🧪"), command=self.test_build_last).pack(side="left", padx=8)
        self.test_lbl = ttk.Label(r, text="", wraplength=900, justify="left"); self.test_lbl.pack(anchor="w", padx=8)
        self.meta_detail = ttk.Label(r, text="", foreground=PAL["muted"], wraplength=900, justify="left")
        self.meta_detail.pack(anchor="w", padx=8, pady=(6, 0))
        self._lb_index = []
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

    def refresh_builds(self, select=0, keep=False):
        if keep and self.cur in self.cfg["builds"]:
            select = self.cfg["builds"].index(self.cur)
        q = gamedata.nrm(self.b_search.get()) if hasattr(self, "b_search") else ""
        self.lb.delete(0, "end"); self._lb_index = []
        for i, b in enumerate(self.cfg["builds"]):
            if q and q not in gamedata.nrm(b["name"] + " " + " ".join(b.get("sets_or_brands", []))): continue
            self.lb.insert("end", self.build_label(b)); self._lb_index.append(i)
        if self._lb_index:
            pos = self._lb_index.index(select) if select in self._lb_index else 0
            self.lb.selection_set(pos); self.lb.see(pos); self.on_pick()
        if hasattr(self, "pb"): self.pb["values"] = [b["name"] for b in self.cfg["builds"]]

    @staticmethod
    def build_label(b):
        """Listede görünen ad: ⭐ meta, 🔒 düzenlenmiş meta, 🔥 popülerlik."""
        if not b.get("meta_id"): return b["name"]
        pop = b.get("meta", {}).get("popularity", 0)
        return f"{'🔒' if b.get('meta_locked') else '⭐'} {b['name']}" + (f"  🔥{pop}" if pop else "")

    def selected_build_index(self):
        s = self.lb.curselection()
        return self._lb_index[s[0]] if s and s[0] < len(self._lb_index) else None

    def on_pick(self, event=None):
        i = self.selected_build_index()
        if i is None: return
        self.cur = self.cfg["builds"][i]
        if event is not None: self.flash_build(self.cur)   # kullanıcı tıkladıysa amblem 5 sn
        self.v_name.set(self.cur["name"]); self.v_bonus.set(str(self.cur.get("set_bonus", 0)))
        self.sets_lb.delete(0, "end")
        for s in self.cur.get("sets_or_brands", []): self.sets_lb.insert("end", s)
        self.items_lb.delete(0, "end")
        for s in self.cur.get("items", []): self.items_lb.insert("end", s)
        slots = self.cur.get("slots") or engine.ALL_SLOTS
        for s, v in self.v_slots.items(): v.set(s in slots)
        types = (self.cur.get("weapons") or {}).get("types", [])
        for k, v in self.v_wtypes.items(): v.set(k in types)
        guess = engine.weapon_types_of(self.cur) if not types else []
        self.wtype_hint.config(text=t("build.wtype_guess", types=", ".join(engine.TYPE_LABEL[x] for x in guess)) if guess else "")
        self.test_lbl.config(text="")
        self.refresh_trees()
        if hasattr(self, "meta_detail"): self.meta_detail.config(text=self.meta_detail_text(self.cur))
        self.draw_sheet()

    def draw_sheet(self):
        """Build ayrıntısı: özet, kaynaklar, set/marka bonusu, 8 yuva (ne aranmalı + elindeki parça + ✔/✖), silahlar."""
        box = getattr(self, "sheet_box", None)
        b = getattr(self, "cur", None)
        if box is None or not b: return
        for w in box.winfo_children(): w.destroy()
        is_act = active_build(self.cfg) is b
        head = ttk.Frame(box); head.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(head, text=b["name"], font=(ui_theme.FONT_SEMI, 16)).pack(side="left")
        if is_act:
            tk.Label(head, text="⭐ " + t("plan.is_active"), bg=PAL["accent"], fg="white", font=(ui_theme.FONT_SEMI, 9), padx=8, pady=2).pack(side="left", padx=10)
        else:
            ttk.Button(head, text="⭐ " + t("plan.make_active"), style="Accent.TButton",
                       command=lambda: (self.set_active_build(b["name"]), self.refresh_builds(keep=True))).pack(side="left", padx=10)
        ttk.Button(head, text="🧍 " + t("plan.open_progress"), command=lambda: (self.pb.set(b["name"]), self.refresh_prog(),
                                                                              self.nb.select(self.tab_keys.index("progress")))).pack(side="right")
        stt = self.build_status(b)
        have = sum(1 for v in stt.values() if v[0] in ("done", "partial")); full = sum(1 for v in stt.values() if v[0] == "done")
        tot = sum(1 for v in stt.values() if v[0] != "off")
        pb = ttk.Progressbar(box, maximum=max(tot, 1), value=have); pb.pack(fill="x", padx=10, pady=(2, 0))
        ttk.Label(box, text=t("plan.progress", have=have, full=full, total=tot), foreground=PAL["muted"]).pack(anchor="w", padx=10)
        m = b.get("meta", {})
        summ = m.get("summary", {}) if isinstance(m.get("summary"), dict) else {}
        line = summ.get(i18n.current_language()) or summ.get("en") or ""
        info = []
        if m.get("mode") or m.get("role"): info.append(" · ".join(x for x in (m.get("mode"), m.get("role"), f"🔥 {m.get('popularity')}" if m.get("popularity") else "") if x))
        if line: info.append(line)
        sets = b.get("sets_or_brands", [])
        if sets: info.append(t("plan.sets_line", s=", ".join(sets)))
        for br in sets:
            bon = GAME.data.get("brand_bonuses", {}).get(br) if GAME.ok else None
            if bon:
                start = 2 if GAME.ok and br in GAME.data.get("gear_sets", []) else 1
                info.append(f"   {br}: " + " · ".join(f"{i + start}pc {x}" for i, x in enumerate(bon)))
        if b.get("items"): info.append(t("plan.items_line", s=", ".join(b["items"])))
        if b.get("talents"): info.append(t("plan.talents_line", s=", ".join(f"{n} ({w:g})" for n, w in sorted(b["talents"].items(), key=lambda kv: -kv[1]))))
        if b.get("attributes"):
            info.append(t("plan.attrs_line", s=", ".join(f"{attr_name(k)} ≥{r.get('good_at') or '—'}" for k, r in
                                                           sorted(b["attributes"].items(), key=lambda kv: -float(kv[1].get("weight", 1))))))
        if info:
            ttk.Label(box, text="\n".join(info), wraplength=1100, justify="left").pack(anchor="w", padx=10, pady=(6, 4))
        for src in m.get("sources", [])[:4]:
            lk = ttk.Label(box, text="🔗 " + (src.get("title") or src.get("url")), foreground=PAL["accent"], cursor="hand2")
            lk.pack(anchor="w", padx=14); lk.bind("<Button-1>", lambda e, u=src.get("url"): __import__("webbrowser").open(u))
        grid = ttk.Frame(box); grid.pack(fill="x", padx=4, pady=8)
        for c in range(4): grid.columnconfigure(c, weight=1, uniform="sheet")
        plan = plan_of(b)
        colors = {"done": PAL["success"], "partial": PAL["warning"], "missing": PAL["danger"], "off": PAL["border"]}
        for i, slot in enumerate(engine.ALL_SLOTS):
            state, rec, checks = stt[slot]
            card = elevated(grid, row=i // 4, column=i % 4, depth=self.cfg["settings"].get("ui_depth", True))
            card.config(highlightbackground=colors[state])
            tk.Label(card, text=f"{SLOT_ICONS.get(slot, '•')}  {slot_name(slot)}   " + t("plan.st_" + state), bg=PAL["surface"],
                     fg=colors[state] if state != "off" else PAL["muted"], font=(ui_theme.FONT_SEMI, 11), anchor="w").pack(fill="x")
            tk.Label(card, text="\n".join(req_lines(plan.get(slot))), bg=PAL["surface"], fg=PAL["fg"], justify="left", anchor="w",
                     font=(ui_theme.FONT, 9), wraplength=300).pack(fill="x", pady=(4, 2))
            if rec:
                tk.Label(card, text="🎒 " + t("plan.have", item=rec.get("item"), score=rec.get("score")), bg=PAL["surface"], fg=PAL["accent"],
                         justify="left", anchor="w", font=(ui_theme.FONT_SEMI, 9), wraplength=300).pack(fill="x")
                tk.Label(card, text="\n".join(check_lines(checks)), bg=PAL["surface"], fg=PAL["muted"], justify="left", anchor="w",
                         font=(ui_theme.FONT, 9), wraplength=300).pack(fill="x")
            elif state == "missing":
                tk.Label(card, text=t("plan.missing_hint"), bg=PAL["surface"], fg=PAL["muted"], justify="left", anchor="w",
                         font=(ui_theme.FONT, 9), wraplength=300).pack(fill="x")
            card.bind("<Configure>", lambda e, c=card: [w.config(wraplength=max(120, e.width - 26))
                                                       for w in c.winfo_children() if isinstance(w, tk.Label)])

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
        for k, r in self.cur["attributes"].items():
            mx = GAME.max_of(k) if GAME.ok else None
            self.ta.insert("", "end", iid=k, values=(attr_name(k), r["weight"], r.get("good_at", ""), f"{mx:g}" if mx else "—"))
        wnames = {gamedata.nrm(n) for n in GAME.data.get("weapon_talents", [])} if GAME.ok else set()
        for n, w in self.cur["talents"].items():
            kind = t("build.kind_weapon") if gamedata.nrm(n).replace("perfect ", "") in wnames else t("build.kind_gear")
            self.tt.insert("", "end", iid=n, values=(n, kind, w))

    def add_set(self):
        v = self.v_setpick.get().strip()
        if v and v not in self.sets_lb.get(0, "end"): self.sets_lb.insert("end", v)

    def del_set(self):
        s = self.sets_lb.curselection()
        if s: self.sets_lb.delete(s[0])

    def attr_key_from_label(self, label):
        return next((k for k in self.attr_keys if attr_name(k) == label), label)

    def attr_default_good(self, _=None):
        k = self.attr_key_from_label(self.v_ak.get())
        mx = GAME.max_of(k) if GAME.ok else None
        if mx and not self.v_ag.get(): self.v_ag.set(f"{mx * 0.9:g}")
        elif mx: self.v_ag.set(f"{mx * 0.9:g}")

    def pick_attr(self, _=None):
        s = self.ta.selection()
        if s:
            r = self.cur["attributes"].get(s[0], {})
            self.v_ak.set(attr_name(s[0])); self.v_aw.set(r.get("weight", 1)); self.v_ag.set(r.get("good_at", ""))

    def pick_tal(self, _=None):
        s = self.tt.selection()
        if s: self.v_tn.set(s[0]); self.v_tw.set(self.cur["talents"].get(s[0], 2))

    def set_attr(self):
        k = self.attr_key_from_label(self.v_ak.get())
        if not k: return
        try:
            mx = GAME.max_of(k) if GAME.ok else None
            good = float(self.v_ag.get()) if self.v_ag.get().strip() else (mx * 0.9 if mx else 0)
            self.cur["attributes"][k] = {"weight": float(self.v_aw.get()), "good_at": round(good, 2)}
        except ValueError:
            return messagebox.showerror(APP_NAME, t("build.err_weight_val"))
        self.refresh_trees()

    def del_attr(self):
        self.cur["attributes"].pop(self.attr_key_from_label(self.v_ak.get()), None); self.refresh_trees()

    def set_tal(self):
        n = self.v_tn.get().strip()
        if not n: return
        try: self.cur["talents"][n] = float(self.v_tw.get())
        except ValueError: return messagebox.showerror(APP_NAME, t("build.err_weight"))
        self.refresh_trees()

    def del_tal(self):
        self.cur["talents"].pop(self.v_tn.get().strip(), None); self.refresh_trees()

    def new_build(self):
        self.cfg["builds"].append({"name": t("build.new_name"), "sets_or_brands": [], "set_bonus": 0, "attributes": {}, "talents": {}})
        self.refresh_builds(len(self.cfg["builds"]) - 1)

    def dup_build(self):
        i = self.selected_build_index()
        if i is None: return
        b = json.loads(json.dumps(self.cfg["builds"][i]))
        for k in ("meta_id", "meta_locked", "meta"): b.pop(k, None)
        b["name"] += " (2)"
        self.cfg["builds"].insert(i + 1, b); save_cfg(self.cfg); self.refresh_builds(i + 1)

    def del_build(self):
        i = self.selected_build_index()
        if i is not None and messagebox.askyesno(APP_NAME, t("build.delete_confirm")):
            mid = self.cfg["builds"][i].get("meta_id")
            if mid:   # silinen meta build bir sonraki senkronda geri gelmesin
                hid = self.cfg["settings"].setdefault("meta_hidden", [])
                if mid not in hid: hid.append(mid)
            del self.cfg["builds"][i]; save_cfg(self.cfg); self.refresh_builds()

    def save_build(self):
        i = self.selected_build_index()
        if i is None: return
        try: bonus = float(self.v_bonus.get() or 0)
        except ValueError: return messagebox.showerror(APP_NAME, t("build.err_bonus"))
        old = self.cur["name"]; new = self.v_name.get().strip() or t("word.unnamed")
        slots = [s for s, v in self.v_slots.items() if v.get()]
        self.cur.update(name=new, set_bonus=bonus, sets_or_brands=list(self.sets_lb.get(0, "end")))
        if slots and len(slots) < len(engine.ALL_SLOTS): self.cur["slots"] = slots
        else: self.cur.pop("slots", None)
        types = [k for k, v in self.v_wtypes.items() if v.get()]
        if types: self.cur.setdefault("weapons", {})["types"] = types
        elif "weapons" in self.cur: self.cur["weapons"].pop("types", None)
        self.cur["items"] = list(self.items_lb.get(0, "end"))
        if self.cur.get("meta_id"): self.cur["meta_locked"] = True   # artık senkron bu build'i değiştirmez
        if old != new and old in self.progress:
            self.progress[new] = self.progress.pop(old); save_progress(self.progress)
        save_cfg(self.cfg); self.refresh_builds(i); self.toast(t("msg.saved"))

    def test_build_last(self):
        if not self.last_scan: return self.test_lbl.config(text=t("prog.no_scan_yet"))
        item, res, sig = self.last_scan
        text = item.get("_text", "")
        if item.get("kind") == "weapon":
            pct, why = engine.score_weapon(item, self.cur, text, GAME)
        else:
            pct, why = engine.score_gear(item, self.cur, gamedata.nrm(text), GAME)
        self.test_lbl.config(text=t("build.test_result", item=item["name"], pct=pct) + "\n" + (", ".join(why) or "—"))

    # ---------- Eksik parça (v2) ----------
    def build_prog(self):
        """Eksik Parça v2: seçili build'in 8 yuvası kart olarak; her kartta parça, set/marka, puan ve rulolar."""
        f = self.tabs["progress"]
        bar = ttk.Frame(f); bar.pack(fill="x", padx=10, pady=10)
        ttk.Label(bar, text=t("label.build")).pack(side="left")
        self.pb = ttk.Combobox(bar, state="readonly", width=48, values=[b["name"] for b in self.cfg["builds"]])
        self.pb.pack(side="left", padx=6); self.pb.bind("<<ComboboxSelected>>", lambda e: (self.set_active_build(self.pb.get()), self.refresh_prog()))
        a0 = active_build(self.cfg)
        if a0: self.pb.set(a0["name"])
        ttk.Button(bar, text=ui_theme.with_icon(t("prog.reset_build"), "↺"), command=self.reset_build_prog).pack(side="right")
        self.pg_lbl = ttk.Label(f, style="Section.TLabel"); self.pg_lbl.pack(anchor="w", padx=12)
        self.pbar = ttk.Progressbar(f, maximum=100); self.pbar.pack(fill="x", padx=12, pady=6)
        mid = ttk.Frame(f); mid.pack(fill="x", padx=8, pady=4)
        av_box = tk.Frame(mid, bg=PAL["surface"], highlightthickness=1, highlightbackground=PAL["border"])
        av_box.pack(side="left", fill="y", padx=(4, 8), pady=6)
        tk.Label(av_box, text="🧍 " + t("v3d.agent"), bg=PAL["surface"], fg=PAL["fg"], font=(ui_theme.FONT_SEMI, 11)).pack(anchor="w", padx=10, pady=(8, 0))
        self.agent3d = view3d.AgentView(av_box, bg=PAL["surface"], width=360, height=420)
        self.agent3d.pack(padx=6, pady=4)
        self.agent3d.on_pick = self._pick_slot3d
        self.agent3d.set_labels({x: slot_name(x) for x in engine.ALL_SLOTS})
        tk.Label(av_box, text=t("v3d.agent_hint"), bg=PAL["surface"], fg=PAL["muted"], font=(ui_theme.FONT, 9),
                 wraplength=350, justify="left").pack(anchor="w", padx=10, pady=(0, 8))
        self.agent3d.spin()
        self.sel_slot = None
        self.slot_grid = ttk.Frame(mid); self.slot_grid.pack(side="left", fill="both", expand=True)
        cols = 4
        for c in range(cols): self.slot_grid.columnconfigure(c, weight=1, uniform="slot")
        self.slot_cards = {}
        for i, s in enumerate(engine.ALL_SLOTS):
            box = elevated(self.slot_grid, row=i // cols, column=i % cols, depth=self.cfg["settings"].get("ui_depth", True))
            head = tk.Label(box, text=SLOT_ICONS.get(s, "•") + "  " + slot_name(s), bg=PAL["surface"], fg=PAL["fg"],
                            font=(ui_theme.FONT_SEMI, 12), anchor="w")
            head.pack(fill="x")
            body = tk.Label(box, text="", bg=PAL["surface"], fg=PAL["muted"], justify="left", anchor="w",
                            font=(ui_theme.FONT, 10), wraplength=360)
            body.pack(fill="x", pady=(4, 6))
            box.bind("<Configure>", lambda e, b=body: b.config(wraplength=max(120, e.width - 30)))
            btns = tk.Frame(box, bg=PAL["surface"]); btns.pack(fill="x")
            ttk.Button(btns, text="📥 " + t("prog.put_last"), command=lambda s=s: self.save_last_scan(s)).pack(side="left")
            ttk.Button(btns, text="✖", width=3, command=lambda s=s: self.clear_slot(s)).pack(side="left", padx=6)
            self.slot_cards[s] = (box, head, body)
        ttk.Label(f, text=t("prog.all_builds"), style="Section.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        low = ttk.Frame(f); low.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.allp = ttk.Treeview(low, columns=("b", "n", "m"), show="headings", height=7)
        for c, hd, w in (("b", t("panel.col_build"), 300), ("n", t("prog.col_have"), 80), ("m", t("prog.col_missing"), 420)):
            self.allp.heading(c, text=hd); self.allp.column(c, width=w, anchor="center" if c == "n" else "w")
        self.allp.pack(side="left", fill="both", expand=True)
        bx = tk.Frame(low, bg=PAL["surface"], highlightthickness=1, highlightbackground=PAL["border"]); bx.pack(side="left", fill="both", padx=(10, 0))
        tk.Label(bx, text="📊 " + t("v3d.bars"), bg=PAL["surface"], fg=PAL["fg"], font=(ui_theme.FONT_SEMI, 11)).pack(anchor="w", padx=10, pady=(8, 0))
        self.bars3d = view3d.Bars3D(bx, bg=PAL["surface"], width=520, height=260)
        self.bars3d.pack(padx=6, pady=4)
        self.bars3d.on_pick = lambda tag: self.bars_info.config(text=tag)
        self.bars_info = tk.Label(bx, text=t("v3d.bars_hint"), bg=PAL["surface"], fg=PAL["muted"], font=(ui_theme.FONT, 9))
        self.bars_info.pack(anchor="w", padx=10, pady=(0, 8))
        self.allp.bind("<<TreeviewSelect>>", self._pick_allp)
        self.refresh_prog()

    def _pick_slot3d(self, slot):
        """3D ajanda tıklanan yuva: ilgili kart vurgulanır."""
        self.sel_slot = None if self.sel_slot == slot else slot
        for s2, (box, head, body) in self.slot_cards.items():
            box.config(highlightbackground=PAL["accent"] if s2 == self.sel_slot else box._base_border)
        self.agent3d.set_status(self.agent3d.status, self.sel_slot)

    def _pick_allp(self, _=None):
        s = self.allp.selection()
        if s and s[0] in self.pb["values"]:
            self.pb.set(s[0]); self.refresh_prog()

    def refresh_prog(self):
        name = self.pb.get()
        b = next((x for x in self.cfg["builds"] if x["name"] == name), None)
        slots = build_slots(self.cfg, name) if b else engine.ALL_SLOTS
        have = 0
        status3d = {}
        stt = self.build_status(b) if b else {x: ("missing", None, []) for x in engine.ALL_SLOTS}
        plan = plan_of(b) if b else {}
        colors = {"done": PAL["success"], "partial": PAL["warning"], "missing": PAL["danger"], "off": PAL["border"]}
        for s, (box, head, body) in self.slot_cards.items():
            state, d, checks = stt.get(s, ("missing", None, []))
            if s not in slots: state = "off"
            status3d[s] = {"done": "ok", "partial": "ok", "missing": "miss", "off": "off"}[state]
            box._base_border = colors[state]
            box.config(highlightbackground=colors[state]); head.config(fg=colors[state] if state != "off" else PAL["muted"])
            if state == "off":
                body.config(text=t("prog.not_in_build"), fg=PAL["muted"]); continue
            need = "\n".join(req_lines(plan.get(s)))
            if d:
                have += 1
                body.config(text=f"✔ {d['item']}  ·  {t('col.score')}: {d['score']}%  ·  {d.get('time', '')[:10]}\n"
                                 + "\n".join(check_lines(checks)) + "\n— " + t("plan.wanted") + " —\n" + need, fg=PAL["fg"])
            else:
                body.config(text=t("plan.missing_title") + "\n" + need, fg=PAL["muted"])
        self.agent3d.set_status(status3d, self.sel_slot)
        rows, vals = [], []
        for bb in self.cfg["builds"][:10]:
            sl, pr = build_slots(self.cfg, bb["name"]), self.progress.get(bb["name"], {})
            rows.append(bb["name"][:28])
            vals.append([(pr[x]["score"] if x in pr else 0) if x in sl else None for x in engine.ALL_SLOTS])
        self.bars3d.set_data(rows, [slot_name(x) for x in engine.ALL_SLOTS], vals)
        self.pg_lbl.config(text=t("prog.completed", have=have, total=len(slots)))
        self.pbar["value"] = 100 * have / max(len(slots), 1)
        self.allp.delete(*self.allp.get_children())
        for bb in self.cfg["builds"]:
            sl = build_slots(self.cfg, bb["name"]); miss = [s for s in sl if s not in self.progress.get(bb["name"], {})]
            self.allp.insert("", "end", iid=bb["name"], values=(bb["name"], f"{len(sl) - len(miss)}/{len(sl)}",
                                                                 ", ".join(slot_name(x) for x in miss) if miss else t("prog.done_all")))

    def save_last_scan(self, slot=None):
        if not self.last_scan: return messagebox.showinfo(APP_NAME, t("prog.no_scan_yet"))
        item, res, sig = self.last_scan
        name = self.pb.get()
        slot = slot or item.get("slot")
        if not slot: return messagebox.showinfo(APP_NAME, t("prog.no_slot"))
        if item.get("slot") and item["slot"] != slot and not messagebox.askyesno(APP_NAME, t("prog.slot_mismatch", a=slot_name(item["slot"]), b=slot_name(slot))):
            return
        sc = next((p for p, n, _ in res if n == name), 0)
        self.record(name, slot, sc, item, sig); self.refresh_prog()

    def clear_slot(self, slot=None):
        if slot and self.progress.get(self.pb.get(), {}).pop(slot, None) is not None:
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
        self._build_community(f)
        grid = ttk.Frame(f); grid.pack(fill="both", expand=True, padx=8, pady=6)
        self.cvs = []
        for i in range(4):
            cv = tk.Canvas(grid, height=230, bg=PAL["surface"], highlightthickness=1, highlightbackground=PAL["border"])
            cv.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4); self.cvs.append(cv)
        for c in (0, 1): grid.columnconfigure(c, weight=1)
        for r in (0, 1): grid.rowconfigure(r, weight=1)

    def _build_community(self, f):
        st = self.cfg["settings"]
        cb = ttk.LabelFrame(f, text="🌐 " + t("drops.box")); cb.pack(fill="x", padx=10, pady=(6, 2))
        r = ttk.Frame(cb); r.pack(fill="x", padx=8, pady=4)
        self.drop_var = tk.BooleanVar(value=bool(st.get("drop_share")))
        ttk.Checkbutton(r, text=t("drops.share"), variable=self.drop_var, command=self._drop_toggle).pack(side="left")
        ttk.Label(r, text=t("drops.server")).pack(side="left", padx=(16, 2))
        self.drop_srv = tk.StringVar(value=st.get("drop_server") or dropstats.DEFAULT_URL)
        ttk.Entry(r, textvariable=self.drop_srv, width=40).pack(side="left")
        ttk.Button(r, text="💾", width=3, command=self._drop_server_save).pack(side="left", padx=4)
        ttk.Button(r, text="⇪ " + t("drops.send_now"), command=self.drops_flush).pack(side="left", padx=4)
        ttk.Button(r, text="Σ " + t("drops.summary_btn"), command=self.drops_summary).pack(side="left")
        self.drop_lbl = ttk.Label(cb, text="", foreground=PAL["muted"]); self.drop_lbl.pack(anchor="w", padx=12)
        self._drops_label()
        hold = ttk.Frame(cb); hold.pack(fill="x", padx=8, pady=(2, 6))
        self.cs_out = None
        if self.premium_gate(hold, "drop_stats_view"):
            r2 = ttk.Frame(hold); r2.pack(fill="x")
            self.cs_act = ttk.Combobox(r2, state="readonly", width=22, values=[v for k, v in self._acts.items() if k != "none"])
            self.cs_act.pack(side="left")
            ttk.Label(r2, text=t("drops.search")).pack(side="left", padx=(12, 2))
            self.cs_q = tk.StringVar(); ttk.Entry(r2, textvariable=self.cs_q, width=28).pack(side="left")
            ttk.Button(r2, text="🔍 " + t("drops.show"), command=self.community_stats).pack(side="left", padx=6)
            self.cs_out = tk.Text(hold, height=7, bg=PAL["surface"], fg=PAL["fg"], relief="flat", wrap="word", font=(ui_theme.FONT, 10))
            self.cs_out.pack(fill="x", pady=(4, 0))
        ttk.Label(cb, text=t("drops.privacy"), foreground=PAL["muted"], wraplength=1000, justify="left").pack(anchor="w", padx=12, pady=(0, 6))

    def _drop_toggle(self):
        self.cfg["settings"]["drop_share"] = bool(self.drop_var.get()); self.cfg["settings"]["drop_asked"] = True
        save_cfg(self.cfg)

    def _drop_server_save(self):
        u = self.drop_srv.get().strip().rstrip("/")
        if u and not re.match(r"^https?://[\w.\-:]+(/[\w.\-/]*)?$", u):
            return messagebox.showerror(APP_NAME, t("drops.bad_url"))
        self.cfg["settings"]["drop_server"] = u; save_cfg(self.cfg); self.toast(t("drops.saved"))

    def drops_summary(self):
        url = self.cfg["settings"].get("drop_server") or dropstats.DEFAULT_URL
        if not url: return messagebox.showinfo(APP_NAME, t("drops.no_server"))
        def go():
            try: s_ = dropstats.summary(url); msg = t("drops.summary", drops=s_.get("drops", 0), players=s_.get("contributors", 0))
            except Exception as e: msg = t("drops.send_failed", e=e)
            self.root.after(0, lambda: messagebox.showinfo(APP_NAME, msg))
        threading.Thread(target=go, daemon=True).start()

    def community_stats(self):
        url = self.cfg["settings"].get("drop_server") or dropstats.DEFAULT_URL
        if not url: return messagebox.showinfo(APP_NAME, t("drops.no_server"))
        act = next((k for k, v in self._acts.items() if v == self.cs_act.get()), None)
        q, key = self.cs_q.get().strip(), self.cfg["settings"].get("license_key", "")
        def go():
            try: data, err = dropstats.stats(url, key, act, q), None
            except Exception as e: data, err = None, e
            self.root.after(0, lambda: self._community_show(data, err))
        threading.Thread(target=go, daemon=True).start()

    def _community_show(self, d, err):
        T = self.cs_out; T.config(state="normal"); T.delete("1.0", "end")
        if err: T.insert("end", t("drops.send_failed", e=err))
        else:
            T.insert("end", t("drops.weeks", n=d.get("weeks"), since=d.get("since")) + "\n")
            for a in d.get("activities", [])[:8]:
                T.insert("end", f"  {self._acts.get(a['activity'], a['activity'])}: {a['drops']}  ·  ★{a.get('named') or 0}  ⬢{a.get('exotic') or 0}  ·  {a.get('players')}👤\n")
            if d.get("top"):
                T.insert("end", "\n" + t("drops.top", act=self._acts.get(d["activity"], d["activity"])) + "\n")
                for x in d["top"][:15]: T.insert("end", f"  {x['n']:4d}  {x['item']}  ({x.get('slot') or x.get('kind')})\n")
            if d.get("where") is not None and d.get("q"):
                T.insert("end", "\n" + t("drops.where", q=d["q"]) + "\n")
                for w in d["where"]: T.insert("end", f"  {self._acts.get(w['activity'], w['activity'])}: {w['n']}  ({w['per1000']}‰)\n")
                if not d["where"]: T.insert("end", "  —\n")
        T.config(state="disabled")

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
        ttk.Button(row, text=ui_theme.with_icon(t("ai.diag"), "🩺"), command=self.run_voice_diag).pack(side="left", padx=(4, 0))
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
            log.exception("Microphone failed")
            self.results.put(("vstatus", t("err.mic", e=e)))

    def run_voice_diag(self):
        self.vstatus.config(text=t("ai.diag_running"))
        def work():
            rows = voice_diagnostics(self.cfg)
            self.results.put(("chat", "sys", "\n".join(rows)))
            self.results.put(("vstatus", ""))
        threading.Thread(target=work, daemon=True).start()

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
            except RuntimeError as e:                  # konuşma tanıyıcı kurulu değil: beklenen durum, iz kaydı gerekmez
                log.warning("Voice command unavailable: %s", e)
                self.results.put(("vstatus", t("err.stt", e=e)))
            except Exception as e:
                log.exception("Voice command failed")
                self.results.put(("vstatus", t("err.stt", e=e)))
            finally:
                self.voice_busy = False
        threading.Thread(target=work, daemon=True).start()

    def save_ai_settings(self):
        st = self.cfg["settings"]
        try:
            check_hotkey(self.av["voice_hotkey"].get())
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
        """Görevler v3: yalnızca arayüz dilinde, gruplu ve öz liste; çift tıkla → görselli ayrıntı penceresi.
        Alt sekmeler: Görevler · Ekle/Ekrandan oku · Claude ile getir · Sıfırlama ve senkron."""
        st = self.cfg["settings"]
        self.task_nb = ttk.Notebook(self.tabs["tasks"]); self.task_nb.pack(fill="both", expand=True, padx=8, pady=8)
        pg = {}
        for key, icon in (("list", "🗂"), ("add", "➕"), ("claude", "🤖"), ("sync", "⏱")):
            fr = ttk.Frame(self.task_nb); self.task_nb.add(fr, text=f" {icon} {t('tpage.' + key)} ")
            pg[key] = fr

        # ---- liste
        L = pg["list"]
        head = ttk.Frame(L); head.pack(fill="x", padx=6, pady=(8, 4))
        self.task_cat = tk.StringVar(value=TASK_CATS[0])
        self.cat_btns = {}
        icons = {"projects": "📋", "journey": "🧭", "manhunt": "🎯"}
        for c in TASK_CATS:
            b = ttk.Radiobutton(head, text="", value=c, variable=self.task_cat, style="Toolbutton",
                                command=self.refresh_tasks)
            b.pack(side="left", padx=(0, 6)); self.cat_btns[c] = (b, icons.get(c, "•"))
        self.task_q = tk.StringVar()
        ttk.Label(head, text="🔎").pack(side="left", padx=(14, 2))
        qe = ttk.Entry(head, textvariable=self.task_q, width=24); qe.pack(side="left")
        qe.bind("<KeyRelease>", lambda e=None: self.refresh_tasks())
        self.hide_done = tk.BooleanVar(value=bool(st.get("tasks_hide_done", False)))
        ttk.Checkbutton(head, text=t("tasks.hide_done"), variable=self.hide_done,
                        command=lambda: (st.__setitem__("tasks_hide_done", self.hide_done.get()), save_cfg(self.cfg), self.refresh_tasks())).pack(side="left", padx=12)
        self.reset_lbl = ttk.Label(head, foreground=PAL["muted"]); self.reset_lbl.pack(side="right")

        body = ttk.Panedwindow(L, orient="horizontal"); body.pack(fill="both", expand=True, padx=6, pady=4)
        lf, rf = ttk.Frame(body), ttk.Frame(body)
        body.add(lf, weight=3); body.add(rf, weight=2)
        self.task_tv = ttk.Treeview(lf, columns=("st", "src"), show="tree headings", selectmode="browse")
        self.task_tv.heading("#0", text=t("tasks.col_task")); self.task_tv.column("#0", width=560, anchor="w")
        self.task_tv.heading("st", text="✔"); self.task_tv.column("st", width=44, anchor="center", stretch=False)
        self.task_tv.heading("src", text=t("col.source")); self.task_tv.column("src", width=90, anchor="center", stretch=False)
        self.task_tv.tag_configure("group", font=(ui_theme.FONT_SEMI, 10), foreground=PAL["accent"])
        self.task_tv.tag_configure("done", foreground=PAL["muted"])
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.task_tv.yview); self.task_tv.configure(yscrollcommand=sb.set)
        self.task_tv.pack(side="left", fill="both", expand=True); sb.pack(side="left", fill="y")
        self.task_tv.bind("<Double-1>", self.on_task_double)
        self.task_tv.bind("<Return>", self.on_task_double)
        self.task_tv.bind("<<TreeviewSelect>>", self.show_task_how)
        self.task_tv.bind("<space>", lambda e=None: e is not None and self.toggle_task_done())
        # sağ: önizleme kartı
        card = tk.Frame(rf, bg=PAL["surface"], highlightthickness=1, highlightbackground=PAL["border"])
        card.pack(fill="both", expand=True, padx=(8, 0))
        self.prev_title = tk.Label(card, text=t("tasks.how_pick"), bg=PAL["surface"], fg=PAL["fg"], font=(ui_theme.FONT_SEMI, 13),
                                   wraplength=420, justify="left", anchor="w")
        self.prev_title.pack(fill="x", padx=14, pady=(14, 4))
        self.prev_meta = tk.Label(card, text="", bg=PAL["surface"], fg=PAL["accent"], font=(ui_theme.FONT, 9), anchor="w")
        self.prev_meta.pack(fill="x", padx=14)
        self.how_lbl = tk.Label(card, text="", bg=PAL["surface"], fg=PAL["muted"], font=(ui_theme.FONT, 10), wraplength=420,
                                justify="left", anchor="nw")
        self.how_lbl.pack(fill="both", expand=True, padx=14, pady=8)
        card.bind("<Configure>", lambda e=None: e is not None and [w.config(wraplength=max(160, e.width - 30)) for w in (self.prev_title, self.how_lbl)])
        pb = tk.Frame(card, bg=PAL["surface"]); pb.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(pb, text=ui_theme.with_icon(t("tasks.details"), "🔍"), style="Accent.TButton", command=self.on_task_double).pack(side="left")
        self.how_btn = ttk.Button(pb, text=ui_theme.with_icon(t("tasks.open_source"), "🔗"), command=self.open_how_source, state="disabled")
        self.how_btn.pack(side="left", padx=6)
        tb = ttk.Frame(L); tb.pack(fill="x", padx=6, pady=(2, 8))
        ttk.Button(tb, text=ui_theme.with_icon(t("task.toggle_done"), "✔"), command=self.toggle_task_done).pack(side="left")
        ttk.Button(tb, text=ui_theme.with_icon(t("btn.delete"), "🗑"), command=self.delete_task).pack(side="left", padx=6)
        ttk.Button(tb, text=ui_theme.with_icon(t("task.clear_done"), "🧹"), command=self.clear_done_tasks).pack(side="left")
        ttk.Button(tb, text=ui_theme.with_icon(t("task.clear_cat"), "🗑"), command=self.clear_all_tasks).pack(side="left", padx=6)
        ttk.Label(tb, text=t("tasks.dbl_hint"), foreground=PAL["muted"]).pack(side="right")

        # ---- ekle / ekrandan oku
        A = ui_theme.scrollable(pg["add"], PAL["bg"])
        add = ttk.LabelFrame(A, text=t("task.add_box")); add.pack(fill="x", padx=10, pady=10)
        row = ttk.Frame(add); row.pack(fill="x", padx=8, pady=6)
        ttk.Label(row, text=t("label.category")).pack(side="left")
        self.cat_var = tk.StringVar(value=add_choice_name(*ADD_CHOICES[0]))
        ttk.Combobox(row, textvariable=self.cat_var, values=[add_choice_name(*c) for c in ADD_CHOICES],
                     width=24, state="readonly").pack(side="left", padx=4)
        ttk.Button(row, text=t("task.read_screen"), command=self.capture_task_region).pack(side="left", padx=8)
        ttk.Button(row, text=ui_theme.with_icon(t("tasks.read_projects"), "📋"), style="Accent.TButton",
                   command=self.read_projects_screen).pack(side="left")
        ttk.Button(row, text=t("tasks.reset_region"), command=lambda: self.read_projects_screen(reselect=True)).pack(side="left", padx=6)
        ttk.Label(add, text=t("tasks.projects_note"), foreground=PAL["muted"], wraplength=900, justify="left").pack(anchor="w", padx=8)
        self.task_in = tk.Text(add, height=6, wrap="word"); self.task_in.pack(fill="x", padx=8, pady=(4, 4))
        row2 = ttk.Frame(add); row2.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(row2, text=t("task.translate_add"), command=self.translate_and_add, style="Accent.TButton").pack(side="left")
        self.tr_status = ttk.Label(row2, text=""); self.tr_status.pack(side="left", padx=10)

        # ---- Claude ile getir (eski ChatGPT ekran makrosu yerine)
        C = ui_theme.scrollable(pg["claude"], PAL["bg"])
        cb = ttk.LabelFrame(C, text="🤖 " + t("cl.box")); cb.pack(fill="x", padx=10, pady=10)
        ttk.Label(cb, text=t("cl.note"), wraplength=900, justify="left").pack(anchor="w", padx=8, pady=(6, 4))
        cr = ttk.Frame(cb); cr.pack(fill="x", padx=8, pady=6)
        ttk.Button(cr, text=ui_theme.with_icon(t("cl.run"), "🌐"), style="Accent.TButton", command=self.run_claude_fetch).pack(side="left")
        self.cl_replace = tk.BooleanVar(value=bool(st.get("claude_tasks_replace", True)))
        ttk.Checkbutton(cr, text=t("cl.replace"), variable=self.cl_replace).pack(side="left", padx=12)
        ttk.Label(cr, text=t("cl.hotkey")).pack(side="left", padx=(12, 2))
        self.gv = {"tasks_hotkey": tk.StringVar(value=str(st.get("tasks_hotkey", "<f10>")))}
        ttk.Entry(cr, textvariable=self.gv["tasks_hotkey"], width=8).pack(side="left")
        ttk.Button(cr, text=t("btn.save_short"), command=self.save_task_fetch_settings).pack(side="left", padx=6)
        self.cl_status = ttk.Label(cb, text=self.claude_cli_state(), foreground=PAL["muted"], wraplength=900, justify="left")
        self.cl_status.pack(anchor="w", padx=8)
        ttk.Label(cb, text=t("cl.raw"), foreground=PAL["muted"]).pack(anchor="w", padx=8, pady=(8, 0))
        self.cl_raw = tk.Text(cb, height=10, state="disabled", wrap="word", font=("Consolas", 9)); self.cl_raw.pack(fill="x", padx=8, pady=(0, 8))

        # ---- sıfırlama ve senkron
        S = ui_theme.scrollable(pg["sync"], PAL["bg"])
        top = ttk.LabelFrame(S, text=t("task.reset_box")); top.pack(fill="x", padx=10, pady=10)
        self.reset_lbl2 = ttk.Label(top, style="Section.TLabel"); self.reset_lbl2.pack(anchor="w", padx=8, pady=4)
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
        ttk.Label(top, text=t("task.reset_note"), foreground=PAL["muted"]).pack(anchor="w", padx=8, pady=(0, 4))
        fb = ttk.LabelFrame(S, text=t("tasks.feed_box")); fb.pack(fill="x", padx=10, pady=(0, 8))
        fr = ttk.Frame(fb); fr.pack(fill="x", padx=8, pady=6)
        ttk.Button(fr, text=ui_theme.with_icon(t("tasks.sync_now"), "🌐"), style="Accent.TButton",
                   command=lambda: self.meta_sync_start(force=True, what=("tasks",))).pack(side="left")
        self.bv_tasks = {k: tk.BooleanVar(value=bool(st.get(k, True))) for k in ("tasks_sync", "auto_reset_times")}
        ttk.Checkbutton(fr, text=t("tasks.enable"), variable=self.bv_tasks["tasks_sync"], command=self.save_task_feed_flags).pack(side="left", padx=(14, 0))
        ttk.Checkbutton(fr, text=t("tasks.auto_resets"), variable=self.bv_tasks["auto_reset_times"], command=self.save_task_feed_flags).pack(side="left", padx=(14, 0))
        self.tasks_info = ttk.Label(fb, text=self.tasks_status_text(), foreground=PAL["muted"], wraplength=900, justify="left")
        self.tasks_info.pack(anchor="w", padx=8)
        wr = ttk.Frame(fb); wr.pack(fill="x", padx=8, pady=(6, 2))
        ttk.Button(wr, text=ui_theme.with_icon(t("wiki.sync_now"), "📚"), style="Accent.TButton",
                   command=lambda: self.meta_sync_start(force=True, what=("wiki",))).pack(side="left")
        self.bv_tasks["wiki_sync"] = tk.BooleanVar(value=bool(st.get("wiki_sync", True)))
        ttk.Checkbutton(wr, text=t("wiki.enable"), variable=self.bv_tasks["wiki_sync"], command=self.save_task_feed_flags).pack(side="left", padx=(14, 0))
        ttk.Button(wr, text=ui_theme.with_icon(t("wiki.open"), "🔗"), command=self.open_wiki_page).pack(side="left", padx=(14, 0))
        self.wiki_lbl = ttk.Label(fb, text=self.wiki_status_text(), foreground=PAL["muted"], wraplength=900, justify="left")
        self.wiki_lbl.pack(anchor="w", padx=8)
        ttk.Label(fb, text=t("wiki.note") + "\n" + t("tasks.feed_note"), foreground=PAL["muted"], wraplength=900,
                  justify="left").pack(anchor="w", padx=8, pady=(4, 8))
        self.refresh_tasks(); self.update_reset_label()
        self.root.after(1500, self.translate_wiki_tasks)

    def claude_cli_state(self):
        return t("cl.ready") if find_claude_cli() else t("ai.cc_missing")

    def save_task_fetch_settings(self):
        st = self.cfg["settings"]
        try:
            check_hotkey(self.gv["tasks_hotkey"].get())
        except Exception as e:
            return messagebox.showerror(APP_NAME, t("err.bad_setting", e=e))
        st["tasks_hotkey"] = self.gv["tasks_hotkey"].get().strip()
        st["claude_tasks_replace"] = bool(self.cl_replace.get())
        save_cfg(self.cfg)
        if self.running: self.stop(); self.start()
        self.toast(t("msg.settings_saved"))

    def run_claude_fetch(self):  # pynput thread'inden de çağrılır: tk'ya dokunma
        if getattr(self, "_cl_busy", False): return
        self._cl_busy = True
        threading.Thread(target=self._claude_fetch_work, daemon=True).start()

    def _claude_fetch_work(self):
        st = self.cfg["settings"]
        try:
            if not find_claude_cli():
                return self.results.put(("cl_status", t("ai.cc_missing")))
            self.results.put(("cl_status", t("cl.working")))
            raw = ask_claude_code(st.get("claude_code_model", ""), claude_tasks_prompt(),
                                  [{"role": "user", "content": "List the current Division 2 Journey, Manhunt and project tasks as JSON."}],
                                  timeout=420, tools="WebSearch,WebFetch", max_turns=12)
            self.results.put(("cl_raw", raw))
            parsed, season = parse_claude_tasks(raw)
            total = sum(len(v) for v in parsed.values())
            if not total:
                return self.results.put(("cl_status", t("cl.nothing")))
            self.results.put(("claude_tasks", parsed, season))
        except Exception as e:
            log.exception("Claude task fetch failed")
            self.results.put(("cl_status", t("err.generic", e=e)))
        finally:
            self._cl_busy = False

    def apply_claude_tasks(self, parsed, season):
        replace = bool(getattr(self, "cl_replace", None) and self.cl_replace.get())
        added = 0
        for cat, items in parsed.items():
            cur = self.tasks["items"].setdefault(cat, [])
            if replace:
                cur[:] = [x for x in cur if x.get("src") != "Claude"]
            have = {gamedata.nrm(x.get("en") or task_text(x, "en")[0]) for x in cur}
            for x in items:
                if gamedata.nrm(x["en"]) in have: continue
                cur.append(x); have.add(gamedata.nrm(x["en"])); added += 1
        save_tasks(self.tasks); self.refresh_tasks()
        self.cl_status.config(text=t("cl.added", n=added, season=season or "—"))
        log.info("Claude tasks: %d added (season %s)", added, season)
        self.translate_wiki_tasks()

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
        txt = t("task.reset_line", daily=fmt_remaining(nd, now), day=weekday_names()[st["weekly_reset_day"]],
                weekly=fmt_remaining(nw, now))
        for w in (getattr(self, "reset_lbl", None), getattr(self, "reset_lbl2", None)):
            try: w and w.config(text=("⏱ " + txt))
            except tk.TclError: pass

    # ---------- Meta build senkronu ----------
    def meta_sync_start(self, force=False, quiet=False, what=("builds", "tasks", "wiki")):
        """Arka planda meta build + görev listelerini indirir (günde bir; force=True ise hemen)."""
        st = self.cfg["settings"]
        if self.meta_busy: return
        if not meta_sync.configured_urls(st.get("meta_feed_url", "")):
            if force and not quiet: self.toast(t("meta.not_configured"))
            log.info("Meta sync skipped: feed URL not configured")
            return
        do_b = "builds" in what and st.get("meta_sync", True) and (force or meta_sync.due(st, "builds"))
        do_t = "tasks" in what and st.get("tasks_sync", True) and (force or meta_sync.due(st, "tasks"))
        do_w = "wiki" in what and st.get("wiki_sync", True) and (force or meta_sync.due(st, "wiki"))
        if not (do_b or do_t or do_w): return
        self.meta_busy = True
        if do_b: st["meta_last_try"] = time.time()
        if do_t: st["tasks_last_try"] = time.time()
        if do_w: st["wiki_last_try"] = time.time()
        save_cfg(self.cfg)
        if force and not quiet: self.toast(t("meta.syncing"))
        verbose = force and not quiet

        def work():
            out = {}
            for kind, fn, cache, on in (("builds", meta_sync.run, META_CACHE, do_b),
                                        ("tasks", meta_sync.run_tasks, TASKS_CACHE, do_t)):
                if not on: continue
                try: out[kind] = (fn(self.cfg, cache, APP_VERSION, force=force), None)
                except Exception as e: out[kind] = (None, e)
            if do_b:     # oyun verisi (adlar, talent'ler, en yüksek değerler) — aynı depodan
                try:
                    urls = [u.replace("meta_builds.json", "game_data.json") for u in meta_sync.configured_urls(st.get("meta_feed_url", ""))
                            if u.endswith("meta_builds.json")]
                    gd, _ = meta_sync.fetch(urls, APP_VERSION)
                    if gd.get("schema") == 1 and gd.get("attributes") and gd.get("exotics"):
                        GAME_DATA_CACHE.write_text(json.dumps(gd, ensure_ascii=False), encoding="utf-8")
                        out["game"] = (gd.get("version"), None)
                except Exception as e:
                    log.debug("Game data fetch failed: %s", e)
            if do_w:     # wiki: ortak listenin söylediği sezon sayfasından başla (yeni sezona kendisi geçer)
                res_t = out.get("tasks", (None, None))[0]          # (feed, kaynak) ya da None
                start = res_t[0].get("wiki_season", "") if res_t else ""
                start = start or self.tasks.get("wiki_season") or wiki_sync.DEFAULT_SEASON
                try: out["wiki"] = (wiki_sync.run(start, APP_VERSION), None)
                except Exception as e: out["wiki"] = (None, e)
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
        if "wiki" in out:
            m = self.wiki_sync_done(*out["wiki"], verbose)
            if m: msgs.append(m)
        if "game" in out:
            global GAME
            GAME = gamedata.GameData(GAME_DATA_CACHE, BASE / "meta" / "game_data.json", BUNDLE / "meta" / "game_data.json").attach_learned(LEARNED_LIB)
            log.info("Game data loaded: version %s", GAME.data.get("version"))
        if msgs: self.toast("  ·  ".join(msgs))

    def tasks_sync_done(self, res, err, verbose):
        if err is not None:
            log.warning("Tasks sync failed: %s", err)
            return t("meta.failed") if verbose else ""
        feed, source = res
        st = self.cfg["settings"]
        summary = meta_sync.merge_tasks(self.tasks, feed)
        self.tasks["guides"] = feed.get("guides", [])
        if feed.get("wiki_season"): self.tasks["wiki_season"] = feed["wiki_season"]
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

    def wiki_sync_done(self, res, err, verbose):
        if err is not None:
            log.warning("Wiki sync failed: %s", err)
            return t("wiki.failed") if verbose else ""
        summary = meta_sync.merge_tasks(self.tasks, res, scope="wiki")
        cats = [x["cat"] for x in res["tasks"]]
        self.tasks["wiki_info"] = {"season": res["season"], "url": res["season_url"], "manhunt": cats.count("manhunt"),
                                   "journey": cats.count("journey"), "projects": cats.count("projects"),
                                   "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
        save_tasks(self.tasks)
        log.info("Wiki sync: season=%s tasks=%d added=%d removed=%d", res["season"], len(res["tasks"]),
                 summary["added"], summary["removed"])
        try: self.refresh_tasks()
        except Exception: pass
        if hasattr(self, "wiki_lbl"): self.wiki_lbl.config(text=self.wiki_status_text())
        self.translate_wiki_tasks()
        if summary["added"] or summary["removed"] or verbose:
            return t("wiki.synced", added=summary["added"], removed=summary["removed"])
        return ""

    def wiki_status_text(self):
        w = self.tasks.get("wiki_info")
        if not w: return t("wiki.none")
        return t("wiki.status", season=w["season"], manhunt=w["manhunt"], journey=w["journey"],
                 projects=w["projects"], when=w["time"])

    def open_wiki_page(self):
        import webbrowser
        webbrowser.open((self.tasks.get("wiki_info") or {}).get("url") or wiki_sync.WIKI + "Seasons")

    def translate_wiki_tasks(self):
        """Wiki metni İngilizce: bir yapay zekâ seçiliyse görevleri arka planda kullanıcının diline çevirir."""
        lang = i18n.current_language()
        if lang == "en" or self.cfg["settings"].get("ai_provider", "builtin") == "builtin" or getattr(self, "_wiki_tr_busy", False):
            return
        todo = [x for c in self.tasks["items"].values() for x in c
                if x.get("en") and lang not in x.get("texts", {}) and not (lang == "tr" and x.get("tr"))][:30]
        if not todo: return
        self._wiki_tr_busy = True

        def work():
            done = {}
            for x in todo:
                try:
                    tr, src = translate_task_text(self, x["en"])
                    if src != t("src.ai"): break                       # yapay zekâ yanıt vermiyor: sözlükle karıştırma
                    how_en = (x.get("how") or {}).get("en", "")
                    how_tr = translate_task_text(self, how_en)[0] if how_en else ""
                    done[id(x)] = (tr.strip(), how_tr.strip())
                except Exception as e:
                    log.debug("Wiki translation failed: %s", e); break
            self.root.after(0, lambda: self._apply_wiki_translations(lang, done))
        threading.Thread(target=work, daemon=True).start()

    def _apply_wiki_translations(self, lang, done):
        self._wiki_tr_busy = False
        for c in self.tasks["items"].values():
            for x in c:
                if id(x) in done:
                    tr, how = done[id(x)]
                    x.setdefault("texts", {})[lang] = tr
                    if how: x.setdefault("how", {})[lang] = how
        if done:
            save_tasks(self.tasks); self.refresh_tasks()
            log.info("Wiki tasks translated to %s: %d", lang, len(done))

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
        self.normalize_builds()
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
        drop = set()
        if self.tasks["last_daily_key"] and self.tasks["last_daily_key"] != dk: drop.add("daily")
        if self.tasks["last_weekly_key"] and self.tasks["last_weekly_key"] != wk: drop.add("weekly")
        if drop:
            self.tasks["items"]["projects"] = [x for x in self.tasks["items"]["projects"] if x.get("kind") not in drop]
            changed = True
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
        """Üstteki kategori düğmelerinde seçili olanın kimliği."""
        v = self.task_cat.get() if hasattr(self, "task_cat") else TASK_CATS[0]
        return v if v in TASK_CATS else TASK_CATS[0]

    def selected_task(self):
        """(kategori, sıra) ya da (None, None) — grup satırı seçiliyse None."""
        sel = self.task_tv.selection() if hasattr(self, "task_tv") else ()
        if not sel or not sel[0].startswith("t:"): return None, None
        _, cat, i = sel[0].split(":", 2)
        return cat, int(i)

    def refresh_tasks(self):
        if not hasattr(self, "task_tv"): return
        lang = i18n.current_language()
        cat = self.selected_list_cat()
        q = gamedata.nrm(self.task_q.get()) if hasattr(self, "task_q") else ""
        for c, (b, icon) in self.cat_btns.items():
            lst = self.tasks["items"].get(c, [])
            open_n = sum(1 for x in lst if not x.get("done"))
            b.config(text=f"{icon} {cat_name(c)}  {open_n}/{len(lst)}")
        keep = self.task_tv.selection()
        self.task_tv.delete(*self.task_tv.get_children())
        groups = {}
        lst = self.tasks["items"].get(cat, [])
        best = {}                                              # kopyalar: çevrili ve ortak listeden geleni göster
        for i, task in enumerate(lst):
            k = task_dedupe_key(task)
            score = (task_text(task, lang)[1], task.get("src", "").lower() != "wiki", bool(task.get("how")))
            if k not in best or score > best[k][0]: best[k] = (score, i)
        show_idx = {v[1] for v in best.values()}
        for i, task in enumerate(lst):
            if i not in show_idx: continue
            if self.hide_done.get() and task.get("done"): continue
            text, ok = task_text(task, lang)
            if q and q not in gamedata.nrm(text): continue
            gkey, group = task_group(task, cat)
            _, short = split_title(text)
            if cat == "projects" and task.get("kind") in PROJECT_KINDS:
                gkey, group = "k:" + task["kind"] + gkey, cat_name(task["kind"]) + (f" · {group}" if group != t("tasks.other_group") else "")
            if gkey not in groups:
                groups[gkey] = self.task_tv.insert("", "end", iid=f"g:{len(groups)}", text=f"  {group}", open=True, tags=("group",))
            group = gkey
            src = task.get("src", "")
            src = {"wiki": "📚 Wiki"}.get(src.lower(), src) + (" 💡" if self.task_how(task)[0] else "")
            label = ("" if ok else "🌐 ") + (short if len(short) <= 110 else short[:107] + "…")
            self.task_tv.insert(groups[group], "end", iid=f"t:{cat}:{i}", text=label,
                                values=("✔" if task.get("done") else "○", src), tags=("done",) if task.get("done") else ())
        for k in keep:
            if self.task_tv.exists(k): self.task_tv.selection_set(k); self.task_tv.see(k)
        self.show_task_how()

    def task_how(self, task):
        """(ipucu metni, kaynak adresi) — yalnızca arayüz dilinde (yoksa İngilizce)."""
        lang = i18n.current_language()
        how = task.get("how") or {}
        if how:
            return how.get(lang) or how.get("en", ""), task.get("url", "")
        g = meta_sync.find_guide(task.get("en", ""), self.tasks.get("guides"))
        if g:
            return g["tip"].get(lang) or g["tip"].get("en", ""), g.get("source", "")
        return "", task.get("url", "")

    def show_task_how(self, _=None):
        if not hasattr(self, "how_lbl"): return
        cat, i = self.selected_task()
        items = self.tasks["items"].get(cat, []) if cat else []
        if cat is None or i >= len(items):
            self.prev_title.config(text=t("tasks.how_pick")); self.prev_meta.config(text="")
            self.how_lbl.config(text=t("tasks.dbl_hint")); self.how_url = ""
            try: self.how_btn.config(state="disabled")
            except Exception: pass
            return
        task = items[i]
        text, ok = task_text(task)
        group, short = split_title(text)
        tip, url = self.task_how(task)
        self.prev_title.config(text=short)
        meta = [cat_name(cat)] + ([cat_name(task["kind"])] if task.get("kind") in PROJECT_KINDS else []) + ([group] if group else [])
        if task.get("done"): meta.append("✔ " + t("tasks.done"))
        if not ok: meta.append("🌐 " + t("tasks.not_translated"))
        self.prev_meta.config(text="  ·  ".join(meta))
        self.how_lbl.config(text=(tip or t("tasks.how_none")) + "\n\n" + t("tasks.dbl_hint")); self.how_url = url
        try: self.how_btn.config(state="normal" if url else "disabled")
        except Exception: pass

    def on_task_double(self, _=None):
        cat, i = self.selected_task()
        if cat is None:
            sel = self.task_tv.selection()                    # grup satırı: aç/kapa
            if sel: self.task_tv.item(sel[0], open=not self.task_tv.item(sel[0], "open"))
            return "break"
        self.open_task_detail(cat, i)
        return "break"

    def open_task_detail(self, cat, i):
        """Ayrı pencere: başlık bandı, açıklama, adım adım nasıl yapılır, wiki görselleri, kaynak, tamamlandı."""
        items = self.tasks["items"].get(cat, [])
        if i >= len(items): return
        task = items[i]
        text, ok = task_text(task)
        group, short = split_title(text)
        tip, url = self.task_how(task)
        f = getattr(self, "ui_factor", 1.0)
        w = tk.Toplevel(self.root); w.title(f"{cat_name(cat)} — {short[:60]}"); w.configure(bg=PAL["bg"])
        ww, wh = int(980 * max(0.6, f)), int(700 * max(0.6, f))
        w.geometry(f"{ww}x{wh}+{self.root.winfo_rootx() + 60}+{self.root.winfo_rooty() + 60}")
        w.transient(self.root)
        # başlık bandı
        hb = tk.Canvas(w, height=int(118 * max(0.6, f)), highlightthickness=0, bg="#0d0f13"); hb.pack(fill="x")
        accent = {"projects": "#ff6d10", "journey": "#38bdf8", "manhunt": "#ef4444"}.get(cat, PAL["accent"])

        def draw_head(_=None):
            hb.delete("all")
            W, H = max(200, hb.winfo_width()), int(hb["height"])
            for k in range(24):                                  # koyu degrade + altıgen deseni
                c = int(13 + 10 * (1 - k / 24))
                hb.create_rectangle(0, H * k / 24, W, H * (k + 1) / 24 + 1, fill=f"#{c:02x}{c + 2:02x}{c + 6:02x}", outline="")
            r = 18
            for row in range(-1, H // 26 + 2):
                for col in range(W // 31 + 2):
                    x, y = col * 31 + (15 if row % 2 else 0), row * 26
                    hb.create_polygon([(x + r * math.cos(math.radians(60 * a + 30)), y + r * math.sin(math.radians(60 * a + 30))) for a in range(6)],
                                      outline="#1b2029", fill="")
            hb.create_rectangle(0, H - 4, W, H, fill=accent, outline="")
            hb.create_text(24, 26, anchor="w", text=(cat_name(cat) + ("  ·  " + cat_name(task["kind"]) if task.get("kind") in PROJECT_KINDS else "")).upper(),
                           fill=accent, font=(ui_theme.FONT_SEMI, 10))
            hb.create_text(24, 56, anchor="w", text=group or cat_name(cat), fill="#ffffff", font=(ui_theme.FONT_SEMI, 20))
            st_txt = "✔ " + t("tasks.done") if task.get("done") else "○ " + t("tasks.open")
            hb.create_text(W - 24, 26, anchor="e", text=st_txt, fill="#4ade80" if task.get("done") else "#c9ced8",
                           font=(ui_theme.FONT_SEMI, 11))
        hb.bind("<Configure>", draw_head)
        body = ttk.Panedwindow(w, orient="horizontal"); body.pack(fill="both", expand=True, padx=12, pady=10)
        left, right = ttk.Frame(body), ttk.Frame(body)
        body.add(left, weight=3); body.add(right, weight=2)
        tk.Label(left, text=short, bg=PAL["bg"], fg=PAL["fg"], font=(ui_theme.FONT_SEMI, 14), wraplength=520,
                 justify="left", anchor="w").pack(fill="x", pady=(0, 6))
        if not ok:
            tk.Label(left, text="🌐 " + t("tasks.not_translated"), bg=PAL["bg"], fg=PAL["warning"], font=(ui_theme.FONT, 9),
                     anchor="w").pack(fill="x")
        ttk.Label(left, text=t("tasks.how_title"), style="Section.TLabel").pack(anchor="w", pady=(10, 2))
        steps = [x.strip() for x in re.split(r"(?<=[.!?])\s+", tip or "") if x.strip()]
        sf = tk.Frame(left, bg=PAL["bg"]); sf.pack(fill="x")
        if steps:
            for n, stp in enumerate(steps, 1):
                r_ = tk.Frame(sf, bg=PAL["bg"]); r_.pack(fill="x", pady=3)
                tk.Label(r_, text=str(n), bg=accent, fg="white", font=(ui_theme.FONT_SEMI, 9), width=3).pack(side="left", anchor="n")
                tk.Label(r_, text=stp, bg=PAL["bg"], fg=PAL["fg"], font=(ui_theme.FONT, 10), wraplength=480, justify="left",
                         anchor="w").pack(side="left", fill="x", padx=8)
        else:
            tk.Label(sf, text=t("tasks.how_none"), bg=PAL["bg"], fg=PAL["muted"], font=(ui_theme.FONT, 10), anchor="w").pack(fill="x")
        meta = []
        if task.get("src"): meta.append(t("tasks.src_line", src=task["src"]))
        if task.get("expires"): meta.append(t("tasks.expires", d=str(task["expires"])[:16]))
        if task.get("time"): meta.append(t("tasks.added_at", d=str(task["time"])[:16].replace("T", " ")))
        if meta:
            tk.Label(left, text="   ·   ".join(meta), bg=PAL["bg"], fg=PAL["muted"], font=(ui_theme.FONT, 9), anchor="w").pack(fill="x", pady=(12, 0))
        bb = ttk.Frame(left); bb.pack(fill="x", pady=12)

        def toggle():
            task["done"] = not task.get("done"); save_tasks(self.tasks); self.refresh_tasks(); draw_head()
            done_btn.config(text=ui_theme.with_icon(t("tasks.mark_open") if task.get("done") else t("tasks.mark_done"), "✔"))
        done_btn = ttk.Button(bb, text=ui_theme.with_icon(t("tasks.mark_open") if task.get("done") else t("tasks.mark_done"), "✔"),
                              style="Accent.TButton", command=toggle)
        done_btn.pack(side="left")
        if url:
            ttk.Button(bb, text=ui_theme.with_icon(t("tasks.open_source"), "🔗"), command=lambda: __import__("webbrowser").open(url)).pack(side="left", padx=6)
        ttk.Button(bb, text=t("btn.close"), command=w.destroy).pack(side="right")
        # görseller (wiki) — arka planda yüklenir
        ttk.Label(right, text="🖼 " + t("tasks.images"), style="Section.TLabel").pack(anchor="w")
        galh = ttk.Frame(right); galh.pack(fill="both", expand=True, pady=(4, 0))
        gal = ui_theme.scrollable(galh, PAL["surface"])
        loading = tk.Label(gal, text=t("tasks.images_loading"), bg=PAL["surface"], fg=PAL["muted"], font=(ui_theme.FONT, 10))
        loading.pack(pady=30)
        w._photos = []

        def show(imgs):
            if not w.winfo_exists(): return
            loading.destroy()
            if not imgs:
                art = Image.new("RGB", (420, 240), (18, 21, 28))
                d = ImageDraw.Draw(art)
                for k in range(0, 420, 28): d.line((k, 0, k - 120, 240), fill=(26, 30, 38), width=2)
                d.rectangle((0, 232, 420, 240), fill=tuple(int(accent[j:j + 2], 16) for j in (1, 3, 5)))
                imgs = [(art, "")]
                tk.Label(gal, text=t("tasks.no_images"), bg=PAL["surface"], fg=PAL["muted"], font=(ui_theme.FONT, 9)).pack(anchor="w", padx=8)
            maxw = max(240, right.winfo_width() - 20)
            for img, page in imgs:
                k = min(1.0, maxw / img.width, 260 / img.height)
                ph = ImageTk.PhotoImage(img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS))
                w._photos.append(ph)
                lb = tk.Label(gal, image=ph, bg=PAL["surface"], cursor="hand2" if page else "")
                lb.pack(padx=8, pady=(8, 0), anchor="w")
                if page:
                    tk.Label(gal, text="📚 " + page + " — The Division Wiki", bg=PAL["surface"], fg=PAL["muted"],
                             font=(ui_theme.FONT, 8)).pack(anchor="w", padx=8)
                    lb.bind("<Button-1>", lambda e, pg_=page: __import__("webbrowser").open(wiki_sync.page_url(pg_)))
        threading.Thread(target=lambda: (lambda imgs: self.root.after(0, lambda: show(imgs)))(load_task_images(task)), daemon=True).start()
        w.bind("<Escape>", lambda e: w.destroy())
        w.bind("<space>", lambda e: toggle())
        w.focus_set()

    def open_how_source(self):
        if getattr(self, "how_url", ""):
            import webbrowser; webbrowser.open(self.how_url)

    def read_projects_screen(self, reselect=False):
        """Oyundaki Projeler ekranını kayıtlı bölgeden okuyup seçili kategoriye ekler.
        Bölge yoksa (veya reselect) bir kez seçtirir; sonra tek tıkla okunur."""
        region = self.cfg["settings"].get("projects_region")
        if region and not reselect:
            def go():
                try:
                    text = ocr(grab(region), self.cfg["settings"]["ocr_lang"])
                except Exception as e:
                    err = e
                    return self.root.after(0, lambda: messagebox.showerror(APP_NAME, t("err.read", e=err)))
                self.root.after(0, lambda: self._projects_text(text))
            self.root.withdraw(); self.root.after(2500, lambda: (threading.Thread(target=go, daemon=True).start(),
                                                                 self.root.after(1200, self.root.deiconify)))
            return
        self._proj_mode = True
        self.capture_task_region()

    def _projects_text(self, text):
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 3]
        if not lines:
            return self.tr_status.config(text=t("tasks.nothing_read"))
        self.task_in.delete("1.0", "end"); self.task_in.insert("end", "\n".join(lines))
        self.translate_and_add()

    def capture_task_region(self):
        if not messagebox.askokcancel(APP_NAME, t("calib.ask_tasks")):
            self._proj_mode = False
            return
        self.root.withdraw(); self.root.after(5000, self._task_region_capture)

    def _task_region_capture(self):
        mon = self.screen_monitor()
        with mss.mss() as sct:
            s = sct.grab(mon); img = Image.frombytes("RGB", s.size, s.rgb)
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
            proj, self._proj_mode = getattr(self, "_proj_mode", False), False
            if proj:
                self.cfg["settings"]["projects_region"] = region; save_cfg(self.cfg)
            try:
                text = ocr(grab(region), self.cfg["settings"]["ocr_lang"])
                if proj:
                    self._projects_text(text)
                else:
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
                added.append({"en": line, "texts": {"en": line, i18n.current_language(): tr.strip()}, "src": src, "done": False,
                             "time": datetime.now().isoformat(timespec="seconds")})
            self.results.put(("tasks_added", cat, added))
        threading.Thread(target=work, daemon=True).start()

    def selected_add_cat(self):
        """Ekleme kutusundaki açılır listede seçili kategorinin kimliği."""
        label = self.cat_var.get()
        return next((c for c in ADD_CHOICES if add_choice_name(*c) == label), ADD_CHOICES[0])

    def toggle_task_done(self):
        cat, i = self.selected_task()
        if cat is None: return
        self.tasks["items"][cat][i]["done"] = not self.tasks["items"][cat][i].get("done")
        save_tasks(self.tasks); self.refresh_tasks()

    def delete_task(self):
        cat, i = self.selected_task()
        if cat is None: return
        del self.tasks["items"][cat][i]; save_tasks(self.tasks); self.refresh_tasks()

    def clear_done_tasks(self):
        cat = self.selected_list_cat()
        self.tasks["items"][cat] = [x for x in self.tasks["items"].get(cat, []) if not x.get("done")]
        save_tasks(self.tasks); self.refresh_tasks()

    def clear_all_tasks(self):
        cat = self.selected_list_cat()
        if messagebox.askyesno(APP_NAME, t("task.clear_cat_confirm", cat=cat_name(cat))):
            self.tasks["items"][cat] = []; save_tasks(self.tasks); self.refresh_tasks()

    # ---------- Ayarlar ----------
    def build_settings(self):
        st = self.cfg["settings"]
        # Ayarlar alt sekmelere ayrıldı: Genel · Tarama · Ekran ve oyun · OCR · Bindirme · Senkron · Kayıt
        outer = self.tabs["settings"]
        bar = ttk.Frame(outer); bar.pack(side="bottom", fill="x", padx=10, pady=8)
        ttk.Button(bar, text=ui_theme.with_icon(t("set.save"), "💾"), command=self.save_settings, style="Accent.TButton").pack(side="left")
        ttk.Label(bar, text=t("set.save_hint"), foreground=PAL["muted"]).pack(side="left", padx=12)
        self.set_nb = ttk.Notebook(outer); self.set_nb.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        P = {}
        for key, icon in (("general", "⚙"), ("fx", "✨"), ("scan", "🎯"), ("display", "🖥"), ("ocr", "🔍"), ("overlay", "🪟"),
                          ("sync", "🔄"), ("premium", "⭐"), ("logs", "📝")):
            holder = ttk.Frame(self.set_nb); self.set_nb.add(holder, text=f" {icon} {t('setpage.' + key)} ")
            P[key] = ui_theme.scrollable(holder, PAL["bg"])
        self._set_keys = ["general", "fx", "scan", "display", "ocr", "overlay", "sync", "premium", "logs"]
        self.build_fx_box(P["fx"], st)
        self.build_premium_box(P["premium"], st)
        if getattr(self, "_set_page", None) in self._set_keys:
            self.set_nb.select(self._set_keys.index(self._set_page))
        f = P["general"]
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

        # ---- Güncellemeler ----
        ub = ttk.LabelFrame(f, text="⬆ " + t("upd.box")); ub.pack(fill="x", padx=10, pady=6)
        ur = ttk.Frame(ub); ur.pack(fill="x", padx=8, pady=6)
        ttk.Label(ur, text=t("upd.current", v=APP_VERSION, mode=t("upd.mode_exe") if FROZEN else t("upd.mode_src"))).pack(side="left")
        ttk.Button(ur, text="🔎 " + t("upd.check"), command=lambda: self.check_update(auto=False)).pack(side="left", padx=10)
        self.upd_now_btn = ttk.Button(ur, text="⬆ " + t("upd.now"), command=self.do_update, style="Accent.TButton")
        self.upd_auto = tk.BooleanVar(value=bool(st.get("update_check", True)))
        ttk.Checkbutton(ur, text=t("upd.auto"), variable=self.upd_auto,
                        command=lambda: (st.__setitem__("update_check", bool(self.upd_auto.get())), save_cfg(self.cfg))).pack(side="right")
        self.upd_lbl = ttk.Label(ub, text="", foreground=PAL["muted"], wraplength=900, justify="left")
        self.upd_lbl.pack(anchor="w", padx=12, pady=(0, 6))
        if getattr(self, "upd_info", None) and updater.newer(self.upd_info["version"], APP_VERSION):
            self._upd_show(self.upd_info)

        # ---- Telefon arkadaşı ----
        cb_ = ttk.LabelFrame(P["sync"], text="📱 " + t("comp.box")); cb_.pack(fill="x", padx=10, pady=(10, 6))
        if self.premium_gate(cb_, "companion"):
            r = ttk.Frame(cb_); r.pack(fill="x", padx=8, pady=6)
            self.comp_btn = ttk.Button(r, text="", command=self.toggle_companion, style="Accent.TButton"); self.comp_btn.pack(side="left")
            ttk.Label(r, text=t("comp.port")).pack(side="left", padx=(12, 2))
            self.comp_port = tk.StringVar(value=str(st.get("companion_port", 8765)))
            ttk.Entry(r, textvariable=self.comp_port, width=7).pack(side="left")
            self.comp_url = ttk.Label(r, text="", foreground=PAL["accent"]); self.comp_url.pack(side="left", padx=12)
            self.comp_qr = tk.Label(cb_, bg=PAL["bg"]); self.comp_qr.pack(anchor="w", padx=12, pady=4)
            ttk.Label(cb_, text=t("comp.note"), foreground=PAL["muted"], wraplength=900, justify="left").pack(anchor="w", padx=12, pady=(0, 8))
            self._companion_ui()

        # ---- Meta build senkronu ----
        mb = ttk.LabelFrame(P["sync"], text=t("meta.box")); mb.pack(fill="x", padx=10, pady=6)
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

        # ---- Ekran ve oyun / display & game ----
        self.build_display_box(P, st)

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
        self.bv["ui_depth"] = tk.BooleanVar(value=bool(st.get("ui_depth", True)))
        ttk.Checkbutton(rb, text=t("v3d.depth"), variable=self.bv["ui_depth"]).pack(side="left", padx=(18, 0))
        ttk.Label(ap, text=t("set.theme_note") + "\n" + t("set.art_note"), foreground=PAL["muted"], wraplength=820,
                  justify="left").pack(anchor="w", padx=8, pady=(0, 6))

        # ---- Tarama / scanning ----
        gb = ttk.LabelFrame(P["scan"], text=t("set.scan_box")); gb.pack(fill="x", padx=10, pady=6)
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
        lg = ttk.LabelFrame(P["logs"], text=t("set.log_box")); lg.pack(fill="x", padx=10, pady=6)
        r1 = ttk.Frame(lg); r1.pack(fill="x", padx=8, pady=6)
        ttk.Label(r1, text=t("set.log_level")).pack(side="left")
        ttk.Combobox(r1, textvariable=self.sv["log_level"], values=["DEBUG", "INFO", "WARNING", "ERROR"],
                     width=10, state="readonly").pack(side="left", padx=6)
        ttk.Label(r1, text=t("set.log_size")).pack(side="left", padx=(12, 2))
        ttk.Entry(r1, textvariable=self.sv["log_max_kb"], width=7).pack(side="left")
        ttk.Label(r1, text=t("set.log_backups")).pack(side="left", padx=(12, 2))
        ttk.Entry(r1, textvariable=self.sv["log_backups"], width=5).pack(side="left")


    # ---------- Efektler ----------
    def build_fx_box(self, f, st):
        self.fxv = {
            "fx_cursor": tk.BooleanVar(value=bool(st.get("fx_cursor", True))),
            "fx_trail": tk.BooleanVar(value=bool(st.get("fx_trail", True))),
            "fx_transitions": tk.BooleanVar(value=bool(st.get("fx_transitions", True))),
            "fx_video": tk.BooleanVar(value=bool(st.get("fx_video", True))),
        }
        styles = [t("fx.cur_" + x) for x in fx.CURSOR_STYLES]
        self.fx_style = tk.StringVar(value=t("fx.cur_" + st.get("fx_cursor_style", "crosshair")))
        self.fx_ccol = tk.StringVar(value=st.get("fx_cursor_color", "#ff6d10"))
        self.fx_custom = tk.StringVar(value=st.get("fx_cursor_custom", ""))
        self.fx_tcol = tk.StringVar(value=st.get("fx_trail_color", "#ff6d10"))
        self.fx_tlen = tk.IntVar(value=int(st.get("fx_trail_len", 18)))
        self.fx_dim = tk.DoubleVar(value=float(st.get("fx_video_dim", 0.45)))
        colors = ["#ff6d10", "#ffffff", "#22c55e", "#38bdf8", "#ef4444", "#eab308", "#a855f7"]

        c = ttk.LabelFrame(f, text="🖱 " + t("fx.cursor_box")); c.pack(fill="x", padx=10, pady=(10, 6))
        r1 = ttk.Frame(c); r1.pack(fill="x", padx=8, pady=6)
        ttk.Checkbutton(r1, text=t("fx.enable"), variable=self.fxv["fx_cursor"]).pack(side="left")
        ttk.Label(r1, text=t("fx.style")).pack(side="left", padx=(16, 4))
        ttk.Combobox(r1, textvariable=self.fx_style, values=styles, state="readonly", width=20).pack(side="left")
        ttk.Label(r1, text=t("fx.color")).pack(side="left", padx=(16, 4))
        ttk.Combobox(r1, textvariable=self.fx_ccol, values=colors, width=10).pack(side="left")
        r2 = ttk.Frame(c); r2.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Label(r2, text=t("fx.custom")).pack(side="left")
        ttk.Entry(r2, textvariable=self.fx_custom, width=50).pack(side="left", padx=6)
        ttk.Button(r2, text=t("btn.browse"), command=lambda: self.fx_custom.set(filedialog.askopenfilename(
            filetypes=[(t("fx.images"), "*.png *.cur *.ani *.ico *.webp")]) or self.fx_custom.get())).pack(side="left")
        prev = ttk.Frame(c); prev.pack(fill="x", padx=8, pady=(0, 8))
        self._cur_prev = []
        for stl in fx.CURSOR_STYLES[1:-1]:
            img, _ = fx.draw_cursor(stl, self.fx_ccol.get(), 40)
            bg = Image.new("RGBA", img.size, (23, 26, 33, 255)); bg.alpha_composite(img)
            ph = ImageTk.PhotoImage(bg); self._cur_prev.append(ph)
            b = tk.Label(prev, image=ph, bg=PAL["surface"], cursor="hand2", padx=6, pady=6)
            b.pack(side="left", padx=4)
            b.bind("<Button-1>", lambda e, x=stl: self.fx_style.set(t("fx.cur_" + x)))
        ttk.Label(c, text=t("fx.cursor_note"), foreground=PAL["muted"], wraplength=900, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

        tr = ttk.LabelFrame(f, text="☄ " + t("fx.trail_box")); tr.pack(fill="x", padx=10, pady=6)
        r3 = ttk.Frame(tr); r3.pack(fill="x", padx=8, pady=8)
        ttk.Checkbutton(r3, text=t("fx.enable"), variable=self.fxv["fx_trail"]).pack(side="left")
        ttk.Label(r3, text=t("fx.color")).pack(side="left", padx=(16, 4))
        ttk.Combobox(r3, textvariable=self.fx_tcol, values=colors, width=10).pack(side="left")
        ttk.Label(r3, text=t("fx.length")).pack(side="left", padx=(16, 4))
        ttk.Scale(r3, from_=6, to=40, variable=self.fx_tlen, length=160).pack(side="left")

        an = ttk.LabelFrame(f, text="🎞 " + t("fx.anim_box")); an.pack(fill="x", padx=10, pady=6)
        ar = ttk.Frame(an); ar.pack(fill="x", padx=8, pady=8)
        ttk.Checkbutton(ar, text=t("fx.transitions"), variable=self.fxv["fx_transitions"]).pack(side="left")
        ttk.Label(ar, text=t("fx.speed")).pack(side="left", padx=(18, 4))
        self.fx_tms = tk.IntVar(value=int(st.get("fx_transition_ms", 650)))
        tl = ttk.Label(ar, text=f"{self.fx_tms.get()} ms", width=8)
        ttk.Scale(ar, from_=250, to=1500, variable=self.fx_tms, length=200,
                  command=lambda v: (self.fx_tms.set(int(float(v))), tl.config(text=f"{int(float(v))} ms"))).pack(side="left")
        tl.pack(side="left", padx=4)
        ttk.Button(ar, text=ui_theme.with_icon(t("fx.preview"), "▶"),
                   command=lambda: (setattr(self.fxbar, "duration", int(self.fx_tms.get())), self.fxbar.play())).pack(side="left", padx=8)

        self.fxv["fx_bgwatch"] = tk.BooleanVar(value=bool(st.get("fx_bgwatch", True)))
        self.fx_wdim = tk.DoubleVar(value=float(st.get("fx_bgwatch_dim", 0.0)))
        wbx = ttk.LabelFrame(f, text="⌚ " + t("fx.watch_box")); wbx.pack(fill="x", padx=10, pady=6)
        wr_ = ttk.Frame(wbx); wr_.pack(fill="x", padx=8, pady=6)
        ttk.Checkbutton(wr_, text=t("fx.enable"), variable=self.fxv["fx_bgwatch"]).pack(side="left")
        ttk.Label(wr_, text=t("fx.dim")).pack(side="left", padx=(16, 4))
        ttk.Scale(wr_, from_=0.0, to=0.7, variable=self.fx_wdim, length=160).pack(side="left")
        ttk.Label(wbx, text=t("fx.watch_note"), foreground=PAL["muted"], wraplength=900, justify="left").pack(anchor="w", padx=12, pady=(0, 8))
        vd = ttk.LabelFrame(f, text="🎬 " + t("fx.video_box")); vd.pack(fill="x", padx=10, pady=6)
        r4 = ttk.Frame(vd); r4.pack(fill="x", padx=8, pady=6)
        ttk.Checkbutton(r4, text=t("fx.enable"), variable=self.fxv["fx_video"]).pack(side="left")
        ttk.Label(r4, text=t("fx.dim")).pack(side="left", padx=(16, 4))
        ttk.Scale(r4, from_=0.0, to=0.7, variable=self.fx_dim, length=160).pack(side="left")
        ttk.Button(r4, text=ui_theme.with_icon(t("fx.add_video"), "➕"), command=self.add_video).pack(side="left", padx=(16, 4))
        ttk.Button(r4, text=ui_theme.with_icon(t("fx.open_videos"), "📂"), command=lambda: self.open_folder(ART_DIR / "videos")).pack(side="left")
        ttk.Button(r4, text=ui_theme.with_icon(t("fx.multiply"), "🎬"), command=lambda: self.make_videos(count=6)).pack(side="left", padx=(8, 0))
        n = len(fx.list_videos(ART_DIR / "videos"))
        be = fx.video_backend()
        mp4s = [x for x in (ART_DIR / "videos").glob("*") if x.suffix.lower() in fx.VIDEO_EXT] if (ART_DIR / "videos").exists() else []
        state = t("fx.video_state", n=n, be=be) + ("  ·  " + t("fx.webp_note", n=len(mp4s)) if be == "pil" and mp4s else "")
        self.fx_vstate = ttk.Label(vd, text=state, foreground=PAL["warning"] if not n else PAL["muted"])
        self.fx_vstate.pack(anchor="w", padx=12)
        ttk.Label(vd, text=t("fx.video_note"), foreground=PAL["muted"], wraplength=900, justify="left").pack(anchor="w", padx=12, pady=(2, 8))
        ttk.Button(f, text=ui_theme.with_icon(t("fx.apply"), "✨"), command=self.save_fx, style="Accent.TButton").pack(anchor="w", padx=12, pady=8)

    def _fx_from_ui(self):
        st = self.cfg["settings"]
        for k, v in self.fxv.items(): st[k] = bool(v.get())
        st["fx_cursor_style"] = next((x for x in fx.CURSOR_STYLES if t("fx.cur_" + x) == self.fx_style.get()), "crosshair")
        st["fx_cursor_color"] = self.fx_ccol.get().strip() or "#ff6d10"
        st["fx_cursor_custom"] = self.fx_custom.get().strip()
        st["fx_trail_color"] = self.fx_tcol.get().strip() or "#ff6d10"
        st["fx_trail_len"] = int(self.fx_tlen.get())
        st["fx_video_dim"] = round(float(self.fx_dim.get()), 2)
        st["fx_transition_ms"] = int(self.fx_tms.get())
        st["fx_bgwatch_dim"] = round(float(self.fx_wdim.get()), 2)
        if hasattr(self, "fxbar"): self.fxbar.duration = st["fx_transition_ms"]

    def save_fx(self):
        self._fx_from_ui(); save_cfg(self.cfg); self.apply_fx(); self.toast(t("msg.settings_saved"))

    def make_videos(self, count=None):
        """Özgün (koddan çizilen) arka plan videoları üretir; count verilirse yeni çeşitlerle çoğaltır."""
        if getattr(self, "_vid_busy", False): return
        self._vid_busy, self._vid_prog = True, 0.0
        def work():
            try:
                made = bgvideo.generate(ART_DIR / "videos", count=count, start_seed=int(time.time()) if count else None,
                                        progress=lambda f: setattr(self, "_vid_prog", f))
                log.info("Background videos generated: %d", len(made))
                self._vid_made = len(made)
            except Exception:
                log.exception("Background video generation failed"); self._vid_made = -1
            finally:
                self._vid_busy = False
        threading.Thread(target=work, daemon=True).start()
        self._vid_poll()

    def _vid_poll(self):
        if getattr(self, "_vid_busy", False):
            try: self.banner.toast_text = t("fx.generating", pct=int(self._vid_prog * 100)); self.banner._redraw_overlay_only()
            except Exception: pass
            self.root.after(700, self._vid_poll); return
        try: self.banner.toast_text = ""
        except Exception: pass
        n = getattr(self, "_vid_made", 0)
        if n >= 0:
            self.toast(t("fx.generated", n=n))
            if hasattr(self, "fx_vstate"):
                self.fx_vstate.config(text=t("fx.video_state", n=len(fx.list_videos(ART_DIR / "videos")), be=fx.video_backend() or "—"))
            if not getattr(self, "video", None): self.apply_fx()

    def add_video(self):
        paths = filedialog.askopenfilenames(initialdir=str(Path.home() / "Videos"),
                                            filetypes=[(t("fx.videos"), " ".join("*" + e for e in fx.VIDEO_EXT))])
        if not paths: return
        dst = ART_DIR / "videos"; dst.mkdir(parents=True, exist_ok=True)
        for p in paths:
            try: shutil.copy2(p, dst / Path(p).name)
            except Exception as e: log.warning("Video copy failed: %s", e)
        self.save_fx(); self._set_page = "fx"; self.rebuild_ui(tab="settings")

    def open_folder(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        try: os.startfile(str(path))
        except Exception: pass

    # ---------- Ekran ve oyun ----------
    def build_display_box(self, P, st):
        db = ttk.LabelFrame(P["display"], text=t("disp.box")); db.pack(fill="x", padx=10, pady=6)
        mw, mh, src = game_size(st)
        det_label = display.profile_for(mw, mh)[1]["label"]
        r1 = ttk.Frame(db); r1.pack(fill="x", padx=8, pady=(6, 2))
        ttk.Label(r1, text=t("disp.monitor", res=f"{mw}×{mh}", prof=det_label) +
                  {"window": "  ·  🎮 oyun penceresi / game window", "state.cfg": "  ·  oyun ayarı / game settings"}.get(src, "")).pack(side="left")
        r2 = ttk.Frame(db); r2.pack(fill="x", padx=8, pady=4)
        ttk.Label(r2, text=t("disp.profile")).pack(side="left")
        self._prof_keys = ["auto"] + list(display.PROFILES)
        labels = [t("disp.auto", prof=det_label)] + [display.PROFILES[k]["label"] for k in display.PROFILES]
        cur = st.get("res_profile", "auto")
        self.prof_var = tk.StringVar(value=labels[self._prof_keys.index(cur)] if cur in self._prof_keys else labels[0])
        pcb = ttk.Combobox(r2, textvariable=self.prof_var, values=labels, width=34, state="readonly"); pcb.pack(side="left", padx=6)
        self._prof_labels = labels
        pcb.bind("<<ComboboxSelected>>", lambda e: (self._apply_profile_defaults(), self._profile_warn()))
        self.prof_warn = ttk.Label(db, text="", foreground=PAL["warning"], wraplength=900, justify="left")
        self.prof_warn.pack(anchor="w", padx=12)
        self._profile_warn()

        # oyun ayar dosyası (yalnız okuma)
        gx = ttk.Frame(db); gx.pack(fill="x", padx=8, pady=(8, 2))
        ttk.Label(gx, text="🎮 " + t("disp.game_settings"), style="Section.TLabel").pack(side="left")
        ttk.Button(gx, text=ui_theme.with_icon(t("disp.reread"), "↻"), command=self.refresh_game_settings).pack(side="left", padx=10)
        self.gfx_lbl = ttk.Label(db, text="", justify="left", wraplength=900); self.gfx_lbl.pack(anchor="w", padx=12)
        self.gfx_tips = ttk.Label(db, text="", justify="left", wraplength=900, foreground=PAL["muted"]); self.gfx_tips.pack(anchor="w", padx=12, pady=(2, 6))
        self.refresh_game_settings()

        # OCR ince ayar
        ob = ttk.LabelFrame(P["ocr"], text=t("ocr.box")); ob.pack(fill="x", padx=10, pady=(10, 6))
        o1 = ttk.Frame(ob); o1.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(o1, text=t("ocr.engine")).pack(side="left")
        self._ocr_engines = {"auto": t("ocr.engine_auto"), "rapidocr": "RapidOCR (PP-OCR)", "tesseract": "Tesseract"}
        self.ocr_engine_var = tk.StringVar(value=self._ocr_engines.get(st.get("ocr_engine", "auto"), self._ocr_engines["auto"]))
        ttk.Combobox(o1, textvariable=self.ocr_engine_var, values=list(self._ocr_engines.values()), width=26,
                     state="readonly").pack(side="left", padx=6)
        eng_txt = t("ocr.active", name="RapidOCR" if OCR.name == "rapidocr" else "Tesseract")
        if not ocr_backend.rapid_available(): eng_txt += "  —  " + t("ocr.rapid_missing")
        ttk.Label(o1, text=eng_txt, foreground=PAL["muted"], wraplength=640, justify="left").pack(side="left", padx=10)
        o2 = ttk.Frame(ob); o2.pack(fill="x", padx=8, pady=4)
        ttk.Label(o2, text=t("ocr.threshold")).pack(side="left")
        self.ocr_thr = tk.IntVar(value=int(st.get("ocr_threshold", 170)))
        thr_lbl = ttk.Label(o2, text=str(self.ocr_thr.get()), width=4)
        ttk.Scale(o2, from_=100, to=230, variable=self.ocr_thr, length=220,
                  command=lambda v: (self.ocr_thr.set(int(float(v))), thr_lbl.config(text=str(int(float(v)))))).pack(side="left", padx=6)
        thr_lbl.pack(side="left")
        ttk.Label(o2, text=t("ocr.scale")).pack(side="left", padx=(16, 2))
        self.ocr_scale_var = tk.StringVar(value=t("ocr.auto") if st.get("ocr_scale", "auto") == "auto" else str(st.get("ocr_scale")))
        ttk.Combobox(o2, textvariable=self.ocr_scale_var, values=[t("ocr.auto"), "1.0", "1.25", "1.5", "1.75", "2.0", "2.5", "3.0", "4.0", "6.0"],
                     width=8).pack(side="left")
        ttk.Label(o2, text="PSM").pack(side="left", padx=(16, 2))
        self.ocr_psm_var = tk.StringVar(value=str(st.get("ocr_psm", 6)))
        ttk.Combobox(o2, textvariable=self.ocr_psm_var, values=["6", "4", "3", "11"], width=4, state="readonly").pack(side="left")
        ttk.Label(o2, text=t("ocr.passes")).pack(side="left", padx=(16, 2))
        self.ocr_pass_var = tk.StringVar(value=t("ocr.auto") if st.get("ocr_passes_auto", True) else str(st.get("ocr_passes", 3)))
        ttk.Combobox(o2, textvariable=self.ocr_pass_var, values=[t("ocr.auto"), "1", "2", "3"], width=9, state="readonly").pack(side="left")
        o3 = ttk.Frame(ob); o3.pack(fill="x", padx=8, pady=4)
        ttk.Button(o3, text=ui_theme.with_icon(t("ocr.calibrate"), "🎯"), command=self.auto_calibrate_ocr).pack(side="left")
        ttk.Button(o3, text=ui_theme.with_icon(t("ocr.preview"), "👁"), command=self.ocr_preview).pack(side="left", padx=8)
        self.ocr_msg = ttk.Label(o3, text="", foreground=PAL["muted"]); self.ocr_msg.pack(side="left", padx=8)
        ttk.Label(ob, text=t("ocr.note_rapid") if OCR.name == "rapidocr" else t("ocr.note"), foreground=PAL["muted"],
                  wraplength=900, justify="left").pack(anchor="w", padx=12, pady=(0, 4))

        # bindirme
        ovb = ttk.LabelFrame(P["overlay"], text=t("overlay.box")); ovb.pack(fill="x", padx=10, pady=(10, 6))
        o4 = ttk.Frame(ovb); o4.pack(fill="x", padx=8, pady=(8, 8))
        ttk.Label(o4, text=t("overlay.mode")).pack(side="left")
        self.ov_mode = tk.StringVar(value=t("overlay.mode_card") if st.get("overlay_mode", "card") == "card" else t("overlay.mode_corner"))
        ttk.Combobox(o4, textvariable=self.ov_mode, values=[t("overlay.mode_card"), t("overlay.mode_corner")], width=24,
                     state="readonly").pack(side="left", padx=6)
        ttk.Label(o4, text=t("overlay.alpha")).pack(side="left", padx=(16, 2))
        self.ov_alpha = tk.DoubleVar(value=float(st.get("overlay_alpha", 0.94)))
        ttk.Scale(o4, from_=0.4, to=1.0, variable=self.ov_alpha, length=120).pack(side="left")
        ttk.Label(o4, text=t("overlay.size")).pack(side="left", padx=(16, 2))
        self.ov_size = tk.DoubleVar(value=float(st.get("overlay_size", 1.0)))
        ttk.Scale(o4, from_=0.7, to=1.6, variable=self.ov_size, length=120).pack(side="left")
        ttk.Button(o4, text=ui_theme.with_icon(t("overlay.test"), "▶"), command=self.overlay_test).pack(side="left", padx=12)
        ttk.Label(ovb, text=t("overlay.note"), foreground=PAL["muted"], wraplength=900, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

    def _profile_warn(self):
        key = self._profile_key()
        w = display.profile_warning(key, *display.monitor_size()) if key != "auto" else None
        if w and w[0] == "disp.low_res":
            self.prof_warn.config(text="ℹ " + t(w[0], **w[1]), foreground=PAL["muted"])
        else:
            self.prof_warn.config(text=("⚠ " + t(w[0], **w[1])) if w else "", foreground=PAL["warning"])

    def _profile_key(self):
        try: return self._prof_keys[self._prof_labels.index(self.prof_var.get())]
        except (ValueError, AttributeError): return "auto"

    def _apply_profile_defaults(self):
        key = self._profile_key()
        if key in display.PROFILES:
            pr = display.PROFILES[key]
        else:
            gw, gh, _ = game_size()
            pr = display.profile_for(gw, gh)[1]
        self.ocr_thr.set(pr["threshold"]); self.ocr_scale_var.set(str(pr["ocr_scale"]))
        st = self.cfg["settings"]
        st["res_profile"], st["ocr_threshold"], st["ocr_scale"] = key, pr["threshold"], ("auto" if key == "auto" else pr["ocr_scale"])
        st["ocr_tuned"] = False
        save_cfg(self.cfg); apply_ocr_settings(st); self.card_box = None
        # pencere ve arayüz yeni ekran boyutuna göre hemen yeniden kurulur (yeniden başlatma yok)
        # Yazı tipleri Tk'da önbelleğe alındığı için ölçek değişimi en temiz yeniden açılışla uygulanır (~2 sn)
        self.toast(t("disp.restarting", prof=pr["label"]))
        self.root.after(600, lambda: self.restart_app(tab="settings", page="display"))

    def refresh_game_settings(self):
        """Oyunun kendi GFXSettings dosyasını OKUR (yazmaz) ve öneriler gösterir."""
        mw, mh = display.monitor_size()
        try: g = display.read_game_settings()
        except Exception as e:
            log.warning("Game settings read failed: %s", e); g = {"error": str(e)}
        self.game_settings = g
        if g and not g.get("error"):
            parts = [t("disp.file", f=Path(g["file"]).name)]
            if g.get("width"): parts.append(t("disp.game_res", res=f"{g['width']}×{g['height']}" + (f" @{g['refresh']}Hz" if g.get("refresh") else "")))
            if g.get("display_mode"): parts.append(t("disp.mode", m=g["display_mode"]))
            if g.get("hdr") is not None: parts.append("HDR: " + (t("disp.on") if g["hdr"] else t("disp.off")))
            if g.get("dx12") is not None: parts.append("DX12: " + (t("disp.on") if g["dx12"] else t("disp.off")))
            if g.get("preset"): parts.append(t("disp.preset", p=g["preset"]))
            if g.get("view_scale") is not None: parts.append(t("disp.view_scale", v=f"{float(g['view_scale']) * 100:.0f}%"))
            if g.get("enlarge_ui") is not None: parts.append(t("disp.ui_enlarge", v=t("disp.on") if g["enlarge_ui"] else t("disp.off")))
            self.gfx_lbl.config(text="   ·   ".join(parts))
            log.info("Game settings: %s", {k: g.get(k) for k in ("file", "width", "height", "refresh", "display_mode", "hdr", "dx12", "language", "view_scale", "enlarge_ui")})
        else:
            self.gfx_lbl.config(text=t("disp.not_found"))
        tips = [x for x in display.recommendations(g, mw, mh) if x[0] != "disp.no_game_file"]
        icon = {"disp.all_good": "✔ "}
        self.gfx_tips.config(text="".join(icon.get(k, "⚠ ") + t(k, **kw) + "\n" for k, kw in tips) + t("disp.requirements"))

    def _calib_image(self):
        img = getattr(self, "last_card_img", None)
        if img is None and (BASE / "last_card.png").exists():
            img = Image.open(BASE / "last_card.png").convert("RGB")
        return img

    def auto_calibrate_ocr(self):
        """Son okunan kart üzerinde eşik × ölçek denenir, en çok bilgiyi tanıyan ayar seçilir."""
        img = self._calib_image()
        if img is None: return messagebox.showinfo(APP_NAME, t("ocr.need_card"))
        if OCR.name == "tesseract" and not self.tess: return messagebox.showwarning(APP_NAME, t("msg.no_tesseract"))
        self.ocr_msg.config(text=t("ocr.calibrating")); self.root.update_idletasks()

        def work():
            old_t, old_s = gamedata.THRESHOLD, gamedata.SCALE
            best = (-1, old_t, None)
            try:
                if OCR.name == "rapidocr":                # renkli görüntüyü okur: eşik yok, yalnız ölçek denenir
                    for sc in (1.0, 1.25, 1.5, 2.0, 2.5):
                        q = ocr_quality(read_card(img, scale=sc)[0])
                        log.debug("calib rapidocr scale=%s quality=%.2f", sc, q)
                        if q > best[0]: best = (q, old_t, sc)
                    return self.root.after(0, lambda: self._calib_done(best))
                for sc in (1.25, 1.5, 2.0):
                    for th in range(130, 215, 20):
                        gamedata.THRESHOLD, gamedata.SCALE = th, sc
                        q = ocr_quality(read_card(img)[0])
                        log.debug("calib thr=%s scale=%s quality=%.2f", th, sc, q)
                        if q > best[0]: best = (q, th, sc)
            finally:
                gamedata.THRESHOLD, gamedata.SCALE = old_t, old_s
            self.root.after(0, lambda: self._calib_done(best))
        threading.Thread(target=work, daemon=True).start()

    def _calib_done(self, best):
        q, th, sc = best
        self.ocr_thr.set(th); self.ocr_scale_var.set(str(sc))
        self.ocr_msg.config(text=t("ocr.calib_done", thr=th, scale=sc, q=round(q, 1)))
        log.info("OCR auto-calibration: threshold=%s scale=%s quality=%.2f", th, sc, q)

    def ocr_preview(self):
        """Orijinal kart ↔ işlenmiş (siyah-beyaz) görüntü + OCR metni + tanınanlar; eşik kaydırıcısıyla canlı."""
        img = self._calib_image()
        if img is None: return messagebox.showinfo(APP_NAME, t("ocr.need_card"))
        w = tk.Toplevel(self.root); w.title(t("ocr.preview")); w.configure(bg=PAL["bg"])
        top = ttk.Frame(w); top.pack(fill="both", expand=True, padx=10, pady=10)
        h = min(640, int(self.root.winfo_screenheight() * 0.55))
        k = h / img.height
        orig = ImageTk.PhotoImage(img.resize((max(1, int(img.width * k)), h)))
        l1 = tk.Label(top, image=orig, bg=PAL["bg"]); l1.image = orig; l1.pack(side="left", padx=4)
        l2 = tk.Label(top, bg=PAL["bg"]); l2.pack(side="left", padx=4)
        txt = tk.Text(top, width=48, height=30, bg=PAL["surface"], fg=PAL["fg"], font=("Consolas", 10), relief="flat")
        txt.pack(side="left", fill="both", expand=True, padx=4)
        bar = ttk.Frame(w); bar.pack(fill="x", padx=10, pady=(0, 10))
        thr = tk.IntVar(value=self.ocr_thr.get())
        ttk.Label(bar, text=t("ocr.threshold")).pack(side="left")
        vl = ttk.Label(bar, text=str(thr.get()), width=4)

        def run(_=None):
            th = int(thr.get()); vl.config(text=str(th))
            old_t, old_s = gamedata.THRESHOLD, gamedata.SCALE
            gamedata.THRESHOLD = th
            sc = self.ocr_scale_var.get().strip()
            try: gamedata.SCALE = None if sc in ("", "auto", t("ocr.auto")) else float(sc)
            except ValueError: gamedata.SCALE = None
            try:
                if OCR.name == "rapidocr":
                    out, lines = read_card(img)
                    pre = img.copy(); dr = ImageDraw.Draw(pre)
                    for _, b, c in lines:
                        dr.rectangle(b, outline=(60, 220, 120) if c > 0.8 else (255, 170, 40), width=max(1, img.height // 400))
                else:
                    pre = gamedata.text_image(img)
                    out = read_card(img)[0] if self.tess else ""
                kk = h / pre.height
                ph = ImageTk.PhotoImage(pre.resize((max(1, int(pre.width * kk)), h)))
                l2.config(image=ph); l2.image = ph
            finally:
                gamedata.THRESHOLD, gamedata.SCALE = old_t, old_s
            txt.delete("1.0", "end"); txt.insert("end", out)
            if GAME.ok and out:
                r = GAME.recognize(out)
                txt.insert("end", "\n────────────\n" + f"{r.get('name')}  [{r.get('known') or '?'}]  {t('panel.quality')}: {round(r.get('confidence', 0) * 100)}%\n")
                for a, v in r.get("attrs", {}).items():
                    txt.insert("end", f"  {attr_name(a)}: {v:g}  ({r.get('quality', {}).get(a, '?')}%)\n")
                if r.get("talents"): txt.insert("end", "  ★ " + ", ".join(r["talents"]) + "\n")
                txt.insert("end", t("ocr.score", q=round(ocr_quality(out), 1)))
        ttk.Scale(bar, from_=100, to=230, variable=thr, length=300, command=lambda v: thr.set(int(float(v)))).pack(side="left", padx=6)
        vl.pack(side="left")
        ttk.Button(bar, text=ui_theme.with_icon(t("ocr.rerun"), "↻"), command=run).pack(side="left", padx=8)
        ttk.Button(bar, text=ui_theme.with_icon(t("ocr.use_this"), "✔"),
                   command=lambda: (self.ocr_thr.set(int(thr.get())), w.destroy())).pack(side="left")
        run()

    def overlay_test(self):
        """Bindirmeyi örnek bir sonuçla gösterir (son kart ya da örnek)."""
        st = self.cfg["settings"]
        backup = {k: st.get(k) for k in ("overlay_alpha", "overlay_size", "overlay_mode")}
        st["overlay_alpha"], st["overlay_size"] = float(self.ov_alpha.get()), float(self.ov_size.get())
        st["overlay_mode"] = "card" if self.ov_mode.get() == t("overlay.mode_card") else "corner"
        item = {"name": "Stoner LAMG", "rarity": ["HIGH-END"], "brand": None, "gear_set": None,
                "quality": {"weapon_type_damage": 74, "crit_chance": 85, "headshot_damage": 52}, "_note": ""}
        res = [(82, "Striker LMG", ["✔ Light Machine Gun", "talent Optimist"]), (55, "Heartbreaker", [])]
        if not getattr(self, "last_card_screen", None):
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.last_card_screen = (int(sw * 0.55), int(sh * 0.18), int(sw * 0.72), int(sh * 0.8))
        try: self.popup("KEEP", item, res, None)
        finally: st.update(backup)

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
        self.translate_wiki_tasks()

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
            check_hotkey(self.sv["hotkey"].get())
            for k in ("keep_threshold", "consider_threshold", "overlay_seconds", "auto_interval_ms"): st[k] = float(self.sv[k].get())
            st["log_max_kb"] = max(16, int(float(self.sv["log_max_kb"].get())))
            st["log_backups"] = max(0, int(float(self.sv["log_backups"].get())))
            st["bg_interval"] = max(0, int(float(self.sv["bg_interval"].get() or 0)))
            st["ocr_threshold"] = int(self.ocr_thr.get())
            st["ocr_tuned"] = st["ocr_threshold"] != active_profile({**st, "res_profile": self._profile_key()})[1]["threshold"]
            sc = self.ocr_scale_var.get().strip()
            st["ocr_scale"] = "auto" if sc in ("", "auto", t("ocr.auto")) else float(sc)
            st["ocr_psm"] = int(self.ocr_psm_var.get())
            pv = self.ocr_pass_var.get()
            st["ocr_passes_auto"] = pv == t("ocr.auto")       # otomatik: bilgisayarın okuma hızına göre 1-3
            if not st["ocr_passes_auto"]: st["ocr_passes"] = int(pv)
            st["ocr_engine"] = next((k for k, v in self._ocr_engines.items() if v == self.ocr_engine_var.get()), "auto")
            st["overlay_alpha"] = round(float(self.ov_alpha.get()), 2)
            st["overlay_size"] = round(float(self.ov_size.get()), 2)
        except Exception as e:
            return messagebox.showerror(APP_NAME, t("err.bad_setting", e=e))
        for k in ("hotkey", "overlay_corner", "ocr_lang", "tesseract_cmd", "log_level", "meta_feed_url"): st[k] = self.sv[k].get().strip()
        for k, v in self.bv.items(): st[k] = v.get()
        if hasattr(self, "fxv"): self._fx_from_ui()
        st["res_profile"] = self._profile_key()
        st["overlay_mode"] = "card" if self.ov_mode.get() == t("overlay.mode_card") else "corner"
        apply_ocr_settings(st); self.card_box = None
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
            self.apply_fx()
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
    # ---------- Güncelleme ----------
    def check_update(self, auto=False):
        st = self.cfg["settings"]
        if auto and (not st.get("update_check", True) or time.time() - float(st.get("update_last", 0) or 0) < 12 * 3600):
            return
        if getattr(self, "upd_busy", False): return
        self.upd_busy = True
        if not auto and hasattr(self, "upd_lbl"): self.upd_lbl.config(text=t("upd.checking"))

        def work():
            try: info, err = updater.latest(), None
            except Exception as e: info, err = None, e
            self.root.after(0, lambda: self._upd_checked(info, err, auto))
        threading.Thread(target=work, daemon=True).start()

    def _upd_checked(self, info, err, auto):
        self.upd_busy = False
        st = self.cfg["settings"]
        st["update_last"] = time.time(); save_cfg(self.cfg)
        if err:
            log.info("Update check failed: %s", err)
            if not auto:
                if hasattr(self, "upd_lbl"): self.upd_lbl.config(text=t("upd.failed", e=err))
            return
        self.upd_info = info
        if not updater.newer(info["version"], APP_VERSION):
            log.info("Update check: up to date (%s, latest %s)", APP_VERSION, info["version"])
            if hasattr(self, "upd_lbl"): self.upd_lbl.config(text=t("upd.latest_ok", v=APP_VERSION))
            return
        log.info("Update available: %s -> %s", APP_VERSION, info["version"])
        self._upd_show(info)
        if auto and st.get("update_skip") == info["version"]:
            return
        notes = re.sub(r"[#*`|>\-]+", " ", info.get("notes", "")).strip()
        notes = re.sub(r"\s+", " ", notes)[:500]
        if messagebox.askyesno(APP_NAME, t("upd.ask", new=info["version"], old=APP_VERSION) + ("\n\n" + notes if notes else "")):
            self.do_update()
        elif auto:
            st["update_skip"] = info["version"]; save_cfg(self.cfg)

    def _upd_show(self, info):
        if hasattr(self, "upd_lbl"):
            self.upd_lbl.config(text=t("upd.available", v=info["version"]))
            try: self.upd_now_btn.pack(side="left")
            except Exception: pass

    def do_update(self):
        info = getattr(self, "upd_info", None)
        if not info: return self.check_update(auto=False)
        if FROZEN and not info.get("setup"):
            return messagebox.showwarning(APP_NAME, t("upd.failed", e="no installer in release"))
        self.toast(t("upd.downloading", v=info["version"]))

        def prog(f):
            self.root.after(0, lambda: hasattr(self, "upd_lbl") and self.upd_lbl.config(text=t("upd.progress", p=int(f * 100))))

        def work():
            try:
                if FROZEN:
                    updater.install_frozen(info, prog)
                    self.root.after(0, self._upd_quit_for_installer)
                else:
                    n, bak = updater.update_source(info, BASE, prog)
                    self.root.after(0, lambda: self._upd_source_done(info, n, bak))
            except Exception as e:
                log.exception("Update failed")
                err = e
                self.root.after(0, lambda: messagebox.showerror(APP_NAME, t("upd.failed", e=err)))
        threading.Thread(target=work, daemon=True).start()

    def _upd_quit_for_installer(self):
        """Kurulum dosyası çalıştı: dosyaları değiştirebilsin diye program kapanır; kurulum bitince kendisi açar."""
        self.toast(t("upd.installing"))
        self.root.after(800, self.on_close)

    def _upd_source_done(self, info, n, bak):
        if not n:
            return messagebox.showinfo(APP_NAME, t("upd.no_changes"))
        if messagebox.askyesno(APP_NAME, t("upd.source_done", v=info["version"], n=n, bak=bak)):
            updater.restart_source()
            self.on_close()

    # ---------- Premium ----------
    def premium_gate(self, parent, feature):
        """Özellik açıksa True. Değilse yerine kilit kartı koyar ve False döner."""
        if self.ent.has(feature): return True
        box = tk.Frame(parent, bg=PAL["surface"], highlightthickness=1, highlightbackground=PAL["accent"])
        box.pack(fill="x", padx=4, pady=6)
        tk.Label(box, text="⭐ " + t("prem.locked") + " — " + t("feat." + feature), bg=PAL["surface"], fg=PAL["accent"],
                 font=(ui_theme.FONT_SEMI, 11), anchor="w").pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(box, text=t("prem.locked_hint"), bg=PAL["surface"], fg=PAL["muted"], font=(ui_theme.FONT, 10),
                 anchor="w", justify="left", wraplength=700).pack(fill="x", padx=10)
        ttk.Button(box, text=t("prem.open"), command=self.open_premium_page).pack(anchor="w", padx=10, pady=8)
        return False

    def open_premium_page(self):
        self.nb.select(self.tab_keys.index("settings"))
        if "premium" in getattr(self, "_set_keys", []): self.set_nb.select(self._set_keys.index("premium"))

    def build_premium_box(self, f, st):
        pb = ttk.LabelFrame(f, text=t("prem.box")); pb.pack(fill="x", padx=10, pady=(10, 6))
        r = ttk.Frame(pb); r.pack(fill="x", padx=8, pady=8)
        ttk.Label(r, text=t("prem.key")).pack(side="left")
        self.lic_var = tk.StringVar(value=st.get("license_key", ""))
        ttk.Entry(r, textvariable=self.lic_var, width=70).pack(side="left", padx=6, fill="x", expand=True)
        ttk.Button(r, text=ui_theme.with_icon(t("prem.activate"), "✔"), command=self.activate_license,
                   style="Accent.TButton").pack(side="left")
        self.lic_status = ttk.Label(pb, text="", foreground=PAL["muted"]); self.lic_status.pack(anchor="w", padx=12, pady=(0, 8))
        self._lic_status_text()
        fb = ttk.LabelFrame(f, text=t("prem.features")); fb.pack(fill="x", padx=10, pady=6)
        for name, tier in features.FEATURES.items():
            row = tk.Frame(fb, bg=PAL["bg"]); row.pack(fill="x", padx=10, pady=1)
            ok = self.ent.has(name)
            soon = name in features.COMING
            tk.Label(row, text=("⏳ " if soon else "✔ " if ok else "🔒 ") + t("feat." + name) + (f"  ({t('prem.soon')})" if soon else ""),
                     bg=PAL["bg"], fg=PAL["fg"] if ok and not soon else PAL["muted"],
                     font=(ui_theme.FONT, 10), anchor="w").pack(side="left")
            tk.Label(row, text=t("prem." + tier), bg=PAL["bg"], fg=PAL["accent"] if tier == "premium" else PAL["muted"],
                     font=(ui_theme.FONT_SEMI, 9)).pack(side="right")
        ttk.Label(f, text=t("prem.note"), foreground=PAL["muted"], wraplength=900, justify="left").pack(anchor="w", padx=14, pady=8)

    def _lic_status_text(self):
        e = self.ent
        if e.valid:
            exp = t("prem.exp", date=e.expires()) if e.expires() else t("prem.never")
            txt = t("prem.status_ok", name=e.payload.get("name", ""), exp=exp)
        elif e.reason == "empty":
            txt = t("prem.status_free")
        elif e.reason == "expired":
            txt = t("prem.expired", date=e.expires() or "?")
        else:
            txt = t("prem.bad_" + ("signature" if e.reason == "signature" else "format"))
        self.lic_status.config(text=txt)

    def activate_license(self):
        key = self.lic_var.get().strip()
        self.ent.set_key(key)
        self.cfg["settings"]["license_key"] = key if (self.ent.valid or not key) else self.cfg["settings"].get("license_key", "")
        save_cfg(self.cfg)
        log.info("License: %s (%s)", self.ent.tier, self.ent.reason)
        if self.ent.valid or not key:
            self.rebuild_ui(tab="settings"); self.open_premium_page()
        else:
            self._lic_status_text()

    # ---------- Satıcılar ----------
    def _build_vendor_page(self, p):
        top = ttk.Frame(p); top.pack(fill="x", padx=8, pady=8)
        self.vend_mode = tk.BooleanVar(value=bool(self.cfg["settings"].get("vendor_mode")))
        ttk.Checkbutton(top, text=t("vend.mode"), variable=self.vend_mode, command=self._vendor_mode_toggle).pack(side="left")
        ttk.Button(top, text="🧹 " + t("vend.clear_scans"), command=self._vendor_clear_scans).pack(side="left", padx=8)
        self.vend_btn = ttk.Button(top, text="↻ " + t("vend.refresh"), command=lambda: self.vendor_refresh(force=True))
        self.vend_btn.pack(side="right")
        self.vend_info = ttk.Label(p, text="", foreground=PAL["muted"], wraplength=1000, justify="left"); self.vend_info.pack(anchor="w", padx=12)
        self.vend_tl = ttk.Label(p, text="", foreground=PAL["accent"], wraplength=1000, justify="left"); self.vend_tl.pack(anchor="w", padx=12, pady=(4, 0))
        self.vend_tv = None
        holder = ttk.Frame(p); holder.pack(fill="both", expand=True, padx=8, pady=6)
        if self.premium_gate(holder, "vendor_watch"):
            cols = ("build", "slot", "item", "vendor", "fit", "attrs")
            tv = self.vend_tv = ttk.Treeview(holder, columns=cols, show="headings")
            for c, w in zip(cols, (230, 90, 220, 110, 110, 420)):
                tv.heading(c, text=t("vend.col_" + c)); tv.column(c, width=w, anchor="w", stretch=c in ("attrs", "build"))
            tv.pack(fill="both", expand=True)
        src = ttk.Frame(p); src.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Label(src, text=t("vend.source", src=vendor.SOURCE_NAME), foreground=PAL["muted"]).pack(side="left")
        import webbrowser
        ttk.Button(src, text="🌐", width=3, command=lambda: webbrowser.open(vendor.SOURCE_URL)).pack(side="left", padx=6)

    def _vendor_mode_toggle(self):
        self.cfg["settings"]["vendor_mode"] = bool(self.vend_mode.get()); save_cfg(self.cfg)
        self.toast(t("vend.mode_on") if self.vend_mode.get() else t("vend.mode_off"))

    def _vendor_clear_scans(self):
        self.vendor_scans = []; self._vendor_match(); self.refresh_stash()

    def vendor_refresh(self, force=False, auto=False):
        """Haftalık listeyi indir (Salı sıfırlamasından sonra bir kez ya da elle) ve eşleştir."""
        st = self.cfg["settings"]
        if self.vendor_busy: return
        if auto and not (st.get("vendor_auto", True) and self.ent.has("vendor_watch")): return
        if not force and not vendor.stale(self.vendor_week):
            self._vendor_match(notify=auto); return
        self.vendor_busy = True
        try: self.vend_info.config(text=t("vend.loading"))
        except Exception: pass

        def work():
            try:
                wk = vendor.fetch_week(); vendor.save_cache(VENDOR_CACHE, wk); err = None
            except Exception as e:
                wk, err = None, e
            self.root.after(0, lambda: self._vendor_loaded(wk, err, auto))
        threading.Thread(target=work, daemon=True).start()

    def _vendor_loaded(self, wk, err, auto):
        self.vendor_busy = False
        if wk: self.vendor_week = wk
        if err:
            log.warning("Vendor feed failed: %s", err)
            if not auto: messagebox.showwarning(APP_NAME, t("vend.failed", e=err))
        self._vendor_match(notify=auto)
        if self.current_tab() == "stash": self.refresh_stash()

    def _vendor_items(self):
        items = [vendor.to_item(r, GAME) for r in (self.vendor_week or {}).get("items", [])] if GAME.ok else []
        return items + list(self.vendor_scans)

    def _vendor_match(self, notify=False):
        if not self.ent.has("vendor_watch") or not GAME.ok:
            self.vendor_hits = []; return
        try:
            self.vendor_hits = vendor.match(self._vendor_items(), self.cfg["builds"], plan_of, self.stash.owned(), GAME)
        except Exception:
            log.exception("vendor match failed"); self.vendor_hits = []
        st = self.cfg["settings"]; wk = (self.vendor_week or {}).get("week", "")
        act = (active_build(self.cfg) or {}).get("name")
        mine = [h for h in self.vendor_hits if h["build"] == act]
        if notify and mine and st.get("vendor_notified") != wk:
            st["vendor_notified"] = wk; save_cfg(self.cfg)
            self.toast(t("vend.notify", n=len(mine), build=act))
        self._companion_refresh_build()

    def _refresh_vendor(self):
        wk = self.vendor_week or {}
        if wk:
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(wk.get("fetched", 0)))
            self.vend_info.config(text=t("vend.info", week=wk.get("week", "?"), n=len(wk.get("items", [])),
                                         scans=len(self.vendor_scans), when=when))
        else:
            self.vend_info.config(text=t("vend.none", scans=len(self.vendor_scans)))
        tl = vendor.target_loot_today(wk) if self.ent.has("vendor_watch") else []
        self.vend_tl.config(text="\n".join(t("vend.target", ev=ev, loot=", ".join(loot), missions=", ".join(ms[:5]))
                                           for ev, loot, ms, _d in tl))
        if self.vend_tv is None: return
        if not self.vendor_hits and (wk or self.vendor_scans): self._vendor_match()
        tv = self.vend_tv; tv.delete(*tv.get_children())
        act = (active_build(self.cfg) or {}).get("name")
        for h in sorted(self.vendor_hits, key=lambda h: (h["build"] != act, -h["gain"])):
            it = h["item"]
            tv.insert("", "end", values=(("★ " if h["build"] == act else "") + h["build"], slot_name(h["slot"]), it.get("name"),
                                         h.get("vendor") or "", f"{h['fit']}% ← {h['have']}%", self._attrs_short(it)))
        if not self.vendor_hits:
            tv.insert("", "end", values=("", "", t("vend.no_hits"), "", "", ""))

    # ---------- Telefon arkadaşı ----------
    def _companion_labels(self):
        return {"build": t("comp.h_build"), "vendor": t("comp.h_vendor"), "waiting": t("comp.waiting"),
                "offline": t("comp.offline"), "no_vendor": t("vend.no_hits")}

    def _companion_update(self, item, verdict, res, note):
        try:
            q = item.get("quality") or {}
            self.comp_state.update({
                "verdict": verdict, "verdict_label": verdict_label(verdict), "note": note or item.get("_note") or "",
                "best": f"{res[0][1]} {res[0][0]}%" if res else "",
                "item": {"name": item.get("name"), "slot": slot_name(item.get("slot") or "") if item.get("slot") else "",
                         "source": item.get("gear_set") or item.get("brand") or "",
                         "attrs": [{"name": attr_name(k), "value": f"{v:g}", "q": q.get(k)} for k, v in (item.get("attrs") or {}).items()]},
                "time": datetime.now().strftime("%H:%M:%S")})
            self._companion_refresh_build()
        except Exception:
            log.debug("companion state failed", exc_info=True)

    def _companion_refresh_build(self):
        try:
            b = active_build(self.cfg)
            if b:
                r = stash.optimize(b, plan_of(b), self.stash.owned(), GAME)
                self.comp_state["build"] = {"name": b["name"], "completion": r["completion"],
                                            "slots": [{"slot": slot_name(s), "item": (v["item"] or {}).get("name"), "fit": v["fit"],
                                                       "done": v["done"]} for s, v in r["slots"].items()]}
            act = (b or {}).get("name")
            self.comp_state["vendor"] = [{"slot": slot_name(h["slot"]), "item": h["item"].get("name"), "vendor": h.get("vendor"),
                                          "fit": h["fit"]} for h in self.vendor_hits if h["build"] == act][:6]
        except Exception:
            log.debug("companion build state failed", exc_info=True)

    def toggle_companion(self):
        if not self.ent.has("companion"): return
        if self.companion and self.companion.running:
            self.companion.stop(); self.companion = None
        else:
            try: port = max(1024, min(65535, int(self.comp_port.get())))
            except ValueError: port = 8765
            self.cfg["settings"]["companion_port"] = port; save_cfg(self.cfg)
            self._companion_refresh_build()
            try:
                self.companion = companion.Companion(lambda: dict(self.comp_state), self._companion_labels(), port,
                                                     lang=i18n.current_language())
                self.companion.start()
            except OSError as e:
                self.companion = None
                messagebox.showerror(APP_NAME, t("comp.port_busy", port=port, e=e))
        self._companion_ui()

    def _companion_ui(self):
        if not hasattr(self, "comp_btn"): return
        on = bool(self.companion and self.companion.running)
        self.comp_btn.config(text=("⏹ " + t("comp.stop")) if on else ("▶ " + t("comp.start")))
        self.comp_url.config(text=self.companion.url if on else "")
        img = companion.qr_image(self.companion.url, 5) if on else None
        if img is not None:
            ph = ImageTk.PhotoImage(img); self.comp_qr.config(image=ph); self.comp_qr.image = ph
        else:
            self.comp_qr.config(image="", text=(t("comp.no_qr") if on else "")); self.comp_qr.image = None

    # ---------- Build paylaşımı ----------
    def share_build(self):
        b = getattr(self, "cur", None)
        if not b: return
        code = share.encode(b)
        self.root.clipboard_clear(); self.root.clipboard_append(code)
        w = tk.Toplevel(self.root); w.title(t("share.title")); w.configure(bg=PAL["bg"])
        ttk.Label(w, text=t("share.copied", name=b["name"]), style="Section.TLabel").pack(anchor="w", padx=14, pady=(12, 4))
        txt = tk.Text(w, height=4, width=70, bg=PAL["surface"], fg=PAL["fg"], relief="flat", wrap="char", font=("Consolas", 9))
        txt.insert("end", code); txt.config(state="disabled"); txt.pack(fill="x", padx=14)
        img = companion.qr_image(code, 4)
        if img is not None:
            ph = ImageTk.PhotoImage(img); lb = tk.Label(w, image=ph, bg=PAL["bg"]); lb.image = ph; lb.pack(pady=8)
        ttk.Label(w, text=t("share.note"), foreground=PAL["muted"], wraplength=520, justify="left").pack(anchor="w", padx=14, pady=(0, 12))

    def import_build_code(self):
        try: clip = self.root.clipboard_get()
        except Exception: clip = ""
        w = tk.Toplevel(self.root); w.title(t("share.paste")); w.configure(bg=PAL["bg"])
        ttk.Label(w, text=t("share.paste_hint")).pack(anchor="w", padx=14, pady=(12, 4))
        txt = tk.Text(w, height=5, width=70, bg=PAL["surface"], fg=PAL["fg"], relief="flat", wrap="char", font=("Consolas", 9))
        txt.pack(fill="x", padx=14)
        if share.PREFIX in clip: txt.insert("end", clip.strip())

        def go():
            try:
                b = share.decode(txt.get("1.0", "end"))
            except ValueError as e:
                return messagebox.showerror(APP_NAME, t("share.bad", e=e), parent=w)
            names = {x["name"] for x in self.cfg["builds"]}
            base, i = b["name"], 2
            while b["name"] in names: b["name"] = f"{base} ({i})"; i += 1
            b.setdefault("sets_or_brands", []); b.setdefault("attributes", {}); b.setdefault("talents", {}); b.setdefault("set_bonus", 0)
            self.cfg["builds"].append(b); self.normalize_builds(); save_cfg(self.cfg)
            w.destroy(); self.refresh_builds(len(self.cfg["builds"]) - 1); self.toast(t("share.added", name=b["name"]))
        ttk.Button(w, text="✔ " + t("share.add"), command=go, style="Accent.TButton").pack(anchor="w", padx=14, pady=10)

    # ---------- Sandık (envanter) ----------
    def build_stash(self):
        f = self.tabs["stash"]
        self.st_nb = ttk.Notebook(f); self.st_nb.pack(fill="both", expand=True, padx=8, pady=8)
        pages = {}
        for key, icon in (("inv", "🗄"), ("opt", "🧮"), ("audit", "🧾"), ("vendor", "🏪")):
            holder = ttk.Frame(self.st_nb); self.st_nb.add(holder, text=f" {icon} {t('stash.page_' + key)} ")
            pages[key] = holder
        self.st_nb.bind("<<NotebookTabChanged>>", lambda e=None: self.refresh_stash())
        # envanter
        p = pages["inv"]
        bar = ttk.Frame(p); bar.pack(fill="x", padx=8, pady=8)
        self.st_rec = tk.BooleanVar(value=bool(self.cfg["settings"].get("stash_record", True)))
        ttk.Checkbutton(bar, text=t("stash.record"), variable=self.st_rec, command=self._stash_rec_toggle).pack(side="left")
        ttk.Label(bar, text=t("col.slot") + ":").pack(side="left", padx=(16, 2))
        self.st_slot = tk.StringVar(value=t("stash.all_slots"))
        cb = ttk.Combobox(bar, textvariable=self.st_slot, state="readonly", width=14,
                          values=[t("stash.all_slots")] + [slot_name(x) for x in engine.ALL_SLOTS])
        cb.pack(side="left"); cb.bind("<<ComboboxSelected>>", lambda e=None: self.refresh_stash())
        self.st_count = ttk.Label(bar, text="", foreground=PAL["muted"]); self.st_count.pack(side="left", padx=12)
        bar2 = ttk.Frame(p); bar2.pack(fill="x", padx=8)
        ttk.Button(bar2, text="🔨 " + t("stash.dismantled"), command=lambda: self._stash_mark("dismantled")).pack(side="left")
        ttk.Button(bar2, text="✖ " + t("stash.delete"), command=self._stash_delete).pack(side="left", padx=6)
        ttk.Button(bar2, text="⇩ " + t("stash.import"), command=self._stash_import).pack(side="left")
        ttk.Button(bar2, text="📤 " + t("stash.export") + ("" if self.ent.has("stash_export") else " ⭐"),
                   command=self._stash_export).pack(side="left", padx=6)
        ttk.Button(bar2, text="🧹 " + t("stash.clear"), command=self._stash_clear).pack(side="right")
        cols = ("slot", "item", "src", "attrs", "verdict", "best", "time")
        tv = self.st_tv = ttk.Treeview(p, columns=cols, show="headings", selectmode="extended")
        widths = {"slot": 90, "item": 200, "src": 170, "attrs": 330, "verdict": 120, "best": 220, "time": 130}
        for c in cols:
            tv.heading(c, text=t("stash.col_" + c)); tv.column(c, width=widths[c], anchor="w", stretch=c in ("attrs", "best"))
        for v, col in VFG.items(): tv.tag_configure(v, foreground=col)
        tv.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(p, text=t("stash.hint"), foreground=PAL["muted"], wraplength=1000, justify="left").pack(anchor="w", padx=12, pady=(0, 8))
        # optimize
        p = pages["opt"]
        ob = ttk.Frame(p); ob.pack(fill="x", padx=8, pady=8)
        ttk.Label(ob, text=t("label.build")).pack(side="left")
        self.opt_b = ttk.Combobox(ob, state="readonly", width=48, values=[b["name"] for b in self.cfg["builds"]])
        self.opt_b.pack(side="left", padx=6)
        a0 = active_build(self.cfg)
        if a0: self.opt_b.set(a0["name"])
        self.opt_b.bind("<<ComboboxSelected>>", lambda e=None: (self.set_active_build(self.opt_b.get()), self.refresh_stash()))
        self.opt_sum = ttk.Label(p, text="", style="Section.TLabel"); self.opt_sum.pack(anchor="w", padx=12)
        self.opt_bar = ttk.Progressbar(p, maximum=100); self.opt_bar.pack(fill="x", padx=12, pady=4)
        self.opt_next = ttk.Label(p, text="", foreground=PAL["accent"], wraplength=1000, justify="left"); self.opt_next.pack(anchor="w", padx=12)
        cols = ("slot", "item", "fit", "checks")
        self.opt_tv = ttk.Treeview(p, columns=cols, show="headings", height=8)
        for c, w in zip(cols, (100, 240, 70, 560)):
            self.opt_tv.heading(c, text=t("opt.col_" + c)); self.opt_tv.column(c, width=w, anchor="w", stretch=c == "checks")
        self.opt_tv.tag_configure("done", foreground=VFG.get("KEEP", PAL["fg"]))
        self.opt_tv.tag_configure("miss", foreground=VFG.get("DISMANTLE", PAL["fg"]))
        self.opt_tv.pack(fill="x", padx=8, pady=6)
        low = ttk.Frame(p); low.pack(fill="both", expand=True, padx=8, pady=4)
        lf = ttk.LabelFrame(low, text=t("opt.recal_title")); lf.pack(side="left", fill="both", expand=True, padx=(0, 4))
        rf = ttk.LabelFrame(low, text=t("opt.rank_title")); rf.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.opt_recal_box, self.opt_rank_box = lf, rf
        self.opt_recal = self.opt_rank = None
        if self.premium_gate(lf, "recal_advisor"):
            self.opt_recal = tk.Text(lf, height=8, bg=PAL["surface"], fg=PAL["fg"], relief="flat", wrap="word", font=(ui_theme.FONT, 10))
            self.opt_recal.pack(fill="both", expand=True, padx=6, pady=6)
        if self.premium_gate(rf, "optimizer_all"):
            self.opt_rank = tk.Text(rf, height=8, bg=PAL["surface"], fg=PAL["fg"], relief="flat", wrap="word", font=(ui_theme.FONT, 10))
            self.opt_rank.pack(fill="both", expand=True, padx=6, pady=6)
        # denetim
        p = pages["audit"]
        ab = ttk.Frame(p); ab.pack(fill="x", padx=8, pady=8)
        ttk.Button(ab, text="↻ " + t("audit.refresh"), command=self.refresh_stash).pack(side="left")
        ttk.Button(ab, text="🔨 " + t("audit.mark_all"), command=self._audit_mark_all).pack(side="left", padx=6)
        self.audit_txt = tk.Text(p, bg=PAL["surface"], fg=PAL["fg"], relief="flat", wrap="word", font=(ui_theme.FONT, 10))
        self.audit_txt.tag_configure("h", font=(ui_theme.FONT_SEMI, 12), foreground=PAL["accent"])
        self.audit_txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._audit = None
        self._build_vendor_page(pages["vendor"])
        self.refresh_stash()

    def _stash_rec_toggle(self):
        self.cfg["settings"]["stash_record"] = bool(self.st_rec.get()); save_cfg(self.cfg)

    @staticmethod
    def _attrs_short(r):
        q = r.get("quality") or {}
        return ", ".join(f"{attr_name(k)} {v:g}" + (f" ({q[k]}%)" if k in q else "") for k, v in (r.get("attrs") or {}).items())

    def refresh_stash(self):
        if not hasattr(self, "st_tv"): return
        items = self.stash.owned()
        sel = self.st_slot.get()
        slot = next((x for x in engine.ALL_SLOTS if slot_name(x) == sel), None)
        tv = self.st_tv; tv.delete(*tv.get_children())
        for r in sorted(items, key=lambda r: (engine.ALL_SLOTS.index(r["slot"]) if r.get("slot") in engine.ALL_SLOTS else 99,
                                              r.get("name") or "")):
            if slot and r.get("slot") != slot: continue
            v = r.get("verdict") or "REVIEW"
            tv.insert("", "end", iid=r["id"], tags=(v,), values=(
                slot_name(r.get("slot") or ""), r.get("name") or "?", r.get("gear_set") or r.get("brand") or "",
                self._attrs_short(r), verdict_label(v),
                (r.get("best") or "") + (f" ({r['score']}%)" if r.get("score") is not None else ""), (r.get("seen") or "")[:16].replace("T", " ")))
        from collections import Counter
        c = Counter(r.get("verdict") or "REVIEW" for r in items)
        self.st_count.config(text=t("stash.count", n=len(items), keep=c.get("KEEP", 0) + c.get("CONSIDER", 0),
                                    dis=c.get("DISMANTLE", 0), rev=c.get("REVIEW", 0)))
        try: page = self.st_nb.index(self.st_nb.select())
        except Exception: page = 0
        if page == 1: self._refresh_opt(items)
        elif page == 2: self._refresh_audit(items)
        elif page == 3: self._refresh_vendor()

    def _refresh_opt(self, items):
        b = build_by_name(self.cfg, self.opt_b.get()) or active_build(self.cfg)
        if not b: return
        plan = plan_of(b)
        r = stash.optimize(b, plan, items, GAME)
        self.opt_sum.config(text=t("opt.summary", build=b["name"], pct=r["completion"], done=r["done"], total=r["total"]))
        self.opt_bar["value"] = r["completion"]
        nxt = ", ".join(f"{slot_name(s)} ({req_lines_short(req)})" for s, _g, req in r["next_drop"])
        self.opt_next.config(text=t("opt.next", list=nxt) if nxt else "")
        tv = self.opt_tv; tv.delete(*tv.get_children())
        for s, v in r["slots"].items():
            it = v["item"]
            tv.insert("", "end", tags=("done" if v["done"] else "miss" if not it else "",), values=(
                slot_name(s), (it.get("name") if it else t("opt.none")), f"{v['fit']}%" if it else "—",
                "  ".join(check_lines(v["checks"])) if it else req_lines_short(v["req"])))
        if self.opt_recal is not None:
            self.opt_recal.config(state="normal"); self.opt_recal.delete("1.0", "end")
            adv = stash.recal_advice(r, items, GAME)
            for a in adv:
                self.opt_recal.insert("end", "• " + t("opt.recal_line", slot=slot_name(a["slot"]), target=a["target"],
                                                       attr=attr_name(a["attr"]), have=a["have"], q=a["quality"], donor=a["donor"]) + "\n")
            if not adv: self.opt_recal.insert("end", t("opt.recal_none") + "\n")
            self.opt_recal.insert("end", "\n" + t("opt.recal_note")); self.opt_recal.config(state="disabled")
        if self.opt_rank is not None:
            self.opt_rank.config(state="normal"); self.opt_rank.delete("1.0", "end")
            for pct, name, rr in stash.rank_builds(self.cfg["builds"], plan_of, items, GAME)[:10]:
                self.opt_rank.insert("end", f"{pct:3d}%  {name}  ({rr['done']}/{rr['total']})\n")
            self.opt_rank.config(state="disabled")

    def _refresh_audit(self, items):
        T = self.audit_txt; T.config(state="normal"); T.delete("1.0", "end")
        if not items:
            T.insert("end", t("audit.empty")); T.config(state="disabled"); return
        a = self._audit = stash.audit(items, self.cfg["builds"], plan_of, GAME)
        T.insert("end", t("audit.title") + "\n", "h")
        T.insert("end", t("audit.summary", n=a["total"], prot=a["protected"]) + "\n")
        T.insert("end", "  " + "  ·  ".join(f"{verdict_label(k)}: {v}" for k, v in a["counts"].items()) + "\n\n")
        T.insert("end", t("audit.dismantle", n=len(a["dismantle"])) + "\n", "h")
        for r in a["dismantle"]:
            T.insert("end", f"  🔨 {r.get('name')} ({slot_name(r.get('slot') or '')}) — {self._attrs_short(r)}\n")
        T.insert("end", "\n" + t("audit.dups", n=len(a["duplicates"])) + "\n", "h")
        for best, rest in a["duplicates"]:
            T.insert("end", "  " + t("audit.dup_line", name=best.get("name"), slot=slot_name(best.get("slot") or ""), n=len(rest)) + "\n")
        T.insert("end", "\n" + t("audit.library", n=len(a["library"])) + "\n", "h")
        for r, k, q in a["library"]:
            T.insert("end", "  📚 " + t("audit.lib_line", name=r.get("name"), attr=attr_name(k), q=q) + "\n")
        if a["ranks"]:
            T.insert("end", "\n" + t("opt.rank_title") + "\n", "h")
            for pct, name, rr in a["ranks"][:5]:
                T.insert("end", f"  {pct:3d}%  {name}\n")
        T.config(state="disabled")

    def _stash_selected(self):
        return list(self.st_tv.selection()) if hasattr(self, "st_tv") else []

    def _stash_mark(self, status):
        ids = self._stash_selected()
        if not ids: return
        for rid in ids: self.stash.mark(rid, status)
        self.stash.save(); self.refresh_stash()

    def _stash_delete(self):
        ids = self._stash_selected()
        if not ids: return
        for rid in ids: self.stash.remove(rid)
        self.stash.save(); self.refresh_stash()

    def _stash_import(self):
        n = self.stash.import_progress(self.progress, GAME) if GAME.ok else 0
        self.stash.save(); self.refresh_stash()
        messagebox.showinfo(APP_NAME, t("stash.imported", n=n))

    def _stash_clear(self):
        if not messagebox.askyesno(APP_NAME, t("stash.clear_q")): return
        self.stash.clear(); self.stash.save(); self.refresh_stash()

    def _stash_export(self):
        if not self.ent.has("stash_export"):
            return messagebox.showinfo(APP_NAME, t("prem.locked") + "\n\n" + t("prem.locked_hint"))
        p = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="td2_stash.csv", filetypes=[("CSV", "*.csv")])
        if not p: return
        stash.export_csv(self.stash.owned(), p)
        messagebox.showinfo(APP_NAME, t("stash.exported", path=p))

    def _audit_mark_all(self):
        a = self._audit or stash.audit(self.stash.owned(), self.cfg["builds"], plan_of, GAME)
        if not a["dismantle"]: return
        if not messagebox.askyesno(APP_NAME, t("audit.mark_q", n=len(a["dismantle"]))): return
        for r in a["dismantle"]: self.stash.mark(r["id"], "dismantled")
        self.stash.save(); self._audit = None; self.refresh_stash()

    def build_help(self):
        """Yardım metni dil dosyasındaki help.body anahtarından gelir."""
        f = self.tabs["help"]
        box = tk.Text(f, wrap="word", font=("Segoe UI", 10))
        sb = ttk.Scrollbar(f, orient="vertical", command=box.yview); box.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=10); box.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        body = t("help.body")
        if body == "help.body":          # dil dosyasında yoksa İngilizceye düşülmüş olmalı
            body = "Help text is missing from this language file."
        box.configure(bg=PAL["surface"], fg=PAL["fg"], relief="flat", padx=18, pady=14, spacing3=4)
        box.tag_configure("h", foreground=PAL["accent"], font=(ui_theme.FONT_SEMI, 12), spacing1=10)
        for line in body.splitlines(True):              # BÜYÜK HARFLİ satırlar başlık
            plain = line.strip()
            box.insert("end", line, ("h",) if plain and plain == plain.upper() and any(c.isalpha() for c in plain) else ())
        box.config(state="disabled")

    def on_close(self):
        self.stop(); self.speaker.close()
        if self.companion: self.companion.stop()
        st_ = self.cfg["settings"]
        if st_.get("drop_share") and len(self.dropq) and (st_.get("drop_server") or dropstats.DEFAULT_URL):
            th = threading.Thread(target=lambda: self.dropq.flush(st_.get("drop_server"), st_["drop_client"], timeout=3), daemon=True)
            th.start(); th.join(4)
        for name in ("video", "watch_bg", "trail_fx"):            # arka plan işleri / pencereleri
            obj = getattr(self, name, None)
            try: obj and obj.stop()
            except Exception: pass
        self.root.destroy()


if __name__ == "__main__":
    try:
        App().root.mainloop()
    except Exception:
        log.exception("Fatal error — application stopped")
        raise
    finally:
        log.info("=== %s stopped ===", APP_NAME)
