"""Tests for src/validation_width_exclusion.py (post-hoc check, not in the analysis plan)."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

from primary_analysis import WINDOWS
from validation_width_exclusion import (
    MIN_INSCRIBED_DIAMETER_M,
    diameter_rho,
    exclusion_counts,
    width_exclusion,
)


def random_lakes(n=80, seed=0):
    rng = np.random.default_rng(seed)
    dims = pd.DataFrame(
        {
            "objectid": np.arange(n),
            "acres": rng.uniform(100, 1000, n),
            "shoreline_m": rng.uniform(2000, 9000, n),
            **{f"dim_{w}": 1 + rng.uniform(0, 0.1, n) for w in WINDOWS},
        }
    )
    # 20 lakes narrower than 400 m, one exactly 400 m wide (kept), the rest wider
    diameter = np.r_[rng.uniform(150, 399.9, 20), 400.0, rng.uniform(400.1, 3000, n - 21)]
    return dims, pd.DataFrame({"objectid": np.arange(n), "inscribed_diameter_m": diameter})


def ranked_lakes(direction_20_200):
    # 40 wide lakes whose estimate rises with size in every window (or falls in
    # 20_200 when direction_20_200 is -1), and 10 narrow lakes, the largest,
    # whose estimate falls with size
    wide = np.arange(1, 41, dtype=float)
    narrow = np.arange(41, 51, dtype=float)
    acres = np.r_[wide, narrow] * 100
    trend = np.r_[wide, -narrow] / 1000
    dims = pd.DataFrame(
        {
            "objectid": np.arange(50),
            "acres": acres,
            "shoreline_m": acres * 10,
            "dim_20_100": 1 + trend,
            "dim_10_100": 1 + trend,
            "dim_20_200": 1 + direction_20_200 * trend,
        }
    )
    width = pd.DataFrame({"objectid": np.arange(50), "inscribed_diameter_m": np.r_[np.full(40, 1000.0), np.full(10, 300.0)]})
    return dims, width


def test_cutoff_is_twice_the_largest_box_of_the_20_200_m_window():
    assert MIN_INSCRIBED_DIAMETER_M == 400.0
    assert MIN_INSCRIBED_DIAMETER_M == 2 * WINDOWS["20_200"][-1]


def test_drops_the_same_narrow_lakes_in_every_window():
    dims, width = random_lakes()
    rho, rules = width_exclusion(dims, width, n_resamples=50)
    assert len(rho) == 6
    assert set(zip(rho["window"], rho["measure"])) == {(w, m) for w in WINDOWS for m in ["area", "shoreline"]}
    # the lake exactly 400 m wide is not narrower than 400 m, so it stays
    assert set(rho["n"]) == {60}
    assert set(rho["n_excluded"]) == {20}
    assert set(rules["measure"]) == {"area", "shoreline"}


def test_rho_is_spearman_on_the_kept_lakes():
    dims, width = random_lakes()
    rho, _ = width_exclusion(dims, width, n_resamples=50)
    kept = dims[width["inscribed_diameter_m"] >= 400.0]
    rows = rho.set_index(["window", "measure"])
    for window in WINDOWS:
        for measure, column in [("area", "acres"), ("shoreline", "shoreline_m")]:
            row = rows.loc[(window, measure)]
            assert row["rho"] == pytest.approx(spearmanr(kept[f"dim_{window}"], kept[column]).statistic)
            assert row["ci_low"] <= row["rho"] <= row["ci_high"]


@pytest.mark.parametrize("direction, outcome", [(1, "supported"), (-1, "window-dependent")])
def test_decision_rule_uses_only_the_kept_lakes(direction, outcome):
    dims, width = ranked_lakes(direction)
    rho, rules = width_exclusion(dims, width, n_resamples=50)
    assert set(rho["n"]) == {40}
    assert rho.loc[rho["window"] != "20_200", "rho"].tolist() == pytest.approx([1.0] * 4)
    assert rho.loc[rho["window"] == "20_200", "rho"].tolist() == pytest.approx([float(direction)] * 2)
    assert rules.set_index("measure")["outcome"].to_dict() == {"area": outcome, "shoreline": outcome}


def test_every_lake_needs_a_finite_diameter():
    dims, width = random_lakes()
    with pytest.raises(ValueError):
        width_exclusion(dims, width.iloc[1:], n_resamples=10)
    with pytest.raises(ValueError):
        diameter_rho(dims, width.iloc[1:], n_resamples=10)
    width.loc[0, "inscribed_diameter_m"] = np.nan
    with pytest.raises(ValueError):
        width_exclusion(dims, width, n_resamples=10)
    with pytest.raises(ValueError):
        diameter_rho(dims, width, n_resamples=10)


def test_diameter_rho_uses_every_lake_in_each_window():
    dims, width = random_lakes()
    table = diameter_rho(dims, width, n_resamples=50).set_index("window")
    assert list(table.index) == list(WINDOWS)
    assert set(table["n"]) == {80}
    for window in WINDOWS:
        expected = spearmanr(width["inscribed_diameter_m"], dims[f"dim_{window}"]).statistic
        assert table.loc[window, "rho"] == pytest.approx(expected)
        assert table.loc[window, "ci_low"] <= table.loc[window, "rho"] <= table.loc[window, "ci_high"]


def test_counts():
    width = pd.DataFrame({"objectid": range(7), "inscribed_diameter_m": [100, 397.9, 398.0, 399.5, 400.0, 401, 1000]})
    counts = exclusion_counts(width).iloc[0]
    assert counts["n_lakes"] == 7
    assert counts["n_excluded"] == 4
    assert counts["n_kept"] == 3
    assert counts["percent_excluded"] == pytest.approx(400 / 7)
    # computed diameters are at most 2 m short (1 m inscribed-circle
    # tolerance on the radius): 398.0 and 399.5 could be 400 m or wider
    assert counts["n_excluded_within_tolerance"] == 2
