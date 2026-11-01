"""Post-hoc check, not in the analysis plan: width-based exclusion.

The narrow-shore share in src/validation_width.py tracks the lake estimate
(results/validation/width_rho.csv), so dropping lakes on it selects them on a
near-proxy of the outcome. This check drops lakes by their widest point
instead: the diameter of the largest circle inside the lake
(inscribed_diameter_m in results/validation/width.csv, not recomputed here).

Set by the author on 2026-11-01, after the narrow-shore results and before
this check's results: drop lakes narrower than 400 m at their widest point,
twice the largest box of the 20-200 m window, and drop the same lakes in all
three windows. The six primary rhos are recomputed on the kept lakes with the
planned percentile bootstrap (2,000 resamples, seed 0) and the planned
decision rule is applied. Over all primary lakes, spearman rho between the
inscribed diameter and the estimate is reported in each window.

Every analysis that uses lake estimates is run on both sets of estimates
(DIMS_VERSIONS in src/validation.py).

Writes to results/validation/: width_exclusion_*.csv. width.csv and
results/primary/ are only read.

Run from the project root: .venv/bin/python src/validation_width_exclusion.py
"""

import sys

import numpy as np
import pandas as pd

from primary_analysis import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    CI_LEVEL,
    EXPECTED_PRIMARY_N,
    MEASURES,
    ROOT,
    WINDOWS,
    decision_rule,
    spearman_with_ci,
)
from validation import OUT_DIR, read_dims_versions
from validation_width import DECISION_DIRS, INSCRIBED_TOLERANCE_M

# author's cutoff (2026-11-01, set before this check's results): twice the
# largest box of the 20-200 m window. a lake narrower than this at its widest
# point is dropped from every window
MIN_INSCRIBED_DIAMETER_M = 2 * WINDOWS["20_200"][-1]

# a computed inscribed diameter is short of the true one by at most twice the
# radius tolerance, so excluded lakes this close below the cutoff could be at
# or above it. counted only; the cutoff is applied to the computed diameter
DIAMETER_TOLERANCE_M = 2 * INSCRIBED_TOLERANCE_M


def with_diameter(dims, width):
    """dims with each lake's inscribed diameter; raises unless every lake has a finite one."""
    both = dims.merge(width[["objectid", "inscribed_diameter_m"]], on="objectid", validate="one_to_one")
    if len(both) != len(dims):
        raise ValueError(f"width holds {len(both):,} of the {len(dims):,} lakes")
    if not np.isfinite(both["inscribed_diameter_m"].to_numpy(dtype=float)).all():
        raise ValueError("an inscribed diameter is missing or not finite")
    return both


def width_exclusion(dims, width, min_diameter=MIN_INSCRIBED_DIAMETER_M, n_resamples=BOOTSTRAP_RESAMPLES):
    """The six primary rhos without lakes narrower than min_diameter, and the planned decision rule.

    The same lakes are dropped in every window.
    """
    both = with_diameter(dims, width)
    keep = both["inscribed_diameter_m"] >= min_diameter
    kept = both[keep]
    rows = []
    for window, sizes in WINDOWS.items():
        for measure, column in MEASURES.items():
            rows.append(
                {
                    "window": window,
                    "window_min_m": sizes[0],
                    "window_max_m": sizes[-1],
                    "measure": measure,
                    "min_inscribed_diameter_m": min_diameter,
                    "n_excluded": int((~keep).sum()),
                    **spearman_with_ci(kept[f"dim_{window}"], kept[column], n_resamples),
                }
            )
    rho = pd.DataFrame(rows)
    rules = []
    for measure in MEASURES:
        by_window = rho[rho["measure"] == measure].set_index("window")["rho"]
        rules.append({"measure": measure, **{f"rho_{w}": by_window[w] for w in WINDOWS}, **decision_rule(by_window.to_dict())})
    return rho, pd.DataFrame(rules)


def diameter_rho(dims, width, n_resamples=BOOTSTRAP_RESAMPLES):
    """Spearman rho of the inscribed diameter against the estimate in each window, over all lakes."""
    both = with_diameter(dims, width)
    return pd.DataFrame(
        [
            {
                "window": window,
                "window_min_m": sizes[0],
                "window_max_m": sizes[-1],
                **spearman_with_ci(both["inscribed_diameter_m"], both[f"dim_{window}"], n_resamples),
            }
            for window, sizes in WINDOWS.items()
        ]
    )


def exclusion_counts(width, min_diameter=MIN_INSCRIBED_DIAMETER_M):
    diameter = width["inscribed_diameter_m"]
    excluded = diameter < min_diameter
    return pd.DataFrame(
        [
            {
                "min_inscribed_diameter_m": min_diameter,
                "n_lakes": len(width),
                "n_excluded": int(excluded.sum()),
                "n_kept": int((~excluded).sum()),
                "percent_excluded": 100 * excluded.mean(),
                "diameter_tolerance_m": DIAMETER_TOLERANCE_M,
                "n_excluded_within_tolerance": int((excluded & (diameter >= min_diameter - DIAMETER_TOLERANCE_M)).sum()),
            }
        ]
    )


def main():
    width = pd.read_csv(OUT_DIR / "width.csv")
    versions = read_dims_versions()
    if len(width) != EXPECTED_PRIMARY_N or width["objectid"].tolist() != versions["planned"]["objectid"].tolist():
        sys.exit("stopped: width.csv does not hold the primary lakes in order")

    exclusion_counts(width).to_csv(OUT_DIR / "width_exclusion_counts.csv", index=False)
    rho_rows, rule_rows, diameter_rows = [], [], []
    for version, dims in versions.items():
        rho, rules = width_exclusion(dims, width)
        rho_rows.append(rho.assign(dims=version))
        planned_rule = pd.read_csv(DECISION_DIRS[version] / "decision_rule.csv").set_index("measure")
        rules["outcome_all_lakes"] = rules["measure"].map(planned_rule["outcome"])
        rule_rows.append(rules.assign(dims=version))
        diameter_rows.append(diameter_rho(dims, width).assign(dims=version))
        print(f"done: {version}", flush=True)
    for name, rows in [("rho", rho_rows), ("decision_rule", rule_rows), ("diameter_rho", diameter_rows)]:
        table = pd.concat(rows)
        table[["dims", *[c for c in table.columns if c != "dims"]]].to_csv(
            OUT_DIR / f"width_exclusion_{name}.csv", index=False
        )
    pd.DataFrame(
        [
            ("min_inscribed_diameter_m", MIN_INSCRIBED_DIAMETER_M),
            ("inscribed_tolerance_m", INSCRIBED_TOLERANCE_M),
            ("bootstrap_resamples", BOOTSTRAP_RESAMPLES),
            ("bootstrap_seed", BOOTSTRAP_SEED),
            ("ci_level_percent", 100 * CI_LEVEL),
        ],
        columns=["parameter", "value"],
    ).to_csv(OUT_DIR / "width_exclusion_parameters.csv", index=False)
    print(f"wrote width exclusion results to {OUT_DIR.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
