# Spec: requests and results

The source of truth is `schemas/plotpoint.schema.json`; this page explains it.
Validate any document with
`visualize.py validate <kind> FILE`, where kind is `storyboardRequest`,
`storyboardResult`, `renderRequest` or `renderResult`. Requests can be YAML or
JSON. Paths inside a request resolve relative to the request file's folder.

## Data: `path` or `inline`

`data` takes exactly one key.

```yaml
data: {path: data/loans_by_quarter.csv}       # format from the extension
data: {path: data/branches.json}              # JSON array of records
data: {path: exports/wait_times.tsv}          # tab-separated
data: {path: logs/visits.jsonl}               # one JSON record per line
data: {inline: "metric,value\nActive members,48210\n"}   # CSV text
```

| Form | Use when |
| --- | --- |
| `path` (default) | The data already exists as a file; more than ~100 rows or ~5 KB; the same dataset feeds several visuals |
| `inline` | A tiny summary computed on the fly, where writing a file would be overhead |

Formats: `.csv`, `.tsv`, `.json` (array of records), `.jsonl`. Column types are
inferred: number, date (`YYYY-MM` or `YYYY-MM-DD`), or text. Summarized, flat
tables work best; use readable column names or set display `names` (below).
Both forms are handled the same way afterwards, so the choice is convenience,
not capability.

## Storyboard request

```yaml
writeup:
  title: "City library services review, FY26"
  audiences:
    board: "Library board: decision-makers, non-specialists"
    managers: "Branch managers: practitioners who act on detail"
  default_audience: board
  targets: [md/document, html/document]
  layout: {preset: report}                # optional
  draft: {path: drafts/review.md}         # optional (.md, .html, .txt, or inline)
questions:
  - id: q1
    question: "Did the Q2 renovation reduce library use?"
    audience: [board, managers]           # optional; default_audience if absent
    takeaway: "Total loans fell 18% ..."  # optional
    datasets: [loans_print, loans_ebook]
datasets:
  - id: loans_print
    data: {path: data/loans_print.csv}
    source: "Library circulation system export"
    as_of: 2026-09-30
    units: loans (thousands)              # optional
    notes: "..."                          # optional caveats
```

| Field | Required | Meaning |
| --- | --- | --- |
| `writeup.audiences` | Yes | Named audiences, one line each |
| `writeup.default_audience` | Yes | Used when a question names none |
| `writeup.targets` | Yes | Targets to plan renderings for: `md/document`, `html/document`, `html/slide`, `image/slide` |
| `writeup.layout` | No | Layout for all targets, or per target (`references/targets.md`) |
| `writeup.draft` | No | The draft write-up; enables narrative and conversion advice |
| `questions[].question` | Yes | What must be answered; drives the visual choice |
| `questions[].takeaway` | No | The conclusion already reached; without it, headlines are drafts |
| `questions[].datasets` | Yes | Dataset ids supporting the question |
| `datasets[].source`, `as_of` | Yes | Printed under every visual |

## Storyboard result

```yaml
visuals:                       # in recommended order
  - id: v1
    questions: [q1]
    datasets: [loans_print, loans_ebook]
    audience: [board, managers]
    placement: summary         # summary | body | appendix
    intent: {...}              # see Intent below
    data: {path: data/derived/loans_by_quarter.csv}   # optional: the table to render from
    data_note: "Join print and e-book loans on quarter"  # optional: how to build it
    renderings:
      md/document: {technique: mermaid, compensations: ["callout as text under the chart"]}
      html/document: {technique: svg}
recommendations:
  - {kind: merge, detail: "Print and e-book loans tell one story", affects: [v1]}
  - {kind: cut, detail: "Café revenue answers no question", affects: [cafe_sales]}
color_map: {E-book: accent, Print: context}
```

