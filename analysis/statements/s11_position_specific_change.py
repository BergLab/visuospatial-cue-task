"""Results, Figure 4 C3-F3: laser-induced change in the proportion of choices to each position.

Change = (p_on - p_off) x 100 (pp) per position, per rat. The Friedman test asks whether the
change differs between the three positions; it does not identify which position. Pairwise
post-hoc comparisons: two-sided Wilcoxon signed-rank, Holm-corrected over the three pairs.
"""
import _path  # noqa: F401
from scipy.stats import friedmanchisquare

from common import (load_sessions, stage_data, per_rat_side_props, fmt, wilcoxon_p, friedman_exact_p, holm,
                    STIM_STAGES)

PAIRS = [("Center vs Left", 1, 0), ("Center vs Right", 1, 2), ("Left vs Right", 0, 2)]

res = load_sessions()
for stage, panel in zip(STIM_STAGES, "CDEF"):
    d = stage_data(res, stage)
    delta = (per_rat_side_props(d, "side_bias_laser_true") - per_rat_side_props(d, "side_bias_laser_false")) * 100
    print(f"Stage {stage} (Fig 4{panel}3), n = {len(delta)} rats, change in pp (mean ± SEM)")
    print("  " + "; ".join(f"{name} {fmt(delta[:, i])}" for i, name in enumerate(["Left", "Center", "Right"])))
    fr = friedmanchisquare(*delta.T)
    print(f"  Friedman: chi2 = {fr.statistic:.2f}, p = {fr.pvalue:.3f} (chi-square), "
          f"p = {friedman_exact_p(delta):.3f} (exact)")
    raw = [wilcoxon_p(delta[:, a], delta[:, b]) for _, a, b in PAIRS]
    for (name, _, _), r, h in zip(PAIRS, raw, holm(raw)):
        print(f"    {name:16s} p = {r:.3f}, Holm-adjusted p = {h:.3f}")
