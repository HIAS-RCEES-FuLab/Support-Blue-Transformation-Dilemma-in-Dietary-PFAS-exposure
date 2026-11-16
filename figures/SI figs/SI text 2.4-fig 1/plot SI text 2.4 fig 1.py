"""Draw 2003–2016 aquatic PFAS concentrations from the archived annual quartiles."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

HERE = Path(__file__).resolve().parent


def save(fig, folder, name):
    for ext in ('pdf', 'png'):
        fig.savefig(folder / f'{name}.{ext}', dpi=400, facecolor='white', bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)


def plot_style():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.labelsize': 11,
        'axes.titlesize': 11, 'axes.linewidth': .9, 'axes.facecolor': 'white',
        'xtick.labelsize': 9, 'ytick.labelsize': 9, 'pdf.fonttype': 42})


FOOD_GROUPS = {"Freshwater fish": "#D75753", "Marine fish": "#D6B340", "Other seafood": "#3C9B79"}
YEARS = range(2003, 2017)


def concentration_plot(folder):
    df = pd.read_csv(folder / 'Annual concentration percentiles.csv')
    fig, ax = plt.subplots(figsize=(9.5, 4.0), layout='constrained')
    legends = []
    for shift, (group, color) in zip((-0.245, 0, 0.245), FOOD_GROUPS.items()):
        data = df.loc[(df.food_group == group) & (df.compound == 'Sum7')]
        for y, lo, med, hi in zip(data.year, data.q25_ng_g_ww, data.median_ng_g_ww, data.q75_ng_g_ww):
            center = y + shift
            ax.add_patch(Rectangle((center - 0.102, lo), 0.204, hi-lo, fc=color, ec=color, lw=1, alpha=.48))
            ax.hlines(med, center-.102, center+.102, color=np.array(to_rgb(color))*.66, lw=1.85, zorder=3)
        legends.append(Patch(fc=color, ec=color, alpha=.55, label=group))
    legends.append(Line2D([0], [0], lw=1.8, color='0.25', label='Median'))
    ax.set(xlim=(2002.5, 2016.5), ylim=(0, df.loc[df.compound == 'Sum7', 'q75_ng_g_ww'].max()*1.16),
           xticks=list(YEARS), xlabel='Simulation year', ylabel=r'$\Sigma_7$ PFAS concentration (ng/g ww)')
    ax.grid(axis='y', lw=.65, ls='--', color='.77')
    ax.set_axisbelow(True)
    ax.legend(handles=legends, ncol=4, loc='upper right', frameon=True, edgecolor='none', framealpha=.96)
    save(fig, folder, 'SI Text 2.4 Fig 1 - Calibrated aquatic PFAS concentrations')


def main():
    plot_style()
    concentration_plot(HERE)


if __name__ == "__main__":
    main()
