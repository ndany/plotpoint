# 2026-11-16-T2: recorded by scripts/record_run.py

- Test: T2; model: sonnet; dependencies: venv
- Turns: 31; cost (client estimate): $1.68
- Plugins loaded: plotpoint (<scratch>/.plugin/plotpoint)
- Tool calls naming an answer file: 0
- Tool calls with a path outside the scratch folder: 0

## Session notes

# Notes: storyboarding storyboard-request.yaml

## What I produced

Ran the `plotpoint:visualize` skill's **storyboard** operation on
`storyboard-request.yaml` (mode B: all 7 datasets, no draft). Steps taken,
per the skill's instructions:

1. Validated the request (`visualize.py validate storyboardRequest ...`) — valid.
2. Profiled all 7 datasets (`visualize.py profile ...`) and read the profiles
   (outliers, dominance, extreme rows) rather than raw data.
3. Planned the story by hand, following `references/storyboard.md`.
4. Wrote `storyboard-result.yaml` (5 visuals, 5 recommendations, 1 color map).
5. Validated the result and dry-ran every visual with `check-plan` — all
   checks (`headline_numbers`, `takeaway`, `outliers`, `callouts`,
   `legibility`, `capacity`, `render`) came back `pass` or an expected `skip`
   (skips are only where no takeaway was given, or where a text/table output
   has no fixed font size to check).

Result: `storyboard-result.yaml`, 5 visuals:

| id | question | visual | placement | audience |
| --- | --- | --- | --- | --- |
| v1 | q1 (renovation & use) | line, print + e-book loans merged | summary | board, managers |
| v2 | q2 (active users) | number, active members | summary | board |
| v3 | q3 (staffing) | scatter, staff vs. wait, Riverside highlighted | summary | board, managers |
| v4 | q3 (staffing detail) | table, all branch metrics | appendix | managers |
| v5 | q4 (wait times) | histogram, individual visit waits | body | managers |

Key recommendations given alongside the plan:
- **Merge** loans_print + loans_ebook into one line chart (same quarters, same
  measure family) rather than two bar charts.
- **Cut** `cafe_sales` from q2: café revenue measures sales, not people, so it
  doesn't answer "how many people actively use the library." The question is
  answered by active membership alone.
- **Demote** `branch_overview` to an appendix table: four measures across
  twelve branches have no single takeaway (would be a 48-bar grouped chart).
- **Widen** v3's audience from managers-only to board+managers and placed it
  in `summary`: Riverside's staffing gap bears on a resourcing decision
  ("which branches need more staff"), which the board should see too, not
  just the managers it was scoped to.
