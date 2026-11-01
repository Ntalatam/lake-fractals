"""Post-hoc validation, not pre-registered: checks of the box-counting estimator.

Everything here was added after review and after the planned results. It
does not change the planned analysis or any file in results/primary/ or
results/exploratory/, which are only read. Writes to results/validation/:
- benchmarks.csv: circle, Koch snowflake (6 and 7 iterations) and Sierpinski
  triangle in the three analysis windows, at the planned point spacing
- calibration.csv: shapes of known dimension near 1, one row per shape,
  window and point spacing: generalized Koch snowflakes (D = 1.02, 1.05,
  1.10), ellipses sized like the lakes (D = 1) and the benchmark circle, at
  point spacings of 0.1 (planned), 0.03 and 0.01 of the smallest box
- calibration_summary.csv: bias, sd and share below 1 of the calibration
  estimates, per shape, size, window and point spacing
- below_one.csv: estimates below 1 in results/primary/dims.csv, per window

Every box count uses the planned 8 box sizes per window and 8 grid offsets
from seed 0 (src/boxcount.py). The grid is placed relative to the lower-left
corner of the boundary points, so shifting a shape moves the grid with it and
leaves the box counts unchanged up to floating-point rounding. The random
shifts of the ellipses are kept as requested.

Run from the project root: .venv/bin/python src/validation.py
(or name the parts to run: benchmarks, calibration, below-one)
"""

import argparse
import math
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from shapely.geometry import MultiPolygon, Point, Polygon

from boxcount import DEFAULT_N_OFFSETS, DEFAULT_SEED, DENSIFY_FRACTION, box_count_dimension
from primary_analysis import ROOT, WINDOWS, default_workers

OUT_DIR = ROOT / "results" / "validation"
PRIMARY_DIMS = ROOT / "results" / "primary" / "dims.csv"

# square meters in one international acre
M2_PER_ACRE = 4046.8564224

KOCH_DIMENSION = math.log(4) / math.log(3)
SIERPINSKI_DIMENSION = math.log(3) / math.log(2)

# benchmark sizes (author's). circle: radius 10 times the largest box in any
# window. koch: side 7,290 m, see tests/test_boxcount.py for the sizing rule.
# sierpinski: 8 levels on a 1,280 m side, smallest triangle side 5 m.
CIRCLE_RADIUS_M = 2000.0
KOCH_SIDE_M = 7290.0
BENCHMARK_KOCH_ITERATIONS = [6, 7]
SIERPINSKI_SIDE_M = 1280.0
SIERPINSKI_LEVELS = 8

# calibration near 1 (author's): generalized Koch snowflakes with a known
# dimension in the range of the lake estimates, 6 iterations, side 7,290 m
CALIBRATION_DIMENSIONS = [1.02, 1.05, 1.10]
CALIBRATION_KOCH_ITERATIONS = 6

# smooth shapes sized like the lakes (author's): ellipses of these areas and
# axis ratios, true dimension 1, vertices at most 10 m apart along the edge
ELLIPSE_ACRES = [100, 1000, 10000]
ELLIPSE_ASPECT_RATIOS = [1, 3, 10]
ELLIPSE_VERTEX_SPACING_M = 10.0

# 40 random rotations and shifts per ellipse, seed 0 (author's). the same 40
# draws are used for every area and axis ratio, so those differ only in shape.
# the ranges were not set by the author: rotation is uniform on [0, 180 deg),
# since a half turn leaves an ellipse unchanged, and the shift is uniform on
# [0, 200 m) in x and y, the largest box in any window.
ELLIPSE_DRAWS = 40
ELLIPSE_SEED = 0
ELLIPSE_SHIFT_MAX_M = 200.0

# point spacing, as a fraction of the smallest box (author's): the planned
# 0.1 and two finer spacings
DENSIFY_FRACTIONS = [DENSIFY_FRACTION, 0.03, 0.01]


def circle(radius=CIRCLE_RADIUS_M):
    # quad_segs 512: 2,048 vertices, 6.1 m apart at radius 2,000 m
    return Point(0, 0).buffer(radius, quad_segs=512)


