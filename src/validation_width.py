"""Post-hoc check, not in the analysis plan: lake width and narrow shore.

For each primary lake:
- the diameter of the largest circle inside the lake
  (shapely.maximum_inscribed_circle)
- the short and long sides of the minimum rotated rectangle around it
- the narrow-shore share for the largest box of each window: the share of
  shoreline in parts of the lake narrower than that box

Narrow shore (author's definition, 2026-11-01). The lake is opened with a
disk of radius r, half the largest box (r = 50 m for the 100 m box, 100 m
for the 200 m box): opened = lake.buffer(-r).buffer(r). Parts narrower than
2r, and convex corners, are not in the opened lake. Narrow shore is the
shoreline more than 1 m from the opened lake, and the share is its length
over the total shoreline length. The first definition, shoreline within 1 m
of lake minus opened, was replaced before any result was computed: buffer
round-off leaves centimeter-thin slivers between the lake and the opened
lake along the whole shore, so a plain circle scored 0.38 at r = 50 m.

Sensitivity check (set by the author before results): the six primary rhos
are recomputed without the lakes whose narrow-shore share for that window's
largest box is above 10%, and the planned decision rule is applied.

Every analysis that uses lake estimates is run on both sets of estimates
(DIMS_VERSIONS in src/validation.py).

Writes to results/validation/: width.csv and width_*.csv. results/primary/
is only read.

Run from the project root: .venv/bin/python src/validation_width.py
"""

import sys
from concurrent.futures import ProcessPoolExecutor

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from primary_analysis import (
    BOOTSTRAP_RESAMPLES,
    EXPECTED_PRIMARY_N,
    LAKES,
    MEASURES,
    PRIMARY_MIN_ACRES,
    ROOT,
    WINDOWS,
    decision_rule,
    default_workers,
    spearman_with_ci,
)
from primary_analysis import OUT_DIR as PRIMARY_DIR
from validation import OUT_DIR, read_dims_versions

# opening radius per window: half its largest box (author's)
NARROW_RADIUS_M = {window: sizes[-1] / 2 for window, sizes in WINDOWS.items()}
RADII_M = sorted(set(NARROW_RADIUS_M.values()))

# narrow shore is shoreline more than 1 m from the opened lake (author's)
SHORE_GAP_M = 1.0

# sensitivity check (author's, set before results): drop lakes whose narrow
# share for the window's largest box is above 10%
MAX_NARROW_SHARE = 0.10

# inscribed-circle tolerance. chosen here, not set by the author: GEOS's
# default is 1/1000 of the lake's extent, tens of meters for the largest
# lakes, and 1 m keeps the error in the radius under 1 m for every lake
INSCRIBED_TOLERANCE_M = 1.0

# lakes with inscribed diameter below these are counted (author's)
DIAMETER_THRESHOLDS_M = [200.0, 400.0]

DECISION_DIRS = {"planned": PRIMARY_DIR, "spacing_0p01": OUT_DIR / "spacing_0p01"}
WIDTH_MEASURES = [
    "inscribed_diameter_m",
    "rectangle_short_side_m",
    "rectangle_long_side_m",
    *[f"narrow_share_r{r:g}" for r in RADII_M],
]


def share_column(window):
    return f"narrow_share_r{NARROW_RADIUS_M[window]:g}"


def inscribed_diameter(geometry):
    return 2 * shapely.maximum_inscribed_circle(geometry, tolerance=INSCRIBED_TOLERANCE_M).length


def rectangle_sides(geometry):
    """(short, long) sides of the minimum rotated rectangle.

    GEOS 3.14 warns "invalid value" on axis-aligned rectangles but returns the
    right rectangle (tests/test_validation_width.py); main() checks that every
    lake's result is finite.
    """
    corners = np.asarray(shapely.oriented_envelope(geometry).exterior.coords)
    sides = np.hypot(*np.diff(corners[:3], axis=0).T)
    return float(sides.min()), float(sides.max())


def narrow_share(geometry, radius):
    """Share of shoreline more than SHORE_GAP_M from the lake opened with a disk of this radius."""
    opened = geometry.buffer(-radius).buffer(radius)
    shore = geometry.boundary
    return shore.difference(opened.buffer(SHORE_GAP_M)).length / shore.length


def lake_width(geometry):
    short, long = rectangle_sides(geometry)
    return {
        "inscribed_diameter_m": inscribed_diameter(geometry),
        "rectangle_short_side_m": short,
        "rectangle_long_side_m": long,
        **{f"narrow_share_r{r:g}": narrow_share(geometry, r) for r in RADII_M},
    }


def distribution(table, columns):
    rows = []
    for column in columns:
        values = table[column].to_numpy(dtype=float)
        p5, p25, median, p75, p95 = np.percentile(values, [5, 25, 50, 75, 95])
        rows.append(
            {"measure": column, "n": len(values), "min": values.min(), "p5": p5, "p25": p25, "median": median,
             "p75": p75, "p95": p95, "max": values.max(), "mean": values.mean()}
        )
    return pd.DataFrame(rows)


