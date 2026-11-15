# Decisions

Decisions, alternatives, rationale, and when to revisit. Rewritten for v1
(2026-11-01): the earlier draft was never committed or tested. Add new entries at
the end; mark superseded ones rather than deleting them.

---

## D-1: Standalone repository and marketplace

**Chosen:** plotpoint is its own public repository and its own plugin
marketplace, not part of a personal Claude environment repo.
**Alternatives:** a personal environment repo; one repo for many skills; a hub
marketplace listing several repos.
**Rationale:** reusable and shareable by the maintainer (personally and at work)
and the public; installable on its own with one command; its own CI and releases.
A hub can list it later without changes.
**Revisit:** when a hub marketplace is created (`HANDOFF.md` backlog).

## D-2: Name "plotpoint", skill "visualize"

**Chosen:** plugin `plotpoint`, skill `visualize` (`plotpoint:visualize`).
**Alternatives:** plotline, chartwright, storyplot, plotwise, chartlede; skill
names `storytell`, `chart`, `plotpoint`.
**Rationale:** a plot point is a turning point in a story and a point on a chart,
so the plugin name carries the storytelling purpose; the skill name is the action
and covers rendering-only use (e.g. a Markdown-to-HTML converter). `plotpoint`
was free on PyPI and npm (2026-10-24); a Rust crate of that name exists.
**Revisit:** before publishing any package.

## D-3: Apache-2.0

**Chosen:** Apache License 2.0, with `NOTICE` carrying acknowledgments.
**Alternatives:** MIT; AGPL-3.0.
**Rationale:** permissive, paying forward the work plotpoint builds on;
redistributors must keep `NOTICE`, so credit travels with every copy; explicit
patent and trademark terms. No share-back obligation.
**Revisit:** if a downstream user needs GPLv2 compatibility.

## D-4: Purpose is storytelling; two operations in one skill

**Chosen:** one skill with two stateless operations: **storyboard** (advice
across a whole write-up) and **render** (one visual). Storyboard is advisory.
**Alternatives:** two skills; render only, with callers iterating.
**Rationale:** seeing every question and dataset at once enables order, merge,
demote, cut, audience placement, one color map and per-format techniques. One
skill shares the chooser, theme and scripts without duplication; a skill can only
rely on files in its own folder.
**Cost:** a larger `SKILL.md` (mitigated by loading references per operation).
**Revisit:** if the operations diverge enough to need separate triggers.

## D-5: Judgment in instructions, everything computable in code

**Chosen:** the model decides the story, form, headline and outlier handling;
scripts load, profile, shape, draw and check.
**Rationale:** repeatable, testable output; numbers verified against the data
rather than read by eye; layout computed rather than guessed.

## D-6: Vega-Lite via vl-convert as the rendering engine

**Chosen:** Vega-Lite specs rendered by `vl-convert-python` (SVG, PNG,
interactive HTML); Mermaid and tables as text-native techniques.
**Alternatives:** matplotlib plus separate HTML templates.
**Rationale:** one spec per visual type renders every format; offline; BSD-3;
confirmed available in the maintainer's work environment (1.9.0.post1).
**Cost:** one compiled dependency; Vega-Lite's defaults needed a theme.
**Revisit:** if the dependency is blocked somewhere plotpoint must run.

## D-7: Intent vs rendering

**Chosen:** one format-independent intent per visual; a technique per target,
with recorded compensations where a format can't carry part of the intent.
**Rationale:** the story stays identical across Markdown and HTML while each
format uses what it does best.

## D-8: Targets are format plus layout; presets plus overrides

**Chosen:** targets `md/document`, `html/document`, `html/slide`, `image/slide`;
layout presets `prose` 800, `report` 960 (default), `wide` 1100, `dashboard`,
`deck` 1440×810, `slide-image` 1920×1080; callers override with exact widths.
Draw at content width, never scale up, keep labels ≥ 11 px at the narrowest
expected display width.
**Alternatives:** one fixed width; fully caller-specified sizes.
**Rationale:** in-use page conventions vary by content type and were chosen for
readability; scaling changes apparent text size, so the drawing width must match.
**Revisit:** after use; presets live in `config/layouts.yaml`.

## D-9: Data by path or inline CSV

**Chosen:** `data: {path}` (csv, tsv, json, jsonl) or `data: {inline}` (CSV text).
**Alternatives:** three forms (path, rows, csv); Excel and Parquet.
**Rationale:** `rows` and `csv` were two spellings of one thing; inline data is
written to a temporary file and handled exactly like a path. Excel and Parquet
need heavy dependencies.
**Revisit:** when a caller needs Excel or Parquet.

## D-10: Profiles surface outliers; outliers are handled explicitly

**Chosen:** profiles include distribution stats, IQR outliers, a dominance flag,
extreme rows and deterministic samples that include the extremes. A flagged
outlier must be handled by callout, log scale, exclusion (with a reason) or
acceptance (with a reason).
**Rationale:** random samples hide the values that shape a chart; silent
exclusion misleads.

