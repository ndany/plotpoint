# visualize

The skill in the plotpoint plugin (`plotpoint:visualize`). Its goal is better
**storytelling with data**: it plans the visual story of a write-up and draws
each visual so the takeaway is obvious.

| Operation | What it does |
| --- | --- |
| **storyboard** | Across a whole write-up: which visuals, in what order, for which audience and placement; what to merge, demote or cut; one color map; the technique per format |
| **render** | One visual to Markdown, HTML fragments and slide images, with a takeaway headline, emphasis, callouts, and checked numbers |

## Folder

| Path | Contents |
| --- | --- |
| `SKILL.md` | What Claude follows |
| `references/` | Spec, targets and layouts, profiling, storyboarding, chart chooser, composition, fallback rendering |
| `schemas/plotpoint.schema.json` | Request and result contract |
| `config/` | Layout presets, theme, capacity limits |
| `scripts/visualize.py` | Command line: `profile`, `render` (with `--dry-run`), `validate` |
| `scripts/bootstrap.py` | Dependency check before the engine loads; exit code 3 and setup commands if anything is missing |
| `scripts/ppviz/` | The engine: load, profile, shape, draw, check |
| `DESIGN.md` | Rationale and test findings |

## Requirements

Python 3.11+ and three packages (jsonschema, PyYAML, vl-convert-python;
`scripts/requirements.txt`). With [uv](https://docs.astral.sh/uv/), `uv run
scripts/visualize.py ...` installs them itself; without it, `visualize.py` stops
with exit code 3 and prints the commands for your OS (a venv in the per-user
cache folder); once it exists the script re-runs itself with it. Optional: the Mermaid CLI, to test Mermaid output.
Recommended: Anthropic's dataviz skill.

Callers: start with the repository's
[guide](../../../../docs/guide/using-plotpoint.md).
