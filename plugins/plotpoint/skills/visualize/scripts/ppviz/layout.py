"""Resolve a target plus layout request into concrete sizes.

The scaling rule (references/targets.md): draw at the content width the chart
will occupy, never scale up, and raise text sizes so that labels stay at or
above the legibility minimum at the narrowest expected display width.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from . import config

TEXT_KEYS = ("label", "axis_title", "direct_label", "callout", "source")


class LayoutError(ValueError):
    pass


@dataclass
class Layout:
    target: str
    preset: str
    kind: str  # document | slide
    width: int  # chart drawing width (CSS px)
    height: int
    min_display_width: int
    sizes: dict[str, float]
    canvas: tuple[int, int] | None = None  # slides only
    png_scale: int = 1

    @property
    def is_slide(self) -> bool:
        return self.kind == "slide"

    @property
    def font(self) -> str:
        """Font stack: the bundled font for slide images, system fonts elsewhere."""
        t = config.theme()
        return t["slide_font"] if self.target == "image/slide" else t["font"]

    @property
    def measure_font(self) -> str:
        """Font Vega-Lite measures text with; slide charts are redrawn in `font`."""
        if self.target == "image/slide":
            return config.theme()["slide_measure_font"]
        return self.font

    def display_ratio(self) -> float:
        """Smallest expected display width / drawing width (<= 1)."""
        drawn = self.canvas[0] if self.canvas else self.width
        return min(1.0, self.min_display_width / drawn)

    def smallest_text_px(self) -> float:
        return min(self.sizes[k] for k in TEXT_KEYS) * self.display_ratio()


def _pick(layout_req: dict[str, Any] | None, target: str) -> dict[str, Any]:
    if not layout_req:
        return {}
    if any(
        k in layout_req
        for k in ("preset", "content_width", "height", "min_display_width")
    ):
        return layout_req
    return layout_req.get(target, {}) or {}


def resolve(target: str, layout_req: dict[str, Any] | None = None) -> Layout:
    cfg = config.layouts()
    if target not in cfg["targets"]:
        raise LayoutError(f"unknown target {target!r}")
    req = _pick(layout_req, target)
    preset_name = req.get("preset") or cfg["targets"][target]["preset"]
    preset = cfg["presets"][preset_name]
    kind = preset["kind"]
    if (kind == "slide") != target.endswith("/slide"):
        raise LayoutError(f"preset {preset_name!r} doesn't fit target {target!r}")
    canvas = tuple(preset["canvas"]) if "canvas" in preset else None
    if canvas:
        width, height = preset["chart_box"]
    else:
        width = preset["content_width"]
        if "columns" in preset:
            cols, gap = preset["columns"], preset["gap"]
            width = (width - gap * (cols - 1)) // cols
        height = round(width * preset["height_ratio"])
    width = req.get("content_width", width)
    height = req.get(
        "height",
        height
        if "content_width" not in req
        else round(req["content_width"] * preset.get("height_ratio", 0.45)),
    )
    min_display = req.get("min_display_width", preset["min_display_width"])

    base = dict(config.theme()["scale"][kind])
    min_px = cfg["legibility"]["min_label_px"]
    drawn = canvas[0] if canvas else width
    floor_px = math.ceil(min_px * drawn / min(min_display, drawn))
    sizes = {k: (max(v, floor_px) if k in TEXT_KEYS else v) for k, v in base.items()}
    return Layout(
        target=target,
        preset=preset_name,
        kind=kind,
        width=int(width),
        height=int(height),
        min_display_width=int(min_display),
        sizes=sizes,
        canvas=canvas,
        png_scale=int(preset.get("png_scale", 1)),
    )
