# CLAUDE.md — plotpoint

## What this repo is

A Claude Code plugin marketplace containing one plugin, `plotpoint`, with one
skill, **`visualize`** (`plotpoint:visualize`). Its purpose is **better
storytelling with data**: it storyboards a write-up's visuals (order, merge,
demote, cut, audience placement, one color map, technique per format) and
renders each visual to Markdown, HTML and slide images with checked numbers.

## Read first

`HANDOFF.md` (state, next steps, backlog), then `docs/architecture.md`.

## Architecture in brief

| Layer | Where | Rule |
| --- | --- | --- |
| Instructions | `skills/visualize/SKILL.md`, `references/` | Judgment only: story, form, headline, outlier handling |
| Contract | `schemas/plotpoint.schema.json` | Every request and result validates against it |
| Engine | `scripts/ppviz/` | Deterministic: load, profile, shape, draw, check |
| Configuration | `config/*.yaml` | Layout presets, theme, capacity; tune here, not in code |

Boundaries: plotpoint advises, the caller decides; plotpoint never invents a
conclusion (no `takeaway` → `draft` headline). Rendering style follows the
dataviz skill; don't add color or mark rules to the instructions outside
`references/fallback-rendering.md`; change `config/theme.yaml` instead and
re-validate the palette with dataviz's `validate_palette.py`.

## Non-negotiable conventions

### Runtime docs live in the skill folder

An installed skill can only see its own folder. Anything Claude needs at run
time goes in `plugins/plotpoint/skills/visualize/`. Repo docs link to it; never
copy it.

### Portability

- `SKILL.md` frontmatter: only `name`, `description`, `license`, `compatibility`,
  `metadata`, `allowed-tools` (enforced by `scripts/check_frontmatter.py`).
- Skill folder name equals the frontmatter `name`.
- No Claude Code-only features in `SKILL.md`.
- Scripts: Python 3.11+, dependencies only from `scripts/requirements.txt`.

### Public-ready and private-free

Never commit employer, client or organization names, real metric values,
names of other private projects, or absolute home paths (use `~`). Examples
and fixtures use invented data, labelled as such. `scripts/check-privacy.sh`
enforces paths plus patterns in the gitignored `.privacy-patterns.local`.
Commit messages, issues and PRs aren't scanned: review them by eye.

### Attribution

A new source → update `ACKNOWLEDGMENTS.md` and `NOTICE` in the same change.
Paraphrase; if copying text, code or data, check its license first and log it in
`docs/decisions.md`.

### Quality gates

```bash
scripts/check-all.sh
```

markdownlint, ruff (lint + format), shellcheck, pytest (engine, schemas, checks,
renders, recorded runs), frontmatter, privacy, `claude plugin validate`. Mermaid
render tests need the Mermaid CLI (`mmdc`) and are skipped without it.
Lint suppressions: report the count before adding any (currently three, each
justified inline).

### Testing

See `docs/testing.md`. Engine changes need pytest coverage. Changes to
`SKILL.md` or `references/` need a recorded model run by an agent that hasn't
seen the answers, saved under `tests/fixtures/library-review/runs/`. After any
rendering change, render the fixture and **look** at the output.

### Git

- Sole maintainer; committing directly to `main` for now. Branch and PR rules are
  deferred, not dropped (`docs/decisions.md` D-17, `HANDOFF.md` backlog).
- Ask before committing; summarize changes first.
- Identity from global git config (GitHub noreply email). AI attribution via
  trailer: `Co-Authored-By: Claude <noreply@anthropic.com>`.
- Commits on `main` are signed with the maintainer's local SSH key (D-18). Don't
  commit from environments without it unless the maintainer decides otherwise.

## Key files

| File | Purpose |
| --- | --- |
| `HANDOFF.md` | Current state, next steps, backlog |
| `docs/architecture.md` | How it's built and why |
| `docs/decisions.md` | Decisions, alternatives, revisit triggers |
| `docs/testing.md` | Fixture, test map, recording model runs |
| `docs/guide/using-plotpoint.md` | For callers |
| `docs/guide/try-it.md` | Hands-on tour; keep its commands working (`tests/fixtures/library-review/requests/`) |
| `docs/examples/` | Worked examples (invented data); re-render after rendering changes |
| `docs/plans/` | Dated plans (history) |
| `skills/visualize/references/spec.md` | Field reference; schemas are the source of truth |
| `skills/visualize/DESIGN.md` | Skill rationale and test findings |
| `tests/fixtures/library-review/` | The test write-up and expectations |

## Documentation sync map

When a change touches the skill, a decision or the structure, update every
surface that describes it before calling the change done:

- `HANDOFF.md`: state and next steps; **Backlog is the single index of deferred work** (rows keep a Status; never delete them)
- `README.md`: tagline, what you get, formats and visual types, install, layout
- Repo description (GitHub "About"), `plugin.json`, `marketplace.json`: identical to the README tagline
- `CLAUDE.md`, `docs/architecture.md`, `docs/decisions.md`
- Field or behavior changes: `schemas/`, `references/spec.md`, `docs/guide/`, and the fixture's reference answer
- Layout, technique or capacity changes: `config/`, `references/targets.md`
- `SKILL.md`, the skill's `README.md` and `DESIGN.md`
- `docs/testing.md` and `tests/fixtures/library-review/expected.md` when tests change
- `ACKNOWLEDGMENTS.md` + `NOTICE` when a source is added
- `plugin.json` version on release
