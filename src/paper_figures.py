"""Figures for the paper draft, drawn from the existing primary results.

Reads results/primary/ (dims.csv, rho_primary.csv, source_groups.csv,
kruskal_wallis.csv, parameters.csv) and, for the map only, the lake polygons
in data/processed/lakes_filtered.gpkg. Writes to paper/figures/:
- fig1_dimension_vs_shoreline.png: dimension vs shoreline length
- fig2_dimension_vs_area.png: dimension vs area (DNR acres)
- fig3_dimension_by_source.png: median dimension by mapping source group
- fig4_map_dimension.png: map of the primary lakes colored by dimension

Every figure uses the primary window. Nothing is recomputed: each number
printed on a figure is read from a csv in results/primary/, and results/ is
only read.

Run from the project root: .venv/bin/python src/paper_figures.py
"""

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")  # write files only, no window

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

from primary_analysis import LAKES, OUT_DIR, PRIMARY_WINDOW, ROOT

FIGURES = ROOT / "paper" / "figures"
DIM = f"dim_{PRIMARY_WINDOW}"

# colors from the reference palette of the dataviz guidance. each figure shows
# one series, so its marks take categorical slot 1 and need no legend; text
# and chrome use the ink and hairline tokens, never the series color.
SERIES = "#2a78d6"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#ffffff"  # print figures sit on white

# map color scale: the one-hue blue ramp at steps 250, 400, 550 and 700. the
# lighter steps are left out so low-dimension lakes stay visible as points on
# white (step 250 is 2.1:1 against white). these four pass the palette
# validator as a monotone one-hue ramp.
SEQUENTIAL = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

# display choices, not analysis choices:
# points are partly transparent so dense clusters of lakes show as darker
# areas instead of a solid block
POINT_ALPHA = 0.35
# the map's colors saturate at these percentiles of the primary-window
# dimension, so a few extreme lakes do not squeeze the scale for the rest; the
# color bar's arrows mark the saturated ends
MAP_PERCENTILES = (1, 99)
# fixed seed for the sideways spread of points in figure 3, so the figure is
# the same on every run
JITTER_SEED = 0
JITTER_HALF_WIDTH = 0.3

DPI = 300


def rho_row(rho, measure, window=PRIMARY_WINDOW):
    """The one row of a rho table for this measure and window."""
    rows = rho[(rho["window"] == window) & (rho["measure"] == measure)]
    if len(rows) != 1:
        raise ValueError(f"expected one {measure} row for window {window}, found {len(rows)}")
    return rows.iloc[0]


def rho_label(row, ci_level_percent):
    """rho, its interval and n, rounded as in results/primary/summary.md."""
    return (
        f"Spearman ρ = {row['rho']:.4f} ({ci_level_percent:g}% CI {row['ci_low']:.4f} to "
        f"{row['ci_high']:.4f}), n = {int(row['n']):,}"
    )


def window_label(row):
    return f"{row['window_min_m']:g}–{row['window_max_m']:g} m"


def lake_points(lakes, dims):
    """One point inside each lake in dims, joined to that lake's row of dims.

    representative_point always falls inside the polygon, unlike the centroid
    of a curved or ring-shaped lake. Stops if a lake in dims has no polygon.
    """
    points = gpd.GeoDataFrame(
        {"objectid": lakes["objectid"].to_numpy()},
        geometry=lakes.geometry.representative_point().to_numpy(),
        crs=lakes.crs,
    )
    joined = points.merge(dims, on="objectid", validate="one_to_one")
    if len(joined) != len(dims):
        missing = sorted(set(dims["objectid"]) - set(joined["objectid"]))
        raise ValueError(f"{len(missing)} lakes in dims have no polygon, e.g. objectid {missing[:5]}")
    return joined


def style():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 9,
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": AXIS,
            "axes.linewidth": 0.8,
            "axes.labelcolor": INK_SECONDARY,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "grid.linestyle": "-",
            "xtick.color": AXIS,
            "ytick.color": AXIS,
            "xtick.labelcolor": INK_SECONDARY,
            "ytick.labelcolor": INK_SECONDARY,
        }
    )


def heading(ax, title, subtitle):
    """Title and subtitle above the plot, left-aligned with the axes."""
    common = {"xy": (0, 1), "xycoords": "axes fraction", "textcoords": "offset points", "ha": "left", "va": "bottom"}
    ax.annotate(title, xytext=(0, 22), fontsize=11, color=INK, weight="bold", **common)
    ax.annotate(subtitle, xytext=(0, 8), fontsize=9, color=INK_SECONDARY, **common)


