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

## Planned decision rule

**Table 3. Spearman rho of dimension against shoreline length and area, primary sample, n = 3,274.** <!-- results/primary/rho_primary.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | window | rho | 95% CI <!-- level: results/primary/parameters.csv, ci_level_percent --> | p |
|---|---|---|---|---|
| shoreline length | 20–100 m (primary) | 0.4099 | 0.3806 to 0.4381 | 7.14e-133 <!-- results/primary/rho_primary.csv: 20_100, shoreline --> |
| shoreline length | 10–100 m | 0.4261 | 0.3975 to 0.4537 | 1.43e-144 <!-- results/primary/rho_primary.csv: 10_100, shoreline --> |
| shoreline length | 20–200 m | 0.4240 | 0.3968 to 0.4514 | 4.73e-143 <!-- results/primary/rho_primary.csv: 20_200, shoreline --> |
| area | 20–100 m (primary) | -0.0048 | -0.0388 to 0.0291 | 0.784 <!-- results/primary/rho_primary.csv: 20_100, area --> |
| area | 10–100 m | 0.0197 | -0.0141 to 0.0535 | 0.259 <!-- results/primary/rho_primary.csv: 10_100, area --> |
| area | 20–200 m | -0.0590 | -0.0942 to -0.0247 | 0.000725 <!-- results/primary/rho_primary.csv: 20_200, area --> |

The outcome of the decision rule, as planned <!-- results/primary/decision_rule.csv: direction, direction_holds, outcome -->:

- **Dimension vs shoreline length: supported.** rho is positive in all three windows.
- **Dimension vs area: window-dependent.** rho is negative in the 20–100 m and 20–200 m windows and positive in the 10–100 m window <!-- results/primary/rho_primary.csv: rho, window_min_m, window_max_m -->. Two of the three 95% <!-- results/primary/parameters.csv: ci_level_percent --> confidence intervals include zero, in the 20–100 m and 10–100 m windows <!-- results/primary/rho_primary.csv: ci_low, ci_high, window_min_m, window_max_m -->; only the 20–200 m interval excludes it <!-- results/primary/rho_primary.csv: ci_low, ci_high, window_min_m, window_max_m -->.

Figures 1 and 2 show dimension against shoreline length and against area in the primary window.

## Within-source check: 2004 FSA only

Reported alongside the decision rule, not as part of it.

**Table 4. Spearman rho within the 2004 FSA group, n = 1,543.** <!-- results/primary/rho_within_2004_fsa.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | window | rho | 95% CI <!-- level: results/primary/parameters.csv, ci_level_percent --> | p |
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

| group | lakes | median dimension, 20–100 m <!-- window bounds: results/primary/rho_primary.csv, window 20_100 --> |
|---|---|---|
| 2004 FSA | 1,543 | 1.0289 <!-- results/primary/source_groups.csv: 2004 FSA --> |
| ORIG DLG | 293 | 1.0122 <!-- results/primary/source_groups.csv: ORIG DLG --> |
| DNR 24k POLYS | 223 | 1.0100 <!-- results/primary/source_groups.csv: DNR 24k POLYS --> |
| PWI | 54 | 1.0444 <!-- results/primary/source_groups.csv: PWI --> |
| other | 1,110 | 1.0242 <!-- results/primary/source_groups.csv: other --> |

A Kruskal–Wallis test across the five groups gives H = 170.90 and p = 6.71e-36, on 3,223 lakes, with the 51 lakes that have no delineat_1 excluded <!-- results/primary/kruskal_wallis.csv: n_groups, H, p_value, n_lakes, n_excluded_missing -->. The test was run in the primary window only. Figure 3 shows the group medians against the individual lakes.

## Sensitivity analysis: pilot lakes excluded

**Table 6. Spearman rho without the pilot lakes, n = 3,174.** <!-- results/primary/rho_sensitivity_no_pilot.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | window | rho | 95% CI <!-- level: results/primary/parameters.csv, ci_level_percent --> | p |
|---|---|---|---|---|
| shoreline length | 20–100 m (primary) | 0.4182 | 0.3881 to 0.4480 | 1.23e-134 <!-- results/primary/rho_sensitivity_no_pilot.csv: 20_100, shoreline --> |
| shoreline length | 10–100 m | 0.4331 | 0.4042 to 0.4626 | 2.77e-145 <!-- results/primary/rho_sensitivity_no_pilot.csv: 10_100, shoreline --> |
| shoreline length | 20–200 m | 0.4360 | 0.4065 to 0.4643 | 2.01e-147 <!-- results/primary/rho_sensitivity_no_pilot.csv: 20_200, shoreline --> |
| area | 20–100 m (primary) | -0.0044 | -0.0357 to 0.0319 | 0.804 <!-- results/primary/rho_sensitivity_no_pilot.csv: 20_100, area --> |
| area | 10–100 m | 0.0187 | -0.0139 to 0.0544 | 0.293 <!-- results/primary/rho_sensitivity_no_pilot.csv: 10_100, area --> |
| area | 20–200 m | -0.0565 | -0.0898 to -0.0201 | 0.00144 <!-- results/primary/rho_sensitivity_no_pilot.csv: 20_200, area --> |

