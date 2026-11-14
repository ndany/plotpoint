#!/usr/bin/env python3
"""Check every SKILL.md for portable Agent Skills frontmatter.

Rules (see docs/decisions.md D-7):
- Frontmatter block present, delimited by '---' lines.
- Only standard fields: name, description, license, compatibility, metadata,
  allowed-tools. Anything else breaks Claude.ai upload.
- `name` is present, lowercase letters/digits/hyphens, at most 64 characters,
  and equals the skill's folder name.
- `description` is present, at most 1024 characters, with no angle brackets.

Usage: scripts/check_frontmatter.py [ROOT]   (ROOT defaults to the repo root)
Exit code 0 when all skills pass, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ALLOWED_FIELDS = frozenset(
    {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
)
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024


def parse_frontmatter(text: str) -> dict | None:
    """Return the frontmatter mapping, or None if the block is missing."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for end, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            data = yaml.safe_load("\n".join(lines[1:end])) or {}
            return data if isinstance(data, dict) else None
    return None


def check_skill(skill_md: Path) -> list[str]:
    """Return a list of problems for one SKILL.md (empty when it passes)."""
    folder = skill_md.parent.name
    try:
        meta = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"invalid YAML frontmatter: {exc}"]
    if meta is None:
        return ["missing frontmatter block delimited by '---'"]

    problems = []
    extra = sorted(set(meta) - ALLOWED_FIELDS)
    if extra:
        problems.append(f"non-standard fields: {', '.join(extra)}")

    name = meta.get("name")
    if not isinstance(name, str) or not name:
        problems.append("missing 'name'")
    else:
        if not NAME_PATTERN.match(name) or len(name) > MAX_NAME:
            problems.append(
                f"'name' must be lowercase letters, digits and hyphens, "
                f"max {MAX_NAME} chars: {name!r}"
            )
        if name != folder:
            problems.append(f"'name' {name!r} does not match folder {folder!r}")

    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        problems.append("missing 'description'")
    else:
        if len(description) > MAX_DESCRIPTION:
            problems.append(
                f"'description' is {len(description)} chars (max {MAX_DESCRIPTION})"
            )
        if "<" in description or ">" in description:
            problems.append("'description' must not contain angle brackets")

    return problems


def find_skills(root: Path) -> list[Path]:
    return sorted(root.glob("plugins/*/skills/*/SKILL.md"))


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    skills = find_skills(root)
    if not skills:
        print(f"no SKILL.md files found under {root}/plugins/*/skills/")
        return 1

    failed = False
    for skill_md in skills:
        rel = skill_md.relative_to(root)
        problems = check_skill(skill_md)
        if problems:
            failed = True
            for problem in problems:
                print(f"FAIL {rel}: {problem}")
        else:
            print(f"ok   {rel}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
