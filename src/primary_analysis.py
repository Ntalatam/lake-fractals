"""Primary (confirmatory) analysis, following the pre-registered design in CLAUDE.md.

Computes the box-counting dimension of every primary-sample lake in the three
pre-registered windows, then writes to results/primary/:
- dims.csv: one row per lake
- rho_primary.csv: spearman rho of dimension vs area and vs shoreline length,
  per window, with p-value and bootstrap confidence interval
- decision_rule.csv: the pre-registered rule, separately for area and length
- r2_below_threshold.csv: lakes with r squared below the threshold, per window
- source_groups.csv, kruskal_wallis.csv: the mapping source comparison
- rho_within_2004_fsa.csv: the within-source check
- rho_sensitivity_no_pilot.csv: the sensitivity analysis without pilot lakes
- sample_log.csv, parameters.csv, runtime.csv

Stops if a lake errors or takes longer than 60 seconds.

Run from the project root: .venv/bin/python src/primary_analysis.py
With --reuse-dims, the statistics are recomputed from an existing dims.csv.
"""

import argparse
import os
import subprocess
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import kruskal, spearmanr

from boxcount import DEFAULT_N_OFFSETS, DEFAULT_SEED, DENSIFY_FRACTION, box_count_dimension

ROOT = Path(__file__).resolve().parent.parent
LAKES = ROOT / "data" / "processed" / "lakes_filtered.gpkg"
PILOT = ROOT / "results" / "pilot" / "pilot_dims.csv"
OUT_DIR = ROOT / "results" / "primary"

# pre-registered primary sample (CLAUDE.md): acres >= 100. the other filters
# (Lake or Pond, shoreline >= 1,000 m, non-null geometry, outside_mn not Y/B)
# are already applied in lakes_filtered.gpkg.
PRIMARY_MIN_ACRES = 100
EXPECTED_PRIMARY_N = 3274

# pre-registered windows (CLAUDE.md), 8 log-spaced box sizes each, keyed
# "<smallest>_<largest>" in meters. 20-100 m is the primary window; the other
# two are sensitivity windows on the same lakes. every window uses the 8 grid
# offsets from seed 0 in boxcount.py and reports the median dimension.
WINDOWS = {
    "20_100": np.geomspace(20.0, 100.0, 8),
    "10_100": np.geomspace(10.0, 100.0, 8),
    "20_200": np.geomspace(20.0, 200.0, 8),
}
PRIMARY_WINDOW = "20_100"

# size measures for the spearman correlations (pre-registered): area is the
# DNR acres attribute, shoreline length is shoreline_m from src/filter_lakes.py
MEASURES = {"area": "acres", "shoreline": "shoreline_m"}

# mapping source groups (pre-registered, set on the 10-acre sample and kept
# unchanged): these four stand alone and every other value goes to "other".
# a missing value stays missing, and is excluded from the source comparison
# only.
STANDALONE_SOURCES = ["2004 FSA", "ORIG DLG", "DNR 24k POLYS", "PWI"]
OTHER = "other"

# within-source check (pre-registered): spearman rho within this group only
WITHIN_SOURCE_GROUP = "2004 FSA"

# bootstrap confidence interval for every spearman rho (pre-registered): 95%,
# 2,000 resamples, seed 0. lakes are resampled with replacement and the
# interval is the 2.5th to 97.5th percentile of the resampled rhos (the
# percentile method, the simplest bootstrap interval to state and check).
CI_LEVEL = 0.95
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 0

# author's reporting threshold for fit quality
MIN_R_SQUARED = 0.98

# author's stop rule: stop if one lake takes longer than this, all windows together
MAX_SECONDS_PER_LAKE = 60


class LakeTooSlow(RuntimeError):
    pass


def source_group(delineat_1):
    """Pre-registered mapping source group for each delineat_1 value."""
    groups = delineat_1.where(delineat_1.isin(STANDALONE_SOURCES), OTHER)
    return groups.where(delineat_1.notna())


