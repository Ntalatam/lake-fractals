"""Tests for the number check in src/summarize_primary.py."""

import pandas as pd

from summarize_primary import unmatched_numbers


def write_csv(tmp_path, frame):
    path = tmp_path / "values.csv"
    frame.to_csv(path, index=False)
    return [path]


def test_numbers_rounded_from_a_csv_value_are_matched(tmp_path):
    csvs = write_csv(tmp_path, pd.DataFrame({"rho": [-0.236012], "p": [0.000766321], "n": [3274], "q": [2.2134e-10]}))
    assert unmatched_numbers("rho -0.2360, p 0.000766, n 3,274, q 2.21e-10", csvs) == []


def test_a_number_not_in_any_csv_is_reported(tmp_path):
    csvs = write_csv(tmp_path, pd.DataFrame({"rho": [-0.236012]}))
    assert unmatched_numbers("rho -0.2360 and 0.5", csvs) == ["0.5"]


def test_a_wrongly_rounded_number_is_reported(tmp_path):
    csvs = write_csv(tmp_path, pd.DataFrame({"rho": [-0.236012]}))
    assert unmatched_numbers("rho -0.2361", csvs) == ["-0.2361"]


def test_labels_containing_digits_are_ignored(tmp_path):
    csvs = write_csv(tmp_path, pd.DataFrame({"n": [5]}))
    assert unmatched_numbers("2004 FSA has 5 lakes", csvs, ignore=["2004 FSA"]) == []
