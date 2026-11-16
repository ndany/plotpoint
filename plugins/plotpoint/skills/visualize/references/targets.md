# Targets, layouts and techniques

A **target** is a format plus a layout. The **intent** is the same in every
target; the **technique** (how it's drawn) can differ per target.

| Target | Where it's shown | Default layout | Techniques (default first) |
| --- | --- | --- | --- |
| `md/document` | VS Code preview, GitHub | `report` | `svg`, `mermaid`, `table`, `text` |
| `html/document` | A column in an HTML page | `report` | `svg`, `vega`, `table`, `text` |
| `html/slide` | One 16:9 slide in an HTML deck | `deck` | `svg`, `vega`, `table`, `text` |
| `image/slide` | Pasted into PowerPoint, Keynote, Google Slides | `slide-image` | `png` (an SVG is written too) |

## Techniques

| Format | Technique | Good for | Limits |
| --- | --- | --- | --- |
| `.md` | `svg`: an image file plus `![headline](file.svg)` | Full quality: highlight, callouts, every v1 type | A file sits beside the `.md` |
| `.md` | `mermaid` (line and bar only) | Text-only, diffable, no extra files | No callouts (written as text under the chart). Legends need Mermaid 11.17+, so series are always named in text. Per-bar highlights become text. VS Code needs the Markdown Preview Mermaid Support extension; GitHub renders natively |
| `.md` | `table` | Many categories, exact values | Not a picture |
| `.md` | `text` | A single number or sentence | — |
| HTML | `svg` (default): an inline SVG inside a `<figure>` | No scripts; prints and emails well; safe under strict page policies | No hover |
| HTML | `vega`: interactive Vega-Lite | Hover tooltips | The page must load Vega once (the fragment's comment gives the three `<script>` tags) |
| HTML | `table`, `text` | Exact values; a single figure | — |
| Image | `png` at 2× | Slides | Static; set in the bundled Source Sans 3 (`fonts/`, `slide_font` in `config/theme.yaml`), not system fonts, so it looks the same on every machine. Tables and sentences aren't rendered as slide images in v1 |

**Choosing per target.** Keep the intent identical; pick the technique that
carries it best:

- A line or bar chart with no callouts can be `mermaid` in Markdown (text-only,
  easy to diff) and `svg` in HTML.
- Anything with callouts that matter, or a scatter or histogram: `svg` in
  Markdown too.
- Mermaid is a trade-off, not a default: it keeps the `.md` text-only but moves
  callouts under the chart. If a callout carries a headline number, `svg` is
  the safer choice. Either is acceptable; say which you chose and why.
- A `number` is `text` in Markdown and HTML (HTML draws a styled tile); a
  `table` is `table`. Neither has a size or an image file, so check them by
  reading the snippet.
- Record any `compensations` in the storyboard: what the format can't carry
  and how the rendering makes up for it. Omit the key when there are none.

## Layouts and the scaling rule

An SVG is drawn at a **design width**, then scaled to its container. Scaling
changes the apparent size of everything: drawn at 960 px and shown at 800, text
shrinks to 83%. So the renderer:

1. **Draws at the content width** the chart will occupy (container minus padding).
2. **Never scales up**: HTML embeds use `width:100%; max-width:<design width>`.
3. **Raises text sizes** so labels stay at 11 px or more at the narrowest
   expected display width (`min_display_width`). The `legibility` check verifies it.

| Preset | Drawing size | Expected narrowest display | Typical page |
| --- | --- | --- | --- |
| `prose` | 800 wide | 600 | Document-style reading pages |
| `report` (default) | 960 wide | 768 | Table-heavy analysis reports |
| `wide` | 1100 wide | 768 | Diagram-first or illustrated pages |
| `dashboard` | 384 wide (1200 split into 3 cards) | 1024 | Card grids |
| `deck` | 1440 × 810 canvas, chart area 1320 × 560 | 1280 | Fixed-canvas HTML slide decks |
| `slide-image` | 1920 × 1080 canvas, chart area 1760 × 720; PNG at 3840 × 2160 | 1280 | Slide images |

Override per request when you know the page:
`layout: {preset: prose}`, `layout: {content_width: 752, height: 400}`, or per
target: `layout: {html/document: {content_width: 752}}`. Presets live in
`config/layouts.yaml`.

## Capacity

Past a limit, the form changes rather than squeezing. Document limits are for
960 px and scale with width; slide limits are fixed (`config/capacity.yaml`).

| Type | Documents (960) | Slides | Past the limit |
| --- | --- | --- | --- |
| `bar` (categories) | 12 | 7 | Largest N−1 kept, the rest summed into "Other" |
| `stacked_bar` (segments) | 5 | 4 | Same, for segments |
| `line` (series) | 7 (direct labels up to 4) | 3 | Non-highlighted series grayed and unlabeled; warning |
| `scatter` (points) | 2,000 | 500 | Warning: overplotting |
| Mermaid `xychart` (categories) | 10 | — | Warning: crowded labels |

The `capacity` check reports what changed. A folded "Other" bigger than a shown
bar or segment warns (readers take it for one item); it fails when that bar is
highlighted or named in the headline, because the chart then contradicts the
headline. If the result no longer tells the story, choose another form: the top
items without "Other" plus a note of how many were left out, a layout with more
room, small multiples, a table, or a highlight.
