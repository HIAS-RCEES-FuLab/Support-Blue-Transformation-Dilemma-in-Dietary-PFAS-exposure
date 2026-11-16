"""Reproduce SI Text 2.3 Fig. 6 from the plot data beside this script.

The local inputs contain the 2026-11-12 Monte Carlo draws and their annual
geometric means, derived from the regional pelagic PFOA source files.
Requires NumPy and Matplotlib.
"""

import csv
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


STEM = "SI_Text_2_3_Fig6_regional_pelagic_PFOA"

ROOT = Path(__file__).resolve().parent

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.labelsize": 9,
    "axes.titlesize": 10, "axes.linewidth": 0.8, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "pdf.fonttype": 42,
})


def read_rows(filename):
    with (ROOT / filename).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def mark_panel(ax, letter, title):
    ax.set_title(title, pad=8)
    ax.text(-0.14, 1.055, letter, transform=ax.transAxes,
            fontsize=12, fontweight="bold", ha="left", va="bottom")
    ax.spines[["top", "right"]].set_visible(False)


def save(fig):
    fig.savefig(ROOT / f"{STEM}.png", dpi=300, facecolor="white")
    fig.savefig(ROOT / f"{STEM}.pdf", facecolor="white")
    plt.close(fig)



BLUE, RED = "#2171b5", "#c52d35"


def main():
    draw_data = read_rows("regional_pelagic_pfoa_draws.csv")
    mean_data = read_rows("regional_pelagic_pfoa_geometric_means.csv")
    draws_by_region_year = defaultdict(list)
    for row in draw_data:
        draws_by_region_year[row["region"], int(row["year"])].append(float(row["log10_ng_g"]))

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.55), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.14)
    for ax, letter, region in zip(axes, "ab", ("North America and Europe", "Asia")):
        data = sorted((int(row["year"]), float(row["log10_geometric_mean"]))
                      for row in mean_data if row["region"] == region)
        for year, mean in data:
            draws = draws_by_region_year[region, year]
            np.testing.assert_allclose(np.mean(draws), mean, rtol=1e-12, atol=1e-12)
            ax.scatter(np.full(len(draws), year), draws, s=10, color=BLUE,
                       alpha=0.095, linewidths=0, rasterized=True)
        x, y = np.asarray(data).T
        ax.scatter(x, y, s=22, color=RED, linewidths=0, zorder=3)
        mark_panel(ax, letter, region)
        ax.set(xlim=(2009.5, 2023.5), xlabel="Year",
               ylabel="log₁₀ PFOA concentration (ng/g ww)")
        ax.set_xticks([2010, 2012, 2014, 2016, 2018, 2020, 2022])
    axes[0].legend(handles=[
        Line2D([], [], marker="o", color=BLUE, linestyle="none", alpha=0.45,
               markersize=5, label="Monte Carlo draws"),
        Line2D([], [], marker="o", color=RED, linestyle="none",
               markersize=5, label="Annual geometric mean"),
    ], loc="lower left", fontsize=8, frameon=False)
    save(fig)


if __name__ == "__main__":
    main()
