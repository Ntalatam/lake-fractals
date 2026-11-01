"""Tests for the data handling in src/paper_figures.py on small synthetic inputs."""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from paper_figures import lake_points, rho_label, rho_row

CRS = "EPSG:26915"


def rho_table():
    # distinct values per row, so picking the wrong row changes the answer
    return pd.DataFrame(
        {
            "window": ["20_100", "20_100", "10_100"],
            "window_min_m": [20.0, 20.0, 10.0],
            "window_max_m": [100.0, 100.0, 100.0],
            "measure": ["area", "shoreline", "shoreline"],
            "n": [3274, 3274, 3274],
            "rho": [-0.004787785, 0.40987724, 0.42610644],
            "ci_low": [-0.03877494, 0.38056463, 0.39745898],
            "ci_high": [0.02911421, 0.43813044, 0.45366163],
        }
    )


def test_rho_row_picks_the_measure_in_the_primary_window():
    assert rho_row(rho_table(), "shoreline")["rho"] == pytest.approx(0.40987724)
    assert rho_row(rho_table(), "area")["rho"] == pytest.approx(-0.004787785)
    assert rho_row(rho_table(), "shoreline", window="10_100")["rho"] == pytest.approx(0.42610644)


def test_rho_row_refuses_a_missing_or_repeated_row():
    with pytest.raises(ValueError):
        rho_row(rho_table(), "area", window="10_100")
    repeated = pd.concat([rho_table(), rho_table().iloc[[0]]])
    with pytest.raises(ValueError):
        rho_row(repeated, "area")


def test_rho_label_rounds_like_the_summary():
    label = rho_label(rho_row(rho_table(), "area"), ci_level_percent=95.0)
    assert label == "Spearman ρ = -0.0048 (95% CI -0.0388 to 0.0291), n = 3,274"


def lakes():
    # three square lakes far apart, objectids out of order
    return gpd.GeoDataFrame(
        {"objectid": [30, 10, 20]},
        geometry=[box(0, 0, 1000, 1000), box(5000, 0, 6000, 1000), box(0, 5000, 1000, 6000)],
        crs=CRS,
    )


def test_lake_points_joins_each_lake_to_its_own_dimension():
    dims = pd.DataFrame({"objectid": [20, 30], "dim_20_100": [1.2, 1.05]})
    points = lake_points(lakes(), dims)
    assert len(points) == 2
    polygons = lakes().set_index("objectid").geometry
    by_id = points.set_index("objectid")
    for objectid, dimension in [(20, 1.2), (30, 1.05)]:
        assert by_id.loc[objectid, "dim_20_100"] == dimension
        assert polygons[objectid].contains(by_id.geometry[objectid])
    assert points.crs == CRS


def test_lake_points_stops_if_a_lake_in_dims_has_no_polygon():
    dims = pd.DataFrame({"objectid": [20, 99], "dim_20_100": [1.2, 1.0]})
    with pytest.raises(ValueError):
        lake_points(lakes(), dims)
