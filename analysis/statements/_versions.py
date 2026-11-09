"""Comparison of the two protocol versions of a stage (info.xlsx column 'time')."""
import polars as pl

from common import load_sessions, stage_data, rats_in, wilcoxon_p, RT_EXTENSION


def compare_versions(stage, versions):
    """versions: {info.xlsx 'time' code: label}. Per-rat means for each version, paired
    two-sided Wilcoxon signed-rank test over rats that ran both versions."""
    d = stage_data(load_sessions(), stage)
    d = d.with_columns((pl.col("accuracy_laser_true") - pl.col("accuracy_laser_false")).alias("laser_effect"),
                       (pl.col("response_time_laser_true") - RT_EXTENSION.get(stage, 0.0)).alias("rt_laser_on"))
    for t, label in versions.items():
        print(f"  {label}: {d.filter(pl.col('time') == t).height} sessions")
    labels = list(versions.values())
    measures = {"accuracy, laser on": "accuracy_laser_true", "accuracy, on - off": "laser_effect",
                "response time (s), laser on": "rt_laser_on", "response time (s), laser off": "response_time_laser_false"}
    for name, col in measures.items():
        pairs = []
        for r in rats_in(d):
            rd = d.filter(pl.col("rat_number") == r)
            v = [rd.filter(pl.col("time") == t)[col].mean() for t in versions]
            if None not in v:
                pairs.append(v)
        a = [p[0] for p in pairs]
        b = [p[1] for p in pairs]
        print(f"  {name:30s} {labels[0]}: {sum(a) / len(a):.3f}   {labels[1]}: {sum(b) / len(b):.3f}   "
              f"(n = {len(pairs)} rats)  p = {wilcoxon_p(a, b):.3f}")
