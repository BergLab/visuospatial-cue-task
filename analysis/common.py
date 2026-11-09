"""Shared data loading, session inclusion, per-session metrics, statistics and plot helpers.

Conventions used throughout the analysis:
  * experimental unit: the rat. Session values are averaged per rat; laser-off and laser-on
    values are paired within rat.
  * accuracy = correct / (correct + incorrect); premature responses (PR) and omissions excluded.
  * chance level = 1/3 (three response positions).
  * mean +- SEM, SEM = SD (ddof = 1) / sqrt(n).
  * two-sided Wilcoxon signed-rank tests with exact null distribution (scipy.stats.wilcoxon);
    Friedman tests with chi-square (scipy) and exact permutation p-values; Holm correction for
    post-hoc pairwise comparisons.
"""
from pathlib import Path
import re

import numpy as np
import polars as pl
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection
from scipy.stats import sem as _sem, wilcoxon

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"
INFO_FILE = ROOT / "data" / "info.xlsx"
FIG_DIR = ROOT / "figures"

# Session inclusion criteria
MIN_LASER_OFF_ACCURACY = 0.6     # laser-off accuracy must be strictly greater
MIN_RESPONSE_TRIALS = 50         # correct + incorrect trials must be strictly greater
N_SKIPPED_TRIALS = 10            # the first 10 trials of every session are discarded
INCLUDED_RATS = [22, 31, 33, 35, 36, 38, 40]
STIM_STAGES = [6, 7, 8, 9]       # 6: during cue, 7: during extended cue, 8: before cue, 9: after cue
RT_EXTENSION = {8: 2.0}          # s added to the pre-cue interval on laser-on trials (removed from RT)

CHANCE = 1 / 3
OFF_COLOR = "#334155"
ON_COLOR = "#C85450"

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.sans-serif"] = ["Arial"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"] = "none"


# --------------------------------------------------------------------------- #
# Per-session metrics
# --------------------------------------------------------------------------- #
def is_response(outcome):
    """True for correct/incorrect choices; False for premature responses and omissions."""
    return str(outcome).lower() in ("true", "false")


def accuracy(outcomes, laser, laser_on):
    sel = [o.lower() == "true" for o, ls in zip(outcomes, laser) if ls == laser_on and is_response(o)]
    return sum(sel) / len(sel) if sel else None


def mean_response_time(outcomes, rts, laser, laser_on):
    """Mean response time of correct + incorrect trials. The task software measures response
    time from the laser-trigger time point, 0.5 s before cue onset."""
    vals = [rt for o, rt, ls in zip(outcomes, rts, laser) if ls == laser_on and is_response(o)]
    return float(np.mean(vals)) if vals else None


def side_proportions(chosen, laser, laser_on):
    """Proportion of choices to the [left, center, right] stimulus."""
    counts = [0, 0, 0]
    for c, ls in zip(chosen, laser):
        if c is not None and ls == laser_on:
            counts[c] += 1
    total = sum(counts)
    return [n / total if total else 0.0 for n in counts]


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _session_id(filename):
    m = re.search(r"r(\d+)st(\d+)s(\d+)", filename)
    return tuple(int(g) for g in m.groups()) if m else (None, None, None)


def load_sessions(apply_criteria=True, verbose=False):
    """One row per session: per-trial lists, per-session metrics and session metadata.

    apply_criteria: keep sessions with laser-off accuracy > 60 % and > 50 response trials
                    (after discarding the first 10 trials) from the included rats.
    Every included stimulation-stage session must have a row in info.xlsx (stimulated hemisphere and
    protocol version); a missing row raises an error.
    """
    rows = []
    for csv_file in sorted(DATA_DIR.rglob("*.csv")):
        rat, stage, session = _session_id(csv_file.name)
        if rat is None:
            continue
        df = pl.read_csv(csv_file, schema_overrides={"Trial Correct": pl.Utf8})
        if df["Laser status"].dtype == pl.Utf8:
            df = df.with_columns(pl.col("Laser status").str.to_lowercase() == "true")
        s = N_SKIPPED_TRIALS
        outcomes = df["Trial Correct"].to_list()[s:]
        laser = df["Laser status"].cast(pl.Boolean, strict=False).to_list()[s:]
        chosen = df["Chosen Square"].cast(pl.Int64, strict=False).to_list()[s:]
        rts = df["Response Time"].cast(pl.Float32, strict=False).to_list()[s:]
        row = {"rat_number": rat, "stage_number": stage, "session_number": session,
               "source_file": csv_file.name, "trial_correct": outcomes, "laser_status": laser,
               "chosen_square": chosen, "response_time": rts,
               "n_responses": sum(is_response(o) for o in outcomes)}
        for on, tag in [(True, "true"), (False, "false")]:
            row[f"accuracy_laser_{tag}"] = accuracy(outcomes, laser, on)
            row[f"side_bias_laser_{tag}"] = side_proportions(chosen, laser, on)
            row[f"response_time_laser_{tag}"] = mean_response_time(outcomes, rts, laser, on)
        rows.append(row)
    result = pl.DataFrame(rows)
    n_loaded = result.height

    if apply_criteria:
        result = result.filter((pl.col("accuracy_laser_false") > MIN_LASER_OFF_ACCURACY)
                               & (pl.col("n_responses") > MIN_RESPONSE_TRIALS)
                               & pl.col("rat_number").is_in(INCLUDED_RATS))

    info = pl.read_excel(INFO_FILE)
    result = result.join(info, on=["rat_number", "stage_number", "session_number"], how="left")
    no_info = result.filter(pl.col("stage_number").is_in(STIM_STAGES) & pl.col("side").is_null())
    if apply_criteria and no_info.height:
        raise ValueError("Stimulation sessions without a row in info.xlsx: "
                         + ", ".join(no_info["source_file"]))
    if verbose:
        print(f"Sessions: {n_loaded} loaded, {result.height} included")
    return result.sort(["stage_number", "rat_number", "session_number"])