def spearman_with_ci(x, y, n_resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED, level=CI_LEVEL):
    """Spearman rho, its p-value, and a percentile bootstrap confidence interval.

    The generator is re-seeded on every call, so every rho computed on the same
    lakes is resampled with the same lakes.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    rho, p_value = spearmanr(x, y)
    rng = np.random.default_rng(seed)
    resampled = np.empty(n_resamples)
    with warnings.catch_warnings():
        # in tiny inputs a resample can be constant; its rho is nan and skipped
        warnings.simplefilter("ignore")
        for i in range(n_resamples):
            index = rng.integers(0, len(x), len(x))
            resampled[i] = spearmanr(x[index], y[index]).statistic
    tail = (1 - level) / 2 * 100
    low, high = np.nanpercentile(resampled, [tail, 100 - tail])
    return {"n": len(x), "rho": float(rho), "p_value": float(p_value), "ci_low": float(low), "ci_high": float(high)}


def rho_table(dims, sample, windows=WINDOWS, n_resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    """Spearman rho of dimension vs each size measure, one row per window and measure."""
    rows = []
    for window, sizes in windows.items():
        for measure, column in MEASURES.items():
            rows.append(
                {
                    "sample": sample,
                    "window": window,
                    "window_min_m": sizes[0],
                    "window_max_m": sizes[-1],
                    "measure": measure,
                    **spearman_with_ci(dims[f"dim_{window}"], dims[column], n_resamples, seed),
                }
            )
    return pd.DataFrame(rows)


def decision_rule(rho_by_window):
    """Pre-registered rule: supported only if rho has the same sign in all three windows."""
    if set(rho_by_window) != set(WINDOWS):
        raise ValueError(f"need rho for windows {list(WINDOWS)}, got {list(rho_by_window)}")
    rhos = np.array(list(rho_by_window.values()))
    if (rhos < 0).all():
        direction = "negative"
    elif (rhos > 0).all():
        direction = "positive"
    else:
        direction = "mixed"
    holds = direction != "mixed"
    return {"direction_holds": holds, "direction": direction, "outcome": "supported" if holds else "window-dependent"}


def source_comparison(dims, window=PRIMARY_WINDOW):
    """Kruskal-wallis of dimension across source groups, missing sources excluded."""
    known = dims[dims["source_group"].notna()]
    present = set(known["source_group"])
    order = [group for group in STANDALONE_SOURCES + [OTHER] if group in present]
    samples = [known.loc[known["source_group"] == group, f"dim_{window}"] for group in order]
    statistic, p_value = kruskal(*samples)
    groups = pd.DataFrame(
        {
            "window": window,
            "group": order,
            "n": [len(s) for s in samples],
            "median_dim": [s.median() for s in samples],
        }
    )
    test = {
        "window": window,
        "n_groups": len(order),
        "n_lakes": len(known),
        "n_excluded_missing": int(dims["source_group"].isna().sum()),
        "H": float(statistic),
        "p_value": float(p_value),
    }
    return groups, test


def lake_dimensions(geometry, windows=WINDOWS, densify_fraction=DENSIFY_FRACTION):
    """Dimension and r squared of one lake in each window, plus the runtime.

    densify_fraction is the planned 0.1 unless a post-hoc check sets it.
    """
    start = time.perf_counter()
    row = {}
    for name, sizes in windows.items():
        result = box_count_dimension(geometry, sizes, DEFAULT_N_OFFSETS, DEFAULT_SEED, densify_fraction)
        row[f"dim_{name}"] = result.dimension
        row[f"r2_{name}"] = result.r_squared
    row["runtime_s"] = time.perf_counter() - start
    return row


def default_workers():
    """Performance cores on Apple silicon, otherwise all cores.

    Leaving out the slower efficiency cores keeps each lake's runtime close to
    what it would be on its own, so the 60 s stop rule measures the lake, not
    the scheduler.
    """
    try:
        out = subprocess.run(
            ["sysctl", "-n", "hw.perflevel0.physicalcpu"], capture_output=True, text=True, check=True
        )
        return int(out.stdout)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return os.cpu_count() or 1


def compute_dimensions(
    lakes,
    windows=WINDOWS,
    workers=1,
    max_seconds=MAX_SECONDS_PER_LAKE,
    progress_every=0,
    densify_fraction=DENSIFY_FRACTION,
):
    """lake_dimensions for every lake, one row per lake in input order.

    Raises LakeTooSlow as soon as a finished lake took longer than max_seconds,
    and lets any error from a lake propagate. Both stop the run.
    """
    geometries = list(lakes.geometry)
    objectids = lakes["objectid"].to_numpy()
    rows = [None] * len(geometries)
    done = 0
    start = time.perf_counter()

    def record(i, row):
        nonlocal done
        rows[i] = row
        done += 1
        if row["runtime_s"] > max_seconds:
            raise LakeTooSlow(
                f"lake objectid {objectids[i]} took {row['runtime_s']:.1f} s (limit {max_seconds} s)"
            )
        if progress_every and done % progress_every == 0:
            print(f"{done:,}/{len(rows):,} lakes, {time.perf_counter() - start:.0f} s", flush=True)

    if workers == 1:
        for i, geometry in enumerate(geometries):
            record(i, lake_dimensions(geometry, windows, densify_fraction))
    else:
        # longest shorelines first, so the slowest lakes do not finish last
        order = np.argsort(-lakes.geometry.length.to_numpy(), kind="stable")
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(lake_dimensions, geometries[i], windows, densify_fraction): i for i in order}
            try:
                for future in as_completed(futures):
                    record(futures[future], future.result())
            except BaseException:
                for future in futures:
                    future.cancel()
                raise
    return pd.DataFrame({"objectid": objectids}).join(pd.DataFrame(rows))


def main():
    parser = argparse.ArgumentParser(description="primary analysis (pre-registered design)")
    parser.add_argument("--reuse-dims", action="store_true", help="read results/primary/dims.csv instead of recomputing")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    lakes = gpd.read_file(LAKES)
    primary = lakes[lakes["acres"] >= PRIMARY_MIN_ACRES].reset_index(drop=True)
    if len(primary) != EXPECTED_PRIMARY_N:
        sys.exit(f"stopped: primary sample has {len(primary):,} lakes, expected {EXPECTED_PRIMARY_N:,}")
    pilot_ids = set(pd.read_csv(PILOT)["objectid"])

    if args.reuse_dims:
        dims = pd.read_csv(OUT_DIR / "dims.csv")
        if sorted(dims["objectid"]) != sorted(primary["objectid"]):
            sys.exit("stopped: dims.csv does not hold the primary sample")
    else:
        workers = default_workers()
        print(f"computing dimensions for {len(primary):,} lakes with {workers} workers", flush=True)
        wall_start = time.perf_counter()
        try:
            computed = compute_dimensions(primary, WINDOWS, workers=workers, progress_every=250)
        except LakeTooSlow as error:
            sys.exit(f"stopped: {error}")
        wall_s = time.perf_counter() - wall_start
        dims = pd.DataFrame(
            {
                "objectid": primary["objectid"],
                "acres": primary["acres"],
                "shoreline_m": primary["shoreline_m"],
                "source_group": source_group(primary["delineat_1"]),
                "in_pilot": primary["objectid"].isin(pilot_ids),
            }
        ).merge(computed, on="objectid", validate="one_to_one")
        dims.to_csv(OUT_DIR / "dims.csv", index=False)
        slowest = dims.loc[dims["runtime_s"].idxmax()]
        pd.DataFrame(
            [
                {
                    "run": "primary",
                    "n_lakes": len(dims),
                    "workers": workers,
                    "median_s": dims["runtime_s"].median(),
                    "max_s": slowest["runtime_s"],
                    "slowest_objectid": slowest["objectid"],
                    "slowest_shoreline_m": slowest["shoreline_m"],
                    "wall_s": wall_s,
                }
            ]
        ).to_csv(OUT_DIR / "runtime.csv", index=False)

    # spearman rho per window and measure, and the decision rule (confirmatory)
    rho = rho_table(dims, sample="primary")
    rho.to_csv(OUT_DIR / "rho_primary.csv", index=False)
    rules = []
    for measure in MEASURES:
        by_window = rho[rho["measure"] == measure].set_index("window")["rho"]
        rules.append(
            {"measure": measure, **{f"rho_{w}": by_window[w] for w in WINDOWS}, **decision_rule(by_window.to_dict())}
        )
    pd.DataFrame(rules).to_csv(OUT_DIR / "decision_rule.csv", index=False)

    pd.DataFrame(
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
    ).to_csv(OUT_DIR / "r2_below_threshold.csv", index=False)

    # mapping source comparison, primary window, missing sources excluded
    groups, test = source_comparison(dims, PRIMARY_WINDOW)
    groups.to_csv(OUT_DIR / "source_groups.csv", index=False)
    pd.DataFrame([test]).to_csv(OUT_DIR / "kruskal_wallis.csv", index=False)

    # within-source check and the sensitivity analysis without pilot lakes
    within = dims[dims["source_group"] == WITHIN_SOURCE_GROUP]
    rho_table(within, sample=f"{WITHIN_SOURCE_GROUP} only").to_csv(OUT_DIR / "rho_within_2004_fsa.csv", index=False)
    no_pilot = dims[~dims["in_pilot"]]
    rho_table(no_pilot, sample="primary without pilot lakes").to_csv(
        OUT_DIR / "rho_sensitivity_no_pilot.csv", index=False
    )

    pd.DataFrame(
        [
            {"sample": "primary", "n": len(dims)},
            {"sample": "primary, delineat_1 missing (excluded from source comparison)", "n": test["n_excluded_missing"]},
            {"sample": "source comparison", "n": test["n_lakes"]},
            {"sample": "pilot lakes in primary (excluded in sensitivity)", "n": int(dims["in_pilot"].sum())},
            {"sample": "primary without pilot lakes", "n": len(no_pilot)},
            {"sample": f"{WITHIN_SOURCE_GROUP} only (within-source check)", "n": len(within)},
        ]
    ).to_csv(OUT_DIR / "sample_log.csv", index=False)

    pd.DataFrame(
        [
            ("primary_min_acres", PRIMARY_MIN_ACRES),
            ("box_sizes_per_window", len(WINDOWS[PRIMARY_WINDOW])),
            ("grid_offsets", DEFAULT_N_OFFSETS),
            ("grid_seed", DEFAULT_SEED),
            ("bootstrap_resamples", BOOTSTRAP_RESAMPLES),
            ("bootstrap_seed", BOOTSTRAP_SEED),
            ("ci_level_percent", CI_LEVEL * 100),
            ("r2_threshold", MIN_R_SQUARED),
            ("max_seconds_per_lake", MAX_SECONDS_PER_LAKE),
        ],
        columns=["parameter", "value"],
    ).to_csv(OUT_DIR / "parameters.csv", index=False)
    print(f"wrote results to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
