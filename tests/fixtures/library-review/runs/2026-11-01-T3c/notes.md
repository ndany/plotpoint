# T3c: render, mode C (r1–r5)

All five final requests validate (`validate renderRequest`) and render with no
`fail` and no `warn`. Outputs are in `figures/rN/`; PNG previews (made with
`vl_convert.svg_to_png`) sit beside the SVGs. The md and html SVGs are
byte-identical for each chart (both use the `report` preset, 960 px).

## r1: line

- **Why:** the question is about change over time (five quarters) with two
  series, and the second clause of the takeaway is about e-book. E-book is
  highlighted and print is context gray. A rule at Q2 '26 carries the total
  (1,230 → 1,008, −18%), because total isn't plotted.
- **Headline (confirmed):** "Total loans fell 18% during the Q2 renovation;
  e-book loans have since recovered to a new high". This is the caller's
  takeaway, tightened. "New high" is true (445 > 440) but no check verifies it.
- **Checks:** all pass. headline_numbers matched 18% and −18% to the total
  change from Q1 '26 to Q2 '26, which is the right comparison.
- **What I fixed:** I had copied `units: Loans (thousands)` from the spec
  example, but nothing in the data says the values are in thousands. I changed
  it to `Loans`. The checks passed with the wrong unit either way.
- **What I saw:** clean. The callout sits left of the rule and the e-book end
  label is clear. The print line ends in an unlabeled gray dot: fine, but it
  gives a little emphasis to the context series.

## r2: number

- **Why:** one figure answers "how many people". `previous` gives the change.
- **Headline (draft):** "Active membership grew 3.2% to 48,210". My first
  headline said "3%", but the tile prints "+3.2%". The check passed, but the two
  didn't match, so I changed the headline to 3.2%. I also dropped "on the
  previous period" because the data doesn't say what `previous` is (last year?
  last quarter?). The caller should give the period.
- **Checks:** headline_numbers pass (3.2% = value vs previous, 48,210 =
  value); legibility skip. All others pass.
- **What I saw:** read the snippet. The headline repeats the big number
  directly underneath it, which is redundant but acceptable. In HTML the big
  figure is drawn in the accent blue (`color:#1f6fd1`), which goes against
  "Text is ink-colored, never series-colored".

## r3: scatter

- **Why:** "Which branches need more staff" means wait compared with staffing,
  so the plot is staff_fte (x) against avg_wait_min (y), labelled by branch.
  Riverside is highlighted.
- **Headline (confirmed):** the takeaway verbatim. I checked "at similar
  staffing" before accepting it: Eastgate also has 4.5 FTE and waits 15 min,
  and Mill Road has 5 FTE and waits 14, so the claim holds.
- **Outliers:**
  - avg_wait_min (48) is handled by `callout`, since Riverside is the story.
  - staff_fte (Central, 24) is handled by `accept`. It stretches the x axis
    from 4 to 26, but the 4.5–9 cluster still reads. I tried no alternative
    (`log_scale` would hurt a board audience).
