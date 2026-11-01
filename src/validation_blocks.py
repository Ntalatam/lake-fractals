"""Post-hoc check, not in the analysis plan: spatial block bootstrap.

The planned intervals resample single lakes, which treats lakes as
independent. Here each primary lake is assigned to a square block by its
centroid in EPSG:26915, for blocks of 25, 50 and 100 km, and whole blocks are
resampled with replacement (as many blocks as the sample has, 2,000
resamples, seed 0). Percentile 95% intervals are computed for the six
primary rhos, the six within-2004-FSA rhos, and each source group's median
in the primary window.

Each statistic is resampled within its own sample: the 2004 FSA rhos resample
the blocks that hold 2004 FSA lakes, and each group's median resamples the
blocks that hold that group's lakes, as the lake-level intervals resample
lakes within the same sample. The generator is re-seeded for each statistic,
so every statistic of one sample and block size uses the same resampled
blocks. The lake-level rho intervals beside them are read from the planned
files; the lake-level median intervals (not in the planned files) are
computed here with the same settings.

Every analysis is run on both sets of lake estimates (DIMS_VERSIONS in
src/validation.py).

Writes to results/validation/: blocks_counts.csv, blocks_rho.csv,
blocks_medians.csv, blocks_parameters.csv. results/primary/ is only read.

Run from the project root: .venv/bin/python src/validation_blocks.py
"""

import sys
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from primary_analysis import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    CI_LEVEL,
    EXPECTED_PRIMARY_N,
    LAKES,
    MEASURES,
    OTHER,
    PRIMARY_MIN_ACRES,
    PRIMARY_WINDOW,
    ROOT,
    STANDALONE_SOURCES,
    WINDOWS,
    WITHIN_SOURCE_GROUP,
)
from primary_analysis import OUT_DIR as PRIMARY_DIR
from validation import OUT_DIR, read_dims_versions

# author's settings: square blocks of 25, 50 and 100 km, 2,000 resamples of
# blocks, seed 0, percentile 95% intervals (the planned resample count, seed
# and level). the block grid is anchored at the origin of EPSG:26915 (chosen
# here, not set by the author: any fixed grid would do, and the origin needs
# no choice of its own).
BLOCK_SIZES_KM = [25, 50, 100]
BLOCK_RESAMPLES = BOOTSTRAP_RESAMPLES
BLOCK_SEED = BOOTSTRAP_SEED

# where the planned lake-level rho intervals are, for each set of estimates
LAKE_LEVEL_DIRS = {"planned": PRIMARY_DIR, "spacing_0p01": OUT_DIR / "spacing_0p01"}
RHO_FILES = {"primary": "rho_primary.csv", f"{WITHIN_SOURCE_GROUP} only": "rho_within_2004_fsa.csv"}
GROUP_ORDER = STANDALONE_SOURCES + [OTHER]


def block_ids(x, y, size_m):
    """A block number for each point: squares of side size_m on a grid anchored at (0, 0)."""
    ix = np.floor(np.asarray(x, dtype=float) / size_m).astype(np.int64)
    iy = np.floor(np.asarray(y, dtype=float) / size_m).astype(np.int64)
    _, ids = np.unique(np.column_stack([ix, iy]), axis=0, return_inverse=True)
    return ids.ravel()


def block_members(ids):
    """Index arrays of the lakes in each occupied block."""
    _, ids = np.unique(ids, return_inverse=True)
    order = np.argsort(ids, kind="stable")
    return np.split(order, np.cumsum(np.bincount(ids))[:-1])


def block_counts(ids):
    sizes = np.array([len(m) for m in block_members(ids)])
    return {
        "n_lakes": int(sizes.sum()),
        "n_blocks": len(sizes),
        "lakes_per_block_min": int(sizes.min()),
        "lakes_per_block_median": float(np.median(sizes)),
        "lakes_per_block_mean": float(sizes.mean()),
        "lakes_per_block_max": int(sizes.max()),
    }


def block_resample(members, rng):
    """Lake indices of one resample: as many blocks as there are, drawn with replacement."""
    picks = rng.integers(0, len(members), len(members))
    return np.concatenate([members[i] for i in picks])


def percentile_interval(values, level):
    tail = (1 - level) / 2 * 100
    low, high = np.nanpercentile(values, [tail, 100 - tail])
    return float(low), float(high)


