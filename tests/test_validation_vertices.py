"""Tests for src/validation_vertices.py (post-hoc check, not in the analysis plan)."""

import numpy as np
import pandas as pd
import pytest
import shapely
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box

from boxcount import box_count_dimension
from primary_analysis import PRIMARY_WINDOW, WINDOWS
from validation_vertices import (
    EQUALIZED_FRACTIONS,
    INTERVALS_M,
    MAX_WALL_SECONDS,
    MIN_RING_VERTICES,
    PARTS,
    WORKERS,
    parse_parts,
    resample_lake,
    resample_ring,
    spacing_by_group,
    vertex_spacing,
)


def test_settings():
    assert INTERVALS_M == [25.0, 50.0]
    assert MIN_RING_VERTICES == 4
    assert EQUALIZED_FRACTIONS == [0.1, 0.01]
    assert WORKERS == 4
    assert MAX_WALL_SECONDS == 3 * 60 * 60


def test_parts_can_be_run_alone():
    # the vertex spacing tables take seconds and the equalized resampling
    # about half an hour, so each can be run without the other
    assert PARTS == ["vertices", "equalized"]
    assert parse_parts([]) == PARTS
    assert parse_parts(["vertices"]) == ["vertices"]
    assert parse_parts(["equalized", "vertices"]) == PARTS
    with pytest.raises(SystemExit):
        parse_parts(["calibration"])


def test_vertex_spacing_of_a_square():
    spacing = vertex_spacing(MultiPolygon([box(0, 0, 100, 100)]))
    assert spacing["n_rings"] == 1
    assert spacing["n_segments"] == 4
    assert spacing["median_spacing_m"] == 100.0
    assert spacing["p90_spacing_m"] == 100.0


def test_vertex_spacing_pools_every_ring_of_every_part():
    # outer square: 4 segments of 1,000 m; island: 4 of 10 m; second part: 4 of 100 m
    lake = Polygon(box(0, 0, 1000, 1000).exterior.coords, [box(400, 400, 410, 410).exterior.coords])
    spacing = vertex_spacing(MultiPolygon([lake, box(2000, 0, 2100, 100)]))
    assert spacing["n_rings"] == 3
    assert spacing["n_segments"] == 12
    assert spacing["median_spacing_m"] == 100.0
    assert spacing["p90_spacing_m"] == 1000.0
    assert spacing["n_zero_segments"] == 0


def test_vertex_spacing_counts_repeated_vertices():
    ring = [(0, 0), (100, 0), (100, 0), (100, 100), (0, 100), (0, 0)]
    spacing = vertex_spacing(MultiPolygon([Polygon(ring)]))
    assert spacing["n_segments"] == 5
    assert spacing["n_zero_segments"] == 1


def test_square_resampled_at_25_m_has_vertices_25_m_apart():
    points = resample_ring(box(0, 0, 100, 100).exterior, 25.0)
    assert len(points) == 16
    closed = np.vstack([points, points[:1]])
    assert np.allclose(np.hypot(*np.diff(closed, axis=0).T), 25.0)


def test_resampling_keeps_the_ring_start_point_and_steps_along_the_ring():
    ring = Point(3, 7).buffer(500.0, quad_segs=64).exterior
    points = resample_ring(ring, 50.0)
    assert tuple(points[0]) == ring.coords[0]
    along = shapely.line_locate_point(LineString(ring.coords), shapely.points(points))
    assert np.allclose(along, np.arange(len(points)) * 50.0)
    assert along[-1] < ring.length


def test_rings_too_short_for_4_vertices_are_dropped_and_logged():
    # 30 m square island: 120 m of shore keeps 5 vertices at 25 m, 3 at 50 m
    lake = Polygon(box(0, 0, 1000, 1000).exterior.coords, [box(400, 400, 430, 430).exterior.coords])
    at_25, log_25 = resample_lake(MultiPolygon([lake]), 25.0)
    at_50, log_50 = resample_lake(MultiPolygon([lake]), 50.0)
    assert len(at_25.geoms[0].interiors) == 1
    assert (log_25["n_rings"], log_25["n_rings_dropped"]) == (2, 0)
    assert len(at_50.geoms[0].interiors) == 0
    assert (log_50["n_rings"], log_50["n_rings_dropped"], log_50["n_rings_dropped_3_vertices"]) == (2, 1, 1)
    assert log_50["dropped_length_m"] == pytest.approx(120.0)


@pytest.mark.parametrize("interval", [25.0, 50.0])
def test_resampled_polygons_stay_valid(interval):
    lake = Polygon(
        Point(0, 0).buffer(2000.0, quad_segs=256).exterior.coords,
        [Point(300, 200).buffer(400.0, quad_segs=64).exterior.coords, box(-900, -900, -700, -600).exterior.coords],
    )
    shapes = [MultiPolygon([lake]), MultiPolygon([box(0, 0, 1000, 300), box(3000, 0, 3500, 500)])]
    for shape in shapes:
        resampled, log = resample_lake(shape, interval)
        assert resampled.is_valid
        assert log["is_valid"]


def test_circle_r2000_resampled_at_25_m_estimates_within_0_01_of_1():
    resampled, _ = resample_lake(MultiPolygon([Point(0, 0).buffer(2000.0, quad_segs=512)]), 25.0)
    result = box_count_dimension(resampled, WINDOWS[PRIMARY_WINDOW], densify_fraction=0.01)
    assert abs(result.dimension - 1.0) < 0.01


def test_spacing_by_group_reports_median_and_quartiles():
    table = pd.DataFrame(
        {
            "source_group": ["PWI"] * 4 + ["other"] * 3 + [None],
            "median_spacing_m": [1.0, 2.0, 3.0, 4.0, 10.0, 20.0, 30.0, 99.0],
            "p90_spacing_m": [5.0, 6.0, 7.0, 8.0, 40.0, 50.0, 60.0, 99.0],
        }
    )
    groups = spacing_by_group(table).set_index("group")
    assert groups.loc["PWI", "n"] == 4
    assert groups.loc["PWI", "median_spacing_median"] == 2.5
    assert (groups.loc["PWI", "median_spacing_q25"], groups.loc["PWI", "median_spacing_q75"]) == (1.75, 3.25)
    assert groups.loc["other", "p90_spacing_median"] == 50.0
    assert groups.loc["all lakes", "n"] == 8
    assert "missing" not in groups.index
