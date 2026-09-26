"""Small deterministic helpers for the DDR first-evidence pilot.

Only canonical, pre-locked gene rows may be passed to these functions.
This module does not download, select cohorts, infer endpoints, train a
model, calculate p-values, or claim assay-population uncertainty.
The functions are optional; the protocol, not this implementation, owns
scientific meaning. Tested with synthetic fixtures only by the author.
"""
from __future__ import annotations

import math
from statistics import median
from typing import Any, Mapping, Sequence

Row = Mapping[str, Any]


def numeric(value: Any, field: str = "value") -> float:
    """Reject booleans, nonnumeric values and nonfinite scores."""
    if isinstance(value, bool):
        raise ValueError(f"{field}: boolean cannot be a numerical score")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}: not numeric") from exc
    if not math.isfinite(out):
        raise ValueError(f"{field}: not finite")
    return out


def rank_numerators(values: Sequence[float]) -> list[int]:
    """Exact integer numerators of q=(midrank-.5)/n, denominator 2*n."""
    n = len(values)
    if n == 0:
        raise ValueError("rank_fraction: empty input")
    a = [numeric(v) for v in values]
    order = sorted(range(n), key=lambda i: a[i])
    out = [0] * n
    lo = 0
    while lo < n:
        hi = lo + 1
        while hi < n and a[order[hi]] == a[order[lo]]:
            hi += 1
        for k in range(lo, hi):
            out[order[k]] = lo + hi
        lo = hi
    return out


def rank_fraction(values: Sequence[float]) -> list[float]:
    """(ascending midrank - 0.5) / n; ties receive equal midranks."""
    return [v / (2 * len(values)) for v in rank_numerators(values)]


def summarize_records(records: Sequence[Row]) -> dict[str, Any]:
    """Summarize one gene's ORIGINAL eligible records without collapsing labels.

    Input mappings have unique original-row `record_id`, `rho`, and `gamma`.
    None, blank, NA/NaN, or nonfinite values are missing; unexpected strings
    raise an error. rho and gamma summaries use only same-record finite pairs.
    Original records are returned unchanged, with paired completeness beside
    them. Duplicate gene/transcript labels are permitted; duplicate original
    row IDs raise rather than silently deduplicating or double-counting.
    """
    if not records:
        raise ValueError("no original eligible records")
    ids = [r["record_id"] for r in records]
    if any(v is None or str(v).strip() == "" for v in ids) or len(set(ids)) != len(ids):
        raise ValueError("original record IDs must be present and unique")

    def finite_or_missing(v: Any) -> float | None:
        if v is None or (isinstance(v, str) and v.strip().lower() in ("", "na", "nan", "null")):
            return None
        if isinstance(v, bool):
            raise ValueError("boolean cannot be a numerical score")
        value = float(v)
        return value if math.isfinite(value) else None

    parsed = [(finite_or_missing(r["rho"]), finite_or_missing(r["gamma"])) for r in records]
    complete = [a is not None and b is not None for a, b in parsed]
    paired = [(a, b) for (a, b), ok in zip(parsed, complete) if ok]
    rho = [a for a, _ in paired]
    gamma = [b for _, b in paired]
    signs = sorted({-1 if v < 0 else 1 if v > 0 else 0 for v in rho})
    out = {
        "r3_n_records": len(records), "r3_n_complete": len(paired),
        "r3_any_missing": not all(complete),
        "r3_sign_discordance": len(signs) > 1, "r3_rho_sign_set": signs,
        "r3_all_observed_rho_negative": all(v < 0 for v in rho) if rho else None,
        "r3_single_original_paired_complete": len(records) == 1 and all(complete),
        "r3_all_original_paired_complete": all(complete),
        "records": [dict(r) for r in records], "paired_complete": complete,
    }
    for prefix, values in (("rho_R3", rho), ("gamma_R3", gamma)):
        for suffix, func in (("min", min), ("median", median), ("max", max)):
            out[f"{prefix}_{suffix}"] = func(values) if values else None
    return out


