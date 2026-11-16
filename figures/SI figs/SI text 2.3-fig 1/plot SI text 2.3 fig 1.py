"""Reproduce SI Text 2.3 Fig. 1 from the plot data beside this script.

The local CSV contains the archived whole-food series from the conc sheet of
infor to plot fig0.xlsx. Annual geometric means have equal weight in the fits.
Requires NumPy, Matplotlib and SciPy.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr


STEM = "SI_Text_2_3_Fig1_annual_Sum7PFAS"

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



def main():
    data = read_rows("annual_geometric_means.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.16)
    groups = (("Aquatic foods", "#1c9e89"), ("Terrestrial foods", "#d59833"))
    for ax, letter, (group, colour) in zip(axes, "ab", groups):
        x, y = np.asarray([
            (int(row["year"]), float(row["geometric_mean_ng_g"]))
            for row in data if row["food_group"] == group
        ]).T
        r, p = pearsonr(x, y)
        coefficients = np.polyfit(x - 2000, y, 1)
        line_year = np.linspace(x.min(), x.max(), 150)
        ax.scatter(x, y, color=colour, edgecolor="#202020", linewidth=0.5,
                   s=24, zorder=3, label="Annual geometric mean")
        ax.plot(line_year, np.polyval(coefficients, line_year - 2000),
                color="#c52d35", linestyle="--", linewidth=1.4, label="Linear fit")
        ax.text(0.96, 0.9, f"r = {r:.3f}, p = {p:.3f}",
                transform=ax.transAxes, ha="right", va="top")
        mark_panel(ax, letter, group)
        ax.set(xlim=(1999.5, 2023.5), ylim=(-0.15, 8.4),
               xlabel="Year", ylabel="Σ7PFAS concentration (ng/g ww)")
        ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2023])
        ax.grid(axis="y", linewidth=0.5, color="#dddddd")
        if letter == "a":
            ax.legend(loc="upper left", frameon=False, fontsize=7)
    save(fig)


if __name__ == "__main__":
    main()
