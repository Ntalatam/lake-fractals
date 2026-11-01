"""Post-hoc validation, not pre-registered: the primary analysis at a finer point spacing.

The planned analysis places boundary points at most 1/10 of the smallest box
apart (DENSIFY_FRACTION in src/boxcount.py). This rerun places them at most
1/100 apart (densify_fraction 0.01), on the same 3,274 primary lakes and in
the same three windows, and repeats the planned statistics with the planned
settings (planned_statistics, the statistics code of src/primary_analysis.py
main()): spearman rho with percentile bootstrap intervals (2,000 resamples,
seed 0), the decision rule exactly as in CLAUDE.md, kruskal-wallis and group
medians in the primary window, the within-source check and the sensitivity
analysis without pilot lakes. It also counts estimates below 1 per window and
puts each planned result beside the rerun's (comparison_*.csv). The planned
results are not replaced.

Stop rule for this run (author's): stop only if the whole run passes 3 hours.
The planned 60 s per-lake limit is not applied, since 10 times as many points
make the longest shorelines take several minutes each. The 3-hour limit is
checked when a lake finishes, and lakes already running finish before the
run stops.

Writes to results/validation/spacing_0p01/, with the file names and columns
of results/primary/ where a file has a planned counterpart. results/primary/
is only read.

Run from the project root: .venv/bin/python src/validation_spacing.py
"""

import math
import signal
import sys
import time

import geopandas as gpd
import numpy as np
import pandas as pd

from boxcount import DEFAULT_N_OFFSETS, DEFAULT_SEED, DENSIFY_FRACTION
from primary_analysis import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    CI_LEVEL,
    EXPECTED_PRIMARY_N,
    LAKES,
    MEASURES,
    MIN_R_SQUARED,
    PILOT,
    PRIMARY_MIN_ACRES,
    PRIMARY_WINDOW,
    ROOT,
    WINDOWS,
    WITHIN_SOURCE_GROUP,
    compute_dimensions,
    decision_rule,
    rho_table,
    source_comparison,
    source_group,
)
from primary_analysis import OUT_DIR as PRIMARY_DIR
from validation import below_one

OUT_DIR = ROOT / "results" / "validation" / "spacing_0p01"

# author's settings for this rerun: points at most 1/100 of the smallest box
# apart, 4 worker processes, and stop only if the whole run passes 3 hours
DENSIFY_FRACTION_USED = 0.01
WORKERS = 4
MAX_WALL_SECONDS = 3 * 60 * 60

RUN_LABEL = "primary, densify_fraction 0.01"


class RunTooLong(RuntimeError):
    pass


def planned_statistics(dims, n_resamples=BOOTSTRAP_RESAMPLES):
    """The statistics of src/primary_analysis.py main(), computed from a dims table.

    Returns {file name: table}, with the planned file names and columns.
    """
    rho = rho_table(dims, sample="primary", n_resamples=n_resamples)
    rules = []
    for measure in MEASURES:
        by_window = rho[rho["measure"] == measure].set_index("window")["rho"]
        rules.append(
            {"measure": measure, **{f"rho_{w}": by_window[w] for w in WINDOWS}, **decision_rule(by_window.to_dict())}
        )
    r2 = pd.DataFrame(
        [
            {
                "window": window,
                "window_min_m": sizes[0],
                "window_max_m": sizes[-1],
                "n_lakes": len(dims),
                "n_r2_below": int((dims[f"r2_{window}"] < MIN_R_SQUARED).sum()),
                "min_r2": dims[f"r2_{window}"].min(),
            }
            for window, sizes in WINDOWS.items()
        ]
    )
    groups, test = source_comparison(dims, PRIMARY_WINDOW)
    within = dims[dims["source_group"] == WITHIN_SOURCE_GROUP]
    no_pilot = dims[~dims["in_pilot"]]
    samples = pd.DataFrame(
        [
            {"sample": "primary", "n": len(dims)},
            {"sample": "primary, delineat_1 missing (excluded from source comparison)", "n": test["n_excluded_missing"]},
            {"sample": "source comparison", "n": test["n_lakes"]},
            {"sample": "pilot lakes in primary (excluded in sensitivity)", "n": int(dims["in_pilot"].sum())},
            {"sample": "primary without pilot lakes", "n": len(no_pilot)},
            {"sample": f"{WITHIN_SOURCE_GROUP} only (within-source check)", "n": len(within)},
        ]
    )
    return {
        "rho_primary.csv": rho,
        "decision_rule.csv": pd.DataFrame(rules),
        "r2_below_threshold.csv": r2,
        "source_groups.csv": groups,
        "kruskal_wallis.csv": pd.DataFrame([test]),
        "rho_within_2004_fsa.csv": rho_table(within, sample=f"{WITHIN_SOURCE_GROUP} only", n_resamples=n_resamples),
        "rho_sensitivity_no_pilot.csv": rho_table(
            no_pilot, sample="primary without pilot lakes", n_resamples=n_resamples
        ),
        "sample_log.csv": samples,
    }


