"""Layouts and legibility (T5), colors, schemas, and the headline/outlier checks."""

from __future__ import annotations

import pytest
from conftest import FIXTURE
from ppviz import checks, colors, config, data, docio, layout, profile, render, schema

PRESETS_BY_TARGET = {
    "md/document": ["prose", "report", "wide", "dashboard"],
    "html/document": ["prose", "report", "wide", "dashboard"],
    "html/slide": ["deck"],
    "image/slide": ["slide-image"],
}


@pytest.mark.parametrize(
    ("target", "preset"),
    [(t, p) for t, ps in PRESETS_BY_TARGET.items() for p in ps],
)
def test_every_preset_is_legible(target: str, preset: str) -> None:
    lay = layout.resolve(target, {"preset": preset})
    status, detail = checks.legibility(lay)
    assert status == "pass", detail


@pytest.mark.parametrize("width", [480, 752, 1280])
def test_caller_width_is_used_and_legible(width: int) -> None:
    lay = layout.resolve("html/document", {"content_width": width})
    assert lay.width == width
    assert checks.legibility(lay)[0] == "pass"


def test_default_layout_is_report_960() -> None:
    lay = layout.resolve("html/document")
    assert (lay.preset, lay.width) == ("report", 960)


def test_per_target_layout_override() -> None:
    req = {"html/document": {"preset": "prose"}}
    assert layout.resolve("html/document", req).width == 800
    assert layout.resolve("md/document", req).width == 960


def test_slide_preset_rejected_for_document() -> None:
    with pytest.raises(layout.LayoutError):
        layout.resolve("html/document", {"preset": "deck"})


def test_colors_highlight_and_map() -> None:
    theme = config.theme()
    out = colors.resolve(["Print", "E-book"], ["E-book"], None)
    assert out == {"Print": theme["context"], "E-book": theme["accent"]}
    mapped = colors.resolve(["a", "b"], None, {"b": "slot1"})
    assert mapped["b"] == theme["palette"][0]
    assert mapped["a"] == theme["palette"][1]


def test_colors_never_cycle() -> None:
    with pytest.raises(colors.ColorError):
        colors.resolve([str(i) for i in range(9)], None, None)


def test_golden_storyboard_and_requests_are_valid() -> None:
    for kind, name in [
        ("storyboardRequest", "storyboard-request.yaml"),
        ("storyboardRequest", "storyboard-request-with-draft.yaml"),
        ("storyboardResult", "storyboard-golden.yaml"),
    ]:
        assert schema.errors(kind, docio.load(FIXTURE / name)) == [], name


@pytest.mark.parametrize(
    ("kind", "doc", "fragment"),
    [
        (
            "renderRequest",
            {
                "data": {"path": "a.csv", "inline": "x"},
                "source": "s",
                "as_of": "2026-01-01",
                "targets": ["md/document"],
                "question": "q",
            },
            "data",
        ),
        (
            "renderRequest",
            {
                "data": {"path": "a.xlsx"},
                "source": "s",
                "as_of": "2026-01-01",
                "targets": ["md/document"],
                "question": "q",
            },
            "data/path",
        ),
        (
            "renderRequest",
            {
                "data": {"path": "a.csv"},
                "source": "s",
                "as_of": "2026-01-01",
                "targets": ["pdf/document"],
                "question": "q",
            },
            "targets/0",
        ),
        (
            "renderRequest",
            {
                "data": {"path": "a.csv"},
                "source": "s",
                "as_of": "2026-01-01",
                "targets": ["md/document"],
            },
            "(top level)",
        ),
    ],
)
def test_invalid_requests_are_rejected(kind: str, doc: dict, fragment: str) -> None:
    errs = schema.errors(kind, doc)
    assert errs and any(e.startswith(fragment) for e in errs), errs


def test_exclude_requires_values_and_reason() -> None:
    intent = {
        "visual_type": "bar",
        "headline": "h",
        "headline_status": "draft",
        "outlier_handling": {"method": "exclude"},
    }
    doc = {
        "intent": intent,
        "data": {"path": "a.csv"},
        "source": "s",
        "as_of": "2026-01-01",
        "targets": ["md/document"],
    }
    assert schema.errors("renderRequest", doc)


LOANS = data.load({"path": "data/derived/loans_by_quarter.csv"}, FIXTURE)
LINE = {"visual_type": "line", "fields": {"x": "quarter", "y": ["print", "ebook"]}}


