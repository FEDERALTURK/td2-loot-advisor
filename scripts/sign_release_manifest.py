"""Sign release metadata without exposing the private key in workflow logs."""
import argparse
import base64
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import updater


def signed_manifest(tag, version, checksum_file, source_url, source_data, private_key):
    checksums = {}
    for line in Path(checksum_file).read_text(encoding="ascii").splitlines():
        fields = line.strip().split()
        if len(fields) < 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", fields[0]):
            raise ValueError("checksum file contains an invalid row")
        name = fields[-1].lstrip("*")
        if Path(name).name != name:
            raise ValueError("checksum file contains an invalid asset name")
        checksums[name] = fields[0].lower()
    installer = f"TD2LootAdvisor_Setup_{version}.exe"
    if installer not in checksums:
        raise ValueError("release checksum file does not contain the installer")
    manifest = {
        "schema": 1,
        "repository": updater.REPO,
        "tag": tag,
        "version": version,
        "assets": checksums,
        "source_zipball": {"url": source_url, "sha256": hashlib.sha256(source_data).hexdigest()},
    }
    body = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return body, base64.b64encode(private_key.sign(body)) + b"\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--installer-dir", default="installer")
    args = parser.parse_args()
    if not re.fullmatch(r"v?\d+(?:\.\d+)+(?:-beta\.\d+)?", args.tag, re.I):
        parser.error("invalid release tag")
    if args.version.lower() != args.tag.lstrip("vV").lower():
        parser.error("release tag and version do not match")
    key_value = os.environ.get("TD2_RELEASE_SIGNING_KEY_BASE64", "")
    if not key_value:
        parser.error("TD2_RELEASE_SIGNING_KEY_BASE64 secret is required for a release")

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    try:
        key_bytes = base64.b64decode(key_value, validate=True)
        private_key = serialization.load_pem_private_key(key_bytes, password=None)
    except Exception as exc:
        parser.error(f"release signing key is invalid ({type(exc).__name__})")
    if not isinstance(private_key, Ed25519PrivateKey):
        parser.error("release signing key must be Ed25519")

    out = Path(args.installer_dir)
    source_name = f"TD2LootAdvisor_{args.version}_source.zip"
    source_path = out / source_name
    if source_name not in {line.split()[-1].lstrip("*") for line in (out / "SHA256SUMS.sha256").read_text(encoding="ascii").splitlines() if line.split()}:
        parser.error("release checksum file does not contain the source archive")
    if not source_path.is_file():
        parser.error("release source archive is missing")
    source_url = f"https://github.com/{updater.REPO}/releases/download/{args.tag}/{source_name}"
    source_data = source_path.read_bytes()
    try:
        body, signature = signed_manifest(args.tag, args.version, out / "SHA256SUMS.sha256",
                                          source_url, source_data, private_key)
    except ValueError as exc:
        parser.error(str(exc))
    (out / "TD2_RELEASE_MANIFEST.json").write_bytes(body)
    (out / "TD2_RELEASE_MANIFEST.sig").write_bytes(signature)
    print("Signed release manifest created; private key was not written or logged.")


if __name__ == "__main__":
    main()
