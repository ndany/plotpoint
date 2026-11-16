#!/usr/bin/env python3
"""Record a blind model run of the visualize skill (docs/testing.md, D-34).

Usage:
  scripts/record_run.py TEST [--model sonnet] [--budget 5] [--deps venv|none]
                             [--storyboard FILE] [--scratch DIR] [--dry-run]

TEST is one of T1 (mode A), T2 (mode B), T3 (mode C), D (render a plan, needs
--storyboard) or SETUP (missing dependencies: run with --deps none).

It copies the fixture without the answer files, and the plugin without
DESIGN.md, into a scratch folder outside the repo; runs a headless `claude -p`
session there with the blind brief and only that plugin loaded; audits the
transcript for anything opened outside the scratch folder; and saves the
result, the session's notes and the audit to
tests/fixtures/library-review/runs/<date>-<test>/. Scoring is pytest's job
(tests/test_storyboard_runs.py). Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "tests" / "fixtures" / "library-review"
PLUGIN = REPO / "plugins" / "plotpoint"
RUNS = FIXTURE / "runs"

# Never copied into the scratch folder: the answers and earlier findings.
ANSWERS = {"storyboard-golden.yaml", "expected.md", "render-data.yaml", "runs"}
# Flagged if any tool call mentions them, wherever they are.
FORBIDDEN = [
    "storyboard-golden",
    "expected.md",
    "render-data",
    "DESIGN.md",
    "/runs/",
    "docs/plans",
    "walkthrough-holdout",
    "FINDINGS",
]

BRIEF = """You are testing a Claude Code skill, plotpoint:visualize, as a first-time
user would. Work only inside the current folder. Do not open anything outside
it: not the plotpoint repository, its docs/ or tests/ folders, any runs/
folder, DESIGN.md, docs/plans/, storyboard-golden.yaml, expected.md,
render-data.yaml, or notes from earlier tests. The skill's own files (loaded
from the plugin) are fine to read. If you open anything else, say so in
notes.md.

Task: {task}

When done, write notes.md in this folder with: what you produced, which
headlines are drafts and why, decisions the caller must make, anything you
opened outside this folder (or "none"), and a "Skill feedback" section: what
in the skill's instructions or tools was unclear, wrong or missing."""

TASKS = {
    "T1": (
        "Use plotpoint to storyboard storyboard-request-with-draft.yaml and say "
        "what to change in the draft. Save the result as storyboard-result.yaml."
    ),
    "T2": (
        "Use plotpoint to storyboard storyboard-request.yaml. Save the result as "
        "storyboard-result.yaml."
    ),
    "T3": (
        "For each of the five datasets behind questions q1-q4 in "
        "storyboard-request.yaml (merged loans: data/derived/loans_by_quarter.csv; "
        "members; branch_waits; branch_overview; wait_minutes), write a render "
        "request with its question (and takeaway, if the question has one) but "
        "no intent, as r1.yaml to r5.yaml, targets md/document and "
        "html/document. Then use plotpoint to render each one (mode C): it "
        "decides the chart, headline and emphasis. Look at each result."
    ),
    "D": (
        "Use plotpoint to render every visual in storyboard-result.yaml to "
        "Markdown and HTML. Look at each result."
    ),
    "SETUP": (
        "Use plotpoint to render requests/v1-line.yaml to Markdown. If something "
        "is missing, follow the skill's instructions."
    ),
}
# What each test saves from the scratch folder, besides notes.md.
OUTPUTS = {
    "T1": ["storyboard-result.yaml"],
    "T2": ["storyboard-result.yaml"],
    "T3": [f"r{i}.yaml" for i in range(1, 6)],
    "D": [],
    "SETUP": [],
}
TOOLS = "Bash Read Write Edit Glob Grep Skill"


def run_dir(test: str, today: str) -> Path:
    base = RUNS / f"{today}-{test}"
    for suffix in ["", *"bcdefgh"]:
        d = Path(f"{base}{suffix}")
        if not d.exists():
            return d
    raise SystemExit(f"too many runs for {test} today")


