# Box-Counting Analysis of Minnesota Lake Shorelines: Lake Size, Shoreline Length, and Mapping Source

Code, results and paper drafts for a study of Minnesota lake shorelines. It asks how a box-counting exponent of each lake's shoreline relates to lake area and shoreline length, and how much it changes with the source the shoreline was mapped from.

## Paper

The preprint is `paper/talatam_2026_minnesota_lake_shorelines.pdf` (November 2, 2026, not peer reviewed). The `paper/*.md` files are working drafts that name the file behind each number; where they differ from the PDF, the PDF is the paper.

## What is measured

Each lake's shoreline is every ring of its polygon: the outer shore and the shore of each island. The shoreline is covered with square boxes at 8 box sizes, evenly spaced on a log scale from 20 to 100 m, and the boxes it passes through are counted. The estimate is the slope of log(box count) against log(1 / box size), fitted for each of 8 grid offsets (random, seed 0), and the median of the 8 slopes (`src/boxcount.py`). Before counting, points are placed along the shoreline at most 1/10 of the smallest box apart.

This is a scaling exponent over one range of scales, box sizes from 20 to 100 m (a factor of 5). It is not proof that the shorelines are fractal. A smooth curve gives an exponent near 1 over this range, and the exponent says nothing about scales outside it. The same exponent is computed over 10–100 m and 20–200 m as sensitivity windows.

The analysis reports:

- Spearman rho of the exponent against lake area (the DNR `acres` attribute) and against shoreline length, in each of the three windows, with a decision rule set in the analysis plan (below): a relationship is supported only if rho has the same sign in all three windows.
- A Kruskal–Wallis test of the exponent across mapping source groups (the `delineat_1` attribute), in the 20–100 m window.

The primary sample is the 3,274 lakes of 100 acres or more (`results/primary/sample_log.csv`); the 13,269 lakes of 10 acres or more are an exploratory sample (`results/filter_log.csv`).

## Data

| | |
|---|---|
| Source | Minnesota Geospatial Commons, "DNR Hydrography Dataset", published by the Minnesota Department of Natural Resources (MNDNR) |
| Dataset page | https://gis.data.mn.gov/maps/d26eb1d402e84c4db9a302d29f4fc1c9/about |
| Layer | "Dnr Hydro Features All": https://gis.data.mn.gov/datasets/minnesota::dnr-hydrography-dataset-1/about?layer=1 |
| Format | Shapefile, from the layer's download options |
| Saved as | `data/raw/dnr_hydro_all.zip` (115,744,537 bytes), read directly from the zip, never unzipped |
| Accessed | 2026-11-01 |
| Records | 130,912 |
| SHA-256 | `3bb9e0e69453d0b2156f7047e4562b6471557bab4e40485ebe9d3c8235fb7ba3` |
| Coordinates | EPSG:26915 (NAD83 / UTM zone 15N, meters) |

The zip holds `Dnr_Hydro_Features_All` (.shp, .shx, .dbf, .prj, .cpg) and the provider's metadata (.xml). MNDNR updates the dataset as needed, and on 2026-11-01 the layer page showed "Data Updated: September 23, 2026". A later download may hold different records, so compare its SHA-256 with the one above. `src/filter_lakes.py` stops if its first two filter steps keep different counts from those in `results/filter_log.csv`.

The data are not redistributed here: `data/` is not in git.

### License and terms of use

The dataset page does not state a license. It lists a "Custom License", and the license details read "None" (dataset page above, checked 2026-11-01; the layer page shows the same).

The full metadata linked from that page ("View All Metadata", also `Dnr_Hydro_Features_All.xml` in the zip) gives Access Constraints and Use Constraints as None. Its Distribution Liability field points to the MNDNR General Data and Software License Agreement: https://www.dnr.state.mn.us/sitetools/data_software_license.html. That agreement allows derivative works if MNDNR is acknowledged as a contributor to them, and does not allow the complete data to be resold, distributed or displayed. Read it in full before reusing the data.

