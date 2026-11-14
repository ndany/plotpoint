"""Build Vega-Lite specs for v1 visual types from shaped data.

Every spec is drawn at exactly the layout's chart box (autosize fit, padding
included), so the SVG's size is the design size. Styling follows the dataviz
rules: thin marks, recessive grid, one y-axis, text in ink colors (never the
series color), legend for two or more series plus selective direct labels.
"""

from __future__ import annotations

from typing import Any

from . import config
from .layout import Layout
from .shape import Shaped, fmt, match_callout, uses_log

LINE_HEIGHT = 1.35  # callout line spacing, as a multiple of font size
ONE = {"values": [{}]}  # a single datum, so a callout layer draws once
CHAR_EM = 0.58  # average character width as a fraction of font size


def _text_width(text: str, size: float) -> float:
    return (
        max((len(line) for line in str(text).split("\n")), default=0) * size * CHAR_EM
    )


def base(layout: Layout, transparent: bool) -> dict[str, Any]:
    t = config.theme()
    ink, s = t["ink"], layout.sizes
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "width": layout.width,
        "height": layout.height,
        "autosize": {"type": "fit", "contains": "padding"},
        "background": None if transparent else ink["surface"],
        "config": {
            "font": t["font"],
            "view": {"stroke": None},
            "axis": {
                "labelFontSize": s["label"],
                "titleFontSize": s["axis_title"],
                "labelColor": ink["secondary"],
                "titleColor": ink["secondary"],
                "titleFontWeight": "normal",
                "gridColor": ink["grid"],
                "domainColor": ink["axis"],
                "tickColor": ink["axis"],
                "labelPadding": 6,
                "titlePadding": 8,
            },
            "axisX": {"grid": False, "labelAngle": 0, "ticks": False},
            "axisY": {"domain": False, "ticks": False, "tickCount": 6},
            "legend": {
                "orient": "top",
                "title": None,
                "labelFontSize": s["label"],
                "labelColor": ink["secondary"],
                "symbolStrokeWidth": s["line_width"],
                "direction": "horizontal",
            },
            "text": {"font": t["font"]},
        },
    }


def _x_enc(shaped: Shaped, **extra: Any) -> dict[str, Any]:
    """x encoding that keeps data order on discrete axes in every layer."""
    enc: dict[str, Any] = {
        "field": "x",
        "type": shaped.x_type,
        "title": shaped.x_title,
        **extra,
    }
    if shaped.x_type in ("nominal", "ordinal"):
        enc["sort"] = list(shaped.categories)
        enc["scale"] = {"domain": list(shaped.categories)}
    return enc


def _x_datum(shaped: Shaped, value: Any) -> dict[str, Any]:
    """x encoding for a constant position (callouts), on the same scale as the data."""
    enc = {k: v for k, v in _x_enc(shaped).items() if k not in ("field", "title")}
    return {**enc, "datum": value}


def _rule_levels(
    rules: list[dict[str, Any]], frac: Any, width: float, size: float, align: str
) -> list[int]:
    """Stack level per rule label: 0 unless it would overlap an earlier label.
    frac(x) gives the rule's position as a fraction of the plot width."""
    placed: list[tuple[float, float, int, int]] = []  # left, right, level, lines
    levels = []
    for c in rules:
        w = _text_width(c["text"], size) + 12
        x = frac(c["x"]) * width
        left, right = (x - w, x) if align == "right" else (x, x + w)
        lines = len(c["text"].split("\n"))
        level = 0
        for pl, pr, lv, ln in placed:
            if left < pr and pl < right:
                level = max(level, lv + ln)
        placed.append((left, right, level, lines))
        levels.append(level)
    return levels


def _y_columns(intent: dict[str, Any]) -> list[str]:
    y = (intent.get("fields") or {}).get("y")
    return [y] if isinstance(y, str) else list(y or [])


def _y_scale(intent: dict[str, Any]) -> dict[str, Any]:
    cols = _y_columns(intent) or [None]
    return {"type": "log"} if any(uses_log(intent, c) for c in cols) else {"zero": True}


