"""Figure 4 - Testing for side bias across stimulation stages.

Generates panels C1-F4 as one 4 x 4 grid (fig4_side_bias.svg); A and B are schematics.
Rows: C = Stage 6 (during cue), D = Stage 7 (during extended cue), E = Stage 8 (before cue),
F = Stage 9 (after cue). Columns:
    1  % of choices to the left / center / right stimulus per rat (laser off, laser on)
    2  mean side bias (pp) per rat, laser off vs on
    3  preference for each position (p - 1/3, pp), laser off vs on
    4  as 3, positions relative to the stimulated hemisphere (ipsi / center / contra)
Bars: mean +- SEM over rats; points: individual rats.
"""
import numpy as np

from common import (load_sessions, stage_data, rats_in, per_rat_side_props, per_rat_side_props_ipsi,
                    mean_side_bias, sem, gradient_line, savefig, plt, OFF_COLOR, ON_COLOR,
                    CHANCE, STIM_STAGES)

JITTER_SEED = 0
OFF, ON = "side_bias_laser_false", "side_bias_laser_true"


def cm(x):
    return x / 2.54


def _pairs(ax, x0, off, on, rng, s=2):
    for y0, y1 in zip(off, on):
        dx = rng.uniform(-0.2, 0.2)
        gradient_line(ax, x0 + dx, y0, x0 + 1 + dx, y1, linewidth=0.6)
        ax.scatter(x0 + dx, y0, color=OFF_COLOR, s=s, zorder=4)
        ax.scatter(x0 + 1 + dx, y1, color=ON_COLOR, s=s, zorder=4)


def _bar(ax, x, vals, color):
    ax.bar(x, np.mean(vals), edgecolor=color, width=0.7, fill=False, lw=1, zorder=3, yerr=sem(vals),
           error_kw={"ecolor": color, "capsize": 3, "capthick": 1, "elinewidth": 1})


def panel_distribution(ax, d):
    rats = rats_in(d)
    p_off, p_on = per_rat_side_props(d, OFF) * 100, per_rat_side_props(d, ON) * 100
    for i in range(len(rats)):
        for side in range(3):
            ax.bar(i * 10 - 2 + side - 1, p_off[i, side], color=OFF_COLOR, width=0.7)
            ax.bar(i * 10 + 2 + side - 1, p_on[i, side], color=ON_COLOR, width=0.7)
    ax.set_xlabel("Rat nr.", fontsize=8)
    ax.set_ylabel("% of responses", fontsize=8)
    ax.set_xticks([10 * i for i in range(len(rats))])
    ax.set_xticklabels(rats, fontsize=7)
    ax.set_ylim([0, 100])
    ax.axhline(CHANCE * 100, linestyle="dashed", color="black", lw=1, alpha=0.3, zorder=-10)


def panel_mean_bias(ax, d, rng):
    off = mean_side_bias(per_rat_side_props(d, OFF))
    on = mean_side_bias(per_rat_side_props(d, ON))
    _pairs(ax, 0, off, on, rng)
    _bar(ax, 0, off, OFF_COLOR)
    _bar(ax, 1, on, ON_COLOR)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Laser off", "Laser on"], fontsize=7)
    ax.set_ylabel("Mean sidebias (pp)", fontsize=8)
    ax.set_ylim([0, 40])


def panel_preference(ax, p_off, p_on, labels, rng):
    pref_off, pref_on = (p_off - CHANCE) * 100, (p_on - CHANCE) * 100
    for side in range(3):
        _pairs(ax, side * 2, pref_off[:, side], pref_on[:, side], rng)
        _bar(ax, side * 2, pref_off[:, side], OFF_COLOR)
        _bar(ax, side * 2 + 1, pref_on[:, side], ON_COLOR)
    ax.set_xticks([0.5, 2.5, 4.5])
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylim([-60, 60])
    ax.set_ylabel("Mean sidebias (pp)", fontsize=8)


result = load_sessions(verbose=True)
rng = np.random.RandomState(JITTER_SEED)
fig, axes = plt.subplots(4, 4, figsize=(cm(16.5), cm(16.5)), dpi=300,
                         gridspec_kw={"width_ratios": [2, 0.7, 1.5, 1.5]})
for row, stage in enumerate(STIM_STAGES):
    d = stage_data(result, stage)
    panel_distribution(axes[row, 0], d)
    panel_mean_bias(axes[row, 1], d, rng)
    panel_preference(axes[row, 2], per_rat_side_props(d, OFF), per_rat_side_props(d, ON),
                     ["Left", "Center", "Right"], rng)
    panel_preference(axes[row, 3], per_rat_side_props_ipsi(d, OFF), per_rat_side_props_ipsi(d, ON),
                     ["Ipsi", "Center", "Contra"], rng)
    for ax in axes[row]:
        ax.tick_params(labelsize=7)
    for ax in axes[row, 1:]:
        ax.tick_params("x", rotation=20)

fig.tight_layout(h_pad=2.0)
savefig(fig, "fig4_side_bias.svg")
