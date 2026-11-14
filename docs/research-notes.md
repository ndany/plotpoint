# Research notes — data visualization sources

*Compiled 2026-10-24. Starting point: a social-media post listing five data visualization websites, plus independent review. These notes informed the design of plotpoint (drafted first as a `storytelling` skill, built as `plotpoint:visualize`); see `docs/decisions.md` for the decisions that followed.*

---

## The five referenced sites

| # | Site | URL | Job it does |
| --- | --- | --- | --- |
| 1 | From Data to Viz | <https://www.data-to-viz.com/> | Pick the chart type from the data's shape |
| 2 | ColorBrewer 2.0 | <https://colorbrewer2.org/> | Pick a color scheme by data type |
| 3 | Dashboard Design Patterns | <https://dashboarddesignpatterns.github.io/> | Vocabulary for dashboard content & layout |
| 4 | Storytelling with Data | <https://www.storytellingwithdata.com/> | Turn a chart into a message for an audience |
| 5 | Dataviz Inspiration | <https://www.dataviz-inspiration.com/> | Gallery of examples by chart type & tool |

---

### 1. From Data to Viz — <https://www.data-to-viz.com/>

**By:** Yan Holtz (analyst) & Conor Healy (designer).

- **Decision tree** keyed on data type: numeric, categoric, numeric + categoric, maps, network, time series (~20 dataset formats).
- **Chart families by purpose:** distribution, correlation, ranking, part-of-whole, evolution, maps, flow.
- **Caveats gallery** (the most valuable part): unordered bars, truncated y-axis, spaghetti lines, pie charts, histogram bin size, boxplots hiding sample size, overplotting, rainbow palettes.
- Each chart links to R, Python and D3.js code galleries.

**Use in a skill:** Step 1 "pick the form" and a pre-flight anti-pattern check.

### 2. ColorBrewer 2.0 — <https://colorbrewer2.org/>

**By:** Cynthia Brewer, Mark Harrower, Penn State. Built for cartography.

- **Three scheme types:** sequential (low→high), diverging (around a midpoint), qualitative (categories).
- 3–12 classes; filters for **colorblind-safe**, **print-friendly**, **photocopy-safe**.
- Exports: JS array, CSS, ASE (Adobe), GIMP/Inkscape palette, permalink.

**Use in a skill:** The rule "color by the job the data does" (identity / magnitude / polarity).

### 3. Dashboard Design Patterns — <https://dashboarddesignpatterns.github.io/>

**By:** Benjamin Bach (Univ. of Edinburgh) et al. Paper: *Dashboard Design Patterns*, IEEE VIS / TVCG 2023 (arXiv 2205.00757).

**43 patterns in 8 groups:**

| Group | Patterns |
| --- | --- |
| Data Information | Individual Values, Derived Values, Filtered, Thresholds, Aggregated Data, Detailed Datasets |
| Meta Information | Data Source, Disclaimer, Data Description, Update Information, Annotations |
| Visual Representations | Numbers, Trend-Arrows, Pictograms, Gauges & Progress Bars, Signature Charts, Detailed Charts, Tables, Text Lists |
| Interactions | Exploration, Navigation, Personalization, Filter & Focus |
| Screenspace | Screenfit, Overflow, Detail-on-Demand, Parameterized, Multiple Page |
| Structure | Single Page, Hierarchical, Parallel, Open, Semantic |
| Page Layout | Open, Table, Stratified, Grouped, Schematic |
| Color | Distinct, Shared, Data Encoding, Semantic, Emotive |

Also: dashboard genres, design trade-offs, process guidance, downloadable cheatsheets.

**Use in a skill:** A dashboard-planning checklist — e.g. always include Meta Information (source, last updated) and decide screenspace strategy up front.

### 4. Storytelling with Data — <https://www.storytellingwithdata.com/>

**By:** Cole Nussbaumer Knaflic and team. Book: *Storytelling with Data* (Wiley, 2015).

**Core lessons from the book:**

1. Understand the context — who is the audience, what should they do?
2. Choose an appropriate visual.
3. Eliminate clutter.
4. Focus attention where you want it (color/contrast as a highlighter).
5. Think like a designer.
6. Tell a story (beginning, middle, end).