def _callout_layers(
    intent: dict[str, Any], shaped: Shaped, layout: Layout, y_field: str = "value"
) -> list[dict[str, Any]]:
    ink, s = config.theme()["ink"], layout.sizes
    layers: list[dict[str, Any]] = []
    rules = [c for c in intent.get("callouts") or [] if c["kind"] == "rule"]
    cats = [str(k) for k in shaped.categories]

    def frac(x: Any) -> float:
        if str(x) in cats and len(cats) > 1:
            return (cats.index(str(x)) + 0.5) / len(cats)
        return 0.5

    levels = iter(_rule_levels(rules, frac, layout.width, s["callout"], "right"))
    for c in intent.get("callouts") or []:
        if c["kind"] == "rule":
            stacked = next(levels)
            layers.append(
                {
                    "mark": {
                        "type": "rule",
                        "color": ink["axis"],
                        "strokeWidth": s["rule_width"],
                    },
                    "data": ONE,
                    "encoding": {"x": _x_datum(shaped, c["x"])},
                }
            )
            layers.append(
                {
                    "mark": {
                        "type": "text",
                        "align": "right",
                        "baseline": "top",
                        "dx": -8,
                        "dy": 4 + stacked * s["callout"] * LINE_HEIGHT,
                        "fontSize": s["callout"],
                        "color": ink["secondary"],
                        "lineBreak": "\n",
                    },
                    "data": ONE,
                    "encoding": {
                        "x": _x_datum(shaped, c["x"]),
                        "y": {"value": 0},
                        "text": {"value": c["text"]},
                    },
                }
            )

        elif c["kind"] == "point":
            row, _problem = match_callout(c, shaped)
            if row is None:
                continue  # reported by the callouts check
            layers.append(
                {
                    "data": {"values": [row]},
                    "mark": {
                        "type": "text",
                        "align": "left",
                        "baseline": "bottom",
                        "dx": 8,
                        "dy": -6,
                        "fontSize": s["callout"],
                        "color": ink["primary"],
                        "lineBreak": "\n",
                    },
                    "encoding": {
                        "x": _x_enc(shaped)
                        if y_field == "value"
                        else {"field": "x", "type": "quantitative"},
                        "y": {"field": y_field, "type": "quantitative"},
                        "text": {"value": c["text"]},
                    },
                }
            )
    return layers


def line(
    shaped: Shaped,
    intent: dict[str, Any],
    colors: dict[str, str],
    layout: Layout,
    transparent: bool,
) -> dict[str, Any]:
    spec = base(layout, transparent)
    ink, s = config.theme()["ink"], layout.sizes
    cap = config.capacity()["line"]
    highlight = {str(h) for h in intent.get("highlight") or []}
    last_x = shaped.categories[-1] if shaped.categories else None
    ends = [r for r in shaped.rows if r["x"] == last_x]
    labeled = [
        e
        for e in ends
        if (not highlight and len(shaped.series) <= cap["direct_label_max"])
        or e["series"] in highlight
    ]
    for e in labeled:
        e["label"] = f"{e['series']}  {fmt(e['value'])}"
        e["strong"] = e["series"] in highlight
    right = (
        max((_text_width(e["label"], s["direct_label"]) for e in labeled), default=0)
        + 16
    )
    spec["padding"] = {"left": 4, "top": 8, "right": int(right), "bottom": 4}
    color = {
        "field": "series",
        "type": "nominal",
        "scale": {"domain": shaped.series, "range": [colors[n] for n in shaped.series]},
        "legend": {} if len(shaped.series) > 1 else None,
    }
    x, y = (
        _x_enc(shaped),
        {
            "field": "value",
            "type": "quantitative",
            "title": shaped.y_title,
            "scale": _y_scale(intent),
        },
    )
    spec["data"] = {"values": shaped.rows}
    spec["layer"] = [
        {
            "mark": {
                "type": "line",
                "strokeWidth": s["line_width"],
                "strokeCap": "round",
                "strokeJoin": "round",
            },
            "encoding": {"x": x, "y": y, "color": color},
        },
        {
            "data": {"values": ends},
            "mark": {
                "type": "point",
                "filled": True,
                "opacity": 1,
                "size": s["point_size"],
                "stroke": ink["surface"],
                "strokeWidth": 2,
            },
            "encoding": {
                "x": _x_enc(shaped),
                "y": {"field": "value", "type": "quantitative"},
                "color": {**color, "legend": None},
            },
        },
    ]
    for strong in (False, True):
        group = [e for e in labeled if e["strong"] == strong]
        if not group:
            continue
        spec["layer"].append(
            {
                "data": {"values": group},
                "mark": {
                    "type": "text",
                    "align": "left",
                    "dx": 10,
                    "fontSize": s["direct_label"],
                    "fontWeight": "bold" if strong else "normal",
                    "color": ink["primary"] if strong else ink["secondary"],
                },
                "encoding": {
                    "x": _x_enc(shaped),
                    "y": {"field": "value", "type": "quantitative"},
                    "text": {"field": "label"},
                },
            }
        )
    spec["layer"] += _callout_layers(intent, shaped, layout)
    return spec


