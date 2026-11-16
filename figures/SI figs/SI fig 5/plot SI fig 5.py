"""Draw the current SI Fig. 5 GDP–HI regressions from the 47 country pairs in the archived summary."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
import csv
import numpy as np
from scipy.stats import linregress
from matplotlib.colors import to_rgb
from matplotlib.ticker import PercentFormatter

HERE = Path(__file__).resolve().parent


def save(fig, folder, name):
    for ext in ('pdf', 'png'):
        fig.savefig(folder / f'{name}.{ext}', dpi=400, facecolor='white', bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)


def plot_style():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.labelsize': 11,
        'axes.titlesize': 11, 'axes.linewidth': .9, 'axes.facecolor': 'white',
        'xtick.labelsize': 9, 'ytick.labelsize': 9, 'pdf.fonttype': 42})


def scatter_style(ax):
    ax.grid(which='major', axis='both', color='.7', ls='--', lw=.8, alpha=.46)
    ax.set_axisbelow(True)
    ax.tick_params(axis='both', which='major', length=4)


def plot(folder):
    with (folder / "Country GDP growth and HI data.csv").open(encoding="utf-8-sig", newline="") as handle:
        data = [{key: float(row[key]) for key in ("real_gdp_per_capita_change_pct", "bau_hi_change_pct",
                                                "hr_hi_change_pct")} for row in csv.DictReader(handle)]
    x = np.array([row['real_gdp_per_capita_change_pct'] for row in data])
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.7), sharex=True, sharey=True, layout='constrained')
    for panel, ax, column, title, color in zip('ab', axes, ('bau_hi_change_pct', 'hr_hi_change_pct'),
            ('Business as Usual', 'High Road'), ('#D09A59', '#CF837D')):
        y = np.array([row[column] for row in data])
        fit = linregress(x, y)
        xx = np.array([x.min(), x.max()])
        ax.axhline(0, color='0.62', ls=':', lw=1.1, zorder=1)
        ax.plot(xx, fit.intercept + fit.slope * xx, ls='--', lw=1.5, c=np.array(to_rgb(color))*.70, zorder=2)
        ax.scatter(x, y, s=29, marker='o', color=color, edgecolors='black', linewidths=.6, zorder=3)
        ax.set_title(f'{panel}   {title}', loc='left', fontweight='bold')
        ax.text(.97, .98, f'$r$ = {fit.rvalue:.3f}    $p$ = {fit.pvalue:.4f}\n$n$ = {len(x)}',
                transform=ax.transAxes, ha='right', va='top', fontsize=9, zorder=4)
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        scatter_style(ax)
    axes[0].set_ylabel('Change in hazard index, 2020–2050')
    fig.supxlabel('Projected change in real GDP per capita, 2020–2050', fontsize=11)
    save(fig, folder, 'GDP per capita growth and HI change - BAU and HR')


def main():
    plot_style()
    plot(HERE)


if __name__ == "__main__":
    main()
