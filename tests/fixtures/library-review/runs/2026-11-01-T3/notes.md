# T3 render run: notes

All five requests ran in mode C: I wrote each request without an intent, validated it, profiled the data, then added the intent, validated again and rendered. Targets were `md/document` and `html/document`.

## r1: loans by quarter. `line` (svg in both targets)
- **Why a line:** the question is about change over time across 5 quarters. There are two series (print, e-book). E-book is highlighted because the second half of the takeaway is about it. Print is shown in context gray.
- **Headline:** the caller's takeaway (confirmed). The 18% is a change in the *total*, which the chart doesn't plot, so I added a `rule` callout at Q2 '26: "Total 1,230 → 1,008 (−18%)". I also added a `point` callout at the e-book endpoint.
- **Outliers:** the profile flagged print as skewed (−2.0). I set `accept`, because the renovation step-down is the story.
- **Checks:** all pass.
- **Fixed after looking:** the point callout was missing from the first render. I had written `series: ebook` (the column name), but the renderer matches on the display name `E-book`. After fixing that, the callout text "445, a new high" repeated the automatic endpoint label "E-book 445", so I shortened it to "New high".

## r2: active members. `number` (text technique in both targets)
- **Why a number:** the question asks for a single figure, so a stat tile with the change from the previous count answers it.
- **Headline:** draft.
- **Checks:** the first render failed `headline_numbers` on "1,510". That is the absolute change (48,210 − 46,700), and the check doesn't treat it as derivable, but it did accept "3.2%", which is also derived. The tile doesn't show 1,510 either. I rewrote the headline as "48,210 people actively use the library, up 3.2% from 46,700 at the previous count". After that, all checks pass.

## r3: branch waits vs staffing. `scatter` (svg in both targets)
- **Why a scatter:** the takeaway compares wait times *at similar staffing*, so both measures need to be plotted. Riverside is highlighted.
- **Outliers:** set to `callout`. Riverside's 48-minute wait is the story. Central's 24 FTE is a real, larger branch and is drawn as-is. The note about Central lives only in the `reason`, because one method has to cover both flagged columns.
- **Checks:** all pass.
- **Fixed after looking:** the point callout was dropped silently on the first render. I had used `x: Riverside`, reading "`label` (point names, used by highlight and callouts)" to mean the callout's x could be the label. In fact it needs `x: 4.5` plus `series: Riverside`. Once that rendered, the callout text repeated the "Riverside" label, so I shortened it to "48 min at 4.5 FTE".
- **Remaining issue:** the callout text sits on the 50-minute gridline at the top of the plot. The skill offers no way to pad the domain or move the label.
- **Remaining issue:** Central's 24 FTE stretches the x-axis, so the other 11 branches are squeezed into the left third. I left it, since the takeaway still reads clearly: Eastgate, at the same 4.5 FTE, waits 15 minutes.

## r4: branch overview. `table` (table technique in both targets)
- **Why a table:** there are four measures in different units across 12 branches. One y-axis can't carry them, and the caller probably wants to look up each branch. Central is highlighted (shown in bold).
- **Headline:** draft: "Central leads on every measure…". An alternative the caller might prefer: Riverside has the second-highest visits (96k) but the joint-lowest staffing (4.5 FTE), which ties in with r3.
- **Outliers:** set to `accept`. The check still reported "no outliers flagged in plotted measures", so a table seems to be treated as having no plotted measures.
- **Checks:** all pass.

## r5: individual wait times. `histogram` (svg in both targets)
- **Why a histogram:** the question is about how 300 individual waits are spread out.
- **Headline:** draft, built on the median and the maximum. I added a `rule` callout at the median (7.8).
- **Outliers:** set to `accept`. The 10 IQR outliers are the real right tail.
- **Checks:** all pass after the fixes below.
- **Fixed after looking:**
  1. I had set `units: Visits`, meaning the y-axis (counts). It was applied to the **x-axis title**, which then read "Visits" instead of "Wait (minutes)". I removed it.
  2. A `point` callout at x=47.5 was dropped silently, because histogram rows are bins. I replaced it with a `note`, which renders under the chart, outside the SVG.
  3. My first note text said "(the bar at 45–50)". That failed `headline_numbers` because bin edges 45 and 50 don't count as data, so I removed it.

## Skill feedback

1. **Point callouts that match nothing are dropped silently, with no check result and no note.** This happened in 3 of my 3 point callouts on the first try, each for a different reason: a display name vs a column name in `series`; the scatter needing the x value plus `series` = label, rather than the label as x; and histogram bins. This is the biggest problem I found. The checks reported all `pass` while the headline's evidence was missing, and only looking at the output caught it. The render should fail or warn when a callout can't be placed.
2. **spec.md doesn't say how to target a scatter point by name.** The callout table says `point` takes "`x`, optional `series`". The scatter row says `label` is "used by highlight and callouts" but never says the label goes in `series`. Using `series` to mean "point label" is surprising.
3. **`series` matching is inconsistent.** `highlight` accepts "column names or display names", but a point callout's `series` seems to accept only the display name. My `series: ebook` failed even though `highlight: [ebook]` worked.
4. **`units` isn't documented per visual type.** The spec calls it an "optional axis title" without saying which axis. For a line chart it labels y; for a histogram it labels x and overrides `names`. A histogram's natural unit (minutes) vs count (visits) makes this easy to get wrong.
5. **The `headline_numbers` rule on what counts as "derivable" is undocumented and inconsistent.** A percent change (3.2%) passes, but the absolute difference (1,510) fails. Bin edges (45, 50) fail, but a total computed by summing columns (1,230 → 1,008) passed. The skill should list which derivations are recognised. "Every number … must be derivable" is too vague to write against.
6. **Point callouts on a histogram aren't covered.** The spec doesn't say whether `point` works for histogram or bar, or what `x` refers to (a raw value or a bin).
7. **Callouts repeat automatic labels.** Highlighted series and points get automatic end or point labels such as "E-book 445" and "Riverside", but the skill doesn't mention them. As a result, a callout naturally written as "Riverside: 48 min…" duplicates the label. Documenting the auto-labels would avoid a re-render.
8. **One `outlier_handling` per visual.** When two plotted measures are flagged for different reasons (r3: Riverside is the story, Central is accepted as real), the single method can't express both, so I folded the second into the `reason` text.
9. **The table/outliers interaction is unclear.** For a table I set `accept`, but the check said "no outliers flagged in plotted measures". If tables are exempt, profiling.md and the render step should say so, so callers don't have to decide.
10. **There is a contradiction about non-v1 types.** spec.md and chart-chooser.md say the renderer *refuses* other chooser types. The schema's `visualType` description says they are "rendered best-effort".
11. **Step 1 says to validate the request, but a mode-C request has no intent yet.** So validation happens twice: once without the intent and once after adding it. That's harmless, but the SKILL.md wording ("add the intent to the request") implies editing the request file, which then holds both `question` and `intent`. It would help to say whether that is expected or whether the intent should replace `question`.
12. **The "load dataviz when present" rule is ambiguous in the render operation.** The theme already applies dataviz, and render exposes no colour or mark choices. It's unclear whether a render-only session should load dataviz at all. I didn't.
13. **The skill suggests no way to look at text-technique outputs.** Step 5 says to "open the PNG or SVG". For the number and table outputs there is no file, and `files` is empty, so I could only inspect the snippet. The result also reports `width: 960, height: 432` for text outputs, which is meaningless there.
14. **There is no layout control for callouts:** no padding, offset or placement. The r3 callout overlaps the top gridline, and I had no way to fix it within the intent.
