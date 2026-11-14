# T3b: render in mode C, r1–r5

All five requests validated as `renderRequest` before and after adding the intent.
Each was profiled (`profile --data`; r2 is inline, see feedback 4), rendered for
`md/document` + `html/document`, and the SVGs were converted to PNG
(`figures/r*/r*-md-document.png`) and viewed. In every chart the md and html SVGs
are byte-identical.

## r1: loans by quarter → `line`

- **Why:** change over time across 5 quarters, 2 series; the story is the
  renovation dip and the e-book recovery. E-book is highlighted, print is context.
  The total isn't plotted, so a `rule` callout at Q2 '26 carries
  "Total 1,230 → 1,008 (−18%)". I checked the figure by hand: 1,008/1,230 − 1 = −18.0%.
- **Headline:** the caller's takeaway, `confirmed`.
- **Fix after looking:** on a shared 0–800 axis, "recovered and grown" for e-books
  (410 → 445) is hard to see, and only the end value got a label. I added a
  `point` callout "Pre-renovation 440" at Q1 '26, so the reader can see that the
  latest 445 is a new high.
- **Checks:** headline_numbers, outliers, callouts (2 placed), legibility,
  capacity, render all `pass`. `print` is flagged as skewed (informational only).

## r2: active members → `number`

- **Why:** the question asks for a single count. A stat tile with the previous
  value beats a chart.
- **Headline (`draft`):** "48,210 people actively use the library, up 3.2% on the
  previous count". The period of `previous` is unknown, so the caller must confirm it.
- **Fix:** my first headline also said "up 1,510". It passed `headline_numbers`,
  but the tile only shows "+3.2% vs 46,700", so 1,510 appeared nowhere on the
  visual (that breaks the rule "every number in the headline must be visible").
  I dropped it. The check passed even though the output was wrong (feedback 2).
- **Checks:** all `pass`.

## r3: branch waits vs staffing → `scatter`

- **Why:** "which branches need more staff" plus the takeaway "at similar
  staffing" is about how two measures relate (FTE vs average wait). A sorted bar
  of wait alone would hide the staffing comparison. Riverside is highlighted, and
  a `point` callout on Eastgate ("same 4.5 FTE, 15 min") gives the comparison
  at the same staffing.