Every rho has the same sign as in the primary sample. For area, as in the primary sample, the 20–100 m and 10–100 m intervals include zero and the 20–200 m interval excludes it <!-- results/primary/rho_sensitivity_no_pilot.csv: ci_low, ci_high, window_min_m, window_max_m -->.

## Exploratory: 10-acre sample, primary window only <!-- results/primary/exploratory_10acre_r2_below_threshold.csv: min_acres -->

Exploratory. No decision rule is applied.

**Table 7. Spearman rho in the 10-acre sample, 20–100 m window, n = 13,269.** <!-- results/primary/exploratory_10acre_rho.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | rho | 95% CI <!-- level: results/primary/parameters.csv, ci_level_percent --> | p |
|---|---|---|---|
| shoreline length | 0.0711 | 0.0549 to 0.0874 | 2.45e-16 <!-- results/primary/exploratory_10acre_rho.csv: shoreline --> |
| area | -0.2831 | -0.2988 to -0.2676 | 6.29e-243 <!-- results/primary/exploratory_10acre_rho.csv: area --> |

One lake has r² below 0.98 <!-- results/primary/parameters.csv: r2_threshold -->; the lowest r² is 0.9799 <!-- results/primary/exploratory_10acre_r2_below_threshold.csv: n_r2_below, min_r2 -->. This sample passed the 1,000 m shoreline filter <!-- results/filter_log.csv: step 4, description -->, which removes compact small lakes (see Limitations).

## Post-hoc: outer shore only

Post-hoc and not in the analysis plan. No decision rule is applied.

Of the 3,274 primary lakes, 1,135 have at least one island ring, and for 1,094 the outer shore is more than 1% shorter than shoreline_m <!-- results/exploratory/outer_shore/post-hoc_outer_shore_counts.csv: n_lakes, n_with_interior_rings, n_exterior_more_than_1pct_shorter -->.

**Table 8. Spearman rho of the outer-shore dimension, island rings removed, 20–100 m window, n = 3,274.** <!-- results/exploratory/outer_shore/post-hoc_outer_shore_rho.csv: columns measure, window_min_m, window_max_m, n, rho, ci_low, ci_high, p_value -->

| relationship | rho | 95% CI <!-- level: results/primary/parameters.csv, ci_level_percent --> | p |
|---|---|---|---|
| outer-shore dimension vs outer-shore length | 0.3646 | 0.3342 to 0.3942 | 1.75e-103 <!-- results/exploratory/outer_shore/post-hoc_outer_shore_rho.csv: exterior_length --> |
| outer-shore dimension vs area | -0.0244 | -0.0589 to 0.0090 | 0.163 <!-- results/exploratory/outer_shore/post-hoc_outer_shore_rho.csv: area --> |

## Post-hoc validation (not in the analysis plan)

Post-hoc checks made after review (Methods). They are not part of the analysis plan, and the planned results above remain the main results. Each check that uses the lake estimates was run twice, on the planned estimates and on the estimates recomputed with boundary points at most 0.01 of the smallest box apart (spacing 0.01) <!-- results/validation/spacing_0p01/parameters.csv: densify_fraction -->, and the two are shown side by side. Spacing 0.01 is a sensitivity check.

### Shapes of known dimension

**Table 9. Box-counting estimates for shapes of known dimension, planned point spacing.** <!-- results/validation/benchmarks.csv: columns shape, parameters, window, known_d, estimate -->

| shape | known dimension | 20–100 m | 10–100 m | 20–200 m |
|---|---|---|---|---|
| circle, radius 2,000 m | 1.0000 | 0.9863 | 0.9913 | 0.9934 <!-- results/validation/benchmarks.csv: circle, radius_m=2000; quad_segs=512 --> |
| Koch snowflake, 6 iterations | 1.2619 | 1.2489 | 1.2281 | 1.2524 <!-- results/validation/benchmarks.csv: koch, iterations=6; side_m=7290; smallest_segment_m=10; bumps=outward --> |
| Koch snowflake, 7 iterations | 1.2619 | 1.2556 | 1.2468 | 1.2587 <!-- results/validation/benchmarks.csv: koch, iterations=7; side_m=7290; smallest_segment_m=3.33; bumps=outward --> |
| Sierpinski triangle, 8 levels | 1.5850 | 1.5765 | 1.5706 | 1.5752 <!-- results/validation/benchmarks.csv: sierpinski, levels=8; side_m=1280; smallest_side_m=5 --> |

**Table 10. Calibration near 1: mean bias of the ellipse estimates (lowest and highest of the nine areas and axis ratios), bias of the circle, and the generalized Koch estimates.** <!-- results/validation/calibration_summary.csv: columns shape, known_d, window, densify_fraction, bias, mean_estimate -->

