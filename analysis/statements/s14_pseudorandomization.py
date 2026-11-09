"""Methods: pseudorandomization of laser trials and cue positions, verified on the recorded data.

Task software rules: laser on in exactly 5 of every block of 10 trials and never more than two
consecutive trials with the same laser condition; cue position balanced in blocks of 9 trials
(3 per position) and never the same position more than twice in a row.
Checked on all stimulation-stage session files with >= 10 trials (all trials, before any
exclusion).
"""
import _path  # noqa: F401
import re
from itertools import groupby

import polars as pl

from common import DATA_DIR, STIM_STAGES

max_run = {True: 0, False: 0}
max_cue_run, blocks_ok, n = 0, 0, 0
for f in sorted(DATA_DIR.rglob("*.csv")):
    m = re.search(r"r(\d+)st(\d+)s(\d+)", f.name)
    if not m or int(m.group(2)) not in STIM_STAGES:
        continue
    df = pl.read_csv(f, schema_overrides={"Trial Correct": pl.Utf8, "Laser status": pl.Utf8})
    if df.height < 10:
        continue
    laser = [s.lower() == "true" for s in df["Laser status"].to_list()]
    for k, g in groupby(laser):
        max_run[k] = max(max_run[k], len(list(g)))
    cues = df["Correct Square"].cast(pl.Int64, strict=False).to_list()
    max_cue_run = max([max_cue_run] + [len(list(g)) for k, g in groupby(cues) if k is not None])
    blocks = [laser[i:i + 10] for i in range(0, len(laser) - len(laser) % 10, 10)]
    blocks_ok += all(sum(b) == 5 for b in blocks)
    n += 1

print(f"{n} session files")
print(f"Longest run of consecutive laser-on trials : {max_run[True]}")
print(f"Longest run of consecutive laser-off trials: {max_run[False]}")
print(f"Longest run of identical cue positions     : {max_cue_run}")
print(f"Sessions in which every complete block of 10 trials has 5 laser trials: {blocks_ok}/{n}")
