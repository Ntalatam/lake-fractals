# results/validation: post-hoc, not pre-registered

Post-review validation, added after the planned results. Nothing here changes the planned analysis or any file in results/primary/ or results/exploratory/; those are only read.

| file | written by | contents |
|---|---|---|
| benchmarks.csv | src/validation.py | circle, Koch snowflake (6 and 7 iterations, bumps outward) and Sierpinski triangle in the 20–100, 10–100 and 20–200 m windows, at the planned point spacing: is_valid, known dimension, estimate, bias, lowest and highest per-offset slope, r2 |
| calibration.csv | src/validation.py | one row per shape, window and point spacing: generalized Koch snowflakes of known dimension near 1, ellipses sized like the lakes (dimension 1, random rotations and shifts) and the benchmark circle, at point spacings of 0.1 (planned), 0.03 and 0.01 of the smallest box |
| calibration_summary.csv | src/validation.py | calibration.csv per shape, size, window and point spacing: mean estimate, bias (mean minus known dimension), sd, count and share below 1, lowest and highest estimate |
| below_one.csv | src/validation.py | estimates below 1 in results/primary/dims.csv, per window: count, share, percent, lowest |
| spacing_0p01/ | src/validation_spacing.py | the primary analysis rerun on the same lakes with boundary points at most 0.01 of the smallest box apart (planned: 0.1). Files with a planned counterpart keep its name and columns; below_one.csv counts estimates below 1; comparison_*.csv put each planned result beside the rerun's |

Settings for these runs are in the scripts, each with the reason it was chosen. Two were not set by the author: the ellipse rotations are uniform on [0, 180°) and the shifts uniform on [0, 200 m) in x and y (src/validation.py). The box-counting grid is placed relative to the lower-left corner of the boundary points, so a shift leaves the box counts unchanged up to floating-point rounding.

The spacing rerun used 4 worker processes and the author's stop rule for that run: stop only if the whole run passes 3 hours. The planned 60 s per-lake limit was not applied (spacing_0p01/parameters.csv).
