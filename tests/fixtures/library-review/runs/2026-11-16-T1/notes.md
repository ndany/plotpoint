# 2026-11-16-T1: recorded by scripts/record_run.py

- Test: T1; model: sonnet; dependencies: venv
- Turns: 26; cost (client estimate): $1.32
- Plugins loaded: plotpoint (<scratch>/.plugin/plotpoint)
- Tool calls naming an answer file: 0
- Tool calls with a path outside the scratch folder: 0

## Session notes

# plotpoint:visualize — first-time test notes

## What I produced

`storyboard-result.yaml`: a 5-visual storyboard for
`storyboard-request-with-draft.yaml`, validated against the schema and
dry-run with `check-plan` (all checks `pass`, no `warn`/`fail`).

To build it I also had to materialize two derived tables the plan needs
(the storyboard spec requires building any merge/join target yourself so
`check-plan` can dry-run it):

- `data/derived/branch_detail.csv` — new file I wrote, joining
  `branch_overview.json` and `branch_waits.jsonl` on `branch` for the
  appendix table (v5).
- `data/derived/loans_by_quarter.csv` — already existed in `data/derived/`
  before I started; I reused it as-is for v1 (its columns already matched
  the print/e-book join the plan needed).

Visuals, in order:

1. **v1 — line, summary, q1.** Print + e-book loans merged onto one line
   chart over the five quarters (replaces the draft's two separate bar
   charts). Headline is the caller's takeaway verbatim (`confirmed`). A
   rule callout at Q2 '26 carries the "total fell 18%" number since it
   isn't a plotted series by itself.
2. **v2 — number, summary, q2.** Active members: 48,210, up from 46,700.
   Café sales is **not** used here or anywhere — see "cut" below.
3. **v3 — scatter, body, q3.** Staff (FTE) vs. average wait per branch,
   Riverside highlighted. Answers "which branches need more staff" directly.
4. **v4 — histogram, body, q4.** Distribution of the 300 individual visit
   waits.
5. **v5 — table, appendix, q3.** All 12 branches' visits/hours/staff/events/
   avg-wait in one reference table, replacing both the draft's partial
   branch-overview table and its planned separate "waits by branch" appendix.

## Which headlines are drafts, and why

- **v1** (`confirmed`) — uses the caller's `takeaway` for q1 word-for-word.
- **v2** (`draft`) — q2 has no `takeaway` in the request. I wrote "Active
  membership grew to 48,210, up from 46,700" from the `members` dataset
  alone; it needs a person to confirm (and to decide whether "grew ... up
  from" is the right framing, since the request doesn't say what period
  "previous" covers).
- **v3** (`confirmed`) — uses the caller's `takeaway` for q3 word-for-word.
- **v4** (`draft`) — q4 has no `takeaway`. I wrote "Median wait is 7.8
  minutes, and 82% of visits are within 15 minutes" directly from the
  `wait_minutes` profile; needs confirmation.
- **v5** (`title`) — it's a reference table with no single takeaway, so it
  gets a descriptive title, not a claim.

## Decisions the caller must make

1. **Café sales (`cafe_sales`) — recommended cut.** It's listed under q2
   but doesn't answer "how many people actively use the library" (that's
   `members`); no question in the request asks about café revenue either.
   I left it out of the storyboard entirely and flagged it as a `cut`
   recommendation. If the board actually wants café revenue tracked, that
   needs its own question + takeaway, not a ride-along on q2.
2. **q3/q4 audience is `managers` only** — the draft's "Conclusion" section
   leads with the Riverside staffing finding (v3's subject), but since the
   request scopes q3 to managers, v3 landed in `body`, not `summary`. If the
   board should see it too (it's a staffing-budget decision), add `board` to
   q3's `audience` and I'd promote v3 to `summary`. I didn't do this myself
   since it changes who the request says should see it.
3. **v2's "up from 46,700" framing** — the `members` dataset's `previous`
   column has no date attached, so I avoided implying a period ("a year
   earlier" etc.). The caller should supply what "previous" means if it
   should be stated.
4. **Derived files I created are scratch, not canonical** — `data/derived/
   branch_detail.csv` is a join I built to make the appendix table
   dry-runnable; if the project has its own pipeline for this join, use
   that instead and regenerate rather than keeping my copy.

## What I opened outside this folder

None. Everything I read was either inside this folder
(`storyboard-request-with-draft.yaml`, `storyboard-request.yaml`, `data/`,
`drafts/review.md`) or inside `.plugin/plotpoint/skills/visualize/`, which
the task description says is fine (the skill's own files, loaded from the
plugin: `SKILL.md`, `references/*.md`, `schemas/plotpoint.schema.json`,
`scripts/visualize.py`, and `scripts/ppviz/` for the percent-threshold
question below). I did not open the plotpoint repository itself, its
`docs/`/`tests/`, any `runs/` folder, `DESIGN.md`, `docs/plans/`,
`storyboard-golden.yaml`, `expected.md`, `render-data.yaml`, or notes from
earlier tests.

## Skill feedback

- **`uv` detection silently falls back.** SKILL.md says to run with `uv run`
  "when `uv` is on PATH," else `python3`/`py`. There's no visible signal
  either way — I had to run `which uv python3` myself to find out `uv`
  wasn't installed and a venv-aware `python3` was. A one-line "checking for
  uv..." style note, or the script printing which interpreter path it's
  using, would save that detour for a first-time user.
- **Building a merge/join target isn't scripted.** `storyboard.md` says "To
  dry-run it, build that file yourself first (a scratch copy is fine) at
  the path you name" — but there's no helper for this (e.g. a `join` mode
  in `visualize.py`), so I hand-wrote a Python snippet to join two files
  with different formats (`.json` array vs `.jsonl`) on a shared key. For a
  one-off two-table join this is fine, but the skill could at least point to
  a recommended approach (pandas? a tiny built-in merge verb?) rather than
  leaving "build it yourself" fully open-ended.
- **Percent-threshold rounding tolerance is undocumented.** `spec.md` lists
  `"82% within 15 minutes"` as a valid derivable-number pattern for
  distributions, but doesn't say how much rounding slack the `headline_numbers`
  check allows (my true value was 81.67%, rounded to 82%, and it passed —
  good — but I only found that out by running `check-plan`, not by reading
  the docs). Stating the rounding rule explicitly (it's implied for "scaled
  numbers" like "212k" but not for plain percentages) would let me pick a
  headline number with confidence before dry-running.
- **Otherwise straightforward.** `validate` → `profile` → read references →
  write result → `validate` → `check-plan` was a clean, well-documented loop;
  the worked examples in `spec.md` (the exact loans-join and branch-staffing
  callout text) matched this fixture closely enough that I could sanity-check
  my own reasoning against them as I went.
