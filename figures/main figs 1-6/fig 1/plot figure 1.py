# -*- coding: utf-8 -*-
"""Render Figure 1 for Blue_Transformation_1115 - 1300 edited.

Run with Python and numpy, pandas, matplotlib, scipy, pwlf, and openpyxl.
The Excel input and the generated PNG are both beside this script.
"""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd
import pwlf
from scipy import stats


BASE = Path(__file__).resolve().parent
INPUT = BASE / "infor to plot fig0.xlsx"
OUTPUT = BASE / "figure 1.png"
AQUATIC = "#30BDA6"
TERRESTRIAL = "#DBA34C"
WATER_TYPES = {
    "Freshwater Fish": "#DB4D4D",
    "Marine Fish": "#BDB730",
    "Other Seafoods": "#36B88F",
}
STATS = ["5%", "25%", "gmean", "75%", "95%"]


def positive_summary(frame):
    return frame.loc[(frame[STATS] > 0).all(axis=1)]


def style_frame(axis):
    axis.set_axisbelow(True)
    axis.tick_params(length=0, pad=4)
    for spine in axis.spines.values():
        spine.set_color("black")
        spine.set_linewidth(0.9)


def panel_title(figure, letter, label, x, y):
    figure.text(x, y, letter, fontsize=21, weight="bold", va="top")
    figure.text(x + 0.038, y, label, fontsize=21, va="top")


def plot_a(figure, data):
    top = figure.add_axes([0.070, 0.786, 0.414, 0.145])
    bottom = figure.add_axes([0.070, 0.632, 0.414, 0.148], sharex=top)
    data = positive_summary(data).copy()
    data["sample"] = data["sample"].replace("Other Seafood", "Other Seafoods")
    data["period"] = data["year"].map(lambda value: tuple(map(int, re.findall(r"\d{4}", str(value)))))
    periods = sorted(set(data["period"]))
    positions = {period: x for x, period in enumerate(periods)}

    for axis in (top, bottom):
        for (sample, color), offset in zip(WATER_TYPES.items(), (-0.25, 0, 0.25)):
            subset = data.loc[data["sample"] == sample]
            axis.bxp(
                [dict(zip(("whislo", "q1", "med", "q3", "whishi"), row))
                 for row in subset[STATS].itertuples(index=False, name=None)],
                positions=[positions[period] + offset for period in subset["period"]],
                widths=0.21, patch_artist=True, showfliers=False, manage_ticks=False,
                boxprops={"facecolor": to_rgba(color, 0.5), "edgecolor": "none"},
                medianprops={"color": color, "linewidth": 1.5},
                whiskerprops={"color": color, "linewidth": 0.9},
                capprops={"color": color, "linewidth": 0.9},
            )
        for x in np.arange(len(periods) - 1) + 0.5:
            axis.axvline(x, color="0.45", linestyle="--", linewidth=0.8, zorder=0)
        axis.yaxis.set_major_locator(MultipleLocator(20))
        axis.yaxis.set_minor_locator(MultipleLocator(10))
        axis.grid(axis="y", which="major", color="0.68", linestyle="--", linewidth=0.8)
        axis.grid(axis="y", which="minor", color="0.82", linestyle="--", linewidth=0.6)
        style_frame(axis)

    top.set(xlim=(-0.6, len(periods) - 0.4), ylim=(21, 170))
    bottom.set_ylim(-1, 22)
    bottom.set_xticks(range(len(periods)), ["-".join(map(str, p)) for p in periods],
                      rotation=45, ha="right")
    top.tick_params(axis="x", labelbottom=False)
    top.spines["bottom"].set_visible(False)
    bottom.spines["top"].set_visible(False)
    for axis, y in ((top, 0), (bottom, 1)):
        for x in (0, 1):
            axis.plot([x - 0.012, x + 0.012], [y - 0.016, y + 0.016],
                      transform=axis.transAxes, color="black", linewidth=1, clip_on=False)
    figure.text(0.026, 0.783, "concentration (ng/g ww)", va="center",
                ha="center", rotation=90, fontsize=15)

    handles = [
        Patch(facecolor=color, label=label)
        for label, color in zip(("Freshwater Fish", "Marine Fish", "Other Seafood"), WATER_TYPES.values())
    ]
    top.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.75, 0.99),
               frameon=False, fontsize=12.2, handlelength=1.3, borderpad=0.25, labelspacing=0.5)
    # Percentile key for the box, centre line, and whiskers.
    top.plot([0.795, 0.795], [0.22, 0.88], color="black", linewidth=0.75,
             transform=top.transAxes, clip_on=False)
    for y in (0.22, 0.88):
        top.plot([0.787, 0.803], [y, y], color="black", linewidth=0.75,
                 transform=top.transAxes, clip_on=False)
    top.add_patch(plt.Rectangle((0.783, 0.39), 0.024, 0.36,
                                transform=top.transAxes, color="0.75", zorder=3))
    top.plot([0.787, 0.803], [0.55, 0.55], transform=top.transAxes,
             color="black", linewidth=2, zorder=4)
    for y, label in [(0.88, "95%"), (0.72, "75%"), (0.55, "geomean"),
                     (0.39, "25%"), (0.22, "5%")]:
        top.text(0.825, y, label, transform=top.transAxes, va="center", fontsize=11.5)


