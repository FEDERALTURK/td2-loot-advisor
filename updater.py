"""GitHub Releases üzerinden kendini güncelleme.

- Kurulumla yüklenmiş (.exe):  yeni kurulum dosyası indirilir, SHA-256 doğrulanır, sessiz kurulur, program yeniden açılır.
  Ayarlar / build'ler / sandık kurulum klasöründe ayrı dosyalardır, kurulum onlara dokunmaz.
- Kaynaktan (run.bat):  sürümün kaynak arşivi indirilir, YALNIZ program dosyaları yenilenir
  (kişisel dosyalar: builds.json, stash.json, progress.json, private/, logs/ … hiçbir zaman değiştirilmez).

    info = latest()                    # {"version", "tag", "notes", "url", "setup", "setup_sha", "zipball"}
    newer(info["version"], "5.0")      # True / False
"""
import base64
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
from urllib.parse import urlsplit
import zipfile
from pathlib import Path, PurePosixPath

log = logging.getLogger("td2.update")

REPO = "FEDERALTURK/td2-loot-advisor"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases?per_page=100"
UA = {"User-Agent": "TD2-Loot-Advisor-updater", "Accept": "application/vnd.github+json"}

# Kaynak güncellemesinde yenilenebilecek yollar (beyaz liste). Bunların dışındaki hiçbir dosyaya dokunulmaz.
SOURCE_ALLOW = [r"[^/]+\.py", r"lang/[^/]+\.json", r"meta/(game_data|meta_builds|tasks_feed)\.json", r"meta/[^/]+\.md",
                r"art/(agents|backgrounds|branding)/[^/]+\.(png|jpg|webp)",
                r"scripts/[^/]+", r"icon/[^/]+", r"server/[^/]+", r"tests/[^/]+(/[^/]+)?",
                r"requirements[^/]*\.txt", r"README[^/]*\.md", r"LICENSE"]
# Hiçbir koşulda yazılmaz (beyaz listeye uysa bile)
# Kullanıcıya/cihaza ait durum verileri kaynak güncellemesinde hiçbir koşulda
# değiştirilemez. SOURCE_ALLOW bugün bu kök JSON dosyalarının çoğunu zaten
# kapsamıyor; yine de bu liste savunma katmanıdır ve ileride izin listesi
# genişletilirse kişisel oturum/öğrenilmiş ekran verisini korur.
NEVER = {
    "builds.json", "stash.json", "progress.json", "tasks.json", "loot_log.csv",
    "drop_queue.json", "learned_library.json", "sessions.json", "screen_states.json",
    "tasks_sent.json", "verdict_feedback.json", "verdict_feedback.json.tmp",
}


def parse_version(v):
    nums = re.findall(r"\d+", str(v or ""))
    return tuple(int(n) for n in nums[:4]) or (0,)


def newer(remote, local):
    r, l = parse_version(remote), parse_version(local)
    n = max(len(r), len(l))
    return r + (0,) * (n - len(r)) > l + (0,) * (n - len(l))


def _get(url, timeout=15, binary=False, progress=None):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.build_opener(_GitHubRedirectHandler()).open(req, timeout=timeout) as r:
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


def _release_info(d):
    assets = {a["name"]: a["browser_download_url"] for a in d.get("assets", [])}
    version = d.get("tag_name", "").lstrip("vV")
    setup = next((u for n, u in assets.items() if n.lower().startswith("td2lootadvisor_setup") and n.lower().endswith(".exe")), None)
    sha_url = assets.get("SHA256SUMS.sha256")
    source_url = assets.get(f"TD2LootAdvisor_{version}_source.zip") or d.get("zipball_url")
    return {"version": version, "tag": d.get("tag_name", ""), "name": d.get("name", ""),
            "notes": d.get("body", "") or "", "url": d.get("html_url", ""), "setup": setup, "sha_url": sha_url,
            "manifest_url": assets.get("TD2_RELEASE_MANIFEST.json"),
            "signature_url": assets.get("TD2_RELEASE_MANIFEST.sig"),
            "zipball": source_url, "published": d.get("published_at", "")}