Credit: lake polygons and attributes are from the Minnesota Department of Natural Resources, DNR Hydrography Dataset, through the Minnesota Geospatial Commons.

## Setup

The results were computed with Python 3.13.5 (python.org installer) on macOS 26.6.2, on an Apple M4 (4 performance and 6 efficiency cores, 16 GB).

```bash
git clone https://github.com/Ntalatam/lake-fractals.git
cd lake-fractals
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p data/raw
# save the Shapefile download as data/raw/dnr_hydro_all.zip, then check it:
shasum -a 256 data/raw/dnr_hydro_all.zip
```

`requirements.txt` pins every package in the environment the results were computed with (`pip freeze` of `.venv`). The shapely, pyogrio and pyproj wheels bundle GEOS 3.14.1, GDAL 3.12.4 and PROJ 9.8.1.

## Reproducing the results

Run from the project root, in this order. Each script's docstring names its inputs, outputs and settings. Scripts that box-count many lakes use 4 worker processes, the performance cores (`default_workers` in `src/primary_analysis.py`). Runtimes are wall-clock times on the machine above.

| step | command | writes | runtime |
|---|---|---|---|
| 1 | `.venv/bin/python -m pytest` | nothing (the test suite) | 1 min 34 s |
| 2 | `.venv/bin/python src/filter_lakes.py` | `results/filter_log.csv`, `data/processed/lakes_filtered.gpkg` | 5 s |
| 3 | `.venv/bin/python src/pilot_windows.py` | `results/pilot/` | 1 min 30 s |
| 4 | `.venv/bin/python src/feasibility.py` | `results/feasibility/` | 17 s |
| 5 | `.venv/bin/python src/primary_analysis.py` | `results/primary/`, except the files of steps 6 and 7 | 5 min 28 s |
| 6 | `.venv/bin/python src/exploratory_10acre.py` | `results/primary/exploratory_10acre_*.csv` | 2 min 5 s |
| 7 | `.venv/bin/python src/summarize_primary.py` | `results/primary/summary.md` | under 1 s |
| 8 | `.venv/bin/python src/posthoc_outer_shore.py` | `results/exploratory/outer_shore/` | 1 min 15 s |
| 9 | `.venv/bin/python src/paper_figures.py` | `paper/figures/` | 2 s |
| 10 | `.venv/bin/python src/validation.py benchmarks below-one` | `results/validation/benchmarks.csv`, `below_one.csv` | 22 s |
| 11 | **long run:** `.venv/bin/python src/validation.py calibration` | `results/validation/calibration.csv`, `calibration_summary.csv` | 57 min 42 s (note 1) |
| 12 | **long run:** `.venv/bin/python src/validation_spacing.py` | `results/validation/spacing_0p01/` | 63 min 28 s (note 2) |
| 13 | `.venv/bin/python src/validation_width.py` | `results/validation/width.csv` and the other `width_*.csv` files, except `width_exclusion_*` | 17 s |
| 14 | `.venv/bin/python src/validation_width_exclusion.py` | `results/validation/width_exclusion_*.csv` | 16 s |
| 15 | `.venv/bin/python src/validation_blocks.py` | `results/validation/blocks_*.csv` | 54 s |
| 16 | `.venv/bin/python src/validation_vertices.py vertices` | `results/validation/vertices*.csv` | 6 s |
| 17 | **long run:** `.venv/bin/python src/validation_vertices.py equalized` | `results/validation/equalized_*.csv`, except `equalized_flags.csv` and `equalized_clean_*` | 31 min 36 s (note 3) |
| 18 | `.venv/bin/python src/validation_equalized_clean.py` | `results/validation/equalized_flags.csv`, `equalized_clean_*.csv` | 23 s (note 4) |

The three long runs were timed on their original runs on 2026-11-01, steps 1–10 and 13–16 on the fresh-clone run below.

