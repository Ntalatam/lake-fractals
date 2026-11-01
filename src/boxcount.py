"""Box-counting dimension of polygon boundaries (lake shorelines).

The boundary is every ring of the polygon(s): the outer shoreline and the
shorelines of any islands. Coordinates must be in meters (EPSG:26915 for
the lake data).
"""

from dataclasses import dataclass

import numpy as np
import shapely

# 8 log-spaced box sizes from 10 m to 100 m (author's choice). Log spacing
# gives evenly spaced points on the log-log plot, so no part of the range
# dominates the fitted slope.
DEFAULT_BOX_SIZES = np.geomspace(10.0, 100.0, 8)

# 8 grid offsets (author's choice). Box counts depend on where the grid
# starts, so the dimension is fitted once per offset and the median is
# reported.
DEFAULT_N_OFFSETS = 8

# fixed seed so the grid offsets, and therefore every dimension, are
# reproducible from run to run
DEFAULT_SEED = 0

# points along the boundary are placed at most (smallest box / 10) apart.
# a box is counted when a point lands in it, so a gap this small can only
# skip a box that the boundary clips across one corner; the undercount is
# small and similar at every box size.
DENSIFY_FRACTION = 0.1


@dataclass
class BoxCountResult:
    dimension: float  # median log-log slope across grid offsets
    r_squared: float  # median r squared of the per-offset fits
    box_sizes: np.ndarray  # box sizes used, in meters
    offset_dimensions: np.ndarray  # slope for each grid offset
    counts: np.ndarray  # boxes touched, shape (n_offsets, n_box_sizes)


def box_count_dimension(
    polygons,
    box_sizes=DEFAULT_BOX_SIZES,
    n_offsets=DEFAULT_N_OFFSETS,
    seed=DEFAULT_SEED,
):
    """Box-counting dimension of the boundary of a polygon or polygons.

    polygons: a shapely Polygon, MultiPolygon, or a list of them.
    box_sizes: box side lengths in meters.
    n_offsets: number of random grid origins to count with.
    seed: seed for the grid origins.
    """
    box_sizes = np.asarray(box_sizes, dtype=float)
    if isinstance(polygons, (list, tuple)):
        polygons = shapely.GeometryCollection(list(polygons))
    boundary = shapely.boundary(polygons) if polygons.geom_type != "GeometryCollection" \
        else shapely.GeometryCollection([g.boundary for g in polygons.geoms])
    dense = shapely.segmentize(boundary, box_sizes.min() * DENSIFY_FRACTION)
    points = shapely.get_coordinates(dense)
    corner = points.min(axis=0)

    # each offset is a fraction of the box size in x and y, so the grid
    # origin moves by the same relative amount at every box size
    fractions = np.random.default_rng(seed).random((n_offsets, 2))

    counts = np.empty((n_offsets, len(box_sizes)), dtype=np.int64)
    for i, fraction in enumerate(fractions):
        for j, size in enumerate(box_sizes):
            origin = corner - fraction * size
            cells = np.floor((points - origin) / size).astype(np.int64)
            counts[i, j] = len(np.unique(cells, axis=0))

    log_inverse_size = np.log(1.0 / box_sizes)
    slopes = np.empty(n_offsets)
    r_squared = np.empty(n_offsets)
    for i in range(n_offsets):
        log_count = np.log(counts[i])
        slope, intercept = np.polyfit(log_inverse_size, log_count, 1)
        residuals = log_count - (slope * log_inverse_size + intercept)
        total = log_count - log_count.mean()
        slopes[i] = slope
        r_squared[i] = 1.0 - (residuals @ residuals) / (total @ total)

    return BoxCountResult(
        dimension=float(np.median(slopes)),
        r_squared=float(np.median(r_squared)),
        box_sizes=box_sizes,
        offset_dimensions=slopes,
        counts=counts,
    )
