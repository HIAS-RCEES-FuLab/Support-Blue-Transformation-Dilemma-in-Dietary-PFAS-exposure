"""SI fig 1 — Aquatic-food source-share matrices.

Source: Data 7_International food trade source-share matrices.xlsx,
the Trade aquatic and MetaTrade aquatic worksheets (47 × 47).

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
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
COUNTRY_GROUPS = [
    ["Australia", "New Zealand"],
    ["China", "India", "Indonesia", "Japan", "Korea", "Turkiye", "Israel"],
    ["Bulgaria", "Czechia", "Hungary", "Poland", "Romania", "Slovak Republic",
     "Denmark", "Estonia", "Finland", "Iceland", "Ireland", "Latvia", "Lithuania",
     "Norway", "Sweden", "United Kingdom", "Croatia", "Greece", "Italy", "Portugal",
     "Slovenia", "Spain", "Austria", "Belgium", "France", "Germany", "Luxembourg",
     "Netherlands", "Switzerland"],
    ["Canada", "Costa Rica", "Mexico", "United States"],
    ["Argentina", "Brazil", "Chile", "Colombia"],
    ["South Africa"],
]
MATRIX_COLORS = ["#cf50dc", "#ffb600", "#ef6064", "#8bc454", "#4db3d2", "#999999"]


def save(fig, name, dpi=300):
    for ext in ("png", "pdf"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=dpi, facecolor="white")
    plt.close(fig)
    print(name, flush=True)


def plot_trade_matrices(food):
    fig, axes = plt.subplots(2, 1, figsize=(14, 15.8))
    fig.subplots_adjust(left=.105, right=.985, top=.967, bottom=.080, hspace=.29)
    for j, (ax, scenario) in enumerate(zip(axes, ("Trade", "MetaTrade"))):
        groups = COUNTRY_GROUPS
        if scenario == "MetaTrade" and food == "terrestrial":
            groups = [sorted(group) for group in COUNTRY_GROUPS]
        order = [country for group in groups for country in group]
        table = pd.read_csv(DATA / f"{scenario.lower()}_{food}.csv", index_col=0)
        shares = table.loc[order, order].to_numpy()
        colors = np.array([to_rgb(c) for c, group in zip(MATRIX_COLORS, groups) for _ in group])
        rgb = 1 - shares[:, :, None]**.61 * (1-colors[:, None, :])
        ax.imshow(rgb, interpolation="none", aspect="auto")
        for r, c in zip(*np.where(shares >= .005)):
            ax.text(c, r, f"{shares[r,c]:.2f}", ha="center", va="center", fontsize=4.55)
        first = 0
        for group, color in zip(groups, MATRIX_COLORS):
            n = len(group)
            ax.add_patch(Rectangle((first-.5, first-.5), n, n, edgecolor=color, linewidth=.55, fill=False))
            first += n
        ax.set(title=scenario, xlim=(-.5, 46.5), ylim=(46.5, -.5), ylabel="Supplier")
        ax.set_xticks(range(47), order, rotation=90)
        ax.set_yticks(range(47), order)
        ax.tick_params(axis="both", length=0, labelsize=5.8, pad=1.5)
        ax.set_xlabel("Consumer", fontsize=8, labelpad=4)
        ax.text(-.032, 1.023, chr(97+j), transform=ax.transAxes, fontweight="bold", fontsize=15)
        for spine in ax.spines.values():
            spine.set_visible(False)
    name = {"aquatic": "SI_Fig_1_aquatic_trade_matrices",
            "terrestrial": "SI_Fig_2_terrestrial_trade_matrices"}[food]
    save(fig, name)


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
    plot_trade_matrices("aquatic")
