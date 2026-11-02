"""Yerel tanılama, güvenli görünüm ve maskelenmiş hata raporu yardımcıları.

Bu modül arayüzden bağımsız tutulur: rapor maskeleme ve güvenli görünüm
kuralları Tk penceresi açmadan test edilebilir. Ağ isteği ya da GitHub'a
gönderim burada yapılmaz; gönderim her zaman uygulamadaki açık kullanıcı
eylemiyle başlatılır.
"""
from __future__ import annotations

import collections
import logging
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import reports


SAFE_VIEW_CHANGES = {
    "ui_theme": "dark",
    "fx_cursor": False,
    "fx_trail": False,
    "fx_transitions": False,
    "fx_video": False,
    "fx_bgwatch": False,
    "fx_video_dim": 0.0,
    "ui_layout": "standard",
    "ui_nav_layout": "standard",
    "event_fx": "standard",
}


def apply_safe_view(settings: dict) -> list[str]:
    """Kararsız görsel katmanları kapatır; oyun ve kullanıcı verisine dokunmaz."""
    changed = []
    for key, value in SAFE_VIEW_CHANGES.items():
        if settings.get(key) != value:
            settings[key] = value
            changed.append(key)
    return changed


def safe_view_active(settings: dict) -> bool:
    return all(settings.get(key) == value for key, value in SAFE_VIEW_CHANGES.items())


@dataclass(frozen=True)
class Event:
    timestamp: str
    level: str
    category: str
    message: str


@dataclass(frozen=True)
class CheckResult:
    """Gerçek yerel denetimin sonucu; status: ok / warning / error / info."""
    key: str
    title: str
    status: str
    detail: str
    evidence: str = ""
    repair: str = ""


class EventBuffer(logging.Handler):
    """Uygulamanın son olaylarını bellekte tutan, iş parçacığı güvenli log handler."""

    def __init__(self, capacity: int = 300):
        super().__init__()
        self._events = collections.deque(maxlen=max(20, int(capacity)))
        self._lock = threading.Lock()
        self.setFormatter(logging.Formatter("%(message)s"))

    @staticmethod
    def category(record: logging.LogRecord) -> str:
        message = record.getMessage().lower()
        if "translation" in message or "çeviri" in message or "overlay" in message:
            return "Çeviri"
        if "ocr" in message or "scan" in message or "tarama" in message:
            return "OCR/Tarama"
        if "theme" in message or "anim" in message or "cursor" in message or "fx" in message:
            return "Görünüm"
        if "update" in message or "release" in message or "güncelle" in message:
            return "Güncelleme"
        if "game" in message or "oyun" in message or "sync" in message:
            return "Oyun/Senkron"
        if "assistant" in message or "voice" in message or "asistan" in message:
            return "Asistan/Ses"
        return "Sistem"

    def emit(self, record: logging.LogRecord) -> None:
        try:
            event = Event(time.strftime("%H:%M:%S", time.localtime(record.created)),
                          record.levelname, self.category(record), self.format(record)[:700])
            with self._lock:
                self._events.append(event)
        except Exception:
            self.handleError(record)

    def snapshot(self, limit: int = 120, level: str = "ALL") -> list[Event]:
        with self._lock:
            events = list(self._events)
        if level and level != "ALL":
            events = [event for event in events if event.level == level]
        return events[-max(1, int(limit)):]


