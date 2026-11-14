# Using plotpoint

For people and skills that call plotpoint, for example a skill that writes
data-analysis write-ups. Field definitions:
[`references/spec.md`](../../plugins/plotpoint/skills/visualize/references/spec.md).
Formats and layouts:
[`references/targets.md`](../../plugins/plotpoint/skills/visualize/references/targets.md).

New to plotpoint? Start with the hands-on tour: [`try-it.md`](try-it.md).

## Setup

Install the plugin (see the [README](../../README.md)) and the script
dependencies once:

```bash
pip install -r <skill-folder>/scripts/requirements.txt   # jsonschema, PyYAML, vl-convert-python
```

Optional: the Mermaid CLI (`npm install -g @mermaid-js/mermaid-cli`) lets the
renderer test Mermaid output.

## Pick a mode

| You have | Use | Mode |
| --- | --- | --- |
| A draft write-up and its datasets | storyboard, with `writeup.draft` | A |
| Questions and datasets, no prose yet | storyboard | B |
| One dataset and a question | render, no intent | C |
| A storyboard result | render each visual with its intent | D |

## Typical integration: a write-up skill

1. **Prepare** summarized datasets as files (CSV, TSV, JSON, JSONL), or inline
   CSV for tiny ones.
2. **Storyboard** (mode A or B): write a storyboard request listing the
   audiences, questions (with takeaways where you've reached them) and datasets,
   and ask plotpoint to storyboard it. It dry-runs each planned visual, so the
   plan will render. For large write-ups in Claude Code or Cowork, run this in a
   sub-agent and keep only the result.
3. **Decide:** review the recommendations. Order, merges, cuts and placement are
   advice; apply what you agree with. Confirm or rewrite `draft` headlines.
4. **Render** (mode D): for each visual you keep, write a render request with its
   intent, the data file (the visual's `data` when the storyboard names one,
   e.g. a merge you build per its `data_note`), the targets, and the
   storyboard's `color_map`. Ask plotpoint to render it.
5. **Assemble:** drop each target's `snippet` into your document: Markdown into
   the `.md`, the `<figure>` fragment into your HTML page. Keep the files in
   `out_dir` next to the document.

## Converting Markdown to HTML

Render the same intent for both targets and use each target's snippet. The
storyboard's `renderings` say which technique fits each format, e.g. Mermaid in
Markdown but SVG in HTML so a callout can be drawn. Your converter needn't
choose: it asks for the `html/document` rendering.

## Example: one visual (mode D)

```yaml
# figures/v1.yaml
id: v1
intent:
  visual_type: line
  headline: "Total loans fell 18% during the Q2 renovation; e-book loans have since grown to a new high"
  headline_status: confirmed
  fields: {x: quarter, y: [print, ebook], names: {print: Print, ebook: E-book}}
  highlight: [ebook]
  callouts:
    - {kind: rule, x: "Q2 '26", text: "Q2 renovation\nTotal 1,230 → 1,008 (−18%)"}
  outlier_handling: {method: none_flagged}
data: {path: data/loans_by_quarter.csv}
source: "Library circulation system export"
as_of: 2026-09-30
targets: [md/document, html/document]
technique: {md/document: mermaid}
color_map: {E-book: accent, Print: context}
out_dir: figures/v1
```

```bash
python <skill-folder>/scripts/visualize.py render figures/v1.yaml
```

The result lists each target's files and snippet, plus check results. Fix any
`fail` before using the output. `render --dry-run` runs the checks without
writing anything. A worked example with rendered output is in
[`docs/examples/library-review/`](../examples/library-review/).

## HTML pages

- Fragments are `<figure class="pp-figure">` elements with inline styles, so
  they look right without any CSS; the classes let you restyle them.
- The default is inline SVG: no scripts. For hover tooltips, ask for the
  `vega` technique; the fragment's comment gives three `<script>` tags to include
  once in your page's `<head>`.
- Pass your page's real width when you know it:
  `layout: {html/document: {content_width: 752}}`. Charts never scale up, and
  labels stay legible down to the narrowest expected width.
