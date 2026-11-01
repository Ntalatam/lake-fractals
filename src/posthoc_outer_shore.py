"""Post-hoc exploratory check, not pre-registered: outer shore only.

shoreline_m (src/filter_lakes.py) includes island shorelines. This check
removes every interior ring, so only the outer shore of each primary-sample
lake is box-counted, in the primary window (20-100 m, 8 offsets, seed 0).
It reports spearman rho of the outer-shore dimension against outer-shore
length and against acres, with percentile bootstrap intervals (2,000
resamples, seed 0), and counts lakes with interior rings and lakes whose
outer shore is more than 1% shorter than shoreline_m. No decision rule is
applied.

Writes to results/exploratory/outer_shore/. Every file there has "post-hoc"
in its name and on its first line. results/primary/ is only read.

Run from the project root: .venv/bin/python src/posthoc_outer_shore.py
"""

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon

from primary_analysis import (
    EXPECTED_PRIMARY_N,
    LAKES,
    PRIMARY_MIN_ACRES,
    PRIMARY_WINDOW,
    ROOT,
    WINDOWS,
    LakeTooSlow,
    compute_dimensions,
    default_workers,
    spearman_with_ci,
)

OUT_DIR = ROOT / "results" / "exploratory" / "outer_shore"
PRIMARY_DIMS = ROOT / "results" / "primary" / "dims.csv"

# primary window only (author's request for this check)
WINDOWS_USED = {PRIMARY_WINDOW: WINDOWS[PRIMARY_WINDOW]}
DIM = f"dim_outer_{PRIMARY_WINDOW}"
R2 = f"r2_outer_{PRIMARY_WINDOW}"

# author's reporting threshold: outer shore more than 1% shorter than shoreline_m
SHORTER_FRACTION = 0.01

POST_HOC = "post-hoc"


def exterior_only(geometry):
    """The lake polygon(s) with every interior ring (island shoreline) removed."""
    if geometry.geom_type == "Polygon":
        return Polygon(geometry.exterior)
    return MultiPolygon([Polygon(part.exterior) for part in geometry.geoms])


def interior_ring_count(geometry):
    parts = [geometry] if geometry.geom_type == "Polygon" else geometry.geoms
    return sum(len(part.interiors) for part in parts)


def more_than_1pct_shorter(exterior_m, shoreline_m):
    return (shoreline_m - exterior_m) > SHORTER_FRACTION * shoreline_m


def write_posthoc_csv(frame, path, description):
    """Write a csv with "post-hoc" in its file name and on its first line."""
    path = Path(path)
    if POST_HOC not in path.name:
        raise ValueError(f"post-hoc files need '{POST_HOC}' in the name: {path.name}")
    with open(path, "w") as f:
        f.write(f"# {POST_HOC} exploratory check, not pre-registered: {description}\n")
        frame.to_csv(f, index=False)


def read_posthoc_csv(path):
    return pd.read_csv(path, comment="#")


def main():
    lakes = gpd.read_file(LAKES)
    primary = lakes[lakes["acres"] >= PRIMARY_MIN_ACRES].reset_index(drop=True)
    if len(primary) != EXPECTED_PRIMARY_N:
        sys.exit(f"stopped: primary sample has {len(primary):,} lakes, expected {EXPECTED_PRIMARY_N:,}")
    outer = gpd.GeoDataFrame(
        {"objectid": primary["objectid"]}, geometry=primary.geometry.apply(exterior_only), crs=primary.crs
    )

    workers = default_workers()
    print(f"computing outer-shore dimensions for {len(outer):,} lakes with {workers} workers", flush=True)
    try:
        computed = compute_dimensions(outer, WINDOWS_USED, workers=workers, progress_every=500)
    except LakeTooSlow as error:
        sys.exit(f"stopped: {error}")

    dims = pd.DataFrame(
        {
            "objectid": primary["objectid"],
            "acres": primary["acres"],
            "shoreline_m": primary["shoreline_m"],
            "exterior_m": outer.geometry.length,
            "n_interior_rings": primary.geometry.apply(interior_ring_count),
        }
    ).merge(
        computed.rename(columns={f"dim_{PRIMARY_WINDOW}": DIM, f"r2_{PRIMARY_WINDOW}": R2}),
        on="objectid",
        validate="one_to_one",
    )

    sizes = WINDOWS_USED[PRIMARY_WINDOW]
    rho = pd.DataFrame(
        [
            {
                "window": PRIMARY_WINDOW,
                "window_min_m": sizes[0],
                "window_max_m": sizes[-1],
                "measure": measure,
                **spearman_with_ci(dims[DIM], dims[column]),
                "ci_method": "percentile",
            }
            for measure, column in [("exterior_length", "exterior_m"), ("area", "acres")]
        ]
    )
    counts = pd.DataFrame(
        [
            {
                "n_lakes": len(dims),
                "n_with_interior_rings": int((dims["n_interior_rings"] > 0).sum()),
                "n_exterior_more_than_1pct_shorter": int(
                    more_than_1pct_shorter(dims["exterior_m"], dims["shoreline_m"]).sum()
                ),
            }
        ]
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_posthoc_csv(
        dims,
        OUT_DIR / "post-hoc_outer_shore_dims.csv",
        "outer shore only (interior rings removed), primary sample, 20-100 m window, 8 offsets, seed 0. "
        "one row per lake.",
    )
    write_posthoc_csv(
        rho,
        OUT_DIR / "post-hoc_outer_shore_rho.csv",
        "spearman rho of outer-shore dimension vs outer-shore length and vs acres. "
        "percentile bootstrap 95% interval, 2,000 resamples, seed 0. no decision rule applied.",
    )
    write_posthoc_csv(
        counts,
        OUT_DIR / "post-hoc_outer_shore_counts.csv",
        "lakes with interior rings, and lakes whose outer shore is more than 1% shorter than shoreline_m.",
    )

    # consistency check, printed only: a lake without islands has the same
    # boundary in both runs, so its dimension must match results/primary exactly
    check = dims.merge(pd.read_csv(PRIMARY_DIMS)[["objectid", f"dim_{PRIMARY_WINDOW}"]], on="objectid")
    no_rings = check["n_interior_rings"] == 0
    same = (check.loc[no_rings, DIM] == check.loc[no_rings, f"dim_{PRIMARY_WINDOW}"]).all()
    print(f"check: {int(no_rings.sum()):,} lakes without interior rings, dimension equal to results/primary: {same}")
    print(rho.to_string(index=False))
    print(counts.to_string(index=False))
    print(f"max runtime {dims['runtime_s'].max():.2f} s (objectid {dims.loc[dims['runtime_s'].idxmax(), 'objectid']})")


if __name__ == "__main__":
    main()
