"""Tests for src/validation_spacing.py (post-hoc validation, not pre-registered)."""

import numpy as np
import pandas as pd
import pytest

from conftest import assert_close
from primary_analysis import BOOTSTRAP_RESAMPLES, OUT_DIR, ROOT, decision_rule, source_comparison
from validation_spacing import (
    DENSIFY_FRACTION_USED,
    MAX_WALL_SECONDS,
    OUT_DIR as SPACING_DIR,
    WORKERS,
    compare_decision_rule,
    compare_kruskal_wallis,
    compare_rho,
    compare_source_groups,
    planned_statistics,
)


def test_rerun_settings():
    assert DENSIFY_FRACTION_USED == 0.01
    assert WORKERS == 4
    assert MAX_WALL_SECONDS == 3 * 60 * 60
    assert SPACING_DIR == ROOT / "results" / "validation" / "spacing_0p01"


def synthetic_dims(n=40, seed=0):
    rng = np.random.default_rng(seed)
    acres = rng.uniform(100, 5000, n)
    dims = pd.DataFrame(
        {
            "objectid": np.arange(n),
            "acres": acres,
            "shoreline_m": acres * rng.uniform(20, 60, n),
            "source_group": rng.choice(["2004 FSA", "ORIG DLG", "PWI", "other"], n),
            "in_pilot": rng.random(n) < 0.2,
        }
    )
    dims.loc[:2, "source_group"] = None
    for window in ["20_100", "10_100", "20_200"]:
        dims[f"dim_{window}"] = 1 + rng.uniform(0, 0.2, n)
        dims[f"r2_{window}"] = rng.uniform(0.97, 1.0, n)
    return dims


def test_planned_statistics_on_synthetic_dims():
    dims = synthetic_dims()
    tables = planned_statistics(dims, n_resamples=50)
    assert set(tables) == {
        "rho_primary.csv",
        "decision_rule.csv",
        "r2_below_threshold.csv",
        "source_groups.csv",
        "kruskal_wallis.csv",
        "rho_within_2004_fsa.csv",
        "rho_sensitivity_no_pilot.csv",
        "sample_log.csv",
    }
    rho = tables["rho_primary.csv"]
    for rule in tables["decision_rule.csv"].itertuples():
        by_window = rho[rho["measure"] == rule.measure].set_index("window")["rho"].to_dict()
        assert rule.outcome == decision_rule(by_window)["outcome"]
    _, test = source_comparison(dims)
    assert tables["kruskal_wallis.csv"].iloc[0]["H"] == test["H"]
    assert (tables["rho_within_2004_fsa.csv"]["n"] == (dims["source_group"] == "2004 FSA").sum()).all()
    assert (tables["rho_sensitivity_no_pilot.csv"]["n"] == (~dims["in_pilot"]).sum()).all()


def test_planned_statistics_reproduce_the_planned_files(tmp_path):
    # the rerun's statistics code, given the planned dims.csv, must write the
    # files src/primary_analysis.py wrote: the same columns, rows and types,
    # every value that is not a float exactly, and floats within the tolerance
    # in conftest.py, since they can differ in the last digits on other systems
    dims = pd.read_csv(OUT_DIR / "dims.csv")
    tables = planned_statistics(dims, n_resamples=BOOTSTRAP_RESAMPLES)
    for name, table in tables.items():
        table.to_csv(tmp_path / name, index=False)
        written, planned = pd.read_csv(tmp_path / name), pd.read_csv(OUT_DIR / name)
        assert list(written.columns) == list(planned.columns), name
        assert written.dtypes.tolist() == planned.dtypes.tolist(), name
        assert len(written) == len(planned), name
        for column in planned.columns:
            if pd.api.types.is_float_dtype(planned[column]):
                assert_close(written[column], planned[column], (name, column))
            else:
                assert written[column].tolist() == planned[column].tolist(), (name, column)


@pytest.mark.exact
def test_planned_statistics_reproduce_the_planned_files_byte_for_byte(tmp_path):
    # on the computer that wrote results/primary/, the files match byte for byte
    dims = pd.read_csv(OUT_DIR / "dims.csv")
    tables = planned_statistics(dims, n_resamples=BOOTSTRAP_RESAMPLES)
    for name, table in tables.items():
        table.to_csv(tmp_path / name, index=False)
        assert (tmp_path / name).read_bytes() == (OUT_DIR / name).read_bytes(), name


def rho_rows(rhos, lows, highs):
    return pd.DataFrame(
        {
            "sample": "primary",
            "window": ["20_100", "10_100", "20_200"],
            "measure": "area",
            "n": 10,
            "rho": rhos,
            "ci_low": lows,
            "ci_high": highs,
        }
    )


def test_compare_rho_flags_sign_and_interval_changes():
    planned = rho_rows([-0.1, 0.02, -0.06], [-0.2, -0.01, -0.09], [0.01, 0.05, -0.02])
    rerun = rho_rows([-0.1, -0.01, -0.06], [-0.2, -0.04, -0.09], [-0.01, 0.03, -0.02])
    table = compare_rho(planned, rerun).set_index("window")
    assert table["same_sign"].tolist() == [True, False, True]
    assert table["ci_excludes_zero_planned"].tolist() == [False, False, True]
    assert table["ci_excludes_zero_rerun"].tolist() == [True, False, True]
    assert table["same_ci_status"].tolist() == [False, True, True]
    assert table.loc["10_100", "rho_change"] == -0.01 - 0.02


def test_compare_decision_rule_flags_a_changed_outcome():
    planned = pd.DataFrame(
        {"measure": ["area", "shoreline"], "direction": ["mixed", "positive"], "outcome": ["window-dependent", "supported"]}
    )
    rerun = pd.DataFrame(
        {"measure": ["area", "shoreline"], "direction": ["negative", "positive"], "outcome": ["supported", "supported"]}
    )
    table = compare_decision_rule(planned, rerun).set_index("measure")
    assert table["same_outcome"].tolist() == [False, True]
    assert table.loc["area", "outcome_rerun"] == "supported"


def test_compare_kruskal_wallis_and_source_groups_put_planned_beside_rerun():
    planned = pd.DataFrame([{"window": "20_100", "n_groups": 5, "n_lakes": 30, "n_excluded_missing": 2, "H": 9.0, "p_value": 0.01}])
    rerun = planned.assign(H=8.0, p_value=0.02)
    table = compare_kruskal_wallis(planned, rerun)
    assert table.iloc[0][["H_planned", "H_rerun", "p_value_planned", "p_value_rerun"]].tolist() == [9.0, 8.0, 0.01, 0.02]
    assert table.iloc[0]["n_lakes"] == 30
    groups = pd.DataFrame({"window": "20_100", "group": ["PWI", "other"], "n": [3, 4], "median_dim": [1.04, 1.02]})
    table = compare_source_groups(groups, groups.assign(median_dim=[1.05, 1.02])).set_index("group")
    assert table.loc["PWI", ["median_dim_planned", "median_dim_rerun"]].tolist() == [1.04, 1.05]
    assert table.loc["other", "n"] == 4
