"""Tests for src/boxcount.py, run against shapes with known dimensions.

The shapes are built in src/validation.py, which also runs them in all three
analysis windows (results/validation/benchmarks.csv). Each shape is sized in
meters so that the box sizes fall inside the range where the shape is
self-similar. A pre-fractal only has fractal structure between its smallest
segment and its overall size, so the scaling range has to sit between those
two lengths.
"""

import json
import math
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import MultiPolygon, Point, Polygon

from boxcount import DEFAULT_BOX_SIZES, DENSIFY_FRACTION, box_count_dimension
from conftest import assert_close
from primary_analysis import WINDOWS
from validation import circle, koch_snowflake, sierpinski_triangle

# box_count_dimension output at commit 3b85cc7, before densify_fraction became
# an argument (written by write_golden with that commit's src/boxcount.py)
GOLDEN = Path(__file__).parent / "data" / "boxcount_golden_3b85cc7.json"

# a regression guard, not an accuracy claim: the estimator's accuracy near a
# dimension of 1 is measured in results/validation/ (src/validation.py)
TOLERANCE = 0.05


def test_default_box_sizes_are_8_log_spaced_from_10_to_100_m():
    assert len(DEFAULT_BOX_SIZES) == 8
    assert DEFAULT_BOX_SIZES[0] == 10.0
    assert DEFAULT_BOX_SIZES[-1] == 100.0
    assert np.allclose(np.diff(np.log(DEFAULT_BOX_SIZES)), np.log(10) / 7)


def test_circle_dimension_is_about_1():
    shape = circle()
    assert shape.is_valid
    result = box_count_dimension(shape)
    assert abs(result.dimension - 1.0) < TOLERANCE


def test_koch_snowflake_dimension_is_about_1_262():
    """Koch snowflake, 7 iterations, side 7,290 m.

    Sizing rule (author's decision, not a tuned value): the smallest Koch
    segment is at most 1/3 of the smallest box in every analysis window
    (7,290 / 3**7 = 3.3 m, and the smallest box is 10 m), and the side is over
    10 times the largest box in every window (7,290 m > 10 * 200 m).

    A 4-iteration version (side 810 m) failed with 1.338 and was replaced.
    With 4 iterations the curve is only self-similar over a factor of 81,
    so the measured dimension depended on the side length (1.15 to 1.40
    across sides of 405 to 3,240 m), and passing would have meant picking
    a side to fit the answer.

    The 6-iteration version that replaced it (side 7,290 m) built its bumps
    inward: the polygon self-intersected from 2 iterations on (shapely
    is_valid False) and its area was about 2/5 of the starting triangle, not
    8/5. It passed anyway, because box counting uses only boundary points
    and the test did not check the shape. The shape is now checked for
    validity and area (test_koch_snowflake_area_is_8_5_of_the_starting_triangle).
    """
    shape = koch_snowflake(side=7290.0, iterations=7)
    assert shape.is_valid
    result = box_count_dimension(shape)
    assert abs(result.dimension - math.log(4) / math.log(3)) < TOLERANCE


def test_koch_snowflake_area_is_8_5_of_the_starting_triangle():
    # each iteration adds outward bumps, and the area tends to 8/5 of the
    # triangle (an inward build tends to 2/5). at 7 iterations it is 0.13%
    # below 8/5.
    side = 7290.0
    triangle = math.sqrt(3) / 4 * side**2
    shape = koch_snowflake(side=side, iterations=7)
    assert abs(shape.area / (8 / 5 * triangle) - 1) < 0.01


def test_sierpinski_triangle_dimension_is_about_1_585():
    # 8 levels, side 1280 m: smallest triangle side is 1280 / 2**8 = 5 m,
    # below the smallest box, and the whole triangle is far above the largest
    shape = sierpinski_triangle(side=1280.0, levels=8)
    assert shape.is_valid
    result = box_count_dimension(shape)
    assert abs(result.dimension - math.log(3) / math.log(2)) < TOLERANCE


def test_shifting_grid_origin_changes_dimension_by_less_than_0_02():
    # same snowflake as the Koch dimension test
    shape = koch_snowflake(side=7290.0, iterations=7)
    assert shape.is_valid
    first = box_count_dimension(shape, seed=1)
    second = box_count_dimension(shape, seed=2)
    assert abs(first.dimension - second.dimension) < 0.02


def test_result_reports_r_squared_and_box_sizes_used():
    result = box_count_dimension(circle())
    assert 0.99 < result.r_squared <= 1.0
    assert np.array_equal(result.box_sizes, DEFAULT_BOX_SIZES)
    assert len(result.offset_dimensions) == 8


def rough_polygon(radius, center, seed):
    # a star-shaped ring with a rough edge, at UTM-sized coordinates like the
    # lakes. every vertex has its own angle and a positive radius, so the ring
    # never crosses itself.
    rng = np.random.default_rng(seed)
    angles = np.linspace(0, 2 * np.pi, 2000, endpoint=False)
    radii = radius * (1 + 0.1 * np.sin(7 * angles) + 0.03 * np.sin(31 * angles + 1)) + rng.normal(0, 3, 2000)
    return Polygon(np.column_stack([center[0] + radii * np.cos(angles), center[1] + radii * np.sin(angles)]))


