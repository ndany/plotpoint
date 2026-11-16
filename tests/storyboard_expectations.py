"""Expectations E1-E12 for storyboard results on the library-review fixture.

See tests/fixtures/library-review/expected.md. Used for the reference answer
and for recorded runs (tests/fixtures/library-review/runs/).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ppviz import checks, data, docio, schema

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "library-review"
RENDER_DATA = {
    # dataset ids -> the file a visual using them renders from
    frozenset({"loans_print", "loans_ebook"}): {
        "path": "data/derived/loans_by_quarter.csv"
    },
    frozenset({"loans_print"}): {"path": "data/loans_print.csv"},
    frozenset({"loans_ebook"}): {"path": "data/loans_ebook.tsv"},
    frozenset({"members"}): {
        "inline": "metric,value,previous\nActive members,48210,46700\n"
    },
    frozenset({"branch_waits"}): {"path": "data/branch_waits.jsonl"},
    frozenset({"branch_overview"}): {"path": "data/branch_overview.json"},
    frozenset({"wait_minutes"}): {"path": "data/wait_minutes.csv"},
}


def _for_question(result: dict[str, Any], q: str) -> list[dict[str, Any]]:
    return [v for v in result["visuals"] if q in v["questions"]]


def evaluate(result: dict[str, Any]) -> dict[str, tuple[bool, str]]:
    """Return {expectation id: (passed, detail)}."""
    out: dict[str, tuple[bool, str]] = {}
    errs = schema.errors("storyboardResult", result)
    out["E1"] = (not errs, "; ".join(errs[:3]))
    if errs:
        return out
    visuals = result["visuals"]
    recs = result["recommendations"]

    merged = [
        v for v in visuals if {"loans_print", "loans_ebook"} <= set(v["datasets"])
    ]
    out["E2"] = (bool(merged), f"{len(merged)} visual(s) use both loans datasets")

    first = visuals[0] if visuals else None
    ok = bool(first and "q1" in first["questions"] and first["placement"] == "summary")
    out["E3"] = (
        ok,
        f"first visual: {first and first['id']} {first and first['questions']}",
    )

    cut = any(r["kind"] == "cut" and "cafe_sales" in r["affects"] for r in recs)
    used = any("cafe_sales" in v["datasets"] for v in visuals)
    out["E4"] = (cut and not used, f"cut recommended={cut}, used={used}")

    ov = [v for v in visuals if "branch_overview" in v["datasets"]]
    demoted = any(r["kind"] == "demote" for r in recs) and all(
        v["intent"]["visual_type"] == "table" for v in ov
    )
    as_table = bool(ov) and all(v["intent"]["visual_type"] == "table" for v in ov)
    out["E5"] = (
        as_table or demoted,
        f"branch_overview as {[v['intent']['visual_type'] for v in ov]}",
    )

    waits = [
        v
        for v in visuals
        if "branch_waits" in v["datasets"]
        and v["intent"]["visual_type"] not in ("table", "sentence", "number")
    ]  # only charts plot values, so only charts need outlier handling
    good = []
    for v in waits:
        it = v["intent"]
        h = it.get("outlier_handling") or {}
        hs = h if isinstance(h, list) else [h]
        wait = [x for x in hs if x.get("column") in (None, "avg_wait_min")]
        method = wait[0].get("method") if wait else None
        named = "Riverside" in [str(h) for h in it.get("highlight") or []] or any(
            "Riverside" in c["text"] for c in it.get("callouts") or []
        )
        good.append(method not in (None, "none_flagged") and named)
    out["E6"] = (
        bool(waits) and all(good),
        f"{len(waits)} branch_waits visual(s): {good}",
    )

    drafts = [
        v["intent"]["headline_status"] == "draft"
        for q in ("q2", "q4")
        for v in _for_question(result, q)
    ]
    out["E7"] = (bool(drafts) and all(drafts), f"q2/q4 draft flags: {drafts}")

    detail = [  # a one-line summary for decision-makers is allowed on top
        (v["id"], v["audience"], v["placement"])
        for q in ("q3", "q4")
        for v in _for_question(result, q)
        if not (
            v["placement"] == "summary"
            and v["intent"]["visual_type"] in ("sentence", "number")
        )
    ]
    ok = bool(detail) and all(
        a == ["managers"] and p in ("body", "appendix") for _, a, p in detail
    )
    out["E8"] = (ok, str(detail))

    targets = set(result.get("_targets") or ["md/document", "html/document"])
    missing = [v["id"] for v in visuals if not targets <= set(v["renderings"])]
    out["E9"] = (not missing, f"visuals missing a target's rendering: {missing}")

    bad = [
        v["id"]
        for v in visuals
        if any(r["technique"] == "mermaid" for r in v["renderings"].values())
        and v["intent"]["visual_type"] not in ("line", "bar")
    ]
    out["E10"] = (not bad, f"mermaid on unsupported types: {bad}")

    failures = []
    for v in visuals:
        spec = RENDER_DATA.get(frozenset(v["datasets"]))
        if spec is None:
            continue
        table = data.load(spec, FIXTURE)
        it = v["intent"]
        texts = [it["headline"]] + [c["text"] for c in it.get("callouts") or []]
        status, why = checks.headline_numbers(texts, table, it)
        if status == "fail":
            failures.append(f"{v['id']}: {why}")
    out["E11"] = (not failures, "; ".join(failures) or "all derivable")

    request = docio.load(FIXTURE / "storyboard-request.yaml")
    given = {q["id"]: q["takeaway"] for q in request["questions"] if q.get("takeaway")}
    edited = []
    for v in visuals:
        takes = {given[q] for q in v["questions"] if q in given}
        if len(takes) == 1:
            status, _ = checks.takeaway(v["intent"], takes.pop())
            if status == "fail":
                edited.append(v["id"])
    out["E12"] = (
        not edited,
        f"confirmed headlines that edit the caller's takeaway: {edited}",
    )
    return out


def load_and_evaluate(path: Path) -> dict[str, tuple[bool, str]]:
    return evaluate(docio.load(path))