| Field | Meaning |
| --- | --- |
| `placement` | `summary` (read first), `body`, `appendix` |
| `renderings.<target>.technique` | `svg`, `mermaid`, `table`, `text`, `vega` (interactive HTML) or `png` (slide images) |
| `data`, `data_note` | Set when the visual renders from something other than one dataset as given (a merge, a join, a derived column): the file the caller should build, and how. Column names in the intent refer to that table |
| `renderings.<target>.compensations` | What this format can't carry and how the rendering makes up for it. Omit the key when there is nothing to compensate |
| `recommendations[].kind` | `order`, `merge`, `demote`, `cut`, `add-summary`, `placement`, `rendering`, `other` |
| `recommendations[].affects` | Visual ids, or dataset ids for datasets with no visual (e.g. a cut) |
| `color_map` | Entity → `accent`, `context`, `slot1`–`slot8` or `#rrggbb`, for the whole document. Several entities may be `accent` when they are the subjects of different visuals (E-book in one, Riverside in another). Entities beside a highlight are gray anyway; map them to `context` to keep them gray in every visual. Pass it to every render call |

## Intent

The intent is the format-independent decision for one visual. It's the same in
every target; only the rendering changes.

```yaml
intent:
  visual_type: line
  rationale: "Change over time; two series, the story is about one"
  headline: "Total loans fell 18% during the Q2 renovation; e-book loans have since grown to a new high"
  headline_status: confirmed      # confirmed | draft | title
  fields: {x: quarter, y: [print, ebook], names: {print: Print, ebook: E-book}}
  highlight: [ebook]              # column names or display names
  callouts:
    - {kind: rule, x: "Q2 '26", text: "Q2 renovation\nTotal 1,230 → 1,008 (−18%)"}
  outlier_handling: {method: none_flagged}
  units: Loans (thousands)        # optional measure-axis title; take it from the dataset's units
```

| Field | Meaning |
| --- | --- |
| `visual_type` | Rendered in v1: `bar`, `stacked_bar`, `line`, `scatter`, `histogram`, `table`, `number`, `sentence`. Other chooser types are valid in a storyboard, but the renderer refuses them; draw those by hand following dataviz |
| `headline` | A takeaway sentence. Every number in it must be derivable from the data (checked, below) and visible on the visual |
| `headline_status` | `confirmed`: the caller's takeaway. `draft`: written without one; a person confirms it. `title`: a descriptive label for a reference visual with no single takeaway, such as an appendix table |
| `fields` | Column roles, by type (table below); `names` maps columns to display names |
| `highlight` | Entities in the accent color (column names or display names; scatter: point labels). Everything else turns context gray. Highlighted lines get an automatic direct label with their latest value ("E-book 445"), and highlighted scatter points a label with their name ("Riverside"), so don't repeat those in a callout. Tables bold highlighted rows; numbers ignore it |
| `callouts` | Text pinned to the visual (next section) |
| `outlier_handling` | How flagged outliers are handled (section below) |
| `units` | Title for the measure axis: the y axis of line, bar and stacked bar charts; the x axis (the measured value) of a histogram. Name the measure and its unit ("Wait (minutes)"), not the count. Scatter axes use `fields.names` |

### Callouts

