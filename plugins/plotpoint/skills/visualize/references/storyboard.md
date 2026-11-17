# Storyboarding: planning the visual story

Storyboard sees every question and dataset at once, so it can advise on things
single-visual calls can't. Its output is **advice**: the caller decides.

## Advice it gives

| Kind | Ask | Typical signal |
| --- | --- | --- |
| `order` | Which visual leads? | The one that answers the main question for the primary audience goes first |
| `merge` | Do two datasets tell one story? | Same x-axis and measure (e.g. two series over the same quarters) |
| `demote` | Is a chart the right form? | No single takeaway, many measures across many categories: a table |
| `cut` | Does it answer any question? | A dataset attached to a question it doesn't address |
| `add-summary` | Is a headline figure missing? | Decision-makers would need one number first |
| `placement` | Summary, body or appendix? | Audience and level of detail |
| `rendering` | Should the technique differ by format? | E.g. Mermaid in Markdown but SVG in HTML so a callout can be drawn |

When a visual combines datasets (a merge or a join), set the visual's `data`
to the file the caller should build and `data_note` to how; the intent's column
names refer to that table. To dry-run it, build that file yourself first (a
scratch copy is fine) at the path you name. Its source line joins the sources of
every dataset it uses.

## Audiences and placement

Audiences come from the write-up; each question names its own, and the caller
decides them. A visual inherits its question's audiences. You may narrow them
(detail only practitioners need goes to them alone), but never widen them in
the plan: propose it instead (below).

| Placement | For | Contents |
| --- | --- | --- |
| `summary` | Decision-makers, read first | The visual(s) answering the main questions; fewest series; the decision stated |
| `body` | The main readers | Supporting evidence; practitioner detail |
| `appendix` | Reference | Tables and full breakdowns |

Audience changes the level of detail, not the facts. When a question scoped to
practitioners bears on a decision (for example, a fleet manager's question
about which delivery vans are due for replacement, when replacing them is a
budget decision), the decision-makers may need to see it too. Don't add them
to the plan; recommend it, and let the caller decide:

- `add-summary`: a one-line `sentence` or `number` for the decision-makers,
  with the question it answers and why it bears on their decision.
- `placement`: showing them the visual itself, and why.

The plan keeps the caller's audiences until the caller accepts.

## With a draft (mode A)

Read the draft for: the narrative order, the visuals it already has (and what's
wrong with them), conclusions it states, and which formats it's headed for.
Advice can then name the draft's sections and existing visuals, e.g. "replace
the two loans bar charts with one line chart" or "move the café section out".

## Colors across the document

Build one `color_map` so an entity keeps its color in every visual: the
story's subject → `accent`, comparison context → `context` (unmapped
entities beside a highlight are gray anyway; map them to keep them gray
everywhere), otherwise `slot1`…`slot8` in a fixed order. Each visual's subject can be `accent` (one
map may hold several). Never more than eight colored entities in one visual.

## Rules

- Don't invent conclusions. Without a `takeaway`, headlines are `draft`.
- Every visual must answer at least one question.
- Reference visuals with no single takeaway (appendix tables) use a descriptive
  headline with `headline_status: title`.
- Before returning, dry-run the plan (`visualize.py check-plan`) and fix any
  failing check: headline numbers, outliers, callouts.
- Validate the result before returning it.
