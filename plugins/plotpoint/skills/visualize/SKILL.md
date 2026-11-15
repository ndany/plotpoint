---
name: visualize
description: Data storytelling for write-ups, reports, dashboards and slides. Plans the visual story across many datasets (order, merge, demote, cut, audience placement, consistent colors) and decides and draws each visual for Markdown, HTML and slide images, with headline, emphasis and checked numbers. Use when a document or deck needs charts, when choosing how to show a dataset, or when converting visuals between Markdown and HTML.
license: Apache-2.0
---

# plotpoint: visualize

**Purpose: better storytelling with data.** Every choice here (what to show, in
what order, where, how it's drawn) serves the question the reader needs answered.
The caller owns the analysis, the prose and the final layout; this skill
**advises** on the visual story and **draws** visuals. It never invents an
analytical conclusion.

Two operations. Work out which one the caller wants, then follow only that
section. Run `uv run <this-skill>/scripts/visualize.py ...` when `uv` is on PATH (it
installs the dependencies itself). Otherwise use `python3` (macOS, Linux) or `py`
(Windows); the script finds its own cache venv once it exists. If the script stops
with a missing-dependency message (exit code 3), **show that message to the
user and stop**: don't install packages globally, don't look for another
environment, don't work around it.

| Operation | Input | Output |
| --- | --- | --- |
| **storyboard** | A storyboard request: questions, audiences, datasets, targets, optionally the draft write-up | An ordered list of visuals with their intents, recommendations, a color map |
| **render** | One visual: a dataset plus an intent from storyboard, or just a question | Files, a Markdown snippet or HTML fragment per target, check results |

Specs and field meanings: `references/spec.md`. Validate anything you write:
`visualize.py validate <kind> <file>`.

## Operation: storyboard

1. **Validate** the request: `visualize.py validate storyboardRequest request.yaml`.
2. **Profile** every dataset: `visualize.py profile request.yaml`. Read the
   profiles, not the raw rows. They include ranges, outlier and dominance
   flags, the rows holding extremes, and samples (`references/profiling.md`).
   For many or large datasets, do this step and step 4 in a sub-agent if you
   can, and keep only the result.
3. If the request has a `draft`, read it: it shows the narrative, the current
   visuals and what the caller already concluded.
4. **Plan the story**, per `references/storyboard.md`:
   - Map each question to the dataset(s) that answer it.
   - **Order:** summary visuals first, the one answering the main question leading.
   - **Merge** datasets that tell one story; **demote** visuals with no single
     takeaway to tables; **cut** datasets that answer no question.
   - **Audience and placement:** `summary` for decision-makers, `body` or
     `appendix` for practitioner detail.
   - For each visual, decide the **intent** (step 2 of render below). If it
     renders from a merged or derived table, set `data` and `data_note`.
   - Decide the **rendering per target**: the best technique in each format,
     with compensations where a format can't carry part of the intent
     (`references/targets.md`).
   - Build one **color map** for the whole document.
5. Write the result as YAML and **validate** it (`validate storyboardResult`).
   Then **dry-run** every visual: `visualize.py check-plan request.yaml
   result.yaml` runs each one's checks (and shows text outputs) without
   writing files. Fix failures and re-run; then return it. Tell the caller which headlines are drafts and which
   recommendations need their decision.

## Operation: render

1. **Validate** the request (`validate renderRequest`).
2. **Decide the intent** if the request has none (mode C). Profile the data
   (`visualize.py profile request.yaml` works on a render request, inline data
   included; or `profile --data FILE`), then:
   - **Visual type** from the question first, then the data's shape
     (`references/chart-chooser.md`). A table, a single number or a sentence
     is a valid answer.
   - **Headline:** a sentence stating the takeaway, not the topic. Use the
     caller's `takeaway` if given (`headline_status: confirmed`). Otherwise
     state what the data shows and mark it `draft`. A reference table with no
     single takeaway gets a descriptive `title`.
   - **Fields:** which columns play which role; display `names` for columns;
     `bins` for a histogram (a maximum, default 20; `names: {count: ...}` titles its
     y axis).
   - **Highlight:** the series or categories the headline is about. Everything
     else turns context gray.
   - **Callouts:** mark the moment that matters (`rule`, `point`, `note`;
     how each is pinned: `references/spec.md`, Callouts). Every number in the
     headline must be visible on the visual, so add a callout for any figure
     the chart doesn't plot (a total, a median). Highlighted series already
     get a value label; don't repeat it.
   - **Outliers:** if the profile flags any in a plotted measure, set
     `outlier_handling`, per column when they need different treatment:
     `callout`, `log_scale`, `exclude` (with values and a reason; only when
     the caller confirms), or `accept` (with a reason). Never drop one
     silently. Skew alone needs nothing; tables are exempt.
3. **Render:** add the intent to the request and run
   `visualize.py render request.yaml`. Targets, layouts and techniques:
   `references/targets.md`.
4. **Read the checks** in the result. Fix every `fail` (`headline_numbers`,
   `outliers`, `callouts`, `legibility`, `render`) and re-render; report
   `warn`s. Read what each headline number matched: a pass on the wrong row,
   period or statistic is still wrong, so confirm each match is the one your
   sentence means. Render flags (`--dry-run`, `--quiet`): `references/spec.md`, "Render flags".
5. **Look at the output** before delivering: open the PNG or SVG, or
   screenshot the HTML fragment (an SVG converts to PNG with
   `vl_convert.svg_to_png`, or opens in a browser); for text, tables and
   Mermaid, read the snippet. The chart file has no headline or source line;
   the snippet adds them. Check for clipped or overlapping labels, that every number in the
   headline is visible, and that the claim reads at a glance. Checks can't see
   layout.
6. **Return** the snippets and files. Files carry a visible DRAFT or CHECKS FAILED
   mark when they aren't ready (`references/spec.md`, "Status marks"). Flag draft headlines and any
   compensation the caller should know about.

## Rules that always apply

- Rendering style follows the **dataviz** skill. The renderer's theme
  (`config/theme.yaml`) already applies its method, so render-only work needs
  nothing more. Load dataviz when you draw anything by hand (a type the
  renderer refuses, a dashboard layout); if it's unavailable, use
  `references/fallback-rendering.md`.
- One y-axis. Bars start at zero. Text is ink-colored, never series-colored.
- Source and as-of date on every visual (the renderer adds them).
- HTML output is a fragment (`<figure>`), never a full page.
- For multi-chart pages, also use `references/composition.md`.