## D-11: Headline numbers are checked against the data

**Chosen:** every number in a headline or callout must be derivable: a value, a
total, a count, a summary statistic, a share, or a plausible change (consecutive,
first to last, peak or low to latest, or between measures in a row).
**Alternatives:** every pairwise change (rejected: almost any percentage matched).
**Limit:** confirms derivability, not that the sentence describes the right
comparison; the skill's "look at it" step covers that.

## D-12: HTML output is a fragment

**Chosen:** a `<figure>` with inline styles; inline SVG by default; interactive
Vega-Lite on request, with the page including the scripts once.
**Rationale:** the caller owns the page; strict page policies often block
scripts; SVG prints and emails well. Ids are prefixed per visual.

## D-13: Audiences at three levels, with placement

**Chosen:** write-up audiences, per-question audiences, visuals inheriting them;
placement `summary`, `body`, `appendix`.
**Rationale:** write-ups serve several audiences; the summary-first order is
where storytelling starts.

## D-14: dataviz is a recommended dependency

**Chosen:** apply the dataviz skill's method (bundled with Claude) and ship a
short fallback rule set. plotpoint's palette is its own, validated with
dataviz's checker.
**Rationale:** don't rebuild what dataviz does well; degrade gracefully where
bundled skills are turned off.

## D-15: Runtime docs live in the skill folder

**Chosen:** everything Claude needs at run time is inside the skill folder; repo
docs link to it and never copy it.
**Rationale:** an installed skill can only see its own folder; copies drift.

## D-16: Portable frontmatter only

**Chosen:** `SKILL.md` frontmatter limited to Agent Skills standard fields,
enforced by `scripts/check_frontmatter.py`.
**Rationale:** Claude.ai uploads and the API reject other fields.

## D-17: Defer branch and PR workflow

**Chosen:** commit directly to `main` for now (sole maintainer, early stage).
**Cost:** no review or CI gate before changes land; mitigated by the pre-commit
hook and `scripts/check-all.sh`.
**Revisit:** stable v1, a second contributor, or regular outside use (the repo
is public from the start, by choice) (`HANDOFF.md` backlog). Planned
(2026-11-14): require PRs and turn on branch protection for `main`; D-24 ends
then.

## D-18: Signed commits from a local machine

**Chosen:** commits on `main` are signed with an SSH key held on the
maintainer's machine, from the first content commit.
**Alternatives:** GitHub-signed PR merges from cloud sessions; a key generated in
a cloud session (rejected).
The first commit's instructions and message ship in `docs/plans/`
(`FIRST-COMMIT-GUIDE.md`, `COMMIT_MSG.txt`), gitignored so they stay out of
history; they were deleted after that commit (2026-11-14).
**Revisit:** if commits are made from cloud sessions.

## D-19: Model-behavior tests are recorded runs by an independent agent

**Chosen:** storyboard and single-visual decisions are tested by a session that
hasn't seen the design or the answers; results are saved and checked by pytest
against expectations E1–E11.
**Rationale:** model behavior can't be unit-tested, and grading one's own design
isn't independent.

## D-20: Checks fail loudly on anything the renderer would drop

**Chosen:** a `callouts` check fails when a rule or point callout matches
nothing drawn; text and table outputs turn every callout into a note.
**Alternatives:** skip unmatched callouts (the original behavior).
**Rationale:** the first mode C run had three charts whose checks passed while
the callout carrying the headline's evidence had silently disappeared.
**Revisit:** if label placement becomes configurable (`HANDOFF.md` backlog).

## D-21: Outlier handling per column

**Chosen:** `outlier_handling` is one entry for every column, or a list with one
entry per `column`. Skew is informational; tables are exempt.
**Alternatives:** one method per visual.
**Rationale:** a scatter can hold an outlier that is the story (callout) and one
that is real context (accept) at once; all three recorded runs hit this.

## D-22: Storyboards dry-run their plans

**Chosen:** `render --dry-run` runs every check without writing files; the
storyboard operation dry-runs each planned visual before returning. Storyboard
visuals can name the table to render from (`data`, `data_note`), and reference
visuals can carry a descriptive `title` headline.
**Rationale:** without it, a storyboard could return plans that fail at render
time (headline numbers, unhandled outliers, unpinned callouts).
**Cost:** a slower storyboard (one check pass per visual, about a second each).

## D-23: The headline check is strict, explains itself, and checks direction

