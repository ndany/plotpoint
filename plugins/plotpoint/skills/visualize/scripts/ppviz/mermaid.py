"""Mermaid output for line and bar charts (xychart), with validation via mmdc.

What Mermaid can't carry is reported as compensations, which the Markdown
snippet then supplies in text: series names (legends need Mermaid 11.17+),
callouts, and per-bar highlights (xychart colors whole series, not single bars).
"""

from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from . import config
from .layout import Layout
from .shape import Shaped

SUPPORTED = ("line", "bar")


def _nice_max(v: float) -> float:
    """Round up with ~5% headroom to a multiple of half the value's magnitude."""
    if v <= 0:
        return 1
    v *= 1.05
    half = 10 ** math.floor(math.log10(v)) / 2
    return math.ceil(v / half) * half


def _quote(v: Any) -> str:
    return '"' + str(v).replace('"', "'") + '"'


def xychart(
    shaped: Shaped, intent: dict[str, Any], colors: dict[str, str], layout: Layout
) -> tuple[str, list[str]]:
    """Return (mermaid source, compensations)."""
    vt = shaped.visual_type
    if vt not in SUPPORTED:
        raise ValueError(f"Mermaid supports {SUPPORTED}, not {vt!r}")
    t = config.theme()
    comp: list[str] = []
    if vt == "line":
        cats = shaped.categories
        series = shaped.series
        values = {
            n: [
                next(
                    (
                        r["value"]
                        for r in shaped.rows
                        if r["series"] == n and r["x"] == c
                    ),
                    0,
                )
                for c in cats
            ]
            for n in series
        }
        palette = [colors[n] for n in series]
        plots = [
            f"  line {_quote(n)} [{', '.join(str(v) for v in values[n])}]"
            for n in series
        ]
        top = max(max(v) for v in values.values())
        orient = "vertical"
    else:
        cats = [r["x"] for r in shaped.rows]
        vals = [r["value"] for r in shaped.rows]
        highlight = {str(h) for h in intent.get("highlight") or []}
        palette = [t["accent"]]
        plots = [f"  bar [{', '.join(str(v) for v in vals)}]"]
        top = max(vals)
        orient = shaped.orientation
        if highlight:
            comp.append("per-bar highlight shown in text (Mermaid colors whole series)")
    if intent.get("callouts"):
        comp.append("callouts shown as text under the chart")
    if len(cats) > config.capacity()["mermaid_xychart"]["document"]:
        comp.append(f"{len(cats)} categories may crowd Mermaid axis labels")
    s = layout.sizes
    lines = [
        "---",
        "config:",
        "  xyChart:",
        f"    width: {layout.width}",
        f"    height: {layout.height}",
        "    showTitle: false",
        f"    chartOrientation: {orient}",
        "    xAxis:",
        f"      labelFontSize: {int(s['label'])}",
        "    yAxis:",
        f"      labelFontSize: {int(s['label'])}",
        f"      titleFontSize: {int(s['axis_title'])}",
        "  themeVariables:",
        "    xyChart:",
        f'      plotColorPalette: "{", ".join(palette)}"',
        "---",
        "xychart-beta",
        f"  x-axis [{', '.join(_quote(c) for c in cats)}]",
        f"  y-axis {_quote(shaped.y_title or '')} 0 --> {_nice_max(top):g}",
        *plots,
    ]
    return "\n".join(lines), comp


def validate(source: str) -> tuple[str, str]:
    """Render with the Mermaid CLI if available. Returns (status, detail)."""
    mmdc = shutil.which("mmdc")
    if not mmdc:
        return "skip", "Mermaid CLI (mmdc) not installed; Mermaid not render-tested"
    with tempfile.TemporaryDirectory() as tmp:
        src, out = Path(tmp) / "c.mmd", Path(tmp) / "c.svg"
        src.write_text(source, encoding="utf-8")
        # Fixed binary from PATH; arguments are temp files this function created.
        proc = subprocess.run(  # noqa: S603
            [mmdc, "-q", "-i", str(src), "-o", str(out)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if proc.returncode != 0 or not out.exists():
            return "fail", (proc.stderr or proc.stdout or "mmdc failed").strip()[:400]
    return "pass", "Mermaid rendered with mmdc"
