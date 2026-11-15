#!/usr/bin/env python3
"""plotpoint visualize: command-line entry point.

Usage (paths in a request resolve relative to the request file's folder):
  visualize.py profile REQUEST.yaml    profile every dataset in a storyboard request,
                                       or the data of a render request
  visualize.py profile --data FILE     profile one data file (csv, tsv, json, jsonl)
  visualize.py render REQUEST.yaml     render one visual; prints the result
  visualize.py render --dry-run REQ    run the checks only; writes no files
  visualize.py render --checks-only R  render, but print only checks and notes
  visualize.py check-plan REQ RESULT   dry-run every visual in a storyboard result
  visualize.py validate KIND FILE      KIND: storyboardRequest, storyboardResult,
                                       renderRequest or renderResult

Requires: pyyaml, jsonschema, vl-convert-python (scripts/requirements.txt).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ppviz import data, docio, profile, render, schema  # noqa: E402  (after the path setup)


def _load(path: Path) -> dict:
    return docio.load(path)


def _dump(doc: object) -> None:
    sys.stdout.write(docio.dump_yaml(doc))


def cmd_profile(args: argparse.Namespace) -> int:
    if args.data:
        path = Path(args.data)
        _dump(profile.profile(data.load({"path": path.name}, path.parent), path.stem))
        return 0
    req_path = Path(args.request)
    req = _load(req_path)
    if "data" in req and "datasets" not in req:  # a render request (mode C)
        schema.check("renderRequest", req)
        _dump(profile.profile(data.load(req["data"], req_path.parent), req.get("id")))
        return 0
    schema.check("storyboardRequest", req)
    out = [
        profile.profile(data.load(d["data"], req_path.parent), d["id"])
        for d in req["datasets"]
    ]
    _dump(out)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    req_path = Path(args.request)
    result = render.render(_load(req_path), req_path.parent, dry_run=args.dry_run)
    if args.checks_only:  # the full result is in <out_dir>/<id>.result.json
        _dump(
            {"id": result["id"], "checks": result["checks"], "notes": result["notes"]}
        )
    else:
        _dump(result)
    failed = [k for k, v in result["checks"].items() if v["status"] == "fail"]
    if failed:
        sys.stderr.write(f"checks failed: {', '.join(failed)}\n")
        return 1
    return 0


def cmd_check_plan(args: argparse.Namespace) -> int:
    req_path, res_path = Path(args.request), Path(args.result)
    req, res = _load(req_path), _load(res_path)
    schema.check("storyboardRequest", req)
    schema.check("storyboardResult", res)
    report, failed = {}, []
    for r in render.plan_requests(req, res):
        out = render.render(r, req_path.parent, dry_run=True)
        report[r["id"]] = {
            "checks": out["checks"],
            "text_outputs": {t: o["snippet"] for t, o in out["outputs"].items()},
        }
        failed += [
            f"{r['id']}.{k}" for k, v in out["checks"].items() if v["status"] == "fail"
        ]
    _dump(report)
    if failed:
        sys.stderr.write(f"checks failed: {', '.join(failed)}\n")
        return 1
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    errs = schema.errors(args.kind, _load(Path(args.file)))
    if errs:
        sys.stderr.write("\n".join(errs) + "\n")
        return 1
    sys.stdout.write(f"valid {args.kind}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Output holds non-ASCII text (→, –, names); Windows consoles and pipes default
    # to a legacy code page that can't encode it.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        prog="visualize.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("profile")
    p.add_argument("request", nargs="?")
    p.add_argument("--data")
    p.set_defaults(func=cmd_profile)
    r = sub.add_parser("render")
    r.add_argument("request")
    r.add_argument("--dry-run", action="store_true", help="checks only")
    r.add_argument(
        "--checks-only", action="store_true", help="print only checks and notes"
    )
    r.set_defaults(func=cmd_render)
    c = sub.add_parser("check-plan")
    c.add_argument("request")
    c.add_argument("result")
    c.set_defaults(func=cmd_check_plan)
    v = sub.add_parser("validate")
    v.add_argument("kind", choices=schema.KINDS)
    v.add_argument("file")
    v.set_defaults(func=cmd_validate)
    args = parser.parse_args(argv)
    if args.cmd == "profile" and not (args.request or args.data):
        parser.error("profile needs a storyboard request or --data FILE")
    try:
        return args.func(args)
    except (data.DataError, schema.SchemaError, render.RenderError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