def koch_cos_theta(dimension):
    """cos of the bump angle that gives a generalized Koch curve this dimension."""
    return (4 ** (1 / dimension) - 2) / 2


def koch_dimension(cos_theta):
    """Dimension of the generalized Koch curve with bump angle theta."""
    return math.log(4) / math.log(2 + 2 * cos_theta)


def koch_smallest_segment(side, iterations, cos_theta=0.5):
    return side * (1 / (2 + 2 * cos_theta)) ** iterations


def koch_snowflake(side, iterations, cos_theta=0.5):
    """Koch snowflake on an equilateral triangle, every bump outward.

    Each segment is replaced by 4 segments, each r = 1 / (2 + 2 cos theta) of
    its length; the middle two form a bump at angle theta to the segment, so
    the dimension is log 4 / log(1 / r). cos theta = 0.5 (theta 60 deg) is the
    standard snowflake, dimension log 4 / log 3.

    The starting triangle is clockwise, so the interior is on the right of
    every segment and outward is a left turn (+theta). An earlier version in
    tests/test_boxcount.py turned right, which built the bumps inward and made
    the polygon self-intersect from 2 iterations on.
    """
    r = 1 / (2 + 2 * cos_theta)
    sin_theta = math.sqrt(1 - cos_theta**2)
    left_turn = np.array([[cos_theta, -sin_theta], [sin_theta, cos_theta]])
    h = side * math.sqrt(3) / 2
    points = np.array([(0.0, 0.0), (side / 2, h), (side, 0.0)])
    for _ in range(iterations):
        ends = np.roll(points, -1, axis=0)
        step = (ends - points) * r
        first = points + step
        peak = first + step @ left_turn.T
        last = ends - step
        points = np.stack([points, first, peak, last], axis=1).reshape(-1, 2)
    return Polygon(points)


def sierpinski_triangle(side, levels):
    """The smallest triangles after this many subdivisions; they touch only at corners."""
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


def ellipse(acres, aspect_ratio, rotation, shift, vertex_spacing=ELLIPSE_VERTEX_SPACING_M):
    """Ellipse of this area and axis ratio, rotated (radians) about its center, then shifted (m).

    The vertices are equally spaced along the edge, at most vertex_spacing apart.
    """
    # area = pi * a * b, with a = aspect_ratio * b
    minor = math.sqrt(acres * M2_PER_ACRE / (math.pi * aspect_ratio))
    major = aspect_ratio * minor
    # edge length from a fine sampling of the parameter, then vertices at
    # equal steps of edge length
    t = np.linspace(0.0, 2 * math.pi, 2**18 + 1)
    edge = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(major * np.cos(t)), np.diff(minor * np.sin(t))))])
    n = math.ceil(edge[-1] / vertex_spacing)
    t_vertex = np.interp(np.arange(n) * (edge[-1] / n), edge, t)
    x, y = major * np.cos(t_vertex), minor * np.sin(t_vertex)
    c, s = math.cos(rotation), math.sin(rotation)
    return Polygon(np.column_stack([c * x - s * y + shift[0], s * x + c * y + shift[1]]))


def ellipse_draws(n=ELLIPSE_DRAWS, seed=ELLIPSE_SEED):
    """(rotation in radians, (shift x, shift y) in meters) for each ellipse draw."""
    rng = np.random.default_rng(seed)
    rotations = rng.uniform(0.0, math.pi, n)
    shifts = rng.uniform(0.0, ELLIPSE_SHIFT_MAX_M, (n, 2))
    return [(float(r), (float(x), float(y))) for r, (x, y) in zip(rotations, shifts)]


def fit_columns(result, known_d):
    return {
        "estimate": result.dimension,
        "bias": result.dimension - known_d,
        "min_offset_slope": float(result.offset_dimensions.min()),
        "max_offset_slope": float(result.offset_dimensions.max()),
        "r2": result.r_squared,
    }


