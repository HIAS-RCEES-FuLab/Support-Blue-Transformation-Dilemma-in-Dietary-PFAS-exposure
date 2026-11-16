"""Reproduce the eight serum–EDI regressions from the 56 archived chart-cache points. Uses the archived one-sided tests for positive correlation."""

import csv
import math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


PANELS = [('a', 'Σ7PFAS'), ('b', 'PFHxS'), ('c', 'PFOS'), ('d', 'PFOA'), ('e', 'PFNA'), ('f', 'PFDA'), ('g', 'PFUnDA'), ('h', 'PFDoDA')]


def pearson_stats(x, y):
    r = float(np.corrcoef(x, y)[0, 1])
    df = len(x) - 2
    t = r * math.sqrt(df / (1 - r**2))
    # Integrate the exact Student t tail with x = sqrt(df) * cot(theta).
    nodes, weights = np.polynomial.legendre.leggauss(128)
    theta = math.atan2(math.sqrt(df), abs(t))
    angles = (nodes + 1) * theta / 2
    factor = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(math.pi)
    tail = factor * float(np.dot(weights, np.sin(angles) ** (df - 1))) * theta / 2
    return r, tail if r >= 0 else 1 - tail, 2 * tail


def plot(data, output):
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcdefaults()

    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
        "axes.spines.right": False, "savefig.facecolor": "white", "pdf.fonttype": 42,
    })
    with (data / "EDI_serum_coordinates.csv").open(encoding="utf-8-sig", newline="") as file:
        coordinates = list(csv.DictReader(file))
    fig, axes = plt.subplots(4, 2, figsize=(8, 9.2), layout="constrained")
    for axis, (panel, compound) in zip(axes.flat, PANELS):
        selected = [row for row in coordinates if row["panel"] == panel]
        x = np.array([float(row["edi_ng_kg_bw_day"]) for row in selected])
        y = np.array([float(row["serum_ng_ml"]) for row in selected])
        r, p, _ = pearson_stats(x, y)
        slope, intercept = np.polyfit(x, y, 1)
        limits = np.array([x.min(), x.max()])
        axis.scatter(x, y, color="#216d9c", s=26, zorder=3)
        axis.plot(limits, slope * limits + intercept, ":", color="#216d9c", linewidth=1.4)
        axis.set_title(f"{panel}  {compound}", loc="left", fontweight="bold")
        p_label = f"P = {p:.3f}" if p >= 0.0005 else "P < 0.001"
        axis.text(0.05, 0.95, f"r = {r:.3f}\n{p_label}", transform=axis.transAxes,
                  va="top", fontsize=8.5, bbox=dict(facecolor="white", edgecolor="none", alpha=0.9))
        axis.grid(color="#e2e8ec", linewidth=0.6)
        axis.margins(x=0.1, y=0.1)
    fig.supxlabel("Estimated daily intake (ng kg⁻¹ body weight day⁻¹)")
    fig.supylabel("Serum concentration (ng mL⁻¹)")
    fig.suptitle("Dietary PFAS intake and serum concentrations\nPearson tests for positive correlation, seven two-year periods", fontsize=11)
    name = output / "SI_5_Fig_1_EDI_serum_correlations"
    fig.savefig(str(name) + ".png", dpi=300)
    fig.savefig(str(name) + ".pdf")
    plt.close(fig)


def main():
    plot(HERE, HERE)


if __name__ == "__main__":
    main()
