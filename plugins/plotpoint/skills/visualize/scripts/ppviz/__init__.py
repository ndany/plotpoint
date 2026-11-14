"""plotpoint visualize: data loading, profiling, rendering and checks.

Run through ``scripts/visualize.py``; see ``references/spec.md``.
"""

from __future__ import annotations

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = SKILL_DIR / "config"
SCHEMA_PATH = SKILL_DIR / "schemas" / "plotpoint.schema.json"

__version__ = "0.1.0"