def side_by_side(planned, rerun, keys, values):
    """Planned and rerun values next to each other, matched on keys."""
    both = planned.merge(rerun, on=keys, suffixes=("_planned", "_rerun"), validate="one_to_one")
    if len(both) != len(planned) or len(both) != len(rerun):
        raise ValueError("planned and rerun tables do not have the same rows")
    return both[keys + [f"{value}_{side}" for value in values for side in ("planned", "rerun")]].copy()


def compare_rho(planned, rerun):
    """Planned and rerun rho: the change, the sign, and whether each interval excludes zero."""
    table = side_by_side(planned, rerun, ["sample", "window", "measure", "n"], ["rho", "ci_low", "ci_high"])
    table["rho_change"] = table["rho_rerun"] - table["rho_planned"]
    table["same_sign"] = np.sign(table["rho_planned"]) == np.sign(table["rho_rerun"])
    for side in ("planned", "rerun"):
        table[f"ci_excludes_zero_{side}"] = (table[f"ci_low_{side}"] > 0) | (table[f"ci_high_{side}"] < 0)
    table["same_ci_status"] = table["ci_excludes_zero_planned"] == table["ci_excludes_zero_rerun"]
    return table


def compare_decision_rule(planned, rerun):
    """Planned and rerun outcome of the decision rule, per measure."""
    table = side_by_side(planned, rerun, ["measure"], ["direction", "outcome"])
    table["same_outcome"] = table["outcome_planned"] == table["outcome_rerun"]
    return table


def compare_kruskal_wallis(planned, rerun):
    return side_by_side(planned, rerun, ["window", "n_groups", "n_lakes", "n_excluded_missing"], ["H", "p_value"])


def compare_source_groups(planned, rerun):
    return side_by_side(planned, rerun, ["window", "group", "n"], ["median_dim"])


def over_time(signum, frame):
    raise RunTooLong(f"the whole run passed {MAX_WALL_SECONDS / 3600:g} hours")