def reference_line(ax):
    """Hairline at dimension 1, the dimension of any smooth curve.

    The label sits in the right margin, beside the line's end, so it never
    covers a lake.
    """
    ax.axhline(1.0, color=INK_MUTED, linewidth=0.8, zorder=1)
    ax.annotate(
        "1: smooth\ncurve",
        xy=(1, 1.0),
        xycoords=("axes fraction", "data"),
        xytext=(4, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=8,
        color=INK_SECONDARY,
        annotation_clip=False,
    )


def log_axis(ax, formatter):
    # sizes span several orders of magnitude and spearman rho uses ranks only,
    # so a log axis spreads the lakes the way the correlation sees them
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 3.0)))
    ax.xaxis.set_major_formatter(FuncFormatter(formatter))
    ax.xaxis.set_minor_formatter(NullFormatter())


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def scatter_figure(x, dims, row, xlabel, title, ci_level_percent, formatter, path):
    """Primary-window dimension against one size measure, one point per lake."""
    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    ax.scatter(x, dims[DIM], s=7, color=SERIES, alpha=POINT_ALPHA, linewidths=0, zorder=2)
    log_axis(ax, formatter)
    reference_line(ax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(f"box-counting dimension, {window_label(row)} window")
    heading(ax, title, rho_label(row, ci_level_percent))
    save(fig, path)


def source_figure(dims, groups, kw, window, path):
    """Median dimension per source group, over every lake in the group."""
    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    rng = np.random.default_rng(JITTER_SEED)
    labels = []
    for i, group in enumerate(groups.itertuples()):
        values = dims.loc[dims["source_group"] == group.group, DIM]
        if len(values) != group.n:
            raise ValueError(f"{group.group}: {len(values)} lakes in dims.csv, {group.n} in source_groups.csv")
        spread = i + rng.uniform(-JITTER_HALF_WIDTH, JITTER_HALF_WIDTH, len(values))
        ax.scatter(spread, values, s=6, color=SERIES, alpha=POINT_ALPHA, linewidths=0, zorder=2)
        # the median bar sits on a surface-colored ring so it stays readable
        # over the points
        ax.hlines(group.median_dim, i - 0.38, i + 0.38, color=SURFACE, linewidth=4.5, zorder=3)
        ax.hlines(group.median_dim, i - 0.38, i + 0.38, color=INK, linewidth=2, zorder=4)
        labels.append(f"{group.group}\n{group.n:,} lakes\nmedian {group.median_dim:.4f}")
    ax.set_xticks(range(len(labels)), labels)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="x", visible=False)
    reference_line(ax)
    ax.set_ylabel(f"box-counting dimension, {window} window")
    heading(
        ax,
        f"Dimension by mapping source group, {window} window",
        f"Kruskal–Wallis H = {kw['H']:.2f}, p = {kw['p_value']:.3g}; {int(kw['n_lakes']):,} lakes; "
        f"{int(kw['n_excluded_missing']):,} with no source not shown",
    )
    save(fig, path)


def map_figure(points, window, path):
    """Primary lakes as points, colored by primary-window dimension."""
    fig, ax = plt.subplots(figsize=(6.5, 7.2))
    low, high = np.percentile(points[DIM], MAP_PERCENTILES)
    scale = LinearSegmentedColormap.from_list("blue_250_700", SEQUENTIAL)
    dots = ax.scatter(
        points.geometry.x / 1000, points.geometry.y / 1000, c=points[DIM], cmap=scale, vmin=low, vmax=high,
        s=5, linewidths=0,
    )
    ax.set_aspect("equal")
    ax.set_xlabel("easting (km), EPSG:26915")
    ax.set_ylabel("northing (km), EPSG:26915")
    bar = fig.colorbar(dots, ax=ax, extend="both", shrink=0.55, pad=0.03)
    bar.set_label(f"box-counting dimension, {window} window", color=INK_SECONDARY)
    bar.outline.set_edgecolor(AXIS)
    bar.ax.tick_params(color=AXIS, labelcolor=INK_SECONDARY)
    heading(
        ax,
        f"Primary lakes by dimension, {window} window",
        f"{len(points):,} lakes, one point each; colors saturate at the "
        f"{MAP_PERCENTILES[0]}st and {MAP_PERCENTILES[1]}th percentiles",
    )
    save(fig, path)


def main():
    style()
    dims = pd.read_csv(OUT_DIR / "dims.csv")
    rho = pd.read_csv(OUT_DIR / "rho_primary.csv")
    groups = pd.read_csv(OUT_DIR / "source_groups.csv")
    kw = pd.read_csv(OUT_DIR / "kruskal_wallis.csv").iloc[0]
    ci_level_percent = pd.read_csv(OUT_DIR / "parameters.csv").set_index("parameter")["value"]["ci_level_percent"]
    if set(groups["window"]) != {PRIMARY_WINDOW} or kw["window"] != PRIMARY_WINDOW:
        raise ValueError("source_groups.csv and kruskal_wallis.csv must be for the primary window")

    shoreline = rho_row(rho, "shoreline")
    area = rho_row(rho, "area")
    window = window_label(shoreline)

    scatter_figure(
        dims["shoreline_m"] / 1000, dims, shoreline, "shoreline length (km), log scale",
        f"Dimension vs shoreline length, {window} window", ci_level_percent,
        lambda value, _: f"{value:g}", FIGURES / "fig1_dimension_vs_shoreline.png",
    )
    scatter_figure(
        dims["acres"], dims, area, "area (acres, DNR attribute), log scale",
        f"Dimension vs area, {window} window", ci_level_percent,
        lambda value, _: f"{value:,.0f}", FIGURES / "fig2_dimension_vs_area.png",
    )
    source_figure(dims, groups, kw, window, FIGURES / "fig3_dimension_by_source.png")
    lakes = gpd.read_file(LAKES, columns=["objectid"])
    map_figure(lake_points(lakes, dims), window, FIGURES / "fig4_map_dimension.png")


if __name__ == "__main__":
    main()
