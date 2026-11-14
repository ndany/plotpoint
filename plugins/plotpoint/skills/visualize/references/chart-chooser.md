# Chart chooser

Two passes: **the question** narrows the family, **the data shape** picks the form.
Families follow the FT Visual Vocabulary and From Data to Viz.

## Pass 1 — what question is the reader asking?

| Question | Family | Default form | Alternatives |
| --- | --- | --- | --- |
| How big is each one? | Magnitude | Sorted bar (horizontal if labels are long) | Dot plot, lollipop |
| Which is biggest / where do we rank? | Ranking | Sorted bar | Slope chart (rank change), bump chart |
| How has it changed? | Change over time | Line | Column (few periods), area (single series), sparkline (inline) |
| Are we above or below target / baseline? | Deviation | Diverging bar, line vs target line | Bullet graph, variance bar |
| What is it made of? | Part-to-whole | Stacked bar (100% if shares matter) | Pie (2–3 parts only), treemap (many parts, hierarchical) |
| How are values spread out? | Distribution | Histogram | Boxplot (compare groups), violin, strip/beeswarm (small n) |
| Do two measures move together? | Correlation | Scatter | Bubble (3rd measure), heatmap (two categorical axes) |
| Where does it flow? | Flow | Sankey | Chord (mutual flows), funnel (stage drop-off) |
| How is it structured / nested? | Hierarchy | Treemap | Sunburst, indented table |
| Who connects to whom? | Network | Node-link (small) | Adjacency matrix (dense / >50 nodes) |
| Where is it? | Spatial | Choropleth (rates) | Bubble map (counts), hexbin |
| What's the single number? | Headline | Stat tile (value + delta + sparkline) | KPI row, meter vs limit |
| When does each thing happen? | Schedule | Gantt / timeline | Table with dates |

## Pass 2 — refine by data shape

| Data shape | Watch out for |
| --- | --- |
| 1 numeric | Histogram bin width changes the story — try 2–3 widths |
| 1 numeric × 1 categorical | Boxplots hide sample size and bimodality — show n, or overlay points |
| 2 numeric | Overplotting above ~1,000 points — use transparency, hexbin, or 2D density |
| Time series, many series | Spaghetti — highlight 1–2, gray the rest, or use small multiples |
| Many categories (>7) | Fold the tail into "Other", or use a table |
| Series on very different scales | The smaller series looks flat on a shared axis. If it carries the story, give it its own chart, index both to 100, or show the change as a number with a callout |
| Hierarchical | Treemaps make small items unreadable — label only the top level or add a table |
| Flows with many nodes | Sankey becomes a hairball past ~15 nodes — aggregate first |

## Never

- Two y-axes on one chart — use two charts or index both to 100
- Truncated y-axis on a **bar** chart (fine on a line chart if labeled)
- 3D charts, rainbow color scales
- A chart where a single number or a short table would do

## From the chooser to a `visual_type`

The renderer draws these in v1. Prefer them when they fit the question; they
cover most analysis write-ups.

| Chooser form | `visual_type` |
| --- | --- |
| Sorted bar, column | `bar` |
| Stacked bar, 100% stacked bar | `stacked_bar` (`normalize: true` for shares) |
| Line, sparkline | `line` |
| Scatter | `scatter` |
| Histogram | `histogram` |
| Table, indented table | `table` |
| Stat tile, KPI | `number` |
| A finding that needs no picture | `sentence` |

Other forms (diverging bar, slope, boxplot, Sankey, treemap, map, Gantt...)
are valid recommendations, but the renderer refuses them in v1. Either pick the
nearest v1 type and say what's lost in the `rationale`, or tell the caller the
visual must be drawn by hand following the dataviz skill (Mermaid covers Sankey,
Gantt and timelines in Markdown).
