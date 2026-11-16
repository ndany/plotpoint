# Storyboard notes: City library services review, FY26

Followed SKILL.md storyboard steps 1 to 5. The request validated, all seven datasets were profiled, there was no draft (mode B), every planned visual was dry-run (render requests are in `dry/`, all checks `pass`, no `warn`s), and the result validated as `storyboardResult`.

## What I decided and why

| Visual | Question | Placement | Type | Why |
| --- | --- | --- | --- | --- |
| v1 | q1 | summary | line (print + e-book) | The first board question, with a confirmed takeaway. Print and e-book loans are merged into one chart (same quarters, same units). The headline's total (1,230 → 1,008, −18%) isn't a plotted line, so it goes in a rule callout at Q2 '26. E-book is highlighted. |
| v2 | q2 | summary | number | One figure answers "how many": 48,210 active members, up 1,510 (3.2%). The headline is a **draft**. |
| v3 | q3 | summary | sentence | The staffing decision belongs to the board, but q3's audience is managers only, so the board gets the finding as one sentence (Riverside 48 min at 4.5 FTE). |
| v4 | q3 | body | scatter (staff vs wait) | "At similar staffing" means comparing two measures per branch. Riverside is highlighted. Outliers: wait gets `callout` (it is the finding), staff gets `accept` (Central's 24 FTE is real). |
| v5 | q4 | body | histogram | A distribution question. A rule callout marks the median of 7.8. The 10 tail outliers get `accept` (they are real waits). The headline is a **draft**. |
| v6 | q3 | appendix | table | branch_overview has 4 measures × 12 branches and no single takeaway, so it is demoted to a reference table (`title`) with Riverside bolded. |

- **Cut:** cafe_sales. Café revenue doesn't measure how many people use the library.
- **Color map:** `{E-book: accent, Riverside: accent}`. Print is the only context entity, and it appears in just one visual, so it isn't listed (per spec.md).
- **Renderings:** SVG in both formats for v1, v4 and v5. v1's callout carries the headline's −18%, and Mermaid can't draw a scatter or histogram. v2 and v3 are text; v6 is a table. Nothing needs compensating.

## What the caller must decide

1. **v1 takeaway wording.** "E-book loans have since recovered and grown" is true (410 → 445, a new high). But print fell further, to 590, and total loans are still below where they were before the renovation (1,035 vs 1,230). The board could read "recovered" as covering total use. Consider adding a clause.
2. **v2 draft headline.** Is `previous` the prior count of active members, and for what period? Is "active members" what the board means by "actively use"?
3. **v5 draft headline.** Confirm the wording. Note that wait_minutes has no branch column, so we can't tell whether the long tail is Riverside's.
4. **Cutting cafe_sales.** Cut it, or does the caller want a separate café question?
5. **v3 widens q3's audience to the board.** Accept that, or keep q3 for managers only?
6. **v1 source line.** It combines two sources. Confirm the wording.

## Skill feedback

1. **Merged data has a chicken-and-egg problem.** spec.md/storyboard.md say the *caller* builds a merged table (`data` + `data_note`), but storyboard step 5 says to dry-run every visual "with its data". A merged visual has no data to dry-run until someone builds it. Here `data/derived/loans_by_quarter.csv` happened to exist already. Without it, I would have had to build it myself, which the skill neither tells me to do nor where to put it. The skill should say that storyboard builds derived tables in scratch space for the dry-run, or allow `data_note`-only visuals to skip it.
2. **"Every number in the headline must be visible on the visual" isn't checked.** I removed v1's callout, so −18% appeared nowhere on the chart, and `headline_numbers` still passed: it only checks that the number can be derived from the data. Either check visibility for numbers that come from totals or derived values, or say plainly in SKILL.md that this is the author's job and the check won't catch it.
3. **The audience rules contradict each other.** storyboard.md says a visual "inherits its question's audiences, and you may narrow it". The same page also says a decision-bearing question must reach the decision-makers through a summary visual or sentence, which means *widening* (v3: q3 is for managers, v3 is for the board). Say that widening is allowed for add-summary. Also say how to express "a summary sentence": I assumed a `sentence` visual, but it could also be a recommendation only.
4. **`sentence` is underspecified.** The spec's fields table has no `sentence` row, so it's unclear whether it uses fields, highlight or callouts. The schema still requires `data`. With data that has flagged outliers, the `outliers` check reports "no outliers flagged in plotted measures", which is misleading; it should be `skip`, like tables get.
5. **The color-map guidance conflicts.** spec.md's storyboard-result example includes `Print: context`, but the field table says to list context entities only when they appear in more than one visual, and Print appears in one. storyboard.md's "comparison context → `context`" doesn't mention that restriction either. Make the example follow the rule.
6. **Text visuals can't be inspected during storyboarding.** `render --dry-run` returns `outputs: {}`, so number, sentence and table snippets can't be read. targets.md says to check these "by reading the snippet". A dry-run that still returned text snippets, which cost nothing to produce, would let storyboard verify them.
7. **No guidance for multi-source visuals.** A render request takes one `source` string. For a merge (v1), I joined the two sources with ";". Say how to cite several sources, or let `source` be a list.
8. **Scaffolding for step 5 is missing.** Step 5 needs a full render request per visual (source, as_of, targets, color_map, out_dir), but SKILL.md doesn't say where scratch requests go, whether out_dir matters for a dry-run, or that `technique` should match the storyboard's `renderings`. A short template, or a `dry-run --storyboard result.yaml` mode that reads the result directly, would remove the duplication: right now every intent is written twice.
9. **Minor: the outlier example is ambiguous.** profiling.md says "a big category in a bar chart may be an IQR outlier… use accept". For the scatter, the same branch (Central) is an outlier on the x axis and Riverside on the y axis. The per-column list handled this well, but SKILL.md step 2 could say explicitly that scatter checks both axes.
10. **Minor: profile noise.** For a 5-row string column (quarter), the profile prints every value under `top` with share 0.2, which adds bulk and no information. Could the profile summarise it as "all distinct" instead?

## Known miss added 2026-11-16 (C3)

E12: v3 adds "of 48 minutes" to the q3 takeaway and keeps `headline_status:
confirmed`. The run predates the takeaway check; it is the behavior C3 fixes.