def stage_data(result, stage):
    return result.filter(pl.col("stage_number") == stage)


def rats_in(df):
    return sorted(df["rat_number"].unique().to_list())


# --------------------------------------------------------------------------- #
# Per-rat summaries
# --------------------------------------------------------------------------- #
def per_rat_mean(df, col):
    """Mean over sessions of a per-session value, one value per rat."""
    return np.array([df.filter(pl.col("rat_number") == r)[col].mean() for r in rats_in(df)])


def per_rat_side_props(df, col):
    """(n_rats, 3) mean proportion of choices to left / center / right."""
    return np.array([np.array(df.filter(pl.col("rat_number") == r)[col].to_list(), dtype=float).mean(axis=0)
                     for r in rats_in(df)])


def per_rat_side_props_ipsi(df, col):
    """(n_rats, 3) proportions ordered ipsilateral / center / contralateral to the stimulated
    hemisphere (info.xlsx 'side' = l / r). Sessions with unknown side ('x') are skipped."""
    out = []
    for r in rats_in(df):
        rows = []
        for row in df.filter(pl.col("rat_number") == r).iter_rows(named=True):
            if row["side"] == "l":
                rows.append(row[col])
            elif row["side"] == "r":
                rows.append(row[col][::-1])
        out.append(np.array(rows, dtype=float).mean(axis=0))
    return np.array(out)


def mean_side_bias(props):
    """Mean side bias in percentage points: mean over positions of |p - 1/3| x 100."""
    return np.abs(np.asarray(props) - CHANCE).mean(axis=-1) * 100


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def sem(x):
    """Standard error of the mean, SD with ddof = 1."""
    return float(_sem(np.asarray(x, dtype=float)))


def fmt(x, scale=1, d=2):
    x = np.asarray(x, dtype=float) * scale
    return f"{x.mean():.{d}f} ± {sem(x):.{d}f}"


def wilcoxon_p(a, b=None):
    """Two-sided Wilcoxon signed-rank test, exact p-value for n = 7 without ties/zeros."""
    return float((wilcoxon(a, b) if b is not None else wilcoxon(a)).pvalue)


def friedman_exact_p(x):
    """Exact permutation p-value of the Friedman test for an (n, k) array, enumerating all
    (k!)^n within-subject permutations (n = 7, k = 3: 279 936)."""
    from itertools import permutations, product
    from scipy.stats import rankdata
    x = np.asarray(x, dtype=float)
    n, k = x.shape
    ranks = np.apply_along_axis(rankdata, 1, x)
    perms = np.array(list(permutations(range(k))))
    rows = np.stack([r[perms] for r in ranks])
    obs = np.sum(ranks.sum(0) ** 2)
    count = sum(np.sum(rows[np.arange(n), idx].sum(0) ** 2) >= obs - 1e-9
                for idx in product(range(len(perms)), repeat=n))
    return count / len(perms) ** n


