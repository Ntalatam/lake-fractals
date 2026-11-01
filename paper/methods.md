# Methods

<!--
Draft for the author. Each number is followed by an HTML comment naming its
source. In a table, the comment in the last cell of a row covers every number
in that row. Sources under results/ are script outputs. A few numbers are
protocol constants or the author's stated reasoning that no script writes to
results/; their comments say "not in results/" and name where they come from.
Two sources are .txt files, not csv files: results/pilot/pilot_summary.txt and
results/feasibility/feasibility_summary.txt.
Negative numbers use an ASCII minus and p-values use e-notation, so every
number can be checked against its source by script.
-->

## Data

Lake polygons are from the Minnesota DNR Hydrography Dataset, layer "Dnr Hydro Features All", read directly from the distributed zip file. The file holds 130,912 records <!-- results/filter_log.csv: step 1, count_before -->. All lengths are measured in the layer's own coordinate system, EPSG:26915 <!-- results/filter_log.csv: step 4, description --> (NAD83 / UTM zone 15N, in meters <!-- CRS name: CLAUDE.md:8, not in results/ -->).

## Filters

Records were filtered in five steps, in the order of Table 1. Counts before and after each step are logged by src/filter_lakes.py.

**Table 1. Filter steps.** <!-- results/filter_log.csv: columns step, description, count_before, count_after, dropped -->

| step | records kept | before | after | removed |
|---|---|---|---|---|
| 1 | wb_class is "Lake or Pond" | 130,912 | 117,235 | 13,677 <!-- results/filter_log.csv: step 1 --> |
| 2 | acres at least 10 | 117,235 | 14,640 | 102,595 <!-- results/filter_log.csv: step 2 --> |
| 3 | geometry is not null | 14,640 | 14,640 | 0 <!-- results/filter_log.csv: step 3 --> |
| 4 | shoreline length at least 1,000 m | 14,640 | 13,382 | 1,258 <!-- results/filter_log.csv: step 4 --> |
| 5 | outside_mn is not "Y" or "B" | 13,382 | 13,269 | 113 <!-- results/filter_log.csv: step 5 --> |

Step 1 keeps natural lakes only; reservoirs and other water-body classes are not analyzed here. Step 3 removed nothing: the records without geometry have a blank wb_class, so step 1 had already removed them. Step 5 removes lakes entirely outside Minnesota ("Y") and lakes on the state border ("B"), whose polygons include shoreline outside the state; a blank outside_mn is kept.

The 13,269 lakes <!-- results/filter_log.csv: step 5, count_after --> that pass all five steps are the exploratory sample. The primary sample is the 3,274 of them <!-- results/primary/sample_log.csv: primary --> with acres of at least 100 <!-- results/primary/parameters.csv: primary_min_acres -->. The shoreline filter removes no lake from the primary sample <!-- CLAUDE.md:17, not in results/ -->, so it changes only the exploratory sample.

## Size measures

Area is the DNR acres attribute of each record, not the area of the polygon. Shoreline length (shoreline_m) is the perimeter of the polygon in EPSG:26915, summed over every ring: the outer shore and the shore of each island.

## Box-counting dimension

The boundary of a lake is every ring of its polygon, the outer shore and every island shore: the same boundary that shoreline length measures. The boundary is densified so that consecutive points are no more than one-tenth of the smallest box size apart <!-- src/boxcount.py:31 (DENSIFY_FRACTION = 0.1), not in results/ -->. For a box size s, a square grid with cells of side s is laid over the lake, and N(s) is the number of cells that hold at least one boundary point. The dimension is the least-squares slope of log N(s) against log(1/s) over the box sizes of a window.

Box counts depend on where the grid starts, so the grid origin is shifted in x and y by a random fraction of s. Eight such offsets are drawn with seed 0 <!-- results/primary/parameters.csv: grid_offsets, grid_seed -->. One slope is fitted per offset, and the lake's dimension is the median slope; its r² is the median r² of the per-offset fits. The same offset fractions are used for every lake.

**Windows.** Each window has 8 box sizes, evenly spaced on a log scale <!-- results/primary/parameters.csv: box_sizes_per_window -->, and all windows are run on the same lakes.

- Primary window: 20 to 100 m <!-- results/primary/rho_primary.csv: window 20_100, window_min_m and window_max_m -->.
- Sensitivity windows: 10 to 100 m and 20 to 200 m <!-- results/primary/rho_primary.csv: windows 10_100 and 20_200, window_min_m and window_max_m -->.