def spearman_block_ci(x, y, ids, n_resamples=BLOCK_RESAMPLES, seed=BLOCK_SEED, level=CI_LEVEL):
    """Spearman rho and its percentile interval from resampling whole blocks."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    members = block_members(ids)
    rng = np.random.default_rng(seed)
    resampled = np.empty(n_resamples)
    with warnings.catch_warnings():
        # a resample can be constant; its rho is nan and skipped
        warnings.simplefilter("ignore")
        for i in range(n_resamples):
            index = block_resample(members, rng)
            resampled[i] = spearmanr(x[index], y[index]).statistic
    low, high = percentile_interval(resampled, level)
    return {"n": len(x), "n_blocks": len(members), "rho": float(spearmanr(x, y).statistic), "ci_low": low, "ci_high": high}


def median_block_ci(values, ids, n_resamples=BLOCK_RESAMPLES, seed=BLOCK_SEED, level=CI_LEVEL):
    values = np.asarray(values, dtype=float)
    members = block_members(ids)
    rng = np.random.default_rng(seed)
    resampled = np.array([np.median(values[block_resample(members, rng)]) for _ in range(n_resamples)])
    low, high = percentile_interval(resampled, level)
    return {"n": len(values), "n_blocks": len(members), "median": float(np.median(values)), "ci_low": low, "ci_high": high}


def median_lake_ci(values, n_resamples=BLOCK_RESAMPLES, seed=BLOCK_SEED, level=CI_LEVEL):
    """The lake-level counterpart: lakes resampled with replacement."""
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    resampled = np.array([np.median(values[rng.integers(0, len(values), len(values))]) for _ in range(n_resamples)])
    low, high = percentile_interval(resampled, level)
    return {"n": len(values), "median": float(np.median(values)), "ci_low": low, "ci_high": high}


def main():
    lakes = gpd.read_file(LAKES)
    primary = lakes[lakes["acres"] >= PRIMARY_MIN_ACRES].reset_index(drop=True)
    if len(primary) != EXPECTED_PRIMARY_N:
        sys.exit(f"stopped: primary sample has {len(primary):,} lakes, expected {EXPECTED_PRIMARY_N:,}")
    versions = read_dims_versions()
    if versions["planned"]["objectid"].tolist() != primary["objectid"].tolist():
        sys.exit("stopped: results/primary/dims.csv does not hold the primary lakes in order")
    centroids = primary.geometry.centroid
    x, y = centroids.x.to_numpy(), centroids.y.to_numpy()
    source = versions["planned"]["source_group"]

    samples = {"primary": np.ones(len(primary), dtype=bool), f"{WITHIN_SOURCE_GROUP} only": (source == WITHIN_SOURCE_GROUP).to_numpy()}
    groups = {group: (source == group).to_numpy() for group in GROUP_ORDER}

    counts = []
    for size in BLOCK_SIZES_KM:
        for name, mask in {**samples, **groups}.items():
            counts.append({"block_km": size, "sample": name, **block_counts(block_ids(x[mask], y[mask], size * 1000.0))})
    pd.DataFrame(counts).to_csv(OUT_DIR / "blocks_counts.csv", index=False)
    print(pd.DataFrame(counts).to_string(index=False), flush=True)

    rho_rows, median_rows = [], []
    for version, dims in versions.items():
        for sample, mask in samples.items():
            lake_level = pd.read_csv(LAKE_LEVEL_DIRS[version] / RHO_FILES[sample]).set_index(["window", "measure"])
            for window in WINDOWS:
                for measure, column in MEASURES.items():
                    keys = {"dims": version, "sample": sample, "window": window, "measure": measure}
                    lake = lake_level.loc[(window, measure)]
                    rho_rows.append(
                        {**keys, "n": int(lake["n"]), "rho": lake["rho"], "interval": "lake", "block_km": np.nan,
                         "n_blocks": np.nan, "ci_low": lake["ci_low"], "ci_high": lake["ci_high"]}
                    )
                    for size in BLOCK_SIZES_KM:
                        ids = block_ids(x[mask], y[mask], size * 1000.0)
                        block = spearman_block_ci(dims.loc[mask, f"dim_{window}"], dims.loc[mask, column], ids)
                        if not np.isclose(block["rho"], lake["rho"], rtol=0, atol=1e-12) or block["n"] != lake["n"]:
                            sys.exit(f"stopped: rho differs from the planned file for {keys}")
                        rho_rows.append(
                            {**keys, "n": block["n"], "rho": block["rho"], "interval": "block", "block_km": size,
                             "n_blocks": block["n_blocks"], "ci_low": block["ci_low"], "ci_high": block["ci_high"]}
                        )
            print(f"rho intervals done: {version}, {sample}", flush=True)
        for group, mask in groups.items():
            values = dims.loc[mask, f"dim_{PRIMARY_WINDOW}"]
            keys = {"dims": version, "group": group, "window": PRIMARY_WINDOW}
            lake = median_lake_ci(values)
            median_rows.append({**keys, **lake, "interval": "lake", "block_km": np.nan, "n_blocks": np.nan})
            for size in BLOCK_SIZES_KM:
                block = median_block_ci(values, block_ids(x[mask], y[mask], size * 1000.0))
                median_rows.append({**keys, **block, "interval": "block", "block_km": size})
    columns = ["dims", "group", "window", "n", "median", "interval", "block_km", "n_blocks", "ci_low", "ci_high"]
    pd.DataFrame(rho_rows).to_csv(OUT_DIR / "blocks_rho.csv", index=False)
    pd.DataFrame(median_rows)[columns].to_csv(OUT_DIR / "blocks_medians.csv", index=False)
    pd.DataFrame(
        [
            *[(f"block_km_{i + 1}", size) for i, size in enumerate(BLOCK_SIZES_KM)],
            ("block_resamples", BLOCK_RESAMPLES),
            ("block_seed", BLOCK_SEED),
            ("ci_level_percent", CI_LEVEL * 100),
            ("grid_origin_x_m", 0.0),
            ("grid_origin_y_m", 0.0),
        ],
        columns=["parameter", "value"],
    ).to_csv(OUT_DIR / "blocks_parameters.csv", index=False)
    print(f"wrote block bootstrap results to {OUT_DIR.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
