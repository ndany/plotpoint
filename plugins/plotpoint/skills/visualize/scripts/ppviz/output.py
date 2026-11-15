"""Turn rendered charts into deliverables: files, Markdown snippets, HTML fragments
and composed slide images.

HTML output is a fragment (a <figure>), never a whole page: the caller owns the
page. Inline SVG ids are prefixed per visual so several charts can share a page.
"""

from __future__ import annotations

import html
import json
import re
from typing import Any

from . import config
from .layout import Layout

ID_ATTR = re.compile(r'\bid="([^"]+)"')


def prefix_ids(svg: str, prefix: str) -> str:
    """Make every id in an SVG unique to this visual, and update references."""
    ids = set(ID_ATTR.findall(svg))
    for old in sorted(ids, key=len, reverse=True):
        new = f"{prefix}-{old}"
        svg = svg.replace(f'id="{old}"', f'id="{new}"')
        svg = svg.replace(f"url(#{old})", f"url(#{new})")
        svg = svg.replace(f'href="#{old}"', f'href="#{new}"')
    return svg


def inline_svg(svg: str, visual_id: str, headline: str, width: int) -> str:
    """Prepare an SVG for inline use: unique ids, fluid width capped at design width,
    accessible name."""
    svg = re.sub(r"^<\?xml[^>]*>\s*", "", svg)
    svg = prefix_ids(svg, f"pp-{visual_id}")
    svg = re.sub(r'(<svg\b[^>]*?)\s+width="[^"]*"', r"\1", svg, count=1)
    svg = re.sub(r'(<svg\b[^>]*?)\s+height="[^"]*"', r"\1", svg, count=1)
    style = f'style="width:100%;height:auto;max-width:{width}px;display:block"'
    label = html.escape(headline, quote=True)
    return re.sub(
        r"<svg\b", f'<svg {style} role="img" aria-label="{label}"', svg, count=1
    )


def source_line(source: str, as_of: str) -> str:
    return f"Source: {source} · As of {as_of}"


def color_name(hex_color: str) -> str:
    return config.theme()["color_names"].get(hex_color.lower(), hex_color)


def _notes_text(notes: list[str]) -> str:
    return "\n".join(f"- {n}" for n in notes)


def md_snippet(
    headline: str, body: str, notes: list[str], source: str, as_of: str, draft: bool
) -> str:
    parts = []
    if draft:
        parts.append("<!-- plotpoint: draft headline; confirm before publishing -->")
    parts.append(f"**{headline}**")
    parts.append(body)
    if notes:
        parts.append(_notes_text(notes))
    parts.append(f"<sub>{source_line(source, as_of)}</sub>")
    return "\n\n".join(parts) + "\n"


def html_figure(
    visual_id: str,
    headline: str,
    body: str,
    notes: list[str],
    source: str,
    as_of: str,
    layout: Layout,
    draft: bool,
) -> str:
    t = config.theme()
    ink, s = t["ink"], layout.sizes
    headline_px = s["headline"]
    font = html.escape(t["font"])
    width_css = (
        f"width:{layout.canvas[0]}px;height:{layout.canvas[1]}px;"
        f"padding:60px;box-sizing:border-box"
        if layout.canvas
        else f"max-width:{layout.width}px"
    )
    classes = "pp-figure pp-slide" if layout.is_slide else "pp-figure"
    margin = "0" if layout.is_slide else "0 0 2em"  # space before the next block
    out = []
    if draft:
        out.append("<!-- plotpoint: draft headline; confirm before publishing -->")
    out.append(
        f'<figure class="{classes}" data-plotpoint="{visual_id}" '
        f'style="margin:{margin};{width_css};font-family:{font};'
        f'color:{ink["primary"]}">'
    )
    out.append(
        f'<figcaption class="pp-headline" style="font-size:{headline_px}px;'
        f'font-weight:600;line-height:1.25;margin:0 0 12px">'
        f"{html.escape(headline)}</figcaption>"
    )
    out.append(body)
    if notes:
        items = "".join(f"<li>{html.escape(n)}</li>" for n in notes)
        out.append(
            f'<ul class="pp-notes" style="font-size:{s["callout"]}px;'
            f'color:{ink["secondary"]};margin:8px 0 0;padding-left:1.2em">{items}</ul>'
        )
    out.append(
        f'<p class="pp-source" style="font-size:{s["source"]}px;color:{ink["muted"]};'
        f'margin:8px 0 0">{html.escape(source_line(source, as_of))}</p>'
    )
    out.append("</figure>")
    return "\n".join(out)


