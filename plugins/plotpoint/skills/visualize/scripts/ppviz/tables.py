"""Markdown and HTML tables, numbers and sentences.

Tables right-align numbers, format them with thousands separators, and bold
highlighted rows. They are a legitimate output, and the fallback when a visual
exceeds what a chart can carry.
"""

from __future__ import annotations

import html
from typing import Any

from . import config
from .data import Table
from .shape import display, fmt


def _columns(table: Table, intent: dict[str, Any]) -> list[str]:
    cols = (intent.get("fields") or {}).get("columns")
    return list(cols) if cols else list(table.columns)


def _rows(table: Table, intent: dict[str, Any]) -> list[dict[str, Any]]:
    fields = intent.get("fields") or {}
    rows = list(table.rows)
    sort = fields.get("sort")
    key = fields.get("y") if isinstance(fields.get("y"), str) else None
    if key is None:  # default: the first numeric column shown
        key = next(
            (c for c in _columns(table, intent) if table.types.get(c) == "number"),
            None,
        )
    if sort == "value" and key:
        rows.sort(key=lambda r: -(r.get(key) or 0))
    elif sort == "label":
        rows.sort(key=lambda r: str(r.get(table.columns[0])))
    return rows


def _is_highlighted(row: dict[str, Any], highlight: set[str]) -> bool:
    return any(str(v) in highlight for v in row.values() if v is not None)


def markdown_table(table: Table, intent: dict[str, Any]) -> str:
    cols = _columns(table, intent)
    names = (intent.get("fields") or {}).get("names") or {}
    highlight = {str(h) for h in intent.get("highlight") or []}
    head = "| " + " | ".join(display(c, names) for c in cols) + " |"
    sep = (
        "| "
        + " | ".join("---:" if table.types.get(c) == "number" else "---" for c in cols)
        + " |"
    )
    lines = [head, sep]
    for r in _rows(table, intent):
        cells = [fmt(r.get(c)) if r.get(c) is not None else "" for c in cols]
        if _is_highlighted(r, highlight):
            cells = [f"**{c}**" if c else c for c in cells]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def html_table(table: Table, intent: dict[str, Any], font_px: float) -> str:
    t = config.theme()
    ink = t["ink"]
    cols = _columns(table, intent)
    names = (intent.get("fields") or {}).get("names") or {}
    highlight = {str(h) for h in intent.get("highlight") or []}

    def align(c: str) -> str:
        return "right" if table.types.get(c) == "number" else "left"

    cell = f"padding:6px 10px;border-bottom:1px solid {ink['grid']}"
    out = [
        f'<table class="pp-table" style="border-collapse:collapse;font:{font_px}px/1.4 '
        f'{html.escape(t["font"])};color:{ink["primary"]};width:100%">',
        "<thead><tr>",
    ]
    out += [
        f'<th style="{cell};text-align:{align(c)};color:{ink["secondary"]};'
        'font-weight:600">'
        f"{html.escape(display(c, names))}</th>"
        for c in cols
    ]
    out.append("</tr></thead><tbody>")
    for r in _rows(table, intent):
        weight = "font-weight:700;" if _is_highlighted(r, highlight) else ""
        tds = [
            f'<td style="{cell};{weight}text-align:{align(c)};'
            f'font-variant-numeric:tabular-nums">'
            f"{html.escape(fmt(r.get(c)) if r.get(c) is not None else '')}</td>"
            for c in cols
        ]
        out.append("<tr>" + "".join(tds) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def number_parts(table: Table, intent: dict[str, Any]) -> dict[str, str]:
    """The headline figure, its label, and the change vs a previous value, as text."""
    fields = intent.get("fields") or {}
    row = table.rows[0]
    value_col = fields.get("value") or next(
        c for c in table.columns if table.types[c] == "number"
    )
    value = row[value_col]
    label_col = fields.get("label")
    label = (
        str(row[label_col])
        if label_col
        else display(value_col, fields.get("names") or {})
    )
    parts = {"value": fmt(value), "label": label, "change": ""}
    prev_col = fields.get("previous")
    if prev_col and row.get(prev_col):
        prev = row[prev_col]
        pct = (value / prev - 1) * 100
        sign = "+" if pct >= 0 else "−"
        parts["change"] = f"{sign}{abs(pct):.1f}% vs {fmt(prev)}"
    return parts