| window | point spacing | ellipses, mean bias | circle, bias | Koch 1.02 | Koch 1.05 | Koch 1.10 |
|---|---|---|---|---|---|---|
| 20–100 m | 0.1 | -0.0143 to -0.0014 | -0.0137 | 1.0155 | 1.0461 | 1.1099 <!-- results/validation/calibration_summary.csv: window 20_100, densify_fraction 0.1 --> |
| 20–100 m | 0.03 | -0.0049 to 0.0067 | -0.0041 | 1.0189 | 1.0478 | 1.1138 <!-- results/validation/calibration_summary.csv: window 20_100, densify_fraction 0.03 --> |
| 20–100 m | 0.01 | -0.0015 to 0.0089 | -0.0016 | 1.0200 | 1.0494 | 1.1153 <!-- results/validation/calibration_summary.csv: window 20_100, densify_fraction 0.01 --> |
| 10–100 m | 0.1 | -0.0111 to -0.0029 | -0.0087 | 1.0120 | 1.0494 | 1.0981 <!-- results/validation/calibration_summary.csv: window 10_100, densify_fraction 0.1 --> |
| 10–100 m | 0.03 | -0.0030 to 0.0035 | -0.0030 | 1.0154 | 1.0530 | 1.1011 <!-- results/validation/calibration_summary.csv: window 10_100, densify_fraction 0.03 --> |
| 10–100 m | 0.01 | -0.0011 to 0.0052 | -0.0013 | 1.0169 | 1.0543 | 1.1021 <!-- results/validation/calibration_summary.csv: window 10_100, densify_fraction 0.01 --> |
| 20–200 m | 0.1 | -0.0100 to 0.0349 | -0.0066 | 1.0179 | 1.0472 | 1.1046 <!-- results/validation/calibration_summary.csv: window 20_200, densify_fraction 0.1 --> |
| 20–200 m | 0.03 | -0.0041 to 0.0416 | -0.0014 | 1.0199 | 1.0490 | 1.1076 <!-- results/validation/calibration_summary.csv: window 20_200, densify_fraction 0.03 --> |
| 20–200 m | 0.01 | -0.0020 to 0.0433 | -0.0007 | 1.0191 | 1.0495 | 1.1083 <!-- results/validation/calibration_summary.csv: window 20_200, densify_fraction 0.01 --> |

Each ellipse row covers 40 draws <!-- results/validation/calibration_summary.csv: n -->. The 100-acre ellipse with an axis ratio of 10 gives the highest ellipse bias in the 20–200 m window <!-- results/validation/calibration_summary.csv: target_acres, aspect_ratio, window 20_200, bias -->. Every shape is a valid polygon <!-- results/validation/benchmarks.csv: is_valid; results/validation/calibration_summary.csv: all_valid -->.

### Estimates below 1

**Table 11. Primary lakes with an estimate below 1, n = 3,274.** <!-- results/validation/spacing_0p01/comparison_below_one.csv: columns window, n_lakes, n_below_1_planned, n_below_1_rerun, percent_below_1_planned, percent_below_1_rerun, min_below_1_planned, min_below_1_rerun -->

| window | planned: below 1 | planned: lowest | spacing 0.01: below 1 | spacing 0.01: lowest |
|---|---|---|---|---|
| 20–100 m (primary) | 497 (15.2%) | 0.9667 | 138 (4.2%) | 0.9742 <!-- results/validation/spacing_0p01/comparison_below_one.csv: 20_100 --> |
| 10–100 m | 512 (15.6%) | 0.9768 | 110 (3.4%) | 0.9843 <!-- results/validation/spacing_0p01/comparison_below_one.csv: 10_100 --> |
| 20–200 m | 258 (7.9%) | 0.9779 | 74 (2.3%) | 0.9869 <!-- results/validation/spacing_0p01/comparison_below_one.csv: 20_200 --> |

### Spacing rerun

**Table 12. Spearman rho, primary sample, planned estimates and spacing 0.01, n = 3,274.** <!-- results/validation/spacing_0p01/comparison_rho.csv: sample primary, columns window, measure, n, rho_planned, ci_low_planned, ci_high_planned, rho_rerun, ci_low_rerun, ci_high_rerun -->

| relationship | window | rho, planned | 95% CI, planned | rho, spacing 0.01 | 95% CI, spacing 0.01 |
|---|---|---|---|---|---|
| shoreline length | 20–100 m (primary) | 0.4099 | 0.3806 to 0.4381 | 0.4106 | 0.3813 to 0.4386 <!-- results/validation/spacing_0p01/comparison_rho.csv: primary, 20_100, shoreline --> |
| shoreline length | 10–100 m | 0.4261 | 0.3975 to 0.4537 | 0.4267 | 0.3975 to 0.4541 <!-- results/validation/spacing_0p01/comparison_rho.csv: primary, 10_100, shoreline --> |
| shoreline length | 20–200 m | 0.4240 | 0.3968 to 0.4514 | 0.4250 | 0.3977 to 0.4520 <!-- results/validation/spacing_0p01/comparison_rho.csv: primary, 20_200, shoreline --> |
| area | 20–100 m (primary) | -0.0048 | -0.0388 to 0.0291 | -0.0066 | -0.0402 to 0.0280 <!-- results/validation/spacing_0p01/comparison_rho.csv: primary, 20_100, area --> |
| area | 10–100 m | 0.0197 | -0.0141 to 0.0535 | 0.0203 | -0.0132 to 0.0539 <!-- results/validation/spacing_0p01/comparison_rho.csv: primary, 10_100, area --> |
| area | 20–200 m | -0.0590 | -0.0942 to -0.0247 | -0.0585 | -0.0931 to -0.0248 <!-- results/validation/spacing_0p01/comparison_rho.csv: primary, 20_200, area --> |

