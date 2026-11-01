"""Tests for src/validation_width.py (post-hoc check, not in the analysis plan)."""

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import MultiPolygon, Point, box

from primary_analysis import WINDOWS
from validation_width import (
    MAX_NARROW_SHARE,
    NARROW_RADIUS_M,
    SHORE_GAP_M,
    distribution,
    inscribed_diameter,
    lake_width,
    narrow_sensitivity,
    narrow_share,
    rectangle_sides,
)


def circle(radius=1000.0):
    return Point(0, 0).buffer(radius, quad_segs=256)


def circle_with_arm():
    # a 40 m wide arm reaching 600 m beyond a 1,000 m circle: narrower than
    # both boxes, so its shore (2 * 600 m + 40 m at the end) is narrow shore
    return circle().union(box(-20, 990, 20, 1600))


def test_settings():
    # half the largest box of each window, the author's 10% cutoff and 1 m gap
    assert NARROW_RADIUS_M == {"20_100": 50.0, "10_100": 50.0, "20_200": 100.0}
    for window, radius in NARROW_RADIUS_M.items():
        assert radius == WINDOWS[window][-1] / 2
    assert MAX_NARROW_SHARE == 0.10
    assert SHORE_GAP_M == 1.0


def test_rectangle_1000_by_100_m():
    rectangle = box(0, 0, 1000, 100)
    assert inscribed_diameter(rectangle) == pytest.approx(100.0, abs=2.0)
    assert rectangle_sides(rectangle) == pytest.approx((100.0, 1000.0))
    # 100 m wide is narrower than the 200 m box everywhere
    assert narrow_share(rectangle, 100.0) == 1.0


def test_circle_has_no_narrow_shore():
    lake = circle()
    assert inscribed_diameter(lake) == pytest.approx(2000.0, abs=2.0)
    short, long = rectangle_sides(lake)
    assert short == pytest.approx(2000.0, abs=1.0) and long == pytest.approx(2000.0, abs=1.0)
    assert narrow_share(lake, 50.0) == 0.0
    assert narrow_share(lake, 100.0) == 0.0


@pytest.mark.parametrize("radius", [50.0, 100.0])
def test_a_long_narrow_bay_is_narrow_shore(radius):
    lake = circle_with_arm()
    expected = (2 * 600 + 40) / lake.length
    assert narrow_share(lake, radius) == pytest.approx(expected, abs=0.005)
    assert inscribed_diameter(lake) == pytest.approx(2000.0, abs=2.0)


def test_a_lake_narrower_everywhere_than_the_opening_is_all_narrow_shore():
    assert narrow_share(box(0, 0, 3000, 60), 50.0) == 1.0


def test_multipolygon_lake_uses_every_part():
    rectangle = box(5000, 0, 6000, 100)
    lake = MultiPolygon([circle(), rectangle])
    assert inscribed_diameter(lake) == pytest.approx(2000.0, abs=2.0)
    assert narrow_share(lake, 100.0) == pytest.approx(rectangle.length / lake.length, abs=1e-6)
    row = lake_width(lake)
    assert set(row) == {
        "inscribed_diameter_m",
        "rectangle_short_side_m",
        "rectangle_long_side_m",
        "narrow_share_r50",
        "narrow_share_r100",
    }


def test_distribution_reports_quantiles():
    table = distribution(pd.DataFrame({"a": np.arange(101.0)}), ["a"]).set_index("measure")
    assert table.loc["a", ["n", "min", "p5", "p25", "median", "p75", "p95", "max"]].tolist() == [
        101, 0.0, 5.0, 25.0, 50.0, 75.0, 95.0, 100.0
    ]


def test_narrow_sensitivity_drops_lakes_above_the_cutoff_per_window():
    rng = np.random.default_rng(0)
    n = 60
    dims = pd.DataFrame(
        {
            "objectid": np.arange(n),
            "acres": rng.uniform(100, 1000, n),
            "shoreline_m": rng.uniform(2000, 9000, n),
            **{f"dim_{w}": 1 + rng.uniform(0, 0.1, n) for w in WINDOWS},
        }
    )
    width = pd.DataFrame(
        {
            "objectid": np.arange(n),
            "narrow_share_r50": np.where(np.arange(n) < 10, 0.5, 0.05),
            "narrow_share_r100": np.where(np.arange(n) < 25, 0.5, 0.10),
        }
    )
    rho, rules = narrow_sensitivity(dims, width, n_resamples=50)
    by_window = rho.set_index(["window", "measure"])
    assert by_window.loc[("20_100", "area"), "n"] == 50
    assert by_window.loc[("10_100", "area"), "n_excluded"] == 10
    # 0.10 is not above the cutoff, so those lakes stay
    assert by_window.loc[("20_200", "shoreline"), "n"] == 35
    assert set(rules["measure"]) == {"area", "shoreline"}
    assert set(rules["outcome"]) <= {"supported", "window-dependent"}
