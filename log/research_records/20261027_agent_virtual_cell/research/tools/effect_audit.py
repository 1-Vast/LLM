"""effect_audit.py - guards for per-group effect summaries.

Two lessons from R167 turned into code.

  1. A group that appears in a single split produces a zero-width bootstrap interval, because every
     resample is identical. That signature has now appeared eight times in this programme
     (R104, R108, R113, R135, R144, R147, R156, R167). The fix is a minimum-repetition filter applied
     BEFORE any interval is reported, not a note in a protocol.

  2. R167's gate counted groups with a negative point estimate as "reversals". With subsets of two to
     thirty splits, point estimates scatter around zero, so a sign count manufactures reversals that no
     interval supports. A reversal should mean that the interval excludes zero on the negative side.

Both are cheap and neither is optional.
"""

from __future__ import annotations

import numpy as np


def min_reps_filter(groups, min_reps=5):
    """Split groups by how many splits they appear in.

    groups: mapping of name -> record containing 'n_reps'.
    Returns (kept_names, dropped_names). Dropped groups must not be reported with intervals.
    """
    kept, dropped = [], []
    for name, rec in groups.items():
        n = rec.get("n_reps")
        if n is None:
            n = rec.get("reps", 0)
        (kept if n >= min_reps else dropped).append(name)
    return kept, dropped


def ci_degenerate(ci, tol=1e-9):
    """True when an interval has essentially zero width, which means the resampling did not vary."""
    if ci is None:
        return True
    lo, hi = float(ci[0]), float(ci[1])
    return (hi - lo) < tol


def interval_reversals(diffs, cis, names=None):
    """Count only interval-supported reversals.

    diffs: mapping name -> point estimate (or a sequence aligned with names)
    cis:   mapping name -> [lo, hi]  (or a sequence aligned with names)
    A group counts as a reversal only if its whole interval lies below zero.
    """
    if names is None:
        names = list(diffs.keys())
    return [n for n in names if float(cis[n][1]) < 0.0]


def summarise(groups, diff_key, ci_key, min_reps=5, tol=1e-9):
    """Full per-group summary with both guards applied.

    Returns a dict with the kept and dropped groups, any degenerate intervals among the kept ones, the
    interval-supported reversals, and the sign-only count so the two can be compared side by side.
    """
    kept, dropped = min_reps_filter(groups, min_reps)
    deg = [n for n in kept if ci_degenerate(groups[n][ci_key], tol)]
    clean = [n for n in kept if n not in deg]
    revs = interval_reversals({n: groups[n][diff_key] for n in clean},
                              {n: groups[n][ci_key] for n in clean})
    sign_neg = [n for n in clean if float(groups[n][diff_key]) < 0.0]
    return {
        "n_groups_total": len(groups),
        "kept": kept, "dropped": dropped,
        "degenerate_intervals": deg,
        "usable": clean,
        "interval_reversals": revs,
        "sign_only_negatives": sign_neg,
        "note": ("interval_reversals is the defensible count; sign_only_negatives is reported only to show "
                 "how much a sign-counting gate would have overstated"),
    }