- **Order**: q1 (the renovation's effect on loans) leads, since it matches the
  write-up's title and is the primary audience's (board) main question.

## Which headlines are drafts, and why

- **v1** (loans): `confirmed` — uses the caller's `takeaway` word for word.
- **v2** (active members): `draft` — q2 has no `takeaway` in the request.
  I wrote "Active membership grew to 48,210, up from 46,700"; a person should
  confirm this before publishing.
- **v3** (branch staffing): `confirmed` — uses q3's `takeaway` word for word.
- **v4** (branch overview table): `title` — it's a reference table with no
  single takeaway, as the spec requires for appendix-style tables.
- **v5** (wait histogram): `draft` — q4 has no `takeaway`. I wrote "82% of
  visits wait 15 minutes or less, but some stretch to 47.5," derived from the
  profile; a person should confirm it (and confirm it's the finding they want
  led with — the data could just as easily support "most waits are short" as
  the frame).

## Decisions the caller must make

1. **Confirm or edit the two draft headlines** (v2, v5) — no `takeaway` was
   given for q2 or q4, so I wrote them from the data.
2. **Confirm the cut of `cafe_sales`.** I judged it doesn't answer q2 as
   worded ("how many people actively use the library" — a revenue figure
   isn't a usage count). If the intent was closer to "how healthy is the
   library's foot traffic," café revenue would belong as context instead, and
   the cut should be reversed.
3. **Confirm widening v3's audience to the board.** The request scoped q3 to
   `managers` only; I widened it because the takeaway bears on a resourcing
   decision. If the board shouldn't see branch-level staffing detail, this
   should be narrowed back (I'd still suggest a one-line `sentence` visual
   for the board in that case, as the skill's guidance allows either option).
4. **Confirm the Eastgate callout on v3** ("Eastgate: 4.5 FTE, 15 min wait") —
   I added it to ground "at similar staffing" in a concrete comparison; it's
   not required by the takeaway itself.
5. **`members` dataset has no explicit `previous`-period label** (just a
   "previous" column) — I assumed it's prior-year, matching "a year earlier"
   phrasing would need confirmation since the request doesn't state the
   period for `previous`. I kept the headline period-neutral ("up from
   46,700") to avoid asserting a time span the data doesn't confirm.

## Anything opened outside this folder

None. I only read:
- `storyboard-request.yaml` (the task's target file) and the `data/` files it
  points to, all inside this folder.
- `drafts/review.md`, inside this folder — **not needed for this task** (it's
  the draft used by `storyboard-request-with-draft.yaml`'s mode-A run, not by
  the no-draft `storyboard-request.yaml` I was asked to storyboard). I opened
  it while surveying the folder's contents before realizing it belonged to a
  different request file. It didn't influence `storyboard-result.yaml` — mode
  B's plan was built from the profiled datasets and the request's own
  questions/takeaways only.
- I did **not** open `storyboard-request-with-draft.yaml`.
- The skill's own files under `.plugin/plotpoint/skills/visualize/` (SKILL.md,
  `references/*.md`, `scripts/*`, `schemas/*`) — explicitly allowed as the
  skill's own files.

## Skill feedback

What was unclear, wrong, or missing while using the skill as a first-time user:

- **No `uv` on PATH wasn't a problem, but the instructions don't say what to
  check for.** SKILL.md says "Run `uv run ... ` when `uv` is on PATH ...
  Otherwise use `python3`." That worked fine once I checked `which uv`
  myself, but a one-line "check with `which uv`" would save the lookup.
- **The worked examples in `spec.md` and `storyboard.md` use literally this
  fixture's data** (the loans Q2-renovation 18% example, the Riverside/Central
  outlier-handling example, the café-revenue cut example). That's great for
  learning the format by pattern-matching, but it means a new user can't tell
  whether they've reasoned through the fixture correctly or just copied the
  doc's own example back at it. Not a bug, just worth knowing: the docs
  effectively hand you the answer key for this specific practice dataset.
- **`fields.label` for a `number` visual is easy to miss.** The spec line
  ("label: column holding the label shown under the figure; `names` doesn't
  rename it") is correct but easy to skip past; I almost left v2's number
  tile unlabeled before re-reading it. A one-line example in the `number`
  row of the fields table (there's a dedicated table for every other type)
  would help.
- **Nothing in the docs states what `previous` in the `members` dataset
  represents time-wise** (prior month? Prior year?) — this is a request-data
  gap, not a skill gap, but the skill gives no steer on how to phrase a
  headline when the comparison period is unstated. I'd suggest the storyboard
  guidance mention: when a `previous` column's period isn't documented in
  `notes`, keep the headline period-neutral and flag it as a caller decision
  (which I did, but had to infer that was the right move).
- **`check-plan`'s dry-run output is very large for `table`/`text` visuals**
  (it prints the full rendered Markdown/HTML, e.g. the entire 12-row HTML
  table inline) even though those have no image to sanity-check. A flag to
  suppress `text_outputs` in `check-plan` (mirroring `--quiet` on `render`)
  would make dry-running a storyboard with several tables much more usable in
  a terminal.
- Everything else (schema validation messages, the `_candidates`/`_changes`
  derivability rules, outlier-handling methods, capacity limits) matched the
  docs exactly and the dry-run checks were trustworthy — no surprises there.

## Maintainer review (2026-11-16)

E8 miss: v3 widens q3's audience to the board and places the scatter in
`summary`, and asks the caller to confirm (decision 3 above). Listed in
`known-misses.txt` so the suite stays green until the maintainer decides
whether this is acceptable judgment or a miss to fix in the instructions.
Decision (2026-11-17): the move followed `references/storyboard.md`, which
said to widen and then recommend. That applied a change to the caller's own
input before the caller agreed, so the instructions now say to propose it
only (D-35). E8 stays a known miss for this run until T2 is re-run.
