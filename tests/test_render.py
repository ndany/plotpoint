"""Rendering: the reference storyboard to every target (T4), capacity changes,
fragments, and the command-line entry point."""

from __future__ import annotations

import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import SCRIPTS
from ppviz import config, docio, render

TARGETS = ["md/document", "html/document", "html/slide", "image/slide"]
ALL_TARGETS_EXCEPT = {"v4": ["image/slide"]}  # tables aren't slide images in v1


def _request(work: Path, visual: dict, targets: list[str], color_map: dict) -> dict:
    data_map = docio.load(work / "render-data.yaml")
    datasets = {
        d["id"]: d for d in docio.load(work / "storyboard-request.yaml")["datasets"]
    }
    ds = datasets[visual["datasets"][0]]
    return {
        "id": visual["id"],
        "intent": visual["intent"],
        "data": data_map[visual["id"]],
        "source": ds["source"],
        "as_of": ds["as_of"],
        "targets": targets,
        "technique": {t: r["technique"] for t, r in visual["renderings"].items()},
        "color_map": color_map,
        "out_dir": f"figures/{visual['id']}",
    }


@pytest.fixture
def rendered(workdir: Path) -> dict[str, dict]:
    gold = docio.load(workdir / "storyboard-golden.yaml")
    out = {}
    for v in gold["visuals"]:
        targets = [t for t in TARGETS if t not in ALL_TARGETS_EXCEPT.get(v["id"], [])]
        out[v["id"]] = render.render(
            _request(workdir, v, targets, gold["color_map"]), workdir
        )
    out["_work"] = workdir
    out["_gold"] = gold
    return out


def _png_size(path: Path) -> tuple[int, int]:
    return struct.unpack(">II", path.read_bytes()[16:24])


def test_t4_every_check_passes(rendered: dict) -> None:
    for vid, res in rendered.items():
        if vid.startswith("_"):
            continue
        bad = {k: c for k, c in res["checks"].items() if c["status"] == "fail"}
        assert not bad, (vid, bad)


def test_t4_files_exist_and_sizes_match_layout(rendered: dict) -> None:
    work = rendered["_work"]
    for vid in ("v1", "v3", "v5"):
        outs = rendered[vid]["outputs"]
        png = work / outs["image/slide"]["files"][0]
        assert _png_size(png) == (3840, 2160)
        svg = (work / outs["html/document"]["files"][0]).read_text()
        assert re.search(r'<svg[^>]*width="960"[^>]*height="432"', svg), vid
        for target, entry in outs.items():
            for f in entry["files"]:
                assert (work / f).is_file(), (vid, target, f)


def test_t4_techniques_follow_the_storyboard(rendered: dict) -> None:
    for v in rendered["_gold"]["visuals"]:
        outs = rendered[v["id"]]["outputs"]
        for target, plan in v["renderings"].items():
            assert outs[target]["technique"] == plan["technique"], (v["id"], target)


def test_t4_same_intent_different_technique(rendered: dict) -> None:
    v1 = rendered["v1"]["outputs"]
    assert v1["md/document"]["technique"] == "mermaid"
    assert v1["html/document"]["technique"] == "svg"
    headline = rendered["v1"]["intent"]["headline"]
    for target in ("md/document", "html/document", "html/slide"):
        snippet = v1[target]["snippet"].replace("&#x27;", "'").replace("&#39;", "'")
        assert headline in snippet, target
    # Mermaid can't draw callouts: the callout appears as text instead.
    assert "Total 1,230 → 1,008 (−18%)" in v1["md/document"]["snippet"]


def test_t4_colors_follow_the_color_map(rendered: dict) -> None:
    theme = config.theme()
    work = rendered["_work"]
    for target in ("html/document", "html/slide", "image/slide"):
        f = next(
            f for f in rendered["v1"]["outputs"][target]["files"] if f.endswith(".svg")
        )
        svg = (work / f).read_text().lower()
        assert theme["accent"] in svg and theme["context"] in svg, target
    assert (
        f"{theme['context']}, {theme['accent']}"
        in rendered["v1"]["outputs"]["md/document"]["snippet"]
    )