def half_tie_greater(a: float, b: float) -> float:
    return 1.0 if a > b else (0.5 if a == b else 0.0)


def separation(positive: Sequence[float], comparator: Sequence[float]) -> float:
    """Finite-set probability of greater sensitization, with half credit for ties."""
    if not positive or not comparator:
        raise ValueError("NO_SOURCE_CLASS_CONTRAST")
    p = [numeric(x) for x in positive]
    c = [numeric(x) for x in comparator]
    return math.fsum(half_tie_greater(x, y) for x in p for y in c) / (len(p) * len(c))


def validate_rows(rows: Sequence[Row]) -> list[Row]:
    if not rows:
        raise ValueError("empty panel")
    genes = [r.get("gene") for r in rows]
    if any(not isinstance(g, str) or not g or g.strip() != g for g in genes):
        raise ValueError("gene IDs must be explicit nonempty exact strings")
    if len(set(genes)) != len(genes):
        raise ValueError("duplicate gene rows; do not count elements as independent genes")
    fields = (
        "gemini_sensitive", "source_generic_fragility", "rho_R2", "gamma_R2",
        "rho_R3_min", "rho_R3_median", "rho_R3_max", "gamma_R3_median",
        "rho_ATMi_R2", "rho_ATRi_R2", "rho_WEE1i_R2",
    )
    for r in rows:
        for name in fields:
            if name not in r:
                raise ValueError(f"{r['gene']}: missing {name}")
            numeric(r[name], f"{r['gene']}:{name}")
        if not (float(r["rho_R3_min"]) <= float(r["rho_R3_median"]) <= float(r["rho_R3_max"])):
            raise ValueError(f"{r['gene']}: inconsistent observed rho envelope")
        if not 0 <= float(r["source_generic_fragility"]) <= 1:
            raise ValueError("source_generic_fragility must be a fraction")
        if "source_called" in r and (not isinstance(r["source_called"], bool)
                                      or r["source_called"] != (float(r["gemini_sensitive"]) <= -1)):
            raise ValueError(f"{r['gene']}: frozen source class disagrees with locked threshold")
    return sorted(rows, key=lambda r: r["gene"])


def source_mask(rows: Sequence[Row]) -> list[bool]:
    return [numeric(r["gemini_sensitive"]) <= -1.0 for r in rows]


def basic_effects(rows: Sequence[Row]) -> dict[str, Any]:
    r = validate_rows(rows)
    mask = source_mask(r)
    pos = [i for i, h in enumerate(mask) if h]
    neg = [i for i, h in enumerate(mask) if not h]
    if not pos or not neg:
        raise ValueError("NO_SOURCE_CLASS_CONTRAST")
    y2 = [-float(x["rho_R2"]) for x in r]
    y3 = [-float(x["rho_R3_median"]) for x in r]
    y3low = [-float(x["rho_R3_max"]) for x in r]
    y3high = [-float(x["rho_R3_min"]) for x in r]
    out: dict[str, Any] = {
        "N": len(r), "source_called_N": len(pos), "source_not_called_N": len(neg),
        "A_R2": separation([y2[i] for i in pos], [y2[i] for i in neg]),
        "A_R3_median": separation([y3[i] for i in pos], [y3[i] for i in neg]),
        "A_R3_observed_record_lower": separation([y3low[i] for i in pos], [y3high[i] for i in neg]),
        "A_R3_observed_record_upper": separation([y3high[i] for i in pos], [y3low[i] for i in neg]),
    }
    for name, y in (("R2", y2), ("R3_median", y3)):
        out[f"A_{name}_minus_0_5"] = out[f"A_{name}"] - 0.5
        for group, ids in (("source_called", pos), ("source_not_called", neg)):
            out[f"{name}_{group}_fraction_rho_negative"] = sum(y[i] > 0 for i in ids) / len(ids)
            out[f"{name}_{group}_median_rho"] = median(-y[i] for i in ids)
    out["scope"] = "finite published score set; not an assay-population estimate"
    return out


