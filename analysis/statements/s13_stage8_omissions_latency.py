"""Discussion: no increase in response latency or omission rate when stimulation was delivered
before the cue (Stage 8).

Omission rate = omitted trials / all trials of a laser condition, pooled over each rat's
sessions. Response time as in s08 (pre-cue extension of 2.0 s on laser-on trials subtracted).
"""
import _path  # noqa: F401
import numpy as np
import polars as pl

from common import load_sessions, stage_data, rats_in, per_rat_mean, fmt, wilcoxon_p, RT_EXTENSION


def omission_rate(df, laser_on):
    out = []
    for r in rats_in(df):
        rd = df.filter(pl.col("rat_number") == r)
        sel = [o for oc, lsr in zip(rd["trial_correct"], rd["laser_status"]) for o, ls in zip(oc, lsr)
               if ls == laser_on]
        out.append(sum(o is None for o in sel) / len(sel))
    return np.array(out)


d = stage_data(load_sessions(), 8)
off, on = omission_rate(d, False), omission_rate(d, True)
print(f"Stage 8, n = {len(off)} rats (mean ± SEM)")
print(f"  omission rate: off {fmt(off, 100)} %, on {fmt(on, 100)} %, Wilcoxon p = {wilcoxon_p(off, on):.3f}")
rt_off = per_rat_mean(d, "response_time_laser_false")
rt_on = per_rat_mean(d, "response_time_laser_true") - RT_EXTENSION[8]
print(f"  response time: off {fmt(rt_off)} s, on {fmt(rt_on)} s, Wilcoxon p = {wilcoxon_p(rt_off, rt_on):.3f}")
