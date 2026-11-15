"""Tests for scripts/check-privacy.sh and scripts/package-skill.sh."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

# The dev scripts are bash, run on macOS and Linux (CI runs them on ubuntu). On
# Windows runners `bash` can resolve to WSL rather than Git Bash.
pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="bash dev scripts run on macOS and Linux only"
)

REPO = Path(__file__).resolve().parent.parent
PRIVACY = REPO / "scripts" / "check-privacy.sh"
PACKAGE = REPO / "scripts" / "package-skill.sh"

# Build paths at runtime so this test file never contains a literal home path.
HOME_PATH = "/" + "Users" + "/someone/project"
LINUX_HOME_PATH = "/" + "home" + "/someone/project"


def run_privacy(cwd: Path, *files: str, env: dict | None = None):
    return subprocess.run(
        ["bash", str(PRIVACY), *files],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
        check=False,
    )


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


def test_privacy_clean_file_passes(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "ok.md").write_text("Install to ~/.claude/skills/\n")
    assert run_privacy(tmp_path, "ok.md").returncode == 0


def test_privacy_flags_mac_home_path(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "bad.md").write_text(f"see {HOME_PATH}\n")
    result = run_privacy(tmp_path, "bad.md")
    assert result.returncode == 1
    assert "PRIVACY bad.md:1" in result.stdout


def test_privacy_flags_linux_home_path(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "bad.md").write_text(f"see {LINUX_HOME_PATH}\n")
    assert run_privacy(tmp_path, "bad.md").returncode == 1


def test_privacy_local_patterns(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / ".privacy-patterns.local").write_text("# comment\n\nsecret-project\n")
    (tmp_path / "doc.md").write_text("Notes about secret-project.\n")
    (tmp_path / "fine.md").write_text("Nothing private here.\n")
    assert run_privacy(tmp_path, "doc.md").returncode == 1
    assert run_privacy(tmp_path, "fine.md").returncode == 0


def test_privacy_scans_tracked_files_by_default(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "bad.md").write_text(f"see {HOME_PATH}\n")
    subprocess.run(["git", "add", "bad.md"], cwd=tmp_path, check=True)
    assert run_privacy(tmp_path).returncode == 1


def test_privacy_repo_is_clean() -> None:
    """Non-regression: this repository passes its own privacy check."""
    result = run_privacy(REPO)
    assert result.returncode == 0, result.stdout


def make_fake_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    shutil.copy(PACKAGE, root / "scripts" / "package-skill.sh")
    skill = root / "plugins" / "demo" / "skills" / "alpha"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: alpha\ndescription: x\n---\n")
    (skill / "references" / "ref.md").write_text("ref\n")
    return root


def test_package_zip_root_is_skill_folder(tmp_path: Path) -> None:
    root = make_fake_repo(tmp_path)
    out = tmp_path / "out"
    result = subprocess.run(
        ["bash", str(root / "scripts" / "package-skill.sh"), "alpha", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(out / "alpha.zip") as zf:
        names = set(zf.namelist())
    assert "alpha/SKILL.md" in names
    assert "alpha/references/ref.md" in names
    assert all(n.startswith("alpha/") for n in names)


def test_package_unknown_skill_fails(tmp_path: Path) -> None:
    root = make_fake_repo(tmp_path)
    result = subprocess.run(
        ["bash", str(root / "scripts" / "package-skill.sh"), "missing", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "found 0" in result.stderr