def benchmark_shapes():
    """(shape, parameters, known dimension, geometry) for each benchmark shape."""
    koch = [
        (
            "koch",
            f"iterations={n}; side_m={KOCH_SIDE_M:g}; "
            f"smallest_segment_m={koch_smallest_segment(KOCH_SIDE_M, n):.3g}; bumps=outward",
            KOCH_DIMENSION,
            koch_snowflake(KOCH_SIDE_M, n),
        )
        for n in BENCHMARK_KOCH_ITERATIONS
    ]
    sierpinski = (
        "sierpinski",
        f"levels={SIERPINSKI_LEVELS}; side_m={SIERPINSKI_SIDE_M:g}; "
        f"smallest_side_m={SIERPINSKI_SIDE_M / 2**SIERPINSKI_LEVELS:g}",
        SIERPINSKI_DIMENSION,
        sierpinski_triangle(SIERPINSKI_SIDE_M, SIERPINSKI_LEVELS),
    )
    return [("circle", f"radius_m={CIRCLE_RADIUS_M:g}; quad_segs=512", 1.0, circle()), *koch, sierpinski]


def benchmarks(shapes=None, windows=WINDOWS):
    """Each benchmark shape in each window, at the planned point spacing."""
    rows = []
    for shape, parameters, known_d, geometry in benchmark_shapes() if shapes is None else shapes:
        for window, sizes in windows.items():
            rows.append(
                {
                    "shape": shape,
                    "parameters": parameters,
                    "window": window,
                    "window_min_m": sizes[0],
                    "window_max_m": sizes[-1],
                    "densify_fraction": DENSIFY_FRACTION,
                    "is_valid": geometry.is_valid,
                    "known_d": known_d,
                    **fit_columns(box_count_dimension(geometry, sizes), known_d),
                }
            )
    return pd.DataFrame(rows)


def calibration_specs():
    """Every calibration shape, as the arguments that build it."""
    specs = [{"shape": "circle", "known_d": 1.0, "radius_m": CIRCLE_RADIUS_M}]
    specs += [
        {"shape": "koch", "known_d": d, "side_m": KOCH_SIDE_M, "iterations": CALIBRATION_KOCH_ITERATIONS}
        for d in CALIBRATION_DIMENSIONS
    ]
    draws = ellipse_draws()
    for acres in ELLIPSE_ACRES:
        for aspect in ELLIPSE_ASPECT_RATIOS:
            for draw, (rotation, shift) in enumerate(draws):
                specs.append(
                    {
                        "shape": "ellipse",
                        "known_d": 1.0,
                        "target_acres": acres,
                        "aspect_ratio": aspect,
                        "draw": draw,
                        "rotation": rotation,
                        "shift": shift,
                    }
                )
    return specs


def build(spec):
    if spec["shape"] == "circle":
        return circle(spec["radius_m"])
    if spec["shape"] == "koch":
        return koch_snowflake(spec["side_m"], spec["iterations"], koch_cos_theta(spec["known_d"]))
    if spec["shape"] == "ellipse":
        return ellipse(spec["target_acres"], spec["aspect_ratio"], spec["rotation"], spec["shift"])
    raise ValueError(f"unknown shape {spec['shape']}")


def calibration_rows(spec, windows=WINDOWS, fractions=DENSIFY_FRACTIONS):
    """Box-count one calibration shape in every window at every point spacing."""
    geometry = build(spec)
    koch = spec["shape"] == "koch"
    cos_theta = koch_cos_theta(spec["known_d"]) if koch else np.nan
    shape = {
        "shape": spec["shape"],
        "known_d": spec["known_d"],
        "target_acres": spec.get("target_acres", np.nan),
        "aspect_ratio": spec.get("aspect_ratio", np.nan),
        "radius_m": spec.get("radius_m", np.nan),
        "side_m": spec.get("side_m", np.nan),
        "iterations": spec.get("iterations", np.nan),
        "cos_theta": cos_theta,
        "smallest_segment_m": koch_smallest_segment(spec["side_m"], spec["iterations"], cos_theta) if koch else np.nan,
        "draw": spec.get("draw", np.nan),
        "rotation_deg": math.degrees(spec["rotation"]) if "rotation" in spec else np.nan,
        "shift_x_m": spec["shift"][0] if "shift" in spec else np.nan,
        "shift_y_m": spec["shift"][1] if "shift" in spec else np.nan,
        "n_vertices": len(geometry.exterior.coords) - 1,
        "area_acres": geometry.area / M2_PER_ACRE,
        "is_valid": geometry.is_valid,
    }
    rows = []
    for window, sizes in windows.items():
        for fraction in fractions:
            result = box_count_dimension(geometry, sizes, DEFAULT_N_OFFSETS, DEFAULT_SEED, fraction)
            rows.append(
                {
                    **shape,
                    "window": window,
                    "window_min_m": sizes[0],
                    "window_max_m": sizes[-1],
                    "densify_fraction": fraction,
                    "point_spacing_m": sizes[0] * fraction,
                    **fit_columns(result, spec["known_d"]),
                }
            )
    return rows


