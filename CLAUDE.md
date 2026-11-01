# project
title: Fractal Geometry of Minnesota Lake Shorelines: Area, Length, and Mapping Source
question: how do box-counting dimensions of natural lake shorelines relate to lake area and shoreline length, and how much does the mapping source change them?

# data
- source: Minnesota DNR Hydrography Dataset, layer "Dnr Hydro Features All"
- file: data/raw/dnr_hydro_all.zip (shapefile, read directly from the zip, never unzipped)
- crs: EPSG:26915 (NAD83 / UTM zone 15N, meters)
- 130,912 records in the full file
- key columns: wb_class (lake type), acres, shore_mi, dowlknum (lake id), delineat_1 (shoreline source: how the shoreline was drawn), dnr_region, cty_name
- do not use delineatio: it is a date with placeholder values of 9999 (3,286 in the full file; 3,186 in Lake or Pond + Reservoir; 2,540 in Lake or Pond + Reservoir at >= 10 acres).
- do not use delineat_2: it is free text.
- 3 records have no geometry. drop them and log the count.
- never modify or overwrite anything in data/raw

# sample
- primary sample: wb_class 'Lake or Pond', acres >= 100, shoreline_m >= 1,000, after the other filter steps in src/filter_lakes.py (non-null geometry, outside_mn not 'Y' or 'B'): 3,274 lakes. (3,356 without the outside_mn step. shoreline_m >= 1,000 drops none at >= 100 acres.)
- exploratory sample: the same filters at acres >= 10 (13,269 lakes, results/filter_log.csv). label every 10-acre result as exploratory.
- reservoirs: wb_class 'Reservoir' (37 at >= 10 acres). descriptive only, no hypothesis test.
- do not pool man-made classes (sewage, tailings, mine pits, artificial basins) into one group.

# pre-registered design (recorded 2026-11-01, before any full-sample dimension was computed)
- primary window: 8 log-spaced box sizes from 20 m to 100 m, 8 grid offsets from seed 0, median dimension across offsets.
- sensitivity windows, on the same lakes: 10 to 100 m, and 20 to 200 m (each 8 log-spaced sizes, 8 offsets from seed 0, median).
- decision rule: the size-dimension relationship is supported only if its direction holds in all three windows. otherwise report it as window-dependent.
- "direction holds" means spearman rho has the same sign in all three windows (author's decision, 2026-11-01). p-values are reported but are not part of the rule.
- the rule is applied separately to two relationships: dimension vs area, and dimension vs shoreline length. each is reported on its own as supported or window-dependent (author's decision, 2026-11-01).
- the 10-acre analysis is exploratory.
- disclosure: before this design was recorded, a 200-lake pilot (results/pilot/, commit d5a7e1d) computed dimensions and spearman correlations with log(acres) under the 10-100 m and 20-200 m windows, on a sample stratified across 10-acre-plus lakes.
- the design was informed by the pilot results. the methods must state this.
- pilot overlap: the 200-lake pilot (commit d5a7e1d) overlaps the primary sample (100 of its lakes are in it). the primary run uses all lakes, and a sensitivity analysis excludes the pilot lakes (author's decision, 2026-11-01).
- confidence intervals: a 95% bootstrap confidence interval for every spearman rho, 2,000 resamples, seed 0. reported alongside the decision rule, not part of it (author's decision, 2026-11-01).
- within-source check: spearman rho within the 2004 FSA group only (author's decision, 2026-11-01).

## addendum (2026-11-01, written after the primary results in commit 9ecfa25)
- percentile bootstrap, 2,000 resamples, seed 0. the protocol did not specify a method. BCa was considered after the primary results were reviewed and not used.

# mapping source groups (delineat_1)
- values with 1,000+ lakes in the 10-acre sample stand alone: ORIG DLG (4,094), 2004 FSA (3,378), DNR 24k POLYS (3,182), PWI (1,461). (counts before the shoreline and outside_mn steps.)
- all other values pool into "other".
- the groups were set on the 10-acre sample and are kept unchanged for the primary sample: 2004 FSA, ORIG DLG, DNR 24k POLYS and PWI stand alone, and every other value, including 2010 FSA, goes to "other". do not re-derive groups from 100-acre counts (author's decision, 2026-11-01).
- missing delineat_1 (51 lakes in the primary sample): kept in the area and shoreline tests, excluded from the source comparison. log the count (author's decision, 2026-11-01).

# tests
- kruskal-wallis: dimension across mapping source groups.
- spearman correlation: dimension vs area, and dimension vs shoreline length.
- fix the random seed for any permutation test.

# stack
python 3.13 in .venv. always run python as .venv/bin/python.
geopandas, shapely, numpy, scipy, pandas, matplotlib, pytest

# layout
data/raw   raw data (never modify, not in git)
src        analysis code
tests      pytest tests, written before analysis code
results    output tables, logs, and figures
paper      manuscript drafts

# rules
- write tests before analysis code. start with known shapes: circle about 1.0, koch curve about 1.262, sierpinski triangle about 1.585.
- fix random seeds for any randomized test (permutation tests, etc.).
- log every filtering step with counts before and after, saved to results/.
- every number in the paper must come from a script output in results/. no numbers from memory.
- comment each choice (scale range, cutoffs, tests) with why it was chosen, so the author can defend it.
- do not pick cutoffs, groupings, or tests on your own. propose options with reasoning and wait for approval.
- no network downloads. all data is local.
- git: never add co-author or "generated with" lines to commits. commits use the author's git identity only.

# open decisions (pending the author)
- none.