- **Outliers:** `avg_wait_min` → `callout` (Riverside is the story);
  `staff_fte` → `accept` (Central's 24 FTE is real). In the render, Central
  stretches the x axis to 26, so the 11 other branches crowd into the left third.
  The chart still reads, but the space is wasted.
- **Checks:** all `pass`.
- **Not fixed:** Riverside's direct label is just "Riverside", with no value
  (feedback 5). The headline has no number, so I left it.

## r4: branch overview → `table`

- **Why:** 4 measures × 12 branches with no single takeaway. A reference table
  (`headline_status: title`), sorted by visits (`sort: value`), with display names.
- **Checks:** all `pass`; outliers `skip` (tables are exempt).
- **Note:** I took "FY26" in the title from the storyboard request. The check
  never looks at it (feedback 1, last bullet).

## r5: individual wait times → `histogram`

- **Why:** how 300 individual waits are spread out.
- **Headline (`draft`):** "Half of visitors are helped within 7.8 minutes, but a
  quarter wait longer than 13 minutes". There are `rule` callouts at the median
  (7.8) and the upper quartile (13; Q3 = 13.025).
- **Outliers:** 10 flagged (27–47.5 min) → `accept`; they are real visits and part of the tail.
- **Fix after looking:** the two rule labels ran into each other
  ("Median 7.8 minUpper quartile 13 min"). All checks passed. I broke each
  label onto two lines with `\n`. They are separate now, but the second line of
  each label sits on the 100 gridline.
- **Checks:** all `pass`.

## Skill feedback

1. **`headline_numbers` lets wrong headlines through. It is the safety net for
   "never invent a conclusion", and it misses real errors.** I probed it with
   `--dry-run`:
   - r1 "Total loans fell **22%**" passes (the true figure is 18%). The percent
     pool includes each value's share of its column total, and for a time series
     that is meaningless: 805 / 3,603 print loans summed over 5 quarters = 22.3%.
     "Fell **19%**" passes the same way (e-book 410 / 2,145).
   - r1 "Print loans fell **25%**" passes (the true figure is 24.3%). It
     matched 24.6%, the gap between e-book and print in the *same row*
     (445 vs 590 in Q3 '26), through the "two measures in one row" rule. With
     shares, consecutive changes, first/last/peak changes and every in-row
     permutation all in one pool, a 5×2 table yields dozens of candidate
     percentages, so a near-miss is likely.
   - r5 "Half of visitors are helped within **12** minutes" (and "within **3**")
     passes, though the median is 7.8. Every raw value enters the pool, so on a
     300-row dataset almost any number in range "exists". The check means little
     on unaggregated data, which is exactly where a histogram headline needs it.
   - r1 "Total loans fell **3%** during the renovation" passes. 2.7% is the
     Q2 → Q3 total *rise*. The documented limit is "confirms a number exists,
     not its use", but the sign and direction of a change could be checked cheaply.
   - r3 "Riverside's wait is **8** times the median" passes because Elm Park has
     8 FTE. Ratios aren't supported, but they pass by coincidence.
   - Numbers glued to letters ("FY27", "Q5") are never tokenized, because the
     regex lookbehind excludes `\w`, so they are never checked.

   The pass detail never says *what* each number matched. If it said
   "18% = change in row total Q1 '26 → Q2 '26", a reviewer would spot a wrong
   match at once. Suggested fixes: report the match source; drop
   share-of-total when x is ordered or time; for a histogram or a dataset over N
   rows, don't put raw values in the pool (use summary stats only); check the
   direction of a change (fell vs rose).
2. **Nothing checks that headline numbers are visible.** SKILL.md step 2 says
   every number in the headline must be visible on the visual, but no check
   tests that. r2: "up 1,510" passed, though the tile shows only "+3.2% vs 46,700".
   A cheap check: each headline number must appear in the rendered text (axis
   ticks excluded), a callout, or a direct label.
3. **Overlapping callout labels pass every check (r5).** Two `rule` callouts
   about 140 px apart rendered as "Median 7.8 minUpper quartile 13 min". SKILL.md
   says checks can't see layout, and looking caught it. But the renderer knows
   both x positions and the text widths, so it could at least warn, or stagger
   the labels vertically. `references/spec.md` says "Label positions are
   automatic in v1", which suggests collisions are handled; they aren't. After
   my `\n` fix, the label text also sits on a gridline.
4. **Mode C can't profile inline data.** Render step 2 says "profile the data
   (`visualize.py profile --data FILE`)". r2 has `data: {inline: ...}`, and
   `profile r2.yaml` fails with a storyboardRequest schema error. There is no way
   to profile a render request or inline data short of writing a temp file. Make
   `profile` accept a render request (or `--inline`), or say in SKILL.md what to
   do.
5. **Scatter highlights get no value, against the spec.** `spec.md` (Intent →
   highlight): "Highlighted lines and points also get an automatic direct label
   with the latest value". The highlighted scatter point shows "Riverside" only,
   not "Riverside 48". Either draw the value or fix the spec, so callers know
   whether to add a point callout (the spec currently tells them not to).
6. **`legibility` reports px sizes for text and table outputs** (r2, r4:
   "smallest text 11.2px at 768px display"). Neither has a drawn size (the spec
   says so), so the check should `skip`. As it stands it claims something it
   didn't measure.
7. **There is no guidance on one shared axis when series differ in scale or
   when the story is in the smaller series.** In r1 the e-book recovery (410 → 445)
   is a nearly flat line next to print. The chooser offers only "index both to
   100" or two charts, as a "Never" footnote. A short note in chart-chooser or
   storyboard on choosing between index-to-100, small multiples, or a callout
   would help with a very common case. I fell back on a callout.
8. **Scatter axis stretching from an accepted outlier isn't addressed.** In r3,
   `accept` on Central's 24 FTE leaves about 60% of the plot width empty. The
   outlier methods are `callout`, `log_scale`, `exclude` or `accept`; none is
   "clip the axis with an annotation", and profiling.md doesn't mention that
   an outlier on the x axis squeezes the others. At least mention it in
   profiling.md.
9. **Minor points:**
   - Profile YAML uses anchors and aliases (`&id001` / `*id001`) in
     `extreme_rows` and `sample_rows`, which are harder for a model to read.
     Dump with aliases off.
   - The `number` fields don't say whether `names` or the `label` column wins
     for the tile label. In r2 both said "Active members", so I couldn't tell.
   - Rule callout text is gray, but point callout text is ink (r1). It's unclear
     whether that's on purpose.
