"""GitHub Releases üzerinden kendini güncelleme.

- Kurulumla yüklenmiş (.exe):  yeni kurulum dosyası indirilir, SHA-256 doğrulanır, sessiz kurulur, program yeniden açılır.
  Ayarlar / build'ler / sandık kurulum klasöründe ayrı dosyalardır, kurulum onlara dokunmaz.
- Kaynaktan (run.bat):  sürümün kaynak arşivi indirilir, YALNIZ program dosyaları yenilenir
  (kişisel dosyalar: builds.json, stash.json, progress.json, private/, logs/ … hiçbir zaman değiştirilmez).

    info = latest()                    # {"version", "tag", "notes", "url", "setup", "setup_sha", "zipball"}
    newer(info["version"], "5.0")      # True / False
"""
import hashlib
import io
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

log = logging.getLogger("td2.update")

REPO = "FEDERALTURK/td2-loot-advisor"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
UA = {"User-Agent": "TD2-Loot-Advisor-updater", "Accept": "application/vnd.github+json"}

# Kaynak güncellemesinde yenilenebilecek yollar (beyaz liste). Bunların dışındaki hiçbir dosyaya dokunulmaz.
SOURCE_ALLOW = [r"[^/]+\.py", r"lang/[^/]+\.json", r"meta/(game_data|meta_builds|tasks_feed)\.json", r"meta/[^/]+\.md",
                r"scripts/[^/]+", r"icon/[^/]+", r"server/[^/]+", r"tests/[^/]+(/[^/]+)?",
                r"requirements[^/]*\.txt", r"README[^/]*\.md", r"LICENSE"]
# Hiçbir koşulda yazılmaz (beyaz listeye uysa bile)
NEVER = {"builds.json", "stash.json", "progress.json", "tasks.json", "loot_log.csv", "drop_queue.json", "learned_library.json"}


def parse_version(v):
    nums = re.findall(r"\d+", str(v or ""))
    return tuple(int(n) for n in nums[:4]) or (0,)


def newer(remote, local):
    r, l = parse_version(remote), parse_version(local)
    n = max(len(r), len(l))
    return r + (0,) * (n - len(r)) > l + (0,) * (n - len(l))


def _get(url, timeout=15, binary=False, progress=None):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if not binary:
            return json.loads(r.read().decode("utf-8"))
        total = int(r.headers.get("Content-Length") or 0)
        buf, got = io.BytesIO(), 0
        while True:
            chunk = r.read(256 * 1024)
            if not chunk: break
            buf.write(chunk); got += len(chunk)
            if progress and total: progress(got / total)
        return buf.getvalue()


def latest(timeout=10):
    """En son yayınlanmış sürüm bilgisi (ağ gerektirir)."""
    d = _get(API, timeout)
    assets = {a["name"]: a["browser_download_url"] for a in d.get("assets", [])}
    setup = next((u for n, u in assets.items() if n.lower().startswith("td2lootadvisor_setup") and n.lower().endswith(".exe")), None)
    sha_url = next((u for n, u in assets.items() if n.lower().endswith(".sha256")), None)
    return {"version": d.get("tag_name", "").lstrip("vV"), "tag": d.get("tag_name", ""), "name": d.get("name", ""),
            "notes": d.get("body", "") or "", "url": d.get("html_url", ""), "setup": setup, "sha_url": sha_url,
            "zipball": d.get("zipball_url"), "published": d.get("published_at", "")}


def _expected_sha(info, filename):
    if not info.get("sha_url"): return None
    try:
        txt = _get(info["sha_url"], binary=True).decode("utf-8", "replace")
    except Exception:
        return None
    for line in txt.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == filename and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]): return parts[0].lower()
    return None


DOWNLOAD_PREFIX = f"https://github.com/{REPO}/releases/download/"


def install_frozen(info, progress=None):
    """Kurulum dosyasını indir, doğrula, sessiz kurulumu başlat. Çağıran program hemen kapanmalı.
    Doğrulama zorunludur: dosya bu deponun sürümünden gelmeli ve SHA256SUMS'taki özetle eşleşmeli (yoksa kurulmaz).
    Dönüş: indirilen dosyanın yolu. Hata durumunda istisna."""
    if not info.get("setup"): raise RuntimeError("release has no installer asset")
    for k in ("setup", "sha_url"):
        if not str(info.get(k) or "").startswith(DOWNLOAD_PREFIX):
            raise RuntimeError("unexpected download location — not installing")
    name = info["setup"].rsplit("/", 1)[-1]
    if not re.fullmatch(r"TD2LootAdvisor_Setup_[0-9.]+\.exe", name, re.I): raise RuntimeError("unexpected installer name")
    want = _expected_sha(info, name)
    if not want: raise RuntimeError("no checksum published for the installer — not installing")
    data = _get(info["setup"], timeout=60, binary=True, progress=progress)
    got = hashlib.sha256(data).hexdigest()
    if want != got: raise RuntimeError("SHA-256 mismatch — download corrupted, not installing")
    path = Path(tempfile.mkdtemp(prefix="td2upd-")) / name     # her seferinde yeni, yalnız bu kullanıcının klasörü
    path.write_bytes(data)
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    # /SILENT: ilerleme penceresi görünür ama soru sorulmaz; kurulum bitince program kendini yeniden açar ([Run] ShouldRelaunch, /RELAUNCH=1)
    subprocess.Popen([str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS", "/RELAUNCH=1"],
                     creationflags=flags, close_fds=True)
    log.info("Update: started installer %s (sha %s, verified)", name, got[:12])
    return path


def _allowed(rel):
    if rel in NEVER or rel.split("/", 1)[0] in ("private", "logs", "reports", "cache", "art", "build", "dist", "installer"):
        return False
    return any(re.fullmatch(p, rel) for p in SOURCE_ALLOW)


def update_source(info, base, progress=None):
    """Kaynak arşivinden program dosyalarını yenile. Eski dosyalar backup/<tarih>/ altına kopyalanır.
    Dönüş: (değişen dosya sayısı, yedek klasörü)."""
    base = Path(base)
    data = _get(info["zipball"], timeout=60, binary=True, progress=progress)
    zf = zipfile.ZipFile(io.BytesIO(data))
    backup = base / "backup" / time.strftime("%Y%m%d_%H%M%S")
    changed = 0
    for zi in zf.infolist():
        if zi.is_dir(): continue
        parts = PurePosixPath(zi.filename).parts
        if len(parts) < 2: continue
        rel = "/".join(parts[1:])                       # ilk klasör: <owner>-<repo>-<sha>/
        if ".." in parts or not _allowed(rel): continue
        new = zf.read(zi)
        dst = base / rel
        if dst.exists() and dst.read_bytes() == new: continue
        if dst.exists():
            (backup / rel).parent.mkdir(parents=True, exist_ok=True)
            (backup / rel).write_bytes(dst.read_bytes())
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.name + ".new")
        tmp.write_bytes(new); os.replace(tmp, dst)
        changed += 1
    log.info("Update: source updated to %s, %d files changed (backup %s)", info.get("tag"), changed, backup)
    return changed, (backup if changed else None)


def restart_source():
    """Kaynaktan çalışan programı yeniden başlat."""
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    exe = sys.executable
    if os.name == "nt" and exe.lower().endswith("python.exe"):
        w = exe[:-10] + "pythonw.exe"
        if os.path.exists(w): exe = w
    subprocess.Popen([exe, os.path.abspath(sys.argv[0])], creationflags=flags, close_fds=True,
                     cwd=os.path.dirname(os.path.abspath(sys.argv[0])))
