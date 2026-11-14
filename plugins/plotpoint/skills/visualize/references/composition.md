# Composition: dashboards and multi-chart pages

For a write-up, the storyboard handles order and placement
(`references/storyboard.md`). Use this page when several visuals share one
screen: a dashboard, or a summary section with a KPI row and charts.

Based on *Dashboard Design Patterns* (Bach et al., IEEE VIS 2023) and Stephen Few's
dashboard principles.

## 1. Decide the dashboard's genre

| Genre | Reader | Implication |
| --- | --- | --- |
| Strategic / executive | Leadership, monthly or quarterly | Few KPIs, trends vs target, minimal interaction, fits one screen |
| Operational | Team leads, daily | Current status, thresholds, alerts, drill-down |
| Analytical | Analysts | Filters, exploration, detailed charts and tables |

Don't mix genres on one page. If a request does, split it into pages.

## 2. Screenspace — pick one deliberately

- **Screenfit** (default for executive): everything visible without scrolling.
- **Detail-on-demand**: summary visible; details in tooltips, expandable rows, or a linked page.
- **Overflow** (scrolling): acceptable for reports read top-to-bottom; put the most important content first.
- **Multiple pages**: when content truly exceeds one screen; give each page its own headline.

## 3. Layout — reading order is importance order

Readers scan top-left first, then across, then down.

1. **Top row:** headline sentence + KPI row (3–5 stat tiles, never more than 6).
2. **Middle:** the 1–2 charts that explain the KPIs (trend vs target, breakdown).
3. **Bottom:** supporting detail — tables, secondary breakdowns.

Group related charts and align them on a shared grid. Charts that compare the same
measure share the same scale and color assignment.

## 4. Required metadata (always include)

- **Data source** — system or report name
- **As-of date** — when the data was extracted, not when the page was built
- **Definitions** — a one-line definition for any metric that could be misread
- **Annotations** — known events that explain spikes or drops

## 5. Color across the page

- One consistent color per entity across every chart on the page.
- Reserve status colors (good / warning / critical) for status only — always with an icon or label.
- Accent color is spent on the headline's subject; everything else neutral.

## 6. Interaction (HTML only)

- Filters in one row above the charts; the default view must answer the headline without any clicks.
- Tooltips add detail; they never hold the only copy of an important number.
