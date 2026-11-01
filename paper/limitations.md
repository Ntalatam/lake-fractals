# Limitations

<!--
Draft for the author. Each number is followed by an HTML comment naming its
source, as in methods.md and results.md. Numbers not written by a script to
results/ say "not in results/" and name where they come from.
-->

## 1. Shoreline length partly encodes complexity

For lakes of the same area, a longer shoreline is a more convoluted one, and box counts between 20 and 100 m <!-- results/primary/rho_primary.csv: window 20_100, window_min_m and window_max_m --> respond to the same convolution. Shoreline length and dimension are therefore not independent measures, and part of the supported positive relationship (rho 0.4099 in the primary window) <!-- results/primary/rho_primary.csv: 20_100, shoreline --> is built into the two measures. Islands add to both: shoreline_m and the box count include every island ring, and 1,135 primary lakes have at least one <!-- results/exploratory/outer_shore/post-hoc_outer_shore_counts.csv: n_with_interior_rings -->. In the post-hoc check with island rings removed, rho is 0.3646 <!-- results/exploratory/outer_shore/post-hoc_outer_shore_rho.csv: exterior_length -->, so removing islands lowers the correlation but does not remove it. No analysis holds area fixed when relating dimension to shoreline length (for example a partial correlation, or a shoreline development index), and none was pre-registered.

## 2. Finite-size effects in the 20–200 m window <!-- results/primary/rho_primary.csv: window 20_200 -->

The smallest primary lake has an equivalent diameter of 717.8 m <!-- results/feasibility/feasibility_summary.txt: min (not a csv) -->, and the largest box in the 20–200 m window is 200 m <!-- results/primary/rho_primary.csv: window 20_200, window_max_m -->. The finite-size argument for the 100-acre cutoff (Methods) was made for the 100 m box of the primary window, and the feasibility check compared lake size only with the 100 m box <!-- results/feasibility/feasibility_summary.txt (not a csv) -->, so neither shows that the 20–200 m window <!-- results/primary/rho_primary.csv: window 20_200 --> is free of finite-size bias. The only area correlation in the primary sample whose interval excludes zero is in this window: rho -0.0590 (95% CI -0.0942 to -0.0247) <!-- results/primary/rho_primary.csv: 20_200, area -->. It may reflect finite-size bias rather than shoreline geometry.

The estimates also carry bias of their own. Every window has some lakes with an estimated dimension below 1 (results/primary/dims.csv; Figures 1 and 2). The box-counting dimension of a curve cannot be below 1, so these values are estimation error; how large that error is, and whether it depends on lake size, was not measured. The Koch and Sierpinski checks covered only box sizes from 10 to 100 m <!-- src/boxcount.py:16 (DEFAULT_BOX_SIZES), not in results/ -->, and the larger windows were checked only on a circle.

## 3. Source differences are smaller than the test tolerance

The median dimensions of the source groups run from 1.0100 (DNR 24k POLYS) to 1.0444 (PWI) <!-- results/primary/source_groups.csv: median_dim -->. The estimator was validated only to within 0.05 of known dimensions <!-- tests/test_boxcount.py:16 (TOLERANCE), not in results/ -->, a margin wider than the whole spread of group medians. The Kruskal–Wallis test (H = 170.90) <!-- results/primary/kruskal_wallis.csv: H --> shows that dimension differs between the groups. The validation cannot show that the estimator is accurate at the scale of these differences, so it cannot separate a mapping effect from estimator bias that differs between groups. Mapping source was also not assigned at random: the groups may differ in lake size, region and digitizing detail, and the comparison controls for none of these.

## 4. The 1,000 m shoreline filter selects on shape <!-- results/filter_log.csv: step 4, description -->

At 10 acres, a circular lake has a shoreline shorter than 1,000 m <!-- 10: results/filter_log.csv, step 2 description; 1,000 m: step 4 description; that the circle's shoreline is shorter is a geometric fact, not in results/ -->. Step 4 therefore removes small lakes with compact shorelines and keeps a small lake only if its shoreline is long for its area. It removed 1,258 lakes <!-- results/filter_log.csv: step 4, dropped -->. Among the smallest lakes in the exploratory sample, this favors convoluted shorelines, which may raise their dimensions and push the exploratory area correlation (rho -0.2831) <!-- results/primary/exploratory_10acre_rho.csv: area --> toward negative values. The size of this effect was not measured. The filter removes no lake from the primary sample <!-- CLAUDE.md:17, not in results/ -->.

## 5. Lakes are not independent

Lakes cluster in space (Figure 4), share regional geology, and were mapped in regional projects, so neighboring lakes are likely to have similar shorelines and the same mapping source. The p-values and the bootstrap intervals treat lakes as independent (the bootstrap resamples single lakes), so both are likely too narrow. No spatial structure was modeled.

## 6. No multiple-comparison correction

The primary sample alone gives six correlations, two measures in three windows <!-- results/primary/rho_primary.csv: one row per measure and window -->. The within-source, pilot-excluded, exploratory and post-hoc checks and the Kruskal–Wallis test add more. Every p-value is unadjusted. The decision rule uses only the sign of rho, so it is unaffected, but any statement of significance should allow for the number of tests.

## 7. The 20 m lower bound assumes map-based digitizing <!-- results/primary/rho_primary.csv: window 20_100, window_min_m -->

Of the 3,274 primary lakes <!-- results/primary/sample_log.csv: primary -->, 1,543 (the 2004 FSA group) <!-- results/primary/source_groups.csv: 2004 FSA, n --> were digitized from 2004 aerial imagery, not 1:24,000 maps <!-- the year is in the delineat_1 value "2004 FSA"; that these shorelines were digitized from aerial imagery is the author's statement, best cited to the DNR layer metadata; 1:24,000 is the map scale in Methods (US National Map Accuracy Standards); not in results/ -->. The rationale for the primary window's 20 m lower bound <!-- results/primary/rho_primary.csv: window 20_100, window_min_m --> rests on the accuracy of digitizing from those maps (Methods), so it fits these lakes less exactly.
