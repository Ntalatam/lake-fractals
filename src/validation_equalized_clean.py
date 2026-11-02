"""Post-hoc check, not in the analysis plan: equalized resampling on lakes it left whole.

The equalized resampling in src/validation_vertices.py rebuilds every ring with
vertices every 25 m and every 50 m. Besides the vertex spacing, it changed the
geometry: it dropped rings too short to keep 4 vertices and left some lakes
invalid (results/validation/equalized_rings.csv). This check flags, for each
primary lake, whether the resampling at 25 m and at 50 m dropped any ring and
whether the result is a valid polygon. The clean subset is the lakes with no
dropped ring and a valid polygon at both intervals.

On the clean subset and on all lakes, for both point spacings (densify
fraction 0.1, planned, and 0.01), with the vertices as digitized and rebuilt
every 25 m and every 50 m (all author's):
- the median estimate of each source group
- the gaps 2004 FSA minus ORIG DLG and 2004 FSA minus DNR 24k POLYS, with
  percentile bootstrap intervals: 2,000 resamples, seed 0, lakes resampled
  within each group
- the spread, the largest group median minus the smallest
- the kruskal-wallis H, reported as a test statistic only; it is not a share
  of the differences explained
Lakes with no delineat_1 are left out of all of these, as in the planned
source comparison.

The estimates are the existing ones: results/primary/dims.csv and
results/validation/spacing_0p01/dims.csv as digitized, and
results/validation/equalized_dims.csv rebuilt. Only the rebuilt geometries are
recomputed, for the flags, and they are checked against equalized_rings.csv.

Writes to results/validation/: equalized_flags.csv and equalized_clean_*.csv.
results/primary/ and the existing equalized files are only read.

Run from the project root: .venv/bin/python src/validation_equalized_clean.py
"""

import sys

import geopandas as gpd
import numpy as np
import pandas as pd

from primary_analysis import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    CI_LEVEL,
    EXPECTED_PRIMARY_N,
    LAKES,
    PRIMARY_MIN_ACRES,
    PRIMARY_WINDOW,
    ROOT,
    source_comparison,
)
from validation import OUT_DIR, read_dims_versions
from validation_vertices import (
    ALL_LAKES,
    EQUALIZED_FRACTIONS,
    GROUP_ORDER,
    INTERVALS_M,
    MIN_RING_VERTICES,
    VERSION_OF_FRACTION,
    label,
    resample_lake,
)

# author's gaps: the largest group against the two map-based groups
GAPS = [("2004 FSA", "ORIG DLG"), ("2004 FSA", "DNR 24k POLYS")]

# author's interval settings, the planned ones: 2,000 resamples, seed 0. the
# generator is re-seeded for each gap and draws the resampled lakes of the
# first group, then of the second, so every gap of one subset is computed on
# the same resampled lakes whatever the estimates
GAP_RESAMPLES = BOOTSTRAP_RESAMPLES
GAP_SEED = BOOTSTRAP_SEED

MISSING = "no delineat_1"
SUBSETS = ["clean", ALL_LAKES]


def lake_flags(geometry):
    """Rings, dropped rings and validity of one lake rebuilt at each interval."""
    row = {}
    for interval in INTERVALS_M:
        _, log = resample_lake(geometry, interval)
        row["n_rings"] = log["n_rings"]
        row[f"rings_dropped_{interval:g}m"] = log["n_rings_dropped"]
        row[f"valid_{interval:g}m"] = log["is_valid"]
    return row


def clean_lakes(flags):
    """Lakes with no dropped ring and a valid polygon at every interval."""
    clean = pd.Series(True, index=flags.index)
    for interval in INTERVALS_M:
        clean &= (flags[f"rings_dropped_{interval:g}m"] == 0) & flags[f"valid_{interval:g}m"]
    return clean