1. Run as `taskpolicy -b .venv/bin/python src/validation.py calibration --workers 6`: 6 workers at background priority, which keeps them on the efficiency cores, while step 12 was running. Timed with `time`.
2. 4 workers, while step 11 was running. The time is for the whole script; its box counting alone took 3,790 s (`results/validation/spacing_0p01/runtime.csv`).
3. Timed as one run of the whole script, before steps 16 and 17 could be run apart; it includes step 16. 4 workers. The box-counting time of each rebuilt set is in `results/validation/equalized_runtime.csv`.
4. Timed on its first run, on 2026-11-02. It box-counts nothing: it rebuilds each lake's rings to flag them and reads the existing estimates.

Order matters:

- Step 5 reads the pilot lakes written by step 3.
- Step 7 reads the files of steps 5 and 6.
- Steps 8–10 and 12–18 read `results/primary/dims.csv`; step 11 uses synthetic shapes only.
- Steps 13–18 also read `results/validation/spacing_0p01/` from step 12.
- Step 14 reads `width.csv` from step 13.
- Step 18 reads the `equalized_*.csv` files of step 17.

By default the tests compare integer box counts exactly and floating values within a relative and absolute tolerance of 1e-12 (`tests/conftest.py`), so they pass on systems whose floating-point results differ in the last digits. Three tests require byte identity and are skipped unless asked for. Two compare with output written on the original computer, the golden box counts and the planned statistics files; one compares the default point spacing with an explicit 0.1. To run them:

```bash
LAKE_FRACTALS_EXACT=1 .venv/bin/python -m pytest
```

Steps 2–6, 8, 9, 12, 13 and 15–18 read lake geometry from `data/`, which is not in the repository. Step 2 reads the raw zip, and the others read `data/processed/lakes_filtered.gpkg`, which step 2 writes. So these steps need the lake data downloaded (Data, Setup) and filtered by step 2 first. Steps 1, 7, 10, 11 and 14 read no lake geometry: they read only committed files, or build shapes of known dimension (steps 10 and 11). Every results file is committed, so no step requires repeating the long runs before it.

The paper drafts (`paper/*.md`) are not generated by a script. Every number in them is followed by an HTML comment naming the csv file it comes from.

## What `results/validation/` holds

Post-hoc checks added after review. They are not in the analysis plan, and the planned results in `results/primary/` stay the main results. `results/validation/README.md` lists every file and which settings the author set.

