"""Load a dataset from a file path or inline CSV text into a typed table.

Supported: .csv, .tsv, .json (array of records), .jsonl, and inline CSV text.
Column types are inferred: number, date (YYYY-MM or YYYY-MM-DD) or text.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
NUMBER_RE = re.compile(r"^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$")


class DataError(ValueError):
    """Raised when a dataset can't be loaded or doesn't fit the request."""


@dataclass
class Table:
    columns: list[str]
    rows: list[dict[str, Any]]
    types: dict[str, str] = field(default_factory=dict)

    def values(self, column: str) -> list[Any]:
        if column not in self.columns:
            raise DataError(f"column {column!r} not in data; columns: {self.columns}")
        return [r.get(column) for r in self.rows]

    def numeric(self, column: str) -> list[float]:
        return [v for v in self.values(column) if isinstance(v, (int, float))]


def _cell(raw: Any) -> Any:
    """Convert one raw CSV cell to int, float, or stripped string (None if blank)."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return raw
    text = str(raw).strip()
    if text == "":
        return None
    if NUMBER_RE.match(text):
        num = float(text)
        return (
            int(num)
            if num.is_integer() and "." not in text and "e" not in text.lower()
            else num
        )
    return text


def _infer_type(values: list[Any]) -> str:
    present = [v for v in values if v is not None]
    if not present:
        return "text"
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in present):
        return "number"
    if all(isinstance(v, str) and DATE_RE.match(v) for v in present):
        return "date"
    return "text"


def _from_records(records: list[dict[str, Any]]) -> Table:
    if not records:
        raise DataError("dataset has no rows")
    columns: list[str] = []
    for rec in records:
        if not isinstance(rec, dict):
            raise DataError("JSON data must be an array of objects (records)")
        for key in rec:
            if key not in columns:
                columns.append(key)
    rows = [{c: _cell(rec.get(c)) for c in columns} for rec in records]
    types = {c: _infer_type([r[c] for r in rows]) for c in columns}
    for c, t in types.items():
        if t != "number":
            for r in rows:
                if r[c] is not None and not isinstance(r[c], str):
                    r[c] = str(r[c])
    return Table(columns=columns, rows=rows, types=types)


def _parse_delimited(text: str, delimiter: str) -> Table:
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise DataError("delimited data has no header row")
    return _from_records([dict(row) for row in reader])


def load(spec: dict[str, Any], base_dir: Path | None = None) -> Table:
    """Load ``{"path": ...}`` (relative to base_dir) or ``{"inline": csv_text}``."""
    if "inline" in spec:
        return _parse_delimited(spec["inline"], ",")
    if "path" not in spec:
        raise DataError("data needs either 'path' or 'inline'")
    path = Path(spec["path"])
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    if not path.is_file():
        raise DataError(f"data file not found: {spec['path']}")
    text = path.read_text(encoding="utf-8-sig")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _parse_delimited(text, ",")
    if suffix == ".tsv":
        return _parse_delimited(text, "\t")
    if suffix == ".json":
        data = json.loads(text)
        if not isinstance(data, list):
            raise DataError("JSON data must be an array of objects (records)")
        return _from_records(data)
    if suffix == ".jsonl":
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
        return _from_records(records)
    raise DataError(f"unsupported data format {suffix!r}; use csv, tsv, json or jsonl")
