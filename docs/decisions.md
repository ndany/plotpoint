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
Since 2026-11-15 (C11) it also fails on rule and point callouts on bar and
stacked bar charts drawn by Vega-Lite, which never drew them (the tour found
them silently missing), and table outputs list them as notes like Mermaid.
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

## D-27: Slide images use a bundled font, checked pixel for pixel

**Chosen:** the skill bundles Source Sans 3 (Regular, Semibold, Bold; SIL OFL
1.1) in `fonts/` and registers it with vl-convert once. `image/slide` text uses
`slide_font` from `config/theme.yaml`; documents and `html/slide` keep the
reader's system fonts. Slide charts are laid out with vl-convert's built-in
`sans-serif` (`slide_measure_font`) and drawn in the bundled font, because
vl-convert 1.9 measures a font it doesn't ship differently on Linux. A test
compares each fixture slide's decoded pixels with stored hashes
(`tests/fixtures/slide-hashes.yaml`) on Linux, macOS and Windows.
**Alternatives:** system fonts (each machine drew a different PNG); embed the
font in the SVG or turn text into outlines (about 1.2 MB per SVG, no gain for
the PNG); measure with the bundled font (broke cross-platform identity); compare
images with a tolerance (exact hashes already match on all three platforms, and
a tolerance can hide a real change).
**Rationale:** a slide must look the same wherever it's rendered, and only an
exact check proves it.
**Cost:** 1.2 MB of fonts in the skill. Legends and axes are spaced for slightly
wider text than drawn. A glyph Source Sans 3 lacks still falls back to a system
font. The slide `.svg` written beside the PNG names the font without embedding
it, so on a machine without Source Sans 3 it shows a substitute: use the PNG
for slides. Any vl-convert or font update changes the hashes; refresh them after
looking (`docs/testing.md`, "Platform checks").
**Revisit:** if vl-convert measures registered fonts the same on every platform
(drop `slide_measure_font`), can disable system fonts, or the font changes.

## D-29: Every document format writes a deliverable file

**Chosen:** each target writes one file meant to be published or pasted:
`<id>-md-document.md` (image links relative to its own folder), an `.html`
fragment for every HTML technique (SVG, interactive, table, text), and the
slide PNG. The other files (`.svg`, `.mmd`, `.vl.json`) are by-products.
`spec.md` lists both per target.
**Alternatives:** write a file for Markdown only, as the tour finding asked
(interactive, table and text HTML would still exist only as a snippet in
`result.json`).
**Rationale:** one rule with no exceptions: every format gives you a file to open.
**Cost:** one more small file per HTML target.
**Revisit:** if callers only ever use the snippet.

## D-30: Draft and failed visuals are marked in every file you could publish