def latest(timeout=10):
    """En son kararlı yayın bilgisi (beta/önizleme sürümleri hariç)."""
    return _release_info(_get(API, timeout))


def latest_beta(timeout=10):
    """Kullanıcı açıkça isterse sunulacak en yeni beta sürümü."""
    releases = _get(RELEASES_API, timeout)
    if not isinstance(releases, list): return None
    for d in releases:
        tag = str(d.get("tag_name", ""))
        if d.get("prerelease") and "-beta" in tag.lower():
            return _release_info(d)
    return None


def releases(timeout=10, limit=30):
    """Yayın geçmişini döndürür; geri dönüş seçicisi için yalnızca GitHub Releases kullanılır."""
    raw = _get(RELEASES_API, timeout)
    if not isinstance(raw, list): return []
    out = []
    for d in raw[:max(1, int(limit))]:
        tag = str(d.get("tag_name", ""))
        # Teknik/yardımcı release kayıtlarını (ör. mt-models) kullanıcı seçimine açma.
        if d.get("draft") or not re.fullmatch(r"v?\d+(?:\.\d+)+(?:-beta\.\d+)?", tag, re.I): continue
        item = _release_info(d)
        if not item.get("setup") and not item.get("zipball"): continue
        item["prerelease"] = bool(d.get("prerelease"))
        out.append(item)
    return out


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
RELEASE_SIGNING_PUBLIC_KEY_B64 = "5Z04nYptfFg2o8iaOzj3k07YSKmQdnreaozKp0PzEAI="
SIGNED_RELEASES_FROM = "9.1.5.53"
_RELEASE_TAG = re.compile(r"v?\d+(?:\.\d+)+(?:-beta\.\d+)?", re.I)
_INSTALLER_NAME = re.compile(r"TD2LootAdvisor_Setup_[0-9]+(?:\.[0-9]+)*(?:-beta\.[0-9]+)?\.exe", re.I)


_GITHUB_REDIRECT_HOSTS = {
    "api.github.com", "github.com", "codeload.github.com",
    "objects.githubusercontent.com", "release-assets.githubusercontent.com",
}


