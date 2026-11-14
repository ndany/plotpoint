"""Shared test setup: import the skill's engine and locate the fixture."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "plugins" / "plotpoint" / "skills" / "visualize"
SCRIPTS = SKILL / "scripts"
FIXTURE = REPO / "tests" / "fixtures" / "library-review"

sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    """A writable copy of the library-review fixture."""
    dest = tmp_path / "library-review"
    shutil.copytree(FIXTURE, dest, ignore=shutil.ignore_patterns("runs"))
    return dest
