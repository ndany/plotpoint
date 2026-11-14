# Design notes: visualize

Why the skill is shaped the way it is, and what testing found. Repository-wide
decisions are in `docs/decisions.md`; this file covers the skill itself.

## Shape

- **Storytelling first.** Every step starts from the question and the audience:
  the chooser asks what the reader must see before what the data looks like;
  headlines state takeaways; highlight and callouts point at the claim.
- **Judgment vs computation.** The model decides story, form, headline,
  emphasis and outlier handling. Scripts profile, shape, draw and check, so
  output is repeatable and numbers are verified against the data.
- **Intent vs rendering.** One intent per visual, identical in every format;
  the technique varies per target, with compensations recorded.
- **Profiles, not rows.** The model reads a small profile built so outliers
  and extremes can't hide; the renderer always reads the full data.
- **Advice, not authority.** Storyboard recommends; the caller decides. Without
  the caller's takeaway, headlines are drafts.

## Checks and what they can't see

| Check | Proves | Doesn't prove |
| --- | --- | --- |
| `headline_numbers` | Each number is derivable from the data | That the sentence compares the right things |
| `outliers` | Every flagged column has an explicit handling | That the handling is wise |
| `callouts` | Every rule and point callout is pinned to something drawn | That labels don't overlap |
| `legibility` | Text ≥ 11 px at the narrowest expected width | Clutter |
| `capacity` | What was folded or warned | Whether the folded form still tells the story |

Hence render step 5: look at the output.

## Test findings

### 2026-11-01: v1 recorded runs (T1–T3) and visual review

Three independent agents, given only the skill folder and the request (answer
files removed). Runs: `tests/fixtures/library-review/runs/2026-11-01-*`.

| Run | Result |
| --- | --- |
| T1 (mode A, with draft) | Met E1–E11 except the original E9 ("some visual differs by format"): it chose SVG over Mermaid in Markdown so the callout carrying "18%" stays on the chart. That's a defensible trade-off, so `targets.md` now calls Mermaid a trade-off, and E9 now checks that every target is planned (differential rendering is tested deterministically in T4) |
| T2 (mode B) | Meets E1–E11 |
| T3 (mode C, five visuals) | All checks pass after fixes, but three times the checks passed while the chart was wrong: unmatched point callouts were silently dropped |

Changes made in response:

| Finding (runs) | Change |
| --- | --- |
| Point callouts that matched nothing vanished without a warning (T3) | New `callouts` check fails on unpinned callouts; matching accepts column or display names; scatter points match by label, plus x when labels repeat |
| One outlier method per visual couldn't say "Riverside is the story, Central is real" (T1, T2, T3) | `outlier_handling` takes a list with one entry per `column` |
| Rule callout text drawn once per data row (T1) | Callout layers carry a single datum |
| "1,510" (an absolute change) failed while "3.2%" passed (T3) | Absolute changes count for the same comparisons as percent changes; rules documented in `spec.md` |
| Merged visuals had nowhere to say which table to render (T1) | Storyboard visuals take optional `data` and `data_note` |
| Appendix tables required a takeaway headline (T1) | `headline_status: title` for reference visuals |
| No way to check a plan without drawing (T1, T2) | `render --dry-run`; storyboard dry-runs each visual before returning |
| Tables reported "no outliers" and a pixel size (T3) | Tables skip the outlier check; text, table and Mermaid outputs report no size |
| Callouts on tables and numbers were lost (review) | They become notes |
| Undocumented: callout pinning, automatic direct labels, `units` per type, table `sort`, multiple accents, skew flag, number technique, `compensations` when empty, mode C flow, dataviz for render-only work (T1–T3) | Documented in `spec.md`, `targets.md`, `storyboard.md`, `profiling.md`, `SKILL.md` |
| HTML figures stacked with no space between them (review of `page.html`) | Document figures get a bottom margin |
| Scatter x axis labelled every integer (review) | Fewer ticks |

### 2026-11-01: second round (T2b, T3b) after the fixes above

| Finding (run) | Change |
| --- | --- |
| The headline check passed wrong numbers: "fell 22%" matched a share of a time series, "fell 25%" the gap between two series, "fell 3%" a 3% rise, "half within 12" one of 300 raw values; and a pass never said what matched (T3b) | Check rewritten: matches are listed; shares only on bars and tables; changes only along a series or against `previous`; direction words checked; raw values only up to 50 rows (configurable); distribution claims ("82% within 15", "half within 7.8", "1 in 10") checked as pairs; rules tabled in `spec.md` (D-23) |
| Rule labels at nearby x values ran together (T3b) | Overlapping rule labels stack; distant ones stay level |
| A storyboard had to hand-write a render request per visual to dry-run it (T2b) | `visualize.py check-plan REQUEST RESULT` dry-runs the whole plan and shows text outputs |
| Merged tables had no owner at dry-run time; `sentence` underspecified; audience could only narrow; color-map example contradicted its rule; one `source` for merged data (T2b) | Documented: build the merge file before dry-running; `sentence` fields row and outlier skip; widen audience for decisions with a `sentence` summary; color-map rule restated; join sources |
| Mode C couldn't profile inline data (T3b) | `profile` accepts a render request |
| Legibility reported sizes for text and tables (T3b) | Skipped for them |
| Profiles used YAML anchors (T3b) | Written out in full |
| No guidance for series on very different scales, or an accepted outlier squeezing a scatter (T3b) | Added to `chart-chooser.md` and `profiling.md` |
| Expectations E6 and E8 penalized a board-level `sentence` summary the skill now recommends (T2b) | E6 counts charts only; E8 allows a summary `sentence` or `number` on top |

### 2026-11-01: third round (T3c), with probes

A fresh tester rendered the five requests and probed the headline check with
24 deliberately wrong or tricky headlines. It caught wrong direction, wrong
rounding and invented values, but passed 8 wrong ones. Re-run after the fixes
(`runs/2026-11-01-T3c/probes-after-fixes.md`): 5 of the 8 now fail.

| Finding | Change |
| --- | --- |
| Another row's value passed ("Central's wait is 48" when 48 is Riverside's) | Candidates carry the rows they belong to; when a clause names a row, only its figures (or an aggregate introduced by "median", "total"...) match |
| "8 times" matched a raw 8 | Multiples fail with "state both values" |
| A wrong share matched a change between unordered table rows | Changes only along ordered axes |
| "1 in 10 ... more than 25" passed: share and threshold checked apart | Ratios pair with their threshold like percents |
| A true share on a line chart ("E-book is 43% of loans") couldn't pass | Each measure's share of its row total counts on multi-series charts |
| Details named scatter points by x value | Details name the row (branch, quarter) |
| Render printed ~15 KB of SVG | `render --checks-only` |
| The number tile used the accent color for text | Ink, like all text |
| Histogram y title fixed at "Count"; `bins` unmentioned | `names: {count: ...}`; bins in render step 2 |
| Profile said `string`; skew flagged on 5-point series | `text`, as documented; skew needs at least 8 values |
| How to view an SVG, and that it lacks headline and source | Render step 5 |

Still passing, by design: a real change over a different window (P1, P4); the
detail names the window and step 4 says to confirm it. Numbers inside words
("FY27") aren't checked.

Open, in the backlog: no control over label placement (T3 r3's label sits on a
gridline); bin edges aren't derivable numbers; nothing checks that a headline
number is *visible* (T2b); a `preview` command that shows the chart with its
headline and source (T3c); Mermaid legends need 11.17.
