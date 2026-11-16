"""SI text 9-fig 2 — PFOS, PFOA and PFNA in aquatic food from five major exporters.

Source: the three congener-specific archived production 2030 HR top 5
countries Sample Data worksheets. The archived random-number state
preserves the horizontal jitter when rebuilding this panel on its own.

Inputs are in the adjacent data folder. Run with Python, Matplotlib,
NumPy and pandas installed.
"""


from pathlib import Path
import json



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


def read_distribution(key):
    return pd.read_csv(DATA / f"{key}.csv.gz")


def draw_points(ax, x, values, color, rng, spread=.073):
    positive = values[np.isfinite(values) & (values > 0)]
    ax.scatter(x + rng.normal(0, spread, len(positive)).clip(-.27, .27), positive,
               color=color, s=3.0, alpha=.26, linewidths=0, rasterized=True)


def plot_congeners():
    rng = np.random.default_rng()
    with (DATA / "jitter_rng_state.json").open(encoding="utf-8") as handle:
        rng.bit_generator.state = json.load(handle)
    fig, axes = plt.subplots(3, 1, figsize=(8.6, 10.6), sharex=True, layout="constrained")
    ordered = ["United States", "Canada", "China", "Norway", "Germany"]
    for j, (compound, ax) in enumerate(zip(("PFOS", "PFOA", "PFNA"), axes)):
        table = read_distribution(f"top5_{compound}")
        groups = [table.loc[table.Country.eq(c), "Total_PFAS_Concentration"].to_numpy() for c in ordered]
        for pos, values in enumerate(groups):
            draw_points(ax, pos, values, f"C{pos}", rng, spread=.073)
        ax.boxplot(groups, positions=range(5), widths=.60, whis=(1, 99), showfliers=False,
                   boxprops={"linewidth": .9}, whiskerprops={"linewidth": .9},
                   capprops={"linewidth": .9}, medianprops={"color": "#e38225"})
        q95 = table.Total_PFAS_Concentration.quantile(.95)
        ax.axhline(q95, ls="--", lw=1, color="#2674a5")
        ax.text(4.42, q95*1.07, f"{q95:.2f}", ha="right", color="#2674a5")
        ax.set(yscale="log", xlim=(-.5, 4.5), ylabel=f"{compound} (ng/g wet weight)")
        ax.text(.012, .96, chr(97+j), transform=ax.transAxes, va="top", fontweight="bold", fontsize=12)
    axes[-1].set_xticks(range(5), ordered)
    save(fig, "SI_9_Fig_2_top_five_exporter_congeners")


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
    plot_congeners()
