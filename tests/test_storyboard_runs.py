"""Storyboard expectations (E1-E11) on the reference answer and recorded runs.

Model-behavior runs (T1 mode A, T2 mode B, T3 mode C) can't run in CI: they're
produced by running the skill and saved under
tests/fixtures/library-review/runs/. This test keeps every saved run honest.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import FIXTURE
from storyboard_expectations import load_and_evaluate

RUNS = sorted((FIXTURE / "runs").glob("*/storyboard-result.yaml"))


def test_reference_answer_meets_every_expectation() -> None:
    results = load_and_evaluate(FIXTURE / "storyboard-golden.yaml")
    failed = {k: d for k, (ok, d) in results.items() if not ok}
    assert not failed, failed
    assert len(results) == 11


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
