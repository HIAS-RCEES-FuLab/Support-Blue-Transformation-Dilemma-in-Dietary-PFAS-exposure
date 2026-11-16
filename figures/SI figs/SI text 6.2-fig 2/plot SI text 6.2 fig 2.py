"""Reproduce SI Text 6.2 Figure 2 from its local inputs.

The CSV contains all 3,000 AUC and F1 pairs per outcome from the original workbook charts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
from collections import defaultdict
import csv
from matplotlib.ticker import StrMethodFormatter


HERE = Path(__file__).resolve().parent


def save_figure(figure: plt.Figure, directory: Path, basename: str, dpi: int) -> None:
    figure.savefig(directory / f"{basename}.png", dpi=dpi, facecolor="white")
    figure.savefig(directory / f"{basename}.pdf", facecolor="white")
    plt.close(figure)


def plot_model_comparison(provenance: dict, directory: Path, dpi: int) -> None:
    """Draw every model score pair directly from the archived workbook data."""
    data = defaultdict(list)
    with (HERE / "model_auc_f1.csv").open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            outcome = row["outcome"]
            if int(row["repeat"]) != len(data[outcome]) + 1:
                raise ValueError(f"Unexpected model repeat sequence for {outcome}")
            data[outcome].append((float(row["auc"]), float(row["f1"])))

    figure, axes = plt.subplots(2, 1, figsize=(4.95, 5.96))
    figure.subplots_adjust(left=0.151, right=0.969, top=0.944, bottom=0.091, hspace=0.275)
    settings = (
        ("a", "BPQ020", (0.75, 0.93), (0.50, 0.75),
         [0.75, 0.77, 0.79, 0.81, 0.83, 0.85, 0.87, 0.89, 0.91, 0.93],
         [0.50, 0.55, 0.60, 0.65, 0.70, 0.75]),
        ("b", "MCQ160A", (0.60, 0.90), (0.10, 0.70),
         [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90],
         [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70]),
    )
    for axis, (letter, outcome, xlim, ylim, xticks, yticks) in zip(axes, settings, strict=True):
        points = data[outcome]
        outcome_source = provenance["outcomes"][outcome]
        if len(points) != outcome_source["pairs"]:
            raise ValueError(f"Unexpected model count for {outcome}: {len(points)}")
        x_values, y_values = zip(*points, strict=True)
        cutoff = outcome_source["original_dashed_line"]
        axis.scatter(x_values, y_values, s=3.4, marker="o", c="#4472C4", linewidths=0)
        axis.axhline(cutoff, color="#ED7D31", linewidth=0.85, dashes=(1.4, 1.25))
        axis.annotate(f"{cutoff:.4f}", (0.012, cutoff), xycoords=axis.get_yaxis_transform(),
                      xytext=(0, 2.0), textcoords="offset points", fontsize=9, va="bottom")
        axis.set(xlim=xlim, ylim=ylim, xticks=xticks, yticks=yticks)
        axis.set_title(outcome, fontsize=12, pad=4.0)
        axis.set_ylabel("F1", fontsize=10, labelpad=5)
        axis.text(-0.172, 1.012, letter, transform=axis.transAxes, fontsize=12,
                  fontweight="bold", ha="left", va="top")
        axis.xaxis.set_major_formatter(StrMethodFormatter("{x:g}"))
        axis.yaxis.set_major_formatter(StrMethodFormatter("{x:g}"))
        axis.tick_params(axis="both", direction="in", length=3, labelsize=8.7, width=0.8, pad=4)
    axes[-1].set_xlabel("AUC", fontsize=10, labelpad=4)
    save_figure(figure, directory, "SI_Text_6_2_Fig_2_F1_AUC_3000_models", dpi)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    parser.add_argument("--dpi", type=int, default=600)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.linewidth": 0.8})
    provenance = json.loads((HERE / "provenance.json").read_text(encoding="utf-8"))
    plot_model_comparison(provenance, args.output_dir, args.dpi)


if __name__ == "__main__":
    main()