@pytest.mark.parametrize(
    "text",
    [
        "Total loans fell 18% during the Q2 renovation",  # total change, rounded
        "Total 1,230 → 1,008 (−18%)",  # row totals
        "E-book loans reached 445",  # a value
        "E-book loans grew 8.5% after Q2 '26",  # change within a series
        "Five quarters of data",  # no numbers
    ],
)
def test_headline_numbers_pass(text: str) -> None:
    status, detail = checks.headline_numbers([text], LOANS, LINE)
    assert status == "pass", detail


@pytest.mark.parametrize(
    "text",
    [
        "Total loans fell 12%",
        "E-book loans reached 450",
        "Loans fell 18.4%",
        # near misses an independent tester found passing too easily (T3b)
        "Total loans fell 22%",  # a share of total: meaningless on a line
        "Print loans fell 25%",  # the print vs e-book gap in one quarter
        "Total loans fell 3%",  # matches a 2.7% rise: wrong direction
    ],
)
def test_headline_numbers_fail(text: str) -> None:
    assert checks.headline_numbers([text], LOANS, LINE)[0] == "fail"


def test_headline_numbers_say_what_they_matched() -> None:
    status, detail = checks.headline_numbers(
        ["Total loans fell 18% in Q2 '26"], LOANS, LINE
    )
    assert status == "pass"
    assert "% change in total" in detail and "Q2 '26" in detail


@pytest.mark.parametrize("text", ["Half wait under 12 minutes", "Half wait under 3"])
def test_raw_values_dont_count_for_large_tables(text: str) -> None:
    waits = data.load({"path": "data/wait_minutes.csv"}, FIXTURE)
    hist = {"visual_type": "histogram", "fields": {"value": "wait_min"}}
    assert checks.headline_numbers([text], waits, hist)[0] == "fail"


def test_absolute_changes_count_as_derivable() -> None:
    members = data.load(
        {"inline": "metric,value,previous\nActive members,48210,46700\n"}, FIXTURE
    )
    text = "Active members rose by 1,510 to 48,210"
    number = {
        "visual_type": "number",
        "fields": {"value": "value", "previous": "previous", "label": "metric"},
    }
    assert checks.headline_numbers([text], members, number)[0] == "pass"


def test_summary_statistics_count_as_derivable() -> None:
    waits = data.load({"path": "data/wait_minutes.csv"}, FIXTURE)
    text = "Half of visitors wait under 8 minutes, but one in ten waits more than 19"
    hist = {"visual_type": "histogram", "fields": {"value": "wait_min"}}
    assert checks.headline_numbers([text], waits, hist)[0] == "pass"


def test_outlier_check_requires_handling() -> None:
    table = data.load({"path": "data/branch_waits.jsonl"}, FIXTURE)
    prof = profile.profile(table)
    intent = {
        "visual_type": "scatter",
        "fields": {"x": "staff_fte", "y": "avg_wait_min"},
        "outlier_handling": {"method": "none_flagged"},
    }
    measures = checks.measures_of(intent)
    assert checks.outliers(prof, measures, intent)[0] == "fail"
    intent["outlier_handling"] = {"method": "accept", "reason": "real"}
    assert checks.outliers(prof, measures, intent)[0] == "pass"
    intent["outlier_handling"] = {"method": "callout"}
    assert checks.outliers(prof, measures, intent)[0] == "fail"
    intent["highlight"] = ["Riverside"]
    assert checks.outliers(prof, measures, intent)[0] == "pass"


@pytest.mark.parametrize(
    ("text", "status"),
    [
        ("82% of visits are helped within 15 minutes", "pass"),
        ("Half of visits get help within 7.8 minutes", "pass"),
        ("A long tail waits 30 minutes or more", "pass"),
        ("Half of visits get help within 12 minutes", "fail"),
        ("90% of visits are helped within 15 minutes", "fail"),
        ("One in ten waits more than 19 minutes", "pass"),
    ],
)
def test_distribution_claims(text: str, status: str) -> None:
    waits = data.load({"path": "data/wait_minutes.csv"}, FIXTURE)
    hist = {"visual_type": "histogram", "fields": {"value": "wait_min"}}
    got, detail = checks.headline_numbers([text], waits, hist)
    assert got == status, detail


