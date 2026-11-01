# Results

<!--
Draft for the author. Each number is followed by an HTML comment naming the
csv it comes from. In a table, the comment in the last cell of a row covers
every number in that row. rho, interval bounds and medians are rounded to 4
decimals, p-values to 3 significant figures and H to 2 decimals, as in
results/primary/summary.md. Negative numbers use an ASCII minus and p-values
use e-notation, so every number can be checked against its csv by script.
Tables are numbered after the two tables in methods.md.
-->

## Samples

The primary sample has 3,274 lakes <!-- results/primary/sample_log.csv: primary -->. Of these, 51 have no delineat_1 <!-- results/primary/sample_log.csv: delineat_1 missing --> and are left out of the source comparison only, which uses 3,223 lakes <!-- results/primary/sample_log.csv: source comparison -->. The 2004 FSA group has 1,543 lakes <!-- results/primary/sample_log.csv: 2004 FSA only -->. Of the primary lakes, 100 were in the pilot <!-- results/primary/sample_log.csv: pilot lakes in primary -->, leaving 3,174 without them <!-- results/primary/sample_log.csv: primary without pilot lakes -->. The exploratory 10-acre sample has 13,269 lakes <!-- results/primary/exploratory_10acre_rho.csv: n -->.

## Fit quality

No primary lake has r² below 0.98 <!-- results/primary/r2_below_threshold.csv: n_r2_below; threshold: results/primary/parameters.csv, r2_threshold --> in any window. The lowest r² is 0.9943 in the 20–100 m window, 0.9961 in the 10–100 m window and 0.9914 in the 20–200 m window <!-- results/primary/r2_below_threshold.csv: min_r2, window_min_m, window_max_m -->.

## Pre-registered decision rule

**Table 3. Spearman rho of dimension against shoreline length and area, primary sample, n = 3,274.** <!-- results/primary/rho_primary.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | window | rho | 95% CI | p |
|---|---|---|---|---|
| shoreline length | 20–100 m (primary) | 0.4099 | 0.3806 to 0.4381 | 7.14e-133 <!-- results/primary/rho_primary.csv: 20_100, shoreline --> |
| shoreline length | 10–100 m | 0.4261 | 0.3975 to 0.4537 | 1.43e-144 <!-- results/primary/rho_primary.csv: 10_100, shoreline --> |
| shoreline length | 20–200 m | 0.4240 | 0.3968 to 0.4514 | 4.73e-143 <!-- results/primary/rho_primary.csv: 20_200, shoreline --> |
| area | 20–100 m (primary) | -0.0048 | -0.0388 to 0.0291 | 0.784 <!-- results/primary/rho_primary.csv: 20_100, area --> |
| area | 10–100 m | 0.0197 | -0.0141 to 0.0535 | 0.259 <!-- results/primary/rho_primary.csv: 10_100, area --> |
| area | 20–200 m | -0.0590 | -0.0942 to -0.0247 | 0.000725 <!-- results/primary/rho_primary.csv: 20_200, area --> |

The outcome of the decision rule, as pre-registered <!-- results/primary/decision_rule.csv: direction, direction_holds, outcome -->:

- **Dimension vs shoreline length: supported.** rho is positive in all three windows.
- **Dimension vs area: window-dependent.** rho is negative in the 20–100 m and 20–200 m windows and positive in the 10–100 m window. Two of the three 95% confidence intervals, in the 20–100 m and 10–100 m windows, include zero; only the 20–200 m interval excludes it <!-- results/primary/rho_primary.csv: ci_low, ci_high -->.

Figures 1 and 2 show dimension against shoreline length and against area in the primary window.

## Within-source check: 2004 FSA only

Reported alongside the decision rule, not as part of it.

