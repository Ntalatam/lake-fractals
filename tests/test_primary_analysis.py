"""Tests for src/primary_analysis.py on small synthetic inputs."""

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from scipy.stats import kruskal
from shapely.geometry import Point

from primary_analysis import (
    OTHER,
    PRIMARY_WINDOW,
    WINDOWS,
    LakeTooSlow,
    compute_dimensions,
    decision_rule,
    lake_dimensions,
    rho_table,
    source_comparison,
    source_group,
    spearman_with_ci,
)

CRS = "EPSG:26915"


def test_three_windows_with_8_log_spaced_sizes_each():
    bounds = {name: (sizes[0], sizes[-1], len(sizes)) for name, sizes in WINDOWS.items()}
    assert bounds == {"20_100": (20.0, 100.0, 8), "10_100": (10.0, 100.0, 8), "20_200": (20.0, 200.0, 8)}
    assert PRIMARY_WINDOW == "20_100"
    for sizes in WINDOWS.values():
        assert np.allclose(np.diff(np.log(sizes)), np.log(sizes[-1] / sizes[0]) / 7)


def test_source_groups_keep_four_values_and_pool_the_rest_into_other():
    values = pd.Series(["2004 FSA", "ORIG DLG", "DNR 24k POLYS", "PWI", "2010 FSA", "1991 DOQ", None])
    groups = source_group(values)
    assert list(groups[:6]) == ["2004 FSA", "ORIG DLG", "DNR 24k POLYS", "PWI", OTHER, OTHER]
    assert pd.isna(groups[6])  # a missing source stays missing, it is not "other"


def test_spearman_ci_is_exact_for_a_perfectly_monotone_relation():
    x = np.arange(50.0)
    result = spearman_with_ci(x, -(x**2), n_resamples=200, seed=0)
    assert result["n"] == 50
    assert result["rho"] == pytest.approx(-1.0)
    assert result["ci_low"] == pytest.approx(-1.0)
    assert result["ci_high"] == pytest.approx(-1.0)


def test_spearman_ci_brackets_rho_and_depends_only_on_the_seed():
    rng = np.random.default_rng(1)
    x = rng.normal(size=300)
    y = x + rng.normal(size=300)
    first = spearman_with_ci(x, y, n_resamples=500, seed=0)
    again = spearman_with_ci(x, y, n_resamples=500, seed=0)
    other_seed = spearman_with_ci(x, y, n_resamples=500, seed=1)
    assert first["ci_low"] < first["rho"] < first["ci_high"]
    assert (first["ci_low"], first["ci_high"]) == (again["ci_low"], again["ci_high"])
    assert (first["ci_low"], first["ci_high"]) != (other_seed["ci_low"], other_seed["ci_high"])
    assert 0 < first["p_value"] < 0.001


@pytest.mark.parametrize(
    "rhos, holds, direction, outcome",
    [
        ([-0.3, -0.1, -0.5], True, "negative", "supported"),
        ([0.2, 0.01, 0.4], True, "positive", "supported"),
        ([-0.3, 0.1, -0.5], False, "mixed", "window-dependent"),
        ([-0.3, 0.0, -0.5], False, "mixed", "window-dependent"),
    ],
)
def test_decision_rule_needs_the_same_sign_in_all_three_windows(rhos, holds, direction, outcome):
    result = decision_rule(dict(zip(WINDOWS, rhos)))
    assert result == {"direction_holds": holds, "direction": direction, "outcome": outcome}


def test_decision_rule_refuses_fewer_than_three_windows():
    with pytest.raises(ValueError):
        decision_rule({"20_100": -0.3, "10_100": -0.1})


def synthetic_dims():
    return pd.DataFrame(
        {
            "acres": [100.0, 200, 300, 400, 500, 600],
            "shoreline_m": [3000.0, 2000, 6000, 5000, 9000, 8000],
            "dim_20_100": [1.01, 1.02, 1.03, 1.04, 1.05, 1.06],  # rises with acres
            "dim_10_100": [1.06, 1.05, 1.04, 1.03, 1.02, 1.01],  # falls with acres
            "dim_20_200": [1.01, 1.02, 1.03, 1.04, 1.05, 1.06],
        }
    )


