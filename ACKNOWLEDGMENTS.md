# Acknowledgments

plotpoint stands on other people's work. These are the sources that shaped it,
what was taken from each, and how. Credit here is factual; none of these authors
or organizations is affiliated with plotpoint or endorses it.

| Work | Authors | What plotpoint uses | How |
| --- | --- | --- | --- |
| [From Data to Viz](https://www.data-to-viz.com/) | Yan Holtz, Conor Healy | Chart families organized by data shape; catalogue of common chart mistakes | Ideas, paraphrased |
| [Dataviz Inspiration](https://www.dataviz-inspiration.com/) | Yan Holtz | Reference gallery during research | Inspiration only |
| [ColorBrewer 2.0](https://colorbrewer2.org/) | Cynthia Brewer, Mark Harrower, The Pennsylvania State University | Sequential / diverging / qualitative color framework; scheme names (`Blues`, `RdBu`) | Names and concepts only; no color specifications included |
| [Dashboard Design Patterns](https://dashboarddesignpatterns.github.io/) | Benjamin Bach, Euan Freeman, Alfie Abdul-Rahman, Cagatay Turkay, Saiful Khan, Phong H. Nguyen, Yulei Fan, Min Chen | Pattern vocabulary for dashboard structure, screenspace, layout and color | Pattern names cited; guidance paraphrased |
| [Storytelling with Data](https://www.storytellingwithdata.com/) | Cole Nussbaumer Knaflic | Audience-first workflow: context, declutter, focus attention, tell a story | Principles paraphrased |
| Visual Vocabulary | Financial Times | Chart families organized by the relationship being shown | Grouping idea, paraphrased |
| Okabe-Ito palette | Masataka Okabe, Kei Ito | Colorblind-safe categorical palette in the fallback rendering rules | Seven color values listed |
| Information Dashboard Design | Stephen Few | At-a-glance dashboard principles | Ideas, paraphrased |
| [Vega-Lite](https://vega.github.io/vega-lite/) and [vl-convert](https://github.com/vega/vl-convert) | Vega project contributors (BSD-3-Clause) | The chart grammar and offline renderer behind every SVG, PNG and interactive chart | Runtime dependency (`vl-convert-python`); not redistributed |
| [Source Sans 3](https://github.com/adobe-fonts/source-sans) | Adobe (SIL Open Font License 1.1) | Regular, Semibold and Bold TTFs (release 3.052R) used for slide images so they look the same on every machine | Font files redistributed unmodified in `plugins/plotpoint/skills/visualize/fonts/` with their license |
| dataviz skill | Anthropic | Rendering method: form heuristic, color formula, mark specs, accessibility; palette validator | Method applied; palette checked with its validator; no text or code copied |

## Citation

Dashboard Design Patterns is cited as:

> B. Bach et al., "Dashboard Design Patterns," *IEEE Transactions on
> Visualization and Computer Graphics*, 2023. arXiv:2205.00757.

## Adding to this list

When new work draws on a source, add a row here and a line to `NOTICE` in the
same change. Record **what** was used and **how** (ideas, names, values, code).
If text, code or data is copied rather than paraphrased, check the source's
license first and record the decision in `docs/decisions.md`.