At spacing 0.01 the decision rule gives the same outcomes as planned: shoreline length supported, area window-dependent <!-- results/validation/spacing_0p01/comparison_decision_rule.csv: outcome_planned, outcome_rerun, same_outcome -->. Every rho in the primary sample, within 2004 FSA and without the pilot lakes keeps its sign, and every 95% interval keeps its inclusion or exclusion of zero <!-- results/validation/spacing_0p01/comparison_rho.csv: same_sign, same_ci_status -->. The Kruskal–Wallis H is 164.98 (p = 1.25e-34), against 170.90 (p = 6.71e-36) with the planned estimates <!-- results/validation/spacing_0p01/comparison_kruskal_wallis.csv: H_planned, H_rerun, p_value_planned, p_value_rerun -->.

### Lake width

**Table 13. Width of the primary lakes, n = 3,274.** <!-- results/validation/width_summary.csv: columns measure, n, min, p5, p25, median, p75, p95, max -->

| measure | min | 5th pct | 25th pct | median | 75th pct | 95th pct | max |
|---|---|---|---|---|---|---|---|
| largest inscribed circle, diameter (m) | 166 | 341 | 475 | 610 | 831 | 1,589 | 23,010 <!-- results/validation/width_summary.csv: inscribed_diameter_m --> |
| minimum rotated rectangle, short side (m) | 332 | 558 | 739 | 937 | 1,377 | 2,909 | 48,047 <!-- results/validation/width_summary.csv: rectangle_short_side_m --> |
| narrow-shore share, 100 m box | 0.000 | 0.037 | 0.106 | 0.185 | 0.306 | 0.514 | 0.841 <!-- results/validation/width_summary.csv: narrow_share_r50 --> |
| narrow-shore share, 200 m box | 0.002 | 0.132 | 0.287 | 0.434 | 0.606 | 0.832 | 1.000 <!-- results/validation/width_summary.csv: narrow_share_r100 --> |

The inscribed diameter is below 200 m for 3 lakes and below 400 m for 420 (12.8%) <!-- results/validation/width_counts.csv: inscribed_diameter_m, threshold, n_lakes, percent -->. The narrow-shore share is above 0.10 for 2,529 lakes (77.2%) for the 100 m box and 3,176 (97.0%) for the 200 m box <!-- results/validation/width_counts.csv: narrow_share_r50, narrow_share_r100, threshold, n_lakes, percent -->.

**Table 14. Spearman rho of the narrow-shore share for each window's largest box against the estimate in that window, n = 3,274.** <!-- results/validation/width_rho.csv: columns dims, window, narrow_share_column, n, rho, ci_low, ci_high -->

| window | largest box | rho, planned | 95% CI, planned | rho, spacing 0.01 | 95% CI, spacing 0.01 |
|---|---|---|---|---|---|
| 20–100 m (primary) | 100 m | 0.8646 | 0.8540 to 0.8744 | 0.8617 | 0.8506 to 0.8718 <!-- results/validation/width_rho.csv: 20_100 --> |
| 10–100 m | 100 m | 0.8708 | 0.8608 to 0.8804 | 0.8709 | 0.8610 to 0.8806 <!-- results/validation/width_rho.csv: 10_100 --> |
| 20–200 m | 200 m | 0.8692 | 0.8590 to 0.8786 | 0.8682 | 0.8580 to 0.8775 <!-- results/validation/width_rho.csv: 20_200 --> |

Against area, rho is -0.1319 (-0.1652 to -0.0984) for the 100 m box and -0.2690 (-0.3032 to -0.2373) for the 200 m box <!-- results/validation/width_rho_acres.csv: rho, ci_low, ci_high -->.

**Table 15. Narrow-shore sensitivity check: Spearman rho without the lakes whose narrow-shore share for the window's largest box is above 0.10.** <!-- results/validation/width_sensitivity_rho.csv: columns dims, window, measure, n, n_excluded, rho, ci_low, ci_high; cutoff: results/validation/width_parameters.csv, max_narrow_share -->

| relationship | window | lakes kept | rho, planned | 95% CI, planned | rho, spacing 0.01 | 95% CI, spacing 0.01 |
|---|---|---|---|---|---|---|
| shoreline length | 20–100 m (primary) | 745 | 0.3027 | 0.2322 to 0.3687 | 0.2942 | 0.2259 to 0.3604 <!-- results/validation/width_sensitivity_rho.csv: 20_100, shoreline --> |
| shoreline length | 10–100 m | 745 | 0.3290 | 0.2611 to 0.3936 | 0.3290 | 0.2615 to 0.3927 <!-- results/validation/width_sensitivity_rho.csv: 10_100, shoreline --> |
| shoreline length | 20–200 m | 98 | 0.2349 | 0.0267 to 0.4139 | 0.2039 | -0.0109 to 0.3894 <!-- results/validation/width_sensitivity_rho.csv: 20_200, shoreline --> |
| area | 20–100 m (primary) | 745 | 0.1808 | 0.1080 to 0.2535 | 0.1754 | 0.1028 to 0.2464 <!-- results/validation/width_sensitivity_rho.csv: 20_100, area --> |
| area | 10–100 m | 745 | 0.2055 | 0.1364 to 0.2794 | 0.2122 | 0.1435 to 0.2853 <!-- results/validation/width_sensitivity_rho.csv: 10_100, area --> |
| area | 20–200 m | 98 | 0.1950 | -0.0109 to 0.3814 | 0.1657 | -0.0527 to 0.3550 <!-- results/validation/width_sensitivity_rho.csv: 20_200, area --> |

