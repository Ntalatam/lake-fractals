"""Post-hoc check, not in the analysis plan: digitizing density.

Vertex spacing: for each primary lake, the distance between consecutive
vertices along every ring (outer shore and islands, every part), as digitized
and before any densifying, summarized per lake by its median and 90th
percentile. Reported by mapping source group (median and interquartile range
of the per-lake values), with a kruskal-wallis test of the per-lake median
spacing across the five planned groups (lakes with no delineat_1 excluded, as
in the planned source comparison), and spearman rho between the per-lake
median spacing and the primary-window estimate, over all lakes and within each
group.

Equalized resampling: every ring is rebuilt with vertices at a fixed interval
along it, 25 m and 50 m, starting at the ring's own start point, and the
primary-window estimate is recomputed from the rebuilt rings. A ring too short
to keep 4 vertices is dropped and counted. The author set densify_fraction
0.01 for the recomputed estimates; they are also computed at the planned 0.1,
so that every result can be set beside both the planned estimates and the
spacing-0.01 estimates.

Every analysis that uses lake estimates is run on both sets of estimates
(DIMS_VERSIONS in src/validation.py).

Stop rule (author's): stop only if the whole run passes 3 hours. The planned
60 s per-lake limit is not applied. The limit is checked when a lake
finishes; lakes already running finish first.

Writes to results/validation/: vertices*.csv and equalized*.csv.
results/primary/ is only read.

Run from the project root: .venv/bin/python src/validation_vertices.py
(or name the parts to run: vertices, equalized)
"""

import argparse
import math
import signal
import sys
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from scipy.stats import kruskal
from shapely.geometry import MultiPolygon, Polygon

from boxcount import DENSIFY_FRACTION
from primary_analysis import (
    EXPECTED_PRIMARY_N,
    LAKES,
    OTHER,
    PRIMARY_MIN_ACRES,
    PRIMARY_WINDOW,
    ROOT,
    STANDALONE_SOURCES,
    WINDOWS,
    LakeTooSlow,
    compute_dimensions,
    source_comparison,
    spearman_with_ci,
)
from validation import OUT_DIR, read_dims_versions

# author's settings: vertices every 25 m and every 50 m along each ring; a
# rebuilt ring needs at least 4 distinct vertices (the closing point, which
# repeats the first, is not counted)
INTERVALS_M = [25.0, 50.0]
MIN_RING_VERTICES = 4

# point spacing for the recomputed estimates: the author's 0.01 and the
# planned 0.1, so each can be set beside the matching set of lake estimates
EQUALIZED_FRACTIONS = [0.1, 0.01]
VERSION_OF_FRACTION = {DENSIFY_FRACTION: "planned", 0.01: "spacing_0p01"}

# author's settings for the run: 4 worker processes, stop only if the whole
# run passes 3 hours
WORKERS = 4
MAX_WALL_SECONDS = 3 * 60 * 60

GROUP_ORDER = STANDALONE_SOURCES + [OTHER]
ALL_LAKES = "all lakes"

# the vertex spacing tables take seconds and the equalized resampling about
# half an hour, so either can be run alone
PARTS = ["vertices", "equalized"]


class RunTooLong(RuntimeError):
    pass


def lake_rings(geometry):
    """(part, ring) pairs for every ring of a polygon or multipolygon; ring 0 is the exterior."""
    pairs = []
    for polygon in shapely.get_parts(geometry):
        pairs.append((polygon, polygon.exterior))
        pairs += [(polygon, ring) for ring in polygon.interiors]
    return pairs


def vertex_spacing(geometry):
    """Distances between consecutive vertices over every ring, as digitized."""
    rings = [ring for _, ring in lake_rings(geometry)]
    lengths = np.concatenate([np.hypot(*np.diff(np.asarray(ring.coords), axis=0).T) for ring in rings])
    return {
        "n_rings": len(rings),
        "n_segments": len(lengths),
        "n_zero_segments": int((lengths == 0).sum()),
        "median_spacing_m": float(np.median(lengths)),
        "p90_spacing_m": float(np.percentile(lengths, 90)),
    }


def resample_ring(ring, interval):
    """Points every `interval` meters along a ring from its start point, or None if fewer than 4 fit.

    The points are not closed: the ring closes back to the start point.
    """
    # positions 0, interval, 2 * interval, ... below the ring length; the
    # small allowance keeps a position equal to the length (the start point
    # again) out
    n = int(math.ceil(ring.length / interval - 1e-9))
    if n < MIN_RING_VERTICES:
        return None
    return shapely.get_coordinates(shapely.line_interpolate_point(ring, np.arange(n) * interval))


