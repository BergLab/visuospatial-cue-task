"""Results, Figure 4 C4-F4: laser-induced change in choices ipsilateral vs contralateral to the
stimulated hemisphere.

Positions are re-labelled per session from the stimulated side in info.xlsx (left fiber:
left stimulus = ipsilateral); sessions with unknown side are skipped. Change = (p_on - p_off)
x 100 (pp); proportions are of all choices (left, center, right).
"""
import _path  # noqa: F401
import polars as pl

from common import load_sessions, stage_data, per_rat_side_props_ipsi, fmt, wilcoxon_p, STIM_STAGES

res = load_sessions()
print("Sessions with unknown stimulated side (skipped):",
      ", ".join(res.filter(pl.col("side") == "x")["source_file"].to_list()))
for stage, panel in zip(STIM_STAGES, "CDEF"):
    d = stage_data(res, stage)
    delta = (per_rat_side_props_ipsi(d, "side_bias_laser_true")
             - per_rat_side_props_ipsi(d, "side_bias_laser_false")) * 100
    print(f"Stage {stage} (Fig 4{panel}4), n = {len(delta)}: ipsi {fmt(delta[:, 0])} pp vs "
          f"contra {fmt(delta[:, 2])} pp, Wilcoxon p = {wilcoxon_p(delta[:, 0], delta[:, 2]):.3f}")
