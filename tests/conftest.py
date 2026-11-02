"""Shared test settings.

Tests marked `exact` require byte-identical output: with the golden box counts
and the committed results/primary files written on the original computer, or
between two runs that must match bit for bit. Floating-point results can
differ in the last digits on other systems: a reviewer's run on another
system differed by about 1.6e-15, with identical box counts. So the exact
tests run only when asked for:

    LAKE_FRACTALS_EXACT=1 .venv/bin/python -m pytest

Every exact test has a twin that always runs and compares integer box counts
exactly and floating values within RTOL and ATOL.
"""

import os

import numpy as np
import pytest

# tolerance for floating values compared with output from the original
# computer (the review's request): far looser than the 1.6e-15 seen on
# another system, far tighter than any difference that would change a result
RTOL = 1e-12
ATOL = 1e-12

EXACT = os.environ.get("LAKE_FRACTALS_EXACT") == "1"


def assert_close(actual, expected, label=""):
    np.testing.assert_allclose(actual, expected, rtol=RTOL, atol=ATOL, err_msg=str(label))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "exact: byte-identical to the original computer; runs only when LAKE_FRACTALS_EXACT=1"
    )


def pytest_collection_modifyitems(config, items):
    if EXACT:
        return
    skip = pytest.mark.skip(reason="byte identity is checked only when LAKE_FRACTALS_EXACT=1")
    for item in items:
        if "exact" in item.keywords:
            item.add_marker(skip)
