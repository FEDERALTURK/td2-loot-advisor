"""Panelin kendini güncellemesi (yalnız derlenmiş exe).

Kaynak: özel rapor deposundaki "panel-vX.Y.Z" sürümleri (derleme iş akışı exe'yi ve SHA256SUMS dosyasını yükler).
Kurallar (kapalı-hatalı / fail-closed):
  - yalnız "panel-v<sürüm>" etiketi, yalnız "TD2RaporPaneli.exe" dosyası;
  - SHA256SUMS'ta bu dosya adına TAM eşleşen satır yoksa ya da özet tutmazsa hiçbir şey değişmez;
  - indirme GitHub API'si üzerinden (özel depo, panelin kendi token'ı); yönlendirmede token taşınmaz.
Değiştirme: çalışan exe ".old" adına çekilir (Windows buna izin verir), yeni exe yerine konur ve başlatılır;
bir sonraki açılışta ".old" silinir.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

TAG_RE = re.compile(r"^panel-v(\d+)\.(\d+)\.(\d+)$")
EXE = "TD2RaporPaneli.exe"
SUMS = "SHA256SUMS"


def vtuple(v):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(v))
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None


def _open(url, token=None, accept="application/vnd.github+json", api=True, timeout=30):
    h = {"user-agent": "TD2-Report-Panel", "accept": accept}
    if token and api: h["authorization"] = f"Bearer {token}"
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        return opener.open(urllib.request.Request(url, headers=h), timeout=timeout).read()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("location"):
            loc = e.headers["location"]
            if not loc.startswith("https://") and not loc.startswith("http://127.0.0.1"):
                raise RuntimeError("unexpected redirect")
            return urllib.request.urlopen(urllib.request.Request(loc, headers={"user-agent": "TD2-Report-Panel"}), timeout=timeout).read()
        raise


def latest(api, repo, token, current):
    """Daha yeni panel sürümü varsa {"version", "tag", "notes", "exe_api", "sums_api"} döner, yoksa None."""
    rels = json.loads(_open(f"{api.rstrip('/')}/repos/{repo}/releases?per_page=30", token))
    best = None
    for r in rels:
        m = TAG_RE.match(r.get("tag_name", ""))
        if not m or r.get("draft"): continue
        v = tuple(int(x) for x in m.groups())
        assets = {a["name"]: a for a in r.get("assets", [])}
        if EXE not in assets or SUMS not in assets: continue
        if v > vtuple(current) and (best is None or v > best[0]):
            best = (v, r, assets)
    if not best: return None
    v, r, a = best
    return {"version": ".".join(map(str, v)), "tag": r["tag_name"], "notes": r.get("body") or "",
            "exe_api": a[EXE]["url"], "sums_api": a[SUMS]["url"], "size": a[EXE].get("size", 0)}


def expected_sha(sums_text, name=EXE):
    for line in sums_text.splitlines():
        parts = line.strip().split()
        if len(parts) == 2 and parts[1].lstrip("*") == name and re.fullmatch(r"[0-9a-f]{64}", parts[0].lower()):
            return parts[0].lower()
    return None


def download(info, token):
    """(exe baytları) — özet doğrulanmadan dönmez."""
    sums = _open(info["sums_api"], token, accept="application/octet-stream").decode("utf-8", "replace")
    want = expected_sha(sums)
    if not want: raise RuntimeError("SHA256SUMS içinde panel özeti yok")
    data = _open(info["exe_api"], token, accept="application/octet-stream", timeout=120)
    got = hashlib.sha256(data).hexdigest()
    if got != want: raise RuntimeError("SHA-256 tutmadı — güncelleme kurulmadı")
    if info.get("size") and len(data) != info["size"]: raise RuntimeError("boyut tutmadı")
    return data


def install(data, exe_path=None, relaunch=True):
    """Yeni exe'yi yerine koyar; başarılıysa True (çağıran kapanmalı)."""
    exe = Path(exe_path or sys.executable)
    if exe.name.lower() != EXE.lower(): raise RuntimeError("derlenmiş panel değil")
    new, old = exe.with_name(exe.name + ".new"), exe.with_name(exe.name + ".old")
    new.write_bytes(data)
    try:
        if old.exists(): old.unlink()
    except OSError:
        pass
    os.replace(exe, old)
    try:
        os.replace(new, exe)
    except OSError:
        os.replace(old, exe)               # geri al
        raise
    if relaunch:
        subprocess.Popen([str(exe)], close_fds=True, creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    return True


def cleanup(exe_path=None):
    exe = Path(exe_path or sys.executable)
    for suffix in (".old", ".new"):
        p = exe.with_name(exe.name + suffix)
        try:
            if p.exists(): p.unlink()
        except OSError:
            pass

