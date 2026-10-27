"""Fast source launcher: check module presence without importing large models.

Normal launches do not contact pip when requirements are unchanged and present.
--extras installs optional voice/video packages; --repair rechecks requirements.
--check reports missing required modules without installing or starting the app.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

CORE = ("mss", "PIL", "pytesseract", "pynput", "pystray", "ctranslate2", "sentencepiece", "soundcard")
OCR = (("onnxruntime", "onnxruntime"), ("rapidocr", "rapidocr"))
EXTRAS = (("pyttsx3", "pyttsx3"), ("sounddevice", "sounddevice"), ("numpy", "numpy"),
          ("faster-whisper", "faster_whisper"), ("qrcode", "qrcode"), ("av", "av"))


def present(module, finder=None):
    try: return (finder or importlib.util.find_spec)(module) is not None
    except (ImportError, ValueError, AttributeError): return False


def prepare(root, repair=False, extras=False, check_only=False, finder=None, runner=None):
    root = Path(root); runner = runner or subprocess.run
    missing = [module for module in CORE if not present(module, finder)]
    if check_only: return not missing, missing
    req = root / "requirements.txt"
    digest = hashlib.sha256(req.read_bytes()).hexdigest()
    state_path = root / "cache" / "bootstrap.json"
    try: state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError): state = {}
    if not isinstance(state, dict): state = {}
    same_python = state.get("python") == sys.executable and state.get("version") == list(sys.version_info[:3])
    changed = state.get("requirements") not in (None, digest)

    def pip(args):
        result = runner([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *args], cwd=str(root))
        return result.returncode == 0

    if missing or changed or repair:
        if not pip(["-r", str(req)]): return False, missing
        missing = [module for module in CORE if not present(module, finder)]
        if missing: return False, missing
    # The recommended OCR engine is small compared with optional speech/video.
    # Never replace an existing DirectML installation with the CPU distribution.
    if repair or not same_python or not state.get("ocr_checked"):
        needed = [package for package, module in OCR if not present(module, finder)]
        if needed: pip(needed)           # Tesseract remains available if optional OCR install fails.
    if extras:
        needed = [package for package, module in EXTRAS if not present(module, finder)]
        if needed: pip(needed)
    state = {"python": sys.executable, "version": list(sys.version_info[:3]), "requirements": digest, "ocr_checked": True}
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8"); tmp.replace(state_path)
    except OSError:
        pass                           # Read-only source folder can still launch.
    return True, []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--extras", action="store_true")
    parser.add_argument("--check", action="store_true")
    args, app_args = parser.parse_known_args()
    root = Path(__file__).resolve().parents[1]
    ok, missing = prepare(root, args.repair, args.extras, args.check)
    if not ok:
        print("Required packages missing / Gerekli paketler eksik:", ", ".join(missing))
        return 1
    if args.check:
        print("Required packages ready / Gerekli paketler hazir")
        return 0
    return subprocess.call([sys.executable, str(root / "app.py"), *app_args], cwd=str(root))


if __name__ == "__main__": sys.exit(main())
