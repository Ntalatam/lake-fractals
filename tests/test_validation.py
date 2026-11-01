"""Tests for src/validation.py (post-hoc validation, not pre-registered)."""

import math

import numpy as np
import pandas as pd
import pytest

from primary_analysis import WINDOWS
from validation import (
    CALIBRATION_DIMENSIONS,
    DENSIFY_FRACTIONS,
    ELLIPSE_ACRES,
    ELLIPSE_ASPECT_RATIOS,
    ELLIPSE_DRAWS,
    ELLIPSE_SHIFT_MAX_M,
    KOCH_DIMENSION,
    M2_PER_ACRE,
    below_one,
    benchmark_shapes,
    benchmarks,
    calibration_rows,
    calibration_specs,
    calibration_summary,
    ellipse,
    ellipse_draws,
    koch_cos_theta,
    koch_dimension,
    koch_snowflake,
    koch_smallest_segment,
)


def test_below_one_counts_share_and_minimum_per_window():
    dims = pd.DataFrame(
        {
            "dim_20_100": [0.99, 1.01, 0.97, 1.2],
            "dim_10_100": [1.0, 1.01, 1.02, 1.03],  # exactly 1 is not below 1
            "dim_20_200": [0.995, 0.999, 0.98, 0.9],
        }
    )
    table = below_one(dims).set_index("window")
    assert list(table.index) == list(WINDOWS)
    assert table.loc["20_100", ["n_lakes", "n_below_1"]].tolist() == [4, 2]
    assert table.loc["20_100", "share_below_1"] == 0.5
    assert table.loc["20_100", "percent_below_1"] == 50.0
    assert table.loc["20_100", "min_below_1"] == 0.97
    assert table.loc["10_100", "n_below_1"] == 0
    assert np.isnan(table.loc["10_100", "min_below_1"])
    assert table.loc["20_200", "n_below_1"] == 4
    assert table.loc["20_200", "min_below_1"] == 0.9
    assert (table.loc["20_200", "window_min_m"], table.loc["20_200", "window_max_m"]) == (20.0, 200.0)


def koch_area(side, iterations, cos_theta):
    # starting triangle plus every bump: iteration k puts one bump on each of
    # 3 * 4**(k-1) segments of length side * r**(k-1), and a bump on a segment
    # of length L has area r**2 * L**2 * sin(theta) * cos(theta)
    r = 1 / (2 + 2 * cos_theta)
    sin_cos = math.sqrt(1 - cos_theta**2) * cos_theta
    bumps = sum(3 * 4 ** (k - 1) * r**2 * (side * r ** (k - 1)) ** 2 * sin_cos for k in range(1, iterations + 1))
    return math.sqrt(3) / 4 * side**2 + bumps


def test_every_benchmark_shape_is_valid():
    for shape, parameters, known_d, geometry in benchmark_shapes():
        assert geometry.is_valid, (shape, parameters)


def test_benchmark_shapes_are_the_requested_ones():
    labels = [(shape, parameters) for shape, parameters, _, _ in benchmark_shapes()]
    assert labels == [
        ("circle", "radius_m=2000; quad_segs=512"),
        ("koch", "iterations=6; side_m=7290; smallest_segment_m=10; bumps=outward"),
        ("koch", "iterations=7; side_m=7290; smallest_segment_m=3.33; bumps=outward"),
        ("sierpinski", "levels=8; side_m=1280; smallest_side_m=5"),
    ]


def test_standard_koch_is_the_60_degree_bump_with_area_8_5():
    shape = koch_snowflake(7290.0, 7)
    triangle = math.sqrt(3) / 4 * 7290.0**2
    assert shape.is_valid
    assert shape.area == pytest.approx(koch_area(7290.0, 7, 0.5), rel=1e-9)
    assert abs(shape.area / (8 / 5 * triangle) - 1) < 0.01
    assert koch_cos_theta(KOCH_DIMENSION) == pytest.approx(0.5)
    assert koch_dimension(0.5) == KOCH_DIMENSION


def test_seven_iteration_koch_meets_the_sizing_rule_in_every_window():
    # smallest segment at most 1/3 of the smallest box, side over 10 times the
    # largest box, in every analysis window
    smallest = koch_smallest_segment(7290.0, 7, 0.5)
    assert smallest == pytest.approx(7290.0 / 3**7)
    for sizes in WINDOWS.values():
        assert smallest <= sizes[0] / 3 * (1 + 1e-12)
        assert 7290.0 > 10 * sizes[-1]


@pytest.mark.parametrize("dimension", CALIBRATION_DIMENSIONS)
def test_generalized_koch_has_the_requested_dimension_and_is_valid_and_outward(dimension):
    cos_theta = koch_cos_theta(dimension)
    assert cos_theta == (4 ** (1 / dimension) - 2) / 2
    assert koch_dimension(cos_theta) == pytest.approx(dimension, abs=1e-12)
    shape = koch_snowflake(7290.0, 6, cos_theta)
    assert shape.is_valid
    # outward bumps add area; inward bumps would take it away
    assert shape.area == pytest.approx(koch_area(7290.0, 6, cos_theta), rel=1e-9)
    assert shape.area > math.sqrt(3) / 4 * 7290.0**2


def test_calibration_dimensions_and_spacings_are_the_requested_ones():
    assert CALIBRATION_DIMENSIONS == [1.02, 1.05, 1.10]
    assert DENSIFY_FRACTIONS == [0.1, 0.03, 0.01]
    assert ELLIPSE_ACRES == [100, 1000, 10000]
    assert ELLIPSE_ASPECT_RATIOS == [1, 3, 10]
    assert ELLIPSE_DRAWS == 40


