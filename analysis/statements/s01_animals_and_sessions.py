"""Results / Methods: animals and sessions included in the analysis.

Number of rats, sessions per rat and stage, and response trials per session after applying
the inclusion criteria (laser-off accuracy > 60 %, > 50 correct + incorrect trials after
discarding the first 10 trials).
"""
import _path  # noqa: F401
import polars as pl

from common import load_sessions, STIM_STAGES

res = load_sessions(verbose=True).filter(pl.col("stage_number").is_in(STIM_STAGES))
counts = res.group_by(["stage_number", "rat_number"]).len()
print(f"Rats: {sorted(res['rat_number'].unique().to_list())} (n = {res['rat_number'].n_unique()})")
print("Sessions per rat and stage:")
print(counts.pivot(on="stage_number", index="rat_number", values="len", sort_columns=True).sort("rat_number"))
print(f"Minimum sessions per rat per stage: {counts['len'].min()}")
print(f"Response trials per session: min {res['n_responses'].min()}, median {res['n_responses'].median():.0f}")
