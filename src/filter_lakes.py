"""Filter the DNR hydrography layer down to the lakes used in the analysis.

Reads data/raw/dnr_hydro_all.zip (read only), applies the filtering steps in
order, logs counts before and after each step to results/filter_log.csv, and
writes the kept lakes to data/processed/lakes_filtered.gpkg.

The output is the exploratory sample (acres >= 10). The primary sample
(acres >= 100, CLAUDE.md) is selected from it in src/primary_analysis.py.

Stops without writing anything if steps 1 and 2 do not keep the expected
counts.

Run from the project root: .venv/bin/python src/filter_lakes.py
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "dnr_hydro_all.zip"
OUTPUT = ROOT / "data" / "processed" / "lakes_filtered.gpkg"
LOG = ROOT / "results" / "filter_log.csv"

# NAD83 / UTM zone 15N: the layer's own CRS, in meters, so lengths are in meters
CRS = "EPSG:26915"

# natural lakes only (author's decision). reservoirs are described separately
# and not tested.
WB_CLASS = "Lake or Pond"

# exploratory-sample cutoff (author's decision, CLAUDE.md): every 10-acre
# result is exploratory. the primary sample, acres >= 100, is selected from
# this output in src/primary_analysis.py.
MIN_ACRES = 10

# author's decision. at 1,000 m the shoreline is at least 10 times the
# largest box in the 20-100 m and 10-100 m windows (100 m), so even the
# coarsest box count covers it with several boxes; in the 20-200 m window it
# is 5 times the largest box. at >= 100 acres it drops no lake (CLAUDE.md),
# so it only changes the exploratory sample.
MIN_SHORELINE_M = 1000

# outside_mn values to drop (author's decision): Y = entirely outside
# Minnesota (e.g. Superior in WI/MI, Lake of the Woods in Canada), B = on the
# border. the study is about Minnesota lakes, and these polygons include
# shoreline outside the state. blank values are kept.
OUTSIDE_MN_DROP = ["Y", "B"]

# columns written to the output. objectid is the row's unique id in the raw
# layer (dowlknum is not unique and is sometimes blank), so it is kept for
# joining results back to the raw data.
KEEP_COLUMNS = ["objectid", "dowlknum", "acres", "delineat_1", "shoreline_m", "geometry"]

# counts after steps 1 and 2 on the full file, as in results/filter_log.csv.
# a different count means the raw file or a filter step changed, so the run
# stops instead of overwriting the log and the filtered lakes.
EXPECTED_AFTER = {1: 117_235, 2: 14_640}


def filter_lakes(lakes):
    """Apply the filtering steps in order. Returns (kept lakes, log table)."""
    lakes = lakes.to_crs(CRS)
    log = []

    def step(number, description, keep):
        nonlocal lakes
        before = len(lakes)
        lakes = lakes[keep]
        log.append(
            {
                "step": number,
                "description": description,
                "count_before": before,
                "count_after": len(lakes),
                "dropped": before - len(lakes),
            }
        )

    step(1, f"wb_class == '{WB_CLASS}'", lakes["wb_class"] == WB_CLASS)
    step(2, f"acres >= {MIN_ACRES}", lakes["acres"] >= MIN_ACRES)
    # the full file's records without geometry have a blank wb_class, so step
    # 1 already removes them and this step logs 0 (CLAUDE.md, audit disclosures)
    step(3, "geometry is not null", lakes.geometry.notna())
    # polygon length includes every ring: the outer shore and island shores
    lakes = lakes.assign(shoreline_m=lakes.geometry.length)
    step(4, f"shoreline_m >= {MIN_SHORELINE_M} (EPSG:26915)", lakes["shoreline_m"] >= MIN_SHORELINE_M)
    step(5, "outside_mn not 'Y' or 'B'", ~lakes["outside_mn"].isin(OUTSIDE_MN_DROP))

    return lakes[KEEP_COLUMNS].reset_index(drop=True), pd.DataFrame(log)


def check_expected_counts(log, expected=EXPECTED_AFTER):
    """Raise if any step kept a different count than expected."""
    for number, count in expected.items():
        actual = log.loc[log["step"] == number, "count_after"].item()
        if actual != count:
            raise RuntimeError(f"step {number} kept {actual:,}, expected {count:,}")


def main():
    lakes, log = filter_lakes(gpd.read_file(RAW))
    # checked before anything is written, so a mismatch leaves the old log and
    # filtered lakes in place
    check_expected_counts(log)

    LOG.parent.mkdir(exist_ok=True)
    log.to_csv(LOG, index=False)
    OUTPUT.parent.mkdir(exist_ok=True)
    lakes.to_file(OUTPUT, driver="GPKG")
    print(log.to_string(index=False))
    print(f"wrote {len(lakes):,} lakes to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
