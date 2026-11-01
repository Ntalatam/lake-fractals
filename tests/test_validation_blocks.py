"""Tests for src/validation_blocks.py (post-hoc check, not in the analysis plan)."""

import numpy as np
import pytest

from primary_analysis import spearman_with_ci
from validation_blocks import (
    BLOCK_RESAMPLES,
    BLOCK_SEED,
    BLOCK_SIZES_KM,
    block_counts,
    block_ids,
    block_members,
    block_resample,
    median_block_ci,
    median_lake_ci,
    spearman_block_ci,
)


def test_settings():
    assert BLOCK_SIZES_KM == [25, 50, 100]
    assert BLOCK_RESAMPLES == 2000
    assert BLOCK_SEED == 0


def test_block_ids_put_centroids_in_squares_anchored_at_the_crs_origin():
    x = np.array([0.0, 24_999.0, 25_001.0, -1.0, 10.0])
    y = np.array([0.0, 10.0, 10.0, 0.0, 25_000.0])
    ids = block_ids(x, y, 25_000.0)
    assert ids[0] == ids[1]
    assert len({ids[0], ids[2], ids[3], ids[4]}) == 4


def test_block_counts_report_blocks_and_lakes_per_block():
    ids = np.array([0, 0, 0, 1, 2, 2])
    counts = block_counts(ids)
    assert counts == {
        "n_lakes": 6,
        "n_blocks": 3,
        "lakes_per_block_min": 1,
        "lakes_per_block_median": 2.0,
        "lakes_per_block_mean": 2.0,
        "lakes_per_block_max": 3,
    }


def test_block_resample_draws_whole_blocks_as_many_times_as_there_are_blocks():
    ids = np.array([0, 0, 0, 1, 2, 2, 3])
    members = block_members(ids)
    rng = np.random.default_rng(0)
    for _ in range(50):
        index = block_resample(members, rng)
        times = np.bincount(index, minlength=len(ids))
        # every lake of a block is drawn the same number of times
        for block in members:
            assert len(set(times[block])) == 1
        assert sum(times[block[0]] for block in members) == len(members)


def test_spearman_block_ci_brackets_rho_and_depends_only_on_the_seed():
    rng = np.random.default_rng(1)
    x = rng.normal(size=300)
    y = x + rng.normal(size=300)
    ids = rng.integers(0, 60, 300)
    first = spearman_block_ci(x, y, ids, n_resamples=300, seed=0)
    again = spearman_block_ci(x, y, ids, n_resamples=300, seed=0)
    other = spearman_block_ci(x, y, ids, n_resamples=300, seed=1)
    assert first["ci_low"] < first["rho"] < first["ci_high"]
    assert first == again
    assert (first["ci_low"], first["ci_high"]) != (other["ci_low"], other["ci_high"])
    assert first["n_blocks"] == len(np.unique(ids))
    assert first["n"] == 300


def clustered_lakes(seed=0, n_clusters=20, per_cluster=25):
    """Lakes in tight clusters far apart, with values shared within each cluster."""
    rng = np.random.default_rng(seed)
    centers = rng.uniform(0, 1_000_000, (n_clusters, 2))
    cluster = np.repeat(np.arange(n_clusters), per_cluster)
    xy = centers[cluster] + rng.normal(0, 1_000, (len(cluster), 2))
    shared_x = rng.normal(size=n_clusters)
    shared_y = 0.5 * shared_x + rng.normal(size=n_clusters)
    x = shared_x[cluster] + 0.05 * rng.normal(size=len(cluster))
    y = shared_y[cluster] + 0.05 * rng.normal(size=len(cluster))
    return xy, x, y


def test_spatially_correlated_values_give_wider_block_intervals_than_lake_intervals():
    xy, x, y = clustered_lakes()
    ids = block_ids(xy[:, 0], xy[:, 1], 25_000.0)
    block = spearman_block_ci(x, y, ids, n_resamples=500, seed=0)
    lake = spearman_with_ci(x, y, n_resamples=500, seed=0)
    assert block["rho"] == pytest.approx(lake["rho"])
    assert (block["ci_high"] - block["ci_low"]) > 2 * (lake["ci_high"] - lake["ci_low"])


def test_independent_values_give_similar_block_and_lake_intervals():
    rng = np.random.default_rng(2)
    xy = rng.uniform(0, 1_000_000, (500, 2))
    x = rng.normal(size=500)
    y = 0.5 * x + rng.normal(size=500)
    ids = block_ids(xy[:, 0], xy[:, 1], 100_000.0)
    block = spearman_block_ci(x, y, ids, n_resamples=500, seed=0)
    lake = spearman_with_ci(x, y, n_resamples=500, seed=0)
    ratio = (block["ci_high"] - block["ci_low"]) / (lake["ci_high"] - lake["ci_low"])
    assert 0.7 < ratio < 1.4


def test_median_intervals_are_seeded_and_bracket_the_median():
    rng = np.random.default_rng(3)
    values = 1 + rng.uniform(0, 0.1, 200)
    ids = rng.integers(0, 40, 200)
    block = median_block_ci(values, ids, n_resamples=300, seed=0)
    lake = median_lake_ci(values, n_resamples=300, seed=0)
    assert block["median"] == lake["median"] == np.median(values)
    assert block["ci_low"] <= block["median"] <= block["ci_high"]
    assert lake["ci_low"] <= lake["median"] <= lake["ci_high"]
    assert block == median_block_ci(values, ids, n_resamples=300, seed=0)
    assert lake == median_lake_ci(values, n_resamples=300, seed=0)
