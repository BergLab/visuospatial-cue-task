"""Results: the two Stage 8 versions (2.2 s stimulation ending 0.3 s before cue onset vs 2.5 s
stimulation ending at cue onset) did not differ in accuracy or response time, so the sessions
were pooled."""
import _path  # noqa: F401
from _versions import compare_versions

print("Stage 8 protocol versions")
compare_versions(8, {22: "2.2 s stim", 25: "2.5 s stim"})