**Table 4. Spearman rho within the 2004 FSA group, n = 1,543.** <!-- results/primary/rho_within_2004_fsa.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | window | rho | 95% CI | p |
|---|---|---|---|---|
| shoreline length | 20–100 m (primary) | 0.4030 | 0.3589 to 0.4456 | 2.42e-61 <!-- results/primary/rho_within_2004_fsa.csv: 20_100, shoreline --> |
| shoreline length | 10–100 m | 0.4101 | 0.3660 to 0.4524 | 1.23e-63 <!-- results/primary/rho_within_2004_fsa.csv: 10_100, shoreline --> |
| shoreline length | 20–200 m | 0.4368 | 0.3943 to 0.4762 | 6.70e-73 <!-- results/primary/rho_within_2004_fsa.csv: 20_200, shoreline --> |
| area | 20–100 m (primary) | -0.0834 | -0.1338 to -0.0320 | 0.00104 <!-- results/primary/rho_within_2004_fsa.csv: 20_100, area --> |
| area | 10–100 m | -0.0689 | -0.1201 to -0.0169 | 0.00677 <!-- results/primary/rho_within_2004_fsa.csv: 10_100, area --> |
| area | 20–200 m | -0.1018 | -0.1523 to -0.0508 | 6.16e-05 <!-- results/primary/rho_within_2004_fsa.csv: 20_200, area --> |

Within 2004 FSA, rho with area is negative in all three windows and none of the three intervals includes zero. rho with shoreline length is positive in all three windows.

## Mapping source comparison (primary window)

**Table 5. Median primary-window dimension by mapping source group.** <!-- results/primary/source_groups.csv: columns group, n, median_dim -->

| group | lakes | median dimension, 20–100 m |
|---|---|---|
| 2004 FSA | 1,543 | 1.0289 <!-- results/primary/source_groups.csv: 2004 FSA --> |
| ORIG DLG | 293 | 1.0122 <!-- results/primary/source_groups.csv: ORIG DLG --> |
| DNR 24k POLYS | 223 | 1.0100 <!-- results/primary/source_groups.csv: DNR 24k POLYS --> |
| PWI | 54 | 1.0444 <!-- results/primary/source_groups.csv: PWI --> |
| other | 1,110 | 1.0242 <!-- results/primary/source_groups.csv: other --> |

A Kruskal–Wallis test across the five groups gives H = 170.90 and p = 6.71e-36, on 3,223 lakes, with the 51 lakes that have no delineat_1 excluded <!-- results/primary/kruskal_wallis.csv: n_groups, H, p_value, n_lakes, n_excluded_missing -->. The test was run in the primary window only. Figure 3 shows the group medians against the individual lakes.

## Sensitivity analysis: pilot lakes excluded

**Table 6. Spearman rho without the pilot lakes, n = 3,174.** <!-- results/primary/rho_sensitivity_no_pilot.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | window | rho | 95% CI | p |
|---|---|---|---|---|
| shoreline length | 20–100 m (primary) | 0.4182 | 0.3881 to 0.4480 | 1.23e-134 <!-- results/primary/rho_sensitivity_no_pilot.csv: 20_100, shoreline --> |
| shoreline length | 10–100 m | 0.4331 | 0.4042 to 0.4626 | 2.77e-145 <!-- results/primary/rho_sensitivity_no_pilot.csv: 10_100, shoreline --> |
| shoreline length | 20–200 m | 0.4360 | 0.4065 to 0.4643 | 2.01e-147 <!-- results/primary/rho_sensitivity_no_pilot.csv: 20_200, shoreline --> |
| area | 20–100 m (primary) | -0.0044 | -0.0357 to 0.0319 | 0.804 <!-- results/primary/rho_sensitivity_no_pilot.csv: 20_100, area --> |
| area | 10–100 m | 0.0187 | -0.0139 to 0.0544 | 0.293 <!-- results/primary/rho_sensitivity_no_pilot.csv: 10_100, area --> |
| area | 20–200 m | -0.0565 | -0.0898 to -0.0201 | 0.00144 <!-- results/primary/rho_sensitivity_no_pilot.csv: 20_200, area --> |