Site resources: blog, podcast, chart guide, makeovers, Excel tutorials, an "SWD + AI" guide, community, workshops.

**Use in a skill:** The audience-first layer — headline that states the takeaway, one highlighted series, everything else gray.

### 5. Dataviz Inspiration — <https://www.dataviz-inspiration.com/>

**By:** Yan Holtz (same author as From Data to Viz).

- Hundreds of curated visualizations, Pinterest-style, sorted by chart type and tool.

**Use in a skill:** Reference only — not a rules source (see caveats below).

---

## Contrary views & caveats

- **The list has no decision layer at the top.** Data to Viz picks charts from data *shape*; executives need charts picked from the *question/decision*. Start with SWD's "context" step, then use Data to Viz.
- **ColorBrewer is cartography-first and dated.** Not every scheme is CVD-safe (e.g. Set1, Paired include red/green pairs); filter explicitly. For continuous screen data, perceptually uniform maps (viridis family) or OKLCH-based ramps are the modern default. Validate computationally rather than trusting a label.
- **Dashboard Design Patterns is descriptive, not prescriptive.** It names options; it doesn't say which is better for a given audience.
- **Dataviz Inspiration skews editorial/artistic.** Novel forms cost comprehension time — wrong trade for a board deck.
- **"Declutter" can go too far.** Research (Bateman et al., CHI 2010) found some embellishment improves recall without hurting accuracy. Minimalism is a default, not a law.
- **Pie/donut bans are overstated.** For 2–3 parts of a whole, a pie is fine; the failure is 6+ slices.

## Additional resources worth adding

These URLs were not verified at the time of writing; check them before relying on them.

- **FT Visual Vocabulary** — chart chooser organized by *relationship* (deviation, correlation, ranking, part-to-whole…), better than data-type trees for business questions. <https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary>
- **Stephen Few — Perceptual Edge** / *Information Dashboard Design* — the canonical text on at-a-glance operational dashboards (bullet graphs, sparklines). <https://www.perceptualedge.com/>
- **IBCS (International Business Communication Standards)** — notation rules for management reports: consistent scenario styling (actual/plan/forecast), variance charts. <https://www.ibcs.com/>
- **Datawrapper Academy / blog** — practical, current guidance on chart and color choices. <https://academy.datawrapper.de/>
- **Viz Palette** (Susie Lu & Elijah Meeks) — test a palette for CVD conflicts. <https://projects.susielu.com/viz-palette>

## Skill architecture (as proposed, 2026-10-24)

> Superseded by the v1 design: one skill, `plotpoint:visualize`, with a
> storyboard and a render operation on its own rendering engine. See
> `docs/architecture.md`. The layering below still holds.

Three layers, each a separate skill so they can be reused independently:

| Layer | Skill | Owns |
| --- | --- | --- |
| Rendering | `dataviz` (existing, Anthropic) | Chart-job → form table, color formula + validator script, mark specs, hover/tooltips, accessibility, anti-patterns |
| Communication | `plotpoint:visualize` (proposed as `storytelling`) | Audience & headline first (SWD); extended chart chooser for forms `dataviz` doesn't cover (distribution, correlation, flow, hierarchy, maps — Data to Viz / FT Visual Vocabulary); dashboard composition (Dashboard Design Patterns); defers to `dataviz` for rendering |
| Domain | planned separate plugin — metrics library for a first domain (to be chosen) | Metric definitions, formulas, targets/thresholds, preferred visual per metric, known pitfalls (e.g. 5×5 risk heat maps). Reusable by reporting, analytics agents, and decks |

**Gap found in `dataviz`:** its form chooser is job-based and covers business forms (bar, line, stacked/diverging bar, dumbbell, heatmap, stat tile, KPI row, meter, table). It does not cover distributions (histogram, boxplot), scatter/correlation, flows (Sankey), hierarchy (treemap), networks or maps. The communication layer fills that.

**Portability:** keep frontmatter to the Agent Skills standard fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`) so the same SKILL.md works in Claude.ai, Claude Code and the API.
