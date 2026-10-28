#!/usr/bin/env python3
"""TD2 Raporları Admin Paneli: GitHub issue'larını göster, durumlarını yönet, yanıt ver."""
import json
import os
import re
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

sys.path.insert(0, str(Path(__file__).parent.parent))
from github_api import GitHub

class Panel:
    def __init__(self, root):
        self.root = root
        self.root.title("TD2 Raporları — Admin Paneli")
        self.root.geometry("1400x800")
        self.gh = None
        self.issues = []
        self.selected_issue = None
        self.config_path = self._config_path()
        self._load_settings()
        self._build_ui()
        self._on_settings_change()
    
    def _config_path(self):
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", "~")).expanduser()
        else:
            base = Path("~").expanduser()
        return base / "td2_admin_panel.json"
    
    def _load_settings(self):
        try:
            self.settings = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            self.settings = {"repo": "", "token": "", "api": "https://api.github.com", "admin_login": ""}
    
    def _save_settings(self):
        self.config_path.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
    
    def _build_ui(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True)
        
        # Ayarlar
        f_set = ttk.Frame(nb); nb.add(f_set, text="⚙ Ayarlar")
        ttk.Label(f_set, text="GitHub Repo (owner/name):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.e_repo = ttk.Entry(f_set, width=40)
        self.e_repo.insert(0, self.settings.get("repo", ""))
        self.e_repo.grid(row=0, column=1, padx=5, pady=5)
        self.e_repo.bind("<KeyRelease>", lambda e: self._update_setting("repo", self.e_repo.get()))
        
        ttk.Label(f_set, text="GitHub Token:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.e_token = ttk.Entry(f_set, width=40, show="•")
        self.e_token.insert(0, self.settings.get("token", ""))
        self.e_token.grid(row=1, column=1, padx=5, pady=5)
        self.e_token.bind("<KeyRelease>", lambda e: self._update_setting("token", self.e_token.get()))
        
        ttk.Label(f_set, text="API Base (isteğe bağlı):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.e_api = ttk.Entry(f_set, width=40)
        self.e_api.insert(0, self.settings.get("api", "https://api.github.com"))
        self.e_api.grid(row=2, column=1, padx=5, pady=5)
        self.e_api.bind("<KeyRelease>", lambda e: self._update_setting("api", self.e_api.get()))
        
        ttk.Label(f_set, text="Admin login (yanıtları göstermek için):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.e_admin = ttk.Entry(f_set, width=40)
        self.e_admin.insert(0, self.settings.get("admin_login", ""))
        self.e_admin.grid(row=3, column=1, padx=5, pady=5)
        self.e_admin.bind("<KeyRelease>", lambda e: self._update_setting("admin_login", self.e_admin.get()))
        
        # Liste
        f_list = ttk.Frame(nb); nb.add(f_list, text="📋 Raporlar")
        f_ctrl = ttk.Frame(f_list)
        f_ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Label(f_ctrl, text="Tür:").pack(side="left", padx=2)
        self.cb_type = ttk.Combobox(f_ctrl, values=["Hepsi", "bug", "feature", "question"], state="readonly", width=12)
        self.cb_type.set("Hepsi")
        self.cb_type.pack(side="left", padx=2)
        self.cb_type.bind("<<ComboboxSelected>>", lambda e: self._refresh())
        
        ttk.Label(f_ctrl, text="Durum:").pack(side="left", padx=2)
        self.cb_state = ttk.Combobox(f_ctrl, values=["Tümü", "Açık", "Kapalı"], state="readonly", width=12)
        self.cb_state.set("Açık")
        self.cb_state.pack(side="left", padx=2)
        self.cb_state.bind("<<ComboboxSelected>>", lambda e: self._refresh())
        
        ttk.Button(f_ctrl, text="Yenile", command=self._refresh).pack(side="left", padx=2)
        self.l_status = ttk.Label(f_ctrl, text="Hazır")
        self.l_status.pack(side="right", padx=2)
        
        # Treeview
        cols = ("No", "Tür", "Başlık", "Durum", "Sürüm")
        self.tree = ttk.Treeview(f_list, columns=cols, height=20)
        self.tree.column("#0", width=0)
        for col in cols:
            self.tree.column(col, width=150 if col == "Başlık" else 80)
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_select())
        
        # Detay
        f_det = ttk.Frame(nb); nb.add(f_det, text="📄 Detay")
        self.t_detail = tk.Text(f_det, height=20, width=100, wrap="word")
        self.t_detail.pack(fill="both", expand=True, padx=5, pady=5)
        
        f_act = ttk.Frame(f_det)
        f_act.pack(fill="x", padx=5, pady=5)
        ttk.Button(f_act, text="Yanıt Ekle", command=self._reply).pack(side="left", padx=2)
        ttk.Button(f_act, text="Etiket Ayarla", command=self._set_labels).pack(side="left", padx=2)
        ttk.Button(f_act, text="Kapat/Aç", command=self._toggle_state).pack(side="left", padx=2)
        ttk.Button(f_act, text="GitHub'da Aç", command=self._open_github).pack(side="left", padx=2)
    
    def _update_setting(self, key, val):
        self.settings[key] = val
        self._save_settings()
        self._on_settings_change()
    
    def _on_settings_change(self):
        if self.settings.get("repo") and self.settings.get("token"):
            self.gh = GitHub(self.settings["token"], self.settings["repo"], self.settings.get("api", "https://api.github.com"))
            self._refresh()
    
    def _refresh(self):
        if not self.gh:
            messagebox.showwarning("Ayar", "Repo ve token gir.")
            return
        self.l_status.config(text="Yükleniyor...")
        self.root.update()
        
        def fetch():
            state_map = {"Açık": "open", "Kapalı": "closed", "Tümü": "all"}
            state = state_map.get(self.cb_state.get(), "open")
            self.issues = self.gh.issues(state=state) or []
            self.root.after(0, self._populate_list)
        
        t = threading.Thread(target=fetch, daemon=True)
        t.start()
    
    def _populate_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for issue in self.issues:
            ttype = next((l.split(":")[1] for l in issue["labels"] if l.startswith("type:")), "?")
            version = next((l for l in issue["labels"] if l.startswith("v")), "?")
            
            if self.cb_type.get() != "Hepsi" and ttype != self.cb_type.get():
                continue
            
            self.tree.insert("", "end", values=(issue["number"], ttype, issue["title"][:40], issue["state"][:3], version))
        
        self.l_status.config(text=f"Toplam: {len(self.issues)}")
    
    def _on_select(self):
        sel = self.tree.selection()
        if not sel: return
        no = int(self.tree.item(sel[0])["values"][0])
        self.selected_issue = next((i for i in self.issues if i["number"] == no), None)
        if self.selected_issue:
            self._show_detail()
    
    def _show_detail(self):
        issue = self.selected_issue
        self.t_detail.config(state="normal")
        self.t_detail.delete("1.0", "end")
        
        body = f"#{issue['number']} — {issue['title']}\n"
        body += f"Durum: {issue['state']} | Etiketler: {', '.join(issue['labels'])}\n"
        body += f"Yapan: {issue['user']} ({issue['created_at'][:10]})\n\n"
        body += f"Gövde:\n{issue['body']}\n\n"
        
        comments = self.gh.comments(issue["number"]) or []
        if comments:
            body += f"--- {len(comments)} yorum ---\n"
            for c in comments:
                body += f"\n@{c['user']['login']} ({c['created_at'][:10]}):\n{c['body']}\n"
        
        self.t_detail.insert("1.0", body)
        self.t_detail.config(state="disabled")
    
    def _reply(self):
        if not self.selected_issue:
            messagebox.showwarning("Seç", "Bir issue seç.")
            return
        
        top = tk.Toplevel(self.root)
        top.title("Yanıt Ekle")
        ttk.Label(top, text="Yanıt metni:").pack(padx=5, pady=5)
        t = tk.Text(top, height=10, width=60)
        t.pack(padx=5, pady=5)
        
        def send():
            text = t.get("1.0", "end").strip()
            if self.gh.add_comment(self.selected_issue["number"], text):
                messagebox.showinfo("OK", "Yorum eklendi.")
                top.destroy()
                self._show_detail()
            else:
                messagebox.showerror("Hata", "Gönderilmedi.")
        
        ttk.Button(top, text="Gönder", command=send).pack(pady=5)
    
    def _set_labels(self):
        if not self.selected_issue:
            messagebox.showwarning("Seç", "Bir issue seç.")
            return
        
        top = tk.Toplevel(self.root)
        top.title("Etiketler")
        ttk.Label(top, text="Etiketler (virgülle ayırılmış):").pack(padx=5, pady=5)
        e = ttk.Entry(top, width=60)
        e.insert(0, ", ".join(self.selected_issue.get("labels", [])))
        e.pack(padx=5, pady=5)
        
        def save():
            labels = [l.strip() for l in e.get().split(",") if l.strip()]
            if self.gh.set_labels(self.selected_issue["number"], labels):
                messagebox.showinfo("OK", "Etiketler güncellendi.")
                top.destroy()
                self._refresh()
            else:
                messagebox.showerror("Hata", "Güncellenemedi.")
        
        ttk.Button(top, text="Kaydet", command=save).pack(pady=5)
    
    def _toggle_state(self):
        if not self.selected_issue:
            messagebox.showwarning("Seç", "Bir issue seç.")
            return
        
        no = self.selected_issue["number"]
        state = self.selected_issue["state"]
        if state == "open":
            if self.gh.close(no):
                messagebox.showinfo("OK", "Kapatıldı.")
                self._refresh()
        else:
            if self.gh.reopen(no):
                messagebox.showinfo("OK", "Açıldı.")
                self._refresh()
    
    def _open_github(self):
        if self.selected_issue:
            import webbrowser
            webbrowser.open(f"https://github.com/{self.settings['repo']}/issues/{self.selected_issue['number']}")

if __name__ == "__main__":
    root = tk.Tk()
    app = Panel(root)
    root.mainloop()