- Shapes of known dimension (circle, Koch snowflakes, Sierpinski triangle) in the three windows, and a calibration near 1 with generalized Koch snowflakes and ellipses sized like the lakes.
- Lake estimates below 1. The limiting dimension of a polygon boundary is 1, but a slope fitted over a finite window of box sizes can fall below 1 through finite-window and numerical effects.
- A rerun of the primary analysis with boundary points 10 times closer together (`spacing_0p01/`), a sensitivity check. Every check that uses the lake estimates is run on both the planned estimates and these.
- Lake width: the diameter of the largest circle inside each lake, the minimum rotated rectangle, and the narrow-shore share (the share of shoreline in parts of the lake narrower than a window's largest box).
  - The narrow-shore sensitivity subset (`width_sensitivity_*.csv`) drops lakes by narrow-shore share. That share tracks the estimate (`width_rho.csv`), so the subset is selected on a near-proxy of the estimate and should not be interpreted.
  - The width-based exclusion (`width_exclusion_*.csv`) drops lakes by inscribed-circle diameter instead.
- Spatial block bootstrap: intervals from resampling 25, 50 and 100 km blocks of lakes instead of single lakes. The blocks address uncertainty from spatial clustering, not confounding between mapping source and region.
- Digitizing density: vertex spacing as digitized, by source group, and the estimates with every ring rebuilt at 25 m and 50 m vertex intervals (equalized resampling).
  - The equalized resampling narrowed the source gaps, but it also changed the geometry. It dropped every ring too short to keep 4 vertices: mostly island shores, plus a few outer rings of small separate parts of multipart lakes. It also left some polygons invalid. So it does not isolate vertex spacing, and a fall in the Kruskal–Wallis H is not a share of the source differences explained.
  - The clean-subset check, which the paper calls "resampling without ring loss or invalid polygons" (`equalized_flags.csv`, `equalized_clean_*.csv`), flags the lakes whose rebuilding dropped a ring or left an invalid polygon. It repeats the group medians, the gaps between groups, the spread and H on the lakes that kept every ring and a valid polygon.

## Analysis plan

The analysis plan is the "pre-registered design" section of `CLAUDE.md`, with the decisions recorded under it. It was committed to this git repository after a 200-lake pilot and before the full analysis. It was not submitted to a registry. Older files and commit messages that say "pre-registered" or "pre-registration" mean this committed plan. The pilot results informed the plan, and `CLAUDE.md` marks what was added after the primary results (the addendum and the disclosures found in audit).

Every commit that changed `CLAUDE.md`, and the pilot and primary-analysis commits, are below. Times are UTC on 2026-11-01. The commit date is the one git recorded; the push time is GitHub's (`docs/push_timeline.md` has every commit).

| commit | change | commit date | pushed to GitHub |
|---|---|---|---|
| f20606f | project setup: data, a 10-acre main sample, source groups; no windows or decision rule | 06:08:09 | 06:08:27 |
| d5a7e1d | 200-lake pilot (`results/pilot/`); `CLAUDE.md` unchanged | 06:22:07 | 06:22:08 |
| c4abc80 | analysis plan: 100-acre primary sample, 20–100 m window and two sensitivity windows, decision rule, pilot disclosure; feasibility check (`results/feasibility/`) | 06:28:37 | 06:28:38 |
| 5e041df | decision rule defined: same sign of rho in all three windows, for area and shoreline length separately | 06:34:56 | 06:34:57 |
| 7af119f | bootstrap intervals, pilot-lake sensitivity analysis, within-2004-FSA check, source groups and missing values | 06:44:11 | 06:44:13 |
| 9ecfa25 | primary analysis (`results/primary/`); `CLAUDE.md` unchanged | 06:59:02 | 06:59:03 |
| ff3908c | addendum after the results: percentile bootstrap | 07:06:00 | 07:06:01 |
| 6c24ab3 | disclosures found in audit, after the results | 07:39:06 | 07:39:10 |
| d61206b | rationale for the 20–100 m window, recorded after the results | 07:57:25 | 07:57:28 |
| 3b85cc7 | correction to the digitizing accuracy in that rationale | 08:17:10 | 09:17:14 |

Every commit was pushed on its own. For 6ff2e1f, b53487f and 3b85cc7 the push time is one hour after the commit date; for every other commit it is under a minute (`docs/push_timeline.md`).

## Reproduction from a fresh clone

On 2026-11-01, from 22:35 to 22:50 UTC, the repository was cloned from GitHub into a temporary folder at commit b610563, and this release's files were added before they were committed. Then:

- A new `.venv` was made as in Setup. pip installed all 23 pinned packages from its local cache.
- `dnr_hydro_all.zip` was copied in, and its SHA-256 matched the one above.
- Steps 1–10 and 13–16 were run as written above. The three long runs (steps 11, 12 and 17) were skipped.

All 120 tests passed, every step finished without error, and each output was compared with its committed version.

A rerun cannot reproduce timing fields. Before the run, the author exempted them from the comparison:

- the per-lake `runtime_s` column;
- the `median_s`, `max_s`, `wall_s` and slowest-lake columns of the runtime files;
- the Runtime table of `results/primary/summary.md`;
- the runtime lines of `results/pilot/pilot_summary.txt`.

Files with these fields still had to match in every row and every other column. Any other difference would have stopped the release.

Reproduced from a fresh clone:

- Byte for byte (43 files):
  - `results/filter_log.csv` and both files in `results/feasibility/`.
  - In `results/primary/`: `decision_rule.csv`, `kruskal_wallis.csv`, `parameters.csv`, `r2_below_threshold.csv`, `rho_primary.csv`, `rho_sensitivity_no_pilot.csv`, `rho_within_2004_fsa.csv`, `sample_log.csv`, `source_groups.csv`, `exploratory_10acre_r2_below_threshold.csv` and `exploratory_10acre_rho.csv`.
  - `results/exploratory/outer_shore/post-hoc_outer_shore_counts.csv` and `post-hoc_outer_shore_rho.csv`.
  - The four figures in `paper/figures/`.
  - In `results/validation/`: `benchmarks.csv`, `below_one.csv`, `width.csv` and all twelve `width_*.csv` files (`width_exclusion_*` included), the four `blocks_*.csv` files and the four `vertices*.csv` files.
- Identical except for the timing fields (8 files):
  - `results/primary/dims.csv`, `exploratory_10acre_dims.csv`, `runtime.csv`, `exploratory_10acre_runtime.csv` and `summary.md`.
  - `results/pilot/pilot_dims.csv` and `pilot_summary.txt`.
  - `results/exploratory/outer_shore/post-hoc_outer_shore_dims.csv`.
- `data/processed/lakes_filtered.gpkg`, which is not in git, holds the same lakes, attributes and geometry as the file the results were computed from.

Not reproduced from a fresh clone:

- The outputs of the three long runs:
  - `results/validation/calibration.csv` and `calibration_summary.csv` (step 11).
  - The 17 files in `results/validation/spacing_0p01/` (step 12). Steps 13–16 read the committed estimates there.
  - The six `results/validation/equalized_*.csv` files of step 17.
- Files that no script writes: `results/validation/README.md` and the paper drafts in `paper/`.
- Step 18 and its outputs (`equalized_flags.csv`, `equalized_clean_*.csv`), added on 2026-11-02, after this run.

The outputs were byte-identical on the original computer, apart from the timing fields. On another system, a reviewer's run of the test suite gave floating values that agreed with the original computer's to about 1e-15, with identical box counts. The default tests therefore compare floating values with a tolerance and keep byte identity for `LAKE_FRACTALS_EXACT=1` (Reproducing the results).

## Repository map

```
CLAUDE.md                  project notes and the analysis plan
README.md                  this file
LICENSE                    MIT license (code)
LICENSE-paper.md           CC BY 4.0 (paper text and figures)
CITATION.cff               how to cite
requirements.txt           pinned Python packages
pyproject.toml             pytest settings (tests import from src/)
.claude/settings.json      Claude Code project setting: no attribution lines in commits
src/
  boxcount.py              box-counting estimator
  filter_lakes.py          step 2: raw layer to the 10-acre sample, with a filter log
  pilot_windows.py         step 3: 200-lake pilot, before the analysis plan
  feasibility.py           step 4: lake sizes and fit quality, no estimates reported
  primary_analysis.py      step 5: the planned analysis
  exploratory_10acre.py    step 6: 10-acre sample, primary window
  summarize_primary.py     step 7: results/primary/summary.md
  posthoc_outer_shore.py   step 8: outer shore only (post-hoc)
  paper_figures.py         step 9: figures for the paper drafts
  validation*.py           steps 10-18: post-hoc validation
tests/                     pytest tests, written before the code they test
  conftest.py              tolerance for floating values; byte-identity tests run only with LAKE_FRACTALS_EXACT=1
  data/                    golden box counts for test_boxcount.py
data/                      not in git
  raw/                     dnr_hydro_all.zip
  processed/               lakes_filtered.gpkg (step 2)
results/
  filter_log.csv           counts before and after each filter step
  pilot/                   step 3
  feasibility/             step 4
  primary/                 steps 5-7: planned results and the exploratory 10-acre results
  exploratory/outer_shore/ step 8
  validation/              steps 10-18 (README.md lists every file)
paper/
  talatam_2026_minnesota_lake_shorelines.pdf   the paper (preprint, November 2, 2026)
  methods.md, results.md, limitations.md   drafts
  figures/                 step 9
docs/
  push_timeline.md         GitHub push times next to commit dates
  push_events.json         PushEvent entries from GitHub's events API (none returned)
  push_activity.json       GitHub's repository activity records, as returned
```

## Licenses

- Code: MIT (`LICENSE`).
- Paper text and figures: CC BY 4.0 (`LICENSE-paper.md`).
- Data: not included; see the MNDNR terms above.

## Citation

See `CITATION.cff`.
