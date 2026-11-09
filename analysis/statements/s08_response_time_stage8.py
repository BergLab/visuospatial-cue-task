"""Results: response time did not differ between laser-off and laser-on trials in Stage 8.

Response time is recorded from the laser-trigger time point (0.5 s before cue onset), so with a
0.5 s cue and 0.5 s second black screen the choice stimuli appear at 1.5 s. On Stage 8 laser-on
trials the pre-cue interval is 2.0 s longer; this is subtracted. The latency from choice-stimulus
onset is response time - 1.5 s.
"""
import _path  # noqa: F401
from common import load_sessions, stage_data, per_rat_mean, fmt, wilcoxon_p, RT_EXTENSION

d = stage_data(load_sessions(), 8)
off = per_rat_mean(d, "response_time_laser_false")
on = per_rat_mean(d, "response_time_laser_true") - RT_EXTENSION[8]
print(f"Stage 8, n = {len(off)} rats (mean ± SEM)")
print(f"  response time laser off: {fmt(off)} s   (latency from stimulus onset {fmt(off - 1.5)} s)")
print(f"  response time laser on : {fmt(on)} s   (latency from stimulus onset {fmt(on - 1.5)} s)")
print(f"  Wilcoxon signed-rank: p = {wilcoxon_p(off, on):.3f}")
