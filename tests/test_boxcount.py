"""Tests for src/boxcount.py, run against shapes with known dimensions.

Every shape is sized in meters so that the project's box sizes (10-100 m)
fall inside the range where the shape is self-similar. A pre-fractal only
has fractal structure between its smallest segment and its overall size,
so the scaling range has to sit between those two lengths.
"""

import math

import numpy as np
from shapely.geometry import MultiPolygon, Point, Polygon

from boxcount import DEFAULT_BOX_SIZES, box_count_dimension

TOLERANCE = 0.05


def circle(radius=2000.0):
    # radius 2000 m: much larger than the biggest box (100 m), so at every
    # box size the boundary looks like a smooth curve (dimension 1)
    return Point(0, 0).buffer(radius, quad_segs=512)


def koch_snowflake(side, iterations):
    # start from a clockwise equilateral triangle so every bump points outward
    h = side * math.sqrt(3) / 2
    points = [np.array(p) for p in [(0.0, 0.0), (side / 2, h), (side, 0.0)]]
    rotate = np.array([[0.5, -math.sqrt(3) / 2], [math.sqrt(3) / 2, 0.5]])  # +60 deg
    for _ in range(iterations):
        new_points = []
        for a, b in zip(points, points[1:] + points[:1]):
            step = (b - a) / 3
            p1 = a + step
            peak = p1 + rotate.T @ step  # -60 deg turn = outward for clockwise rings
            new_points += [a, p1, peak, a + 2 * step]
        points = new_points
    return Polygon(points)


def sierpinski_triangle(side, levels):
    triangles = [((0.0, 0.0), (side, 0.0), (side / 2, side * math.sqrt(3) / 2))]
    for _ in range(levels):
        next_triangles = []
        for a, b, c in triangles:
            ab = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            bc = ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2)
            ca = ((c[0] + a[0]) / 2, (c[1] + a[1]) / 2)
            next_triangles += [(a, ab, ca), (ab, b, bc), (ca, bc, c)]
        triangles = next_triangles
    return MultiPolygon([Polygon(t) for t in triangles])


def test_default_box_sizes_are_8_log_spaced_from_10_to_100_m():
    assert len(DEFAULT_BOX_SIZES) == 8
    assert DEFAULT_BOX_SIZES[0] == 10.0
    assert DEFAULT_BOX_SIZES[-1] == 100.0
    assert np.allclose(np.diff(np.log(DEFAULT_BOX_SIZES)), np.log(10) / 7)


def test_circle_dimension_is_about_1():
    result = box_count_dimension(circle())
    assert abs(result.dimension - 1.0) < TOLERANCE


def test_koch_snowflake_dimension_is_about_1_262():
    """Koch snowflake, 6 iterations, side 7,290 m.

    Sizing rule (author's decision, not a tuned value): the smallest Koch
    segment equals the smallest box (7,290 / 3**6 = 10 m), and the side is
    at least 10 times the largest box (7,290 m >= 10 * 100 m).

    A 4-iteration version (side 810 m) failed with 1.338 and was replaced.
    With 4 iterations the curve is only self-similar over a factor of 81,
    so the measured dimension depended on the side length (1.15 to 1.40
    across sides of 405 to 3,240 m), and passing would have meant picking
    a side to fit the answer.
    """
    result = box_count_dimension(koch_snowflake(side=7290.0, iterations=6))
    assert abs(result.dimension - math.log(4) / math.log(3)) < TOLERANCE


def test_sierpinski_triangle_dimension_is_about_1_585():
    # 8 levels, side 1280 m: smallest triangle side is 1280 / 2**8 = 5 m,
    # below the smallest box, and the whole triangle is far above the largest
    result = box_count_dimension(sierpinski_triangle(side=1280.0, levels=8))
    assert abs(result.dimension - math.log(3) / math.log(2)) < TOLERANCE


def test_shifting_grid_origin_changes_dimension_by_less_than_0_02():
    # same snowflake as the Koch dimension test
    shape = koch_snowflake(side=7290.0, iterations=6)
    first = box_count_dimension(shape, seed=1)
    second = box_count_dimension(shape, seed=2)
    assert abs(first.dimension - second.dimension) < 0.02


def test_result_reports_r_squared_and_box_sizes_used():
    result = box_count_dimension(circle())
    assert 0.99 < result.r_squared <= 1.0
    assert np.array_equal(result.box_sizes, DEFAULT_BOX_SIZES)
    assert len(result.offset_dimensions) == 8
