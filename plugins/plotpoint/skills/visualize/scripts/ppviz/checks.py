"""Checks run on every render. Each returns (status, detail).

- headline_numbers: every number in the headline and callouts can be derived
  from the plotted data, and the detail says what each one matched. Allowed:
  values of plotted measures (only min and max above a row limit), counts,
  totals, summary statistics (mean, median, quartiles, deciles), shares of a
  total (bar, stacked bar, table), and changes (percent or absolute) between
  consecutive values, first and last, or peak or low and latest (time series,
  bars, tables), or between a value and its `previous`. A change must go the
  way the text says ("fell 3%" doesn't match a 3% rise). Bin edges, ranks and
  differences between arbitrary rows don't count.
- callouts: every point or rule callout is pinned to something on the chart.
- outliers: a flagged outlier in a plotted measure is handled explicitly, per
  column when columns need different handling. Tables and sentences skip.
- legibility: the smallest text stays >= the minimum px at the narrowest
  expected display width.
- capacity: reported from the shaping step (form changed, or warning).
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from typing import Any

from . import config
from .data import Table
from .layout import Layout
from .shape import Shaped, fmt, handling_for, match_callout

NUMBER_TOKEN = re.compile(
    r"(?<![\w'’.])([-−]?\d[\d,]*(?:\.\d+)?)(\s?%)?"
    r"(?:(k|K|M|B)|\s?(bn)|\s(thousand|million|billion))?(?![\w'’])"
)
# Scale suffixes ('212k', '1.2M', '3bn', '4 million'); lowercase m stays minutes.
SCALES = {"k": 3, "K": 3, "thousand": 3, "M": 6, "million": 6}
SCALES |= {"B": 9, "bn": 9, "billion": 9}
_UNIT_WORDS = {3: "thousands", 6: "millions", 9: "billions"}
# A measure declared in a scaled unit: 'visits_k', 'Visits (k)', 'in thousands'.
UNIT_HINTS = {
    3: re.compile(r"(?:_k$|\(k\)|\bthousands?\b|\b000s\b)", re.I),
    6: re.compile(r"(?:_m$|_mn$|\(m\)|\(mn\)|\bmillions?\b)", re.I),
    9: re.compile(r"(?:_bn$|\(bn\)|\bbillions?\b)", re.I),
}
FALL = re.compile(
    r"\b(fell|fall|falls|drop\w*|declin\w*|down|decreas\w*|lower|los[st]|shr[ua]nk|cut)\b",
    re.I,
)
RISE = re.compile(
    r"\b(rose|rise|rises|grew|grow\w*|up|increas\w*|higher|gain\w*|climb\w*|jump\w*)\b",
    re.I,
)
RATIO = re.compile(r"\b(\d+) (?:in|out of) (\d+)\b")
QUANTILE_SHARES = {10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90}
SHARE_WORDS = {
    "half": 50.0,
    "a third": 100 / 3,
    "one third": 100 / 3,
    "two thirds": 200 / 3,
    "a quarter": 25.0,
    "one quarter": 25.0,
    "three quarters": 75.0,
    "most": None,  # more than half
}
SHARE_WORD = re.compile(r"\b(" + "|".join(SHARE_WORDS) + r")\b", re.I)
THRESHOLD = re.compile(
    r"(?:\b(?:over|above|under|below|within|more than|less than|at least|at most)"
    r"\s+$)|(?:^\s*\w*\s*(?:or more|or longer|or less|or fewer|or above|or below|\+))",
    re.I,
)
AGGREGATE = re.compile(
    r"\b(mean|median|total|overall|typical|across|all|percentile|quartile|sum|combined"
    r"|everyone|every)\b",
    re.I,
)
MULTIPLE = re.compile(r"\s*(?:times\b|×|x\b|-fold\b)", re.I)
SERIES_TYPES = ("line", "bar", "stacked_bar", "number")
SHARE_TYPES = ("bar", "stacked_bar", "table")


def _scale(m: re.Match[str]) -> int:
    """Power of ten a number's suffix stands for (0 without one)."""
    suffix = m.group(3) or m.group(4) or m.group(5)
    return SCALES[suffix.lower() if len(suffix) > 1 else suffix] if suffix else 0


