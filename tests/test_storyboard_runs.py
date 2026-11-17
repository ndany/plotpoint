"""Storyboard expectations (E1-E12) on the reference answer and recorded runs.

Model-behavior runs (T1 mode A, T2 mode B, T3 mode C) can't run in CI: they're
produced by running the skill and saved under
tests/fixtures/library-review/runs/. This test keeps every saved run honest.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from conftest import FIXTURE
from ppviz import docio
from storyboard_expectations import evaluate, load_and_evaluate

RUNS = sorted((FIXTURE / "runs").glob("*/storyboard-result.yaml"))


def test_reference_answer_meets_every_expectation() -> None:
    results = load_and_evaluate(FIXTURE / "storyboard-golden.yaml")
    failed = {k: d for k, (ok, d) in results.items() if not ok}
    assert not failed, failed
    assert len(results) == 12


def _golden_with(change) -> dict:
    result = copy.deepcopy(docio.load(FIXTURE / "storyboard-golden.yaml"))
    change(result)
    return result


def test_e8_fails_a_widened_audience() -> None:
    """D-35: widening a q3 visual's audience in the plan is a miss."""

    def widen(result: dict) -> None:
        v3 = next(v for v in result["visuals"] if v["id"] == "v3")
        v3["audience"] = ["board", "managers"]
        v3["placement"] = "summary"

    ok, _ = evaluate(_golden_with(widen))["E8"]
    assert not ok


def test_e8_fails_a_board_summary_added_to_the_plan() -> None:
    """D-35: a board summary sentence is proposed (add-summary), not added."""
    t2b = docio.load(FIXTURE / "runs/2026-11-01-T2b/storyboard-result.yaml")
    sentence = next(v for v in t2b["visuals"] if v["id"] == "v3")
    assert sentence["intent"]["visual_type"] == "sentence"

    def add(result: dict) -> None:
        result["visuals"].append({**sentence, "id": "v9"})

    ok, _ = evaluate(_golden_with(add))["E8"]
    assert not ok


@pytest.mark.parametrize("run", RUNS, ids=[r.parent.name for r in RUNS])
def test_recorded_storyboard_run(run: Path) -> None:
    results = load_and_evaluate(run)
    failed = {k: d for k, (ok, d) in results.items() if not ok}
    allowed = _known_misses(run.parent)
    unexpected = {k: d for k, d in failed.items() if k not in allowed}
    assert not unexpected, unexpected


def _known_misses(run_dir: Path) -> set[str]:
    """Expectation ids a run is recorded as missing (see the run's README)."""
    f = run_dir / "known-misses.txt"
    if not f.exists():
        return set()
    return {line.split()[0] for line in f.read_text().splitlines() if line.strip()}
