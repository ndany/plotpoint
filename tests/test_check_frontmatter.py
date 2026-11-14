"""Tests for scripts/check_frontmatter.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "check_frontmatter.py"

spec = importlib.util.spec_from_file_location("check_frontmatter", SCRIPT)
cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf)


def make_skill(root: Path, folder: str, frontmatter: str) -> Path:
    skill_dir = root / "plugins" / "demo" / "skills" / folder
    skill_dir.mkdir(parents=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(f"---\n{frontmatter}\n---\n\n# Body\n", encoding="utf-8")
    return skill_md


def test_valid_skill_passes(tmp_path: Path) -> None:
    md = make_skill(
        tmp_path, "demo", "name: demo\ndescription: Does a thing.\nlicense: Apache-2.0"
    )
    assert cf.check_skill(md) == []


def test_non_standard_field_rejected(tmp_path: Path) -> None:
    md = make_skill(
        tmp_path, "demo", "name: demo\ndescription: Does a thing.\nargument-hint: x"
    )
    assert any("non-standard fields: argument-hint" in p for p in cf.check_skill(md))


def test_name_folder_mismatch_rejected(tmp_path: Path) -> None:
    md = make_skill(tmp_path, "demo", "name: other\ndescription: Does a thing.")
    assert any("does not match folder" in p for p in cf.check_skill(md))


@pytest.mark.parametrize("bad_name", ["Demo", "demo_skill", "-demo", "a" * 65])
def test_bad_name_format_rejected(tmp_path: Path, bad_name: str) -> None:
    md = make_skill(tmp_path, "demo", f"name: {bad_name}\ndescription: Does a thing.")
    assert any("lowercase letters" in p for p in cf.check_skill(md))


def test_missing_description_rejected(tmp_path: Path) -> None:
    md = make_skill(tmp_path, "demo", "name: demo")
    assert "missing 'description'" in cf.check_skill(md)


def test_long_description_rejected(tmp_path: Path) -> None:
    md = make_skill(tmp_path, "demo", f"name: demo\ndescription: {'x' * 1025}")
    assert any("max 1024" in p for p in cf.check_skill(md))


def test_angle_brackets_rejected(tmp_path: Path) -> None:
    md = make_skill(tmp_path, "demo", "name: demo\ndescription: Use for <charts>.")
    assert any("angle brackets" in p for p in cf.check_skill(md))


def test_missing_frontmatter_rejected(tmp_path: Path) -> None:
    skill_dir = tmp_path / "plugins" / "demo" / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    md = skill_dir / "SKILL.md"
    md.write_text("# No frontmatter\n", encoding="utf-8")
    assert cf.check_skill(md) == ["missing frontmatter block delimited by '---'"]


def test_cli_exit_codes(tmp_path: Path) -> None:
    make_skill(tmp_path, "demo", "name: demo\ndescription: Does a thing.")
    ok = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path)], check=False)
    assert ok.returncode == 0

    make_skill(tmp_path, "broken", "name: wrong\ndescription: Does a thing.")
    bad = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path)], check=False)
    assert bad.returncode == 1


def test_cli_fails_when_no_skills(tmp_path: Path) -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path)], check=False)
    assert result.returncode == 1


def test_repo_skills_pass() -> None:
    """Non-regression: every skill in this repo has portable frontmatter."""
    skills = cf.find_skills(REPO)
    assert skills, "expected at least one skill in the repo"
    for md in skills:
        assert cf.check_skill(md) == [], md
