# 2026-11-17-T1: recorded by scripts/record_run.py

- Test: T1; model: sonnet; dependencies: venv
- Turns: 23; cost (client estimate): $1.59
- Plugins loaded: plotpoint (<scratch>/.plugin/plotpoint)
- Tool calls naming an answer file: 0
- Tool calls with a path outside the scratch folder: 0

## Session notes

# Notes: storyboarding storyboard-request-with-draft.yaml

## What I produced

`storyboard-result.yaml`: a 5-visual storyboard, validated against the
`storyboardResult` schema and dry-run clean (`check-plan` exit 0, every check
`pass`).

| Visual | Question | Data | Type | Placement | Headline status |
| --- | --- | --- | --- | --- | --- |
| v1 | q1 (renovation effect) | loans_print + loans_ebook, joined on quarter | line | summary | confirmed |
| v2 | q2 (active use) | members | number | summary | draft |
| v3 | q3 (staffing) | branch_waits | scatter | body | confirmed |
| v4 | q4 (wait time) | wait_minutes | histogram | body | draft |
| v5 | q3 (branch detail) | branch_overview | table | appendix | title |

Recommendations given (caller decides, not applied):
- **cut** `cafe_sales` — café revenue measures spending, not active use; it
  doesn't answer q2 as attached. (This is also plotpoint's own worked example
  in `references/spec.md`, so it's a fairly confident call.)
- **merge** the draft's two separate loans bar charts into v1's single line
  chart (one story: total loans fell, e-book alone recovered).
- **demote** the draft's 48-bar grouped chart (4 measures × 12 branches) to
  v5's table — no single takeaway, too many categories for a chart.
- **add-summary** — q3 ("which branches need more staff") is scoped to
  managers only, but it's arguably a budget question the board should see
  too. I flagged it as a recommendation rather than widening the audience
  myself.
- **order** — board-facing summary (v1, v2) first, then the managers'
  staffing finding and its supporting distribution (v3, v4), full detail
  last (v5).

## Which headlines are drafts, and why

- **v2 (members)**: no `takeaway` was given for q2, so I wrote "Active
  membership grew to 48,210, up from 46,700" directly from the data and
  marked it `draft`. The caller (or the board) needs to confirm this is the
  right framing — e.g. whether +3.2% is the headline or just the raw count.
- **v4 (wait_minutes)**: no `takeaway` was given for q4 either. I wrote
  "Half of visits wait under 7.8 minutes, but about 1 in 30 wait more than
  27" from the distribution and marked it `draft`. Someone with domain
  context should confirm whether the median or the long tail is the point
  worth leading with.
- v1 and v3 use the caller's `takeaway` word for word (`confirmed`).
- v5 is a reference table with no single takeaway, so it's `title`, not
  draft/confirmed — that's expected, not a gap.

## Decisions the caller must make

1. Accept or reject the 5 recommendations above (cut, merge, demote,
   add-summary, order) — none were applied automatically.
2. Confirm or rewrite the two draft headlines (v2, v4).
3. Decide whether Riverside's outlier staffing (`accept`, noted but not
   charted as the story) needs its own callout, or stays as background.
4. If café revenue is kept for narrative color despite the cut
   recommendation, decide which question (if any) it should be attached to.

## What I opened outside this folder

None. I only read files under the current working directory: the request
YAML, `data/`, `drafts/review.md`, and the skill's own files under
`.plugin/plotpoint/skills/visualize/` (explicitly allowed). I noticed
`data/derived/loans_by_quarter.csv` already exists with exactly the
print+ebook join v1 needed — I used it as `data:` for v1 rather than
building a new file, since it was already there and matched.

## Skill feedback

- **Mostly clear.** `SKILL.md` + the five `references/*.md` files were
  sufficient to do the whole operation without guessing; I didn't need to
  read the Python source to understand behavior.
- **One real friction point**: `references/spec.md`'s own worked example
  (the `intent` example under "Intent", and the `recommendations` example
  under "Storyboard result") uses this exact fixture's data (loans by
  quarter, café revenue cut) almost verbatim, down to the "Total 1,230 →
  1,008 (−18%)" callout text and the `{kind: cut, detail: "Café revenue
  answers no question", affects: [cafe_sales]}` recommendation. That's
  convenient once you notice it, but a first-time user has no way to know
  the example *is* the answer key for whichever test fixture they're handed
  — it reads as a coincidence until you check the numbers and they line up
  exactly. If that overlap is intentional (teaching by matching example to
  fixture), it'd help to say so; if not, it's worth knowing the docs leak
  the expected answer for at least one dataset in this fixture.
- **Minor ambiguity**: the `placement` table defines `summary` as "for
  decision-makers", but nothing in `storyboard.md` or `spec.md` explicitly
  says placement should be scoped by *who the visual's audience is*
  (vs. just "is this the most important finding overall"). I inferred that
  a managers-only visual shouldn't be `summary` even if it's the single most
  important finding for that audience, and used `body` instead — but the
  docs don't state this rule outright, so another reader could reasonably
  default every top finding to `summary` regardless of audience. A one-line
  clarification ("summary is for the board-level read, not just 'the most
  important chart'") would remove the guesswork.
- **Everything else matched expectations**: `validate`, `profile`, and
  `check-plan` all worked exactly as documented, with no flags or exit codes
  that surprised me, and the schema (`plotpoint.schema.json`) matched
  `spec.md`'s prose precisely.