def assess(snapshot: dict) -> list[dict]:
    """Basit, tekrarlanabilir kullanıcı tanılama sonuçları üretir."""
    settings = snapshot.get("settings", {})
    checks = []
    checks.append({"name": "Güvenli Görünüm", "status": "ok" if safe_view_active(settings) else "info",
                   "detail": "Kararlı görünüm profili etkin." if safe_view_active(settings) else "Animasyonlu görünüm profili kullanılıyor."})
    checks.append({"name": "Fare izi", "status": "warning" if settings.get("fx_trail") else "ok",
                   "detail": "Fare izi kapalı; katman/tıklama çakışmasını önler." if not settings.get("fx_trail") else "Açık. Sorun yaşanırsa Güvenli Görünüm kullanılmalı."})
    checks.append({"name": "Canlı çeviri", "status": "ok" if snapshot.get("translation_ready") else "warning",
                   "detail": "Çeviri motoru hazır." if snapshot.get("translation_ready") else "Motor/model hazır değil veya henüz doğrulanmadı."})
    checks.append({"name": "OCR", "status": "ok" if snapshot.get("ocr_ready") else "warning",
                   "detail": "OCR motoru algılandı." if snapshot.get("ocr_ready") else "OCR motoru bulunamadı; Ayarlar > OCR bölümünü kontrol edin."})
    checks.append({"name": "Oyun penceresi", "status": "ok" if snapshot.get("game_found") else "info",
                   "detail": "Oyun penceresi bulundu." if snapshot.get("game_found") else "Oyun açık değil veya henüz algılanmadı."})
    return checks


def _result(key, title, status, detail, evidence="", repair=""):
    return CheckResult(key, title, status, detail, evidence, repair)


