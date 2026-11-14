"""Validate requests and results against schemas/plotpoint.schema.json."""

from __future__ import annotations

import json
from functools import cache
from typing import Any

from jsonschema import Draft202012Validator

from . import SCHEMA_PATH

KINDS = ("storyboardRequest", "storyboardResult", "renderRequest", "renderResult")


class SchemaError(ValueError):
    pass


@cache
def _validator(kind: str) -> Draft202012Validator:
    if kind not in KINDS:
        raise SchemaError(f"unknown kind {kind!r}; use one of {KINDS}")
    doc = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema = {
        "$schema": doc["$schema"],
        "$defs": doc["$defs"],
        "$ref": f"#/$defs/{kind}",
    }
    return Draft202012Validator(schema)


def errors(kind: str, document: Any) -> list[str]:
    """Readable error messages; empty when the document is valid."""
    out = []
    for err in sorted(
        _validator(kind).iter_errors(document), key=lambda e: list(e.path)
    ):
        where = "/".join(str(p) for p in err.absolute_path) or "(top level)"
        out.append(f"{where}: {err.message}")
    return out


def check(kind: str, document: Any) -> None:
    errs = errors(kind, document)
    if errs:
        raise SchemaError(f"{kind} is invalid:\n  " + "\n  ".join(errs))
