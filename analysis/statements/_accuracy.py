"""Accuracy statement for one stimulation stage: laser off vs on, and each vs chance."""
from common import load_sessions, stage_data, per_rat_mean, fmt, wilcoxon_p, CHANCE


def accuracy_statement(stage):
    d = stage_data(load_sessions(), stage)
    off = per_rat_mean(d, "accuracy_laser_false")
    on = per_rat_mean(d, "accuracy_laser_true")
    print(f"Stage {stage}, n = {len(off)} rats (mean ± SEM)")
    print(f"  accuracy laser off : {fmt(off, 100, 1)} %")
    print(f"  accuracy laser on  : {fmt(on, 100, 1)} %")
    print(f"  difference (on-off): {fmt(on - off, 100, 1)} percentage points")
    print(f"  Wilcoxon signed-rank, off vs on   : p = {wilcoxon_p(off, on):.3f}")
    print(f"  Wilcoxon signed-rank, off vs 1/3  : p = {wilcoxon_p(off - CHANCE):.3f}")
    print(f"  Wilcoxon signed-rank, on  vs 1/3  : p = {wilcoxon_p(on - CHANCE):.3f}")
