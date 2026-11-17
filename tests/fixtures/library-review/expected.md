# Expected outcomes: library-review fixture

What a correct storyboard (modes A and B) and correct single-visual decisions
(mode C) must do for this fixture. Encoded as checks in
`tests/storyboard_expectations.py`; recorded runs in `runs/` are verified by
`tests/test_storyboard_runs.py`. The reference answer is
`storyboard-golden.yaml`. All data is invented.

## Storyboard (T1 mode A, T2 mode B)

| Id | Expectation | Why it's built into the fixture |
| --- | --- | --- |
| E1 | Valid against the `storyboardResult` schema | Contract |
| E2 | **Merge:** one visual uses both `loans_print` and `loans_ebook` | Two datasets, one story |
| E3 | **Order:** the first visual answers `q1` (the main question) and is in `summary` | The board reads the summary first |
| E4 | **Cut:** `cafe_sales` is recommended for cut and used by no visual | Attached to q2 but answers nothing about membership |
| E5 | **Demote:** `branch_overview` is shown as a `table`, or recommended for demotion | Four measures × twelve branches, no single story |
| E6 | **Outlier:** every chart (not table) using `branch_waits` handles the wait outlier explicitly (not `none_flagged`) and highlights or calls out Riverside | Riverside's 48-minute wait |
| E7 | **Drafts:** visuals for `q2` and `q4` (no takeaway given) have `headline_status: draft` | Never invent conclusions |
| E8 | **Audience:** detail visuals for `q3` and `q4` are for `managers` only and placed in `body` or `appendix`. Showing the board anything for them is proposed as a recommendation (`add-summary` or `placement`), not added to the plan (D-35) | Practitioner detail; the caller decides audiences |
| E9 | **Rendering:** every visual plans a technique for every requested target. (Whether techniques differ is a judgment; differential rendering itself is tested deterministically in T4) | Per-format planning |
| E10 | Mermaid is only planned for `line` or `bar` visuals | Renderer support |
| E11 | Every number in each headline is derivable from that visual's data (`headline_numbers` check) | Accuracy |
| E12 | A `confirmed` headline is the caller's takeaway as written; any edit (shortened, reworded, a number added) is `draft` (`takeaway` check) | q1 and q3 have takeaways; never put words in the caller's mouth |

Mode A (with the draft) should also name the draft's existing visuals in its
advice (for example, replacing the two loans bar charts). That's judged by
reading the run, not automatically.

## Single visuals (T3, mode C)

Each dataset, rendered alone with its question and no storyboard:

| Dataset | Expected `visual_type` | Notes |
| --- | --- | --- |
| loans (merged file) | `line` | Change over time |
| members | `number` | A single figure; headline `draft` |
| branch_waits | `scatter` (or `bar` of waits with Riverside highlighted) | Outliers handled explicitly |
| branch_overview | `table` | |
| wait_minutes | `histogram` | Headline `draft`; tail accepted or called out |

All render checks pass for each.
