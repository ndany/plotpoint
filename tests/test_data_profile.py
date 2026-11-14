"""Data loading (every supported form) and profiling, including outliers (T6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import FIXTURE
from ppviz import data, profile


@pytest.mark.parametrize(
    ("path", "rows", "number_col"),
    [
        ("data/loans_print.csv", 5, "print"),
        ("data/loans_ebook.tsv", 5, "ebook"),
        ("data/branch_overview.json", 12, "visits_k"),
        ("data/branch_waits.jsonl", 12, "avg_wait_min"),
    ],
)
def test_loads_every_file_format(path: str, rows: int, number_col: str) -> None:
    table = data.load({"path": path}, FIXTURE)
    assert len(table.rows) == rows
    assert table.types[number_col] == "number"


def test_inline_csv_matches_file_form(tmp_path: Path) -> None:
    text = "quarter,print\nQ1,790\nQ2,598\n"
    (tmp_path / "d.csv").write_text(text)
    inline = data.load({"inline": text})
    from_file = data.load({"path": "d.csv"}, tmp_path)
    assert inline.rows == from_file.rows
    assert inline.types == from_file.types == {"quarter": "text", "print": "number"}


def test_type_inference() -> None:
    t = data.load(
        {"inline": "month,label,value,rate\n2026-01,a,3,0.5\n2026-02,b,,1.5\n"}
    )
    assert t.types == {
        "month": "date",
        "label": "text",
        "value": "number",
        "rate": "number",
    }
    assert t.rows[1]["value"] is None


@pytest.mark.parametrize(
    "spec",
    [{"path": "missing.csv"}, {"path": "data/x.xlsx"}, {}],
)
def test_bad_data_raises(spec: dict) -> None:
    with pytest.raises(data.DataError):
        data.load(spec, FIXTURE)


def test_profile_flags_the_outlier_and_keeps_its_row() -> None:
    p = profile.profile(
        data.load({"path": "data/branch_waits.jsonl"}, FIXTURE), "waits"
    )
    wait = next(c for c in p["columns"] if c["name"] == "avg_wait_min")
    assert wait["outliers"]["count"] == 1
    assert wait["outliers"]["values"] == [48]
    assert any("avg_wait_min" in f and "outlier" in f for f in p["flags"])
    maxima = [e["row"] for e in p["extreme_rows"] if e["column"] == "avg_wait_min"]
    assert {"branch": "Riverside", "staff_fte": 4.5, "avg_wait_min": 48} in maxima


def test_sample_includes_extremes_and_is_deterministic() -> None:
    table = data.load({"path": "data/wait_minutes.csv"}, FIXTURE)
    a, b = profile.profile(table), profile.profile(table)
    assert a == b
    biggest = max(table.numeric("wait_min"))
    assert any(r["wait_min"] == biggest for r in a["sample_rows"])
    assert len(a["sample_rows"]) <= 15


def test_dominance_flag() -> None:
    t = data.load({"inline": "k,v\na,1\nb,2\nc,2\nd,3\ne,200\n"})
    v = next(c for c in profile.profile(t)["columns"] if c["name"] == "v")
    assert v["dominance_flag"] is True


def test_profile_is_small_for_large_data() -> None:
    import json

    table = data.load({"path": "data/wait_minutes.csv"}, FIXTURE)
    assert len(json.dumps(profile.profile(table))) < 3000