SUMMARY_KEYS = [
    "shape",
    "known_d",
    "target_acres",
    "aspect_ratio",
    "radius_m",
    "side_m",
    "iterations",
    "window",
    "window_min_m",
    "window_max_m",
    "densify_fraction",
]


def calibration_summary(rows):
    """Bias, sd and share below 1 of the estimates, per shape, size, window and point spacing.

    bias is the mean estimate minus the known dimension; sd has 1 degree of
    freedom removed and is empty for a shape with a single draw.
    """
    groups = rows.assign(below_1=rows["estimate"] < 1).groupby(SUMMARY_KEYS, dropna=False, sort=False)
    summary = groups.agg(
        n=("estimate", "size"),
        all_valid=("is_valid", "all"),
        mean_estimate=("estimate", "mean"),
        sd=("estimate", "std"),
        n_below_1=("below_1", "sum"),
        share_below_1=("below_1", "mean"),
        min_estimate=("estimate", "min"),
        max_estimate=("estimate", "max"),
    ).reset_index()
    summary.insert(summary.columns.get_loc("mean_estimate") + 1, "bias", summary["mean_estimate"] - summary["known_d"])
    return summary


def below_one(dims, windows=WINDOWS):
    """Estimates below 1 per window: count, share, and the lowest of them.

    The box-counting dimension of a curve is at least 1. min_below_1 is
    empty when no estimate is below 1.
    """
    rows = []
    for window, sizes in windows.items():
        dim = dims[f"dim_{window}"]
        below = dim[dim < 1]
        rows.append(
            {
                "window": window,
                "window_min_m": sizes[0],
                "window_max_m": sizes[-1],
                "n_lakes": len(dim),
                "n_below_1": len(below),
                "share_below_1": len(below) / len(dim),
                "percent_below_1": 100 * len(below) / len(dim),
                "min_below_1": below.min(),
            }
        )
    return pd.DataFrame(rows)


PARTS = ["benchmarks", "calibration", "below-one"]


def main():
    parser = argparse.ArgumentParser(description="post-hoc validation of the box-counting estimator")
    parser.add_argument("parts", nargs="*", help=f"any of {PARTS} (default: all)")
    parser.add_argument("--workers", type=int, default=default_workers(), help="processes for the calibration")
    args = parser.parse_args()
    parts = args.parts or PARTS
    if unknown := set(parts) - set(PARTS):
        sys.exit(f"unknown parts {sorted(unknown)}; choose from {PARTS}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if "benchmarks" in parts:
        benchmarks().to_csv(OUT_DIR / "benchmarks.csv", index=False)
        print(f"wrote {(OUT_DIR / 'benchmarks.csv').relative_to(ROOT)}", flush=True)

    if "calibration" in parts:
        specs = calibration_specs()
        print(f"calibration: {len(specs)} shapes with {args.workers} workers", flush=True)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            rows = [row for shape_rows in pool.map(calibration_rows, specs) for row in shape_rows]
        calibration = pd.DataFrame(rows)
        calibration.to_csv(OUT_DIR / "calibration.csv", index=False)
        calibration_summary(calibration).to_csv(OUT_DIR / "calibration_summary.csv", index=False)
        print(f"wrote {(OUT_DIR / 'calibration.csv').relative_to(ROOT)} and calibration_summary.csv", flush=True)

    if "below-one" in parts:
        below_one(pd.read_csv(PRIMARY_DIMS)).to_csv(OUT_DIR / "below_one.csv", index=False)
        print(f"wrote {(OUT_DIR / 'below_one.csv').relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