def test_rho_table_has_one_row_per_window_and_measure():
    table = rho_table(synthetic_dims(), sample="test", n_resamples=100, seed=0)
    assert len(table) == 6
    assert set(zip(table["window"], table["measure"])) == {(w, m) for w in WINDOWS for m in ["area", "shoreline"]}
    assert (table["n"] == 6).all() and (table["sample"] == "test").all()
    rows = table.set_index(["window", "measure"])
    assert rows.loc[("20_100", "area"), "rho"] == pytest.approx(1.0)
    assert rows.loc[("10_100", "area"), "rho"] == pytest.approx(-1.0)
    # shoreline ranks 2,1,4,3,6,5 against dimension ranks 1..6: rho = 1 - 6*6/210
    assert rows.loc[("20_100", "shoreline"), "rho"] == pytest.approx(1 - 36 / 210)
    assert rows.loc[("20_100", "area"), "window_min_m"] == 20.0
    assert rows.loc[("20_200", "area"), "window_max_m"] == 200.0


def test_source_comparison_excludes_missing_sources_and_reports_medians():
    dims = pd.DataFrame(
        {
            "source_group": ["2004 FSA"] * 3 + ["PWI"] * 3 + [OTHER] * 3 + [None, None],
            "dim_20_100": [1.01, 1.02, 1.03, 1.10, 1.11, 1.12, 1.05, 1.06, 1.07, 1.50, 1.60],
        }
    )
    groups, test = source_comparison(dims, window="20_100")
    expected = kruskal([1.01, 1.02, 1.03], [1.10, 1.11, 1.12], [1.05, 1.06, 1.07])
    assert test["n_excluded_missing"] == 2
    assert test["n_lakes"] == 9
    assert test["n_groups"] == 3
    assert test["H"] == pytest.approx(expected.statistic)
    assert test["p_value"] == pytest.approx(expected.pvalue)
    by_group = groups.set_index("group")
    assert by_group.loc["PWI", "n"] == 3
    assert by_group.loc["PWI", "median_dim"] == pytest.approx(1.11)


def circle(radius=1000.0):
    return Point(0, 0).buffer(radius, quad_segs=256)


def test_lake_dimensions_returns_dim_r2_and_runtime_for_each_window():
    result = lake_dimensions(circle())
    for name in WINDOWS:
        assert abs(result[f"dim_{name}"] - 1.0) < 0.05
        assert 0.99 < result[f"r2_{name}"] <= 1.0
    assert result["runtime_s"] > 0


def two_lakes():
    # objectids out of order and lakes of different size, so input order matters
    return gpd.GeoDataFrame({"objectid": [7, 3]}, geometry=[circle(500.0), circle(2000.0)], crs=CRS)


def test_compute_dimensions_keeps_input_order_in_parallel():
    serial = compute_dimensions(two_lakes(), workers=1)
    parallel = compute_dimensions(two_lakes(), workers=2)
    assert list(parallel["objectid"]) == [7, 3]
    columns = [f"{kind}_{name}" for name in WINDOWS for kind in ("dim", "r2")]
    pd.testing.assert_frame_equal(serial[columns], parallel[columns])


@pytest.mark.parametrize("workers", [1, 2])
def test_compute_dimensions_stops_when_a_lake_exceeds_the_time_limit(workers):
    with pytest.raises(LakeTooSlow):
        compute_dimensions(two_lakes(), workers=workers, max_seconds=0.0)


def test_lake_dimensions_default_point_spacing_is_the_planned_0_1():
    default = lake_dimensions(circle())
    explicit = lake_dimensions(circle(), densify_fraction=0.1)
    for name in WINDOWS:
        assert (default[f"dim_{name}"], default[f"r2_{name}"]) == (explicit[f"dim_{name}"], explicit[f"r2_{name}"])


@pytest.mark.parametrize("workers", [1, 2])
def test_compute_dimensions_passes_the_point_spacing_to_every_lake(workers):
    columns = [f"{kind}_{name}" for name in WINDOWS for kind in ("dim", "r2")]
    fine = compute_dimensions(two_lakes(), workers=workers, densify_fraction=0.01)
    expected = pd.DataFrame([lake_dimensions(g, densify_fraction=0.01) for g in two_lakes().geometry])
    pd.testing.assert_frame_equal(fine[columns], expected[columns])
    planned = compute_dimensions(two_lakes(), workers=workers)
    assert not planned[columns].equals(fine[columns])