- **What I fixed:**
  - With only the highlight, Eastgate (the comparison that makes "at similar
    staffing" true) was an anonymous gray dot. I added point callouts for
    Riverside ("48 min with 4.5 FTE") and Eastgate ("Eastgate: same 4.5 FTE,
    15 min").
  - My first `accept` reason said "Central is the large main branch". I made
    that up, so I rewrote the reason.
- **Checks:** all pass. headline_numbers detail: "48 = Average wait (minutes)
  at 4.5; 4.5 = Staff (FTE) at 4.5; 15 = Average wait (minutes) at 4.5".
  Riverside and Eastgate both sit at x = 4.5, so this detail can't tell me
  which point each number came from.
- **What I saw:**
  - Riverside's callout is stacked directly on top of the auto "Riverside"
    label, just under the 50 gridline. It's tight but legible.
  - Central (6 min, 24 FTE) is unlabeled at the far right. Readers will wonder
    what it is.

## r4: table

- **Why:** four measures in different units across 12 branches, and no single
  takeaway. It's a reference table sorted by visits, with
  `headline_status: title`.
- **Checks:** headline_numbers pass ("no numbers"); outliers skip; legibility
  skip. All others pass.
- **What I fixed:** my first title was "…, FY26" and labelled the hours column
  "Weekly opening hours". I invented both the fiscal year and "weekly", and the
  check passed anyway: "FY26" is skipped as a text token. I removed both.
- **What I saw:** the Markdown table and the HTML table are correct, sorted
  descending by visits, with right-aligned tabular numbers.

## r5: histogram

- **Why:** "how long do visitors wait" is a distribution question over 300
  individual visits.
- **Headline (draft):** "Half of visitors get help within 7.8 minutes, but 1 in
  10 waits more than 18.9".
- **Callouts and outliers:** rules at the median (7.8) and the 90th percentile
  (18.9). There are 10 IQR outliers (27–47.5 min), handled by `accept`: the
  tail is real and is part of the story.
- **Checks:** all pass. 7.8 matched the median. In the headline, "18.9"
  matched only "threshold inside the range" and "1 in 10" matched "a quantile
  share" as a separate item. The "90th percentile" match comes from the
  callout, not the headline. See probe P17.
- **What I saw:**
  - The default bins are 5 minutes wide. The rules and labels are clear.
  - I also tried `bins: 24` (2-minute bins, in
    `probes/probes/r5bins/`). It shows the mode at 2–6 min more clearly, but
    the story is the same, so I kept the default.
  - The y-axis title is "Count", which can't be changed through `units`.
    "Visits" would be clearer.

## Probes

All probes were dry-run renders with only the headline changed and callouts
removed. The requests are in `probes/P*.yaml` and the raw results in
`probes/results.json`. The "Correct?" column says whether the check's verdict
was right.

| # | Base | Kind | Headline | Check | Correct? |
| --- | --- | --- | --- | --- | --- |
| P1 | r1 | wrong rounding (true: −18.05%) | Total loans fell 17% during the Q2 renovation | **pass**: matched the change from Q3 '25 to Q3 '26 (1,240 → 1,035) | **No.** A coincidental match on the year-over-year change; the claim is about the renovation quarter |
| P2 | r1 | wrong rounding (coarse) | …fell 20%… | fail | Yes |
| P3 | r1 | wrong direction | Total loans rose 18%… | fail | Yes |
| P4 | r1 | coincidental match, wrong period | Print loans fell 28% during the Q2 renovation | **pass**: peak to latest (820 → 590) | **No.** Print fell 24% in Q2 |
| P5 | r1 | share on a time series | E-book loans are now 43% of all loans | fail | Arguably wrong: this is true (445/1,035), but the spec excludes shares on time series |
| P6 | r1 | absolute change of an unplotted total | Total loans fell by 222… | pass | Yes, but 222 isn't visible unless you add it |
| P7 | r2 | wrong direction | Active membership fell 3.2% to 48,210 | fail | Yes |
| P8 | r2 | number not in data | …, 31% of residents | fail | Yes |
| P9 | r3 | multiple, which the spec says doesn't count | Riverside's average wait is 8 times Central's | **pass**: "8 = Staff (FTE) at 8" | **No.** A coincidental match on Elm Park's staffing (the true ratio is 8, so it's right only by luck) |
| P10 | r3 | another branch's value | Riverside's average wait is 14 minutes | **pass**: "14 = Average wait at 5" (Mill Road) | **No** |
| P11 | r3 | value attributed to the wrong entity | Central's average wait is 48 minutes | **pass** | **No** |
| P12 | r4 | share of total, correct (23.5%) | Central accounts for 24% of all visits | pass: "24% = 1's share of Visits" | Yes, but the detail says "1" instead of "Central" |
| P13 | r4 | share of total, wrong | Central accounts for 21% of all visits | **pass**: "% change in Opening hours from 1 to 2 (68 → 54)" | **No.** It matched a consecutive-row change in an unordered reference table, labelled by row index |
| P14 | r4 | number in a title token | Branch overview, FY27 | pass ("no numbers to check") | **No.** The year is never checked |
| P21 | r4 | wrong row count | 13 branches compared… | fail | Yes (the spelled-out "Thirteen" is ignored) |
| P22 | r4 | year as a standalone number | Branch overview for 2027 | fail | Yes, but inconsistent with P14 |
| P23 | r1 | value not in data | E-book loans reached a new high of 450 | fail | Yes |
| P24 | r3 | true multiple | Riverside's 48-minute wait is 8 times Central's 6 | pass ("8 = Staff (FTE) at 8") | Right verdict for the wrong reason |
| P15 | r5 | wrong share at a threshold | 90% of visitors get help within 15 minutes | fail | Yes |
| P16 | r5 | correct share at a threshold (81.7%) | 82% … within 15 minutes | pass | Yes |
| P17 | r5 | quantile share with the wrong threshold (true P90 = 18.9) | 1 in 10 visitors waits more than 25 minutes | **pass**: "1 in 10 = a quantile share; 25 = threshold inside the range" | **No.** The share and the threshold are checked separately, not as a pair (only 6% wait more than 25) |
| P18 | r5 | wrong threshold for "half" | Half of visitors wait more than 3 minutes | fail | Yes, though the statement is literally true (more than half do) |
| P19 | r5 | spec example | Half wait under 12 minutes | fail | Yes |
| P20 | r5 | mean presented as "typical" | The typical visitor waits 9.6 minutes | pass: matched the mean | Debatable: the median (7.8) is the honest "typical" for skewed data |

The check caught 10 of the 20 deliberately wrong or misleading headlines. It
missed 8: P1, P4, P9, P10, P11, P13, P14 and P17. Every miss was a pass on a
coincidental or wrong-entity match. P1, P4, P10 and P13 show the wrong
statistic in the detail, so a careful reader catches them. P11 and P17 don't:
the detail looks plausible.

## Skill feedback

1. **The headline check passes values that belong to the wrong entity
   (P10, P11, P9).**
   - On scatter and bar charts, any plotted value anywhere matches any number
     in the headline. "Central's wait is 48" passes because Riverside's wait
     is 48.
   - The detail keys scatter matches by x value ("at 4.5"), not by label. With
     two points at x = 4.5 (Riverside, Eastgate), the detail can't show which
     entity matched, so step 4 ("read what each number matched") can't be done.
   - Fix: report the label (`fields.label` or the category). Better, when the
     headline names an entity, prefer and require a match on that entity's row.
2. **Consecutive-row changes in a categorical table are meaningless but count
   (P13).**
   - "21% = % change in Opening hours from 1 to 2 (68 → 54)" lets a wrong share
     pass. The change is from Central to Riverside, in a table sorted by
     another column.
   - The detail also shows row indices ("1", "2") instead of branch names
     (P12 does the same).
   - Fix: allow changes only when the first column or `x` is ordered (time or
     ordinal), and always print the label.
3. **The distribution check takes a share and a threshold separately (P17).**
   - "1 in 10 waits more than 25" passes because "1 in 10" is "a quantile
     share" and 25 is "inside the range". The spec says the share and the
     threshold are checked "in one clause", so this looks like a bug.
   - My real r5 headline matched the same loose way. The "90th percentile"
     confirmation came only from the callout.
4. **Wrong comparison window passes (P1, P4).**
   - "Fell 17% during the Q2 renovation" matches the year-over-year change, and
     "print fell 28% during the renovation" matches peak to latest.
   - The detail does show the window, so this is a step 4 catch. But SKILL.md
     step 4 is one sentence. Add an explicit instruction: "confirm the matched
     window or entity is the one the sentence names."
   - Consider ranking matches, so the most specific candidate (adjacent
     quarters) is reported, and listing every candidate when several fit.
5. **A check pass doesn't mean the output is correct. Three cases here:**
   - (a) r1 passed with the invented unit "Loans (thousands)", which came from
     the spec example.
   - (b) r4 passed with an invented "FY26" in the title, because the check
     skips numbers inside tokens such as FY26 or Q2. P22 ("2027") does fail,
     so this is inconsistent (P14).
   - (c) r2 passed with headline "3%" while the tile shows "+3.2%".
   - Suggestions:
     - Don't put a unit like "(thousands)" in the canonical example unless the
       example data says so.
     - Check year-like tokens in titles against `as_of`.
     - Warn when a headline percentage is rounded differently from the
       rendered label.
6. **The render command prints the entire result to stdout, including inline
   SVG HTML (about 15 KB per chart).** The same content goes to
   `<out_dir>/<id>.result.json`. For an agent this wastes a lot of context. A
   `--quiet` or `--checks-only` default, or printing only checks and file
   paths, would help.
7. **Neither step 5 nor `targets.md` says how to view an SVG.**
   - The test prompt had to tell me to use `vl_convert.svg_to_png`.
   - The headline and source are not in the SVG (they're in the
     snippet/figcaption), so the PNG preview shows a headless chart. Step 5
     ("check that every number in the headline is visible") needs the
     headline beside it.
   - Ship a `visualize.py preview` command that writes PNGs, including the
     headline and source.
8. **`out_dir` and data paths resolve relative to the request file.** This is
   documented, but copying a request into a subfolder silently writes to
   `sub/figures/...` (in my run, `probes/probes/r5bins`) and breaks data paths.
   A one-line warning or an absolute-path example would help.
9. **The `number` visual uses accent-colored text** (`.pp-number`
   `color:#1f6fd1`), which contradicts "Text is ink-colored, never
   series-colored" in the SKILL.md rules. Either exempt stat tiles in the rule
   or ink the figure.
10. **Scatter: no easy way to label context points.**
    - The "similar staffing" comparison (Eastgate) and the far-right Central
      point stay anonymous unless you add point callouts.
    - The point callout then stacks directly on the highlight's auto label
      (Riverside), close to the top gridline.
    - Consider a `label: [names]` field for context points, separate from
      highlight, or smarter callout placement.
11. **Histogram y-axis title is fixed at "Count".**
    - `units` sets only the x axis, and nothing lets you name what is counted
      ("Visits").
    - The chooser says "try 2–3 bin widths", but render step 2 never mentions
      `bins`. Add it to step 2 for histograms.
12. **Rules on what counts as derivable that surprised me:**
    - Multiples ("8 times") are listed as not counting, yet P9 and P24 pass by
      matching an unrelated 8.
    - True shares on time series fail (P5). Putting the share in a `note`
      callout fails too (verified, `probes/P5b.yaml`), so a correct, useful
      figure ("e-book is 43% of loans") can't appear anywhere on a line chart
      without a `fail`. That needs a documented escape hatch, such as a derived
      share column or an `unchecked` note.
13. **Minor issues:**
    - The profile reports column type `string`, but the spec says "text".
    - The skew flag on a 5-point series (r1 print, −2.0) is noise; consider
      suppressing it below about 8 rows.
    - Mode C says "validate the request once, decide the intent, add it, and
      render", but doesn't say whether to drop `takeaway`/`question` afterwards.
      I kept them, which is valid.