def numbers_in(text: str) -> list[tuple[float, int, bool, str]]:
    """(value, decimals, is_percent, token) for each standalone number in text.
    Suffixed numbers are scaled ('212k' -> 212000), and their decimals go
    negative, so the match tolerance follows the rounding ('212k' is +-500)."""
    found = []
    for m in NUMBER_TOKEN.finditer(text):
        token = m.group(1).replace("−", "-")
        digits = token.replace(",", "")
        decimals = len(digits.split(".")[1]) if "." in digits else 0
        exp = _scale(m)
        found.append(
            (
                float(digits) * 10**exp,
                decimals - exp,
                bool(m.group(2)),
                m.group(0).strip(),
            )
        )
    return found


def _declared_scales(table: Table, intent: dict[str, Any]) -> set[int]:
    """Scales the measures say they're stored in (column name, names, units)."""
    names = (intent.get("fields") or {}).get("names") or {}
    texts = [intent.get("units") or ""]
    for c in _measures(table, intent):
        texts += [c, str(names.get(c, ""))]
    return {e for e, rx in UNIT_HINTS.items() if any(rx.search(t) for t in texts)}


@dataclass
class Candidate:
    value: float  # signed for changes
    percent: bool
    change: bool
    desc: str
    entities: frozenset[str] = frozenset()  # rows it belongs to; empty = aggregate


def _measures(table: Table, intent: dict[str, Any]) -> list[str]:
    f = intent.get("fields") or {}
    ms = [m for m in measures_of(intent) if table.types.get(m) == "number"]
    if intent.get("visual_type") == "table":
        cols = f.get("columns") or table.columns
        ms += [c for c in cols if table.types.get(c) == "number" and c not in ms]
    if not ms:
        ms = [c for c in table.columns if table.types.get(c) == "number"]
    return ms


def _changes(name: str, xs: list[Any], vals: list[float]) -> list[Candidate]:
    pairs = [(i, i + 1) for i in range(len(vals) - 1)]
    if len(vals) > 1:
        last = len(vals) - 1
        hi = max(range(len(vals)), key=lambda i: vals[i])
        lo = min(range(len(vals)), key=lambda i: vals[i])
        pairs += [(0, last), (hi, last), (lo, last)]
    out = []
    for i, j in dict.fromkeys(pairs):
        a, b = vals[i], vals[j]
        where = f"{name} from {xs[i]} to {xs[j]} ({fmt(a)} → {fmt(b)})"
        ents = frozenset({str(xs[i]), str(xs[j])})
        out.append(Candidate(b - a, False, True, f"change in {where}", ents))
        if a:
            out.append(
                Candidate((b / a - 1) * 100, True, True, f"% change in {where}", ents)
            )
    return out


def _entity_column(table: Table, intent: dict[str, Any]) -> str | None:
    """The column naming each row: a scatter's labels, a chart's x, or a table's
    first text column."""
    f = intent.get("fields") or {}
    vt = intent.get("visual_type")
    if vt == "scatter":
        return f.get("label")
    if vt == "table":
        cols = f.get("columns") or table.columns
        return next((c for c in cols if table.types.get(c) != "number"), None)
    return f.get("x") or f.get("label")


