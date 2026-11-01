"""Tests for src/filter_lakes.py on a small synthetic table."""

import geopandas as gpd
import pytest
from shapely.geometry import box

from filter_lakes import filter_lakes

CRS = "EPSG:26915"


def lakes():
    big = box(0, 0, 500, 500)  # 2,000 m shoreline
    small = box(0, 0, 200, 200)  # 800 m shoreline
    return gpd.GeoDataFrame(
        {
            "objectid": [1, 2, 3, 4, 5, 6, 7, 8],
            "wb_class": ["Lake or Pond", "Reservoir"] + ["Lake or Pond"] * 6,
            "acres": [50.0, 50.0, 5.0, 10.0, 50.0, 50.0, 50.0, 50.0],
            "delineat_1": ["PWI", "PWI", "PWI", "ORIG DLG", None, "2004 FSA", "PWI", "PWI"],
            "dowlknum": ["a", "b", "c", "d", "e", "f", "g", "h"],
            # Y = outside Minnesota, B = on the border, N = inside, None = blank
            "outside_mn": ["N", "N", "N", None, "N", "N", "Y", "B"],
            "geometry": [big, big, big, big, None, small, big, big],
        },
        crs=CRS,
    )


def test_steps_run_in_order_with_counts_before_and_after():
    _, log = filter_lakes(lakes())
    assert list(log["step"]) == [1, 2, 3, 4, 5]
    assert list(log["count_before"]) == [8, 7, 6, 5, 4]
    assert list(log["count_after"]) == [7, 6, 5, 4, 2]
    assert list(log["dropped"]) == [1, 1, 1, 1, 2]


def test_keeps_only_lakes_passing_every_step():
    result, _ = filter_lakes(lakes())
    # 10 acres exactly is kept, and a blank outside_mn is not dropped
    assert list(result["objectid"]) == [1, 4]


def test_keeps_delineat_1_acres_and_shoreline_in_meters():
    result, _ = filter_lakes(lakes())
    assert {"delineat_1", "acres", "shoreline_m"} <= set(result.columns)
    assert result["shoreline_m"].iloc[0] == pytest.approx(2000.0)
    assert result.crs == CRS


def test_shoreline_is_measured_in_utm_meters_even_if_input_is_not():
    result, _ = filter_lakes(lakes().to_crs("EPSG:4326"))
    assert result["shoreline_m"].iloc[0] == pytest.approx(2000.0, rel=1e-3)