def golden_shapes():
    """One shape for each kind of input box_count_dimension accepts."""
    lake = rough_polygon(1500.0, (480000.0, 5200000.0), seed=0)
    other = rough_polygon(600.0, (490000.0, 5205000.0), seed=1)
    island = Point(480200.0, 5200100.0).buffer(150.0, quad_segs=64)
    return {
        "polygon": lake,
        "polygon_with_island": Polygon(lake.exterior.coords, [island.exterior.coords]),
        "multipolygon": MultiPolygon([lake, other]),
        "list_of_polygons": [lake, other],
    }


def result_record(result):
    """Every field of a BoxCountResult, floats as hex so equality is bit for bit."""
    return {
        "dimension": float(result.dimension).hex(),
        "r_squared": float(result.r_squared).hex(),
        "box_sizes": [float(v).hex() for v in result.box_sizes],
        "offset_dimensions": [float(v).hex() for v in result.offset_dimensions],
        "offset_dimensions_dtype": str(result.offset_dimensions.dtype),
        "counts": result.counts.tolist(),
        "counts_dtype": str(result.counts.dtype),
    }


def from_hex(value):
    return np.array([float.fromhex(v) for v in value]) if isinstance(value, list) else float.fromhex(value)


def assert_same_result(actual, expected, label=""):
    """Two result records: box counts and dtypes exactly, floating values within the tolerance in conftest.py."""
    for key in ["counts", "counts_dtype", "offset_dimensions_dtype"]:
        assert actual[key] == expected[key], (label, key)
    for key in ["dimension", "r_squared", "box_sizes", "offset_dimensions"]:
        assert_close(from_hex(actual[key]), from_hex(expected[key]), (label, key))


def write_golden():
    """Write GOLDEN with the box_count_dimension currently importable.

    Run once, with src/boxcount.py as of commit 3b85cc7:
    .venv/bin/python -c "import sys; sys.path[:0] = ['src', 'tests']; import test_boxcount; test_boxcount.write_golden()"
    """
    cases = {
        f"{name}/{window}": result_record(box_count_dimension(shape, sizes))
        for name, shape in golden_shapes().items()
        for window, sizes in WINDOWS.items()
    }
    GOLDEN.parent.mkdir(exist_ok=True)
    GOLDEN.write_text(json.dumps({"source": "src/boxcount.py at commit 3b85cc7", "cases": cases}, indent=1) + "\n")


def test_default_output_matches_3b85cc7():
    # the planned analysis calls box_count_dimension without densify_fraction,
    # so its results must not change now that the spacing is an argument. box
    # counts must match exactly; floating values may differ in the last digits
    # on other systems
    golden = json.loads(GOLDEN.read_text())["cases"]
    shapes = golden_shapes()
    assert len(golden) == len(shapes) * len(WINDOWS)
    for name, shape in shapes.items():
        for window, sizes in WINDOWS.items():
            assert_same_result(result_record(box_count_dimension(shape, sizes)), golden[f"{name}/{window}"], (name, window))


@pytest.mark.exact
def test_default_output_is_byte_identical_to_3b85cc7():
    # on the computer that wrote the golden file, every field matches bit for bit
    golden = json.loads(GOLDEN.read_text())["cases"]
    shapes = golden_shapes()
    assert len(golden) == len(shapes) * len(WINDOWS)
    for name, shape in shapes.items():
        for window, sizes in WINDOWS.items():
            assert result_record(box_count_dimension(shape, sizes)) == golden[f"{name}/{window}"], (name, window)


def test_golden_shapes_are_valid():
    for name, shape in golden_shapes().items():
        parts = shape if isinstance(shape, list) else [shape]
        assert all(part.is_valid for part in parts), name


def test_densify_fraction_defaults_to_the_planned_0_1():
    assert DENSIFY_FRACTION == 0.1
    shape = golden_shapes()["polygon"]
    explicit = box_count_dimension(shape, densify_fraction=0.1)
    assert_same_result(result_record(explicit), result_record(box_count_dimension(shape)))


@pytest.mark.exact
def test_densify_fraction_default_is_byte_identical_to_0_1():
    shape = golden_shapes()["polygon"]
    explicit = box_count_dimension(shape, densify_fraction=0.1)
    assert result_record(explicit) == result_record(box_count_dimension(shape))


def test_densify_fraction_sets_the_point_spacing():
    # diagonal edges cross some boxes only near a corner. points one smallest
    # box apart skip many of those boxes; points 1/100 of a box apart do not.
    shape = Polygon([(0.0, 0.0), (1000.0, 370.0), (370.0, 1000.0)])
    coarse = box_count_dimension(shape, densify_fraction=1.0)
    fine = box_count_dimension(shape, densify_fraction=0.01)
    assert coarse.counts.sum() < fine.counts.sum()
