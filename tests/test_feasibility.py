"""Tests for src/feasibility.py."""

import math

import numpy as np
import pytest

from feasibility import PRIMARY_BOX_SIZES, PRIMARY_MIN_ACRES, equivalent_diameter


def test_equivalent_diameter_of_a_circle_is_its_diameter():
    assert equivalent_diameter(math.pi * 500.0**2) == pytest.approx(1000.0)


def test_equivalent_diameter_works_on_arrays():
    areas = np.array([math.pi, 4 * math.pi])  # radius 1 and 2
    assert np.allclose(equivalent_diameter(areas), [2.0, 4.0])


def test_primary_window_is_8_log_spaced_sizes_from_20_to_100_m():
    assert len(PRIMARY_BOX_SIZES) == 8
    assert PRIMARY_BOX_SIZES[0] == 20.0
    assert PRIMARY_BOX_SIZES[-1] == 100.0
    assert np.allclose(np.diff(np.log(PRIMARY_BOX_SIZES)), np.log(5) / 7)


def test_primary_sample_starts_at_100_acres():
    assert PRIMARY_MIN_ACRES == 100