def bar(
    shaped: Shaped,
    intent: dict[str, Any],
    colors: dict[str, str],
    layout: Layout,
    transparent: bool,
) -> dict[str, Any]:
    spec = base(layout, transparent)
    ink, s = config.theme()["ink"], layout.sizes
    highlight = {str(h) for h in intent.get("highlight") or []}
    rows = [
        {
            **r,
            "xs": str(r["x"]),
            "color": colors[str(r["x"])],
            "label": fmt(r["value"]),
            "show": (str(r["x"]) in highlight)
            or (not highlight and len(shaped.rows) <= 8),
        }
        for r in shaped.rows
    ]
    horizontal = shaped.orientation == "horizontal"
    cat = {"field": "xs", "type": "nominal", "sort": None, "title": None}
    val = {
        "field": "value",
        "type": "quantitative",
        "title": shaped.y_title,
        "scale": _y_scale(intent),
    }
    if horizontal:
        cat["axis"] = {"grid": False, "domain": False, "ticks": False, "labelLimit": 0}
        val["axis"] = {"grid": True, "domain": False}
    enc = {"x": val, "y": cat} if horizontal else {"x": cat, "y": val}
    spec["data"] = {"values": rows}
    widest = max(
        (_text_width(r["label"], s["direct_label"]) for r in rows if r["show"]),
        default=0,
    )
    spec["padding"] = (
        {"left": 4, "top": 4, "right": int(widest) + 12, "bottom": 4}
        if horizontal
        else {"left": 4, "top": int(s["direct_label"] * 1.6), "right": 4, "bottom": 4}
    )
    spec["layer"] = [
        {
            "mark": {"type": "bar", "cornerRadiusEnd": 4},
            "encoding": {
                **enc,
                "color": {"field": "color", "type": "nominal", "scale": None},
            },
        },
        {
            "transform": [{"filter": "datum.show"}],
            "mark": {
                "type": "text",
                "fontSize": s["direct_label"],
                "color": ink["primary"],
                **(
                    {"align": "left", "dx": 6}
                    if horizontal
                    else {"baseline": "bottom", "dy": -4}
                ),
            },
            "encoding": {**enc, "text": {"field": "label"}},
        },
    ]
    return spec


def stacked_bar(
    shaped: Shaped,
    intent: dict[str, Any],
    colors: dict[str, str],
    layout: Layout,
    transparent: bool,
) -> dict[str, Any]:
    spec = base(layout, transparent)
    ink = config.theme()["ink"]
    normalize = bool((intent.get("fields") or {}).get("normalize"))
    spec["data"] = {"values": shaped.rows}
    spec["padding"] = {"left": 4, "top": 4, "right": 4, "bottom": 4}
    spec["mark"] = {"type": "bar", "stroke": ink["surface"], "strokeWidth": 1}
    spec["encoding"] = {
        "x": {"field": "x", "type": shaped.x_type, "sort": None, "title": None},
        "y": {
            "field": "value",
            "type": "quantitative",
            "title": shaped.y_title,
            "stack": "normalize" if normalize else "zero",
            **({"axis": {"format": "%"}} if normalize else {}),
        },
        "color": {
            "field": "series",
            "type": "nominal",
            "scale": {
                "domain": shaped.series,
                "range": [colors[n] for n in shaped.series],
            },
        },
        "order": {"field": "order", "type": "quantitative"},
    }
    order = {n: i for i, n in enumerate(shaped.series)}
    for r in shaped.rows:
        r["order"] = order[r["series"]]
    return spec