With the planned decision rule applied to these subsets, both relationships are supported, with rho positive in all three windows, for the planned estimates and for spacing 0.01 (area: supported; shoreline length: supported) <!-- results/validation/width_sensitivity_decision_rule.csv: dims, measure, direction, outcome -->. With all lakes, the area relationship is window-dependent <!-- results/validation/width_sensitivity_decision_rule.csv: outcome_all_lakes -->. The subsets differ by window: 745 lakes in the two windows whose largest box is 100 m and 98 in the 20–200 m window <!-- results/validation/width_sensitivity_rho.csv: window, n -->.

### Spatial block bootstrap

**Table 16. Blocks and lakes per block.** <!-- results/validation/blocks_counts.csv: columns block_km, sample, n_lakes, n_blocks, lakes_per_block_min, lakes_per_block_median, lakes_per_block_max -->

| block size | sample | lakes | blocks | lakes per block, min | median | max |
|---|---|---|---|---|---|---|
| 25 km | primary | 3,274 | 273 | 1 | 9 | 66 <!-- results/validation/blocks_counts.csv: 25, primary --> |
| 25 km | 2004 FSA only | 1,543 | 227 | 1 | 4 | 38 <!-- results/validation/blocks_counts.csv: 25, 2004 FSA only --> |
| 50 km | primary | 3,274 | 91 | 1 | 24 | 148 <!-- results/validation/blocks_counts.csv: 50, primary --> |
| 50 km | 2004 FSA only | 1,543 | 82 | 1 | 12 | 91 <!-- results/validation/blocks_counts.csv: 50, 2004 FSA only --> |
| 100 km | primary | 3,274 | 30 | 1 | 76 | 326 <!-- results/validation/blocks_counts.csv: 100, primary --> |
| 100 km | 2004 FSA only | 1,543 | 28 | 1 | 38 | 174 <!-- results/validation/blocks_counts.csv: 100, 2004 FSA only --> |

**Table 17. 95% intervals for Spearman rho, planned estimates: lakes resampled, and blocks resampled.** <!-- results/validation/blocks_rho.csv: dims planned, columns sample, window, measure, n, rho, interval, block_km, ci_low, ci_high -->

| sample | relationship | window | rho | lakes | 25 km blocks | 50 km blocks | 100 km blocks |
|---|---|---|---|---|---|---|---|
| primary | shoreline length | 20–100 m | 0.4099 | 0.3806 to 0.4381 | 0.3678 to 0.4502 | 0.3575 to 0.4668 | 0.3531 to 0.4754 <!-- results/validation/blocks_rho.csv: planned, primary, 20_100, shoreline --> |
| primary | shoreline length | 10–100 m | 0.4261 | 0.3975 to 0.4537 | 0.3859 to 0.4639 | 0.3754 to 0.4778 | 0.3739 to 0.4878 <!-- results/validation/blocks_rho.csv: planned, primary, 10_100, shoreline --> |
| primary | shoreline length | 20–200 m | 0.4240 | 0.3968 to 0.4514 | 0.3841 to 0.4635 | 0.3727 to 0.4791 | 0.3629 to 0.4918 <!-- results/validation/blocks_rho.csv: planned, primary, 20_200, shoreline --> |
| primary | area | 20–100 m | -0.0048 | -0.0388 to 0.0291 | -0.0428 to 0.0335 | -0.0443 to 0.0386 | -0.0388 to 0.0339 <!-- results/validation/blocks_rho.csv: planned, primary, 20_100, area --> |
| primary | area | 10–100 m | 0.0197 | -0.0141 to 0.0535 | -0.0187 to 0.0586 | -0.0190 to 0.0619 | -0.0135 to 0.0552 <!-- results/validation/blocks_rho.csv: planned, primary, 10_100, area --> |
| primary | area | 20–200 m | -0.0590 | -0.0942 to -0.0247 | -0.0960 to -0.0221 | -0.0985 to -0.0133 | -0.0946 to -0.0201 <!-- results/validation/blocks_rho.csv: planned, primary, 20_200, area --> |
| 2004 FSA only | shoreline length | 20–100 m | 0.4030 | 0.3589 to 0.4456 | 0.3364 to 0.4706 | 0.3097 to 0.4814 | 0.3027 to 0.4963 <!-- results/validation/blocks_rho.csv: planned, 2004 FSA only, 20_100, shoreline --> |
| 2004 FSA only | shoreline length | 10–100 m | 0.4101 | 0.3660 to 0.4524 | 0.3464 to 0.4759 | 0.3212 to 0.4877 | 0.3130 to 0.4987 <!-- results/validation/blocks_rho.csv: planned, 2004 FSA only, 10_100, shoreline --> |
| 2004 FSA only | shoreline length | 20–200 m | 0.4368 | 0.3943 to 0.4762 | 0.3768 to 0.4995 | 0.3498 to 0.5113 | 0.3422 to 0.5213 <!-- results/validation/blocks_rho.csv: planned, 2004 FSA only, 20_200, shoreline --> |
| 2004 FSA only | area | 20–100 m | -0.0834 | -0.1338 to -0.0320 | -0.1404 to -0.0242 | -0.1513 to -0.0131 | -0.1213 to -0.0355 <!-- results/validation/blocks_rho.csv: planned, 2004 FSA only, 20_100, area --> |
| 2004 FSA only | area | 10–100 m | -0.0689 | -0.1201 to -0.0169 | -0.1247 to -0.0086 | -0.1321 to 0.0017 | -0.1095 to -0.0230 <!-- results/validation/blocks_rho.csv: planned, 2004 FSA only, 10_100, area --> |
| 2004 FSA only | area | 20–200 m | -0.1018 | -0.1523 to -0.0508 | -0.1563 to -0.0400 | -0.1705 to -0.0292 | -0.1437 to -0.0540 <!-- results/validation/blocks_rho.csv: planned, 2004 FSA only, 20_200, area --> |