def plot_b(figure, data):
    axis = figure.add_axes([0.551, 0.632, 0.414, 0.299])
    for sample, color in (("All Aquatics", AQUATIC), ("All Terrestrial", TERRESTRIAL)):
        series = positive_summary(data.loc[data["sample"] == sample]).sort_values("year")
        year = series["year"].to_numpy(float)
        geometric_mean = series["gmean"].to_numpy(float)
        axis.fill_between(year, series["25%"].to_numpy(float), series["75%"].to_numpy(float),
                          color=color, alpha=0.45, zorder=2)
        axis.scatter(year, geometric_mean, edgecolors="black", facecolors=color, s=42, zorder=5)
        if sample == "All Aquatics":
            model = pwlf.PiecewiseLinFit(year, np.log(geometric_mean), seed=0)
            model.fit(3, tol=0.0001)
            fitted_year = np.linspace(year.min(), year.max(), 250)
            axis.plot(fitted_year, np.exp(model.predict(fitted_year)), color="darkgreen",
                      linewidth=1.8, zorder=6)
    axis.set(xlim=(1999.5, 2023.5), ylim=(-0.5, 15),
             xlabel="Year", ylabel="concentration (ng/g ww)")
    axis.set_xticks(range(2000, 2021, 5))
    axis.set_yticks(range(0, 15, 2))
    axis.grid(color="0.81", linewidth=0.8)
    style_frame(axis)
    handles = [
        (
            Patch(facecolor=to_rgba(color, 0.45), edgecolor=to_rgba(color, 0.7)),
            Line2D([], [], marker="o", markeredgecolor="black", markerfacecolor=color,
                   markersize=7.5, linestyle="none"),
        )
        for color in (AQUATIC, TERRESTRIAL)
    ]
    handles.extend([
        Line2D([], [], marker="o", markeredgecolor="black", markerfacecolor="0.6",
               markersize=7.5, linestyle="none"),
        Patch(facecolor="0.8", edgecolor="0.62"),
        Line2D([], [], color="darkgreen", linewidth=1.8),
    ])
    axis.legend(handles, ["aquatic", "terrestrial", "geometric mean", "25%-75%", "piecewise fit"],
                handler_map={tuple: HandlerTuple(ndivide=1)}, loc="upper right",
                frameon=False, fontsize=13.5, handleheight=1.1, borderaxespad=0.35, labelspacing=0.28)


def plot_c(figure, exposure, aquatic):
    axis = figure.add_axes([0.062, 0.058, 0.567, 0.449])
    data = exposure[["year", "ave"]].merge(aquatic[["year", "ave"]], on="year",
                                            suffixes=("_total", "_aquatic")).sort_values("year")
    years = data["year"].to_numpy(int)
    total = data["ave_total"].to_numpy(float)
    water = data["ave_aquatic"].to_numpy(float)
    land = np.maximum(total - water, 0)
    for amount, base, color, label in (
        (water, 0, AQUATIC, "Aquatic EDI"),
        (land, water, TERRESTRIAL, "Terrestrial EDI"),
    ):
        axis.bar(years, amount, bottom=base, width=0.72, facecolor=to_rgba(color, 0.5),
                 edgecolor=color, linewidth=1.5, label=label, zorder=3)
    for year, water_value, land_value, total_value in zip(years, water, land, total):
        aquatic_pct = 100 * np.round(water_value, 2) / np.round(total_value, 2)
        terrestrial_pct = 100 * np.round(land_value, 2) / np.round(total_value, 2)
        axis.text(year, water_value / 2, f"{aquatic_pct:.1f}%", ha="center",
                  va="center", fontsize=10, rotation=45)
        axis.annotate(f"{terrestrial_pct:.1f}%", (year, total_value),
                      xytext=(0, 2), textcoords="offset points",
                      ha="center", va="bottom", rotation=45, fontsize=8.7)
    axis.set(xlim=(years.min() - 0.7, years.max() + 0.7),
             ylim=(0, total.max() * 1.15), ylabel="EDI (ng/kg bw/day)")
    axis.yaxis.set_label_coords(-0.053, 0.5)
    axis.set_xticks(years, years, rotation=45)
    axis.grid(linestyle="--", alpha=0.35)
    axis.legend(frameon=False, loc="upper right", fontsize=11)
    style_frame(axis)


