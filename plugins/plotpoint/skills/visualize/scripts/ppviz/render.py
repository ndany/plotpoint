"""Render one visual for every requested target, write files, run checks.

The render step is deterministic: the intent (decided by the model, or passed in
from a storyboard) says what to show; this module draws it.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import vl_convert as vlc

from . import (
    checks,
    colors,
    config,
    data,
    layout,
    mermaid,
    output,
    profile,
    schema,
    shape,
    tables,
)

CHARTS = ("line", "bar", "stacked_bar", "scatter", "histogram")
TEXTUAL = ("table", "number", "sentence")


class RenderError(ValueError):
    pass


def _one_line(text: str) -> str:
    """Callout text for text contexts (bullets, notes): line breaks become ': '."""
    return ": ".join(part.strip() for part in text.split("\n") if part.strip())


def _slug(target: str) -> str:
    return target.replace("/", "-")


def _technique(request: dict[str, Any], target: str, vt: str) -> str:
    chosen = (request.get("technique") or {}).get(target)
    allowed = config.layouts()["targets"][target]["techniques"]
    if chosen and chosen not in allowed:
        raise RenderError(
            f"technique {chosen!r} isn't available for {target}; use one of {allowed}"
        )
    if chosen:
        return chosen
    if vt in TEXTUAL:
        if target == "image/slide":
            return "png"
        return "table" if vt == "table" else "text"
    return config.layouts()["targets"][target]["default_technique"]


def _normalize(
    intent: dict[str, Any], color_map: dict[str, str] | None
) -> tuple[dict[str, Any], dict[str, str]]:
    """Let highlights and color-map keys use either column names or display names."""
    names = (intent.get("fields") or {}).get("names") or {}
    it = dict(intent)
    if it.get("highlight"):
        it["highlight"] = [names.get(str(h), h) for h in it["highlight"]]
    if it.get("callouts"):
        it["callouts"] = [
            {**c, "series": names.get(c["series"], c["series"])}
            if c.get("series") is not None
            else c
            for c in it["callouts"]
        ]
    cmap = {names.get(k, k): v for k, v in (color_map or {}).items()}
    return it, cmap


def _entities(shaped: shape.Shaped) -> list[str]:
    if shaped.visual_type == "bar":
        return [str(c) for c in shaped.categories]
    return list(shaped.series)


def plan_requests(
    request: dict[str, Any], result: dict[str, Any]
) -> list[dict[str, Any]]:
    """Render requests for every visual in a storyboard result, for dry runs.

    Data is the visual's own `data` if set, else its first dataset's; sources of
    all its datasets are joined; as-of is the latest."""
    datasets = {d["id"]: d for d in request["datasets"]}
    out = []
    for v in result["visuals"]:
        used = [datasets[d] for d in v["datasets"] if d in datasets]
        if not used:
            raise RenderError(
                f"visual {v['id']}: none of its datasets is in the request"
            )
        out.append(
            {
                "id": v["id"],
                "intent": v["intent"],
                "data": v.get("data") or used[0]["data"],
                "source": "; ".join(dict.fromkeys(d["source"] for d in used)),
                "as_of": max(str(d["as_of"]) for d in used),
                "targets": list(v["renderings"]),
                "technique": {t: r["technique"] for t, r in v["renderings"].items()},
                "layout": request["writeup"].get("layout"),
                "color_map": result["color_map"],
                "out_dir": f"figures/{v['id']}",
            }
        )
    for r in out:
        if r["layout"] is None:
            del r["layout"]
    return out


def render(
    request: dict[str, Any], base_dir: Path, dry_run: bool = False
) -> dict[str, Any]:
    """Render every target. With dry_run, run the checks only: no files are
    written, and only text outputs (tables, numbers, sentences) are returned."""
    schema.check("renderRequest", request)
    if "intent" not in request:
        raise RenderError(
            "render needs an intent. Decide it first (SKILL.md, render step 2), "
            "add it to the request, then render."
        )
    visual_id = request.get("id", "visual")
    raw_intent = request["intent"]
    table = data.load(request["data"], base_dir)
    prof = profile.profile(table, visual_id)
    intent, cmap = _normalize(raw_intent, request.get("color_map"))
    vt = intent["visual_type"]
    out_rel = request.get("out_dir", "figures")
    scratch = tempfile.TemporaryDirectory() if dry_run else None
    out_dir = Path(scratch.name) if scratch else base_dir / out_rel
    out_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "id": visual_id,
        "intent": raw_intent,
        "outputs": {},
        "checks": {},
        "notes": [],
    }
    measures = checks.measures_of(intent)
    texts = [intent["headline"]] + [c["text"] for c in intent.get("callouts") or []]
    st, detail = checks.headline_numbers(texts, table, intent)
    result["checks"]["headline_numbers"] = {"status": st, "detail": detail}
    st, detail = checks.outliers(prof, measures, intent)
    result["checks"]["outliers"] = {"status": st, "detail": detail}
    if intent["headline_status"] == "draft":
        result["notes"].append(
            "Headline is a draft: a person should confirm it before publishing."
        )

    legib: list[str] = []
    render_status: list[str] = []
    capacity_notes: list[str] = []
    callout_checks: dict[str, str] = {}
    for target in request["targets"]:
        lay = layout.resolve(target, request.get("layout"))
        technique = _technique(request, target, vt)
        if technique in ("text", "table"):  # sized by the page, not drawn
            legib.append(f"{target}: skip (text follows the page's font size)")
        else:
            st, detail = checks.legibility(lay)
            legib.append(f"{target}: {detail}" + ("" if st == "pass" else " FAIL"))
        shaped = shape.shape(table, intent, lay.kind, lay.width)
        capacity_notes += [
            f"{target}: {n}" for n in shaped.notes if "capacity" in n or "exceed" in n
        ]
        st, detail = checks.callouts(intent, shaped)
        callout_checks.setdefault(f"{st}: {detail}", target)
        notes = [
            _one_line(c["text"])
            for c in intent.get("callouts") or []
            if c["kind"] == "note" or vt in TEXTUAL
        ]
        notes += [n for n in shaped.notes if n.startswith("Excluded")]
        try:
            entry = _render_target(
                target,
                technique,
                lay,
                table,
                shaped,
                intent,
                cmap,
                notes,
                request,
                visual_id,
                out_dir,
                out_rel,
            )
            render_status.append(f"{target}: {entry.pop('_status', 'pass')}")
        except Exception as exc:  # report per target, keep going
            render_status.append(f"{target}: fail ({exc})")
            continue
        result["outputs"][target] = entry
    fails = [k for k in callout_checks if k.startswith("fail")]
    result["checks"]["callouts"] = (
        {"status": "fail", "detail": fails[0][len("fail: ") :]}
        if fails
        else {"status": "pass", "detail": next(iter(callout_checks))[len("pass: ") :]}
    )
    result["checks"]["legibility"] = {
        "status": "fail"
        if any(s.endswith("FAIL") for s in legib)
        else "skip"
        if all(": skip" in s for s in legib)
        else "pass",
        "detail": "; ".join(legib),
    }
    result["checks"]["capacity"] = {
        "status": "warn" if any("exceed" in n for n in capacity_notes) else "pass",
        "detail": "; ".join(capacity_notes) or "within capacity for every target",
    }
    worst = (
        "fail"
        if any("fail" in s for s in render_status)
        else "skip"
        if any("skip" in s for s in render_status)
        else "pass"
    )
    result["checks"]["render"] = {"status": worst, "detail": "; ".join(render_status)}
    result["notes"] += capacity_notes
    if scratch:  # keep text outputs (no files) so they can be read
        result["outputs"] = {
            t: o for t, o in result["outputs"].items() if not o["files"]
        }
        result["notes"].append("Dry run: checks only, no files written.")
        scratch.cleanup()
    schema.check("renderResult", result)
    if not dry_run:
        (out_dir / f"{visual_id}.result.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
    return result


def _entity_colors(
    shaped: shape.Shaped, intent: dict[str, Any], cmap: dict[str, str]
) -> dict[str, str]:
    """Bars of one measure share one hue unless highlighted or mapped; series get
    distinct colors."""
    if shaped.visual_type == "bar" and not intent.get("highlight"):
        accent = config.theme()["accent"]
        mapped = colors.resolve([c for c in _entities(shaped) if c in cmap], None, cmap)
        return {c: mapped.get(c, accent) for c in _entities(shaped)}
    return colors.resolve(_entities(shaped), intent.get("highlight"), cmap)


def _chart_spec(
    shaped: shape.Shaped,
    intent: dict[str, Any],
    cmap: dict[str, str],
    lay: layout.Layout,
    transparent: bool,
) -> dict[str, Any]:
    from . import vl

    entity_colors = _entity_colors(shaped, intent, cmap)
    return vl.BUILDERS[shaped.visual_type](
        shaped, intent, entity_colors, lay, transparent
    )


def _render_target(
    target: str,
    technique: str,
    lay: layout.Layout,
    table: data.Table,
    shaped: shape.Shaped,
    intent: dict[str, Any],
    cmap: dict[str, str],
    notes: list[str],
    request: dict[str, Any],
    visual_id: str,
    out_dir: Path,
    out_rel: str,
) -> dict[str, Any]:
    vt = intent["visual_type"]
    headline, draft = intent["headline"], intent["headline_status"] == "draft"
    source, as_of = request["source"], str(request["as_of"])
    stem = f"{visual_id}-{_slug(target)}"
    entry: dict[str, Any] = {"technique": technique, "files": [], "snippet": ""}
    if technique not in ("text", "table", "mermaid"):  # drawn at a fixed size
        entry["width"] = lay.canvas[0] if lay.canvas else lay.width
        entry["height"] = lay.canvas[1] if lay.canvas else lay.height
    if vt not in CHARTS + TEXTUAL:
        raise RenderError(
            f"no v1 renderer for {vt!r}; draw it by hand following dataviz, "
            "or choose a v1 type"
        )

    if target == "image/slide":
        big = tables.number_parts(table, intent) if vt == "number" else None
        if vt in ("table", "sentence"):
            raise RenderError(
                f"{vt} isn't rendered as a slide image in v1; use html/slide"
            )
        chart_svg = None
        if vt in CHARTS:
            chart_svg = vlc.vegalite_to_svg(
                json.dumps(_chart_spec(shaped, intent, cmap, lay, True))
            )
        slide = output.compose_slide(
            chart_svg, headline, notes, source, as_of, lay, big
        )
        svg_path, png_path = out_dir / f"{stem}.svg", out_dir / f"{stem}.png"
        svg_path.write_text(slide, encoding="utf-8")
        png_path.write_bytes(vlc.svg_to_png(slide, scale=lay.png_scale))
        entry["files"] = [f"{out_rel}/{png_path.name}", f"{out_rel}/{svg_path.name}"]
        entry["snippet"] = f"![{headline}]({out_rel}/{png_path.name})"
        return entry

    is_md = target.startswith("md/")
    if vt == "sentence":
        body = headline
        entry["snippet"] = (
            output.md_snippet(headline, "", notes, source, as_of, draft)
            if is_md
            else output.html_figure(
                visual_id, headline, "", notes, source, as_of, lay, draft
            )
        )
        return entry
    if vt == "number":
        p = tables.number_parts(table, intent)
        if is_md:
            body = f"**{p['value']}** {p['label']}" + (
                f" ({p['change']})" if p["change"] else ""
            )
            entry["snippet"] = output.md_snippet(
                headline, body, notes, source, as_of, draft
            )
        else:
            ink = config.theme()["ink"]["primary"]  # text is ink, never a hue
            body = (
                f'<div class="pp-number" style="font-weight:700;color:{ink};'
                f'font-size:{lay.sizes["headline"] * 2.2:.0f}px;line-height:1.1">'
                f'{p["value"]}</div><div class="pp-number-label" '
                f'style="font-size:{lay.sizes["direct_label"]}px">'
                f"{p['label']}"
                + (f" · {p['change']}" if p["change"] else "")
                + "</div>"
            )
            entry["snippet"] = output.html_figure(
                visual_id, headline, body, notes, source, as_of, lay, draft
            )
        return entry
    if vt == "table" or technique == "table":
        if is_md:
            entry["snippet"] = output.md_snippet(
                headline,
                tables.markdown_table(table, intent),
                notes,
                source,
                as_of,
                draft,
            )
        else:
            entry["snippet"] = output.html_figure(
                visual_id,
                headline,
                tables.html_table(table, intent, lay.sizes["label"]),
                notes,
                source,
                as_of,
                lay,
                draft,
            )
        return entry

    if technique == "mermaid":
        entity_colors = _entity_colors(shaped, intent, cmap)
        try:
            code, comp = mermaid.xychart(shaped, intent, entity_colors, lay)
        except ValueError as exc:
            raise RenderError(f"{exc}; use technique svg for {target}") from exc
        mm_notes = list(notes)
        if vt == "line":
            mm_notes.insert(
                0,
                "Lines: "
                + ", ".join(
                    f"{n} ({output.color_name(entity_colors[n])}"
                    + (", highlighted" if n in (intent.get("highlight") or []) else "")
                    + ")"
                    for n in shaped.series
                ),
            )
        elif intent.get("highlight"):
            mm_notes.insert(
                0, "Highlighted: " + ", ".join(str(h) for h in intent["highlight"])
            )
        mm_notes += [
            _one_line(c["text"])
            for c in intent.get("callouts") or []
            if c["kind"] != "note"
        ]
        body = f"```mermaid\n{code}\n```"
        if request.get("md_table"):
            body += "\n\n" + tables.markdown_table(table, intent)
        (out_dir / f"{stem}.mmd").write_text(code + "\n", encoding="utf-8")
        entry["files"] = [f"{out_rel}/{stem}.mmd"]
        entry["snippet"] = output.md_snippet(
            headline, body, mm_notes, source, as_of, draft
        )
        status, detail = mermaid.validate(code)
        entry["_status"] = status if status == "pass" else f"{status} ({detail})"
        return entry

    spec = _chart_spec(shaped, intent, cmap, lay, transparent=True)
    if technique == "vega":
        body = output.vega_embed(visual_id, spec)
        entry["snippet"] = output.html_figure(
            visual_id, headline, body, notes, source, as_of, lay, draft
        )
        entry["snippet"] = (
            "<!-- plotpoint: interactive chart; include once in the page <head>:\n"
            + output.VEGA_PAGE_INCLUDE
            + "\n-->\n"
            + entry["snippet"]
        )
        (out_dir / f"{stem}.vl.json").write_text(
            json.dumps(spec, indent=2), encoding="utf-8"
        )
        entry["files"] = [f"{out_rel}/{stem}.vl.json"]
        return entry

    svg = vlc.vegalite_to_svg(json.dumps(spec))
    svg_path = out_dir / f"{stem}.svg"
    svg_path.write_text(svg, encoding="utf-8")
    entry["files"] = [f"{out_rel}/{svg_path.name}"]
    if is_md:
        body = f"![{headline}]({out_rel}/{svg_path.name})"
        if request.get("md_table"):
            body += "\n\n" + tables.markdown_table(table, intent)
        entry["snippet"] = output.md_snippet(
            headline, body, notes, source, as_of, draft
        )
    else:
        body = output.inline_svg(svg, visual_id, headline, lay.width)
        entry["snippet"] = output.html_figure(
            visual_id, headline, body, notes, source, as_of, lay, draft
        )
        frag = out_dir / f"{stem}.html"
        frag.write_text(entry["snippet"] + "\n", encoding="utf-8")
        entry["files"].append(f"{out_rel}/{frag.name}")
    return entry
