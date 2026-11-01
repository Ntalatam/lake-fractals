"""Tests for the settings in src/exploratory_10acre.py."""

from exploratory_10acre import EXPECTED_N, MIN_ACRES, WINDOWS_USED


def test_exploratory_run_is_the_10_acre_sample_in_the_primary_window_only():
    assert MIN_ACRES == 10
    assert EXPECTED_N == 13269
    assert list(WINDOWS_USED) == ["20_100"]
    assert (WINDOWS_USED["20_100"][0], WINDOWS_USED["20_100"][-1]) == (20.0, 100.0)