def counts_by_group(flags):
    """Lakes, clean lakes and the rest, per source group, for lakes with no source and for all lakes."""
    members = [(group, flags["source_group"] == group) for group in GROUP_ORDER]
    members += [(MISSING, flags["source_group"].isna()), (ALL_LAKES, pd.Series(True, index=flags.index))]
    rows = []
    for group, member in members:
        n, n_clean = int(member.sum()), int((member & flags["clean"]).sum())
        rows.append(
            {"group": group, "n_lakes": n, "n_clean": n_clean, "n_not_clean": n - n_clean,
             "percent_clean": 100 * n_clean / n if n else np.nan}
        )
    return pd.DataFrame(rows)


def gap_with_ci(first, second, n_resamples=GAP_RESAMPLES, seed=GAP_SEED, level=CI_LEVEL):
    """Median of first minus median of second, with a percentile interval from resampling each group."""
    first = np.asarray(first, dtype=float)
    second = np.asarray(second, dtype=float)
    rng = np.random.default_rng(seed)
    first_medians = np.median(first[rng.integers(0, len(first), (n_resamples, len(first)))], axis=1)
    second_medians = np.median(second[rng.integers(0, len(second), (n_resamples, len(second)))], axis=1)
    tail = (1 - level) / 2 * 100
    low, high = np.percentile(first_medians - second_medians, [tail, 100 - tail])
    median_first, median_second = float(np.median(first)), float(np.median(second))
    return {
        "n_first": len(first),
        "n_second": len(second),
        "median_first": median_first,
        "median_second": median_second,
        "gap": median_first - median_second,
        "ci_low": float(low),
        "ci_high": float(high),
    }


def source_statistics(groups, values, n_resamples=GAP_RESAMPLES):
    """Group medians, gaps with intervals, spread and kruskal-wallis for one set of estimates."""
    column = f"dim_{PRIMARY_WINDOW}"
    dims = pd.DataFrame({"source_group": np.asarray(groups, dtype=object), column: np.asarray(values, dtype=float)})
    dims["source_group"] = dims["source_group"].where(dims["source_group"].notna(), None)
    medians, test = source_comparison(dims, PRIMARY_WINDOW)
    by_group = {group: dims.loc[dims["source_group"] == group, column] for group in medians["group"]}
    gaps = pd.DataFrame(
        [{"first": first, "second": second, **gap_with_ci(by_group[first], by_group[second], n_resamples)}
         for first, second in GAPS]
    )
    ordered = medians.set_index("group")["median_dim"]
    spread = {
        "largest_group": ordered.idxmax(),
        "largest_median": float(ordered.max()),
        "smallest_group": ordered.idxmin(),
        "smallest_median": float(ordered.min()),
        "spread": float(ordered.max() - ordered.min()),
    }
    return medians.drop(columns="window"), gaps, spread, test


