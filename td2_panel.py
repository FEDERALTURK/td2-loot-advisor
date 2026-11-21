"""TD2 Loot Advisor administration panel.

This is a small standard-library desktop client for the protected Worker API.
It deliberately does not contain a Supabase key; the admin token is entered at
runtime and is never stored in the per-user Windows config directory.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import urllib.error
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

APP_NAME = "TD2 Loot Advisor Panel"
APP_VERSION = "1.0.0"
DEFAULT_API = "https://td2-stats.td2loot.workers.dev"
CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def save_config(api_base: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"api_base": api_base}), encoding="utf-8")


def normalize_admin_token(value: str) -> str:
    """Normalize clipboard/file whitespace without ever persisting the token."""
    token = " ".join(str(value or "").split())
    if token.lower().startswith("admin "):
        token = token[6:].strip()
    if not token:
        raise RuntimeError("Admin token boş")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in token):
        raise RuntimeError("Admin token geçersiz karakter içeriyor")
    return token


def report_load_status(health: dict, reports: list[dict]) -> str:
    if reports:
        return f"{len(reports)} kayıt yüklendi"
    if health.get("ok") is True and health.get("panel_mirror") == "enabled":
        return "Worker ve Supabase yanıt verdi; henüz hata raporu yok"
    return "0 kayıt yüklendi"


def overview_metric_values(data: dict) -> dict[str, str]:
    accounts = data.get("accounts") or {}
    usage = data.get("usage") or {}
    tasks = data.get("tasks") or {}
    accounts = accounts if isinstance(accounts, dict) else {}
    usage = usage if isinstance(usage, dict) else {}
    tasks = tasks if isinstance(tasks, dict) else {}
    values = {
        "accounts": accounts.get("total"),
        "licenses": accounts.get("active_licenses"),
        "starts": usage.get("starts_today"),
        "suggestions": data.get("suggestions_pending"),
        "tasks": tasks.get("public"),
        "queued": data.get("reports_queued"),
    }
    return {key: "—" if value is None else str(value) for key, value in values.items()}


def api_get(base: str, path: str, token: str) -> dict:
    url = base.rstrip("/") + path
    token = normalize_admin_token(token)
    request = urllib.request.Request(
        url,
        headers={
            "accept": "application/json",
            "authorization": "Admin " + token,
            # Cloudflare blocks Python-urllib's default signature (1010).
            "user-agent": f"{APP_NAME}/{APP_VERSION}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except (OSError, ValueError):
            detail = {}
        raise RuntimeError(detail.get("error", f"HTTP {exc.code}")) from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(f"Worker bağlantısı kurulamadı: {reason}") from exc
    except socket.timeout as exc:
        raise RuntimeError("Worker bağlantısı zaman aşımına uğradı (10 sn)") from exc
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Worker yanıtı okunamadı: {exc}") from exc


class Panel(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1060x680")
        self.minsize(780, 480)
        self.configure(bg="#0b0e14")
        self.config_data = load_config()
        self._build_ui()

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#0b0e14")
        style.configure("TLabel", background="#0b0e14", foreground="#dbe4ec")
        style.configure("Header.TLabel", foreground="#ff6600", font=("Consolas", 16, "bold"))
        style.configure("TButton", padding=6)
        style.configure("Treeview", background="#131a22", fieldbackground="#131a22", foreground="#dbe4ec", rowheight=26)
        style.configure("Treeview.Heading", background="#202b36", foreground="#ff6600")

        header = ttk.Frame(self, padding=14)
        header.pack(fill="x")
        ttk.Label(header, text="◆ TD2 PANEL // OPERATIONS", style="Header.TLabel").pack(side="left")
        self.status = ttk.Label(header, text="Hazır")
        self.status.pack(side="right")

        settings = ttk.Frame(self, padding=(14, 0, 14, 10))
        settings.pack(fill="x")
        ttk.Label(settings, text="Worker API:").pack(side="left")
        self.api_var = tk.StringVar(value=self.config_data.get("api_base", DEFAULT_API))
        ttk.Entry(settings, textvariable=self.api_var, width=52).pack(side="left", padx=(6, 14))
        ttk.Label(settings, text="Admin token:").pack(side="left")
        # Admin token is session-only; never restore a token from disk.
        self.token_var = tk.StringVar(value="")
        ttk.Entry(settings, textvariable=self.token_var, show="•", width=30).pack(side="left", padx=6)
        ttk.Button(settings, text="Bağlan / Yenile", command=self.refresh).pack(side="left", padx=6)
        ttk.Button(settings, text="Ayarları kaydet", command=self.persist).pack(side="left")

        self.health = tk.StringVar(value="Health: bekleniyor")
        ttk.Label(self, textvariable=self.health, padding=(14, 0, 14, 8)).pack(anchor="w")

        summary = ttk.Frame(self, padding=(14, 0, 14, 10))
        summary.pack(fill="x")
        self.metric_vars = {}
        metrics = (("accounts", "Toplam hesap"), ("licenses", "Aktif lisans"), ("starts", "Bugün açılış"),
                   ("suggestions", "Bekleyen öneri"), ("tasks", "Yayındaki görev"), ("queued", "Kuyruktaki rapor"))
        for column, (key, title) in enumerate(metrics):
            card = tk.Frame(summary, bg="#131a22", highlightthickness=1, highlightbackground="#263341", padx=10, pady=7)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
            summary.columnconfigure(column, weight=1, uniform="metric")
            tk.Label(card, text=title, bg="#131a22", fg="#a0aab2", font=("Segoe UI", 8), anchor="w").pack(fill="x")
            value = tk.StringVar(value="—")
            self.metric_vars[key] = value
            tk.Label(card, textvariable=value, bg="#131a22", fg="#ff6600", font=("Consolas", 16, "bold"), anchor="w").pack(fill="x")
        self.summary_note = tk.StringVar(value="Yönetici özeti bekleniyor")
        ttk.Label(self, textvariable=self.summary_note, padding=(14, 0, 14, 8)).pack(anchor="w")

        body = ttk.Frame(self, padding=(14, 0, 14, 14))
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Supabase aynalanan hata raporları", style="Header.TLabel").pack(anchor="w", pady=(0, 8))
        columns = ("id", "created", "version", "platform", "severity", "code", "status", "message")
        self.table = ttk.Treeview(body, columns=columns, show="headings")
        for col, title, width in (("id", "ID", 55), ("created", "Tarih", 150), ("version", "Sürüm", 90),
                                  ("platform", "Platform", 90), ("severity", "Önem", 85), ("code", "Kod", 90),
                                  ("status", "Durum", 90), ("message", "Mesaj", 450)):
            self.table.heading(col, text=title)
            self.table.column(col, width=width, anchor="w")
        self.table.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(body, orient="vertical", command=self.table.yview)
        scroll.pack(fill="y", side="right")
        self.table.configure(yscrollcommand=scroll.set)

    def persist(self) -> None:
        try:
            save_config(self.api_var.get().strip())
            self.status.configure(text="Worker adresi kaydedildi; admin token yalnız oturumda tutulur")
        except OSError as exc:
            messagebox.showerror("Kaydetme hatası", str(exc))

    def refresh(self) -> None:
        self.status.configure(text="Bağlanıyor…")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self) -> None:
        try:
            base, token = self.api_var.get().strip(), self.token_var.get()
            health = api_get(base, "/v1/health", token)
            if not isinstance(health, dict):
                raise RuntimeError("Worker sağlık yanıtı beklenen biçimde değil")
            overview, overview_error = None, None
            reports, reports_error = None, None
            try:
                overview = api_get(base, "/v1/admin/overview", token)
                if not isinstance(overview, dict):
                    raise RuntimeError("Worker özet yanıtı beklenen biçimde değil")
            except Exception as exc:
                overview_error = str(exc) or exc.__class__.__name__
            try:
                response = api_get(base, "/v1/admin/panel-errors?limit=100", token)
                reports = response.get("reports") if isinstance(response, dict) else None
                if not isinstance(reports, list) or any(not isinstance(row, dict) for row in reports):
                    raise RuntimeError("Worker hata raporu yanıtı beklenen biçimde değil")
            except Exception as exc:
                reports_error = str(exc) or exc.__class__.__name__
            self.after(0, lambda: self._show(base, health, reports, overview, overview_error, reports_error))
        except Exception as exc:  # keep the UI out of a perpetual "connecting" state
            message = str(exc) or exc.__class__.__name__
            self.after(0, lambda: self._failed(message))

    def _show(self, base: str, health: dict, reports: list[dict] | None,
              overview: dict | None, overview_error: str | None, reports_error: str | None) -> None:
        self.health.set(f"Health: {'ONLINE' if health.get('ok') else 'OFFLINE'}  |  Supabase mirror: {health.get('panel_mirror', '?')}  |  {base}")
        if overview is not None:
            for key, value in overview_metric_values(overview).items():
                self.metric_vars[key].set(value)
            self.summary_note.set("Açılış sayısı anonim toplamdır; benzersiz kullanıcı sayısı değildir.")
        else:
            for value in self.metric_vars.values():
                value.set("—")
            self.summary_note.set("Yönetici özeti alınamadı: " + (overview_error or "bilinmeyen hata"))
        if reports is not None:
            for item in self.table.get_children():
                self.table.delete(item)
            for row in reports:
                self.table.insert("", "end", values=(row.get("id", ""), row.get("created_at", ""), row.get("app_version", ""),
                                                       row.get("platform", ""), row.get("severity", ""), row.get("error_code", ""),
                                                       row.get("status", ""), str(row.get("message_masked", "")).replace("\n", " ")[:500]))
            self.status.configure(text=report_load_status(health, reports))
        else:
            self.status.configure(text="Rapor listesi alınamadı: " + (reports_error or "bilinmeyen hata"))

    def _failed(self, message: str) -> None:
        self.health.set("Health: bağlantı başarısız")
        self.status.configure(text="Hata")
        messagebox.showerror("Panel bağlantısı", message)


if __name__ == "__main__":
    Panel().mainloop()