def resample_lake(geometry, interval):
    """The lake with every ring rebuilt at `interval`, and a log of dropped rings.

    A dropped exterior drops its whole part, holes included.
    """
    parts = []
    log = {"n_rings": 0, "n_rings_dropped": 0, "n_rings_dropped_3_vertices": 0, "dropped_length_m": 0.0}

    def rebuilt(ring):
        log["n_rings"] += 1
        points = resample_ring(ring, interval)
        if points is None:
            log["n_rings_dropped"] += 1
            log["n_rings_dropped_3_vertices"] += int(math.ceil(ring.length / interval - 1e-9)) == 3
            log["dropped_length_m"] += ring.length
        return points

    for polygon in shapely.get_parts(geometry):
        shell = rebuilt(polygon.exterior)
        holes = [rebuilt(ring) for ring in polygon.interiors]
        if shell is not None:
            parts.append(Polygon(shell, [hole for hole in holes if hole is not None]))
    resampled = MultiPolygon(parts)
    log["is_valid"] = bool(resampled.is_valid)
    return resampled, log


def spacing_by_group(spacing):
    """Median and quartiles of the per-lake spacing, per source group and over all lakes."""
    rows = []
    groups = [(group, spacing[spacing["source_group"] == group]) for group in GROUP_ORDER]
    for group, members in groups + [(ALL_LAKES, spacing)]:
        if members.empty:
            continue
        row = {"group": group, "n": len(members)}
        for measure in ("median_spacing", "p90_spacing"):
            q25, median, q75 = np.percentile(members[f"{measure}_m"], [25, 50, 75])
            row.update({f"{measure}_median": median, f"{measure}_q25": q25, f"{measure}_q75": q75})
        rows.append(row)
    return pd.DataFrame(rows)


def spacing_kruskal_wallis(spacing):
    """Kruskal-wallis of per-lake median spacing across the planned groups, missing sources excluded."""
    known = spacing[spacing["source_group"].notna()]
    samples = [known.loc[known["source_group"] == g, "median_spacing_m"] for g in GROUP_ORDER]
    samples = [s for s in samples if len(s)]
    statistic, p_value = kruskal(*samples)
    return pd.DataFrame(
        [
            {
                "measure": "median_spacing_m",
                "n_groups": len(samples),
                "n_lakes": len(known),
                "n_excluded_missing": int(spacing["source_group"].isna().sum()),
                "H": float(statistic),
                "p_value": float(p_value),
            }
        ]
    )


def spacing_rho(spacing, versions, window=PRIMARY_WINDOW):
    """Spearman rho of median spacing against the estimate, over all lakes and within each group."""
    rows = []
    for version, dims in versions.items():
        both = spacing[["objectid", "source_group", "median_spacing_m"]].merge(
            dims[["objectid", f"dim_{window}"]], on="objectid", validate="one_to_one"
        )
        subsets = [(ALL_LAKES, both)] + [(g, both[both["source_group"] == g]) for g in GROUP_ORDER]
        for group, members in subsets:
            rows.append(
                {
                    "dims": version,
                    "group": group,
                    "window": window,
                    **spearman_with_ci(members["median_spacing_m"], members[f"dim_{window}"]),
                }
            )
    return pd.DataFrame(rows)


def label(interval, fraction):
    return f"{interval:g}m_f{str(fraction).replace('.', 'p')}"


def over_time(signum, frame):
    raise RunTooLong(f"the whole run passed {MAX_WALL_SECONDS / 3600:g} hours")


def parse_parts(argv=None):
    """The parts named on the command line, in PARTS order; all of them if none is named."""
    parser = argparse.ArgumentParser(description="post-hoc check of digitizing density")
    parser.add_argument("parts", nargs="*", help=f"any of {PARTS} (default: all)")
    parts = parser.parse_args(argv).parts or PARTS
    if unknown := set(parts) - set(PARTS):
        sys.exit(f"unknown parts {sorted(unknown)}; choose from {PARTS}")
    return [part for part in PARTS if part in parts]


