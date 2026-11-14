"""Profile a table so decisions can be made without reading every row.

A profile always surfaces outliers: distribution stats, an outlier count by the
1.5 x IQR rule, a dominance flag (max / median > threshold), the full rows that
hold each numeric column's min and max, and sample rows that include those
extremes. Sampling is deterministic (seeded), so the same input gives the same
profile. See references/profiling.md.
"""

from __future__ import annotations

import random
import statistics
from collections import Counter
from typing import Any

from .data import Table

DOMINANCE_RATIO = 10.0
SKEW_THRESHOLD = 1.0
SKEW_MIN_N = 8  # below this, "skew" is noise
SAMPLE_SEED = 20261101
SAMPLE_RANDOM = 5
SAMPLE_MAX = 15
TOP_CATEGORIES = 8


def _round(x: float) -> float:
    return round(x, 4) if isinstance(x, float) else x


def numeric_stats(values: list[float]) -> dict[str, Any]:
    n = len(values)
    out: dict[str, Any] = {"min": min(values), "max": max(values)}
    out["mean"] = _round(statistics.fmean(values))
    out["median"] = _round(statistics.median(values))
    if n >= 4:
        q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    else:
        q1, q3 = min(values), max(values)
    iqr = q3 - q1
    out.update(q1=_round(q1), q3=_round(q3), iqr=_round(iqr))
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = sorted({v for v in values if v < lo or v > hi})
    shown = outliers if len(outliers) <= 10 else outliers[:5] + outliers[-5:]
    out["outliers"] = {
        "count": sum(1 for v in values if v < lo or v > hi),
        "values": shown,
    }
    stdev = statistics.pstdev(values) if n > 1 else 0.0
    skew = 3 * (out["mean"] - out["median"]) / stdev if stdev else 0.0
    out["skew"] = _round(skew)
    out["skew_flag"] = n >= SKEW_MIN_N and abs(skew) > SKEW_THRESHOLD
    median = out["median"]
    out["dominance_flag"] = bool(
        median and median > 0 and out["max"] / median > DOMINANCE_RATIO
    )
    return out


def _category_stats(values: list[Any]) -> dict[str, Any]:
    counts = Counter(values)
    total = len(values)
    top = counts.most_common(TOP_CATEGORIES)
    tail = total - sum(c for _, c in top)
    return {
        "distinct": len(counts),
        "top": [{"value": v, "count": c, "share": _round(c / total)} for v, c in top],
        "tail_share": _round(tail / total) if total else 0.0,
    }


def _date_stats(values: list[str]) -> dict[str, Any]:
    ordered = sorted(set(values))
    return {"min": ordered[0], "max": ordered[-1], "distinct": len(ordered)}


def profile(table: Table, dataset_id: str = "data") -> dict[str, Any]:
    cols: list[dict[str, Any]] = []
    flags: list[str] = []
    extreme_idx: list[tuple[str, str, int]] = []
    for col in table.columns:
        raw = table.values(col)
        present = [v for v in raw if v is not None]
        info: dict[str, Any] = {
            "name": col,
            "type": table.types.get(col, "text"),
            "nulls": len(raw) - len(present),
        }
        if info["type"] == "number" and present:
            info.update(numeric_stats(present))
            for kind, target in (("min", info["min"]), ("max", info["max"])):
                idx = next(i for i, v in enumerate(raw) if v == target)
                extreme_idx.append((col, kind, idx))
            if info["outliers"]["count"]:
                flags.append(
                    f"{col}: {info['outliers']['count']} outlier(s) by 1.5xIQR"
                )
            if info["dominance_flag"]:
                flags.append(
                    f"{col}: max is >{DOMINANCE_RATIO:g}x the median "
                    "(dominates a linear axis)"
                )
            if info["skew_flag"]:
                flags.append(f"{col}: skewed (skew {info['skew']})")
        elif info["type"] == "date" and present:
            info.update(_date_stats(present))
        elif present:
            info.update(_category_stats(present))
        cols.append(info)

    n = len(table.rows)
    picks: list[int] = list(range(min(3, n))) + list(range(max(0, n - 3), n))
    picks += [i for _, _, i in extreme_idx]
    rng = random.Random(SAMPLE_SEED)  # noqa: S311 - deterministic sampling, not security
    picks += rng.sample(range(n), min(SAMPLE_RANDOM, n))
    seen: list[int] = []
    for i in picks:
        if i not in seen:
            seen.append(i)
    sample = [table.rows[i] for i in sorted(seen[:SAMPLE_MAX])]

    return {
        "dataset": dataset_id,
        "rows": n,
        "columns": cols,
        "extreme_rows": [
            {"column": c, "kind": k, "row": table.rows[i]} for c, k, i in extreme_idx
        ],
        "sample_rows": sample,
        "flags": flags,
    }
