"""SI text 2.6-fig 1 — Aquatic-food Σ4PFAS concentration under Trade and MetaTrade.

Source: archived World_PFAS_Distribution_Result workbook Sample Data
worksheets for production 2020 Sum4 and production 2030 HR Sum4.

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
from matplotlib.lines import Line2D


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def save(fig, name, dpi=300):
    for ext in ("png", "pdf"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=dpi, facecolor="white")
    plt.close(fig)
    print(name, flush=True)


def read_distribution(key):
    return pd.read_csv(DATA / f"{key}.csv.gz")


def draw_points(ax, x, values, color, rng, spread=.073):
    positive = values[np.isfinite(values) & (values > 0)]
    ax.scatter(x + rng.normal(0, spread, len(positive)).clip(-.27, .27), positive,
               color=color, s=3.0, alpha=.26, linewidths=0, rasterized=True)


def plot_sum4():
    frames = [read_distribution(key) for key in ("trade_sum4", "metatrade_sum4")]
    categories = [
        ("All aquatic\nfoods", None), ("Freshwater\nfish", "Freshwater Fish"),
        ("Demersal\nfish", "Demersal Fish"), ("Pelagic\nfish", "Pelagic Fish"),
        ("Other marine\nfish", "Marine Fish, Other"), ("Crustaceans", "Crustaceans"),
        ("Molluscs", "Molluscs, Other"),
    ]
    colors = ["#1f77b4", "#ff7f0e"]
    rng = np.random.default_rng(915)
    fig, axes = plt.subplots(1, 7, figsize=(11.5, 6.5), sharey=True)
    fig.subplots_adjust(left=.092, right=.989, bottom=.095, top=.91, wspace=.17)
    for j, (ax, (title, category)) in enumerate(zip(axes, categories)):
        for pos, (table, color) in enumerate(zip(frames, colors)):
            subset = table if category is None else table.loc[table.Food_Type.eq(category)]
            draw_points(ax, pos, subset.Total_PFAS_Concentration.to_numpy(), color, rng, spread=.115)
        ax.axhline(2, color="#ad2929", lw=1, ls="--")
        ax.text(.06, .97, chr(97+j), va="top", transform=ax.transAxes, fontweight="bold", fontsize=12)
        ax.set(title=title, yscale="log", xlim=(-.42, 1.42), xticks=[])
    axes[0].set_ylabel("Σ4PFAS concentration (ng/g wet weight)")
    axes[0].text(-.36, 2.13, "2 ng/g", color="#8b2020", fontsize=8)
    fig.legend([Line2D([], [], marker="o", color=c, linestyle="") for c in colors],
               ["Trade", "MetaTrade"], frameon=False, loc="lower center", ncol=2)
    save(fig, "SI_2.6_Fig_1_sum4_concentration_profiles")


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
    plot_sum4()