def specificity(rows: Sequence[Row]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    r = validate_rows(rows)
    mask = source_mask(r)
    q = {name: rank_fraction([-float(x[field]) for x in r]) for name, field in (
        ("DNAPKi", "rho_R2"), ("ATMi", "rho_ATMi_R2"),
        ("ATRi", "rho_ATRi_R2"), ("WEE1i", "rho_WEE1i_R2"),
    )}
    records: list[dict[str, Any]] = []
    for i, row in enumerate(r):
        s = q["DNAPKi"][i] - median(q[k][i] for k in ("ATMi", "ATRi", "WEE1i"))
        item: dict[str, Any] = {"gene": row["gene"], "source_called": mask[i], "S_R2": s}
        for k in q:
            item[f"q_{k}"] = q[k][i]
        for k in ("ATMi", "ATRi", "WEE1i"):
            item[f"q_DNAPKi_minus_{k}"] = q["DNAPKi"][i] - q[k][i]
        records.append(item)
    pos = [x["S_R2"] for x in records if x["source_called"]]
    neg = [x["S_R2"] for x in records if not x["source_called"]]
    if not pos or not neg:
        raise ValueError("NO_SOURCE_CLASS_CONTRAST")
    summary = {
        "median_S_source_called": median(pos), "median_S_source_not_called": median(neg),
        "difference_of_class_medians": median(pos) - median(neg),
        "scope": "relative rank under tested drug/dose conditions; not biochemical selectivity",
    }
    return summary, records


def matched_diagnostic(rows: Sequence[Row], max_controls: int = 5, caliper: float = 0.2
                       ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if max_controls != 5 or caliper != 0.2:
        raise ValueError("parameters are locked at five controls and 0.20 per coordinate")
    r = validate_rows(rows)
    mask = source_mask(r)
    axes = (
        rank_numerators([float(x["source_generic_fragility"]) for x in r]),
        rank_numerators([-float(x["gamma_R2"]) for x in r]),
        rank_numerators([-float(x["gamma_R3_median"]) for x in r]),
    )
    pos = [i for i, h in enumerate(mask) if h]
    neg = [i for i, h in enumerate(mask) if not h]
    if not pos or not neg:
        raise ValueError("NO_SOURCE_CLASS_CONTRAST")
    pairs: list[dict[str, Any]] = []
    case_effects = {"R2": [], "R3": []}
    matched_genes: list[str] = []
    unique_controls: set[str] = set()
    control_uses: dict[str, int] = {}
    control_weights: dict[str, float] = {}
    for i in pos:
        candidates = []
        for j in neg:
            ds = [abs(ax[i] - ax[j]) for ax in axes]
            # q has denominator 2*n: compare to 1/5 and sort distances
            # as integers so an exact boundary or tie is not rounded away.
            if all(d * 5 <= 2 * len(r) for d in ds):
                candidates.append((sum(d*d for d in ds), r[j]["gene"], j, ds))
        chosen = sorted(candidates, key=lambda t: (t[0], t[1]))[:max_controls]
        if not chosen:
            continue
        matched_genes.append(r[i]["gene"])
        for distance, _, j, ds in chosen:
            cg = r[j]["gene"]
            unique_controls.add(cg)
            control_uses[cg] = control_uses.get(cg, 0) + 1
            control_weights[cg] = control_weights.get(cg, 0) + 1 / len(chosen)
            item = {"source_called_gene": r[i]["gene"], "control_gene": cg,
                    "within_case_weight": 1.0/len(chosen),
                    "squared_distance": distance / (2 * len(r))**2,
                    "degree_rank_gap": ds[0] / (2 * len(r)),
                    "gamma_R2_rank_gap": ds[1] / (2 * len(r)),
                    "gamma_R3_rank_gap": ds[2] / (2 * len(r))}
            for key, axis in zip(("degree", "gamma_R2", "gamma_R3"), axes):
                item[f"{key}_q_case"] = axis[i] / (2 * len(r))
                item[f"{key}_q_control"] = axis[j] / (2 * len(r))
                item[f"{key}_rank_signed_difference"] = (axis[i] - axis[j]) / (2 * len(r))
            for key, field in (("R2", "rho_R2"), ("R3", "rho_R3_median")):
                item[f"{key}_tie_credit"] = half_tie_greater(-float(r[i][field]), -float(r[j][field]))
            pairs.append(item)
        for key, field in (("R2", "rho_R2"), ("R3", "rho_R3_median")):
            a = -float(r[i][field])
            case_effects[key].append(math.fsum(half_tie_greater(a, -float(r[j][field]))
                                               for _, _, j, _ in chosen) / len(chosen))
    summary = {
        "source_called_N": len(pos), "matched_source_called_N": len(matched_genes),
        "match_coverage": len(matched_genes)/len(pos), "unique_controls": len(unique_controls),
        "matched_source_called_genes": matched_genes,
        "unmatched_source_called_genes": [r[i]["gene"] for i in pos if r[i]["gene"] not in matched_genes],
        "matched_pair_N": len(pairs),
        "controls_reused_across_cases_N": sum(v > 1 for v in control_uses.values()),
        "control_use_counts": control_uses,
        "control_total_case_weights": control_weights,
        "effective_comparator_N_kish": (math.fsum(control_weights.values())**2 / math.fsum(v*v for v in control_weights.values())) if control_weights else None,
        "A_R2_matched": math.fsum(case_effects["R2"])/len(matched_genes) if matched_genes else None,
        "A_R3_matched": math.fsum(case_effects["R3"])/len(matched_genes) if matched_genes else None,
        "scope": "retrospective diagnostic on the matched subset; no causal or out-of-sample claim",
    }
    for key in ("degree", "gamma_R2", "gamma_R3"):
        summary[f"mean_matched_{key}_rank_signed_difference"] = (math.fsum(
            p["within_case_weight"] * p[f"{key}_rank_signed_difference"] for p in pairs
        ) / len(matched_genes)) if matched_genes else None
    return summary, pairs


def deletion_ranges(rows: Sequence[Row]) -> dict[str, Any]:
    """Exact influence ranges. Never report these as statistical CIs."""
    r = validate_rows(rows)
    full = basic_effects(r)
    entries = []
    for i, row in enumerate(r):
        reduced = r[:i] + r[i+1:]
        try:
            e = basic_effects(reduced)
        except ValueError as exc:
            if str(exc) != "NO_SOURCE_CLASS_CONTRAST":
                raise
            entries.append({"deleted_gene": row["gene"], "source_called": float(row["gemini_sensitive"]) <= -1,
                            "status": "NO_SOURCE_CLASS_CONTRAST"})
            continue
        item = {"deleted_gene": row["gene"], "source_called": float(row["gemini_sensitive"]) <= -1,
                "status": "computed", **e}
        for key in ("A_R2", "A_R3_median"):
            item[f"delta_{key}"] = e[key] - full[key]
            item[f"absolute_delta_{key}"] = abs(e[key] - full[key])
        entries.append(item)
    out: dict[str, Any] = {"full": full, "deletions": entries,
                           "scope": "finite-set influence; NOT confidence intervals or standard errors"}
    for kind in ("all_genes", "source_called_only"):
        subset = [x for x in entries if x["status"] == "computed" and
                  (kind == "all_genes" or x["source_called"])]
        out[kind] = {key: [min(x[key] for x in subset), max(x[key] for x in subset)] if subset else None
                     for key in ("A_R2", "A_R3_median")}
    out["influence_order"] = {key: [x["deleted_gene"] for x in sorted(
        (x for x in entries if x["status"] == "computed"),
        key=lambda x: (-x[f"absolute_delta_{key}"], x["deleted_gene"]))]
        for key in ("A_R2", "A_R3_median")}
    return out