WAITS_BY_BRANCH = data.load({"path": "data/branch_waits.jsonl"}, FIXTURE)
SCATTER = {
    "visual_type": "scatter",
    "fields": {"x": "staff_fte", "y": "avg_wait_min", "label": "branch"},
}
OVERVIEW = data.load({"path": "data/branch_overview.json"}, FIXTURE)
TABLE = {"visual_type": "table", "fields": {"columns": ["branch", "visits_k"]}}


@pytest.mark.parametrize(
    ("text", "table", "intent", "status"),
    [  # probes from an independent tester (T3c)
        ("Riverside's average wait is 48 minutes", WAITS_BY_BRANCH, SCATTER, "pass"),
        ("Central's average wait is 48 minutes", WAITS_BY_BRANCH, SCATTER, "fail"),
        ("Riverside's average wait is 14 minutes", WAITS_BY_BRANCH, SCATTER, "fail"),
        ("Riverside waits 8 times the median", WAITS_BY_BRANCH, SCATTER, "fail"),
        ("Central has 212k visits", OVERVIEW, TABLE, "pass"),
        ("Riverside has 21% of all visits", OVERVIEW, TABLE, "fail"),
        ("E-book is 43% of loans in Q3 '26", LOANS, LINE, "pass"),
    ],
)
def test_entity_aware_matching(text, table, intent, status) -> None:
    got, detail = checks.headline_numbers([text], table, intent)
    assert got == status, detail


RAW_VISITS = data.load(
    {"inline": "branch,visits\nCentral,212340\nEastgate,1234567\nNorth,3040000000\n"},
    FIXTURE,
)
RAW_BAR = {"visual_type": "bar", "fields": {"x": "branch", "y": "visits"}}
IN_K = data.load({"inline": "branch,visits\nCentral,212\nEastgate,96\n"}, FIXTURE)
K_BAR = {"visual_type": "bar", "fields": {"x": "branch", "y": "visits"}}


@pytest.mark.parametrize(
    ("text", "table", "intent", "status"),
    [  # the tour (2026-11-14): '212k' was skipped, so any value passed
        ("Central has 212k visits", RAW_VISITS, RAW_BAR, "pass"),  # 212,340
        ("Central has 213k visits", RAW_VISITS, RAW_BAR, "fail"),
        ("Eastgate has 1.2M visits", RAW_VISITS, RAW_BAR, "pass"),
        ("Eastgate has 1.3M visits", RAW_VISITS, RAW_BAR, "fail"),
        ("North has 3bn visits", RAW_VISITS, RAW_BAR, "pass"),
        ("North has 3 bn visits", RAW_VISITS, RAW_BAR, "pass"),
        ("North has 3B visits", RAW_VISITS, RAW_BAR, "pass"),
        ("North has 4bn visits", RAW_VISITS, RAW_BAR, "fail"),
        ("Eastgate has 1.2 million visits", RAW_VISITS, RAW_BAR, "pass"),
        ("Central has 212 thousand visits", RAW_VISITS, RAW_BAR, "pass"),
        # data stored in thousands: the column, names or units must say so
        ("Central has 212k visits", OVERVIEW, TABLE, "pass"),  # visits_k
        ("Central has 300k visits", OVERVIEW, TABLE, "fail"),
        ("Central has 212k visits", IN_K, K_BAR, "fail"),  # unit not declared
        (
            "Central has 212k visits",
            IN_K,
            {**K_BAR, "fields": {**K_BAR["fields"], "names": {"visits": "Visits (k)"}}},
            "pass",
        ),
        (
            "Central has 212k visits",
            IN_K,
            {**K_BAR, "units": "Visits (thousands)"},
            "pass",
        ),
    ],
)
def test_suffixed_numbers_are_checked(text, table, intent, status) -> None:
    got, detail = checks.headline_numbers([text], table, intent)
    assert got == status, detail


def test_suffix_failure_says_how_to_declare_the_unit() -> None:
    got, detail = checks.headline_numbers(["Central has 212k visits"], IN_K, K_BAR)
    assert got == "fail"
    assert "212k (= 212,000; if the data is in thousands" in detail


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("212k", [(212000.0, -3, False, "212k")]),
        ("1.2M", [(1200000.0, -5, False, "1.2M")]),
        ("15m", []),  # lowercase m: minutes or metres, not millions
        ("Q3", []),
    ],
)
def test_numbers_in_scales_suffixes(text, expected) -> None:
    assert checks.numbers_in(text) == expected