**Chosen:** a number passes only if it matches a candidate that fits the visual:
plotted values (only min and max above 50 rows), counts, totals, summary
statistics; shares only on bars and tables; changes along a series or against
`previous`, in the direction the text states; distribution claims checked as a
share-and-threshold pair. When a clause names a row, only that row's figures
(or an introduced aggregate) match; multiples fail. Every pass lists what each
number matched.
Scaled numbers ("212k", "1.2M", "3bn") count, within their rounding, and
match data stored in that unit only when the measure declares it (column name,
`names` or `units`); until 2026-11-14 they were skipped, so any value passed
(tour, C7).
Bare thresholds are read with their quantifier ("some" by default; "no",
"never", "all", "every", "at most" mean every value), and a failure names the
counterexample; until 2026-11-14 any threshold inside the data's range passed,
so "no wait over 40" passed with a 47.5 in the data (tour, C8).
**Alternatives:** every value and pairwise change (rejected: an independent
tester got "fell 22%", "fell 3%" for a rise and "half within 12" past it).
**Cost:** some true but unusual phrasings fail and need rewording; the row limit
lives in `config/capacity.yaml`.
**Limit:** it still can't tell whether the sentence compares the right things, or
whether the number is visible; the "look at it" step covers both.

## D-24: Dependency updates are applied locally, not merged on GitHub

**Chosen:** Dependabot's PRs aren't merged on GitHub. Their version bumps are
applied in a signed local commit on `main` (D-17, D-18), and the PRs close as
obsolete (or by hand).
**Alternatives:** merge on the web (GitHub signs that commit, not the
maintainer's key, against D-18); require PRs now (D-17's revisit).
**Cost:** one manual commit per weekly update group; the PRs show closed, not
merged.
**Revisit:** when PRs and branch protection on `main` become required (D-17);
Dependabot's PRs then merge like any other.

## D-25: Markdown figures are linked SVG files beside the document

**Chosen:** Markdown output links SVG files, by default in `figures/<doc-name>/`
next to the document, and the guide and `spec.md` explain it.
**Alternatives:** inline `<svg>` in the Markdown (GitHub strips it; about 10 KB
of markup per chart); SVG as a base64 `data:` URI (GitHub blocks it; about
13 KB of unreadable text per chart; only helps single-file documents read
locally); Mermaid only (exists as a technique, with fewer chart types). A plain
`figures/` folder was rejected because two documents in one folder can both
have a `v1`.
**Rationale:** linked SVG files work on GitHub and in local editors; the
per-document folder never collides and keeps each document's images together.
**Status:** decided 2026-11-14, not built yet (`HANDOFF.md` backlog, "Markdown
figures beside the document", after C12 writes the `.md` file).

## D-26: npm overrides for transitive dev-tool fixes

**Chosen:** when a security fix exists for a transitive dependency of the npm dev
tooling but the direct dependency doesn't pull it in yet, pin the fixed version
in `package.json` `overrides` (first used for `katex`, under `markdownlint`).
**Alternatives:** wait for the upstream package to widen its range (the alert
stays open meanwhile); accept the alert because the tooling is dev-only and not
shipped in the plugin.
**Rationale:** clears the alert now at no cost to the plugin; markdownlint only
loads the overridden package for math syntax, which these docs don't use, and
every gate passes with it.
**Cost:** the override must be removed by hand once upstream catches up, or it
can hold the package back later.
**Revisit:** each npm Dependabot update; drop the override when `npm ls` shows the
direct dependency resolves a fixed version by itself.

## D-28: Dependency bootstrap: uv when available, otherwise stop and say how

**Chosen:** `visualize.py` carries PEP 723 metadata, so `uv run` installs its
dependencies itself (a test keeps the list identical to `requirements.txt`).
Without uv, a standard-library-only `bootstrap.py` checks the Python version and
imports before anything else runs. If a per-user cache venv exists
(`~/Library/Caches/plotpoint/venv` on macOS, `%LOCALAPPDATA%\plotpoint\venv` on
Windows, `~/.cache/plotpoint/venv` on Linux), the script re-runs itself with
that venv's Python (same arguments, exit code passed through, loop guard).
Otherwise it does nothing, exits with code 3 and prints the setup commands for
the current OS. `SKILL.md` tells Claude to show that message to the user and
stop: no global installs, no hunting for other environments.
**Alternatives:** create the venv and install automatically on first run
(hidden network and disk side effects; fails offline or when locked down);
document `pip install` only (breaks on externally managed Pythons, PEP 668, and
on `python` / `python3` / `py` differences); vendor wheels (large and
platform-specific); reuse any `.venv` found nearby (invisible and
unreproducible: the workaround the tour found).
**Rationale:** a missing dependency stops all output, so the user must see it and
be able to fix it by copy and paste; setup happens once, and uv makes it one
step.
**Cost:** one more module; the dependency list kept twice (tested); the re-run
starts a second Python (about 0.1 s). Starting that process needs one lint
suppression (`# noqa: S603`, justified inline, as for the Mermaid CLI): ruff
flags any program start in case its arguments are attacker-controlled, but this
program is plotpoint's own venv Python and the arguments are the caller's own,
with no shell.
**Revisit:** if uv becomes a requirement, a Claude client can run setup with the
user's approval, or the dependencies change.
