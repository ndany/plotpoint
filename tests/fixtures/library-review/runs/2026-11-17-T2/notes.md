# 2026-11-17-T2: recorded by scripts/record_run.py

- Test: T2; model: sonnet; dependencies: venv
- Turns: 24; cost (client estimate): $1.69
- Plugins loaded: plotpoint (<scratch>/.plugin/plotpoint)
- Tool calls naming an answer file: 0
- Tool calls with a path outside the scratch folder: 0

## Session notes

# Notes: plotpoint:visualize storyboard test

## What I produced

Ran the skill's **storyboard** operation on `storyboard-request.yaml` (Mode B —
no draft, 4 questions, 7 datasets, audiences `board`/`managers`, targets
`md/document` + `html/document`). Saved the plan as `storyboard-result.yaml`
in this folder.

Steps followed: `validate storyboardRequest` → `profile` → plan → write YAML →
`validate storyboardResult` → `check-plan` (iterated once on a failing check,
see below) → clean exit 0.

The plan has **5 visuals**:

| id | question | datasets | placement | audience | type |
| --- | --- | --- | --- | --- | --- |
| v1 | q1 (renovation vs. use) | loans_print, loans_ebook (merged) | summary | board, managers | line |
| v2 | q2 (active users) | members | summary | board | number |
| v3 | q3 (staffing) | branch_waits | summary | managers | scatter |
| v4 | q3 (staffing detail) | branch_overview | appendix | managers | table |
| v5 | q4 (wait time) | wait_minutes | body | managers | histogram |

Plus 3 recommendations (not applied, per the skill's rule that storyboard only
advises) and one document-wide `color_map` (`E-book`/`Riverside` → accent,
`Print` → context).

## Headlines: confirmed vs. draft vs. title

- **v1** and **v3**: `confirmed` — the request gave explicit `takeaway` text
  for q1 and q3, used verbatim. `check-plan` confirmed both takeaways match
  and every number in them (e.g. "18%", "1,230 → 1,008") is derivable from
  the data.
- **v2** and **v5**: `draft` — q2 and q4 had no `takeaway` in the request, so
  I wrote headlines from what the data shows ("Active membership rose 3.2% to
  48,210, up from 46,700"; "Half of visitors wait under 7.8 minutes, but
  about 18% wait 15 minutes or more") and marked them draft, per the skill's
  rule against inventing conclusions. A person should confirm these before
  publishing — the rendered files will carry a visible "DRAFT" mark until
  then.
- **v4**: `title` — `branch_overview` has 4 measures × 12 branches with no
  single takeaway, so it's demoted to a reference table with a descriptive
  title rather than a claim.

## Decisions the caller must make

1. **Cut `cafe_sales`?** It was attached to q2 ("how many people actively use
   the library") but it measures café revenue, not usage — I recommended
   cutting it rather than drawing a visual that answers no question.
2. **Show v3 to the board too?** q3 is scoped to `managers`, but Riverside's
   understaffing is a budget-relevant finding the board may want to see. I
   recommended `add-summary`/`placement` for the board, but did not widen the
   audience myself (the skill says never widen in the plan).
3. **Merge `avg_wait_min` into the appendix table (v4)?** `branch_waits` and
   `branch_overview` both key on `branch`/`staff_fte`; joining wait time in
   would let managers see staffing, visits and wait together in one table
   instead of two.
4. **Confirm the two draft headlines** (v2, v5) or supply real takeaways.
5. **Placement judgment call**: I placed v3 (Riverside scatter) as `summary`
   even though its audience is managers-only, reasoning that it's the primary
   decision-bearing finding for that audience, not just supporting detail.
   The spec doesn't say whether "summary" is reserved for the document's
   primary audience or can be a per-audience "read first" slot — worth the
   caller's sign-off either way (see Skill feedback below).

## What I opened outside this folder

None. Everything read was either inside this folder (`storyboard-request.yaml`,
`data/*`, `drafts/review.md` — the last one only out of curiosity; it isn't
referenced by `storyboard-request.yaml`, which has no `draft` key, so it played
no role in the plan) or the skill's own files loaded from the plugin
(`.plugin/plotpoint/skills/visualize/...`), which the task said were fine to
read. I did not open `storyboard-request-with-draft.yaml`, which sits in this
same folder but wasn't the file I was asked to storyboard.

## Skill feedback

- **Counts vs. shares in derivability checks, undocumented gap.** My first
  histogram callout read "7 visits (2.3%) waited 30+ minutes." `check-plan`
  passed the "2.3%" but failed on the bare count "7" ("not derivable from the
  data"). `spec.md`'s "Distributions" row documents that a *share* with a
  threshold is derivable ("82% within 15 minutes") but doesn't say a raw
  *count* for the same subset isn't checked the same way. I only found this
  by trial and error against `check-plan`; a one-line note in that table
  ("a count, unlike a share, isn't matched — state the share instead") would
  have saved a round trip.
- **`check-plan` has no quiet mode.** `render --quiet` suppresses the full
  snippet dump and prints only checks, but `check-plan` (which runs render
  `--dry-run` across every visual) has no equivalent, so checking a 5-visual
  plan with a table and a number visual means scrolling past a full
  12-row HTML table dump to find the one failing check. A `--quiet` passthrough
  would make iterating on a bigger storyboard much faster to read.
- **"Summary" placement semantics for a single-audience question are
  underspecified.** `storyboard.md`'s placement table defines `summary` as
  "decision-makers, read first," which reads as document-level, but a
  question can be scoped to a practitioner-only audience and still be the
  *main* answer to that question (not just supporting detail). It's unclear
  whether `summary` is meant to be reusable per-audience ("the managers'
  read-first item") or whether anything audience-scoped to practitioners
  should default to `body` even when it's the central finding. I made a
  judgment call (summary) and flagged it above for the caller to confirm;
  a worked example with a single-audience question placed in summary (or an
  explicit "no" in the docs) would remove the guesswork.
- Everything else matched the docs closely: `validate`, `profile` and
  `check-plan` behaved exactly as `spec.md`/`storyboard.md` describe, error
  messages were specific enough to fix without re-reading source, and
  `python3` ran the script directly with no missing-dependency prompt.
