"""Results: the two Stage 9 versions (stimulation starting 0.2 s vs 0.5 s after cue offset) did
not differ in accuracy, so the sessions were pooled. info.xlsx codes the versions as time = 12 / 15
(laser onset 1.2 / 1.5 s after the trigger point 0.5 s before cue onset)."""
import _path  # noqa: F401
from _versions import compare_versions

print("Stage 9 protocol versions")
compare_versions(9, {12: "0.2 s after cue", 15: "0.5 s after cue"})
