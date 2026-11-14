# Profiles and outliers

Read profiles, not raw rows: `visualize.py profile request.yaml` (all datasets
in a storyboard request) or `visualize.py profile --data FILE`. A profile is
small no matter how big the data, and it is built so outliers can't hide.

## What a profile contains

| Element | Contents |
| --- | --- |
| Per numeric column | min, max, mean, median, quartiles, IQR, nulls; **outlier count and values** (1.5 × IQR rule); skew and a skew flag |
| Dominance flag | Set when max ÷ median > 10: one value will flatten the rest on a linear axis |
| `extreme_rows` | The full rows holding each numeric column's min and max, so you can see *which* entity is extreme |
| Per text column | Distinct count, top values with their share, long-tail share |
| Per date column | Earliest, latest, distinct count |
| `sample_rows` | First and last rows, the extreme rows, then a seeded random sample: up to 15 rows, the same every run |
| `flags` | One line per notable finding |

## Handling a flagged outlier

When a plotted measure has an outlier or dominance flag, the intent must say how
it's handled (`outlier_handling`). The `outliers` check fails if it doesn't.
Columns can be handled differently: give a list with one entry per `column`
(`references/spec.md`). The skew flag is informational only, and tables are
exempt because they show every value.

| Method | When | How it renders |
| --- | --- | --- |
| `callout` | The outlier **is** the story | Highlight or annotate it (`highlight`, `callouts`) |
| `log_scale` | Values span orders of magnitude and all matter | Log y-axis; say so in the axis title or a note |
| `exclude` | The caller confirms it's an error or out of scope | Rows matching `exclude` values are dropped; a note says what and why |
| `accept` | It's real and the chart reads fine with it (e.g. a histogram's tail) | Drawn as-is; give the `reason` |

Never exclude silently, and never exclude on your own judgment: ask the caller.
Rendering always reads the full data, so outliers are drawn correctly whatever
the profile says; the profile only informs decisions.

Some flags are expected: a small series of five quarters may show "skewed", and
a big category in a bar chart may be an IQR outlier. Decide whether it changes
the story; if not, use `accept` with a short reason.

An accepted outlier still sets the axis range. If it squeezes the other points
into a corner (one branch with three times the staff of the rest), consider
`log_scale` for that column, or keep it and add a note saying why it's there.
