"""Pilot: box-counting dimension of 200 lakes under two scale windows.

Draws a stratified random sample of 50 lakes from each acreage bin, computes
the dimension with window A (10-100 m) and window B (20-200 m), and writes
per-lake results and a summary to results/pilot/. Stops if one lake takes
longer than 60 seconds.

Run from the project root: .venv/bin/python src/pilot_windows.py
"""

import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from boxcount import DEFAULT_N_OFFSETS, DEFAULT_SEED, box_count_dimension

ROOT = Path(__file__).resolve().parent.parent
LAKES = ROOT / "data" / "processed" / "lakes_filtered.gpkg"
OUT_DIR = ROOT / "results" / "pilot"

# acreage bins (author's decision). each edge belongs to the upper bin:
# [10, 25), [25, 100), [100, 1,000), [1,000, inf). the sample starts at 10
# acres, so the lowest bin is 10 to 25.
BIN_EDGES = [-np.inf, 25, 100, 1000, np.inf]
BIN_LABELS = ["under 25", "25 to 100", "100 to 1,000", "over 1,000"]

# author's decision: 50 lakes per bin, seed 0, so the same lakes are drawn
# every run
N_PER_BIN = 50
SAMPLE_SEED = 0

# two scale windows to compare (author's decision), 8 log-spaced sizes each.
# A is the current setting; B is the same span (one decade) shifted up 2x.
WINDOWS = {
    "A": np.geomspace(10.0, 100.0, 8),
    "B": np.geomspace(20.0, 200.0, 8),
}

# author's thresholds for reporting
MIN_R_SQUARED = 0.98
MAX_SECONDS_PER_LAKE = 60


def acreage_bin(acres):
    return pd.cut(acres, BIN_EDGES, labels=BIN_LABELS, right=False).astype(str)


def stratified_sample(lakes, n_per_bin=N_PER_BIN, seed=SAMPLE_SEED):
    lakes = lakes.assign(acreage_bin=acreage_bin(lakes["acres"]))
    rng = np.random.default_rng(seed)
    parts = [
        lakes[lakes["acreage_bin"] == label].sample(n=n_per_bin, random_state=rng)
        for label in BIN_LABELS
    ]
    return pd.concat(parts).reset_index(drop=True)


def main():
    sample = stratified_sample(gpd.read_file(LAKES))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for lake in sample.itertuples():
        start = time.perf_counter()
        row = {
            "objectid": lake.objectid,
            "acreage_bin": lake.acreage_bin,
            "acres": lake.acres,
            "shoreline_m": lake.shoreline_m,
        }
        for name, sizes in WINDOWS.items():
            result = box_count_dimension(lake.geometry, sizes, DEFAULT_N_OFFSETS, DEFAULT_SEED)
            row[f"dim_{name}"] = result.dimension
            row[f"r2_{name}"] = result.r_squared
        row["runtime_s"] = time.perf_counter() - start
        rows.append(row)
        if row["runtime_s"] > MAX_SECONDS_PER_LAKE:
            pd.DataFrame(rows).to_csv(OUT_DIR / "pilot_dims.csv", index=False)
            sys.exit(
                f"stopped: lake {lake.objectid} took {row['runtime_s']:.1f} s "
                f"(limit {MAX_SECONDS_PER_LAKE} s); {len(rows)} lakes written"
            )

    dims = pd.DataFrame(rows)
    dims.to_csv(OUT_DIR / "pilot_dims.csv", index=False)

    log_acres = np.log(dims["acres"])
    by_bin = dims.groupby("acreage_bin", sort=False)[["dim_A", "dim_B"]].median()
    slowest = dims.loc[dims["runtime_s"].idxmax()]
    low_fit = (dims["r2_A"] < MIN_R_SQUARED) | (dims["r2_B"] < MIN_R_SQUARED)
    lines = [
        f"lakes: {len(dims)} ({N_PER_BIN} per bin, seed {SAMPLE_SEED})",
        "",
        "median dimension by acreage bin:",
        by_bin.round(4).to_string(),
        "",
        "spearman correlation with log(acres):",
        "  window A: rho = {:.4f}, p = {:.3g}".format(*spearmanr(dims["dim_A"], log_acres)),
        "  window B: rho = {:.4f}, p = {:.3g}".format(*spearmanr(dims["dim_B"], log_acres)),
        "",
        f"lakes with r2 < {MIN_R_SQUARED} under either window: {int(low_fit.sum())}",
        f"  under window A: {int((dims['r2_A'] < MIN_R_SQUARED).sum())}",
        f"  under window B: {int((dims['r2_B'] < MIN_R_SQUARED).sum())}",
        "",
        "runtime per lake, both windows (s): "
        f"median {dims['runtime_s'].median():.3f}, mean {dims['runtime_s'].mean():.3f}, "
        f"max {dims['runtime_s'].max():.3f}, total {dims['runtime_s'].sum():.1f}",
        f"slowest lake: objectid {slowest['objectid']}, {slowest['acres']:.1f} acres, "
        f"{slowest['shoreline_m']:.0f} m shoreline, {slowest['runtime_s']:.2f} s",
    ]
    summary = "\n".join(lines)
    (OUT_DIR / "pilot_summary.txt").write_text(summary + "\n")
    print(summary)


if __name__ == "__main__":
    main()
