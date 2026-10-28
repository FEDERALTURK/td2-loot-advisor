"""Yayıncı aracı: premium lisans anahtarı üretir. (Yalnız proje sahibi kullanır.)

    python scripts/license_tool.py init                       # bir kez: anahtar çifti üret (private/license_seed.hex)
    python scripts/license_tool.py issue --name "Ali" --days 30
    python scripts/license_tool.py issue --name "Ayşe" --days 0   # süresiz
    python scripts/license_tool.py check TD2P-....

private/license_seed.hex GİZLİDİR: depoya girmez (.gitignore), kimseyle paylaşma, yedeğini al.
Kaybolursa yeni çift üretilir ve eski anahtarların hepsi geçersiz olur.
"""
import argparse, os, re, secrets, sys, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import features  # noqa: E402

SEED = ROOT / "private" / "license_seed.hex"


def load_seed():
    if not SEED.exists():
        sys.exit("private/license_seed.hex yok — önce: python scripts/license_tool.py init")
    return bytes.fromhex(SEED.read_text().strip())


def cmd_init(a):
    if SEED.exists() and not a.force:
        sys.exit("Anahtar zaten var (private/license_seed.hex). Yenisi eski lisansları geçersiz kılar: --force")
    seed = secrets.token_bytes(32)
    SEED.parent.mkdir(exist_ok=True)
    SEED.write_text(seed.hex())
    pub = features.public_key(seed).hex()
    f = ROOT / "features.py"
    s = f.read_text(encoding="utf-8")
    s = re.sub(r'PUBLIC_KEY_HEX = "[0-9a-f]*"', f'PUBLIC_KEY_HEX = "{pub}"', s)
    f.write_text(s, encoding="utf-8")
    print("Gizli anahtar:", SEED, "(YEDEKLE, PAYLAŞMA)")
    print("Açık anahtar features.py'ye yazıldı:", pub)


def cmd_issue(a):
    seed = load_seed()
    now = int(time.time())
    payload = {"id": a.id or uuid.uuid4().hex[:12], "name": a.name, "tier": a.tier, "iat": now}
    if a.days and a.days > 0: payload["exp"] = now + a.days * 86400
    key = features.make_key(seed, payload)
    ok, _, why = features.check_key(key, features.public_key(seed).hex())
    assert ok, why
    print(key)


def cmd_check(a):
    ok, payload, why = features.check_key(a.key)
    print(why, payload)


p = argparse.ArgumentParser()
sp = p.add_subparsers(dest="cmd", required=True)
i = sp.add_parser("init"); i.add_argument("--force", action="store_true"); i.set_defaults(fn=cmd_init)
s = sp.add_parser("issue"); s.add_argument("--name", required=True); s.add_argument("--days", type=int, default=30)
s.add_argument("--tier", default="premium", choices=features.TIERS); s.add_argument("--id", default="")
s.set_defaults(fn=cmd_issue)
c = sp.add_parser("check"); c.add_argument("key"); c.set_defaults(fn=cmd_check)
a = p.parse_args(); a.fn(a)