| Kind | Pinned by | Drawn as |
| --- | --- | --- |
| `rule` | `x`: an x-axis value (line), or a number (scatter, histogram). Bar and stacked bar charts don't draw rules yet: the `callouts` check fails; use a note or `highlight` | A vertical line with the text beside it, in the secondary ink color (context). Several rule labels stack so they don't collide |
| `point` (text in the primary ink color: it's about the data) | Line: `x` (an x-axis value) and `series` (column or display name; required with several series). Scatter: `series` set to the point's label (`fields.label` value) or series, plus `x` (its numeric x value) when labels repeat. Not available on histograms; bar and stacked bar charts don't draw them yet (the check fails; use a note or `highlight`) | Text next to that point |
| `note` | Nothing | A line of text under the visual |

Use `\n` for a line break. A callout that matches nothing, or a rule or point
callout on a bar chart drawn as an image, fails the `callouts` check and isn't
drawn, so fix it before delivering. Mermaid, table and text outputs show rule
and point callouts as text under the visual; numbers show every callout as a
note. Label positions are automatic in v1.

### Outlier handling

The profile flags outliers (1.5 × IQR) and axis dominance per column. Skew is
informational and needs no handling. Every flagged column a visual plots needs a
handling other than `none_flagged`:

```yaml
outlier_handling: {method: accept, reason: "..."}    # one handling for every column
outlier_handling:                                     # or one per column
  - {column: avg_wait_min, method: callout, reason: "Riverside's wait is the finding"}
  - {column: staff_fte, method: accept, reason: "Central's size is real; noted"}
```

| Method | Needs | Effect |
| --- | --- | --- |
| `none_flagged` | | Nothing flagged |
| `callout` | A `highlight` or callout naming it | The outlier is the story |
| `log_scale` | | Log axis for that column |
| `exclude` | `exclude` (values) and `reason`; only when the caller confirms | Rows dropped; a note says what and why |
| `accept` | `reason` | Drawn as-is |

Tables are exempt: they show every value.

| Visual type | Fields |
| --- | --- |
| `bar` | `x` category, `y` measure; optional `orientation` (`vertical`, `horizontal`, `auto`), `sort` (`value`, `data`, `label`) |
| `stacked_bar` | `x`, `y` as a list of segment columns, or `y` + `series` for long data; optional `normalize` |
| `line` | `x` (time or ordered category), `y` as a list of measures, or `y` + `series` |
| `scatter` | `x`, `y` measures; optional `label` (point names, used by highlight and callouts), `series` |
| `histogram` | `value` measure; optional `bins`: the most bins to use (default 20); Vega-Lite picks a round bin width within it, so you may get fewer (20 can give ten 5-minute bins); `names: {count: Visits}` titles the y axis |
| `table` | optional `columns` order, `sort` (`value`: descending by the first numeric column in `columns`, or by `y` if set; `label`: by the first column; `data`: as given), `names` |
| `number` | `value`; optional `label` (column holding the label shown under the figure; `names` doesn't rename it), `previous` (for the change) |
| `sentence` | None: the headline is the visual. `data` is still required so its numbers are checked |

## Render request

```yaml
id: v1                                    # used in file names and HTML ids
intent: {...}                             # from storyboard; or omit and give question (mode C)
question: "..."                           # mode C only
takeaway: "..."                           # mode C, optional
data: {path: data/derived/loans_by_quarter.csv}
source: "Library circulation system export"
as_of: 2026-09-30
targets: [md/document, html/document, html/slide, image/slide]
technique: {md/document: mermaid}         # optional, per target
layout: {html/document: {preset: prose}}  # optional; or {content_width: 752}
color_map: {E-book: accent, Print: context}
out_dir: figures/v1                       # relative to the request; Markdown snippets link here
md_table: false                           # also add a values table under Markdown charts
```

The renderer needs an intent. In mode C, validate the request once, decide the
intent (SKILL.md render step 2), add it, and render; `question` and `takeaway`
may stay in the request.

A render request has no `data_note` (validation rejects it). When `data` is a
table you built, record how in a YAML comment above `data`, or keep the
storyboard's `data_note` with your write-up.

Add `--dry-run` (`visualize.py render --dry-run request.yaml`) to run every
check without writing files; text outputs (tables, numbers, sentences) are
still returned. `--checks-only` is different: it renders and writes every file,
and prints only the checks and notes. For a whole storyboard, `visualize.py check-plan request.yaml
result.yaml` builds a request per visual (its `data`, else its first dataset;
sources joined; latest as-of) and dry-runs them all.

`source` is one string; for several sources, join them ("Circulation export;
E-book platform").

## Render result

```yaml
id: v1
intent: {...}
outputs:
  md/document:
    technique: svg
    files: [figures/v1/v1-md-document.svg, figures/v1/v1-md-document.md]
    snippet: "**Headline**\n\n![Headline](figures/v1/v1-md-document.svg)\n\n<sub>Source: ...</sub>"
  html/document:
    technique: svg
    files: [figures/v1/v1-html-document.svg, figures/v1/v1-html-document.html]
    snippet: "<figure class=\"pp-figure\" ...>...</figure>"
checks:
  headline_numbers: {status: pass, detail: "..."}
  outliers: {status: pass, detail: "..."}
  legibility: {status: pass, detail: "..."}
  callouts: {status: pass, detail: "..."}
  capacity: {status: pass, detail: "..."}
  render: {status: pass, detail: "..."}
notes: []
```

Statuses: `pass`, `warn`, `fail`, `skip`. Fix every `fail` before delivering.
The result is also written to `<out_dir>/<id>.result.json`. `width` and
`height` are reported only for drawn outputs (SVG, PNG, Vega), not text,
tables or Mermaid.

**Files: the deliverable and its by-products.** Each target writes one
*deliverable*: the file a person publishes or pastes. Anything else listed in
`files` is a *by-product*: a part of the deliverable, kept for reuse.

| Target | Deliverable | By-product |
| --- | --- | --- |
| `md/document` | `<id>-md-document.md`: headline, chart or table, notes, source line | `.svg` (technique `svg`): the chart image the `.md` links to, with no headline or source. `.mmd` (technique `mermaid`): the Mermaid code, already inside the `.md` |
| `html/document`, `html/slide` | `<id>-<target>.html`: a `<figure>` fragment, not a page | `.svg` (technique `svg`): the chart alone, already inline in the fragment. `.vl.json` (technique `vega`): the Vega-Lite spec, already embedded |
| `image/slide` | `<id>-image-slide.png` (3840 × 2160) | `.svg`: the same slide as vector |

Keep the deliverable and the files it links to together. Image links in the
`.md` file resolve from the file's own folder (`![..](v1-md-document.svg)`). The
result's `snippet` is the same text for pasting into *your* document, so its
links resolve from the request's folder (`figures/v1/v1-md-document.svg`).

| Check | Fails when |
| --- | --- |
| `headline_numbers` | A number in the headline or a callout isn't derivable from the plotted data. The detail lists what each number matched; read it. Rules below |
| `outliers` | A flagged plotted column has no handling (above). A scatter checks both axes. Tables and sentences skip |
| `callouts` | A rule or point callout matches nothing on the chart, or is on a bar or stacked bar chart drawn as an image (not drawn yet) |
| `legibility` | Text would fall under 11 px at the narrowest expected display width. Text and table outputs skip it (the page sets their size) |
| `capacity` | Warns when the data exceeds what the layout carries (and what was folded into "Other") |
| `render` | A target failed to draw, or Mermaid didn't parse |

**What counts as derivable** (`config/capacity.yaml` sets the row limit):

| Number | Counts | Doesn't count |
| --- | --- | --- |
| Plotted values | Values of plotted measures (above 50 rows, only each measure's min and max) | Raw values of a large table ("half wait under 12" can't match one visit) |
| Summary figures | Row count; totals; mean, median, quartiles, deciles | Bin edges; ranks |
| Shares | Shares of a total, on bar, stacked bar and table visuals; each measure's share of its row total, on multi-series line and bar charts ("E-book is 43% of loans") | Shares of a total on time series |
| Changes | Percent or absolute, between consecutive values, first and last, or peak or low and latest (line, bar, stacked bar, table); value vs `previous` (number) | Changes between arbitrary rows, between two series, or between rows of an unordered table |
| Direction | A change in the direction the text says: "fell 3%" needs a fall, "−18%" a negative change | A change the other way ("fell 3%" when it rose 2.7%) |
| Named rows | When a clause names a row ("Riverside", "Q2 '26"), only that row's figures, or an aggregate introduced by a word like median, mean, total or overall | Another row's figure ("Central's wait is 48" when 48 is Riverside's) |
| Multiples | None: state both values instead ("Riverside waits 48 minutes; the median is 7.8") | "8 times", "3x", "two-fold" |
| Scaled numbers | "212k", "1.2M", "3bn", "4 million", within their rounding ("212k" is 211,500 to 212,500); against data stored in thousands, millions or billions only when the column name (`visits_k`), its `names` label ("Visits (k)") or `units` says so | "212k" against data in thousands that doesn't say so; lowercase m ("15m" is a label, not 15 million) |
| Distributions (histograms, large tables) | A share with a threshold in one clause ("82% within 15 minutes", "half within 7.8", "1 in 10 above 18.9"); a bare threshold read with its quantifier: "30 minutes or more" needs some value that far, "no wait over 40", "all under 30" and "at most 20" need every value on that side | A bare threshold that only falls inside the data's range ("no wait over 40" when one is 47.5) |

Numbers inside text cells ("Branch 12", "Q2 '26") are ignored. The check
confirms a number can be derived and that a change goes the stated way; that it
compares the right things, and that it is *visible* on the visual, is for you to
check by looking. Numbers inside words ("FY26", "Q2") are treated as labels and
not checked.