**Table 18. 95% intervals for Spearman rho, spacing 0.01: lakes resampled, and blocks resampled.** <!-- results/validation/blocks_rho.csv: dims spacing_0p01, columns sample, window, measure, n, rho, interval, block_km, ci_low, ci_high -->

| sample | relationship | window | rho | lakes | 25 km blocks | 50 km blocks | 100 km blocks |
|---|---|---|---|---|---|---|---|
| primary | shoreline length | 20–100 m | 0.4106 | 0.3813 to 0.4386 | 0.3688 to 0.4508 | 0.3593 to 0.4662 | 0.3541 to 0.4756 <!-- results/validation/blocks_rho.csv: spacing_0p01, primary, 20_100, shoreline --> |
| primary | shoreline length | 10–100 m | 0.4267 | 0.3975 to 0.4541 | 0.3863 to 0.4644 | 0.3771 to 0.4774 | 0.3750 to 0.4865 <!-- results/validation/blocks_rho.csv: spacing_0p01, primary, 10_100, shoreline --> |
| primary | shoreline length | 20–200 m | 0.4250 | 0.3977 to 0.4520 | 0.3852 to 0.4642 | 0.3734 to 0.4799 | 0.3639 to 0.4929 <!-- results/validation/blocks_rho.csv: spacing_0p01, primary, 20_200, shoreline --> |
| primary | area | 20–100 m | -0.0066 | -0.0402 to 0.0280 | -0.0437 to 0.0308 | -0.0449 to 0.0360 | -0.0394 to 0.0310 <!-- results/validation/blocks_rho.csv: spacing_0p01, primary, 20_100, area --> |
| primary | area | 10–100 m | 0.0203 | -0.0132 to 0.0539 | -0.0174 to 0.0596 | -0.0183 to 0.0623 | -0.0131 to 0.0554 <!-- results/validation/blocks_rho.csv: spacing_0p01, primary, 10_100, area --> |
| primary | area | 20–200 m | -0.0585 | -0.0931 to -0.0248 | -0.0954 to -0.0213 | -0.0984 to -0.0129 | -0.0944 to -0.0191 <!-- results/validation/blocks_rho.csv: spacing_0p01, primary, 20_200, area --> |
| 2004 FSA only | shoreline length | 20–100 m | 0.4065 | 0.3633 to 0.4489 | 0.3395 to 0.4731 | 0.3135 to 0.4838 | 0.3073 to 0.4989 <!-- results/validation/blocks_rho.csv: spacing_0p01, 2004 FSA only, 20_100, shoreline --> |
| 2004 FSA only | shoreline length | 10–100 m | 0.4123 | 0.3687 to 0.4542 | 0.3478 to 0.4778 | 0.3229 to 0.4893 | 0.3153 to 0.4996 <!-- results/validation/blocks_rho.csv: spacing_0p01, 2004 FSA only, 10_100, shoreline --> |
| 2004 FSA only | shoreline length | 20–200 m | 0.4379 | 0.3959 to 0.4775 | 0.3779 to 0.5009 | 0.3506 to 0.5125 | 0.3428 to 0.5230 <!-- results/validation/blocks_rho.csv: spacing_0p01, 2004 FSA only, 20_200, shoreline --> |
| 2004 FSA only | area | 20–100 m | -0.0820 | -0.1311 to -0.0306 | -0.1375 to -0.0222 | -0.1483 to -0.0107 | -0.1195 to -0.0365 <!-- results/validation/blocks_rho.csv: spacing_0p01, 2004 FSA only, 20_100, area --> |
| 2004 FSA only | area | 10–100 m | -0.0664 | -0.1169 to -0.0128 | -0.1219 to -0.0071 | -0.1296 to 0.0037 | -0.1074 to -0.0203 <!-- results/validation/blocks_rho.csv: spacing_0p01, 2004 FSA only, 10_100, area --> |
| 2004 FSA only | area | 20–200 m | -0.1010 | -0.1521 to -0.0499 | -0.1568 to -0.0384 | -0.1697 to -0.0293 | -0.1435 to -0.0529 <!-- results/validation/blocks_rho.csv: spacing_0p01, 2004 FSA only, 20_200, area --> |

**Table 19. Median primary-window dimension by source group, with 95% intervals: lakes resampled, and blocks resampled within each group.** <!-- results/validation/blocks_medians.csv: columns dims, group, n, median, interval, block_km, ci_low, ci_high -->

