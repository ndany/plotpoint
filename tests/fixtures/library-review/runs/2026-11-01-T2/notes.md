# Storyboard T2: notes for the calling skill

Result: `storyboard-result.yaml` (validates as `storyboardResult`).

## Drafts to confirm

- **v2** (active members, summary): "48,210 people are active members, up 3.2% from 46,700". The data doesn't say which period `previous` is. Name it.
- **v4** (wait histogram, body): "The median visit waits 7.8 minutes, and 82% of visitors are helped within 15 minutes". 82% is 245 of 300 visits under 15 min. The 15-min threshold is my choice. Swap it if the service has a target.
- **v5** (branch table, appendix): its headline is descriptive (a table has no takeaway). Confirm it or rewrite it.
- v1 and v3 use the caller's takeaways as written (`confirmed`).

## Decisions for the caller

1. **Cut café sales** from q2. Revenue doesn't measure active use. You could keep it as q1 context instead, since June is the low month.
2. **q1 wording:** total loans in Q3 '26 (1,035) are still below Q1 '26 (1,230), because print kept falling. The takeaway is accurate, but the prose should not suggest that total use has recovered.
3. **q3 evidence:** at 4.5 FTE, Riverside has 96k visits and Eastgate has 38k. Decide whether to compare waits against visits per FTE before concluding which branches need more staff.
4. **Board visibility of q3:** should the board get a one-sentence staffing summary, if they approve staffing?
5. For v1, render from the merged `quarter, print, ebook` file (`data/derived/loans_by_quarter.csv`).

## Skill feedback

1. **The request fixture references `expected.yaml` and `docs/testing.md`** in its comments. That is harmless, but it leaks test scaffolding into what the skill reads.
2. **There is one `outlier_handling` per visual, but outliers are flagged per column.** In v3 the scatter has two flagged measures that need different handling: Riverside's wait is the story (`callout`), and Central's FTE should be `accept`. There is no way to state both, so I put the second one in `reason`. The `outliers` check may treat it differently; I can't tell without rendering.
3. **For `point` callouts on a scatter, it's unclear what `x` holds.** Spec says `label` is "used by highlight and callouts", so I assumed `x: Riverside` (the label value). The spec doesn't say whether to give the label or the numeric x.
4. **Table `sort` is unclear.** The enum is `value | data | label`, but for a table with several numeric columns it doesn't say which column `value` sorts by. My first try, a column name, failed validation. Spec says only "optional `columns` order, `sort`, `names`".
5. **It's unclear whether `highlight` works on `table` and `number`.** The intent schema allows it everywhere, but the docs only describe it for charts.
6. **It's unclear whether `color_map` can map two entities to `accent`.** I mapped E-book and Riverside to `accent` (different visuals, each is its own story's subject). storyboard.md says "the story's subject → accent", singular. Can two entities share it if they never appear in the same visual?
7. **Skew flags on 5-point series (`print`) need `accept`.** profiling.md mentions this, but `none_flagged` vs `accept` is unclear when only a skew flag (no IQR outliers) is present. Does the `outliers` check care about skew?
8. **The storyboard can't check headline numbers before render.** There is no way to know whether the checker can derive "82%" or "−18%" (computed totals and percentages). A `check` or dry-run command for intents would catch this before the caller confirms.
9. **There is no guidance on choosing between `text` and `svg` for `number` visuals per target.** targets.md lists `text` for "a single number" in Markdown, but says nothing about which to prefer for a stat tile in HTML.
10. **`units` on a scatter or histogram is ambiguous.** It's a single axis title, but a scatter has two measured axes, and a histogram's y is a count. I used `names` for the axes and `units` for y. The intent is a guess.
11. **The `add-summary` kind has no guidance for when the board is not the audience of a decision-bearing question** (q3 here). I used `placement`. A sentence on narrowing or widening audiences would help.
12. **The empty `compensations: []` vs omitting it:** both validate, and the spec doesn't say which to use.