def find_tesseract_candidate(settings: dict) -> str:
    """Tesseract adayını yalnız disk/PATH üzerinden arar, indirme yapmaz."""
    for value in (settings.get("tesseract_cmd", ""), shutil.which("tesseract") or "",
                  r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
        if value and Path(value).is_file():
            return str(Path(value))
    return ""


def run_checks(context: dict, command_runner=subprocess.run) -> list[CheckResult]:
    """Ağ, oyun belleği ve ekran görüntüsü kullanmadan gerçek makine kontrolleri.

    ``context`` uygulama tarafından sağlanan anlık, salt-okunur bilgileri taşır.
    Böylece motor hem birim testinde hem GUI iş parçacığı dışında çalışabilir.
    """
    settings = dict(context.get("settings") or {})
    results: list[CheckResult] = []

    config_path = Path(context.get("config_path") or "")
    try:
        if config_path.is_file() and config_path.stat().st_size > 1:
            results.append(_result("config", "Ayar dosyası", "ok", "Ayar dosyası okunabilir.", str(config_path)))
        else:
            results.append(_result("config", "Ayar dosyası", "warning", "Ayar dosyası bulunamadı veya boş; varsayılanlar kullanılacak."))
    except OSError as exc:
        results.append(_result("config", "Ayar dosyası", "error", "Ayar dosyasına erişilemiyor.", type(exc).__name__))

    log_dir = Path(context.get("log_dir") or "")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        probe = log_dir / ".td2_write_probe.tmp"
        probe.write_text("ok", encoding="utf-8"); probe.unlink(missing_ok=True)
        results.append(_result("log_write", "Günlük klasörü", "ok", "Günlük klasörü yazılabilir.", str(log_dir)))
    except OSError as exc:
        results.append(_result("log_write", "Günlük klasörü", "error", "Günlük klasörüne yazılamıyor.", type(exc).__name__))

    candidate = find_tesseract_candidate(settings)
    if not candidate:
        results.append(_result("tesseract", "Tesseract OCR", "warning", "Tesseract bulunamadı; seçili motor buna ihtiyaç duyabilir.", repair="tesseract"))
    else:
        try:
            completed = command_runner([candidate, "--version"], capture_output=True, text=True, timeout=5, check=False)
            first = ((completed.stdout or completed.stderr or "").splitlines() or [""])[0]
            if completed.returncode == 0:
                results.append(_result("tesseract", "Tesseract OCR", "ok", "Tesseract çalışıyor.", first[:160]))
            else:
                results.append(_result("tesseract", "Tesseract OCR", "error", "Tesseract komutu hata verdi.", first[:160], "tesseract"))
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append(_result("tesseract", "Tesseract OCR", "error", "Tesseract başlatılamadı.", type(exc).__name__, "tesseract"))

    if context.get("translation_ready"):
        results.append(_result("translation", "Çeviri motoru", "ok", "Seçili çeviri motoru/modeli hazır."))
    else:
        results.append(_result("translation", "Çeviri motoru", "warning", "Çeviri modeli veya sağlayıcısı hazır değil.", repair="translation_setup"))

    if context.get("overlay_present") and context.get("last_error"):
        results.append(_result("overlay", "Çeviri bindirmesi", "warning", "Açık bindirme son hata ile birlikte görünüyor; güvenli kapatıp yeniden başlatılabilir.",
                               str(context.get("last_error"))[:180], "reset_overlay"))
    else:
        results.append(_result("overlay", "Çeviri bindirmesi", "ok", "Açık bindirme hatası tespit edilmedi."))

    visual_risk = bool(settings.get("fx_trail") or settings.get("fx_video") or settings.get("fx_bgwatch"))
    if visual_risk:
        results.append(_result("visual_stack", "Görsel katmanlar", "warning", "Etkileşim katmanları açık; sorun yaşanırsa Güvenli Görünüm uygulanabilir.", repair="safe_view"))
    else:
        results.append(_result("visual_stack", "Görsel katmanlar", "ok", "Kararlı görsel katman profili etkin."))

    game = context.get("game_window")
    if game:
        results.append(_result("game_window", "Oyun penceresi", "ok", "Oyun penceresi algılandı.", f"{game.get('width')}x{game.get('height')}"))
    else:
        results.append(_result("game_window", "Oyun penceresi", "info", "Oyun açık değil veya simge durumunda; OCR testi atlandı."))
    return results


def apply_repairs(settings: dict, results: list[CheckResult]) -> tuple[list[str], dict]:
    """Sadece ayar düzeyindeki, geri alınabilir düzeltmeleri uygular.

    Dönüşteki ``actions`` uygulama katmanının (ör. bindirmeyi kapatma) açıkça
    kullanıcı isteğiyle yapacağı işlemleri bildirir.
    """
    keys = {result.repair for result in results if result.repair}
    changed: list[str] = []
    actions: dict[str, bool] = {}
    if "safe_view" in keys:
        changed.extend(apply_safe_view(settings))
    if "tesseract" in keys:
        candidate = find_tesseract_candidate(settings)
        if candidate and settings.get("tesseract_cmd") != candidate:
            settings["tesseract_cmd"] = candidate; changed.append("tesseract_cmd")
    if "reset_overlay" in keys:
        actions["reset_overlay"] = True
    return changed, actions


def markdown_report(app_version: str, snapshot: dict, events: list[Event]) -> str:
    """Paylaşmadan önce önizlenebilen, maskelenmiş Markdown hata raporu."""
    checks = assess(snapshot)
    # Dict/JSON gösteriminde Windows ayıracı iki kez kaçabilir; maskeleme
    # kuralının gerçek dosya yolunu görmesi için önce normalleştiriyoruz.
    system = reports.scrub(str(snapshot.get("system", {})).replace("\\\\", "\\"))
    lines = [
        "# TD2 Loot Advisor Tanılama Raporu",
        "",
        f"- Sürüm: `{reports.scrub(app_version)}`",
        f"- Oluşturma: `{time.strftime('%Y-%m-%d %H:%M:%S')}`",
        "- Bu taslak yerelde oluşturuldu; GitHub'a otomatik gönderilmez.",
        "",
        "## Hızlı Kontrol",
    ]
    lines += [f"- **{reports.scrub(x['name'])}:** {reports.scrub(x['detail'])}" for x in checks]
    lines += ["", "## Sistem Özeti", "```text", system[:3500], "```", "", "## Son Olaylar", "```text"]
    for event in events[-100:]:
        lines.append(reports.scrub(f"{event.timestamp} | {event.level:<7} | {event.category} | {event.message}"))
    lines += ["```", "", "## Gizlilik", "Kullanıcı klasörü yolları, e-posta adresleri, anahtarlar, tokenlar ve yerel ağ IP adresleri maskelenmiştir."]
    return "\n".join(lines)