def make_scratch(scratch: Path, test: str, storyboard: Path | None) -> Path:
    if scratch.exists():
        shutil.rmtree(scratch)
    # requests/ holds reference intents (answers for T2, T3); SETUP needs one
    leave_out = ANSWERS if test == "SETUP" else ANSWERS | {"requests"}
    shutil.copytree(FIXTURE, scratch, ignore=lambda d, names: leave_out & set(names))
    plugin = scratch / ".plugin" / "plotpoint"
    shutil.copytree(
        PLUGIN,
        plugin,
        ignore=shutil.ignore_patterns("DESIGN.md", "__pycache__", ".pytest_cache"),
    )
    if test == "D":
        if storyboard is None:
            raise SystemExit("D needs --storyboard (e.g. a T2 run's result)")
        shutil.copy(storyboard, scratch / "storyboard-result.yaml")
    return plugin


def command(args: argparse.Namespace, plugin: Path) -> list[str]:
    exe = shutil.which("claude")
    if exe is None:
        raise SystemExit("claude (Claude Code CLI) isn't on PATH")
    return [
        exe,
        "-p",
        BRIEF.format(task=TASKS[args.test]),
        "--plugin-dir",
        str(plugin),
        "--setting-sources",
        "project,local",  # not the user's settings, hooks or plugins
        "--model",
        args.model,
        "--max-budget-usd",
        str(args.budget),
        "--allowedTools",
        TOOLS,
        "--permission-mode",
        "acceptEdits",
        "--output-format",
        "stream-json",
        "--verbose",
        "--no-session-persistence",
    ]


def _bootstrap():
    """The skill's own bootstrap module: where it looks for its venv."""
    sys.path.insert(0, str(PLUGIN / "skills" / "visualize" / "scripts"))
    import bootstrap  # stdlib only; found via the path set just above

    return bootstrap


def check_dependencies(deps: str) -> None:
    """Runs see the machine as a user would. With `venv`, the documented
    one-time setup must be done (the per-user cache venv: a shell alias for
    python3 can override PATH, so a venv on PATH isn't enough). With `none`,
    neither the cache venv nor uv may exist."""
    bootstrap = _bootstrap()
    venv = bootstrap.venv_python()
    if deps == "venv" and not venv.exists():
        raise SystemExit(
            "do the skill's one-time setup first (the cache venv), then re-run:\n"
            + bootstrap.setup_message([])
        )
    if deps == "none" and (venv.exists() or shutil.which("uv")):
        raise SystemExit(
            f"SETUP needs a machine without uv and without {venv.parent.parent}; "
            "run it where the skill has never been set up"
        )


def environment(deps: str) -> dict[str, str]:
    env = dict(os.environ)
    env.pop("VIRTUAL_ENV", None)  # no venv borrowed from this shell
    env["PATH"] = os.pathsep.join(
        p for p in env.get("PATH", "").split(os.pathsep) if ".venv" not in p
    )
    return env


# Tool input fields that open, list or run something (not text being written).
ACCESS = ("file_path", "path", "notebook_path", "pattern", "glob", "command")


# An absolute or home path (a bare "/" is usually division in a script), and a
# shell command pointed at the root or home folder.
PATHLIKE = re.compile(r"^(~$|~/|/[\w.])")
ROOT_WALK = re.compile(r"\b(find|ls|cd|du|tree)\s+(-\S+\s+)*[/~](\s|$)")


def audit(transcript: Path, scratch: Path) -> dict:
    """What the session loaded and every tool call that reached outside the
    scratch folder or named an answer file. Only what a tool opens, lists or
    runs counts, not text it writes."""
    plugins, outside, forbidden, cost, turns = [], [], [], None, None
    allowed = (str(scratch.resolve()), str(scratch), "/dev/null")
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            plugins = ev.get("plugins", [])
        if ev.get("type") == "result":
            cost, turns = ev.get("total_cost_usd"), ev.get("num_turns")
        if ev.get("type") != "assistant":
            continue
        for block in ev.get("message", {}).get("content", []):
            if block.get("type") != "tool_use":
                continue
            inp = block.get("input", {})
            text = " ".join(str(inp[k]) for k in ACCESS if k in inp)
            call = f"{block.get('name')}: {text[:200]}"
            if any(f in text for f in FORBIDDEN):
                forbidden.append(call)
            tokens = text.replace('"', " ").replace("'", " ").replace("=", " ")
            if ROOT_WALK.search(text) or any(
                PATHLIKE.match(t) and not t.startswith(allowed) for t in tokens.split()
            ):
                outside.append(call)
    return {
        "plugins": plugins,
        "outside": outside,
        "forbidden": forbidden,
        "cost_usd": cost,
        "turns": turns,
    }


