# Try it: a hands-on tour

Run plotpoint on the invented library-review write-up: first the engine by
itself, then the full skill through Claude. Allow about an hour. Everything
here works on a local copy: nothing is committed or pushed.

## 1. Set up

From the unzipped `plotpoint/` folder:

```bash
cd plotpoint                                  # the repo folder
REPO="$PWD"
python3 --version                             # needs 3.11 or later
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
source .venv/bin/activate                     # so `python` has the dependencies
VIZ="python $REPO/plugins/plotpoint/skills/visualize/scripts/visualize.py"
```

The skill's script checks its own dependencies. On a fresh machine, with
neither the virtual environment above nor [uv](https://docs.astral.sh/uv/), it
does no work and exits with code 3 and a setup message for your OS. Either
follow that message, or use `uv run <script> ...` in place of `python <script>
...`, which installs the dependencies in one step. Once the per-user cache
environment the message sets up exists, plain `python3` (`py` on Windows) works
too: the script finds the environment itself. The tour's `$VIZ` uses the
virtual environment above, so none of this applies to it.

Optional: `npm install -g @mermaid-js/mermaid-cli` lets the renderer test
Mermaid output, and the Markdown Preview Mermaid Support extension shows
Mermaid charts in VS Code's preview.

Work in a scratch copy of the fixture, next to the repo (not inside it), so the
originals stay clean and nothing you generate can end up in a commit:

```bash
SANDBOX="$(dirname "$REPO")/plotpoint-sandbox"   # e.g. ~/dev/plotpoint-sandbox
cp -R tests/fixtures/library-review "$SANDBOX"
# leave out the answer key and the recorded runs, so you form your own view first
rm -rf "$SANDBOX/runs" "$SANDBOX/storyboard-golden.yaml" "$SANDBOX/expected.md" \
  "$SANDBOX/render-data.yaml"
cd "$SANDBOX"
```

**Spoiler note.** The answers stay in the repo, in
`tests/fixtures/library-review/`: `storyboard-golden.yaml` (the reference
storyboard), `expected.md` (what a good answer must do), `render-data.yaml`
(which file each reference visual renders from) and `runs/` (recorded model
runs). Don't open them until you've formed your own view; section 5 uses them.

`$REPO`, `$VIZ` and `$SANDBOX` last for this terminal session; set them again in
a new one.

## 2. Look at the inputs

All data is invented. Open these in VS Code:

| File | What it is |
| --- | --- |
| `storyboard-request.yaml` | The write-up's brief: two audiences, four questions (some with the caller's takeaway), seven datasets |
| `data/` | The datasets, deliberately in every supported form: `.csv`, `.tsv`, `.json`, `.jsonl`, plus one inline in the request |
| `data/derived/` | A table built from two datasets (print and e-book loans joined on quarter), as the storyboard's merge recommendation asks the caller to do |
| `drafts/review.md` | A draft write-up with weak visuals (two bar charts for one story, a 48-bar chart) |
| `storyboard-request-with-draft.yaml` | The same brief plus the draft (mode A) |
| `requests/` | Ready-made render requests for section 3 |

The fixture is built so a good storyboard has to **order** the visuals,
**merge** print and e-book loans, **demote** a wide comparison to a table,
**cut** café revenue (it answers no question), **place** by audience, and
**handle an outlier** (Riverside's 48-minute wait).

Field meanings: `plugins/plotpoint/skills/visualize/references/spec.md`.

## 3. Run the engine yourself (no Claude)

The scripts are deterministic: they check, profile and draw, but don't make
judgments. This is how you learn what the engine guarantees.

**Validate and profile.**

```bash
$VIZ validate storyboardRequest storyboard-request.yaml
$VIZ profile storyboard-request.yaml          # every dataset
$VIZ profile --data data/branch_waits.jsonl   # one file
```

In the profiles, notice the outlier flags (Riverside's wait, Central's
staffing), `extreme_rows` naming which branch is extreme, and samples that
always include the extremes. This is what Claude reads instead of raw rows.

**Render a planned visual to every format.**

```bash
$VIZ render --quiet requests/v1-line.yaml
```

`--quiet` still writes every file; it only shortens what's printed. Every
`render` flag is explained in `spec.md`, "Render flags".

Then look at `requests/out/v1/`. Each format writes one **deliverable**, the
file you'd publish or paste; the other files are **by-products** (parts of a
deliverable, kept for reuse). The full list is in `spec.md`, "Files".

| File | Format | Deliverable or by-product |
| --- | --- | --- |
| `v1-md-document.md` | Markdown: headline, chart, notes, source. Open it in VS Code's preview | Deliverable |
| `v1-md-document.mmd` | The Mermaid chart inside that `.md` | By-product (chart only) |
| `v1-html-document.html` | The HTML fragment (`<figure>` with an inline SVG) to paste into a page | Deliverable |
| `v1-html-document.svg` | The chart alone, already inline in the fragment | By-product (chart only) |
| `v1-html-slide.html` | A 1440 × 810 slide for an HTML deck | Deliverable |
| `v1-image-slide.png` | Slide image (3840 × 2160) to paste into PowerPoint or Keynote | Deliverable |
| `v1-image-slide.svg` | The same slide as vector | By-product |
| `v1.result.json` | Everything: snippets, files, sizes and checks | The report |

With `technique: svg` the Markdown deliverable links its chart image
(`v1-md-document.svg`) from its own folder, so keep the two together. The
`snippet` in `v1.result.json` holds the same text with links relative to the
request's folder, for pasting into a document of yours.