def _mentioned(text: str, table: Table, intent: dict[str, Any]) -> set[str]:
    col = _entity_column(table, intent)
    if not col:
        return set()
    names = {str(v) for v in table.values(col) if v is not None}
    return {n for n in names if re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", text)}


def _candidates(table: Table, intent: dict[str, Any]) -> list[Candidate]:
    vt = intent.get("visual_type")
    f = intent.get("fields") or {}
    names = f.get("names") or {}
    ms = _measures(table, intent)
    limit = config.capacity()["headline_check"]["raw_values_max_rows"]
    xcol = _entity_column(table, intent)
    rows = [r for r in table.rows]
    xs = [r.get(xcol, i + 1) if xcol else i + 1 for i, r in enumerate(rows)]
    out = [Candidate(float(len(rows)), False, False, "row count")]
    series: list[tuple[str, list[Any], list[float]]] = []
    for m in ms:
        pts = [
            (x, r[m])
            for x, r in zip(xs, rows, strict=True)
            if isinstance(r.get(m), (int, float))
        ]
        if pts:
            series.append((names.get(m, m), [p[0] for p in pts], [p[1] for p in pts]))
    plotted = [m for m in ms if m != f.get("previous")]
    if len(plotted) > 1 and vt not in ("scatter", "table"):
        tot = [
            (x, sum(r[m] for m in plotted))
            for x, r in zip(xs, rows, strict=True)
            if all(isinstance(r.get(m), (int, float)) for m in plotted)
        ]
        if tot:
            label = "total (" + " + ".join(names.get(m, m) for m in plotted) + ")"
            series.append((label, [t[0] for t in tot], [t[1] for t in tot]))
    for name, sx, vals in series:
        if len(rows) <= limit:
            out += [
                Candidate(v, False, False, f"{name} at {x}", frozenset({str(x)}))
                for x, v in zip(sx, vals, strict=True)
            ]
        else:
            out += [
                Candidate(min(vals), False, False, f"minimum {name}"),
                Candidate(max(vals), False, False, f"maximum {name}"),
            ]
        out += [
            Candidate(statistics.fmean(vals), False, False, f"mean {name}"),
            Candidate(statistics.median(vals), False, False, f"median {name}"),
            Candidate(sum(vals), False, False, f"sum of {name}"),
        ]
        if len(vals) >= 4:
            for k, q in zip(
                (25, 50, 75),
                statistics.quantiles(vals, n=4, method="inclusive"),
                strict=True,
            ):
                out.append(Candidate(q, False, False, f"{k}th percentile of {name}"))
            for k, q in enumerate(
                statistics.quantiles(vals, n=10, method="inclusive"), 1
            ):
                out.append(
                    Candidate(q, False, False, f"{k * 10}th percentile of {name}")
                )
        total = sum(vals)
        if vt in SHARE_TYPES and total:
            out += [
                Candidate(
                    v / total * 100,
                    True,
                    False,
                    f"{x}'s share of {name}",
                    frozenset({str(x)}),
                )
                for x, v in zip(sx, vals, strict=True)
            ]
        ordered = vt in SERIES_TYPES or (
            vt == "table" and table.types.get(xcol or "") == "date"
        )
        if ordered:  # changes only along an ordered axis, not between table rows
            out += _changes(name, sx, vals)
    if len(plotted) > 1 and vt in ("line", "bar", "stacked_bar"):
        for x, r in zip(xs, rows, strict=True):  # each measure's share of its row
            vals = [r.get(m) for m in plotted]
            if all(isinstance(v, (int, float)) for v in vals) and sum(vals):
                out += [
                    Candidate(
                        r[m] / sum(vals) * 100,
                        True,
                        False,
                        f"{names.get(m, m)}'s share of the total at {x}",
                        frozenset({str(x)}),
                    )
                    for m in plotted
                ]
    prev = f.get("previous")
    if prev:
        for x, r in zip(xs, rows, strict=True):
            a, b = r.get(prev), r.get(f.get("value"))
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                for c in _changes(f"{x}", ["previous", "current"], [a, b]):
                    c.entities = frozenset({str(x)})
                    out.append(c)
    return out


def _direction(text: str, start: int) -> int:
    """-1 if the words just before a number say it fell, +1 if it rose, else 0."""
    window = re.split(r"[;:,(]|\.\s", text[max(0, start - 40) : start])[-1]
    fall, rise = FALL.search(window), RISE.search(window)
    if fall and not rise:
        return -1
    if rise and not fall:
        return 1
    return 0


def _match(
    value: float,
    decimals: int,
    is_pct: bool,
    sign: int,
    pool: list[Candidate],
    named: set[str] | None = None,
    aggregate_ok: bool = True,
) -> Candidate | None:
    """First candidate the number matches. When its clause names rows (a branch,
    a quarter), only candidates about those rows, or aggregates, qualify."""
    tol = 0.5 * 10 ** (-decimals) + 1e-9
    for c in pool:
        if named and c.entities and not (c.entities & named):
            continue
        if named and not c.entities and not aggregate_ok:
            continue  # "Riverside waits 14" must be Riverside's figure
        if c.percent != is_pct and not (is_pct and not c.change and not sign):
            continue  # a bare percent may match a value stored as a percent
        if c.change:
            if sign and c.value * sign < 0:
                continue
            if value < 0 and c.value > 0:
                continue
            if abs(abs(value) - abs(c.value)) <= tol:
                return c
        elif abs(value - c.value) <= tol:
            return c
    return None


def _clause(text: str, pos: int) -> tuple[int, int]:
    """Bounds of the clause around pos (split on ; , and sentence ends)."""
    starts = [m.end() for m in re.finditer(r"[;,]|\.\s", text[:pos])]
    m = re.search(r"[;,]|\.\s", text[pos:])
    return (starts[-1] if starts else 0, pos + m.start() if m else len(text))


def _shares_at(vals: list[float], t: float) -> dict[str, float]:
    n = len(vals)
    return {
        "at or below": sum(v <= t for v in vals) / n * 100,
        "below": sum(v < t for v in vals) / n * 100,
        "above": sum(v > t for v in vals) / n * 100,
        "at or above": sum(v >= t for v in vals) / n * 100,
    }


def _threshold_pairs(
    text: str, table: Table, intent: dict[str, Any]
) -> list[tuple[tuple[int, int], tuple[int, int], str]]:
    """Claims about a distribution, checked as a pair: '82% ... within 15 minutes'
    or 'half ... within 7.8' (a share equal to the share of values at, below or
    above the other number in the same clause), and bare thresholds ('30 minutes
    or more') with no share in their clause, which pass if any value is beyond
    them. Distributions only (histograms, or tables above the raw-value limit)."""
    limit = config.capacity()["headline_check"]["raw_values_max_rows"]
    if intent.get("visual_type") != "histogram" and len(table.rows) <= limit:
        return []
    cols = [c for c in _measures(table, intent) if table.numeric(c)]
    tokens = [(m, numbers_in(m.group(0))[0]) for m in NUMBER_TOKEN.finditer(text)]
    shares = [
        (m.span(), n[0], 0.5 * 10 ** (-n[1]), m.group(0)) for m, n in tokens if n[2]
    ]
    for w in SHARE_WORD.finditer(text):
        v = SHARE_WORDS[w.group(1).lower()]
        shares.append((w.span(), v, 3.0, w.group(1)))
    ratios = [r.span() for r in RATIO.finditer(text)]
    for r in RATIO.finditer(text):
        n, d = int(r.group(1)), int(r.group(2))
        if d:
            shares.append((r.span(), n / d * 100, 2.0, r.group(0)))
    plains = [
        (m, n)
        for m, n in tokens
        if not n[2] and not any(a <= m.start() < b for a, b in ratios)
    ]
    out = []
    used: set[tuple[int, int]] = set()
    for tm, (tv, _, _, ttok) in plains:
        lo, hi = _clause(text, tm.start())
        in_clause = [sh for sh in shares if lo <= sh[0][0] < hi and sh[0] not in used]
        for col in cols:
            dist = _shares_at(table.numeric(col), tv)
            found = None
            for span, val, tol, tok in in_clause:
                for k, sh in dist.items():
                    ok = sh > 50 if val is None else abs(sh - val) <= tol + 1e-9
                    if ok:
                        found = (span, f"{tok} = share of {col} {k} {ttok} ({sh:.0f}%)")
                        break
                if found:
                    break
            if found:
                out.append((tm.span(), found[0], found[1]))
                used.add(found[0])
                break
            phrase = (
                text[max(0, tm.start() - 15) : tm.start()],
                text[tm.end() : tm.end() + 30],
            )
            if not in_clause and (
                THRESHOLD.search(phrase[0]) or THRESHOLD.search(phrase[1])
            ):
                if dist["at or above"] and dist["at or below"]:
                    out.append(
                        (
                            tm.span(),
                            tm.span(),
                            f"{ttok} = threshold inside the range of {col}",
                        )
                    )
                    break
    return out


def _label_numbers(table: Table) -> set[str]:
    """Number-like text inside string or date cells (e.g. 'Branch 12', '2026-09')."""
    found: set[str] = set()
    for c in table.columns:
        if table.types.get(c) != "number":
            for v in table.values(c):
                if v is not None:
                    found.update(re.findall(r"\d+", str(v)))
    return found


def headline_numbers(
    texts: list[str], table: Table, intent: dict[str, Any]
) -> tuple[str, str]:
    pool = _candidates(table, intent)
    labels = _label_numbers(table)
    declared = _declared_scales(table, intent)
    missing, matched = [], []
    for text in texts:
        consumed: list[tuple[int, int]] = []
        for t_span, p_span, desc in _threshold_pairs(text, table, intent):
            matched.append(desc)
            consumed += [t_span, p_span]
        for r in RATIO.finditer(text):  # "1 in 10": a share, checked as one
            if r.span() in consumed:
                continue
            consumed.append(r.span())
            n, d = int(r.group(1)), int(r.group(2))
            share = n / d * 100 if d else -1
            lo, hi = _clause(text, r.start())
            others = [
                m
                for m in NUMBER_TOKEN.finditer(text)
                if lo <= m.start() < hi and not r.start() <= m.start() < r.end()
            ]
            hit = _match(share, 1, True, 0, pool)
            quantile = (
                round(share, 6) in QUANTILE_SHARES
                or round(100 - share, 6) in QUANTILE_SHARES
            )
            if hit or (quantile and not others):
                matched.append(
                    f"{r.group(0)} = " + (hit.desc if hit else "a quantile share")
                )
            else:
                missing.append(r.group(0))
        for m in NUMBER_TOKEN.finditer(text):
            if any(a <= m.start() < b for a, b in consumed):
                continue
            value, decimals, is_pct, token = numbers_in(m.group(0))[0]
            if token.replace(",", "").lstrip("-") in labels:
                continue
            sign = -1 if value < 0 else _direction(text, m.start())
            if MULTIPLE.match(text, m.end()):  # "8 times": a ratio, not checkable
                missing.append(f"{token} (a multiple; state the two values instead)")
                continue
            lo, hi = _clause(text, m.start())
            named = _mentioned(text[lo:hi], table, intent)
            agg = bool(AGGREGATE.search(text[max(0, m.start() - 25) : m.start()]))
            hit = _match(value, decimals, is_pct, sign, pool, named, agg or not named)
            exp = _scale(m)
            if not hit and exp in declared:  # '212k' against a column in thousands
                v, d = value / 10**exp, decimals + exp
                hit = _match(v, d, is_pct, sign, pool, named, agg or not named)
            if hit:
                matched.append(f"{token} = {hit.desc}")
            elif exp:
                missing.append(
                    f"{token} (= {value:,.0f}; if the data is in "
                    f"{_UNIT_WORDS[exp]}, say so in units or names)"
                )
            else:
                missing.append(token)
    if missing:
        return "fail", (
            "not derivable from the data (or the change goes the other way): "
            + ", ".join(missing)
            + ". Fix the number, or use a figure the data supports."
            + (" Matched: " + "; ".join(matched) if matched else "")
        )
    if not matched:
        return "pass", "no numbers to check"
    return "pass", "matched: " + "; ".join(matched)


def legibility(layout: Layout) -> tuple[str, str]:
    min_px = config.layouts()["legibility"]["min_label_px"]
    smallest = layout.smallest_text_px()
    status = "pass" if smallest >= min_px - 0.05 else "fail"
    return status, (
        f"smallest text {smallest:.1f}px at {layout.min_display_width}px display "
        f"(minimum {min_px}px)"
    )


def callouts(intent: dict[str, Any], shaped: Shaped) -> tuple[str, str]:
    problems = [
        p
        for c in intent.get("callouts") or []
        if (p := match_callout(c, shaped)[1]) is not None
    ]
    if problems:
        return "fail", "; ".join(problems) + ". Unpinned callouts are not drawn."
    n = len(intent.get("callouts") or [])
    return "pass", f"{n} callout(s) matched to the data" if n else "no callouts"


def outliers(
    profile: dict[str, Any], measures: list[str], intent: dict[str, Any]
) -> tuple[str, str]:
    if intent.get("visual_type") in ("table", "sentence"):
        return "skip", "nothing is plotted; outlier handling doesn't apply"
    flagged = [
        c
        for c in profile["columns"]
        if c["name"] in measures
        and c.get("type") == "number"
        and (c["outliers"]["count"] or c.get("dominance_flag"))
    ]
    if not flagged:
        return "pass", "no outliers flagged in plotted measures (skew is informational)"
    done, problems = [], []
    for c in flagged:
        name = (
            f"{c['name']} ({c['outliers']['count']} by IQR"
            + (", dominates axis" if c.get("dominance_flag") else "")
            + ")"
        )
        h = handling_for(intent, c["name"])
        method = (h or {}).get("method")
        if method in (None, "none_flagged"):
            problems.append(
                f"{name}: set intent.outlier_handling for this column "
                "(callout, log_scale, exclude, or accept with a reason)"
            )
        elif method == "callout" and not (
            intent.get("callouts") or intent.get("highlight")
        ):
            problems.append(f"{name}: method callout but no callout or highlight set")
        else:
            done.append(f"{name} by {method}")
    if problems:
        return "fail", "; ".join(problems)
    return "pass", "outliers handled: " + "; ".join(done)


def measures_of(intent: dict[str, Any]) -> list[str]:
    """The numeric columns a visual plots."""
    f = intent.get("fields") or {}
    out: list[str] = []
    y = f.get("y")
    if isinstance(y, str):
        out.append(y)
    elif isinstance(y, list):
        out += y
    for key in ("value", "previous"):
        if f.get(key):
            out.append(f[key])
    if intent.get("visual_type") == "scatter" and f.get("x"):
        out.append(f["x"])
    return out
