"""Validate project skill definitions under ``.agents/skills``.

Checks every skill directory for a ``SKILL.md`` with YAML frontmatter that
declares a non-empty ``name`` matching the directory and a usable
``description``. Exit code is ``1`` when any skill is invalid.

Usage:
    python -B scripts/validate_skills.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".agents" / "skills"
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
# Anthropic'in resmi becerileri 1024 karakteri asabiliyor (or. claude-api).
# DSH belgelenmis bir ust sinir yayinlamadigi icin sinir 2048 tutuluyor.
MAX_DESCRIPTION = 2048


def _load_yaml(text: str) -> dict[str, str]:
    """Parse the small YAML subset used by SKILL.md frontmatter."""
    try:
        import yaml  # type: ignore[import-not-found]

        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except ImportError:
        pass

    result: dict[str, str] = {}
    key: str | None = None
    block: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if match and not line.startswith((" ", "\t")):
            if key is not None:
                result[key] = " ".join(block).strip()
                block = []
            key = match.group(1)
            value = match.group(2).strip()
            if value in (">", "|", ">-", "|-"):
                block = []
            else:
                result[key] = value.strip("'\"")
                key = None
        elif key is not None:
            block.append(line.strip())
    if key is not None:
        result[key] = " ".join(block).strip()
    return result


def validate_skill(skill_dir: Path) -> list[str]:
    """Return a list of problems for one skill directory."""
    problems: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [f"{skill_dir.name}: SKILL.md bulunamadi"]

    try:
        text = skill_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{skill_dir.name}: SKILL.md UTF-8 degil"]

    match = FRONTMATTER_RE.match(text)
    if not match:
        return [f"{skill_dir.name}: YAML frontmatter yok"]

    data = _load_yaml(match.group(1))
    name = str(data.get("name") or "").strip()
    description = " ".join(str(data.get("description") or "").split())

    if not name:
        problems.append(f"{skill_dir.name}: 'name' alani bos")
    elif name != skill_dir.name:
        problems.append(f"{skill_dir.name}: name '{name}' klasor adiyla eslesmiyor")

    if not description:
        problems.append(f"{skill_dir.name}: 'description' alani bos")
    elif len(description) > MAX_DESCRIPTION:
        problems.append(
            f"{skill_dir.name}: description {len(description)} karakter "
            f"(> {MAX_DESCRIPTION})"
        )
    return problems


def main() -> int:
    """Validate all skills and report the outcome."""
    if not SKILLS_DIR.is_dir():
        print(f"HATA: {SKILLS_DIR} bulunamadi")
        return 1

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print(f"HATA: {SKILLS_DIR} altinda beceri yok")
        return 1

    problems: list[str] = []
    seen: dict[str, Path] = {}
    for skill_dir in skill_dirs:
        if skill_dir.name.startswith("."):
            continue
        problems.extend(validate_skill(skill_dir))
        if skill_dir.name in seen:
            problems.append(f"{skill_dir.name}: yinelenen beceri adi")
        seen[skill_dir.name] = skill_dir

    for problem in problems:
        print(f"[HATA] {problem}")

    print(f"{len(skill_dirs)} beceri denetlendi, {len(problems)} sorun bulundu.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
