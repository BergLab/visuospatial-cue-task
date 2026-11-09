"""Results, Figure 4 C2-F2: mean side bias, laser off vs on, per stage.

Mean side bias = (|p_L - 1/3| + |p_C - 1/3| + |p_R - 1/3|) / 3 x 100 (percentage points), from
each rat's session-averaged choice proportions.
"""
import _path  # noqa: F401
from common import load_sessions, stage_data, per_rat_side_props, mean_side_bias, fmt, wilcoxon_p, STIM_STAGES

res = load_sessions()
for stage, panel in zip(STIM_STAGES, "CDEF"):
    d = stage_data(res, stage)
    off = mean_side_bias(per_rat_side_props(d, "side_bias_laser_false"))
    on = mean_side_bias(per_rat_side_props(d, "side_bias_laser_true"))
    print(f"Stage {stage} (Fig 4{panel}2), n = {len(off)}: off {fmt(off)} pp, on {fmt(on)} pp, "
          f"increase {fmt(on - off)} pp, Wilcoxon p = {wilcoxon_p(off, on):.3f}")