def test_html_output_is_a_fragment_with_unique_ids(rendered: dict) -> None:
    ids: list[str] = []
    for vid in ("v1", "v3", "v5"):
        snippet = rendered[vid]["outputs"]["html/document"]["snippet"]
        assert snippet.lstrip().startswith(("<figure", "<!--"))
        assert "<html" not in snippet and "<body" not in snippet
        assert "max-width:960px" in snippet
        ids += re.findall(r'\bid="([^"]+)"', snippet)
    assert len(ids) == len(set(ids))
    assert all(i.startswith("pp-") for i in ids)


def test_inline_svg_prefixes_ids_and_references() -> None:
    from ppviz import output

    svg = (
        '<svg width="960" height="432" viewBox="0 0 960 432">'
        '<clipPath id="clip1"><rect/></clipPath>'
        '<g clip-path="url(#clip1)"><use href="#clip1"/></g></svg>'
    )
    out = output.inline_svg(svg, "v9", "A headline", 960)
    assert 'id="pp-v9-clip1"' in out
    assert "url(#pp-v9-clip1)" in out and 'href="#pp-v9-clip1"' in out
    assert 'width="960"' not in out and "max-width:960px" in out
    assert 'aria-label="A headline"' in out


def test_draft_headlines_are_flagged(rendered: dict) -> None:
    v5 = rendered["v5"]
    assert any("draft" in n.lower() for n in v5["notes"])
    assert "draft headline" in v5["outputs"]["md/document"]["snippet"]


def test_table_as_slide_image_is_refused_clearly(workdir: Path) -> None:
    gold = docio.load(workdir / "storyboard-golden.yaml")
    v4 = next(v for v in gold["visuals"] if v["id"] == "v4")
    res = render.render(
        _request(workdir, v4, ["image/slide"], gold["color_map"]), workdir
    )
    assert res["checks"]["render"]["status"] == "fail"
    assert "use html/slide" in res["checks"]["render"]["detail"]


def test_mermaid_output_renders(rendered: dict) -> None:
    if not shutil.which("mmdc"):
        pytest.skip("Mermaid CLI (mmdc) not installed")
    detail = rendered["v1"]["checks"]["render"]["detail"]
    assert "md/document: pass" in detail


def _bar_request(work: Path, n: int, targets: list[str]) -> dict:
    rows = "\n".join(f"Branch {i},{100 - i}" for i in range(n))
    return {
        "id": "many",
        "intent": {
            "visual_type": "bar",
            "headline": "Branch 0 has the most visits",
            "headline_status": "draft",
            "fields": {"x": "branch", "y": "visits"},
            "outlier_handling": {"method": "none_flagged"},
        },
        "data": {"inline": "branch,visits\n" + rows + "\n"},
        "source": "test",
        "as_of": "2026-09-30",
        "targets": targets,
        "out_dir": "figures/many",
    }


def test_capacity_folds_bars_into_other(workdir: Path) -> None:
    res = render.render(
        _bar_request(workdir, 20, ["html/document", "image/slide"]), workdir
    )
    assert "Other" in (workdir / "figures/many/many-html-document.svg").read_text()
    assert any(
        "combined into 'Other'" in n and "capacity 12" in n for n in res["notes"]
    )
    assert any("capacity 7" in n for n in res["notes"])