class _GitHubRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            parsed = urlsplit(newurl)
            trusted = (parsed.scheme == "https" and parsed.hostname in _GITHUB_REDIRECT_HOSTS
                       and parsed.username is None and parsed.password is None and parsed.port is None)
        except ValueError:
            trusted = False
        if not trusted:
            raise urllib.error.HTTPError(req.full_url, code, "untrusted GitHub download redirect", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _release_path(url, tag, filename):
    """Accept only an exact asset URL for this repository and release tag."""
    tag = str(tag or "")
    if not _RELEASE_TAG.fullmatch(tag): return False
    try:
        parsed = urlsplit(str(url or ""))
    except ValueError:
        return False
    expected = f"/{REPO}/releases/download/{tag}/{filename}"
    return (parsed.scheme == "https" and parsed.netloc == "github.com"
            and not parsed.query and not parsed.fragment and parsed.path == expected)


def _signature_required(info):
    return not newer(SIGNED_RELEASES_FROM, info.get("version", ""))


def _verified_release_manifest(info):
    tag, version = str(info.get("tag") or ""), str(info.get("version") or "")
    if (not _release_path(info.get("manifest_url"), tag, "TD2_RELEASE_MANIFEST.json")
            or not _release_path(info.get("signature_url"), tag, "TD2_RELEASE_MANIFEST.sig")):
        raise RuntimeError("signed release manifest is missing or has an unexpected location")
    try:
        raw = _get(info["manifest_url"], timeout=20, binary=True)
        signature = base64.b64decode(_get(info["signature_url"], timeout=20, binary=True).strip(), validate=True)
        manifest = json.loads(raw.decode("utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest root must be an object")
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        if raw != canonical:
            raise ValueError("manifest is not canonical JSON")
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        public_key = base64.b64decode(RELEASE_SIGNING_PUBLIC_KEY_B64, validate=True)
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, raw)
    except Exception as exc:
        raise RuntimeError("release manifest signature is invalid") from exc
    if (not isinstance(manifest, dict) or manifest.get("schema") != 1
            or manifest.get("repository") != REPO or manifest.get("tag") != tag
            or manifest.get("version") != version):
        raise RuntimeError("signed release manifest metadata does not match this release")
    assets = manifest.get("assets")
    source = manifest.get("source_zipball")
    if (not isinstance(assets, dict)
            or any(Path(name).name != name or not isinstance(digest, str)
                   or not re.fullmatch(r"[0-9a-f]{64}", digest) for name, digest in assets.items())
            or not isinstance(source, dict) or source.get("url") != info.get("zipball")
            or not isinstance(source.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"])):
        raise RuntimeError("signed release manifest contains invalid asset checksums")
    return manifest


def install_frozen(info, progress=None):
    """Kurulum dosyasını indir, doğrula, sessiz kurulumu başlat. Çağıran program hemen kapanmalı.
    Doğrulama zorunludur: dosya bu deponun sürümünden gelmeli ve SHA256SUMS'taki özetle eşleşmeli (yoksa kurulmaz).
    Dönüş: indirilen dosyanın yolu. Hata durumunda istisna."""
    if not info.get("setup"): raise RuntimeError("release has no installer asset")
    tag = str(info.get("tag") or "")
    version = str(info.get("version") or "")
    if not _RELEASE_TAG.fullmatch(tag) or version.lower() != tag.lstrip("vV").lower():
        raise RuntimeError("release tag and version do not match — not installing")
    name = info["setup"].rsplit("/", 1)[-1]
    match = _INSTALLER_NAME.fullmatch(name)
    if not match or name[len("TD2LootAdvisor_Setup_"):-4].lower() != version.lower():
        raise RuntimeError("installer name and release version do not match")
    if not _release_path(info["setup"], tag, name) or not _release_path(info.get("sha_url"), tag, "SHA256SUMS.sha256"):
        raise RuntimeError("unexpected release asset location — not installing")
    if _signature_required(info):
        want = _verified_release_manifest(info).get("assets", {}).get(name)
        if not isinstance(want, str) or not re.fullmatch(r"[0-9a-f]{64}", want):
            raise RuntimeError("signed manifest has no valid installer checksum")
    else:
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
    if rel in NEVER or rel.split("/", 1)[0] in ("private", "logs", "reports", "cache", "build", "dist", "installer"):
        return False
    return any(re.fullmatch(p, rel) for p in SOURCE_ALLOW)


def update_source(info, base, progress=None):
    """Kaynak arşivinden program dosyalarını yenile. Eski dosyalar backup/<tarih>/ altına kopyalanır.
    Dönüş: (değişen dosya sayısı, yedek klasörü)."""
    base = Path(base)
    tag = str(info.get("tag") or "")
    if not _RELEASE_TAG.fullmatch(tag):
        raise RuntimeError("invalid release tag — source update refused")
    signed = _signature_required(info)
    if signed:
        source_name = f"TD2LootAdvisor_{info.get('version')}_source.zip"
        if not _release_path(info.get("zipball"), tag, source_name):
            raise RuntimeError("signed source archive is missing or has an unexpected location")
        source = _verified_release_manifest(info).get("source_zipball")
        if not isinstance(source, dict) or source.get("url") != info["zipball"]:
            raise RuntimeError("signed manifest does not cover this source archive")
        want = source.get("sha256")
        if not isinstance(want, str) or not re.fullmatch(r"[0-9a-f]{64}", want):
            raise RuntimeError("signed manifest has no valid source archive checksum")
    else:
        parsed = urlsplit(str(info.get("zipball") or ""))
        expected_zipball = f"/repos/{REPO}/zipball/{tag}"
        if (parsed.scheme != "https" or parsed.netloc != "api.github.com"
                or parsed.path != expected_zipball or parsed.query or parsed.fragment):
            raise RuntimeError("unexpected source archive location — update refused")
        want = None
    data = _get(info["zipball"], timeout=60, binary=True, progress=progress)
    if want and hashlib.sha256(data).hexdigest() != want:
        raise RuntimeError("source archive SHA-256 mismatch — update refused")
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
