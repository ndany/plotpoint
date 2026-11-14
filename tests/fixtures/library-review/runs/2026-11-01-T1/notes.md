# Storyboard T1: notes for the calling skill

Result: `storyboard-result.yaml` (validates as `storyboardResult`). There are five
visuals, in this order: v1 loans line (summary), v2 members number (summary),
v3 staffing-vs-wait scatter (body), v4 wait histogram (body), v5 branch table
(appendix). `cafe_sales` is cut.

## Headlines to confirm (drafts)

- **v2**: "Active members rose 3.2% to 48,210". You also need to say what
  `previous` (46,700) refers to: prior year or prior quarter. The tile's label
  depends on it.
- **v4**: "Half of the 300 surveyed visits waited 7.8 minutes or less; the longest
  took 47.5".
- **v5**: "Central is the largest branch by visits, hours, staff and events;
  Riverside has the longest average wait". This is an appendix table, so a
  plainer topic-style title may suit it better. Your call.
- v1 and v3 use your takeaways word for word (confirmed).

## Decisions you need to make

1. **Cut café revenue.** It answers no question; `q2` is about members. Either
   remove the section or give it its own question.
2. **v1 headline accuracy.** In Q3 '26 total loans (1,035) are still about 16%
   below Q1 '26 (1,230), because print hasn't recovered. "Recovered and grown"
   is true of e-book only. Decide whether the Conclusion should say this.
3. **Provide the merged data for v5.** Join `branch_overview` to `branch_waits`
   on `branch` to add `avg_wait_min`. v1 can use the existing
   `data/derived/loans_by_quarter.csv`.
4. **Central's 24 FTE** stretches v3's x-axis. The plan draws it to scale, with
   a note. The alternative is to exclude Central, but only you can decide that.
5. **Draft restructure:** Summary (v1, v2), then Waiting times (v3, v4), then
   Appendix (v5). Remove the 48-bar grouped chart and the two Mermaid loans bar
   charts.
6. If the visit survey can be exported with a branch column, v4 could show
   Riverside's visits against the rest.

I trial-rendered v1 to v4 in a scratch folder outside the run folder. Every
check passed, so the intents are renderable as written.

## Skill feedback

1. **A storyboard visual can't point at its render data.** The result schema
   has `datasets` (ids) but no `data` path. When visuals are merged (v1, v5), the
   intent's `fields` name columns of a combined table that exists only in a
   recommendation's prose. It would help to have an optional
   `visuals[].data` (or `derived_data`) field, or at least spec guidance on
   where to say it. storyboard.md only says "say in the detail".
2. **One `outlier_handling` per visual is too coarse.** In v3, two measures are
   flagged for different reasons: Riverside's wait is the story (`callout`), and
   Central's FTE is real context (`accept`). I had to choose `callout` and add a
   `reason`. The schema allows `reason` for any method, but the docs only
   mention it for `exclude` and `accept`. Per-column handling would be clearer.
3. **Scatter `point` callouts are underspecified.** spec.md says "`point`: text
   at one point (`x`, optional `series`)". For a scatter, I only found out by
   reading `vl.py` that `x` is the numeric x-value and `series` matches the
   `label` field (e.g. `{x: 4.5, series: Riverside}`). Two branches share 4.5
   FTE, so this matters. Document it, or allow `label:` on callouts.
4. **Doc-wide `color_map` vs. one accent per subject.** storyboard.md says "the
   story's subject → accent", but a document has several subjects (E-book in
   v1, Riverside in v3). I gave both `accent` since they never share a visual.
   It's unclear whether that's intended, or whether non-accent entities like
   "Eastgate" belong in the map at all.
5. **Skew flag vs. outlier rule.** The profile flags `print: skewed`, but
   profiling.md says only outlier and dominance flags need handling. It's easy
   to misread the flag as requiring `accept`. Saying "skew flags are
   informational" in SKILL.md step 2 would remove the doubt.
6. **No guidance on headlines for appendix tables.** Must a `table` intent have
   a takeaway headline? The schema requires `headline`, and SKILL.md says
   "takeaway, not topic", but a reference table often has no single takeaway
   (which is why it was demoted). Say whether a descriptive title is allowed
   there.
7. **`fields.sort` for tables** takes `value | data | label` but doesn't say
   which column `value` sorts by in a multi-measure table.
8. **Technique for `number` in HTML** isn't listed: targets.md lists
   `svg, vega, table, text` for HTML. Only the code (`render.py _technique`)
   shows that textual types default to `text`, which renders a styled tile.
   I chose `text`. One line in targets.md would settle it.
9. **Storyboard step 4 says decide each intent "without drawing it"**, but
   nothing suggests a dry-run render to check the headline numbers, outliers and
   callout matches. Those are exactly what fail at render time. An optional
   "check intents" command, e.g. `render --dry-run`, would let storyboard return
   intents it knows are renderable.
10. **Render-side (seen during the trial render):** in v4's SVG, the histogram
    `rule` callout text "Median 7.8 min" appears three times at the same
    position. It's probably drawn once per data row or bin. It's visually
    stacked, but it's redundant in the SVG and for screen readers.
11. **Small:** the request fixture's header mentions `expected.yaml` and
    `docs/testing.md`. These are out of bounds for this run, which isn't a
    skill problem, but a real caller would never see them.
