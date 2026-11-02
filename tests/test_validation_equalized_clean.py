"""Tests for src/validation_equalized_clean.py (post-hoc check, not in the analysis plan)."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import kruskal
from shapely.geometry import MultiPolygon, Polygon, box

from validation_equalized_clean import (
    GAP_RESAMPLES,
    GAP_SEED,
    GAPS,
    clean_lakes,
    counts_by_group,
    gap_with_ci,
    lake_flags,
    source_statistics,
)

GROUPS = ["2004 FSA", "ORIG DLG", "DNR 24k POLYS", "PWI", "other"]


def lake(*islands):
    return Polygon(box(0, 0, 1000, 800).exterior.coords, [island.exterior.coords for island in islands])


def test_settings():
    assert GAPS == [("2004 FSA", "ORIG DLG"), ("2004 FSA", "DNR 24k POLYS")]
    assert GAP_RESAMPLES == 2000
    assert GAP_SEED == 0


def test_a_lake_the_resampling_leaves_whole_is_flagged_clean():
    # corners and island corners fall on multiples of 25 and 50 m
    flags = lake_flags(lake(box(400, 300, 600, 500)))
    assert flags == {
        "n_rings": 2,
        "rings_dropped_25m": 0,
        "valid_25m": True,
        "rings_dropped_50m": 0,
        "valid_50m": True,
    }


def test_an_island_too_short_for_4_vertices_at_50_m_is_flagged():
    # a 120 m island keeps 5 vertices at 25 m and 3 (too few) at 50 m
    flags = lake_flags(lake(box(400, 300, 600, 500), box(100, 100, 130, 130)))
    assert (flags["rings_dropped_25m"], flags["rings_dropped_50m"]) == (0, 1)
    assert flags["valid_25m"] and flags["valid_50m"]


def test_a_small_second_part_dropped_at_50_m_is_flagged():
    flags = lake_flags(MultiPolygon([box(0, 0, 1000, 800), box(2000, 0, 2030, 30)]))
    assert (flags["rings_dropped_25m"], flags["rings_dropped_50m"]) == (0, 1)


def test_a_lake_left_invalid_is_flagged():
    # at 50 m the rebuilt shore cuts the corner the island sits in, so the
    # island crosses it; at 25 m the cut is smaller and the lake stays valid
    corner_lake = Polygon(box(0, 0, 1010, 1010).exterior.coords, [box(930, 1001, 1008, 1008).exterior.coords])
    assert corner_lake.is_valid
    flags = lake_flags(corner_lake)
    assert (flags["rings_dropped_25m"], flags["rings_dropped_50m"]) == (0, 0)
    assert (flags["valid_25m"], flags["valid_50m"]) == (True, False)


def test_clean_needs_no_dropped_ring_and_a_valid_polygon_at_both_intervals():
    flags = pd.DataFrame(
        {
            "rings_dropped_25m": [0, 0, 1, 0, 0],
            "valid_25m": [True, True, True, False, True],
            "rings_dropped_50m": [0, 1, 1, 0, 0],
            "valid_50m": [True, True, True, True, False],
        }
    )
    assert clean_lakes(flags).tolist() == [True, False, False, False, False]


def test_counts_by_group():
    flags = pd.DataFrame(
        {
            "source_group": ["2004 FSA", "2004 FSA", "ORIG DLG", None, "other"],
            "clean": [True, False, True, False, True],
        }
    )
    counts = counts_by_group(flags).set_index("group")
    assert counts.loc["2004 FSA", ["n_lakes", "n_clean", "n_not_clean"]].tolist() == [2, 1, 1]
    assert counts.loc["ORIG DLG", ["n_lakes", "n_clean", "n_not_clean"]].tolist() == [1, 1, 0]
    # groups with no lakes are listed with zeros; missing sources get their own row
    assert counts.loc["PWI", ["n_lakes", "n_clean", "n_not_clean"]].tolist() == [0, 0, 0]
    assert counts.loc["no delineat_1", ["n_lakes", "n_clean", "n_not_clean"]].tolist() == [1, 0, 1]
    assert counts.loc["all lakes", ["n_lakes", "n_clean", "n_not_clean"]].tolist() == [5, 3, 2]
    assert list(counts.index) == GROUPS + ["no delineat_1", "all lakes"]


def test_gap_is_the_difference_of_group_medians():
    first, second = [1.03, 1.01, 1.05], [1.00, 1.02]
    gap = gap_with_ci(first, second, n_resamples=200)
    assert gap["median_first"] == 1.03
    assert gap["median_second"] == pytest.approx(1.01)
    assert gap["gap"] == pytest.approx(0.02)
    assert (gap["n_first"], gap["n_second"]) == (3, 2)
    assert gap["ci_low"] <= gap["gap"] <= gap["ci_high"]


def test_gap_interval_resamples_lakes_within_each_group():
    # constant groups: every resample has the same medians, so the interval
    # is a single point; pooling the groups would spread it
    gap = gap_with_ci(np.full(40, 1.03), np.full(25, 1.01), n_resamples=200)
    assert gap["ci_low"] == pytest.approx(0.02) and gap["ci_high"] == pytest.approx(0.02)


def test_gap_interval_is_seeded_and_uses_the_same_resampled_lakes_for_any_values():
    rng = np.random.default_rng(1)
    first, second = rng.normal(1.03, 0.02, 60), rng.normal(1.01, 0.02, 40)
    one = gap_with_ci(first, second, n_resamples=300)
    assert gap_with_ci(first, second, n_resamples=300) == one
    # shifting both groups by the same amount leaves every resampled gap, and
    # so the interval, unchanged only if the same lakes are drawn
    shifted = gap_with_ci(first + 0.5, second + 0.5, n_resamples=300)
    assert shifted["ci_low"] == pytest.approx(one["ci_low"], abs=1e-12)
    assert shifted["ci_high"] == pytest.approx(one["ci_high"], abs=1e-12)
    assert one["ci_low"] < one["gap"] < one["ci_high"]


def test_source_statistics():
    rng = np.random.default_rng(0)
    centers = dict(zip(GROUPS, [1.04, 1.01, 1.00, 1.06, 1.03]))
    groups = np.repeat(GROUPS, [30, 20, 15, 9, 25]).tolist() + [None, None]
    values = np.array([centers[g] for g in groups[:-2]] + [2.0, 2.0]) + rng.normal(0, 0.005, len(groups))
    medians, gaps, spread, test = source_statistics(pd.Series(groups), pd.Series(values), n_resamples=200)

    known = pd.DataFrame({"group": groups, "value": values}).dropna()
    expected = known.groupby("group")["value"].median()
    assert medians.set_index("group")["median_dim"].to_dict() == pytest.approx(expected.to_dict())
    assert medians.set_index("group")["n"].to_dict() == {"2004 FSA": 30, "ORIG DLG": 20, "DNR 24k POLYS": 15, "PWI": 9, "other": 25}

    gaps = gaps.set_index("second")
    assert gaps.loc["ORIG DLG", "gap"] == pytest.approx(expected["2004 FSA"] - expected["ORIG DLG"])
    assert gaps.loc["DNR 24k POLYS", "gap"] == pytest.approx(expected["2004 FSA"] - expected["DNR 24k POLYS"])
    assert set(gaps["first"]) == {"2004 FSA"}

    assert spread["spread"] == pytest.approx(expected.max() - expected.min())
    assert (spread["largest_group"], spread["smallest_group"]) == (expected.idxmax(), expected.idxmin())

    # the lakes with no delineat_1 are left out, as in the planned comparison
    statistic = kruskal(*[known.loc[known["group"] == g, "value"] for g in GROUPS]).statistic
    assert test["H"] == pytest.approx(statistic)
    assert (test["n_lakes"], test["n_excluded_missing"]) == (99, 2)