def plot_d(figure, exposure, serum):
    axis = figure.add_axes([0.692, 0.058, 0.270, 0.449])
    periods = serum.iloc[::2].reset_index(drop=True)
    edi = pd.DataFrame([
        exposure.loc[exposure["year"].isin((year, year + 1)), ["gmean", "25%", "75%"]].mean()
        for year in periods["year"]
    ])
    x = edi["gmean"].to_numpy(float)
    y = periods["gmean"].to_numpy(float)
    xerr = np.vstack([x - edi["25%"], edi["75%"] - x])
    yerr = np.vstack([y - periods["25%"], periods["75%"] - y])
    axis.errorbar(x, y, xerr=xerr, yerr=yerr, fmt="o", markersize=6,
                  color="black", ecolor="0.55", elinewidth=0.8,
                  capsize=2, alpha=0.9, zorder=4)

    fit = stats.linregress(x, y)
    fit_x = np.sort(x)
    fit_y = fit.intercept + fit.slope * fit_x
    dof = len(x) - 2
    residual_sd = np.sqrt(np.sum((y - (fit.intercept + fit.slope * x)) ** 2) / dof)
    mean_fit_se = residual_sd * np.sqrt(1 / len(x) + (fit_x - x.mean()) ** 2 / np.sum((x - x.mean()) ** 2))
    interval = stats.t.ppf(0.975, dof) * mean_fit_se
    band = axis.fill_between(fit_x, fit_y - interval, fit_y + interval, color="red", alpha=0.14,
                             label="95% CI of fit", zorder=1)
    line, = axis.plot(fit_x, fit_y, color="red", linestyle="--", linewidth=1.2,
                      label="linear fit", zorder=2)

    offsets = [(6, 10), (6, 8), (-5, 6), (-39, 5), (7, 7), (7, 3), (-24, -14)]
    for year, x_value, y_value, offset in zip(periods["year"].astype(int), x, y, offsets):
        axis.annotate(f"({year}-{(year + 1) % 100:02d})", (x_value, y_value),
                      xytext=offset, textcoords="offset points", fontsize=10.8,
                      ha="right" if year == 2007 else "left", zorder=5)
    axis.text(0.965, 0.978, f"$r$={fit.rvalue:.3f}\n$p$={fit.pvalue:.3f}",
              transform=axis.transAxes, ha="right", va="top", fontsize=12)
    mean_marker = Line2D([], [], color="black", marker="o", linestyle="none", markersize=6)
    # Use the vertical error-bar artist as the key for either axis's IQR.
    iqr = axis.errorbar([], [], yerr=[], fmt="none", ecolor="0.55", capsize=3)
    axis.legend([iqr, line, band, mean_marker],
                ["25%-75% range", "linear fit", "95% CI of fit", "geometric mean"],
                loc="lower right", frameon=False, handlelength=1.45, fontsize=11.5)
    axis.set(xlim=(2.8, 28), ylim=(5.3, 41.8), xlabel="EDI (ng/kg bw/day)",
             ylabel="serum concentration (ng/ml)")
    axis.set_xticks(range(5, 26, 5))
    axis.set_yticks(range(10, 41, 5))
    axis.grid(linestyle="--", alpha=0.45)
    style_frame(axis)


def main():
    sheets = pd.read_excel(
        INPUT, sheet_name=["period conc", "conc", "expo", "aquatic expo", "serum"], engine="openpyxl"
    )
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "font.size": 10,
        "axes.labelsize": 15,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "grid.color": "0.81",
    })
    figure = plt.figure(figsize=(12.94, 9.24), facecolor="white")
    plot_a(figure, sheets["period conc"])
    plot_b(figure, sheets["conc"])
    plot_c(figure, sheets["expo"], sheets["aquatic expo"])
    plot_d(figure, sheets["expo"], sheets["serum"])
    panel_title(figure, "a", "concentration in aquatic food", 0.023, 0.973)
    panel_title(figure, "b", "temporal trend of PFAS in food", 0.512, 0.973)
    panel_title(figure, "c", "exposure source composition", 0.023, 0.555)
    panel_title(figure, "d", "EDI vs serum concentration", 0.651, 0.555)
    figure.savefig(OUTPUT, dpi=300, facecolor="white")
    plt.close(figure)


if __name__ == "__main__":
    main()
