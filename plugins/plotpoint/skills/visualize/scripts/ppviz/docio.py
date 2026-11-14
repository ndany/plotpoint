"""Read and write request/result documents (YAML or JSON).

YAML parses unquoted dates (2026-09-30) into date objects; they're turned back
into ISO strings so callers needn't quote dates.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import yaml


def _normalize(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _normalize(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_normalize(v) for v in node]
    if isinstance(node, (dt.date, dt.datetime)):
        return node.isoformat()
    return node


def load(path: Path) -> Any:
    text = Path(path).read_text(encoding="utf-8")
    doc = json.loads(text) if Path(path).suffix == ".json" else yaml.safe_load(text)
    return _normalize(doc)


def loads_yaml(text: str) -> Any:
    return _normalize(yaml.safe_load(text))


class _NoAliases(yaml.SafeDumper):
    """Write repeated objects out in full: anchors (&id001) are hard to read."""

    def ignore_aliases(self, data: Any) -> bool:
        return True


def dump_yaml(doc: Any) -> str:
    return yaml.dump(
        doc, Dumper=_NoAliases, sort_keys=False, allow_unicode=True, width=100
    )