def holm(pvals):
    """Holm-Bonferroni adjusted p-values."""
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    adj = np.maximum.accumulate([p[i] * (len(p) - j) for j, i in enumerate(order)])
    out = np.empty_like(p)
    out[order] = np.minimum(adj, 1)
    return out


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def gradient_line(ax, x1, y1, x2, y2, c1=OFF_COLOR, c2=ON_COLOR, linewidth=1, alpha=1.0):
    n = 100
    pts = np.array([np.linspace(x1, x2, n), np.linspace(y1, y2, n)]).T.reshape(-1, 1, 2)
    seg = np.concatenate([pts[:-1], pts[1:]], axis=1)
    a = np.array(mcolors.to_rgba(c1, alpha=alpha))
    b = np.array(mcolors.to_rgba(c2, alpha=alpha))
    t = np.linspace(0, 1, len(seg))[:, None]
    ax.add_collection(LineCollection(seg, colors=a + t * (b - a), linewidths=linewidth,
                                     capstyle="round", joinstyle="round"))


def paired_bar(ax, off, on, rng, lw=2, capsize=5, s=10, line_w=1):
    """Open bars (mean +- SEM) with per-rat points joined by lines (x jittered)."""
    for y0, y1 in zip(off, on):
        dx = rng.uniform(-0.2, 0.2)
        gradient_line(ax, dx, y0, 1 + dx, y1, linewidth=line_w)
        ax.scatter(dx, y0, color=OFF_COLOR, s=s, zorder=4)
        ax.scatter(1 + dx, y1, color=ON_COLOR, s=s, zorder=4)
    for x, vals, c in [(0, off, OFF_COLOR), (1, on, ON_COLOR)]:
        ax.bar(x, np.mean(vals), edgecolor=c, width=0.7, fill=False, lw=lw, zorder=3,
               yerr=sem(vals), error_kw={"ecolor": c, "capsize": capsize, "capthick": 1, "elinewidth": 1})
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Laser off", "Laser on"])


RASTER_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "raster", [(1, 1, 1, 0), "#5C6670", "#9B7F92", (1, 1, 1, 0)])
JITTER_SEEDS = {6: 42, 7: 30, 8: 39, 9: 39}


def raster_matrix(df, laser_on):
    """Trial-outcome matrix: one row per session (response trials of one laser condition, in
    order), rats separated by blank rows. 1 = correct, 2 = incorrect, 0/3 = blank."""
    rats = rats_in(df)
    blocks = []
    for rat in rats:
        rd = df.filter(pl.col("rat_number") == rat).sort("session_number")
        rows = [[1 if o.lower() == "true" else 2 for o, ls in zip(oc, lsr) if is_response(o) and ls == laser_on]
                for oc, lsr in zip(rd["trial_correct"].to_list(), rd["laser_status"].to_list())]
        if rat != rats[0]:
            rows.insert(0, [3] * len(rows[0]))
        if rat != rats[-1]:
            rows.append([3] * len(rows[-1]))
            rows.append([0])
        blocks.append(rows)
    width = max(len(r) for b in blocks for r in b)
    return np.array([r + [0] * (width - len(r)) for b in blocks for r in b])


def simulate_random(m, rng):
    """Same layout and number of responses, each outcome correct with probability 1/3."""
    m = m.copy()
    mask = (m == 1) | (m == 2)
    m[mask] = rng.choice([1, 2], size=mask.sum(), p=[CHANCE, 1 - CHANCE])
    return m


def plot_raster(m, title):
    fig, ax = plt.subplots()
    ax.imshow(m, vmin=0, vmax=3, cmap=RASTER_CMAP)
    ax.set_title(title)
    ax.axis("off")
    fig.patch.set_alpha(0)
    return fig


def plot_accuracy(df, stage):
    """Paired laser-off vs laser-on accuracy per rat."""
    off = per_rat_mean(df, "accuracy_laser_false")
    on = per_rat_mean(df, "accuracy_laser_true")
    fig, ax = plt.subplots(figsize=(2, 2 * 1.33), dpi=300)
    paired_bar(ax, off, on, np.random.RandomState(JITTER_SEEDS[stage]))
    ax.set_ylabel("Accuracy")
    ax.set_title(f"Stage {stage}")
    ax.set_ylim([0, 1])
    ax.axhline(CHANCE, linestyle="dashed", color="black", lw=1, alpha=0.3, zorder=1)
    print(f"Stage {stage} accuracy (n = {len(off)} rats): off {fmt(off, d=3)}, on {fmt(on, d=3)}, "
          f"difference {fmt(on - off, d=3)}, Wilcoxon p = {wilcoxon_p(off, on):.4f}")
    return fig


def savefig(fig, name):
    FIG_DIR.mkdir(exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path, dpi=300, bbox_inches="tight", transparent=name.endswith(".svg"))
    print(f"saved {path.relative_to(ROOT)}")
    plt.close(fig)
