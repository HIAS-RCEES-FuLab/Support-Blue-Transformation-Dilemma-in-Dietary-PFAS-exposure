"""SI text 9-fig 3 — Aquatic-food EDI before and after the simulated ban.

Source: the archived before-ban and after-ban aquatic PFAS statistics
by country. Daily intakes use the 65 kg body weight in the source plot.

Inputs are in the adjacent data folder. Run with Python, Matplotlib,
NumPy and pandas installed.
"""


from pathlib import Path



import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def save(fig, name, dpi=300):
    for ext in ("png", "pdf"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=dpi, facecolor="white")
    plt.close(fig)
    print(name, flush=True)


def plot_ban():
    before = pd.read_csv(DATA / "aquatic_edi_before_ban.csv", index_col="Country").sort_values("mean", ascending=False)
    after = pd.read_csv(DATA / "aquatic_edi_after_ban.csv", index_col="Country").reindex(before.index)
    keys = ["p1", "p25", "median", "p75", "p99", "mean"]
    before, after = before[keys]/65, after[keys]/65
    fig, ax = plt.subplots(figsize=(6.9, 10.6))
    fig.subplots_adjust(left=.235, right=.72, top=.98, bottom=.06)
    for offset, table, color, dot in [(-.18, before, "#F28E2B", "#7A3E00"),
                                       (.18, after, "#59A14F", "#1E5B2A")]:
        y = np.arange(len(table)) + offset
        for lo, hi, alpha in [("p1", "p99", .30), ("p25", "p75", .64)]:
            ax.hlines(y, table[lo], table[hi], linewidth=3.9, color=color, alpha=alpha)
        ax.vlines(table["median"], y-.145, y+.145, linewidth=1, color=color)
        ax.scatter(table["mean"], y, color=dot, s=7, zorder=5)
    ax.set(xscale="log", xlabel="Aquatic-food EDI (ng/kg bw/day)",
           yticks=np.arange(len(before)), yticklabels=before.index, ylim=(len(before)-.5, -.5))
    ax.tick_params(axis="y", labelsize=8.5)
    ax.grid(axis="x", color=".85", linestyle="--", alpha=.8)
    guide = fig.add_axes([.745, .83, .235, .13])
    guide.set(xlim=(0, 1), ylim=(0, 1))
    guide.axis("off")
    for y, color, dot, title in [(.72, "#F28E2B", "#7A3E00", "Before ban"),
                                  (.31, "#59A14F", "#1E5B2A", "After ban")]:
        guide.hlines(y, .05, .95, color=color, alpha=.30, lw=4)
        guide.hlines(y, .34, .71, color=color, alpha=.64, lw=4)
        guide.vlines(.55, y-.05, y+.05, color=color, lw=1)
        guide.scatter(.47, y, color=dot, s=8, zorder=4)
        guide.text(.5, y-.17, title, ha="center", fontsize=8)
    for pos, label in zip((.05, .34, .55, .71, .95), ("1%", "25%", "50%", "75%", "99%")):
        guide.text(pos, .83, label, ha="center", fontsize=7.5)
    guide.text(.5, .02, "Dot = mean", ha="center", fontsize=7.5)
    save(fig, "SI_9_Fig_3_edi_before_and_after_ban")


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
    plot_ban()
