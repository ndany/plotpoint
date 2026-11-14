# Fallback rendering rules

Use these **only if the dataviz skill is not available**. They are the minimum, not
a replacement for it.

## Color

- **Categorical** (distinct series): use this colorblind-safe order (Okabe–Ito), never cycled:
  `#0072B2` blue, `#E69F00` orange, `#009E73` green, `#CC79A7` pink, `#56B4E9` sky blue, `#D55E00` vermillion, `#F0E442` yellow (avoid yellow on white backgrounds for thin marks)
- **Emphasis:** one accent (`#0072B2`) for the subject; context series in gray `#B0B0B0`.
- **Sequential** (magnitude): one hue, light to dark. Python: `viridis` or `Blues`.
- **Diverging** (above/below a midpoint): two hues with a neutral gray middle. Python: `RdBu` (reverse if needed so "bad" is red).
- **Status** (good/warning/critical): reserved for status only, always with a text label or icon.
- Text is always dark/neutral ink, never the series color.

## Marks and layout

- One y-axis per chart. Bars start at zero.
- Lines 2px; bars with small gaps; markers at least 8px.
- Light or no gridlines; no chart borders; no 3D; no shadows.
- Legend for 2+ series; direct-label up to 4 series instead of making readers match colors.
- Label selectively — the latest value, the max, the point the headline mentions. Never every point.
- Sort bars by value unless the categories have a natural order (time, severity).

## Accessibility

- Never rely on color alone to carry meaning — add labels, shapes or patterns.
- Provide the underlying numbers as a table (Markdown table, HTML `<table>`, or a CSV next to the image).
- Text contrast at least 4.5:1 against the background.

## Before delivering

Render the output and look at it: label collisions, clipped text, overflow, legibility at the target size.