**Chosen:** a draft headline adds `DRAFT — headline not confirmed`; any failed
check adds `CHECKS FAILED: <names>`. Markdown and HTML get a line above the
headline, slides a colored bar across the top, and chart pictures (`.svg`) the
same bar, so the mark stays with a picture copied on its own. The files are
still written. Colors come from `status` in `config/theme.yaml`: `#8a5a00`
(draft) and `#b3261e` (failed), 5.9:1 and 6.5:1 against white, above WCAG AA's
4.5:1 for text both ways (colored text on white, white text on the bar).
**Alternatives:** an HTML comment (the old draft marker: invisible); write no
files when checks fail (the caller can't see what went wrong); mark only the
page and not the picture (a copied picture loses the mark); mark only the
picture where one exists (tables, text and Mermaid have none, so each
technique would need its own rule).
**Rationale:** a draft or a wrong number must not pass as finished work, in
whichever file leaves the folder.
**Cost:** a page showing a marked picture shows the mark twice. Mermaid and
Vega-Lite sources (`.mmd`, `.vl.json`) aren't pictures and stay unmarked; the
page that uses them is marked. A target that fails to draw writes no file to
mark (the exit code and `result.json` report it). Contrast was computed by hand:
dataviz's `validate_palette.py` wasn't available here.
**Revisit:** if callers need marks they can switch off (e.g. internal review
copies), or the theme changes (re-validate with `validate_palette.py`).

## D-31: `--checks-only` renamed `--quiet`, with no alias

**Chosen:** `render --quiet` writes every file but prints only checks and notes.
The old name is gone; `spec.md`, "Render flags", explains every flag in one
place, and the CLI help and `SKILL.md` point there.
**Alternatives:** keep `--checks-only` as a hidden alias (the misleading name
survives in old scripts and recorded runs, and keeps being copied).
**Rationale:** the old name said "check only" while the command wrote files; the
tour misread it. Version 0.1 has no outside users to break.
**Cost:** recorded runs quote the old name verbatim and aren't edited, so they
no longer run as written.
**Revisit:** never for the alias; rename again only if `--quiet` is misread.

## D-32: A folded "Other" bigger than what it sits beside warns or fails

**Chosen:** when capacity folds the smallest bars (or stacked segments) into
"Other", the `capacity` check compares "Other" with every item still shown. If
it is bigger than any of them, the check warns and names them. If one of those
is highlighted or named in the headline, it fails, so the status mark goes on
every file.
**Alternatives:** a note only (what the tour found: "Other" at 297k beside a
highlighted 212k, and the check said pass); always fail (folding is often fine,
and a big "Other" beside unnamed bars is a judgment call); never fold, always
show every bar (breaks the layout's capacity).
**Rationale:** a merged bar that outgrows the bar the headline is about makes
the chart contradict the headline; beside unnamed bars it's a readability risk,
not an error.
**Cost:** "named" means the bar's label appears in the headline as a whole word,
so a headline that refers to a bar indirectly ("the central branch") only gets
the warning. Line charts don't fold and aren't checked.
**Revisit:** if callers want a setting to drop "Other" entirely, or a headline
names a bar by another word.

## D-33: A confirmed headline is the caller's takeaway, word for word

**Chosen:** `headline_status: confirmed` means the headline is the caller's
`takeaway` as written; case, spacing and a final period don't count. A new
`takeaway` check fails a confirmed headline that differs. `check-plan` gives
each visual its question's takeaway (when its questions have exactly one), so
storyboards are checked too. `SKILL.md` tells the model to mark any edit
`draft` and say what changed; expectation E12 checks recorded runs.
**Alternatives:** allow "close enough" edits (word overlap or similarity: any
threshold lets a new claim through, e.g. "to a new high"); instructions only
(two of two tour runs reworded and kept `confirmed`).
**Rationale:** the caller confirmed a sentence, not a topic. A shortened,
reworded or number-added headline is a new claim they haven't seen, so it has
to show as a draft until they confirm it.
**Cost:** a harmless rewording also becomes a draft and needs one confirmation.
A visual answering two questions with different takeaways isn't checked. The
reference answer and the tour requests had amplified the takeaways for v1 and
v3; they now use them as written (v1 slide hash refreshed after looking; T2b's
recorded run is a known miss).
**Revisit:** if callers want to allow edits by listing approved wordings, or a
visual commonly answers several questions.

## D-34: Recorded runs are automated with a headless harness

**Chosen:** `scripts/record_run.py` runs each model test (T1–T3, D, SETUP) as
a headless `claude -p` session in a scratch copy outside the repo, without the
answer files and with only the plugin under test loaded. It audits the
transcript for anything opened outside the scratch folder and saves the
outputs and notes under `runs/`, where pytest scores them. Changes how D-19
is carried out, not what it requires.
**Alternatives:** a person runs each test in a new VS Code session (slow, and
the step most often skipped); `--bare` isolation (needs an API key: it never
reads the subscription login); blocking reads outside the folder by setting
(`blockReadsOutsideWorkingDirectories` isn't in every Claude Code version yet,
and doesn't cover shell commands, so the audit is still needed).
**Rationale:** re-running every test after each skill change is what keeps the
instructions honest; it only happens if it's one command.
Runs use the skill's own per-user cache venv (the one-time setup in its
message), so they see the machine as a user does.
**Cost:** each run uses the maintainer's Claude login: plan usage on a
subscription, billed tokens with an API key (estimated $0.80–$1.80 per run on
2026-11-16; `--budget` caps it). SETUP can only run
where the skill was never set up. The audit reads tool inputs, so a shell
command that builds a path indirectly could slip past it; the brief also asks
the session to report what it opened. Launching `claude` needs one lint
suppression (`# noqa: S603`, justified inline; five in the repo now).
**Revisit:** when `--bare` works with a subscription login, or Claude Code can
confine shell commands to a folder.

## D-35: The caller's audiences are proposed to, never changed

**Chosen:** a storyboard keeps each question's audiences. It may narrow
them for practitioner detail, but showing a visual to a wider audience is a
recommendation: `add-summary` (a one-line `sentence` or `number` for the
decision-makers) or `placement` (the visual itself), with the reason. The
plan changes only when the caller accepts. E8 now fails any q3 or q4 visual
for the board, including a summary sentence it used to allow.
**Alternatives:** accept a widening the result states (the 2026-11-16 T2
run did this, following the instructions of the time: it applied the change,
then asked); relax E8 to allow a widened summary visual; leave audiences to
the model's judgment (needs a rule for when widening is right, which can't be
written generically).
**Rationale:** plotpoint advises and the caller decides. Audiences, like a
takeaway (D-33), are something the caller stated, so a change to them waits
for the caller's yes. "Who decides" is a rule that holds in any domain;
"when to widen" isn't.
**Cost:** one more confirmation when the caller would have agreed. Two saved
runs (T2b, 2026-11-16 T2) followed the old instruction and list E8 as a known
miss. Needs re-running T1 and T2. The model may still apply a widening; E8
catches it in recorded runs, not in a real caller's plan.
**Revisit:** if callers accept nearly every widening (then apply and mark
it, as with drafts), or a check on real plans is wanted (compare a result's
audiences with the request's).

## D-36: `summary` is the decision-makers' read

**Chosen:** a visual for practitioners only goes in `body` or `appendix`,
even when it's the main answer to its question. If the decision-makers need
it, that's proposed under D-35. E8 already checked this; `storyboard.md` and
`SKILL.md` now say it.
**Alternatives:** a read-first item per audience (a managers' summary
beside the board's); changes E8, the reference answer and what `summary`
means to a reader of the document.
**Rationale:** both 2026-11-17 runs, blind, said the docs didn't settle it
and guessed differently (T1 `body`, T2 `summary`). One summary for the
people who decide keeps the document's structure plain; practitioners read
the body.
**Cost:** a practitioner-only write-up has an empty summary unless its
audiences include a decision-maker; the caller can name managers as
decision-makers there.
**Revisit:** if callers write documents for several decision-making
audiences and ask for a summary each.
