"""Feasibility check for the pre-registered primary sample and window.

Reports the size of primary-sample lakes relative to the largest box, and
the fit quality (r squared) of the primary window on a random 200-lake
subset. It does not report or save any dimension, and computes no
correlation: those wait for the full pre-registered run.

Run from the project root: .venv/bin/python src/feasibility.py
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from boxcount import DEFAULT_N_OFFSETS, DEFAULT_SEED, box_count_dimension

ROOT = Path(__file__).resolve().parent.parent
LAKES = ROOT / "data" / "processed" / "lakes_filtered.gpkg"
OUT_DIR = ROOT / "results" / "feasibility"

# pre-registered primary sample (author's decision, CLAUDE.md 2026-11-01):
# the other filters (Lake or Pond, shoreline >= 1,000 m, non-null geometry,
# outside_mn not Y/B) are already applied in lakes_filtered.gpkg
PRIMARY_MIN_ACRES = 100

# pre-registered primary window (author's decision): 8 log-spaced box sizes
# from 20 m to 100 m
PRIMARY_BOX_SIZES = np.geomspace(20.0, 100.0, 8)
LARGEST_BOX_M = PRIMARY_BOX_SIZES[-1]

# author's decision: 200 lakes, seed 0, for the r squared check
SUBSET_N = 200
SUBSET_SEED = 0


def equivalent_diameter(area):
    """Diameter of the circle with the same area: 2 * sqrt(area / pi)."""
    return 2.0 * np.sqrt(np.asarray(area) / np.pi)


def main():
    lakes = gpd.read_file(LAKES)
    primary = lakes[lakes["acres"] >= PRIMARY_MIN_ACRES].reset_index(drop=True)

    # polygon area in m2 (EPSG:26915). islands are holes, so this is water area
    diameter = equivalent_diameter(primary.geometry.area)
    ratio = diameter / LARGEST_BOX_M

    subset = primary.sample(n=SUBSET_N, random_state=np.random.default_rng(SUBSET_SEED))
    r_squared = [
        box_count_dimension(geom, PRIMARY_BOX_SIZES, DEFAULT_N_OFFSETS, DEFAULT_SEED).r_squared
        for geom in subset.geometry
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {"objectid": subset["objectid"].to_numpy(), "acres": subset["acres"].to_numpy(), "r2_primary": r_squared}
    ).to_csv(OUT_DIR / "feasibility_r2.csv", index=False)

    lines = [
        f"primary sample (acres >= {PRIMARY_MIN_ACRES}): {len(primary)} lakes",
        "",
        "equivalent diameter, 2 * sqrt(area / pi), from polygon area (m):",
        f"  median {np.median(diameter):.1f}, min {diameter.min():.1f}, max {diameter.max():.1f}",
        f"median ratio of diameter to {LARGEST_BOX_M:.0f} m: {np.median(ratio):.2f}",
        "",
        f"r squared under the primary window ({PRIMARY_BOX_SIZES[0]:.0f}-{LARGEST_BOX_M:.0f} m, "
        f"{len(PRIMARY_BOX_SIZES)} sizes, {DEFAULT_N_OFFSETS} offsets, seed {DEFAULT_SEED}), "
        f"random subset of {SUBSET_N} (seed {SUBSET_SEED}):",
        f"  median {np.median(r_squared):.4f}",
    ]
    summary = "\n".join(lines)
    (OUT_DIR / "feasibility_summary.txt").write_text(summary + "\n")
    print(summary)


if __name__ == "__main__":
    main()