def main():
    parts = parse_parts()
    lakes = gpd.read_file(LAKES)
    primary = lakes[lakes["acres"] >= PRIMARY_MIN_ACRES].reset_index(drop=True)
    if len(primary) != EXPECTED_PRIMARY_N:
        sys.exit(f"stopped: primary sample has {len(primary):,} lakes, expected {EXPECTED_PRIMARY_N:,}")
    versions = read_dims_versions()
    planned = versions["planned"]
    if planned["objectid"].tolist() != primary["objectid"].tolist():
        sys.exit("stopped: results/primary/dims.csv does not hold the primary lakes in order")

    if "vertices" in parts:
        # vertex spacing, as digitized
        spacing = pd.DataFrame([vertex_spacing(g) for g in primary.geometry])
        spacing.insert(0, "objectid", primary["objectid"])
        spacing.insert(1, "source_group", planned["source_group"])
        spacing.to_csv(OUT_DIR / "vertices.csv", index=False)
        spacing_by_group(spacing).to_csv(OUT_DIR / "vertices_by_group.csv", index=False)
        spacing_kruskal_wallis(spacing).to_csv(OUT_DIR / "vertices_kruskal_wallis.csv", index=False)
        spacing_rho(spacing, versions).to_csv(OUT_DIR / "vertices_rho.csv", index=False)
        print("wrote vertex spacing tables", flush=True)

    if "equalized" in parts:
        # equalized resampling
        resampled, ring_logs = {}, []
        for interval in INTERVALS_M:
            rebuilt = [resample_lake(g, interval) for g in primary.geometry]
            resampled[interval] = gpd.GeoDataFrame(
                {"objectid": primary["objectid"]}, geometry=[g for g, _ in rebuilt], crs=primary.crs
            )
            logs = pd.DataFrame([log for _, log in rebuilt])
            ring_logs.append(
                {
                    "interval_m": interval,
                    "n_lakes": len(logs),
                    "n_rings": int(logs["n_rings"].sum()),
                    "n_rings_dropped": int(logs["n_rings_dropped"].sum()),
                    "n_rings_dropped_3_vertices": int(logs["n_rings_dropped_3_vertices"].sum()),
                    "dropped_length_m": float(logs["dropped_length_m"].sum()),
                    "n_lakes_with_dropped_rings": int((logs["n_rings_dropped"] > 0).sum()),
                    "n_lakes_invalid_after_resampling": int((~logs["is_valid"]).sum()),
                }
            )
        pd.DataFrame(ring_logs).to_csv(OUT_DIR / "equalized_rings.csv", index=False)
        print(pd.DataFrame(ring_logs).to_string(index=False), flush=True)

        window = {PRIMARY_WINDOW: WINDOWS[PRIMARY_WINDOW]}
        equalized = pd.DataFrame({"objectid": primary["objectid"], "source_group": planned["source_group"]})
        runtimes = []
        signal.signal(signal.SIGALRM, over_time)
        signal.alarm(MAX_WALL_SECONDS)
        try:
            # the author's 0.01 first, then the planned 0.1
            for fraction in sorted(EQUALIZED_FRACTIONS):
                for interval in INTERVALS_M:
                    name = label(interval, fraction)
                    print(f"equalized {name}: {len(primary):,} lakes with {WORKERS} workers", flush=True)
                    start = time.perf_counter()
                    computed = compute_dimensions(
                        resampled[interval],
                        window,
                        workers=WORKERS,
                        max_seconds=math.inf,
                        progress_every=500,
                        densify_fraction=fraction,
                    )
                    wall_s = time.perf_counter() - start
                    equalized[f"dim_{name}"] = computed[f"dim_{PRIMARY_WINDOW}"].to_numpy()
                    equalized[f"r2_{name}"] = computed[f"r2_{PRIMARY_WINDOW}"].to_numpy()
                    runtimes.append(
                        {
                            "run": name,
                            "interval_m": interval,
                            "densify_fraction": fraction,
                            "n_lakes": len(computed),
                            "workers": WORKERS,
                            "median_s": computed["runtime_s"].median(),
                            "max_s": computed["runtime_s"].max(),
                            "wall_s": wall_s,
                        }
                    )
        except (RunTooLong, LakeTooSlow) as error:
            sys.exit(f"stopped: {error}")
        finally:
            signal.alarm(0)
        equalized.to_csv(OUT_DIR / "equalized_dims.csv", index=False)
        pd.DataFrame(runtimes).to_csv(OUT_DIR / "equalized_runtime.csv", index=False)

        # group medians and kruskal-wallis, as digitized (the two sets of lake
        # estimates) and for each resampling
        group_rows, test_rows = [], []
        for fraction in EQUALIZED_FRACTIONS:
            baseline = versions[VERSION_OF_FRACTION[fraction]]
            runs = [("as digitized", np.nan, baseline[["source_group", f"dim_{PRIMARY_WINDOW}"]])]
            for interval in INTERVALS_M:
                column = equalized[["source_group", f"dim_{label(interval, fraction)}"]]
                runs.append((f"every {interval:g} m", interval, column.set_axis(["source_group", f"dim_{PRIMARY_WINDOW}"], axis=1)))
            for vertices, interval, dims in runs:
                groups, test = source_comparison(dims, PRIMARY_WINDOW)
                keys = {"vertices": vertices, "interval_m": interval, "densify_fraction": fraction}
                group_rows += [{**keys, **row} for row in groups.drop(columns="window").to_dict("records")]
                test_rows.append({**keys, **test})
        pd.DataFrame(group_rows).to_csv(OUT_DIR / "equalized_source_groups.csv", index=False)
        pd.DataFrame(test_rows).to_csv(OUT_DIR / "equalized_kruskal_wallis.csv", index=False)

        pd.DataFrame(
            [
                *[(f"interval_m_{i + 1}", interval) for i, interval in enumerate(INTERVALS_M)],
                ("min_ring_vertices", MIN_RING_VERTICES),
                *[(f"densify_fraction_{i + 1}", f) for i, f in enumerate(EQUALIZED_FRACTIONS)],
                ("window_min_m", WINDOWS[PRIMARY_WINDOW][0]),
                ("window_max_m", WINDOWS[PRIMARY_WINDOW][-1]),
                ("workers", WORKERS),
                ("max_wall_seconds", MAX_WALL_SECONDS),
                ("max_seconds_per_lake", math.inf),
            ],
            columns=["parameter", "value"],
        ).to_csv(OUT_DIR / "equalized_parameters.csv", index=False)
        print(f"wrote results to {OUT_DIR.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