def test_ellipse_has_the_target_area_aspect_ratio_and_vertex_spacing():
    shape = ellipse(100, 3, rotation=0.0, shift=(0.0, 0.0))
    assert shape.is_valid
    assert shape.area / M2_PER_ACRE == pytest.approx(100, rel=1e-3)
    minx, miny, maxx, maxy = shape.bounds
    assert (maxx - minx) / (maxy - miny) == pytest.approx(3, rel=1e-3)
    ring = np.asarray(shape.exterior.coords)
    gaps = np.hypot(*np.diff(ring, axis=0).T)
    assert gaps.max() <= 10.0
    assert gaps.min() > 9.9


def test_ellipse_rotation_and_shift_move_the_same_shape():
    plain = ellipse(1000, 10, rotation=0.0, shift=(0.0, 0.0))
    moved = ellipse(1000, 10, rotation=math.pi / 2, shift=(30.0, 40.0))
    assert moved.is_valid
    assert moved.area == pytest.approx(plain.area)
    assert moved.centroid.x == pytest.approx(30.0, abs=0.01) and moved.centroid.y == pytest.approx(40.0, abs=0.01)
    minx, miny, maxx, maxy = moved.bounds
    assert (maxy - miny) / (maxx - minx) == pytest.approx(10, rel=1e-3)


def test_ellipse_draws_are_seeded_and_in_range():
    first = ellipse_draws()
    assert len(first) == ELLIPSE_DRAWS
    assert first == ellipse_draws()
    rotations = np.array([rotation for rotation, _ in first])
    shifts = np.array([shift for _, shift in first])
    assert ((rotations >= 0) & (rotations < math.pi)).all()
    assert ((shifts >= 0) & (shifts < ELLIPSE_SHIFT_MAX_M)).all()


def test_calibration_specs_cover_every_shape_once():
    specs = calibration_specs()
    kinds = [spec["shape"] for spec in specs]
    assert kinds.count("circle") == 1
    assert sorted(spec["known_d"] for spec in specs if spec["shape"] == "koch") == CALIBRATION_DIMENSIONS
    ellipses = [spec for spec in specs if spec["shape"] == "ellipse"]
    assert len(ellipses) == len(ELLIPSE_ACRES) * len(ELLIPSE_ASPECT_RATIOS) * ELLIPSE_DRAWS
    for acres in ELLIPSE_ACRES:
        for aspect in ELLIPSE_ASPECT_RATIOS:
            draws = [s["draw"] for s in ellipses if (s["target_acres"], s["aspect_ratio"]) == (acres, aspect)]
            assert draws == list(range(ELLIPSE_DRAWS))


def test_calibration_rows_run_every_window_and_spacing():
    spec = {"shape": "ellipse", "known_d": 1.0, "target_acres": 100, "aspect_ratio": 1, "draw": 0, "rotation": 0.4, "shift": (5.0, 7.0)}
    rows = pd.DataFrame(calibration_rows(spec))
    assert len(rows) == len(WINDOWS) * len(DENSIFY_FRACTIONS)
    assert set(zip(rows["window"], rows["densify_fraction"])) == {(w, f) for w in WINDOWS for f in DENSIFY_FRACTIONS}
    assert rows["is_valid"].all()
    assert (rows["bias"] == rows["estimate"] - 1.0).all()
    assert (rows["point_spacing_m"] == rows["window_min_m"] * rows["densify_fraction"]).all()
    assert (rows["min_offset_slope"] <= rows["estimate"]).all() and (rows["estimate"] <= rows["max_offset_slope"]).all()


def test_calibration_summary_reports_bias_sd_and_share_below_1():
    rows = pd.DataFrame(
        {
            "shape": "ellipse",
            "known_d": 1.0,
            "target_acres": [100.0] * 4 + [1000.0] * 2,
            "aspect_ratio": 3.0,
            "radius_m": np.nan,
            "side_m": np.nan,
            "iterations": np.nan,
            "window": "20_100",
            "window_min_m": 20.0,
            "window_max_m": 100.0,
            "densify_fraction": 0.1,
            "is_valid": True,
            "estimate": [0.98, 0.99, 1.01, 1.02, 1.03, 1.05],
        }
    )
    summary = calibration_summary(rows).set_index("target_acres")
    assert summary.loc[100.0, "n"] == 4
    assert summary.loc[100.0, "mean_estimate"] == pytest.approx(1.0)
    assert summary.loc[100.0, "bias"] == pytest.approx(0.0, abs=1e-12)
    assert summary.loc[100.0, "sd"] == pytest.approx(np.std([0.98, 0.99, 1.01, 1.02], ddof=1))
    assert summary.loc[100.0, "n_below_1"] == 2
    assert summary.loc[100.0, "share_below_1"] == 0.5
    assert summary.loc[1000.0, "bias"] == pytest.approx(0.04)
    assert summary.loc[1000.0, "share_below_1"] == 0.0
    assert summary.loc[1000.0, "min_estimate"] == 1.03
    assert bool(summary.loc[1000.0, "all_valid"])


def test_benchmarks_table_has_the_requested_columns():
    shapes = [("circle", "radius_m=500", 1.0, ellipse(200, 1, rotation=0.0, shift=(0.0, 0.0)))]
    table = benchmarks(shapes)
    assert list(table.columns) == [
        "shape",
        "parameters",
        "window",
        "window_min_m",
        "window_max_m",
        "densify_fraction",
        "is_valid",
        "known_d",
        "estimate",
        "bias",
        "min_offset_slope",
        "max_offset_slope",
        "r2",
    ]
    assert list(table["window"]) == list(WINDOWS)
    assert (table["bias"] == table["estimate"] - 1.0).all()
    assert (table["densify_fraction"] == 0.1).all()