| group | estimates | lakes | median | lakes | 25 km blocks | 50 km blocks | 100 km blocks |
|---|---|---|---|---|---|---|---|
| 2004 FSA | planned | 1,543 | 1.0289 | 1.0264 to 1.0311 | 1.0237 to 1.0343 | 1.0216 to 1.0371 | 1.0209 to 1.0425 <!-- results/validation/blocks_medians.csv: planned, 2004 FSA --> |
| 2004 FSA | spacing 0.01 | 1,543 | 1.0388 | 1.0363 to 1.0407 | 1.0335 to 1.0441 | 1.0319 to 1.0471 | 1.0313 to 1.0519 <!-- results/validation/blocks_medians.csv: spacing_0p01, 2004 FSA --> |
| ORIG DLG | planned | 293 | 1.0122 | 1.0098 to 1.0161 | 1.0080 to 1.0163 | 1.0080 to 1.0174 | 1.0076 to 1.0188 <!-- results/validation/blocks_medians.csv: planned, ORIG DLG --> |
| ORIG DLG | spacing 0.01 | 293 | 1.0218 | 1.0193 to 1.0253 | 1.0184 to 1.0259 | 1.0182 to 1.0260 | 1.0174 to 1.0268 <!-- results/validation/blocks_medians.csv: spacing_0p01, ORIG DLG --> |
| DNR 24k POLYS | planned | 223 | 1.0100 | 1.0055 to 1.0128 | 1.0051 to 1.0128 | 1.0051 to 1.0130 | 1.0050 to 1.0142 <!-- results/validation/blocks_medians.csv: planned, DNR 24k POLYS --> |
| DNR 24k POLYS | spacing 0.01 | 223 | 1.0198 | 1.0157 to 1.0241 | 1.0157 to 1.0241 | 1.0160 to 1.0248 | 1.0160 to 1.0248 <!-- results/validation/blocks_medians.csv: spacing_0p01, DNR 24k POLYS --> |
| PWI | planned | 54 | 1.0444 | 1.0297 to 1.0603 | 1.0282 to 1.0679 | 1.0252 to 1.0645 | 1.0282 to 1.0679 <!-- results/validation/blocks_medians.csv: planned, PWI --> |
| PWI | spacing 0.01 | 54 | 1.0529 | 1.0391 to 1.0727 | 1.0390 to 1.0768 | 1.0334 to 1.0747 | 1.0391 to 1.0768 <!-- results/validation/blocks_medians.csv: spacing_0p01, PWI --> |
| other | planned | 1,110 | 1.0242 | 1.0221 to 1.0259 | 1.0217 to 1.0263 | 1.0211 to 1.0268 | 1.0209 to 1.0274 <!-- results/validation/blocks_medians.csv: planned, other --> |
| other | spacing 0.01 | 1,110 | 1.0337 | 1.0318 to 1.0355 | 1.0313 to 1.0361 | 1.0310 to 1.0369 | 1.0307 to 1.0374 <!-- results/validation/blocks_medians.csv: spacing_0p01, other --> |

### Digitizing density

**Table 20. Vertex spacing as digitized: per-lake median and 90th percentile, summarized by source group (median and interquartile range, m).** <!-- results/validation/vertices_by_group.csv: columns group, n, median_spacing_median, median_spacing_q25, median_spacing_q75, p90_spacing_median, p90_spacing_q25, p90_spacing_q75 -->

| group | lakes | median spacing | IQR | 90th percentile spacing | IQR |
|---|---|---|---|---|---|
| 2004 FSA | 1,543 | 13.2 | 10.0 to 16.7 | 26.2 | 21.0 to 33.5 <!-- results/validation/vertices_by_group.csv: 2004 FSA --> |
| ORIG DLG | 293 | 27.4 | 21.0 to 36.8 | 75.0 | 61.0 to 91.5 <!-- results/validation/vertices_by_group.csv: ORIG DLG --> |
| DNR 24k POLYS | 223 | 19.2 | 15.1 to 22.7 | 44.9 | 31.8 to 54.0 <!-- results/validation/vertices_by_group.csv: DNR 24k POLYS --> |
| PWI | 54 | 16.9 | 12.4 to 20.3 | 35.1 | 25.6 to 42.1 <!-- results/validation/vertices_by_group.csv: PWI --> |
| other | 1,110 | 14.2 | 11.4 to 18.5 | 33.0 | 25.5 to 43.7 <!-- results/validation/vertices_by_group.csv: other --> |
| all lakes | 3,274 | 14.6 | 11.0 to 19.4 | 30.9 | 23.3 to 44.8 <!-- results/validation/vertices_by_group.csv: all lakes --> |

A Kruskal–Wallis test of the per-lake median spacing across the five groups gives H = 642.56 and p = 9.49e-138, on 3,223 lakes <!-- results/validation/vertices_kruskal_wallis.csv: n_groups, H, p_value, n_lakes -->.

**Table 21. Spearman rho of per-lake median vertex spacing against the primary-window estimate.** <!-- results/validation/vertices_rho.csv: columns dims, group, n, rho, ci_low, ci_high -->

