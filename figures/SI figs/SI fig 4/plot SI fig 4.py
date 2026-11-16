"""Draw the current SI Fig. 4 log-scale estimated versus measured serum concentrations from the archived country pairs."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

HERE = Path(__file__).resolve().parent


PANELS = {
    "Sum4": {"title": r"$\Sigma_4$ PFAS", "slug": "sum4", "color": "#CF837D"},
    "PFOS": {"title": "PFOS", "slug": "pfos", "color": "#D09A59"},
    "PFOA": {"title": "PFOA", "slug": "pfoa", "color": "#729CB5"},
}
POPULATION_MARKERS = {
    "Adults": "o",
    "Whole population": "s",
    "Mothers/female only": "^",
    "Other/unspecified": "D",
}
TICKS = np.array([0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100])


def darken(color: str, factor: float = 0.70) -> tuple[float, float, float]:
    return tuple(channel * factor for channel in to_rgb(color))


def bounds_for(values: np.ndarray) -> tuple[float, float]:
    lo = float(np.min(values)) * 0.68
    hi = float(np.max(values)) * 1.55
    return lo, hi


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
    plot_style()
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 3.25), layout='constrained')
    data = pd.read_csv(folder / "Serum concentration pairs.csv")
    for panel, ax, (name, style) in zip('abc', axes, PANELS.items()):
        pairs = data.loc[data.analyte == name].rename(columns={
            "cohort_group": "population_group", "measured_ng_ml": "measured", "estimated_ng_ml": "predicted"
        })
        x, y = pairs['measured'].to_numpy(), pairs['predicted'].to_numpy()
        fit = linregress(np.log10(x), np.log10(y))
        expected = {'Sum4': (11, .713), 'PFOS': (15, .627), 'PFOA': (15, .748)}
        assert (len(x), round(fit.rvalue, 3)) == expected[name]
        limits = bounds_for(np.concatenate([x, y]))
        ax.set(xscale='log', yscale='log', xlim=limits, ylim=limits)
        xx = np.geomspace(*limits, 200)
        ax.plot(xx, xx, color='0.62', ls=':', lw=1.1, zorder=1)
        ax.plot(xx, 10**fit.intercept * xx**fit.slope, ls='--', lw=1.45, c=darken(style['color']), zorder=2)
        for group, marker in POPULATION_MARKERS.items():
            subset = pairs.loc[pairs.population_group == group]
            if not subset.empty:
                ax.scatter(subset.measured, subset.predicted, marker=marker, s=36,
                           c=style['color'], edgecolors='black', linewidths=.7, zorder=3)
        ticks = TICKS[(TICKS >= limits[0]) & (TICKS <= limits[1])]
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda val, _: f'{val:g}'))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _: f'{val:g}'))
        ax.set_title(f'{panel}   {style["title"]}', loc='left', fontweight='bold')
        ax.text(.035, .96, f'$r$ = {fit.rvalue:.3f}    $p$ = {fit.pvalue:.3f}\n$R^2$ = {fit.rvalue**2:.3f}',
                transform=ax.transAxes, ha='left', va='top', fontsize=9, zorder=4)
        scatter_style(ax)
        handles = [Line2D([0], [0], marker=m, linestyle='none', color='black', markerfacecolor=style['color'],
            markersize=6, label=g) for g, m in POPULATION_MARKERS.items() if g in set(pairs.population_group)]
        ax.legend(handles=handles, loc='lower right', fontsize=7.4, frameon=True, edgecolor='none', framealpha=.94)
    axes[0].set_ylabel('Estimated geometric mean (ng/mL)')
    fig.supxlabel('Measured serum concentration (ng/mL)', fontsize=11)
    save(fig, folder, 'Estimated versus measured serum PFAS concentrations')


def main():
    plot(HERE)


if __name__ == "__main__":
    main()