def main():
    lakes = gpd.read_file(LAKES)
    primary = lakes[lakes["acres"] >= PRIMARY_MIN_ACRES].reset_index(drop=True)
    if len(primary) != EXPECTED_PRIMARY_N:
        sys.exit(f"stopped: primary sample has {len(primary):,} lakes, expected {EXPECTED_PRIMARY_N:,}")
    planned_dims = pd.read_csv(PRIMARY_DIR / "dims.csv")
    pilot_ids = set(pd.read_csv(PILOT)["objectid"])
    lake_columns = pd.DataFrame(
        {
            "objectid": primary["objectid"],
            "acres": primary["acres"],
            "shoreline_m": primary["shoreline_m"],
            "source_group": source_group(primary["delineat_1"]),
            "in_pilot": primary["objectid"].isin(pilot_ids),
        }
    )
    # the same lakes, in the same order and with the same attributes, as the planned run
    try:
        pd.testing.assert_frame_equal(lake_columns, planned_dims[lake_columns.columns], check_dtype=False)
    except AssertionError as error:
        sys.exit(f"stopped: lakes differ from results/primary/dims.csv: {error}")

    print(
        f"computing dimensions for {len(primary):,} lakes with {WORKERS} workers, "
        f"densify_fraction {DENSIFY_FRACTION_USED}",
        flush=True,
    )
    signal.signal(signal.SIGALRM, over_time)
    signal.alarm(MAX_WALL_SECONDS)
    wall_start = time.perf_counter()
    try:
        computed = compute_dimensions(
            primary,
            WINDOWS,
            workers=WORKERS,
            max_seconds=math.inf,
            progress_every=250,
            densify_fraction=DENSIFY_FRACTION_USED,
        )
    except RunTooLong as error:
        sys.exit(f"stopped: {error}")
    finally:
        signal.alarm(0)
    wall_s = time.perf_counter() - wall_start

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dims = lake_columns.merge(computed, on="objectid", validate="one_to_one")
    dims.to_csv(OUT_DIR / "dims.csv", index=False)
    slowest = dims.loc[dims["runtime_s"].idxmax()]
    pd.DataFrame(
        [
            {
                "run": RUN_LABEL,
                "n_lakes": len(dims),
                "workers": WORKERS,
                "median_s": dims["runtime_s"].median(),
                "max_s": slowest["runtime_s"],
                "slowest_objectid": slowest["objectid"],
                "slowest_shoreline_m": slowest["shoreline_m"],
                "wall_s": wall_s,
            }
        ]
    ).to_csv(OUT_DIR / "runtime.csv", index=False)

    tables = planned_statistics(dims)
    for name, table in tables.items():
        table.to_csv(OUT_DIR / name, index=False)
    below_one(dims).to_csv(OUT_DIR / "below_one.csv", index=False)

    pd.DataFrame(
        [
            ("primary_min_acres", PRIMARY_MIN_ACRES),
            ("box_sizes_per_window", len(WINDOWS[PRIMARY_WINDOW])),
            ("grid_offsets", DEFAULT_N_OFFSETS),
            ("grid_seed", DEFAULT_SEED),
            ("densify_fraction", DENSIFY_FRACTION_USED),
            ("planned_densify_fraction", DENSIFY_FRACTION),
            *[(f"point_spacing_m_{w}", sizes[0] * DENSIFY_FRACTION_USED) for w, sizes in WINDOWS.items()],
            ("bootstrap_resamples", BOOTSTRAP_RESAMPLES),
            ("bootstrap_seed", BOOTSTRAP_SEED),
            ("ci_level_percent", CI_LEVEL * 100),
            ("r2_threshold", MIN_R_SQUARED),
            ("workers", WORKERS),
            ("max_wall_seconds", MAX_WALL_SECONDS),
            ("max_seconds_per_lake", math.inf),
        ],
        columns=["parameter", "value"],
    ).to_csv(OUT_DIR / "parameters.csv", index=False)

    def planned(name):
        return pd.read_csv(PRIMARY_DIR / name)

    pd.concat(
        [
            compare_rho(planned(name), tables[name])
            for name in ["rho_primary.csv", "rho_within_2004_fsa.csv", "rho_sensitivity_no_pilot.csv"]
        ]
    ).to_csv(OUT_DIR / "comparison_rho.csv", index=False)
    compare_decision_rule(planned("decision_rule.csv"), tables["decision_rule.csv"]).to_csv(
        OUT_DIR / "comparison_decision_rule.csv", index=False
    )
    compare_kruskal_wallis(planned("kruskal_wallis.csv"), tables["kruskal_wallis.csv"]).to_csv(
        OUT_DIR / "comparison_kruskal_wallis.csv", index=False
    )
    compare_source_groups(planned("source_groups.csv"), tables["source_groups.csv"]).to_csv(
        OUT_DIR / "comparison_source_groups.csv", index=False
    )
    side_by_side(
        below_one(planned_dims), below_one(dims), ["window", "window_min_m", "window_max_m", "n_lakes"],
        ["n_below_1", "share_below_1", "percent_below_1", "min_below_1"],
    ).to_csv(OUT_DIR / "comparison_below_one.csv", index=False)
    print(f"wrote results to {OUT_DIR.relative_to(ROOT)} in {wall_s:.0f} s")


if __name__ == "__main__":
    main()
