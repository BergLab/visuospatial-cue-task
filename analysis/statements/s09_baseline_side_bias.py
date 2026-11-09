"""Results: on laser-off trials (Stages 6-9 pooled) responses were distributed approximately
evenly over the three positions (Friedman test)."""
import _path  # noqa: F401
import polars as pl
from scipy.stats import friedmanchisquare

from common import load_sessions, per_rat_side_props, fmt, friedman_exact_p

d = load_sessions().filter(pl.col("stage_number").is_between(6, 9))
p = per_rat_side_props(d, "side_bias_laser_false")
print(f"Laser-off proportion of choices, Stages 6-9, n = {len(p)} rats (mean ± SEM)")
for i, name in enumerate(["Left", "Center", "Right"]):
    print(f"  {name:6s}: {fmt(p[:, i])}")
res = friedmanchisquare(*p.T)
print(f"  Friedman: chi2 = {res.statistic:.2f}, p = {res.pvalue:.3f} (chi-square), "
      f"p = {friedman_exact_p(p):.3f} (exact)")
