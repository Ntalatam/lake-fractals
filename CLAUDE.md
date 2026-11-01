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
- main sample: wb_class 'Lake or Pond', acres >= 10 (14,640 lakes).
- robustness check: wb_class 'Lake or Pond', acres >= 100 (3,356 lakes).
- reservoirs: wb_class 'Reservoir' (37 at >= 10 acres). descriptive only, no hypothesis test.
- do not pool man-made classes (sewage, tailings, mine pits, artificial basins) into one group.

# mapping source groups (delineat_1)
- values with 1,000+ lakes in the main sample stand alone: ORIG DLG (4,094), 2004 FSA (3,378), DNR 24k POLYS (3,182), PWI (1,461).
- all other values pool into "other".

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
- missing delineat_1: 58 lakes in the main sample (51 at >= 100 acres) have no delineat_1 value. pool into "other", keep as their own group, or drop?
- source groups at >= 100 acres: the four stand-alone groups were set by main-sample counts. at >= 100 acres, PWI has only 60 lakes and 2010 FSA (327) outnumbers ORIG DLG (295). keep the main-sample groups for the robustness check, or regroup?
