"""Load the skill's YAML configuration files."""

from __future__ import annotations

from functools import cache
from typing import Any

import yaml

from . import CONFIG_DIR


@cache
def load(name: str) -> dict[str, Any]:
    """Return config/<name>.yaml as a dict (cached)."""
    with (CONFIG_DIR / f"{name}.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def layouts() -> dict[str, Any]:
    return load("layouts")


def theme() -> dict[str, Any]:
    return load("theme")


def capacity() -> dict[str, Any]:
    return load("capacity")
