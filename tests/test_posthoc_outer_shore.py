"""Tests for src/posthoc_outer_shore.py (post-hoc exploratory check)."""

import pandas as pd
import pytest
from shapely.geometry import MultiPolygon, Point, Polygon, box

from posthoc_outer_shore import (
    WINDOWS_USED,
    exterior_only,
    interior_ring_count,
    more_than_1pct_shorter,
    read_posthoc_csv,
    write_posthoc_csv,
)
from primary_analysis import lake_dimensions


def square_with_island():
    # 1,000 m square lake with a 100 m square island: 4,000 m outer shore + 400 m island shore
    return Polygon(box(0, 0, 1000, 1000).exterior.coords, [box(400, 400, 500, 500).exterior.coords])


def test_exterior_only_removes_island_shorelines():
    lake = square_with_island()
    assert lake.length == pytest.approx(4400.0)
    outer = exterior_only(lake)
    assert len(outer.interiors) == 0
    assert outer.length == pytest.approx(4000.0)


def test_exterior_only_keeps_every_part_of_a_multipolygon():
    lake = MultiPolygon([square_with_island(), box(2000, 0, 2500, 500)])
    outer = exterior_only(lake)
    assert outer.geom_type == "MultiPolygon"
    assert outer.length == pytest.approx(4000.0 + 2000.0)


def test_interior_ring_count_covers_polygons_and_multipolygons():
    two_islands = Polygon(
        box(0, 0, 1000, 1000).exterior.coords,
        [box(100, 100, 200, 200).exterior.coords, box(600, 600, 700, 700).exterior.coords],
    )
    assert interior_ring_count(two_islands) == 2
    assert interior_ring_count(box(0, 0, 10, 10)) == 0
    assert interior_ring_count(MultiPolygon([square_with_island(), two_islands])) == 3
    assert interior_ring_count(exterior_only(two_islands)) == 0


def test_more_than_1pct_shorter_is_strict():
    exterior = pd.Series([98.0, 99.0, 99.5, 100.0])
    shoreline = pd.Series([100.0] * 4)
    assert list(more_than_1pct_shorter(exterior, shoreline)) == [True, False, False, False]


def test_outer_shore_dimension_equals_the_full_dimension_without_islands():
    lake = Point(0, 0).buffer(1000.0, quad_segs=256)
    outer = lake_dimensions(exterior_only(lake), WINDOWS_USED)
    full = lake_dimensions(lake, WINDOWS_USED)
    assert (outer["dim_20_100"], outer["r2_20_100"]) == (full["dim_20_100"], full["r2_20_100"])


def test_outer_shore_dimension_ignores_an_island():
    outer_shore = Point(0, 0).buffer(1000.0, quad_segs=256)
    island = Point(0, 0).buffer(300.0, quad_segs=256)
    lake = Polygon(outer_shore.exterior.coords, [island.exterior.coords])
    assert interior_ring_count(lake) == 1
    with_island = lake_dimensions(lake, WINDOWS_USED)["dim_20_100"]
    outer_only = lake_dimensions(exterior_only(lake), WINDOWS_USED)["dim_20_100"]
    assert outer_only == lake_dimensions(outer_shore, WINDOWS_USED)["dim_20_100"]
    assert outer_only != with_island


def test_check_uses_the_primary_window_only():
    assert list(WINDOWS_USED) == ["20_100"]
    assert (WINDOWS_USED["20_100"][0], WINDOWS_USED["20_100"][-1], len(WINDOWS_USED["20_100"])) == (20.0, 100.0, 8)


def test_posthoc_csv_starts_with_a_post_hoc_line_and_reads_back(tmp_path):
    frame = pd.DataFrame({"objectid": [1, 2], "rho": [0.5, -0.25]})
    path = tmp_path / "post-hoc_test.csv"
    write_posthoc_csv(frame, path, "test table")
    assert path.read_text().splitlines()[0].startswith("# post-hoc")
    pd.testing.assert_frame_equal(read_posthoc_csv(path), frame)


def test_posthoc_csv_refuses_a_filename_without_post_hoc(tmp_path):
    with pytest.raises(ValueError):
        write_posthoc_csv(pd.DataFrame({"a": [1]}), tmp_path / "outer_shore.csv", "test table")
