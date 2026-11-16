"""Reproduce SI Text 2.3 Fig. 5 from the plot data beside this script.

The local inputs preserve the 2026-11-12 deterministic fits to annual
geometric means and the plotted Monte Carlo concentrations. The fit is rebuilt
from its saved slopes and breakpoints. Requires NumPy and Matplotlib.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


STEM = "SI_Text_2_3_Fig5_5_segment_piecewise"
PANEL_ORDER = ('Sum-7', 'PFHxS', 'PFOS', 'PFDA', 'PFOA', 'PFNA', 'PFUnDA', 'PFDoDA')

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



BLUE, RED, GREEN = "#2171b5", "#c52d35", "#2f7d44"


def fitted_line(years, segments, initial):
    """Start at the first fitted value and accumulate each elapsed slope."""
    fitted = np.full(np.shape(years), initial, dtype=float)
    for row in segments:
        start = float(row["start_year"])
        stop = float(row["end_year"])
        fitted += float(row["log10_slope_per_year"]) * np.clip(years - start, 0, stop - start)
    return fitted


def main():
    means = read_rows("annual_and_fitted_values.csv")
    slopes = read_rows("piecewise_segments.csv")
    fig, axes = plt.subplots(3, 3, figsize=(10.7, 8.0), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.11, h_pad=0.12)
    with np.load(ROOT / "monte_carlo_scatter.npz", allow_pickle=False) as scatter:
        for ax, letter, compound in zip(axes.flat, "abcdefgh", PANEL_ORDER):
            data = sorted((row for row in means if row["chemical"] == compound),
                          key=lambda row: int(row["year"]))
            x = np.array([int(row["year"]) for row in data])
            y = np.array([float(row["observed_log10"]) for row in data])
            fit = np.array([float(row["fitted_log10"]) for row in data])
            segments = sorted((row for row in slopes if row["chemical"] == compound),
                              key=lambda row: int(row["segment"]))
            knots = [float(row["end_year"]) for row in segments[:-1]]
            dense_years = np.sort(np.r_[np.linspace(x.min(), x.max(), 500), knots])
            np.testing.assert_allclose(fitted_line(x, segments, fit[0]), fit,
                                       rtol=1e-10, atol=1e-10)

            ax.scatter(scatter[f"{compound}_year_jittered"], scatter[f"{compound}_log10_ng_g"],
                       s=3.2, color=BLUE, linewidths=0, alpha=0.07, rasterized=True)
            ax.scatter(x, y, s=7, facecolor="white", edgecolor=BLUE, linewidth=0.45, zorder=3)
            ax.plot(dense_years, fitted_line(dense_years, segments, fit[0]),
                    color=RED, linewidth=1.35, zorder=4)
            for knot in knots:
                ax.axvline(knot, color=GREEN, linewidth=1.05, linestyle="--", zorder=2)
            mark_panel(ax, letter, "Σ7PFAS" if compound == "Sum-7" else compound)
            ax.set(xlim=(1998.6, 2024.1))
            ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2023])
            if letter in "adg":
                ax.set_ylabel("log₁₀ concentration (ng/g ww)")
            if letter in "fgh":
                ax.set_xlabel("Year")
    legend = axes.flat[8]
    legend.axis("off")
    legend.legend(handles=[
        Line2D([], [], marker="o", color=BLUE, linestyle="none", alpha=0.42,
               markersize=4, label="Monte Carlo draws"),
        Line2D([], [], marker="o", color=BLUE, linestyle="none", markerfacecolor="white",
               markersize=4, label="Annual geometric means"),
        Line2D([], [], color=RED, linewidth=1.35, label="Piecewise fit"),
        Line2D([], [], color=GREEN, linestyle="--", label="Breakpoint"),
    ], loc="center", frameon=False, fontsize=9)
    save(fig)


if __name__ == "__main__":
    main()