@pytest.mark.parametrize(
    ("visual_type", "fields", "dataset"),
    [
        ("bar", {"x": "branch", "y": "visits_k"}, "data/branch_overview.json"),
        (
            "stacked_bar",
            {"x": "quarter", "y": ["print", "ebook"]},
            "data/derived/loans_by_quarter.csv",
        ),
        ("line", {"x": "quarter", "y": ["print"]}, "data/derived/loans_by_quarter.csv"),
        (
            "scatter",
            {"x": "staff_fte", "y": "avg_wait_min", "label": "branch"},
            "data/branch_waits.jsonl",
        ),
        ("histogram", {"value": "wait_min"}, "data/wait_minutes.csv"),
    ],
)
@pytest.mark.parametrize("layout_req", [{"preset": "prose"}, {"content_width": 640}])
def test_t5_each_chart_type_renders_at_each_document_layout(
    workdir: Path, visual_type: str, fields: dict, dataset: str, layout_req: dict
) -> None:
    req = {
        "id": f"t5-{visual_type}",
        "intent": {
            "visual_type": visual_type,
            "headline": "A test chart",
            "headline_status": "draft",
            "fields": fields,
            "outlier_handling": {"method": "accept", "reason": "test"},
        },
        "data": {"path": dataset},
        "source": "test",
        "as_of": "2026-09-30",
        "targets": ["html/document", "md/document"],
        "layout": layout_req,
        "out_dir": "figures/t5",
    }
    res = render.render(req, workdir)
    assert res["checks"]["render"]["status"] == "pass", res["checks"]["render"]
    assert res["checks"]["legibility"]["status"] == "pass"
    width = 800 if layout_req.get("preset") == "prose" else 640
    svg = (workdir / res["outputs"]["html/document"]["files"][0]).read_text()
    assert f'width="{width}"' in svg