| group | lakes | rho, planned | 95% CI, planned | rho, spacing 0.01 | 95% CI, spacing 0.01 |
|---|---|---|---|---|---|
| all lakes | 3,274 | -0.5200 | -0.5463 to -0.4932 | -0.5137 | -0.5409 to -0.4871 <!-- results/validation/vertices_rho.csv: all lakes --> |
| 2004 FSA | 1,543 | -0.6018 | -0.6357 to -0.5669 | -0.5939 | -0.6286 to -0.5589 <!-- results/validation/vertices_rho.csv: 2004 FSA --> |
| ORIG DLG | 293 | -0.4350 | -0.5278 to -0.3343 | -0.4207 | -0.5109 to -0.3199 <!-- results/validation/vertices_rho.csv: ORIG DLG --> |
| DNR 24k POLYS | 223 | -0.3007 | -0.4141 to -0.1785 | -0.3054 | -0.4185 to -0.1837 <!-- results/validation/vertices_rho.csv: DNR 24k POLYS --> |
| PWI | 54 | -0.3337 | -0.5922 to -0.0362 | -0.3184 | -0.5765 to -0.0260 <!-- results/validation/vertices_rho.csv: PWI --> |
| other | 1,110 | -0.4118 | -0.4619 to -0.3625 | -0.4069 | -0.4567 to -0.3583 <!-- results/validation/vertices_rho.csv: other --> |

Rebuilding the rings with vertices every 25 m dropped 1,959 of 10,836 rings, from 350 lakes; every 50 m dropped 3,373, from 603 lakes <!-- results/validation/equalized_rings.csv: interval_m, n_rings, n_rings_dropped, n_lakes_with_dropped_rings -->. After rebuilding, 9 lakes (every 25 m) and 24 lakes (every 50 m) are not valid polygons <!-- results/validation/equalized_rings.csv: n_lakes_invalid_after_resampling -->; box counting uses only the boundary points, and they were kept.

**Table 22. Median primary-window dimension by source group, as digitized and with rings rebuilt at fixed vertex intervals, and the Kruskal–Wallis H.** <!-- results/validation/equalized_source_groups.csv: columns vertices, interval_m, densify_fraction, group, n, median_dim; results/validation/equalized_kruskal_wallis.csv: H -->

| group | lakes | planned spacing: as digitized | every 25 m | every 50 m | spacing 0.01: as digitized | every 25 m | every 50 m |
|---|---|---|---|---|---|---|---|
| 2004 FSA | 1,543 | 1.0289 | 1.0216 | 1.0159 | 1.0388 | 1.0320 | 1.0267 <!-- results/validation/equalized_source_groups.csv: 2004 FSA --> |
| ORIG DLG | 293 | 1.0122 | 1.0092 | 1.0068 | 1.0218 | 1.0196 | 1.0177 <!-- results/validation/equalized_source_groups.csv: ORIG DLG --> |
| DNR 24k POLYS | 223 | 1.0100 | 1.0053 | 1.0032 | 1.0198 | 1.0155 | 1.0143 <!-- results/validation/equalized_source_groups.csv: DNR 24k POLYS --> |
| PWI | 54 | 1.0444 | 1.0372 | 1.0279 | 1.0529 | 1.0479 | 1.0392 <!-- results/validation/equalized_source_groups.csv: PWI --> |
| other | 1,110 | 1.0242 | 1.0181 | 1.0127 | 1.0337 | 1.0286 | 1.0235 <!-- results/validation/equalized_source_groups.csv: other --> |
| Kruskal–Wallis H | 3,223 | 170.90 | 138.52 | 114.27 | 164.98 | 133.73 | 108.25 <!-- results/validation/equalized_kruskal_wallis.csv: H --> |

The columns for points at the planned spacing (0.1 of the smallest box) start from the planned estimates, and the spacing 0.01 columns from the spacing 0.01 estimates <!-- results/validation/equalized_parameters.csv: densify_fraction_1, densify_fraction_2 -->. The largest p-value of these six tests is 1.72e-22 <!-- results/validation/equalized_kruskal_wallis.csv: p_value -->.

## Figures

All four figures are drawn by src/paper_figures.py from the files named below. Numbers printed on a figure are read from those files. In Figures 1 to 3 a gray line marks dimension 1, the dimension of a smooth curve.

**Figure 1** (figures/fig1_dimension_vs_shoreline.png). Box-counting dimension in the primary window against shoreline length in kilometers, log scale, one point per primary lake. The printed rho and interval are from results/primary/rho_primary.csv. Data: results/primary/dims.csv.

**Figure 2** (figures/fig2_dimension_vs_area.png). Box-counting dimension in the primary window against area (DNR acres attribute), log scale, one point per primary lake. The printed rho and interval are from results/primary/rho_primary.csv. Data: results/primary/dims.csv.

**Figure 3** (figures/fig3_dimension_by_source.png). Median primary-window dimension per mapping source group (black bar; the value and the lake count are printed under each group), over every lake in the group (points, spread sideways at random with a fixed seed so they do not overlap). Lakes with no delineat_1 are not shown. Medians and counts: results/primary/source_groups.csv; lakes: results/primary/dims.csv; test: results/primary/kruskal_wallis.csv.

**Figure 4** (figures/fig4_map_dimension.png). Primary lakes, each drawn as one point inside its polygon, colored by primary-window dimension. Colors saturate below the 1st and above the 99th percentile of the dimension <!-- display choice: src/paper_figures.py, MAP_PERCENTILES -->, so a few extreme lakes do not compress the scale. Coordinates are EPSG:26915 in kilometers. Dimensions: results/primary/dims.csv; lake locations: data/processed/lakes_filtered.gpkg.
