"""SI text 9-fig 1 — Σ7PFAS in aquatic food from five major exporters.

Source: 100,000 draws in the archived production 2030 HR top 5 countries
Sample Data worksheet. The 95th percentile is 9.48497 ng/g.

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


def read_distribution(key):
    return pd.read_csv(DATA / f"{key}.csv.gz")


def draw_points(ax, x, values, color, rng, spread=.073):
    positive = values[np.isfinite(values) & (values > 0)]
    ax.scatter(x + rng.normal(0, spread, len(positive)).clip(-.27, .27), positive,
               color=color, s=3.0, alpha=.26, linewidths=0, rasterized=True)


def plot_total_pfas():
    frame = read_distribution("top5_sum7")
    rng = np.random.default_rng(952)
    fig, ax = plt.subplots(figsize=(9.2, 5.6), layout="constrained")
    ordered = ["Canada", "United States", "Germany", "Norway", "China"]
    for pos, country in enumerate(ordered):
        values = frame.loc[frame.Country.eq(country), "Total_PFAS_Concentration"].to_numpy()
        draw_points(ax, pos, values, f"C{pos}", rng, spread=.097)
    quantile = frame.Total_PFAS_Concentration.quantile(.95)
    ax.axhline(quantile, ls="--", lw=1, color="#2674a5")
    ax.text(-.45, quantile*1.09, f"{quantile:.2f} ng/g", color="#2674a5")
    ax.set(yscale="log", xlim=(-.5, 4.5), xticks=range(5), xticklabels=ordered,
           ylabel="Σ7PFAS concentration (ng/g wet weight)")
    save(fig, "SI_9_Fig_1_top_five_exporter_concentrations")


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
    plot_total_pfas()
