# Testing

How plotpoint is tested, what each kind of test proves, and how to add tests.
Run everything with `scripts/check-all.sh` (CI runs the same script).

## The fixture

[`tests/fixtures/library-review/`](../tests/fixtures/library-review/) is an
invented analysis write-up, "City library services review": four questions, two
audiences (board, branch managers) and seven datasets in every supported form
(`.csv`, `.tsv`, `.json`, `.jsonl`, `inline`). It's built so that a correct
storyboard must **order**, **merge**, **demote**, **cut**, place by
**audience**, render **differently per format**, and **handle an outlier**
(Riverside's 48-minute wait).

| File | Purpose |
| --- | --- |
| `storyboard-request.yaml` | Mode B request (datasets only) |
| `storyboard-request-with-draft.yaml` | Mode A request (adds the draft) |
| `drafts/review.md` | A draft with naive visuals |
| `storyboard-golden.yaml` | The maintainer-reviewed reference answer |
| `render-data.yaml` | Which file each reference visual renders from |
| `expected.md` | Expectations E1–E11 and single-visual expectations |
| `requests/` | Render requests for the hands-on tour ([`guide/try-it.md`](guide/try-it.md)); a test keeps them behaving as documented |
| `runs/` | Recorded model runs, kept verbatim (not linted): T1–T3, then T2b, T3b and T3c (with headline probes) after the fixes each round prompted |

## Test map

| Test | Mode | What it proves | Where |
| --- | --- | --- | --- |
| T1 | A: storyboard with draft | The skill's instructions lead a model to the expected story | Recorded run, checked by `test_storyboard_runs.py` |
| T2 | B: storyboard, datasets only | Same, without the draft | Recorded run, checked |
| T3 | C: one visual at a time | Single-visual decisions and checks | Recorded run (notes and render results) |
| T4 | D + differential rendering | Every reference visual renders to all four targets; techniques per target; intent identical across targets; colors follow the color map | `test_render.py` |
| T5 | Layout | Each chart type at each preset and at caller widths; legibility | `test_render.py`, `test_layout_schema_checks.py` |
| T6 | Profiling | Every data form loads; outliers flagged; extremes sampled; deterministic | `test_data_profile.py` |
| Unit | — | Schemas, headline-number, outlier and callout checks, dry run, colors, id prefixing, table sorting, CLI | `test_layout_schema_checks.py`, `test_render.py` |

## Kinds of check

| Kind | What | Runs |
| --- | --- | --- |
| Deterministic | Engine output, schemas, checks, sizes, colors | `pytest`, every commit and CI |
| Render validity | Mermaid parses and renders | `pytest` with the Mermaid CLI; skipped with a notice where it's missing |
| Model behavior | Storyboard and mode C decisions | Recorded runs (below); not in CI |
| Visual review | Clipping, overlap, legibility, whether the claim is visible | By looking at rendered output; findings in the skill's `DESIGN.md` |
| Viewer check | VS Code and GitHub render the Mermaid output | Manual, when the Mermaid version changes |

## Recording a model run (T1–T3)

Model behavior can't be unit-tested, so runs are recorded and their results kept
honest by tests.

1. Copy the fixture to a scratch folder and **remove** the answer files
   (`storyboard-golden.yaml`, `expected.md`, `render-data.yaml`).
   Copy the skill folder in too, without `DESIGN.md` (it holds past test
   findings).
2. Run the skill in a **fresh session or sub-agent that hasn't seen the design
   or the answers**, given only the skill folder and the request. Ask it for the
   result plus a "Skill feedback" section in `notes.md`. Its brief says what not
   to open: the repository (its `docs/`, `tests/` and any `runs/` folder),
   `DESIGN.md`, `docs/plans/`, the answer files by name, and any notes from
   earlier tests; it reads only the scratch folder, and says in `notes.md` if it
   opened anything else. Afterwards, check its transcript for reads outside the
   scratch folder and record the result in `notes.md`.
3. Save the outputs to `tests/fixtures/library-review/runs/<date>-<test>/`:
   `storyboard-result.yaml` (T1, T2), `notes.md`, and for T3 the render requests.
4. `pytest` checks every saved storyboard result against E1–E11
   (`scripts/score_storyboard.py RESULT` scores one by hand). If a run
   misses an expectation for a reason you accept, list it in that run's
   `known-misses.txt` (`E5 reason...`) and record why in `notes.md`.
5. Act on the skill feedback: fix the instructions, then re-run.

## Worked example

`docs/examples/library-review/` is generated from the reference storyboard by
`scripts/build_examples.py` (a Markdown write-up, an HTML page of fragments, and
slide images). Re-run it after any rendering change and look at the result; it
fails if any check fails.

## Adding a test for a new visual type

1. Add a builder in `scripts/ppviz/vl.py` and its shaping in `shape.py`.
2. Add a parametrized case to `test_t5_each_chart_type_renders_at_each_document_layout`.
3. Add it to a fixture visual if it belongs in the story, and to the reference answer.
4. Render it and look at it at each layout; record findings in `DESIGN.md`.
5. Re-run `scripts/build_examples.py` if the example uses it.