def test_cli_validate_profile_render(workdir: Path) -> None:
    cli = [sys.executable, str(SCRIPTS / "visualize.py")]
    ok = subprocess.run(
        [*cli, "validate", "storyboardResult", "storyboard-golden.yaml"],
        cwd=workdir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert ok.returncode == 0, ok.stderr
    prof = subprocess.run(
        [*cli, "profile", "storyboard-request.yaml"],
        cwd=workdir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert prof.returncode == 0 and "dataset: branch_waits" in prof.stdout
    bad = subprocess.run(
        [*cli, "validate", "storyboardResult", "storyboard-request.yaml"],
        cwd=workdir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert bad.returncode == 1


def _scatter_request(callouts: list[dict], **intent: object) -> dict:
    return {
        "id": "s1",
        "intent": {
            "visual_type": "scatter",
            "headline": "Riverside waits 48 minutes",
            "headline_status": "confirmed",
            "fields": {"x": "staff_fte", "y": "avg_wait_min", "label": "branch"},
            "highlight": ["Riverside"],
            "callouts": callouts,
            "outlier_handling": [
                {"column": "avg_wait_min", "method": "callout"},
                {"column": "staff_fte", "method": "accept", "reason": "real"},
            ],
            **intent,
        },
        "data": {"path": "data/branch_waits.jsonl"},
        "source": "Invented",
        "as_of": "2026-09-30",
        "targets": ["html/document"],
        "out_dir": "figures/s1",
    }


def test_unpinned_callouts_fail_instead_of_vanishing(workdir: Path) -> None:
    res = render.render(
        _scatter_request([{"kind": "point", "x": "Riverside", "text": "48 min"}]),
        workdir,
    )
    assert res["checks"]["callouts"]["status"] == "fail"
    assert "matches no plotted point" in res["checks"]["callouts"]["detail"]


def test_scatter_point_callout_by_label_alone(workdir: Path) -> None:
    res = render.render(
        _scatter_request([{"kind": "point", "series": "Riverside", "text": "Busiest"}]),
        workdir,
    )
    assert res["checks"]["callouts"]["status"] == "pass"
    # The check confirms the match, not the drawing (HANDOFF backlog), so it
    # doesn't claim the callout was placed.
    assert res["checks"]["callouts"]["detail"] == "1 callout(s) matched to the data"
    svg = (workdir / "figures/s1/s1-html-document.svg").read_text()
    assert svg.count(">Busiest<") == 1


def test_per_column_outlier_handling(workdir: Path) -> None:
    res = render.render(_scatter_request([]), workdir)
    assert res["checks"]["outliers"]["status"] == "pass"
    req = _scatter_request([])
    req["intent"]["outlier_handling"] = [
        {"column": "avg_wait_min", "method": "callout"}
    ]
    res = render.render(req, workdir)
    assert res["checks"]["outliers"]["status"] == "fail"
    assert "staff_fte" in res["checks"]["outliers"]["detail"]


def test_line_point_callout_accepts_column_name(workdir: Path) -> None:
    gold = docio.load(workdir / "storyboard-golden.yaml")
    v1 = next(v for v in gold["visuals"] if v["id"] == "v1")
    v1["intent"]["callouts"].append(
        {"kind": "point", "x": "Q3 '26", "series": "ebook", "text": "New high"}
    )
    res = render.render(_request(workdir, v1, ["html/document"], {}), workdir)
    assert res["checks"]["callouts"]["status"] == "pass"


def test_callout_rules_draw_once(rendered: dict) -> None:
    work = rendered["_work"]
    for vid, text in (("v5", "Median 7.8 min"), ("v1", "Q2 renovation")):
        svg = (work / f"figures/{vid}/{vid}-html-document.svg").read_text()
        assert svg.count(text) == 1, vid


def test_dry_run_checks_without_writing(workdir: Path) -> None:
    res = render.render(_scatter_request([]), workdir, dry_run=True)
    assert res["outputs"] == {}
    assert res["checks"]["outliers"]["status"] == "pass"
    assert not (workdir / "figures/s1").exists()


def test_text_outputs_report_no_size_and_title_status(rendered: dict) -> None:
    v2 = rendered["v2"]["outputs"]["md/document"]
    assert "width" not in v2 and "height" not in v2
    assert "width" in rendered["v3"]["outputs"]["html/document"]


def test_table_callouts_become_notes_and_outliers_skip(workdir: Path) -> None:
    gold = docio.load(workdir / "storyboard-golden.yaml")
    v4 = next(v for v in gold["visuals"] if v["id"] == "v4")
    v4["intent"]["headline_status"] = "title"
    v4["intent"]["headline"] = "Branch overview"
    v4["intent"]["callouts"] = [{"kind": "point", "x": "Central", "text": "Largest"}]
    res = render.render(_request(workdir, v4, ["md/document"], {}), workdir)
    assert "Largest" in res["outputs"]["md/document"]["snippet"]
    assert res["checks"]["outliers"]["status"] == "skip"
    assert not any("draft" in n for n in res["notes"])


def test_table_sort_value_defaults_to_first_numeric_column(workdir: Path) -> None:
    from ppviz import data, tables

    t = data.load({"path": "data/branch_overview.json"}, workdir)
    intent = {"fields": {"columns": ["branch", "visits_k"], "sort": "value"}}
    rows = tables._rows(t, intent)
    assert [r["visits_k"] for r in rows] == sorted(
        (r["visits_k"] for r in t.rows), reverse=True
    )


def test_check_plan_dry_runs_the_reference_storyboard(workdir: Path) -> None:
    gold = docio.load(workdir / "storyboard-golden.yaml")  # v1 names its merge file
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "visualize.py"),
            "check-plan",
            str(workdir / "storyboard-request.yaml"),
            str(workdir / "storyboard-golden.yaml"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    report = docio.loads_yaml(proc.stdout)
    assert set(report) == {v["id"] for v in gold["visuals"]}
    assert "48,210" in report["v2"]["text_outputs"]["md/document"]
    assert not (workdir / "figures").exists()


def test_profile_accepts_a_render_request_with_inline_data(workdir: Path) -> None:
    req = workdir / "r2.yaml"
    req.write_text(
        docio.dump_yaml(
            {
                "id": "r2",
                "question": "How many members?",
                "data": {
                    "inline": "metric,value,previous\nActive members,48210,46700\n"
                },
                "source": "Invented",
                "as_of": "2026-09-30",
                "targets": ["md/document"],
            }
        )
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "visualize.py"), "profile", str(req)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "48210" in proc.stdout and "&id" not in proc.stdout


def test_cli_writes_utf8_on_a_legacy_code_page(workdir: Path) -> None:
    """Windows consoles and pipes default to cp1252, which can't encode the
    output's non-ASCII text (the 2026-11-14 Windows CI run crashed on '→')."""
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "visualize.py"),
            "check-plan",
            "storyboard-request.yaml",
            "storyboard-golden.yaml",
        ],
        cwd=workdir,
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "cp1252"},
        check=False,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert "→" in proc.stdout.decode("utf-8")


