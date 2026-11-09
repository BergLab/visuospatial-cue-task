# visuospatial-cue-task
This is the code for the paper by Madelaine Bonfils, Silas Larsen, Roar Sorensen, Hayley Burm, Karen Sobriel, Grace Houser, Oksana Dmytriyeva, Martin Tano, Rune W Berg, called “Cue-guided performance is disrupted during pedunculotegmental-induced motor arrest” iScience 2027


Task software, behavioural data and analysis code for the behavioural results (Figures 2-4).

```
game/                  visuospatial cue task (VSCT), runs on the chamber Raspberry Pi
  vsct_game.py         python vsct_game.py --chamber standard | degraded  [--no-electronics]
  sound_01.wav         incorrect / premature response
  sound_02.wav         correct response
data/
  raw/                 one CSV per stimulation session (Stages 6-9), named r<rat>st<stage>s<session>.csv
  info.xlsx            per stimulation session: stimulated hemisphere (side: l / r / x = unknown)
                       and protocol version (time: Stage 8 22 / 25 = 2.2 / 2.5 s stimulation;
                       Stage 9 12 / 15 = stimulation starting 0.2 / 0.5 s after cue offset)
analysis/
  common.py            loading, inclusion criteria, metrics, statistics, plot helpers
  fig2.py              Figure 2 E-J
  fig3.py              Figure 3 B-D, F-H
  fig4.py              Figure 4 C1-F4
  statements/s*.py     one script per quantitative statement in the paper
  run_all.py           everything above
figures/               figure panels (SVG), produced by the figure scripts
```

## Running

```
python -m venv .venv
.venv/Scripts/activate        # Windows;  source .venv/bin/activate  on Linux / macOS
pip install -r requirements.txt
cd analysis
python run_all.py             # or a single script, e.g. python fig2.py
```

Tested with Python 3.12.0; exact package versions are pinned in `requirements.txt`.

## Analysis

* Stimulation stages: 6 = stimulation during cue, 7 = during extended cue, 8 = before cue,
  9 = after cue.
* Session inclusion: laser-off accuracy > 60 % and > 50 correct + incorrect trials; the first 10
  trials of every session are discarded. Seven rats (22, 31, 33, 35, 36, 38, 40) are analysed.
* Accuracy = correct / (correct + incorrect); premature responses and omissions excluded.
* Response time is recorded from the laser-trigger time point, 0.5 s before cue onset. On Stage 8
  laser-on trials the 2.0 s pre-cue extension is subtracted.
* Side bias: proportion of choices to each position; mean side bias = mean over positions of
  |p - 1/3| x 100 (percentage points). Ipsi- / contralateral positions are defined relative to
  the stimulated hemisphere.
* Experimental unit: the rat. Session values are averaged per rat and laser-off / laser-on values
  are paired within rat (n = 7). Mean ± SEM (SD with ddof = 1).
* Tests: two-sided Wilcoxon signed-rank (`scipy.stats.wilcoxon`, exact null distribution);
  Friedman test (`scipy.stats.friedmanchisquare`, chi-square approximation, plus an exact
  permutation p-value); post-hoc pairwise Wilcoxon tests with Holm correction.
* Simulated random sessions (Figure 2H-I) keep the layout and number of responses of the real
  sessions and draw every outcome as correct with probability 1/3 (fixed seed).
