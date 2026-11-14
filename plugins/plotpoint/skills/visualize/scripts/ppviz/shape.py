"""Turn a table plus an intent into the plotted rows for each visual type.

Shared by the Vega-Lite, Mermaid and table renderers so every technique shows
the same numbers. Also applies outlier exclusion and capacity changes, and
records what it did in ``notes``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import config
from .data import DataError, Table


@dataclass
class Shaped:
    visual_type: str
    rows: list[dict[str, Any]]  # long form: x, series, value (or x, y, label, series)
    x_type: str = "nominal"  # nominal | ordinal | temporal | quantitative
    series: list[str] = field(default_factory=list)
    categories: list[Any] = field(default_factory=list)
    x_title: str | None = None
    y_title: str | None = None
    orientation: str = "vertical"
    notes: list[str] = field(default_factory=list)
    excluded: list[Any] = field(default_factory=list)


def display(name: str, names: dict[str, str]) -> str:
    return names.get(name, name)


def fmt(v: Any) -> str:
    if isinstance(v, bool) or v is None:
        return str(v)
    if isinstance(v, int) or (isinstance(v, float) and v.is_integer() and abs(v) >= 1):
        return f"{int(v):,}"
    if isinstance(v, float):
        return f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.1f}"
    return str(v)


def _y_columns(fields: dict[str, Any]) -> list[str]:
    y = fields.get("y")
    if y is None:
        raise DataError("intent.fields.y is required for this visual type")
    return [y] if isinstance(y, str) else list(y)


def _excluded(row: dict[str, Any], values: set[str]) -> bool:
    return any(str(v) in values for v in row.values() if v is not None)


def handlings(intent: dict[str, Any]) -> list[dict[str, Any]]:
    """outlier_handling as a list: one entry, or one per column."""
    h = intent.get("outlier_handling")
    if not h:
        return []
    return list(h) if isinstance(h, list) else [h]


def handling_for(intent: dict[str, Any], column: str | None) -> dict[str, Any] | None:
    """The handling that applies to a column: its own entry, else the general one."""
    hs = handlings(intent)
    for h in hs:
        if column is not None and h.get("column") == column:
            return h
    for h in hs:
        if not h.get("column"):
            return h
    return None


def uses_log(intent: dict[str, Any], column: str | None) -> bool:
    h = handling_for(intent, column)
    return bool(h and h.get("method") == "log_scale")


def _apply_exclusions(
    table: Table, intent: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[Any], str]:
    excl = [h for h in handlings(intent) if h.get("method") == "exclude"]
    if not excl:
        return table.rows, [], ""
    values = {str(v) for h in excl for v in h.get("exclude", [])}
    reason = "; ".join(h["reason"] for h in excl if h.get("reason"))
    kept = [r for r in table.rows if not _excluded(r, values)]
    return kept, sorted(values), reason


def _x_type(table: Table, x: str) -> str:
    t = table.types.get(x)
    if t == "date":
        return "temporal"
    if t == "number":
        return "ordinal"
    return "nominal"


def shape(table: Table, intent: dict[str, Any], kind: str, width: int) -> Shaped:
    vt = intent["visual_type"]
    fields = intent.get("fields") or {}
    names = fields.get("names") or {}
    rows, excluded, reason = _apply_exclusions(table, intent)
    notes: list[str] = []
    if excluded:
        notes.append(
            f"Excluded: {', '.join(excluded)}" + (f" ({reason})" if reason else "")
        )
    cap = config.capacity()

    def limit(name: str) -> int:
        c = cap[name]
        if kind == "slide":
            return int(c["slide"])
        return max(2, int(c["document"] * width / cap["reference_width"]))

    if vt in ("line", "stacked_bar"):
        x = fields.get("x") or table.columns[0]
        if "series" in fields:
            ycol = _y_columns(fields)[0]
            long = [
                {"x": r[x], "series": str(r[fields["series"]]), "value": r[ycol]}
                for r in rows
            ]
            series = list(dict.fromkeys(row["series"] for row in long))
            y_title = display(ycol, names)
        else:
            ycols = _y_columns(fields)
            long = [
                {"x": r[x], "series": display(c, names), "value": r[c]}
                for r in rows
                for c in ycols
            ]
            series = [display(c, names) for c in ycols]
            y_title = intent.get("units") or (
                display(ycols[0], names) if len(ycols) == 1 else None
            )
        long = [r for r in long if r["value"] is not None]
        s = Shaped(
            vt,
            long,
            x_type=_x_type(table, x),
            series=series,
            x_title=None,
            y_title=y_title,
            notes=notes,
            excluded=excluded,
        )
        s.categories = list(dict.fromkeys(r["x"] for r in long))
        key = "line" if vt == "line" else "stacked_bar"
        lim = limit(key)
        if vt == "stacked_bar" and len(series) > lim:
            totals = {
                sname: sum(r["value"] for r in long if r["series"] == sname)
                for sname in series
            }
            keep = sorted(series, key=lambda n: -totals[n])[: lim - 1]
            merged: dict[Any, float] = {}
            for r in long:
                if r["series"] not in keep:
                    merged[r["x"]] = merged.get(r["x"], 0) + r["value"]
            long = [r for r in long if r["series"] in keep] + [
                {"x": k, "series": "Other", "value": v} for k, v in merged.items()
            ]
            s.rows, s.series = long, keep + ["Other"]
            notes.append(
                f"{len(series) - len(keep)} smaller segments combined into 'Other' "
                f"(capacity {lim} for this layout)"
            )
        if vt == "line" and len(series) > lim:
            notes.append(
                f"{len(series)} series exceed {lim} for this layout: "
                "non-highlighted series are grayed and unlabeled"
            )
        return s

    if vt == "bar":
        x = fields.get("x") or table.columns[0]
        ycol = _y_columns(fields)[0]
        pts = [{"x": r[x], "value": r[ycol]} for r in rows if r.get(ycol) is not None]
        sort = fields.get("sort") or (
            "data" if table.types.get(x) == "date" else "value"
        )
        if sort == "value":
            pts.sort(key=lambda r: -r["value"])
        elif sort == "label":
            pts.sort(key=lambda r: str(r["x"]))
        lim = limit("bar")
        if len(pts) > lim:
            head, tail = pts[: lim - 1], pts[lim - 1 :]
            pts = head + [{"x": "Other", "value": sum(r["value"] for r in tail)}]
            notes.append(
                f"{len(tail)} smaller categories combined into 'Other' "
                f"(capacity {lim} for this layout)"
            )
        orient = fields.get("orientation", "auto")
        if orient == "auto":
            longest = max((len(str(p["x"])) for p in pts), default=0)
            orient = "horizontal" if len(pts) > 8 or longest > 10 else "vertical"
        return Shaped(
            vt,
            pts,
            x_type=_x_type(table, x),
            categories=[p["x"] for p in pts],
            x_title=None,
            y_title=intent.get("units") or display(ycol, names),
            orientation=orient,
            notes=notes,
            excluded=excluded,
        )

    if vt == "scatter":
        xcol, ycol = fields.get("x"), _y_columns(fields)[0]
        if not xcol:
            raise DataError("intent.fields.x is required for scatter")
        label, series = fields.get("label"), fields.get("series")
        pts = [
            {
                "x": r[xcol],
                "y": r[ycol],
                "label": str(r[label]) if label else None,
                "series": str(r[series]) if series else None,
            }
            for r in rows
            if r.get(xcol) is not None and r.get(ycol) is not None
        ]
        lim = limit("scatter")
        if len(pts) > lim:
            notes.append(
                f"{len(pts)} points exceed {lim} for this layout: overplotting likely"
            )
        sers = list(dict.fromkeys(p["series"] for p in pts if p["series"]))
        return Shaped(
            vt,
            pts,
            x_type="quantitative",
            series=sers,
            x_title=display(xcol, names),
            y_title=display(ycol, names),
            notes=notes,
            excluded=excluded,
        )

    if vt == "histogram":
        col = fields.get("value") or _y_columns(fields)[0]
        pts = [{"value": r[col]} for r in rows if isinstance(r.get(col), (int, float))]
        return Shaped(
            vt,
            pts,
            x_type="quantitative",
            x_title=intent.get("units") or display(col, names),
            y_title=names.get("count", "Count"),
            notes=notes,
            excluded=excluded,
        )

    if vt in ("table", "number", "sentence"):
        return Shaped(vt, rows, notes=notes, excluded=excluded)

    return Shaped(
        vt,
        rows,
        notes=notes + [f"visual type {vt!r} has no v1 renderer"],
        excluded=excluded,
    )


def _same_x(a: Any, b: Any) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a)))
    return str(a) == str(b)


def match_callout(
    c: dict[str, Any], shaped: Shaped
) -> tuple[dict[str, Any] | None, str | None]:
    """Find what a callout is pinned to. Returns (row, None) on a match, (None, None)
    for callouts that need no row (notes, rules), or (None, problem)."""
    vt, kind = shaped.visual_type, c["kind"]
    label = f"{kind} callout {c['text'].splitlines()[0]!r}"
    if kind == "note" or vt in ("table", "number", "sentence"):
        return None, None
    if kind == "rule":
        if "x" not in c:
            return None, f"{label} needs x"
        if vt in ("histogram", "scatter"):
            if not isinstance(c["x"], (int, float)):
                return None, f"{label}: x must be a number on a {vt}"
            return None, None
        if not any(_same_x(c["x"], k) for k in shaped.categories):
            return None, (
                f"{label}: x {c['x']!r} is not on the x axis "
                f"(one of {', '.join(str(k) for k in shaped.categories[:6])}...)"
            )
        return None, None
    # point
    if vt == "histogram":
        return None, f"{label}: histograms take rule or note callouts, not point"
    series = c.get("series")
    if vt == "scatter":
        cand = [
            r
            for r in shaped.rows
            if (series is None or series in (r.get("label"), r.get("series")))
            and ("x" not in c or _same_x(c["x"], r["x"]))
        ]
        hint = "set series to the point's label and, if labels repeat, x to its x value"
    else:
        cand = [
            r
            for r in shaped.rows
            if "x" in c
            and _same_x(c["x"], r["x"])
            and (series is None or r.get("series") == series)
        ]
        hint = "set x to an x-axis value and series to a series' display name"
        if vt in ("line", "stacked_bar") and series is None and len(shaped.series) > 1:
            return None, f"{label}: name the series ({', '.join(shaped.series)})"
    if not cand:
        return None, f"{label}: matches no plotted point; {hint}"
    if len(cand) > 1:
        return None, f"{label}: matches {len(cand)} points; {hint}"
    return cand[0], None