def test_text_outputs_skip_legibility(rendered: dict) -> None:
    detail = rendered["v2"]["checks"]["legibility"]["detail"]
    assert "md/document: skip" in detail  # text: sized by the page
    assert "image/slide: smallest text" in detail  # the slide image is drawn


def test_histogram_rule_labels_stack() -> None:
    from ppviz import layout as lay
    from ppviz import shape, vl

    intent = {
        "visual_type": "histogram",
        "fields": {"value": "v"},
        "callouts": [
            {"kind": "rule", "x": 7.8, "text": "Median 7.8 min"},
            {"kind": "rule", "x": 9, "text": "Mean 9 min"},  # close: must stack
            {"kind": "rule", "x": 18, "text": "Far away"},  # clear: stays level
        ],
    }
    shaped = shape.Shaped("histogram", [{"value": 1}, {"value": 20}])
    spec = vl.histogram(shaped, intent, {}, lay.resolve("html/document", None), True)
    dys = [lyr["mark"]["dy"] for lyr in spec["layer"] if lyr["mark"]["type"] == "text"]
    assert dys[0] == dys[2] and dys[1] < dys[0]
    assert spec["padding"]["top"] > -min(dys)


def test_try_it_requests_behave_as_documented(workdir: Path) -> None:
    """The hand-testing requests (docs/guide/try-it.md) do what the guide says."""
    reqs = workdir / "requests"
    for name in ("v1-line", "v3-scatter", "v2-number"):
        res = render.render(docio.load(reqs / f"{name}.yaml"), reqs)
        bad = {k: c for k, c in res["checks"].items() if c["status"] == "fail"}
        assert not bad, (name, bad)
    res = render.render(docio.load(reqs / "broken.yaml"), reqs)
    failed = {k for k, c in res["checks"].items() if c["status"] == "fail"}
    assert failed == {"headline_numbers", "outliers", "callouts"}
    with pytest.raises(render.RenderError, match="needs an intent"):
        render.render(docio.load(reqs / "mode-c.yaml"), reqs)


# --- bundled slide font (C2): slide PNGs must not depend on system fonts ---------


def _slide(work: Path, vid: str) -> tuple[str, Path]:
    gold = docio.load(work / "storyboard-golden.yaml")
    v = next(v for v in gold["visuals"] if v["id"] == vid)
    res = render.render(
        _request(work, v, ["image/slide", "html/document"], gold["color_map"]), work
    )
    outs = res["outputs"]
    png = work / outs["image/slide"]["files"][0]
    return outs, png


def test_bundled_font_files_exist_with_license() -> None:
    from ppviz import FONT_DIR

    for name in ("Regular", "Semibold", "Bold"):
        assert (FONT_DIR / f"SourceSans3-{name}.ttf").stat().st_size > 100_000
    assert "SIL OPEN FONT LICENSE Version 1.1" in (FONT_DIR / "OFL.txt").read_text()


def test_slide_names_bundled_family_and_documents_keep_system_stack(
    workdir: Path,
) -> None:
    theme = config.theme()
    assert "Source Sans 3" in theme["slide_font"]
    outs, _ = _slide(workdir, "v1")
    slide_svg = (workdir / outs["image/slide"]["files"][1]).read_text()
    families = set(re.findall(r'font-family="([^"]*)"', slide_svg))
    # every text element, including the chart's, names the bundled family
    assert families == {"&#x27;Source Sans 3&#x27;, sans-serif"}, families
    assert "Segoe UI" not in slide_svg and "system-ui" not in slide_svg
    # chart text inside the slide uses the bundled family too
    assert slide_svg.count("Source Sans 3") > 5
    doc_svg = (workdir / outs["html/document"]["files"][0]).read_text()
    assert "Source Sans 3" not in doc_svg
    assert "Segoe UI" in doc_svg


