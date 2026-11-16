"""Redraw SI Text 6.4 Figure 1 from the accompanying CSV data."""

import csv
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main():
    data = HERE
    output = HERE
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcdefaults()

    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "axes.titleweight": "normal",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.75,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )
    blue = "#176795"
    output.mkdir(parents=True, exist_ok=True)

    def finish(figure, name):
        figure.savefig(output / f"{name}.png", dpi=300)
        figure.savefig(output / f"{name}.pdf")
        plt.close(figure)

    def decorate(axis, letter, title):
        axis.set_title(f"{letter}   {title}", loc="left", pad=8)
        axis.grid(axis="y", color="#dce3e8", linewidth=0.6)
        axis.set_axisbelow(True)

    label = 'BPQ020'
    disease = 'Hypertension'
    fig, axes = plt.subplots(2, 2, figsize=(8.7, 6.5), layout="constrained")
    fig.suptitle(f"{disease} model validation ({label})", fontsize=12, fontweight="bold")
    compound = "PFOS"
    for axis, letter, test in zip(axes[0], "ab", ("T", "X")):
        rows = read_csv(data / f"{label}_{test}_permutation.csv")
        x = np.array([float(row["log10_serum_concentration"]) for row in rows])
        y = np.array([float(row["estimated_probability_change"]) for row in rows])
        axis.scatter(x, y, s=6, color=blue, alpha=0.18, linewidths=0, rasterized=True)
        axis.axhline(0, color="#6c757d", linewidth=0.7, zorder=0)
        axis.set_xlim(-2, 2.6)
        axis.set_ylim(
            (min(-0.45, y.min() - 0.02), max(0.42, y.max() + 0.02))
            if test == "T"
            else (min(-0.08, y.min() - 0.02), max(0.95, y.max() + 0.02))
        )
        axis.set_xlabel(r"$\log_{10}$" + rf" [serum {compound} (ng mL$^{{-1}}$)]")
        axis.set_ylabel("Estimated change in probability")
        decorate(axis, letter, f"{test}-permutation")
        axis.text(
            0.04, 0.96, f"Mean = {np.mean(y):.4f}\nSD = {np.std(y):.4f}",
            transform=axis.transAxes, ha="left", va="top", fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 2},
        )

    for axis, letter, test in zip(axes[1], "cd", ("T", "X")):
        rows = read_csv(data / f"{label}_{test}_robustness.csv")
        x = [int(row["step"]) for row in rows]
        y = [float(row["mean_estimated_probability_change"]) for row in rows]
        errors = [float(row["error_bar_sd_across_step_means"]) for row in rows]
        axis.errorbar(x, y, yerr=errors, fmt="o-", color=blue, linewidth=1.25, markersize=4, capsize=2)
        axis.set_xlim(0.55, 10.45)
        axis.set_xticks(x)
        axis.yaxis.set_major_locator(MaxNLocator(5))
        axis.set_xlabel("Robustness-test step")
        axis.set_ylabel("Mean change in probability")
        decorate(axis, letter, f"{test}-robustness")
    finish(fig, 'SI_6.4_Fig_1_hypertension_validation')


if __name__ == "__main__":
    main()