def main():
    lakes = gpd.read_file(LAKES)
    primary = lakes[lakes["acres"] >= PRIMARY_MIN_ACRES].reset_index(drop=True)
    if len(primary) != EXPECTED_PRIMARY_N:
        sys.exit(f"stopped: primary sample has {len(primary):,} lakes, expected {EXPECTED_PRIMARY_N:,}")
    versions = read_dims_versions()
    planned = versions["planned"]
    equalized = pd.read_csv(OUT_DIR / "equalized_dims.csv")
    for name, table in [("results/primary/dims.csv", planned), ("equalized_dims.csv", equalized)]:
        if table["objectid"].tolist() != primary["objectid"].tolist():
            sys.exit(f"stopped: {name} does not hold the primary lakes in order")

    # the only recomputation: each lake rebuilt at 25 m and 50 m, for its flags
    print(f"flagging {len(primary):,} lakes", flush=True)
    flags = pd.DataFrame([lake_flags(geometry) for geometry in primary.geometry])
    flags.insert(0, "objectid", primary["objectid"])
    flags.insert(1, "source_group", planned["source_group"])
    flags["clean"] = clean_lakes(flags)
    rings = pd.read_csv(OUT_DIR / "equalized_rings.csv").set_index("interval_m")
    for interval in INTERVALS_M:
        dropped = flags[f"rings_dropped_{interval:g}m"]
        found = (int(flags["n_rings"].sum()), int(dropped.sum()), int((dropped > 0).sum()),
                 int((~flags[f"valid_{interval:g}m"]).sum()))
        logged = tuple(int(rings.loc[interval, c]) for c in
                       ["n_rings", "n_rings_dropped", "n_lakes_with_dropped_rings", "n_lakes_invalid_after_resampling"])
        if found != logged:
            sys.exit(f"stopped: flags at {interval:g} m {found} differ from equalized_rings.csv {logged}")
    flags.to_csv(OUT_DIR / "equalized_flags.csv", index=False)
    counts_by_group(flags).to_csv(OUT_DIR / "equalized_clean_counts.csv", index=False)

    median_rows, gap_rows, spread_rows, test_rows = [], [], [], []
    keep = {"clean": flags["clean"].to_numpy(), ALL_LAKES: np.ones(len(flags), dtype=bool)}
    for subset in SUBSETS:
        groups = planned["source_group"].to_numpy(dtype=object)[keep[subset]]
        for fraction in EQUALIZED_FRACTIONS:
            runs = [("as digitized", np.nan, versions[VERSION_OF_FRACTION[fraction]][f"dim_{PRIMARY_WINDOW}"])]
            runs += [(f"every {i:g} m", i, equalized[f"dim_{label(i, fraction)}"]) for i in INTERVALS_M]
            for vertices, interval, values in runs:
                medians, gaps, spread, test = source_statistics(groups, values.to_numpy()[keep[subset]])
                keys = {"subset": subset, "densify_fraction": fraction, "vertices": vertices, "interval_m": interval}
                median_rows += [{**keys, **row} for row in medians.to_dict("records")]
                gap_rows += [{**keys, **row} for row in gaps.to_dict("records")]
                spread_rows.append({**keys, **spread})
                test_rows.append({**keys, **{k: v for k, v in test.items() if k != "window"}})
        print(f"done: {subset}", flush=True)
    medians, tests = pd.DataFrame(median_rows), pd.DataFrame(test_rows)

    # on all lakes, the medians and H must be those of the equalized run
    keys = ["vertices", "densify_fraction"]
    logged = pd.read_csv(OUT_DIR / "equalized_source_groups.csv")
    both = medians[medians["subset"] == ALL_LAKES].merge(logged, on=[*keys, "group"], suffixes=("", "_logged"))
    if len(both) != len(logged) or not (both["median_dim"] == both["median_dim_logged"]).all():
        sys.exit("stopped: all-lakes medians differ from equalized_source_groups.csv")
    logged = pd.read_csv(OUT_DIR / "equalized_kruskal_wallis.csv")
    both = tests[tests["subset"] == ALL_LAKES].merge(logged, on=keys, suffixes=("", "_logged"))
    if len(both) != len(logged) or not (both["H"] == both["H_logged"]).all():
        sys.exit("stopped: all-lakes H differs from equalized_kruskal_wallis.csv")

    medians.to_csv(OUT_DIR / "equalized_clean_medians.csv", index=False)
    pd.DataFrame(gap_rows).to_csv(OUT_DIR / "equalized_clean_gaps.csv", index=False)
    pd.DataFrame(spread_rows).to_csv(OUT_DIR / "equalized_clean_spread.csv", index=False)
    tests.to_csv(OUT_DIR / "equalized_clean_kruskal_wallis.csv", index=False)
    pd.DataFrame(
        [
            *[(f"interval_m_{i + 1}", interval) for i, interval in enumerate(INTERVALS_M)],
            ("min_ring_vertices", MIN_RING_VERTICES),
            *[(f"densify_fraction_{i + 1}", f) for i, f in enumerate(EQUALIZED_FRACTIONS)],
            ("gap_resamples", GAP_RESAMPLES),
            ("gap_seed", GAP_SEED),
            ("ci_level_percent", 100 * CI_LEVEL),
        ],
        columns=["parameter", "value"],
    ).to_csv(OUT_DIR / "equalized_clean_parameters.csv", index=False)
    print(f"wrote equalized_flags.csv and equalized_clean_*.csv to {OUT_DIR.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