Read the checks in `v1.result.json`. `headline_numbers` lists what each number
in the headline matched, for example that 18% is the change in total loans from
Q1 '26 to Q2 '26.

**The other ready-made requests.**

```bash
$VIZ render --quiet requests/v3-scatter.yaml   # outlier handled per column
$VIZ render --quiet requests/v2-number.yaml    # a single number
$VIZ render --quiet requests/broken.yaml       # fails on purpose
```

`broken.yaml` fails three checks at once (and has a draft headline), so its
HTML fragment starts with `DRAFT` and `CHECKS FAILED` lines; slides get a colored
bar. Its comments say why; fix one problem
at a time and re-run until it passes. That's the loop Claude follows.

**Experiments worth doing.** Edit a request, re-run it, and look:

- In `v1-line.yaml`, change `technique: {md/document: mermaid}` to `svg`.
  The intent is the same; the Markdown rendering changes, and the callout moves
  from text under the chart onto the chart.
- In `v3-scatter.yaml`, set `layout: {html/document: {content_width: 600}}`.
  The chart is redrawn at 600 px with larger text, not shrunk.
- Change v1's headline to "Total loans fell 22%", or "rose 18%": both fail.
- Remove the `outlier_handling` list from `v3-scatter.yaml`: `outliers` fails.

## 4. Run the skill through Claude

This is the part the engine can't do alone: choosing the story.

**Install the plugin from your local folder.** It reads the skill from the
folder, so it's exactly what you're about to commit:

```bash
claude plugin marketplace add "$REPO"
claude plugin install plotpoint@plotpoint
```

Run these two commands once in any terminal (VS Code's integrated terminal
works). They install for your user, so the plugin is also available in the
Claude Code extension for VS Code and in the Desktop app's local sessions on the
same computer (not in cloud sessions). In VS Code you can instead type
`/plugins` in the prompt box to open **Manage plugins**. A session that was
already open picks the plugin up after `/reload-plugins`, or when you start a
new one.

Start Claude Code **in the sandbox, with the virtual environment active** (so
the skill's scripts find their dependencies):

```bash
cd "$SANDBOX" && source "$REPO/.venv/bin/activate" && claude
```

In VS Code, open the sandbox folder; in Desktop, choose it with the project
folder control next to the environment selector. There
the skill finds its dependencies itself: if they're missing, Claude shows you
the exit-3 setup message from section 1 and stops.

Check it's there with `/plugin` (`/plugins` in VS Code), or ask "what skills
do you have?". Then try
each mode, in a fresh session each time if you can, so earlier answers don't
leak in.

| Mode | Ask Claude |
| --- | --- |
| B: storyboard, data only | "Use plotpoint to storyboard `storyboard-request.yaml`. Save the result as `my-storyboard.yaml`." |
| A: storyboard with a draft | "Use plotpoint to storyboard `storyboard-request-with-draft.yaml` and tell me what to change in the draft. Save the result as `my-storyboard-a.yaml`." |
| C: one visual, no intent | "Use plotpoint to render `requests/mode-c.yaml`." Claude decides the chart, headline and emphasis, renders, and looks at the result |
| D: render a plan | "Render every visual in `my-storyboard.yaml` to Markdown and HTML with plotpoint." |
| Your own question | "Chart `data/branch_overview.json` with plotpoint for a board slide: which branches are busiest?" |

The answer key isn't in the sandbox, so the session can't read it.

## 5. Compare with the answers (spoilers)

Once you've formed your own view, the answers are in
`$REPO/tests/fixtures/library-review/`. **Score a storyboard** against E1–E11
(in a separate terminal):

```bash
python "$REPO/scripts/score_storyboard.py" my-storyboard.yaml
```

Then compare it with `$REPO/tests/fixtures/library-review/storyboard-golden.yaml`
(and read `expected.md` beside it). Differences aren't automatically
wrong: the reference is one good answer. Recorded runs by independent agents,
and what they got wrong, are in `$REPO/tests/fixtures/library-review/runs/`.

**Dry-run the whole reference storyboard** (checks only, no files):

```bash
$VIZ check-plan storyboard-request.yaml \
  "$REPO/tests/fixtures/library-review/storyboard-golden.yaml"
```

**See the full worked example**, a whole write-up rendered from the reference
storyboard:

```bash
cd "$REPO" && python scripts/build_examples.py && cd "$SANDBOX"
```

Open `docs/examples/library-review/README.md` (Markdown preview) and
`docs/examples/library-review/page.html` (browser) in the repo.

## 6. What to judge while you explore

- **Storyboard:** does the order lead with the answer? Are the merge, demote
  and cut recommendations right? Are draft headlines marked as drafts?
- **Charts:** is the headline's claim visible at a glance? Any clipped or
  overlapping labels? Is the highlight on the right thing?
- **Formats:** would you paste these into your real Markdown and HTML
  documents and slides? Is 960 px (`report`) the right default for your pages?
- **Checks:** did any check pass on something wrong, or fail on something
  right?
- **Docs:** was anything in `SKILL.md` or `references/` unclear when you read it?

Note anything you find; it becomes a fix before the first commit, or a
`HANDOFF.md` backlog item.

## 7. Clean up

```bash
claude plugin uninstall plotpoint@plotpoint
claude plugin marketplace remove plotpoint
rm -rf "$SANDBOX"
```

After the first push, install from GitHub instead
(`claude plugin marketplace add ndany/plotpoint`).