**Fit quality.** For each window, lakes with r² below 0.98 <!-- results/primary/parameters.csv: r2_threshold --> are counted and reported. No lake is excluded for poor fit.

**Checks on known shapes.** The estimator was tested on shapes of known dimension (tests/test_boxcount.py): a circle (1), a Koch snowflake (log 4 / log 3, about 1.262) and a Sierpinski triangle (log 3 / log 2, about 1.585) <!-- known values: CLAUDE.md:61, not in results/ -->. Each test passes if the estimate is within 0.05 of the known value <!-- tests/test_boxcount.py:16 (TOLERANCE), not in results/ -->. The three shapes were tested with box sizes from 10 to 100 m <!-- src/boxcount.py:16 (DEFAULT_BOX_SIZES), not in results/ -->. In all three analysis windows only the circle was tested (tests/test_primary_analysis.py). A first Koch test with a smaller snowflake failed and was replaced by a larger snowflake that is self-similar over the whole box range; the test's docstring records the failure.

## Pilot and pre-registration

The design was informed by the pilot results. The sequence, from the git history, was:

1. **Initial plan** (commit f20606f). The main sample was lakes of at least 10 acres, with a robustness check at 100 acres <!-- CLAUDE.md at commit f20606f, not in results/ -->.
2. **Pilot** (commit d5a7e1d), run before the design was recorded. From the 13,269 filtered lakes <!-- results/filter_log.csv: step 5, count_after -->, 200 lakes were drawn, 50 at random from each of four acreage bins, with seed 0 <!-- results/pilot/pilot_summary.txt (not a csv) --> (Table 2). Their dimensions were computed in a 10–100 m and a 20–200 m window <!-- CLAUDE.md:29 and src/pilot_windows.py:39-42, not in results/ --> and correlated with log(acres). Spearman rho was -0.2360 in the 10–100 m window and -0.4295 in the 20–200 m window <!-- results/pilot/pilot_summary.txt (not a csv) -->. Median dimension fell from the smallest bin to the 100 to 1,000 acre bin in both windows (Table 2). The size–dimension relationship in the pilot therefore changed with the window and was strongest in small lakes.
3. **Pre-registration** (commits c4abc80, 5e041df and 7af119f), recorded after the pilot and before any full-sample dimension was computed. It set the primary sample at 100 acres <!-- results/primary/parameters.csv: primary_min_acres -->; the primary window of 20 to 100 m <!-- results/primary/rho_primary.csv: window 20_100 -->, which the pilot had not used; the two sensitivity windows; the decision rule; the bootstrap intervals; the within-source check; the pilot-excluded sensitivity analysis; and the source groups and the handling of missing sources. The first of these commits also holds a feasibility check (src/feasibility.py). It box-counted 200 randomly chosen primary lakes in the primary window, with seed 0, and saved only their r² (median 0.9990) and the size of the primary lakes relative to the 100 m box <!-- results/feasibility/feasibility_summary.txt (not a csv) -->. It saved no dimension and computed no correlation.
4. **Primary results** (commit 9ecfa25).
5. **After the results**: the addendum on the bootstrap method (commit ff3908c), the post-hoc outer-shore check (commit 47f5fce) and the disclosures found in an audit (commit 6c24ab3).

**Table 2. Pilot: median dimension by acreage bin, 50 lakes per bin.** <!-- results/pilot/pilot_summary.txt (not a csv); bin labels also in results/pilot/pilot_dims.csv, column acreage_bin; window bounds: CLAUDE.md:29, not in results/ -->

| acreage bin | 10–100 m window | 20–200 m window |
|---|---|---|
| under 25 acres | 1.0377 | 1.1068 <!-- results/pilot/pilot_summary.txt: under 25 --> |
| 25 to 100 acres | 1.0225 | 1.0658 <!-- results/pilot/pilot_summary.txt: 25 to 100 --> |
| 100 to 1,000 acres | 1.0144 | 1.0338 <!-- results/pilot/pilot_summary.txt: 100 to 1,000 --> |
| over 1,000 acres | 1.0220 | 1.0453 <!-- results/pilot/pilot_summary.txt: over 1,000 --> |

### Why the primary sample starts at 100 acres

The primary sample was moved from the 10-acre lakes to the 100-acre lakes, which had been the robustness check, for two reasons. The move was made after the pilot.

