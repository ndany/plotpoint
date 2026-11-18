# 2026-11-18-T2: recorded by scripts/record_run.py

- Test: T2; model: sonnet; dependencies: venv
- Turns: 24; cost (client estimate): $1.54
- Plugins loaded: plotpoint (<scratch>/.plugin/plotpoint)
- Tool calls naming an answer file: 0
- Tool calls with a path outside the scratch folder: 0

## Session notes

# Notes: testing plotpoint:visualize (storyboard operation)

## What I produced

`storyboard-result.yaml` — a storyboard for `storyboard-request.yaml`'s four
questions, built by: validating the request, profiling all seven datasets,
planning the story (merge/demote/cut decisions), writing one intent per
visual, and dry-running the whole plan with `check-plan`. Every check
(`headline_numbers`, `takeaway`, `outliers`, `callouts`, `legibility`,
`capacity`, `render`) passed for all five visuals on the first pass after
I'd read the fixture data.

Five visuals, in the order they'd appear:

- **v1** (summary, board+managers) — line chart, print vs. e-book loans by
  quarter, merged from `loans_print` + `loans_ebook` into the existing
  `data/derived/loans_by_quarter.csv`. Headline is the caller's `takeaway`
  word-for-word → `confirmed`.
- **v2** (summary, board) — number tile, active members (48,210, +3% vs
  46,700). No `takeaway` was given for q2 → headline is `draft`.
- **v3** (body, managers) — scatter, staff FTE vs. average wait per branch,
  from `branch_waits` only. Headline is the caller's `takeaway` word-for-word
  → `confirmed`. Riverside highlighted; Riverside's wait outlier handled as
  `callout` (it's the finding), Central's staffing outlier handled as
  `accept` (real, not the point).
- **v5** (body, managers) — histogram, individual wait times from
  `wait_minutes`. No `takeaway` was given for q4 → headline is `draft`.
- **v4** (appendix, managers) — reference table from `branch_overview`
  (visits, open hours, staffing, events per branch). No single takeaway
  fits four measures across twelve branches, so it's a table with
  `headline_status: title`, not a chart.

`cafe_sales` was cut (no `cafe_sales` visual exists) — it measures café
revenue, not library usage, and doesn't answer q2 or any other question.

## Headlines that are drafts, and why

- **v2** — `"Active membership grew 3% to 48,210 members"`. q2 carries no
  `takeaway` in the request, so per the skill's rule ("Without a takeaway,
  headlines are draft") this is draft. The 3% is my rounding of 46,700 →
  48,210 (+3.23%); someone should confirm the number and phrasing.
- **v5** — `"Median wait is 7.8 minutes, but some visitors wait more than 30
  minutes"`. q4 also carries no `takeaway`. I chose the median (checked
  figure) plus a plain-language reading of the long tail (10 of 300 waits
  are flagged outliers, 6 of them past 30 minutes); someone should confirm
  this is the intended framing of that distribution, not just a
  checks-passing sentence.
- **v4**'s headline is a descriptive `title` (not a draft takeaway) — it's a
  reference table, exempt from that distinction by design.

v1 and v3 use the request's own `takeaway` text unchanged, so they're
`confirmed`.

## Decisions the caller must make

1. **Confirm or rewrite the two draft headlines** (v2, v5) above.
2. **Accept or reject the merge** of `loans_print` + `loans_ebook` (v1 reads
   from `data/derived/loans_by_quarter.csv`, which already existed in
   `data/derived/` and matches the join I'd have built).
3. **Accept or reject cutting `cafe_sales`** — it currently has no visual.
4. **Accept or reject demoting `branch_overview`** to an appendix table
   instead of a chart.
5. **Decide on the `add-summary` recommendation for v3**: Riverside's
   staffing gap is a managers-only visual, but it plausibly bears on a board
   budget decision. I proposed (not applied) either a one-line
   sentence/number for the board or showing v3 to them directly — the
   storyboard rules forbid widening audiences without the caller's sign-off,
   so this is left as a recommendation, not an applied change.
6. **Confirm the color map** (`E-book`/`Riverside`: accent, `Print`:
   context) reads correctly once rendered — I haven't rendered the actual
   images, only dry-run the checks (per the skill's storyboard steps, full
   rendering is a separate `render` operation).

## Opened outside this folder

None, other than the skill's own files under `.plugin/plotpoint/skills/visualize/`
(SKILL.md and `references/spec.md`, `references/storyboard.md`,
`references/targets.md`, `references/chart-chooser.md`), which the task
explicitly allowed since they're loaded from the plugin, not the repo.

## Skill feedback

- **`add-summary` / `placement` recommendations have no documented shape.**
  `spec.md`'s only worked examples of `recommendations[]` are `merge` and
  `cut` (just `kind`/`detail`/`affects`). `storyboard.md` says an
  `add-summary` recommendation should carry "a one-line `sentence` or
  `number`... with the question it answers and why it bears on their
  decision," which reads like it wants a structured field, but the schema
  (as far as `validate` let me use it) only exposes free-text `detail`. I
  ended up writing the proposed sentence as prose inside `detail`; a worked
  example for `add-summary`/`placement` in `spec.md` would remove the
  guesswork.
- **"Callout" is overloaded in `outlier_handling`.** The `callout` *method*
  for outlier handling just needs "a highlight or callout naming it" — in my
  case a plain `highlight: [Riverside]` (no explicit `callouts:` entry)
  satisfied it, confirmed by `check-plan`. Someone skimming could easily
  assume the `callout` outlier method requires an actual `callouts:` list
  entry, since the word is also a top-level intent field. A one-line note in
  `spec.md`'s Outlier handling table ("a `highlight` alone counts as naming
  it") would help.
- **Derived-file convention is implicit.** Building a merged table for a
  multi-dataset visual (`data` + `data_note`) is well-explained, but neither
  `storyboard.md` nor `spec.md` states a convention for *where* that file
  should live (I used `data/derived/<name>.csv`, inferred from the spec.md
  worked example's path, and it happened to already exist in this fixture).
  Spelling out the convention explicitly would help a first-time user who
  doesn't have a pre-built file to crib from.
- Everything else (profiling output, `check-plan`'s per-visual detail
  explaining exactly which rows/columns matched each headline number, the
  render-flag table) was clear enough to work from without guessing.
