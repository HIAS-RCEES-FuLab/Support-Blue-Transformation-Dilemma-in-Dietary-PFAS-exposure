"""Render the two-panel Figure 2 in the edited November 15 manuscript.

Requires Python, matplotlib, numpy, pandas, and scipy. Run this script from
any directory. It reads the two CSVs beside it and writes figure 2.png there.

Panel a uses the archived 0105 aquatic and terrestrial concentration pools.
Each CSV value is the sum of available target PFAS arithmetic pool means for
one country and food group, in ng/g wet weight. The violins show these country
values on the log scale. Panel b uses the baseline FAOSTAT aquatic diet and
the archived 0105 2020 Trade individual exposure draws. The seven target PFAS
were summed within each draw and divided by 65 kg before calculating the
geometric mean and percentiles. Country regions come from reference_geography.
The world EDI reference line uses the manuscript's displayed value, 4.51.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import NullLocator
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "figure 2.png"
FOOD_COLORS = {"Aquatic food": "#eb7777", "Terrestrial food": "#b2c487"}
REGIONS = {
    "Southern and South Eastern Asia": ("South and Southeast Asia", "#b8cc78"),
    "Eastern Asia": ("East Asia", "#bd0000"),
    "Latin America": ("Latin America", "#5cdca0"),
    "Africa": ("Africa", "#98ec8b"),
    "North America": ("North America", "#ef9b29"),
    "Southern Europe": ("Southern Europe", "#fc4f12"),
    "Northern Europe": ("Northern Europe", "#fa0050"),
    "Oceania": ("Oceania", "#7bdcc7"),
    "Western Europe": ("Western Europe", "#ff1010"),
    "Eastern Europe+": ("Eastern Europe and West Asia", "#c9eb65"),
}
COUNTRY_LABELS = {"Korea": "South Korea", "Turkiye": "Turkey", "Türkiye": "Turkey"}
WORLD_EDI = 4.51
PERCENTILE_BANDS = [
    ("edi_p05", "edi_p95", 0.32),
    ("edi_p25", "edi_p75", 0.43),
    ("edi_p33", "edi_p66", 0.65),
]


def title(figure, x, y, letter, text, text_offset=0.042):
    figure.text(x, y, letter, weight="bold", fontsize=15, va="top")
    figure.text(x + text_offset, y, text, fontsize=15, va="top")


def plot_concentrations(figure, data):
    axis = figure.add_axes([0.193, 0.565, 0.207, 0.377])
    profiles = []
    for (food, source), rows in data.groupby(["food", "source"], sort=False):
        values = rows["sum7_ng_g_ww"].to_numpy(dtype=float)
        log_values = np.log10(values)
        x = np.linspace(log_values.min(), log_values.max(), 150)
        density = gaussian_kde(log_values)(x)
        profiles.append((food, source, values, x, density))
    density_max = max(density.max() for _, _, _, _, density in profiles)
    for index, (_, source, values, x, density) in enumerate(profiles):
        half_height = 0.38 * density / density_max
        axis.fill_between(
            10**x, index - half_height, index + half_height,
            facecolor=FOOD_COLORS[source], edgecolor="0.52", linewidth=0.95,
        )
        axis.plot(values.mean(), index, "D", color="black", markersize=3.3)
        axis.plot(np.exp(np.log(values).mean()), index, "x", color="black", markersize=3.3)
    axis.axvline(2, color="0.55", linewidth=1.1, linestyle="--")
    axis.set(xscale="log", xlim=(0.001, 100), ylim=(len(profiles) - 0.5, -0.5),
             xlabel=r"$\Sigma_7$PFAS concentration (ng/g ww)")
    axis.set_xticks([0.001, 0.01, 0.1, 1, 10, 100],
                    [r"$10^{-3}$", "0.01", "0.1", "1", "10", "100"])
    axis.xaxis.set_minor_locator(NullLocator())
    axis.set_yticks(np.arange(len(profiles)), [food for food, *_ in profiles],
                    rotation=45, rotation_mode="anchor", va="center", ha="right", fontsize=11.5)
    axis.xaxis.labelpad = 0
    axis.tick_params(axis="both", length=2.5, pad=1.5)
    for spine in axis.spines.values():
        spine.set_color("0.55")
        spine.set_linewidth(1.0)
    title(figure, 0.060, 0.985, "a", "PFAS concentration in Food")

    handles = [Patch(facecolor=color, edgecolor="0.52", label=label)
               for label, color in FOOD_COLORS.items()]
    handles.extend([
        Line2D([], [], marker="D", color="black", linestyle="none", markersize=5, label="mean"),
        Line2D([], [], marker="x", color="black", linestyle="none", markersize=5, label="geometric mean"),
        Line2D([], [], color="0.55", linestyle="--", label="2 ng/g ww"),
    ])
    figure.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.159, 0.514),
                  frameon=False, handlelength=1.65, borderaxespad=0, labelspacing=0.41)


def axis_baseline(axis, start, end, y):
    axis.plot([start, end], [y, y], color="0.18", linewidth=0.85, clip_on=False)


def plot_country_exposure(figure, data):
    left = figure.add_axes([0.549, 0.108, 0.218, 0.841])
    right = figure.add_axes([0.767, 0.108, 0.218, 0.841], sharey=left)
    row = np.arange(len(data))
    countries = data["country"].replace(COUNTRY_LABELS).to_list()
    y_baseline = len(data) - 0.3
    panels = [(left, 2.77, 134, [5, 16, 50]), (right, 0.158, 390, [0.3, 3, 30])]
    for axis, x_min, x_max, ticks in panels:
        axis.set(xscale="log", xlim=(x_min, x_max), ylim=(len(data) + 1.0, -1.0))
        axis.set_yticks(row)
        axis.set_xticks([])
        axis.xaxis.set_minor_locator(NullLocator())
        axis.grid(axis="y", color="0.76", linestyle=":", linewidth=0.95, zorder=0)
        axis.set_axisbelow(True)
        axis.tick_params(axis="y", length=2.4, pad=3)
        for spine in axis.spines.values():
            spine.set_visible(False)
        axis.spines["left"].set_visible(True)
        axis.spines["left"].set_linewidth(0.85 if axis is left else 0.55)
        axis_baseline(axis, ticks[0], ticks[-1] * (2.0 if axis is left else 4.0), y_baseline)
        for tick in ticks:
            axis.plot([tick, tick], [y_baseline, y_baseline + 0.15], color="0.18", linewidth=0.75)
            axis.text(tick, y_baseline + 0.18, f"{tick:g}", ha="center", va="top", fontsize=8.5)
    right.spines["right"].set_visible(True)
    right.spines["right"].set_linewidth(0.85)
    left.set_yticklabels(countries)
    right.tick_params(axis="y", left=False, labelleft=False)

    left.scatter(data["aquatic_kg_person_year"], row, marker="x", color="black",
                 linewidths=1.45, s=19, zorder=3)
    for index, record in enumerate(data.itertuples(index=False)):
        _, color = REGIONS[record.region]
        for lower, upper, opacity in PERCENTILE_BANDS:
            start = getattr(record, lower)
            width = getattr(record, upper) - start
            right.add_patch(Rectangle((start, index - 0.39), width, 0.78,
                                      facecolor=color, edgecolor="none", alpha=opacity, zorder=1))
    right.plot([WORLD_EDI, WORLD_EDI], [-0.55, y_baseline], color="0.48", linewidth=1.2, zorder=2)
    right.scatter(data["edi_geomean"], row, marker="x", color="black",
                  linewidths=1.45, s=19, zorder=3)

    title(figure, 0.488, 0.985, "b", "aquatic consumptions", text_offset=0.061)
    figure.text(0.880, 0.985, "EDI", fontsize=15, va="top")
    figure.text(0.654, 0.107, "kg/year", va="top", ha="center")
    figure.text(0.858, 0.107, "ng/kg bw/day", va="top", ha="center")

    intervals = [
        Line2D([], [], marker="x", color="black", linestyle="none", markersize=6, label="geometric mean"),
        Patch(facecolor="0.34", label="33%-66%"),
        Patch(facecolor="0.65", label="25%-75%"),
        Patch(facecolor="0.80", label="5%-95%"),
        Line2D([], [], color="0.48", label=f"{WORLD_EDI:.2f} ng/kg, global mean EDI"),
    ]
    figure.legend(handles=intervals, loc="upper left", bbox_to_anchor=(0.159, 0.229),
                  frameon=False, handlelength=1.55, borderaxespad=0, labelspacing=0.42)

    positions = [(0.167, 0.075), (0.167, 0.050), (0.167, 0.025),
                 (0.390, 0.075), (0.390, 0.050), (0.390, 0.025),
                 (0.590, 0.075), (0.590, 0.050), (0.590, 0.025), (0.755, 0.021)]
    for (label, color), (x, y) in zip(REGIONS.values(), positions):
        figure.add_artist(Rectangle((x, y - 0.005), 0.015, 0.018,
                                    transform=figure.transFigure, color=color, linewidth=0))
        figure.text(x + 0.033, y + 0.003, label, va="center", fontsize=9)


def main():
    concentrations = pd.read_csv(BASE / "food_concentrations_2020.csv")
    country_exposure = pd.read_csv(BASE / "country_exposure_2020_trade.csv")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "font.size": 10,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 10,
    })
    figure = plt.figure(figsize=(9.72, 7.79), facecolor="white")
    plot_concentrations(figure, concentrations)
    plot_country_exposure(figure, country_exposure)
    figure.savefig(OUTPUT, dpi=300, facecolor="white")
    plt.close(figure)


if __name__ == "__main__":
    main()
