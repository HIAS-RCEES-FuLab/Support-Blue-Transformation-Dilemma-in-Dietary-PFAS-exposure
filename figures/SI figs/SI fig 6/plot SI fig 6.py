"""Rebuild SI Fig. 6 from the archived PFOS/PFOA modeled and measured values."""

from pathlib import Path

import matplotlib

matplotlib.use('Agg')
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
STEM = "SI Fig 6 - PBK serum concentrations and source composition"
STYLES = {
    'no_exposure': ('No exposure after 2004', '#6f6f6f', '--'),
    'terrestrial_only': ('Terrestrial only', '#f0a000', '-'),
    'aquatic_plus_terrestrial': ('Terrestrial + aquatic', '#e65a5a', '-'),
}


def main():
    metrics = ['arithmetic_mean', 'p25', 'p75']
    pfos, pfoa = [pd.read_csv(HERE / f'{name}_combined_period_results.csv').set_index(['scenario', 'period'])
                 for name in ('pfos', 'pfoa')]
    observed = pd.read_csv(HERE / 'nhanes_pfoa_pfos_iqr.csv').set_index('period')
    periods = observed.index.tolist()
    assert pfos.index.is_unique and pfoa.index.is_unique and observed.index.is_unique
    assert set(pfos.index) == set(pfoa.index)
    displayed = pd.MultiIndex.from_product([STYLES, periods], names=['scenario', 'period'])
    assert set(displayed) <= set(pfos.index)
    assert periods == [f'{y}-{y+1}' for y in range(2003, 2017, 2)]
    # Match the existing panel's arithmetic means and marginal percentile band.
    estimated = pfos.loc[displayed, metrics] + pfoa.loc[displayed, metrics]
    total = estimated.loc['aquatic_plus_terrestrial'].loc[periods]
    assert np.isfinite(estimated[metrics].to_numpy()).all()
    assert (total.p25 <= total.p75).all()
    assert (observed.p25 <= observed.arithmetic_mean).all() and (observed.arithmetic_mean <= observed.p75).all()

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.labelsize': 11,
        'xtick.labelsize': 9, 'ytick.labelsize': 9, 'axes.linewidth': .9, 'pdf.fonttype': 42})
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(6.1, 7.0), layout='constrained',
                                gridspec_kw={'height_ratios': [1.14, 1]})
    x = np.arange(len(periods))
    band_color = STYLES['aquatic_plus_terrestrial'][1]
    ax.fill_between(x, total.p25, total.p75, color=band_color, alpha=.18, linewidth=0, zorder=1)
    lines = []
    for scenario, (label, color, style) in STYLES.items():
        line, = ax.plot(x, estimated.loc[scenario].loc[periods].arithmetic_mean, label=label,
                        color=color, ls=style, marker='o', ms=5.5, lw=2, zorder=3)
        lines.append(line)
    y = observed.arithmetic_mean.to_numpy()
    errors = ax.errorbar(x, y, yerr=[y-observed.p25.to_numpy(), observed.p75.to_numpy()-y],
                         fmt='none', ecolor='black', elinewidth=.9, capsize=2.5, capthick=.9,
                         label='NHANES 25th–75th percentiles', zorder=4)
    measured, = ax.plot(x, y, color='black', marker='o', ms=5.5, lw=2.2, label='NHANES measured', zorder=5)
    ax.set(ylim=(0, 42), xlim=(-.27, 6.27), xticks=x, yticks=range(0, 41, 5),
           ylabel='Serum PFOS + PFOA (ng/mL)', xlabel='NHANES survey cycle')
    ax.set_xticklabels([period.replace('-', '\n') for period in periods])
    ax.set_title('a', loc='left', fontsize=12, fontweight='bold')
    ax.set_axisbelow(True)
    ax.grid(axis='both', ls='--', lw=.7, color='.72', alpha=.48)
    ax.legend(handles=[*lines, measured, Patch(fc=band_color, alpha=.18, ec='none', label='Model percentile band'), errors],
              fontsize=8.6, loc='upper right', frameon=False, labelspacing=.43)

    # Decompose the combined-food scenario by subtracting the nested scenarios.
    cycle_means = estimated['arithmetic_mean'].unstack('scenario').reindex(periods)
    assert np.ptp(cycle_means.iloc[0].to_numpy()) < 1e-10
    after_calibration = cycle_means.iloc[1:]
    residual = after_calibration['no_exposure']
    terrestrial = after_calibration['terrestrial_only'] - residual
    aquatic = after_calibration['aquatic_plus_terrestrial'] - after_calibration['terrestrial_only']
    concentration = pd.DataFrame({'carryover_from_2004': residual, 'terrestrial_food': terrestrial, 'aquatic_food': aquatic})
    combined = after_calibration['aquatic_plus_terrestrial']
    assert (concentration >= 0).all().all() and np.allclose(concentration.sum(axis=1), combined)
    composition = concentration.div(combined, axis=0) * 100
    assert np.allclose(composition.sum(axis=1), 100)

    bx.set_title('b', loc='left', fontsize=12, fontweight='bold')
    x_comp = np.arange(len(composition))
    source_styles = {
        'carryover_from_2004': ('Carryover from 2004', '#B9B9B9', '#777777'),
        'terrestrial_food': ('Terrestrial food', '#E8BD78', '#C99141'),
        'aquatic_food': ('Aquatic food', '#82CCBD', '#2C9A84'),
    }
    bottom = np.zeros(len(composition))
    for key, (label, fill, edge) in source_styles.items():
        values = composition[key].to_numpy()
        bx.bar(x_comp, values, bottom=bottom, width=.65, color=fill, edgecolor=edge, lw=.9, label=label, zorder=3)
        for x_value, base, share in zip(x_comp, bottom, values):
            if share >= 5:
                bx.text(x_value, base + share/2, f'{share:.1f}%', ha='center', va='center', fontsize=8.4, zorder=4)
        bottom += values
    bx.set(ylim=(0, 100), xlim=(-.50, len(x_comp)-.50), xticks=x_comp, yticks=np.arange(0, 101, 20),
           ylabel='Share of modeled serum burden', xlabel='NHANES survey cycle')
    bx.set_xticklabels([period.replace('-', '\n') for period in composition.index])
    bx.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    bx.tick_params(axis='y', right=True, labelright=True)
    bx.set_axisbelow(True)
    bx.grid(axis='y', ls='--', lw=.7, color='.72', alpha=.48)
    bx.legend(loc='upper center', bbox_to_anchor=(.5, 1.115), ncol=3, frameon=False, fontsize=8.5,
              columnspacing=1.25, handlelength=1.5)

    for ext in ['png', 'pdf']:
        fig.savefig(HERE / f'{STEM}.{ext}', dpi=400, facecolor='white', bbox_inches='tight', pad_inches=.1)
    plt.close(fig)
    source_table = pd.concat([combined.rename('total_ng_mL'), concentration.add_suffix('_ng_mL'),
                              composition.add_suffix('_pct')], axis=1)
    source_table.to_csv(HERE / 'Serum burden composition by cycle.csv', float_format='%.10g')


if __name__ == '__main__':
    main()
