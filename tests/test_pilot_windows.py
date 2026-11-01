"""Tests for the acreage bins and stratified sample in src/pilot_windows.py."""

import pandas as pd

from pilot_windows import BIN_LABELS, acreage_bin, stratified_sample


def test_bin_edges_put_each_boundary_in_the_upper_bin():
    acres = pd.Series([10.0, 24.99, 25.0, 99.99, 100.0, 999.99, 1000.0, 50000.0])
    assert list(acreage_bin(acres)) == [
        "under 25", "under 25",
        "25 to 100", "25 to 100",
        "100 to 1,000", "100 to 1,000",
        "over 1,000", "over 1,000",
    ]


def test_sample_takes_n_per_bin_and_is_reproducible():
    lakes = pd.DataFrame({"objectid": range(400), "acres": [15.0, 50.0, 500.0, 5000.0] * 100})
    first = stratified_sample(lakes, n_per_bin=10, seed=0)
    second = stratified_sample(lakes, n_per_bin=10, seed=0)
    assert first["acreage_bin"].value_counts().to_dict() == {label: 10 for label in BIN_LABELS}
    assert list(first["objectid"]) == list(second["objectid"])
