"""Exploratory: box-counting dimension of the 10-acre sample, primary window only.

CLAUDE.md labels the 10-acre analysis exploratory, so no decision rule is
applied. Writes to results/primary/:
- exploratory_10acre_dims.csv: one row per lake
- exploratory_10acre_rho.csv: spearman rho of dimension vs area and vs
  shoreline length, with p-value and bootstrap confidence interval
- exploratory_10acre_r2_below_threshold.csv, exploratory_10acre_runtime.csv

Stops if a lake errors or takes longer than 60 seconds.

Run from the project root: .venv/bin/python src/exploratory_10acre.py
"""

import sys
import time

import geopandas as gpd
import pandas as pd

from primary_analysis import (
    LAKES,
    MIN_R_SQUARED,
    OUT_DIR,
    PRIMARY_WINDOW,
    ROOT,
    WINDOWS,
    LakeTooSlow,
    compute_dimensions,
    default_workers,
    rho_table,
)

# exploratory sample (CLAUDE.md): the primary filters at acres >= 10, which is
# every lake in lakes_filtered.gpkg
MIN_ACRES = 10
EXPECTED_N = 13269

# primary window only (author's decision for the exploratory run)
WINDOWS_USED = {PRIMARY_WINDOW: WINDOWS[PRIMARY_WINDOW]}


def main():
    lakes = gpd.read_file(LAKES)
    sample = lakes[lakes["acres"] >= MIN_ACRES].reset_index(drop=True)
    if len(sample) != EXPECTED_N:
        sys.exit(f"stopped: exploratory sample has {len(sample):,} lakes, expected {EXPECTED_N:,}")

    workers = default_workers()
    print(f"computing dimensions for {len(sample):,} lakes with {workers} workers", flush=True)
    wall_start = time.perf_counter()
    try:
        computed = compute_dimensions(sample, WINDOWS_USED, workers=workers, progress_every=1000)
    except LakeTooSlow as error:
        sys.exit(f"stopped: {error}")
    wall_s = time.perf_counter() - wall_start

    dims = pd.DataFrame(
        {"objectid": sample["objectid"], "acres": sample["acres"], "shoreline_m": sample["shoreline_m"]}
    ).merge(computed, on="objectid", validate="one_to_one")
    dims.to_csv(OUT_DIR / "exploratory_10acre_dims.csv", index=False)

    rho_table(dims, sample="exploratory, acres >= 10", windows=WINDOWS_USED).to_csv(
        OUT_DIR / "exploratory_10acre_rho.csv", index=False
    )
    r2 = dims[f"r2_{PRIMARY_WINDOW}"]
    pd.DataFrame(
        [
            {
                "window": PRIMARY_WINDOW,
                "min_acres": MIN_ACRES,
                "n_lakes": len(dims),
                "n_r2_below": int((r2 < MIN_R_SQUARED).sum()),
                "min_r2": r2.min(),
            }
        ]
    ).to_csv(OUT_DIR / "exploratory_10acre_r2_below_threshold.csv", index=False)
    slowest = dims.loc[dims["runtime_s"].idxmax()]
    pd.DataFrame(
        [
            {
                "run": "exploratory, acres >= 10",
                "n_lakes": len(dims),
                "workers": workers,
                "median_s": dims["runtime_s"].median(),
                "max_s": slowest["runtime_s"],
                "slowest_objectid": slowest["objectid"],
                "slowest_shoreline_m": slowest["shoreline_m"],
                "wall_s": wall_s,
            }
        ]
    ).to_csv(OUT_DIR / "exploratory_10acre_runtime.csv", index=False)
    print(f"wrote exploratory results to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
