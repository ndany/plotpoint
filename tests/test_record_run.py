"""scripts/record_run.py: the blind scratch copy and the transcript audit."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "record_run", REPO / "scripts" / "record_run.py"
)
record_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(record_run)


@pytest.mark.parametrize("test", ["T1", "T2", "T3", "SETUP"])
def test_scratch_copy_leaves_out_the_answers(tmp_path: Path, test: str) -> None:
    scratch = tmp_path / "s"
    plugin = record_run.make_scratch(scratch, test, None)
    names = {p.name for p in scratch.rglob("*")}
    assert not names & {"storyboard-golden.yaml", "expected.md", "render-data.yaml"}
    assert not (scratch / "runs").exists()
    assert (plugin / "skills" / "visualize" / "SKILL.md").exists()
    assert not (plugin / "skills" / "visualize" / "DESIGN.md").exists()
    assert (scratch / "requests").exists() == (test == "SETUP")
    assert (scratch / "storyboard-request.yaml").exists()


def test_plan_run_needs_a_storyboard(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        record_run.make_scratch(tmp_path / "s", "D", None)


def _event(name: str, **inp) -> str:
    block = {"type": "tool_use", "name": name, "input": inp}
    return json.dumps({"type": "assistant", "message": {"content": [block]}})


def test_audit_flags_outside_paths_and_answer_files(tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    lines = [
        json.dumps({"type": "system", "subtype": "init", "plugins": [{"name": "p"}]}),
        _event("Read", file_path=str(scratch / "data" / "a.csv")),  # fine
        _event("Bash", command=f"ls {scratch} > /dev/null"),  # fine
        _event("Read", file_path="/elsewhere/notes.md"),  # outside
        _event("Glob", pattern="**/storyboard-golden.yaml"),  # answer file
        _event("Bash", command=f"cd {scratch} && python3 -c 'print(4 / 2)'"),  # fine
        _event("Bash", command="find ~ -maxdepth 4 -iname '*plot*'"),  # outside
        _event("Bash", command="find / -maxdepth 6 -name x"),  # outside
        _event("Write", file_path=str(scratch / "notes.md"), content="see ~/x"),
        json.dumps({"type": "result", "total_cost_usd": 1.5, "num_turns": 9}),
    ]
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join(lines) + "\nnot json\n", encoding="utf-8")
    report = record_run.audit(transcript, scratch)
    assert report["plugins"] == [{"name": "p"}]
    assert len(report["outside"]) == 3, report["outside"]
    assert "/elsewhere/notes.md" in report["outside"][0]
    assert len(report["forbidden"]) == 1 and "golden" in report["forbidden"][0]
    assert (report["cost_usd"], report["turns"]) == (1.5, 9)


def test_run_dir_adds_a_suffix_when_taken(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(record_run, "RUNS", tmp_path)
    (tmp_path / "2026-11-16-T2").mkdir()
    assert record_run.run_dir("T2", "2026-11-16").name == "2026-11-16-T2b"
    assert record_run.run_dir("T1", "2026-11-16").name == "2026-11-16-T1"


def test_saved_files_carry_no_home_or_scratch_path(tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    text = f"ran {scratch}/data/a.csv with {Path.home()}/.venv/bin/python"
    out = record_run.private_free(text, scratch)
    assert out == "ran <scratch>/data/a.csv with ~/.venv/bin/python"


def test_dependency_check_matches_the_test(tmp_path: Path, monkeypatch) -> None:
    bootstrap = record_run._bootstrap()
    missing, present = tmp_path / "none" / "python", tmp_path / "python"
    present.write_text("")
    monkeypatch.setattr(record_run.shutil, "which", lambda _: None)
    monkeypatch.setattr(bootstrap, "venv_python", lambda: missing)
    with pytest.raises(SystemExit, match="one-time setup"):
        record_run.check_dependencies("venv")
    record_run.check_dependencies("none")  # a fresh machine: SETUP can run
    monkeypatch.setattr(bootstrap, "venv_python", lambda: present)
    record_run.check_dependencies("venv")
    with pytest.raises(SystemExit, match="never been set up"):
        record_run.check_dependencies("none")