def narrow_sensitivity(dims, width, n_resamples=BOOTSTRAP_RESAMPLES):
    """The six primary rhos without lakes above MAX_NARROW_SHARE, and the planned decision rule."""
    both = dims.merge(width, on="objectid", validate="one_to_one")
    rows = []
    for window, sizes in WINDOWS.items():
        keep = both[share_column(window)] <= MAX_NARROW_SHARE
        for measure, column in MEASURES.items():
            rows.append(
                {
                    "window": window,
                    "window_min_m": sizes[0],
                    "window_max_m": sizes[-1],
                    "narrow_share_column": share_column(window),
                    "measure": measure,
                    "n_excluded": int((~keep).sum()),
                    **spearman_with_ci(both.loc[keep, f"dim_{window}"], both.loc[keep, column], n_resamples),
                }
            )
    rho = pd.DataFrame(rows)
    rules = []
    for measure in MEASURES:
        by_window = rho[rho["measure"] == measure].set_index("window")["rho"]
        rules.append({"measure": measure, **{f"rho_{w}": by_window[w] for w in WINDOWS}, **decision_rule(by_window.to_dict())})
    return rho, pd.DataFrame(rules)


def main():
    lakes = gpd.read_file(LAKES)
    primary = lakes[lakes["acres"] >= PRIMARY_MIN_ACRES].reset_index(drop=True)
    if len(primary) != EXPECTED_PRIMARY_N:
        sys.exit(f"stopped: primary sample has {len(primary):,} lakes, expected {EXPECTED_PRIMARY_N:,}")
    versions = read_dims_versions()
    planned = versions["planned"]
    if planned["objectid"].tolist() != primary["objectid"].tolist():
        sys.exit("stopped: results/primary/dims.csv does not hold the primary lakes in order")

    workers = default_workers()
    print(f"width of {len(primary):,} lakes with {workers} workers", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(lake_width, primary.geometry, chunksize=16))
    width = pd.concat([planned[["objectid", "acres", "shoreline_m", "source_group"]], pd.DataFrame(rows)], axis=1)
    if not np.isfinite(width[WIDTH_MEASURES].to_numpy(dtype=float)).all():
        sys.exit("stopped: a width measure is not finite")
    width.to_csv(OUT_DIR / "width.csv", index=False)

    distribution(width, WIDTH_MEASURES).to_csv(OUT_DIR / "width_summary.csv", index=False)
    counts = [
        {"measure": "inscribed_diameter_m", "comparison": "below", "threshold": t,
         "n_lakes": int((width["inscribed_diameter_m"] < t).sum())}
        for t in DIAMETER_THRESHOLDS_M
    ] + [
        {"measure": f"narrow_share_r{r:g}", "comparison": "above", "threshold": MAX_NARROW_SHARE,
         "n_lakes": int((width[f"narrow_share_r{r:g}"] > MAX_NARROW_SHARE).sum())}
        for r in RADII_M
    ]
    counts = pd.DataFrame(counts)
    counts["share"] = counts["n_lakes"] / len(width)
    counts["percent"] = 100 * counts["share"]
    counts.to_csv(OUT_DIR / "width_counts.csv", index=False)

    # narrow share against acres (no lake estimate involved)
    pd.DataFrame(
        [{"narrow_share_column": f"narrow_share_r{r:g}", "measure": "area",
          **spearman_with_ci(width[f"narrow_share_r{r:g}"], width["acres"])} for r in RADII_M]
    ).to_csv(OUT_DIR / "width_rho_acres.csv", index=False)

    rho_rows, sensitivity_rows, rule_rows = [], [], []
    for version, dims in versions.items():
        both = dims[["objectid", *[f"dim_{w}" for w in WINDOWS]]].merge(width, on="objectid", validate="one_to_one")
        for window, sizes in WINDOWS.items():
            rho_rows.append(
                {"dims": version, "window": window, "window_min_m": sizes[0], "window_max_m": sizes[-1],
                 "narrow_share_column": share_column(window),
                 **spearman_with_ci(both[share_column(window)], both[f"dim_{window}"])}
            )
        rho, rules = narrow_sensitivity(dims, width[["objectid", *[f"narrow_share_r{r:g}" for r in RADII_M]]])
        sensitivity_rows.append(rho.assign(dims=version))
        planned_rule = pd.read_csv(DECISION_DIRS[version] / "decision_rule.csv").set_index("measure")
        rules["outcome_all_lakes"] = rules["measure"].map(planned_rule["outcome"])
        rule_rows.append(rules.assign(dims=version))
        print(f"done: {version}", flush=True)
    pd.DataFrame(rho_rows).to_csv(OUT_DIR / "width_rho.csv", index=False)
    sensitivity = pd.concat(sensitivity_rows)
    sensitivity[["dims", *[c for c in sensitivity.columns if c != "dims"]]].to_csv(
        OUT_DIR / "width_sensitivity_rho.csv", index=False
    )
    rules = pd.concat(rule_rows)
    rules[["dims", *[c for c in rules.columns if c != "dims"]]].to_csv(
        OUT_DIR / "width_sensitivity_decision_rule.csv", index=False
    )
    pd.DataFrame(
        [
            *[(f"narrow_radius_m_{w}", r) for w, r in NARROW_RADIUS_M.items()],
            ("shore_gap_m", SHORE_GAP_M),
            ("max_narrow_share", MAX_NARROW_SHARE),
            ("inscribed_tolerance_m", INSCRIBED_TOLERANCE_M),
        ],
        columns=["parameter", "value"],
    ).to_csv(OUT_DIR / "width_parameters.csv", index=False)
    print(f"wrote width results to {OUT_DIR.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