**Finite-size bias.** A 10-acre lake is about 230 m across, roughly twice the 100 m box and close to the 200 m box <!-- author's figures: 230 m is the equivalent diameter, 2 * sqrt(area / pi), of a 10-acre circle; "twice" compares it with the 100 m box; not in results/ -->. When the largest box approaches the width of the lake, the box count levels off. This biases the dimension in one direction and can create a size trend on its own. In the primary sample the smallest lake has an equivalent diameter of 718 m <!-- results/feasibility/feasibility_summary.txt: min 717.8 (not a csv) -->, so the largest primary box is under one-seventh of the smallest lake's width <!-- author's figure, from the 100 m box and 717.8 m; not in results/ -->.

**Timing.** The switch was made after the 200-lake pilot (commit d5a7e1d), which showed that the size–dimension relationship changed with the window and was strongest in small lakes. The choice was therefore informed by the data, not specified in advance.

**Effect on the area result.** The 10-acre exploratory result shows that this choice changes the area conclusion. In the 10-acre sample, Spearman rho between dimension and area in the primary window is -0.2831 (95% CI -0.2988 to -0.2676) <!-- results/primary/exploratory_10acre_rho.csv: area -->, against -0.0048 (95% CI -0.0388 to 0.0291) in the primary sample <!-- results/primary/rho_primary.csv: 20_100, area -->. The 10-acre sample was run in the primary window only, so the decision rule was not applied to it.

### Exploratory sample

The 10-acre analysis is exploratory, and every 10-acre result is labeled exploratory. It was run in the primary window only. That window was chosen for this run (src/exploratory_10acre.py) and was not specified in the protocol.

## Statistical analysis

**Correlations.** In the primary sample, Spearman rho between dimension and each size measure, area and shoreline length, is computed in each window.

**Confidence intervals.** Each rho has a 95% <!-- results/primary/parameters.csv: ci_level_percent --> percentile bootstrap interval. Lakes are resampled with replacement 2,000 times with seed 0 <!-- results/primary/parameters.csv: bootstrap_resamples, bootstrap_seed -->, and the interval spans the central 95% <!-- results/primary/parameters.csv: ci_level_percent --> of the resampled rhos. The generator is re-seeded for each rho, so every rho within a sample is computed on the same resampled sets of lakes. The protocol fixed the number of resamples and the seed but not the interval method. The percentile method was recorded in an addendum written after the primary results (commit ff3908c); BCa intervals were considered after the results were reviewed and were not used.

**Decision rule (pre-registered).** The rule is applied separately to two relationships: dimension vs area, and dimension vs shoreline length. A relationship is supported only if rho has the same sign in all three windows <!-- results/primary/decision_rule.csv: columns rho_20_100, rho_10_100, rho_20_200 -->; otherwise it is reported as window-dependent. p-values and confidence intervals are reported but are not part of the rule.

**Mapping source comparison.** The delineat_1 attribute records how each shoreline was drawn. Source groups were set on the 10-acre sample, counted before the shoreline and outside_mn steps. Each value with at least 1,000 lakes stands alone: ORIG DLG (4,094), 2004 FSA (3,378), DNR 24k POLYS (3,182) and PWI (1,461) <!-- CLAUDE.md:39, not in results/ -->. Every other value, including 2010 FSA, is pooled as "other". The groups were kept unchanged for the primary sample. The 51 primary lakes with no delineat_1 <!-- results/primary/sample_log.csv: delineat_1 missing --> are kept in the correlations and left out of the source comparison, which uses 3,223 lakes <!-- results/primary/sample_log.csv: source comparison -->. Dimension is compared across the five groups <!-- results/primary/kruskal_wallis.csv: n_groups --> with a Kruskal–Wallis test in the primary window only. That window was set in the analysis code (src/primary_analysis.py), not in the protocol.

**Within-source check.** Spearman rho is recomputed within the 2004 FSA group only, 1,543 lakes <!-- results/primary/sample_log.csv: 2004 FSA only -->, in all three windows. It is reported alongside the decision rule, not as part of it.

**Pilot-excluded sensitivity analysis.** 100 pilot lakes are in the primary sample <!-- results/primary/sample_log.csv: pilot lakes in primary -->. The primary run uses all lakes. A sensitivity analysis repeats every correlation without the pilot lakes, on 3,174 lakes <!-- results/primary/sample_log.csv: primary without pilot lakes -->.

**Post-hoc check (not pre-registered).** After the primary results, the primary-window dimension was recomputed with every island ring removed, so that only the outer shore of each primary lake is box-counted. It was correlated with outer-shore length and with area (src/posthoc_outer_shore.py, commit 47f5fce). No decision rule is applied to it.

**Software.** Python, with geopandas, shapely, numpy, scipy, pandas and matplotlib. The analysis code is in src/.