def test_fonts_are_registered_once(workdir: Path, monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(render.vlc, "register_font_directory", calls.append)
    monkeypatch.setattr(render, "_fonts_registered", False)
    _slide(workdir, "v1")
    _slide(workdir, "v3")
    assert calls == [str(render.FONT_DIR)]


def _pixel_hash(png: Path) -> str:
    """SHA-256 of the decoded image data, so PNG compression details don't matter."""
    import hashlib
    import zlib

    data, pos, idat = png.read_bytes(), 8, b""
    while pos < len(data):
        n = struct.unpack(">I", data[pos : pos + 4])[0]
        if data[pos + 4 : pos + 8] == b"IDAT":
            idat += data[pos + 8 : pos + 8 + n]
        pos += 12 + n
    return hashlib.sha256(zlib.decompress(idat)).hexdigest()


def test_slide_png_is_identical_on_every_platform(workdir: Path) -> None:
    """Same slide, same pixels everywhere (golden hashes in fixtures/slide-hashes.yaml).

    Fails if text falls back to a system font or measures differently. After an
    intended rendering change, look at the slides, then store the hashes the
    failure prints (docs/testing.md, Slide pixel hashes)."""
    expected = docio.load(Path(__file__).parent / "fixtures" / "slide-hashes.yaml")
    changed = {}
    for vid in expected:
        _, png = _slide(workdir, vid)
        if (got := _pixel_hash(png)) != expected[vid]:
            changed[vid] = got
    assert not changed, (
        f"slides drawn differently: {changed}. Look at them, then store the new "
        "hashes (docs/testing.md, Slide pixel hashes)"
    )


# --- deliverable files (C12): every document target writes a file ----------------

LINK = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def test_every_document_target_writes_its_deliverable(rendered: dict) -> None:
    work = rendered["_work"]
    for vid, res in rendered.items():
        if vid.startswith("_"):
            continue
        for target, out in res["outputs"].items():
            if target == "image/slide":
                continue
            ext = ".md" if target.startswith("md/") else ".html"
            name = f"figures/{vid}/{vid}-{target.replace('/', '-')}{ext}"
            assert name in out["files"], (vid, target, out["files"])
            assert (work / name).is_file()


def test_md_deliverable_links_resolve_from_its_own_folder(workdir: Path) -> None:
    gold = docio.load(workdir / "storyboard-golden.yaml")
    v1 = next(v for v in gold["visuals"] if v["id"] == "v1")
    req = _request(workdir, v1, ["md/document"], gold["color_map"])
    req["technique"] = {"md/document": "svg"}  # a picture, so the file has a link
    res = render.render(req, workdir)
    out = res["outputs"]["md/document"]
    md_file = workdir / "figures/v1/v1-md-document.md"
    links = LINK.findall(md_file.read_text(encoding="utf-8"))
    assert links == ["v1-md-document.svg"]
    assert all((md_file.parent / link).is_file() for link in links)
    # the snippet is for pasting into the caller's document: relative to the request
    assert LINK.findall(out["snippet"]) == ["figures/v1/v1-md-document.svg"]
    assert all((workdir / link).is_file() for link in LINK.findall(out["snippet"]))
    assert md_file.read_text(encoding="utf-8").count("**") >= 2  # headline present


def test_text_outputs_in_dry_run_still_come_back(workdir: Path) -> None:
    gold = docio.load(workdir / "storyboard-golden.yaml")
    v2 = next(v for v in gold["visuals"] if v["id"] == "v2")
    res = render.render(
        _request(workdir, v2, ["md/document", "html/document"], gold["color_map"]),
        workdir,
        dry_run=True,
    )
    assert set(res["outputs"]) == {"md/document", "html/document"}
    assert not (workdir / "figures/v2").exists()
