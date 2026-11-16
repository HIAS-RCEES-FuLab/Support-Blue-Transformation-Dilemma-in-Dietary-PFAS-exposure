"""SI fig 3 — Change in dietary exposure with international trade.

Source: the total_exposure sheets in the archived 2020 scenarios for
Trade and No-Trade. Pearson correlation also requires SciPy.

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
from matplotlib.ticker import PercentFormatter
from scipy.stats import pearsonr


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def save(fig, name, dpi=300):
    for ext in ("png", "pdf"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=dpi, facecolor="white")
    plt.close(fig)
    print(name, flush=True)


def plot_trade_effect():
    t = pd.read_csv(DATA / "trade_edi_2020.csv")
    pct = 100*(t.trade-t.notrade)/t.notrade
    ylog = np.log10(t.notrade)
    corr = pearsonr(pct, ylog)
    line = np.linspace(pct.min(), pct.max())
    slope, intercept = np.polyfit(pct, ylog, 1)
    fig, ax = plt.subplots(figsize=(7.5, 4.6), layout="constrained")
    ax.scatter(pct, t.notrade, color="#4d7cb6", s=26, zorder=3)
    ax.plot(line, 10**(slope*line+intercept), ":", color="#4d7cb6", linewidth=1.3)
    ax.set(xlim=(-70, 180), ylim=(.1, 100), yscale="log",
           xticks=[-70, -20, 30, 80, 130, 180],
           xlabel="Percentage change in EDI from No-Trade to Trade",
           ylabel="No-Trade EDI (ng/kg bw/day)")
    ax.set_yticks([.1, 1, 10, 100], ["0.1", "1", "10", "100"])
    ax.xaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.grid(color=".85", linewidth=.65)
    ax.text(.965, .915, f"r = {corr.statistic:.3f}\np = {corr.pvalue:.5f}", transform=ax.transAxes,
            ha="right", va="top")
    save(fig, "SI_Fig_3_trade_edi_correlation")


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
    plot_trade_effect()