def vega_embed(visual_id: str, spec: dict[str, Any]) -> str:
    """Interactive fragment. The page includes vega, vega-lite and vega-embed once."""
    payload = json.dumps(spec).replace("</", "<\\/")
    div = f"pp-{visual_id}"
    return (
        f'<div id="{div}"></div>\n'
        f'<script type="application/json" id="{div}-spec">{payload}</script>\n'
        f"<script>vegaEmbed('#{div}', JSON.parse(document.getElementById('{div}-spec')"
        f".textContent), {{actions: false, renderer: 'svg'}});</script>"
    )


VEGA_PAGE_INCLUDE = (
    '<script src="https://cdn.jsdelivr.net/npm/vega@6"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>'
)


def _wrap(text: str, size: float, max_width: float) -> list[str]:
    max_chars = max(10, int(max_width / (size * 0.56)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= max_chars:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def compose_slide(
    chart_svg: str | None,
    headline: str,
    notes: list[str],
    source: str,
    as_of: str,
    layout: Layout,
    big_text: dict[str, str] | None = None,
) -> str:
    """A full slide SVG: headline, the chart (or a big number), notes and source."""
    t = config.theme()
    ink, s = t["ink"], layout.sizes
    cw, ch = layout.canvas
    margin = (cw - layout.width) // 2
    font = html.escape(layout.font, quote=True)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw}" height="{ch}" '
        f'viewBox="0 0 {cw} {ch}" font-family="{font}">',
        f'<rect width="{cw}" height="{ch}" fill="{ink["surface"]}"/>',
    ]
    y = margin * 0.9
    for line in _wrap(headline, s["headline"], cw - 2 * margin)[:2]:
        y += s["headline"] * 1.15
        parts.append(
            f'<text x="{margin}" y="{y:.0f}" font-size="{s["headline"]}" '
            f'font-weight="600" fill="{ink["primary"]}">{html.escape(line)}</text>'
        )
    chart_top = y + s["headline"] * 0.8
    if chart_svg is not None:
        inner = re.sub(r"^<\?xml[^>]*>\s*", "", chart_svg)
        inner = re.sub(
            r"<svg\b", f'<svg x="{margin}" y="{chart_top:.0f}"', inner, count=1
        )
        parts.append(inner)
    elif big_text:
        cy = chart_top + layout.height * 0.45
        parts.append(
            f'<text x="{margin}" y="{cy:.0f}" font-size="{s["headline"] * 3:.0f}" '
            f'font-weight="700" fill="{t["ink"]["primary"]}">'
            f"{html.escape(big_text['value'])}</text>"
        )
        parts.append(
            f'<text x="{margin}" y="{cy + s["headline"] * 1.4:.0f}" '
            f'font-size="{s["headline"]}" fill="{ink["secondary"]}">'
            f"{html.escape(big_text['label'])}</text>"
        )
        if big_text.get("change"):
            parts.append(
                f'<text x="{margin}" y="{cy + s["headline"] * 2.6:.0f}" '
                f'font-size="{s["direct_label"]}" fill="{ink["secondary"]}">'
                f"{html.escape(big_text['change'])}</text>"
            )
    foot = ch - margin * 0.6
    parts.append(
        f'<text x="{margin}" y="{foot:.0f}" font-size="{s["source"]}" '
        f'fill="{ink["muted"]}">{html.escape(source_line(source, as_of))}</text>'
    )
    ny = foot - s["source"] * 1.6
    for note in reversed(notes[:3]):
        parts.append(
            f'<text x="{margin}" y="{ny:.0f}" font-size="{s["callout"]}" '
            f'fill="{ink["secondary"]}">{html.escape(note)}</text>'
        )
        ny -= s["callout"] * 1.4
    parts.append("</svg>")
    return "\n".join(parts)