def private_free(text: str, scratch: Path) -> str:
    """Saved files go in the repo: no scratch or home paths (CLAUDE.md)."""
    for path in (str(scratch.resolve()), str(scratch)):
        text = text.replace(path, "<scratch>")
    return text.replace(str(Path.home()), "~")


def write_notes(
    dest: Path, test: str, args: argparse.Namespace, report: dict, scratch: Path
) -> None:
    session = dest / "notes.md"
    body = session.read_text(encoding="utf-8") if session.exists() else ""
    plugins = (
        ", ".join(f"{p.get('name')} ({p.get('path')})" for p in report["plugins"])
        or "none reported"
    )
    lines = [
        f"# {dest.name}: recorded by scripts/record_run.py",
        "",
        f"- Test: {test}; model: {args.model}; dependencies: {args.deps}",
        f"- Turns: {report['turns']}; cost (client estimate): "
        + (f"${report['cost_usd']:.2f}" if report["cost_usd"] is not None else "n/a"),
        f"- Plugins loaded: {plugins}",
        f"- Tool calls naming an answer file: {len(report['forbidden'])}",
        f"- Tool calls with a path outside the scratch folder: "
        f"{len(report['outside'])}",
        "",
    ]
    for title, key in (("Answer files named", "forbidden"), ("Outside", "outside")):
        if report[key]:
            lines += [f"### {title}", "", *[f"- `{c}`" for c in report[key]], ""]
    lines += ["## Session notes", "", body or "(the session wrote no notes.md)"]
    session.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    for f in dest.iterdir():
        f.write_text(private_free(f.read_text(encoding="utf-8"), scratch), "utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("test", choices=sorted(TASKS))
    p.add_argument("--model", default="sonnet")
    p.add_argument("--budget", type=float, default=5.0, help="USD cap per run")
    p.add_argument("--deps", choices=["venv", "none"], default=None)
    p.add_argument("--storyboard", type=Path)
    p.add_argument("--scratch", type=Path, help="default: ../plotpoint-runs/<run>")
    p.add_argument("--dry-run", action="store_true", help="print, don't run")
    args = p.parse_args()
    args.deps = args.deps or ("none" if args.test == "SETUP" else "venv")
    today = dt.date.today().isoformat()
    dest = run_dir(args.test, today)
    scratch = (args.scratch or REPO.parent / "plotpoint-runs" / dest.name).resolve()
    if REPO in scratch.parents:
        raise SystemExit("the scratch folder must be outside the repo")
    check_dependencies(args.deps)
    plugin = make_scratch(scratch, args.test, args.storyboard)
    cmd = command(args, plugin)
    if args.dry_run:
        print(f"scratch: {scratch}\nsave to: {dest}\n" + " ".join(cmd[:2]) + " ...")
        return 0
    transcript = scratch / "transcript.jsonl"
    with transcript.open("w", encoding="utf-8") as out:
        proc = subprocess.run(  # noqa: S603 - the claude CLI, our own arguments
            cmd,
            cwd=scratch,
            env=environment(args.deps),
            stdin=subprocess.DEVNULL,
            stdout=out,
            check=False,
        )
    report = audit(transcript, scratch)
    dest.mkdir(parents=True)
    for name in ["notes.md", *OUTPUTS[args.test]]:
        if (scratch / name).exists():
            shutil.copy(scratch / name, dest / name)
    write_notes(dest, args.test, args, report, scratch)
    print(f"saved {dest.relative_to(REPO)}; transcript in {transcript}")
    print(json.dumps({k: v for k, v in report.items() if k != "plugins"}, indent=1))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