Every rho has the same sign as in the primary sample. For area, as in the primary sample, the 20–100 m and 10–100 m intervals include zero and the 20–200 m interval excludes it.

## Exploratory: 10-acre sample, primary window only

Exploratory. No decision rule is applied.

**Table 7. Spearman rho in the 10-acre sample, 20–100 m window, n = 13,269.** <!-- results/primary/exploratory_10acre_rho.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | rho | 95% CI | p |
|---|---|---|---|
| shoreline length | 0.0711 | 0.0549 to 0.0874 | 2.45e-16 <!-- results/primary/exploratory_10acre_rho.csv: shoreline --> |
| area | -0.2831 | -0.2988 to -0.2676 | 6.29e-243 <!-- results/primary/exploratory_10acre_rho.csv: area --> |

One lake has r² below 0.98; the lowest r² is 0.9799 <!-- results/primary/exploratory_10acre_r2_below_threshold.csv: n_r2_below, min_r2 -->. This sample passed the 1,000 m shoreline filter <!-- results/filter_log.csv: step 4, description -->, which removes compact small lakes (see Limitations).

## Post-hoc: outer shore only

Post-hoc and not pre-registered. No decision rule is applied.

Of the 3,274 primary lakes, 1,135 have at least one island ring, and for 1,094 the outer shore is more than 1% shorter than shoreline_m <!-- results/exploratory/outer_shore/post-hoc_outer_shore_counts.csv: n_lakes, n_with_interior_rings, n_exterior_more_than_1pct_shorter -->.

**Table 8. Spearman rho of the outer-shore dimension, island rings removed, 20–100 m window, n = 3,274.** <!-- results/exploratory/outer_shore/post-hoc_outer_shore_rho.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | rho | 95% CI | p |
|---|---|---|---|
| outer-shore dimension vs outer-shore length | 0.3646 | 0.3342 to 0.3942 | 1.75e-103 <!-- results/exploratory/outer_shore/post-hoc_outer_shore_rho.csv: exterior_length --> |
| outer-shore dimension vs area | -0.0244 | -0.0589 to 0.0090 | 0.163 <!-- results/exploratory/outer_shore/post-hoc_outer_shore_rho.csv: area --> |

## Figures

All four figures are drawn by src/paper_figures.py from the files named below. Numbers printed on a figure are read from those files. In Figures 1 to 3 a gray line marks dimension 1, the dimension of a smooth curve.

**Figure 1** (figures/fig1_dimension_vs_shoreline.png). Box-counting dimension in the primary window against shoreline length in kilometers, log scale, one point per primary lake. The printed rho and interval are from results/primary/rho_primary.csv. Data: results/primary/dims.csv.

**Figure 2** (figures/fig2_dimension_vs_area.png). Box-counting dimension in the primary window against area (DNR acres attribute), log scale, one point per primary lake. The printed rho and interval are from results/primary/rho_primary.csv. Data: results/primary/dims.csv.

**Figure 3** (figures/fig3_dimension_by_source.png). Median primary-window dimension per mapping source group (black bar; the value and the lake count are printed under each group), over every lake in the group (points, spread sideways at random with a fixed seed so they do not overlap). Lakes with no delineat_1 are not shown. Medians and counts: results/primary/source_groups.csv; lakes: results/primary/dims.csv; test: results/primary/kruskal_wallis.csv.

**Figure 4** (figures/fig4_map_dimension.png). Primary lakes, each drawn as one point inside its polygon, colored by primary-window dimension. Colors saturate below the 1st and above the 99th percentile of the dimension <!-- display choice: src/paper_figures.py, MAP_PERCENTILES -->, so a few extreme lakes do not compress the scale. Coordinates are EPSG:26915 in kilometers. Dimensions: results/primary/dims.csv; lake locations: data/processed/lakes_filtered.gpkg.