WAITS = data.load({"path": "data/wait_minutes.csv"}, FIXTURE)  # 0.3 to 47.5
HIST = {"visual_type": "histogram", "fields": {"value": "wait_min"}}


@pytest.mark.parametrize(
    ("text", "status"),
    [  # C8: a bare threshold passed whenever it was inside the data's range
        ("Some waits are 30 minutes or more", "pass"),
        ("Some waits exceed 40 minutes", "pass"),
        ("Some waits are under 1 minute", "pass"),
        ("Waits reach 60 minutes or more", "fail"),  # none that long
        # universal claims need every value on the stated side
        ("No wait is over 40 minutes", "fail"),
        ("No wait exceeds 40 minutes", "fail"),
        ("Waits never go above 35 minutes", "fail"),
        ("All waits are under 30 minutes", "fail"),
        ("Every wait was within 25 minutes", "fail"),
        ("Waits are at most 20 minutes", "fail"),  # 'most' isn't a share here
        ("Waits are no more than 40 minutes", "fail"),
        ("No wait is over 50 minutes", "pass"),
        ("All waits are under 48 minutes", "pass"),
        ("Waits are at most 47.5 minutes", "pass"),
        ("Waits are no more than 50 minutes", "pass"),
        ("Waits are at least 0.3 minutes", "pass"),
        # share-and-threshold pairs are unchanged
        ("82% wait within 15 minutes", "pass"),
        ("Most wait under 20 minutes", "pass"),
    ],
)
def test_bare_thresholds_follow_their_quantifier(text: str, status: str) -> None:
    got, detail = checks.headline_numbers([text], WAITS, HIST)
    assert got == status, detail


def test_threshold_failure_names_the_counterexample() -> None:
    got, detail = checks.headline_numbers(["No wait is over 40 minutes"], WAITS, HIST)
    assert got == "fail"
    assert "claims no value above 40, but 1 of 300 values of wait_min" in detail
    assert "47.5" in detail


def test_ratio_is_checked_with_its_threshold() -> None:
    waits = data.load({"path": "data/wait_minutes.csv"}, FIXTURE)
    hist = {"visual_type": "histogram", "fields": {"value": "wait_min"}}
    text = "1 in 10 waits more than 25 minutes"
    assert checks.headline_numbers([text], waits, hist)[0] == "fail"


def _bar_request(kind: str, targets: list[str], **extra) -> dict:
    callout = {"kind": kind, "text": "CALLOUT"} | (
        {"x": "Central"} if kind != "note" else {}
    )
    return {
        "intent": {
            "visual_type": "bar",
            "headline": "Central has the most visits",
            "headline_status": "draft",
            "fields": {"x": "branch", "y": "visits"},
            "callouts": [callout],
        },
        "data": {"inline": "branch,visits\nCentral,212\nEastgate,96\nNorth,88\n"},
        "source": "Invented",
        "as_of": "2026-09-30",
        "targets": targets,
        **extra,
    }


@pytest.mark.parametrize("kind", ["point", "rule"])
@pytest.mark.parametrize("target", ["md/document", "html/document", "image/slide"])
def test_bar_point_and_rule_callouts_fail_where_not_drawn(kind, target) -> None:
    """C11: bars drawn by Vega-Lite dropped these, yet the check passed (tour)."""
    res = render.render(_bar_request(kind, [target]), FIXTURE, dry_run=True)
    check = res["checks"]["callouts"]
    assert check["status"] == "fail", check
    assert (
        "bar charts don't draw point or rule callouts yet; use a note"
        in check["detail"]
    )


@pytest.mark.parametrize(
    ("kind", "technique"), [("note", None), ("point", "mermaid"), ("rule", "table")]
)
def test_bar_callouts_pass_where_listed_as_notes(kind, technique, tmp_path) -> None:
    extra = {"technique": {"md/document": technique}} if technique else {}
    req = _bar_request(kind, ["md/document"], out_dir=str(tmp_path), **extra)
    res = render.render(req, FIXTURE)
    assert res["checks"]["callouts"]["status"] == "pass", res["checks"]["callouts"]
    assert "CALLOUT" in res["outputs"]["md/document"]["snippet"]  # shown, as a note


def test_line_point_callouts_still_pass() -> None:
    req = _bar_request("point", ["html/document"])
    req["intent"]["visual_type"] = "line"
    res = render.render(req, FIXTURE, dry_run=True)
    assert res["checks"]["callouts"]["status"] == "pass", res["checks"]["callouts"]
