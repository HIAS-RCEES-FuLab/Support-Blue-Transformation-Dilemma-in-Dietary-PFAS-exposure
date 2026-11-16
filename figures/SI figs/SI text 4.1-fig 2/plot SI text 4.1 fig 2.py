"""Replot the weighted aquatic PFAS panel from 158 archived report–site observations."""

import csv
from itertools import accumulate
from math import exp, fsum, log, sqrt
from pathlib import Path
from statistics import NormalDist

import matplotlib

matplotlib.use('Agg')
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.ticker import FuncFormatter


FOLDER = Path(__file__).resolve().parent
DATA_PATH = FOLDER / 'Weighted quantile plot data.csv'
FIGURE_PATH = FOLDER / 'Aquatic PFAS weighted normal quantile plot.png'
NORMAL = NormalDist()
CONCENTRATION_CUTOFF = 30.0


def load_points(csv_path):
    with csv_path.open(encoding='utf-8-sig', newline='') as stream:
        return [(row['source_report'], row['sampling_location'], float(row['sum7_ng_g_ww']),
                 int(row['estimated_sample_weight'])) for row in csv.DictReader(stream)]


def plotting_positions(points):
    ordered = sorted(points, key=lambda point: (point[2], point[0], point[1]))
    if not ordered or any(concentration <= 0 or weight <= 0 for _, _, concentration, weight in ordered):
        raise ValueError('Concentrations and sample weights must be positive.')
    if len({point[:2] for point in ordered}) != len(ordered):
        raise ValueError('The source data contain a repeated report–site key.')
    cumulative = list(accumulate(point[3] for point in ordered))
    total = cumulative[-1]
    records = []
    for point, cum in zip(ordered, cumulative):
        probability = (cum - point[3] / 2) / total
        records.append((*point, cum, probability, NORMAL.inv_cdf(probability)))
    p90_index = next(i for i, cum in enumerate(cumulative) if 10 * cum >= 9 * total)
    return records, total, p90_index


def fit_lognormal(rows):
    weighted_logs = [(row[3], log(row[2])) for row in rows]
    total = sum(weight for weight, _ in weighted_logs)
    mean = fsum(weight * value for weight, value in weighted_logs) / total
    sd = sqrt(fsum(weight * (value - mean) ** 2 for weight, value in weighted_logs) / total)
    return mean, sd


def plot(rows, p90_index, output):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.labelcolor': '#24313a',
                         'xtick.color': '#24313a', 'ytick.color': '#24313a', 'text.color': '#172631',
                         'axes.spines.top': False, 'axes.spines.right': False})
    cmap = LinearSegmentedColormap.from_list('concentration', ['#17854b', '#f0d84c', '#c6272d'])
    fig, ax = plt.subplots(figsize=(6.5, 5.1))
    fig.subplots_adjust(left=.147, right=.959, top=.786, bottom=.238)
    fig.text(.147, .935, 'Σ₇PFAS concentrations in aquatic foods', fontsize=15.5, weight='bold', va='top')
    fig.text(.147, .867, f'Weighted by estimated sample count  |  {len(rows)} report–site means',
             fontsize=9.5, color='#4c5b67', va='top')

    ax.set(yscale='log', ylim=(.002, 520), xlim=(-4, 4),
           xlabel='Standard normal quantile (z)', ylabel='Mean Σ₇PFAS (ng/g wet weight)')
    ax.xaxis.labelpad = 9
    ax.yaxis.labelpad = 9
    ax.set_xticks(range(-4, 5))
    ax.set_yticks([.003, .01, .1, 1, 10, 100, 300])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
    ax.tick_params(which='both', length=3, color='#b0bbc2')
    ax.spines[['bottom', 'left']].set_color('#a8b4bd')
    ax.set_axisbelow(True)
    ax.grid(axis='y', which='major', color='#e7ecef', linewidth=.8)

    mean, sd = fit_lognormal(rows)
    x_reference = ax.get_xlim()
    ax.plot(x_reference, [exp(mean + sd * z) for z in x_reference], color='#687984', linewidth=1.15,
            zorder=1.5, label='Lognormal fit')
    ax.legend(loc='lower right', frameon=False, fontsize=9)
    p90 = rows[p90_index][2]
    p90_z = rows[p90_index][6]
    guide_style = {'color': '#738292', 'linewidth': 1, 'linestyle': (0, (3, 3)), 'zorder': 2}
    ax.axvline(NORMAL.inv_cdf(.90), **guide_style)
    ax.axhline(CONCENTRATION_CUTOFF, **guide_style)
    ranks = [i / max(1, len(rows) - 1) for i in range(len(rows))]
    ax.scatter([row[6] for row in rows], [row[2] for row in rows], c=ranks, cmap=cmap,
               s=30, linewidths=.3, edgecolors='#40515a', zorder=3)
    ax.scatter(p90_z, p90, s=88, facecolors='none', edgecolors='#152c43', linewidths=1.25, zorder=4)
    ax.annotate(f'{CONCENTRATION_CUTOFF:.1f} ng/g', xy=(ax.get_xlim()[0], CONCENTRATION_CUTOFF),
                xytext=(7, 5), textcoords='offset points', ha='left', va='bottom',
                weight='bold', color='#152c43', zorder=5,
                bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 2, 'alpha': .96})

    bar_ax = fig.add_axes([.30, .086, .52, .018])
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0, 1), cmap=cmap),
                       cax=bar_ax, orientation='horizontal')
    bar.set_ticks([0, .5, 1], labels=['Lowest', 'Median', 'Highest'])
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=0, pad=4, labelsize=9)
    fig.savefig(output, dpi=300, facecolor='white', metadata={'Title': 'Weighted aquatic PFAS normal quantile plot'})
    plt.close(fig)


def main():
    rows, _, p90_index = plotting_positions(load_points(DATA_PATH))
    plot(rows, p90_index, FIGURE_PATH)


if __name__ == '__main__':
    main()