def scatter(
    shaped: Shaped,
    intent: dict[str, Any],
    colors: dict[str, str],
    layout: Layout,
    transparent: bool,
) -> dict[str, Any]:
    spec = base(layout, transparent)
    t, s = config.theme(), layout.sizes
    ink = t["ink"]
    highlight = {str(h) for h in intent.get("highlight") or []}
    for p in shaped.rows:
        p["hl"] = p["label"] in highlight if p["label"] else False
        if highlight:
            p["color"] = t["accent"] if p["hl"] else t["context"]
        elif p["series"]:
            p["color"] = colors[p["series"]]
        else:
            p["color"] = t["accent"]
    spec["data"] = {"values": shaped.rows}
    labels = [p for p in shaped.rows if p["hl"]]
    right = max((_text_width(p["label"], s["direct_label"]) for p in labels), default=0)
    spec["padding"] = {"left": 4, "top": 8, "right": int(right) + 12, "bottom": 4}
    ycol = (_y_columns(intent) or [None])[0]
    xcol = (intent.get("fields") or {}).get("x")
    yscale = (
        {"type": "log"} if uses_log(intent, ycol) else {"zero": False, "nice": True}
    )
    xscale = (
        {"type": "log"} if uses_log(intent, xcol) else {"zero": False, "nice": True}
    )
    spec["layer"] = [
        {
            "mark": {
                "type": "point",
                "filled": True,
                "opacity": 0.85,
                "size": s["point_size"],
                "stroke": ink["surface"],
                "strokeWidth": 1,
            },
            "encoding": {
                "x": {
                    "field": "x",
                    "type": "quantitative",
                    "title": shaped.x_title,
                    "scale": {**xscale, "padding": 16},
                    "axis": {"tickCount": 8},
                },
                "y": {
                    "field": "y",
                    "type": "quantitative",
                    "title": shaped.y_title,
                    "scale": {**yscale, "padding": 16},
                },
                "color": {"field": "color", "type": "nominal", "scale": None},
            },
        },
    ]
    if labels:
        spec["layer"].append(
            {
                "data": {"values": labels},
                "mark": {
                    "type": "text",
                    "align": "left",
                    "dx": 10,
                    "fontSize": s["direct_label"],
                    "fontWeight": "bold",
                    "color": ink["primary"],
                },
                "encoding": {
                    "x": {"field": "x", "type": "quantitative"},
                    "y": {"field": "y", "type": "quantitative"},
                    "text": {"field": "label"},
                },
            }
        )
    if shaped.series and not highlight:
        spec["layer"][0]["encoding"]["color"] = {
            "field": "series",
            "type": "nominal",
            "scale": {
                "domain": shaped.series,
                "range": [colors[n] for n in shaped.series],
            },
        }
    spec["layer"] += _callout_layers(intent, shaped, layout, y_field="y")
    return spec


def histogram(
    shaped: Shaped,
    intent: dict[str, Any],
    colors: dict[str, str],
    layout: Layout,
    transparent: bool,
) -> dict[str, Any]:
    spec = base(layout, transparent)
    t, s = config.theme(), layout.sizes
    bins = (intent.get("fields") or {}).get("bins", 20)
    spec["data"] = {"values": shaped.rows}
    rules = [c for c in intent.get("callouts") or [] if c["kind"] == "rule"]
    vals = [r["value"] for r in shaped.rows] or [0, 1]
    lo, hi = min(vals), max(vals)

    def frac(x: Any) -> float:
        return (float(x) - lo) / (hi - lo) if hi > lo else 0.5

    levels = _rule_levels(rules, frac, layout.width, s["callout"], "left")
    rule_lines = max(
        (lv + len(c["text"].split("\n")) for lv, c in zip(levels, rules, strict=True)),
        default=0,
    )
    spec["padding"] = {
        "left": 4,
        "top": int(s["callout"] * LINE_HEIGHT * max(1, rule_lines) + 12),
        "right": 4,
        "bottom": 4,
    }
    x = {
        "field": "value",
        "type": "quantitative",
        "bin": {"maxbins": bins},
        "title": shaped.x_title,
        "axis": {"format": "~g"},
    }
    spec["layer"] = [
        {
            "mark": {
                "type": "bar",
                "color": t["accent"],
                "stroke": t["ink"]["surface"],
                "strokeWidth": 1,
            },
            "encoding": {
                "x": x,
                "y": {
                    "aggregate": "count",
                    "type": "quantitative",
                    "title": shaped.y_title,
                },
            },
        }
    ]
    for c, above in zip(rules, levels, strict=True):  # overlapping labels stack up
        pos = {"datum": c["x"], "type": "quantitative"}
        spec["layer"].append(
            {
                "mark": {
                    "type": "rule",
                    "color": t["ink"]["primary"],
                    "strokeWidth": s["rule_width"],
                    "strokeDash": [4, 3],
                },
                "data": ONE,
                "encoding": {"x": pos},
            }
        )
        spec["layer"].append(
            {
                "mark": {
                    "type": "text",
                    "align": "left",
                    "baseline": "bottom",
                    "dx": 6,
                    "dy": -4 - above * s["callout"] * LINE_HEIGHT,
                    "fontSize": s["callout"],
                    "color": t["ink"]["secondary"],
                    "lineBreak": "\n",
                },
                "data": ONE,
                "encoding": {"x": pos, "y": {"value": 0}, "text": {"value": c["text"]}},
            }
        )
    return spec


BUILDERS = {
    "line": line,
    "bar": bar,
    "stacked_bar": stacked_bar,
    "scatter": scatter,
    "histogram": histogram,
}
