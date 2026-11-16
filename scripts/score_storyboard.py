#!/usr/bin/env python3
"""Score a storyboard result for the library-review fixture against E1-E12.

    .venv/bin/python scripts/score_storyboard.py path/to/storyboard-result.yaml

Expectations: tests/fixtures/library-review/expected.md. Exit 1 if any miss.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    sys.path[:0] = [
        str(REPO / "tests"),
        str(REPO / "plugins/plotpoint/skills/visualize/scripts"),
    ]
    from storyboard_expectations import load_and_evaluate

    results = load_and_evaluate(Path(argv[0]))
    for key, (ok, detail) in sorted(results.items(), key=lambda kv: int(kv[0][1:])):
        print(f"{'pass' if ok else 'MISS'}  {key}  {detail}")
    missed = [k for k, (ok, _) in results.items() if not ok]
    print(f"\n{len(results) - len(missed)}/{len(results)} expectations met")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
